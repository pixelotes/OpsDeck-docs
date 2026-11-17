# Backup & Restore

OpsDeck stores data in two places: PostgreSQL (all application data) and the filesystem (attachments and uploaded files). Both must be backed up together to ensure a consistent restore.

## What to back up

| Component | Location | Method |
|---|---|---|
| Database | PostgreSQL | `pg_dump` |
| Attachments | `/app/data/attachments` (container) or `./data/attachments` (host) | File copy / tar, or restic |
| Configuration | `.env` file, or the Kubernetes Secrets and values file | File copy |

Keep `SECRET_KEY` and `DATA_ENCRYPTION_KEY` with your backups (in a password manager or secret store, not next to the dump). Stored connector credentials are encrypted with them, and a restored database is unreadable for those fields without the same key.

## Docker Compose

### Backup script

```bash
#!/bin/bash
# backup-opsdeck.sh
set -euo pipefail

BACKUP_DIR="/backups/opsdeck"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

# Database backup
echo "Backing up database..."
docker-compose exec -T db pg_dump -U opsdeck opsdeck \
  | gzip > "$BACKUP_DIR/db_${TIMESTAMP}.sql.gz"

# Attachments backup
echo "Backing up attachments..."
tar -czf "$BACKUP_DIR/attachments_${TIMESTAMP}.tar.gz" ./data/attachments

# Cleanup old backups
find "$BACKUP_DIR" -name "*.gz" -mtime +${RETENTION_DAYS} -delete

echo "Backup complete: $BACKUP_DIR/*_${TIMESTAMP}.*"
```

Schedule via cron:

```cron
0 2 * * * /opt/scripts/backup-opsdeck.sh >> /var/log/opsdeck-backup.log 2>&1
```

### Restore procedure

#### 1. Stop the application

```bash
docker-compose stop web
```

#### 2. Restore the database

```bash
# Drop and recreate the database
docker-compose exec db psql -U opsdeck -d postgres -c "DROP DATABASE opsdeck;"
docker-compose exec db psql -U opsdeck -d postgres -c "CREATE DATABASE opsdeck;"

# Restore from backup
gunzip -c /backups/opsdeck/db_20260324_020000.sql.gz \
  | docker-compose exec -T db psql -U opsdeck opsdeck
```

#### 3. Restore attachments

```bash
rm -rf ./data/attachments
tar -xzf /backups/opsdeck/attachments_20260324_020000.tar.gz
```

#### 4. Restart

```bash
docker-compose start web
```

## Kubernetes (Helm backup CronJob)

The Helm chart includes a backup CronJob. When `backup.enabled` is `true` it dumps the database and backs up the dump and the attachments PVC to a [restic](https://restic.net/) repository, usually an S3 bucket. Configuration is described under [Kubernetes Deployment](kubernetes.md#backups); this section explains what the job does and how to restore from it.

### Backup image

The job runs the `pixelotes/opsdeck-backup` image, built from `Dockerfile.opsdeck-backup` in the repository. It is Alpine 3.24 with `postgresql16-client` (for `pg_dump` and `psql`), `restic`, `ca-certificates` and `tzdata`, and its entrypoint is `sh`. Build and push it yourself if you use a private registry:

```bash
docker build -f Dockerfile.opsdeck-backup -t registry.example.com/opsdeck-backup:1 .
docker push registry.example.com/opsdeck-backup:1
```

Then set `backup.image.repository` and `backup.image.tag`.

### What the job does

The script is stored in the `<release>-backup-script` ConfigMap and runs on `backup.schedule` (default `0 3 * * *`, daily at 03:00). The CronJob forbids concurrent runs and keeps the last 3 successful and 3 failed jobs. Each run:

1. Checks the restic repository and runs `restic init` if it does not exist yet.
2. Runs `pg_dump "$DATABASE_URL" | gzip` into `/backup/database/opsdeck-<YYYYMMDD-HHMMSS>.sql.gz`. `DATABASE_URL` is built the same way as for the application, from `database.*` and `postgresql.auth.*`.
3. Runs `restic backup /backup/database /backup/files` with the tags `opsdeck` and `db-<YYYYMMDD-HHMMSS>`. `/backup/files` is the attachments PVC (or `persistence.attachments.existingClaim`), mounted read-only, so the database dump and the attachments end up in one snapshot.
4. Applies the retention policy with `restic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 6 --prune` (values from `backup.retention`).

The dump is written to an `emptyDir`, so only the restic repository keeps it.

The job needs:

| Setting | Purpose |
|---|---|
| `backup.existingSecret` | Secret with `RESTIC_REPOSITORY` (for example `s3:s3.amazonaws.com/my-bucket/opsdeck`) and `RESTIC_PASSWORD` |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` in the same Secret | S3 credentials, unless `backup.aws.useIRSA` is `true` |
| `backup.aws.region` | Sets `AWS_DEFAULT_REGION`; some IRSA setups need it for STS |
| `persistence.attachments.enabled` | The job always mounts the attachments PVC |

!!! warning "Keep the restic password"
    restic encrypts the repository with `RESTIC_PASSWORD`. Without it the backups cannot be read. Store it outside the cluster as well.

### IRSA on EKS

With `backup.aws.useIRSA: true` the job does not get `AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY`. restic then uses the web identity token that the EKS pod identity webhook injects into pods running under a ServiceAccount annotated with an IAM role:

```yaml
backup:
  enabled: true
  existingSecret: opsdeck-backup
  aws:
    useIRSA: true
    region: eu-west-1
  serviceAccount:
    create: true                 # creates <release>-backup
    annotations:
      eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/opsdeck-backup
```

To use a ServiceAccount you manage yourself, set `serviceAccount.create: false` and `serviceAccount.name` to its name. The IAM role needs read and write access to the bucket prefix used by `RESTIC_REPOSITORY`.

### Run a backup now

```bash
kubectl create job --from=cronjob/opsdeck-backup opsdeck-backup-manual -n opsdeck
kubectl logs -f job/opsdeck-backup-manual -n opsdeck
```

### List snapshots

Run restic from a pod that has the same Secret, for example the restore pod below:

```bash
restic snapshots --tag opsdeck
```

### Restore

The dump is a plain SQL `pg_dump` without `DROP` statements, so restore it into an empty database.

#### 1. Stop OpsDeck

```bash
kubectl scale deployment/opsdeck --replicas=0 -n opsdeck
```

This also releases the attachments PVC, which is `ReadWriteOnce`. The next `helm upgrade` sets the replica count back to 1.

#### 2. Start a restore pod

The pod uses the backup image, the backup Secret and the attachments PVC:

```yaml
# restore-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: opsdeck-restore
  namespace: opsdeck
spec:
  restartPolicy: Never
  # serviceAccountName: opsdeck-backup   # when using IRSA
  containers:
    - name: restore
      image: pixelotes/opsdeck-backup:latest
      command: ["sleep", "86400"]
      envFrom:
        - secretRef:
            name: opsdeck-backup
      env:
        - name: DATABASE_URL
          value: postgresql://opsdeck:password@my-aurora-db.aws.com:5432/opsdeck
        # - name: AWS_DEFAULT_REGION
        #   value: eu-west-1
      volumeMounts:
        - name: attachments
          mountPath: /restore-target/attachments
  volumes:
    - name: attachments
      persistentVolumeClaim:
        claimName: opsdeck-attachments-pvc
```

```bash
kubectl apply -f restore-pod.yaml
kubectl exec -it opsdeck-restore -n opsdeck -- sh
```

#### 3. Restore the snapshot

Inside the pod:

```bash
restic snapshots --tag opsdeck
restic restore <snapshot-id> --target /restore     # or: restic restore latest --tag opsdeck --target /restore
ls /restore/backup/database /restore/backup/files
```

The snapshot keeps its original paths, so the dump is in `/restore/backup/database/` and the attachments are in `/restore/backup/files/`.

#### 4. Restore the database

Recreate the database (as a user allowed to drop and create it), then load the dump:

```bash
psql "postgresql://opsdeck:password@my-aurora-db.aws.com:5432/postgres" -c "DROP DATABASE opsdeck;"
psql "postgresql://opsdeck:password@my-aurora-db.aws.com:5432/postgres" -c "CREATE DATABASE opsdeck OWNER opsdeck;"

gunzip -c /restore/backup/database/opsdeck-*.sql.gz | psql "$DATABASE_URL"
```

#### 5. Restore the attachments

```bash
rm -rf /restore-target/attachments/*
cp -a /restore/backup/files/. /restore-target/attachments/
```

#### 6. Clean up and start OpsDeck

```bash
exit
kubectl delete pod opsdeck-restore -n opsdeck
kubectl scale deployment/opsdeck --replicas=1 -n opsdeck
```

On startup OpsDeck applies any migrations newer than the restored database.

### Other options

- For external PostgreSQL (RDS/Aurora), the provider's automated snapshots and point-in-time recovery complement the CronJob.
- Volume-level tools such as Velero or your storage provider's snapshots can back up the PVCs as well.
- `scripts/bcdr-export.py` exports the whole database to Excel files for offline review; see [Helper scripts](../user-guide/data-import.md#helper-scripts). It does not replace a database backup.

## Verification

After any restore, verify:

1. Application starts without migration errors.
2. Dashboard loads with correct data.
3. Attachments are accessible (open any asset or policy with uploaded files).
4. Audit log contains expected history.
5. API connectors still run. If they fail to decrypt their credentials, the `DATA_ENCRYPTION_KEY` (or `SECRET_KEY`) differs from the one in use when the backup was taken.
