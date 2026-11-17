# Kubernetes Deployment (Helm)

Deploy OpsDeck on Kubernetes using the Helm chart in the `helm/` directory of the repository. The chart supports an internal or external PostgreSQL database, persistent storage for logs and attachments, exposure through Ingress or the Gateway API, a scheduled backup job and an optional Filebeat logging sidecar.

## Prerequisites

- Kubernetes cluster v1.21+ (the backup job uses the `batch/v1` CronJob API)
- Helm 3.0+
- `kubectl` configured for your cluster
- Gateway API CRDs (`gateway.networking.k8s.io/v1`), only if you use `gatewayApi.enabled`

## Chart structure

```
helm/
├── Chart.yaml          # Chart metadata and PostgreSQL subchart dependency
├── Chart.lock
├── values.yaml         # Default configuration
├── charts/             # Bundled Bitnami PostgreSQL subchart (15.5.38)
└── templates/
    ├── _helpers.tpl
    ├── deployment.yaml            # OpsDeck pod (and the Filebeat sidecar when enabled)
    ├── service.yaml               # Service on port 5000
    ├── ingress.yaml               # Ingress (ingress.enabled)
    ├── httproute.yaml             # Gateway API HTTPRoute (gatewayApi.enabled)
    ├── db-service.yaml            # <release>-db Service (database.type: internal)
    ├── logs-pvc.yaml              # PVC for /app/logs
    ├── attachments-pvc.yaml       # PVC for /app/data/attachments
    ├── configmap-logging.yaml     # filebeat.yml (loggingSidecar.enabled)
    ├── configmap-backup.yaml      # backup.sh (backup.enabled)
    ├── cronjob-backup.yaml        # Backup CronJob (backup.enabled)
    └── serviceaccount-backup.yaml # Backup ServiceAccount (backup.serviceAccount.create)
```

## Installation

### 1. Create namespace and secrets

Create a Secret with the application settings and reference it in `existingSecret`. The chart loads it with `envFrom`, so **every key becomes an environment variable of the same name**: the keys must be variable names from [Environment Variables](environment-variables.md), such as `SECRET_KEY`.

```bash
kubectl create namespace opsdeck

kubectl create secret generic opsdeck-secrets \
  --from-literal=SECRET_KEY="$(openssl rand -hex 32)" \
  --from-literal=DATA_ENCRYPTION_KEY="$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" \
  --from-literal=DEFAULT_ADMIN_EMAIL='admin@yourcompany.com' \
  --from-literal=DEFAULT_ADMIN_INITIAL_PASSWORD='SecurePassword123!' \
  -n opsdeck
```

Add SSO credentials (`GOOGLE_OAUTH_*`, `AZURE_OAUTH_*`), SMTP settings and `SLACK_BOT_TOKEN` to the same Secret as needed.

Variables under `env` in `values.yaml`, and the `DATABASE_URL` the chart builds, are set with `env`, which takes precedence over `envFrom`. A `DATABASE_URL` key in the Secret is ignored when `database.type` is `internal` or `external`.

### 2. Configure values

```yaml
existingSecret: opsdeck-secrets

env:
  FLASK_ENV: "production"
  TRUST_PROXY: "1"
  APP_BASE_URL: "https://opsdeck.yourcompany.com"
  TIMEZONE: "Europe/Madrid"
```

The image sets `FLASK_APP=run:app`, which the `flask db upgrade` run on startup needs. Set `TRUST_PROXY` when traffic arrives through an Ingress or Gateway, so OAuth redirect URIs and email links use the public host and `https`.

The key decision is the database mode: **external** (an existing database such as RDS or Aurora) or **internal**.

=== "External PostgreSQL (RDS/Aurora)"

    ```yaml
    database:
      type: external
      external:
        host: "my-aurora-db.aws.com"
        port: 5432
        username: "opsdeck"
        database: "opsdeck"
        existingSecret:
          name: "opsdeck-db-secret"
          key: "password"
    ```

    The password is read from `existingSecret.name` / `existingSecret.key` into `DB_PASSWORD_RAW`, and the chart builds `DATABASE_URL` as `postgresql://<username>:$(DB_PASSWORD_RAW)@<host>:<port>/<database>`. A password with characters that are special in URLs (`@`, `:`, `/`, `?`, `#`) must be stored URL-encoded.

    ```bash
    kubectl create secret generic opsdeck-db-secret \
      --from-literal=password='db-password' -n opsdeck
    ```

=== "Internal PostgreSQL"

    ```yaml
    database:
      type: internal

    postgresql:
      enabled: true
      auth:
        username: opsdeck
        password: opsdeck-db-password
        database: opsdeck
    ```

    In this mode the chart creates a Service named `<release>-db` on port 5432 and points `DATABASE_URL` at it, with the credentials from `postgresql.auth`. That Service selects the primary pod of the bundled Bitnami PostgreSQL subchart, which this mode needs (`postgresql.enabled: true`, the default). The chart refuses to render with `database.type: internal` and the subchart turned off.

### 3. Configure persistent storage

```yaml
persistence:
  logs:
    enabled: true
    size: 500Mi
    storageClass: ""       # Uses cluster default
    existingClaim: ""      # Or reference an existing PVC

  attachments:
    enabled: true
    size: 5Gi
    storageClass: ""
    existingClaim: ""
```

The chart creates both PVCs with access mode `ReadWriteOnce`. Logs are mounted at `/app/logs` and attachments at `/app/data/attachments`.

### 4. Install

```bash
helm dependency build ./helm   # only needed when postgresql.enabled is true

helm upgrade --install opsdeck ./helm \
  --namespace opsdeck \
  -f my-values.yaml \
  --set image.tag=latest
```

On startup the container applies database migrations, creates the initial admin user and seeds the production frameworks before gunicorn starts. The startup probe allows up to 5 minutes for this.

### 5. Verify

```bash
kubectl get pods -n opsdeck
kubectl logs -f deployment/opsdeck -n opsdeck
```

## Exposing OpsDeck

The Service is a `ClusterIP` on port 5000 (`service.type`, `service.port`). Expose it with an Ingress or a Gateway API HTTPRoute. Both send every path (`/`, prefix match) to the Service.

### Ingress

```yaml
ingress:
  enabled: true
  className: nginx
  host: opsdeck.yourcompany.com
  tls:
    - secretName: opsdeck-tls
      hosts:
        - opsdeck.yourcompany.com
```

The chart takes a single `host`. It has no `annotations` value, so annotations such as `cert-manager.io/cluster-issuer` cannot be set through the chart; create the TLS Secret yourself or annotate the Ingress afterwards.

### Gateway API

```yaml
gatewayApi:
  enabled: true
  gatewayName: my-gateway     # Existing Gateway in the cluster
  namespace: default          # Namespace of that Gateway
  hostname: opsdeck.yourcompany.com
```

This creates an `HTTPRoute` attached to the existing Gateway. TLS is handled by the Gateway's listener, and the Gateway must allow routes from the OpsDeck namespace.

## Backups

Set `backup.enabled: true` to add a CronJob that dumps the database with `pg_dump` and backs up the dump together with the attachments PVC to a restic repository, typically in S3. See [Backup & Restore](backup-restore.md#kubernetes-helm-backup-cronjob) for how it works and how to restore.

```yaml
backup:
  enabled: true
  schedule: "0 3 * * *"
  existingSecret: opsdeck-backup
  retention:
    keepDaily: 7
    keepWeekly: 4
    keepMonthly: 6
```

The Secret must hold `RESTIC_REPOSITORY` and `RESTIC_PASSWORD`, plus `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` unless you use IRSA:

```bash
kubectl create secret generic opsdeck-backup \
  --from-literal=RESTIC_REPOSITORY='s3:s3.amazonaws.com/my-bucket/opsdeck' \
  --from-literal=RESTIC_PASSWORD="$(openssl rand -hex 32)" \
  --from-literal=AWS_ACCESS_KEY_ID='AKIA...' \
  --from-literal=AWS_SECRET_ACCESS_KEY='...' \
  -n opsdeck
```

On EKS you can use IAM Roles for Service Accounts (IRSA) instead of access keys:

```yaml
backup:
  enabled: true
  existingSecret: opsdeck-backup   # RESTIC_REPOSITORY and RESTIC_PASSWORD only
  aws:
    useIRSA: true
    region: eu-west-1
  serviceAccount:
    create: true
    annotations:
      eks.amazonaws.com/role-arn: arn:aws:iam::123456789012:role/opsdeck-backup
```

## Logging sidecar

Set `loggingSidecar.enabled: true` to run a Filebeat container next to OpsDeck. It reads the `*.log` and `*.json` files in `/app/logs` from the logs PVC (so `persistence.logs.enabled` must be on), parses them as NDJSON and ships them to Elasticsearch.

```yaml
loggingSidecar:
  enabled: true
  elasticsearch:
    host: elasticsearch.logging.svc
    port: 9200
    protocol: https
    existingSecret: opsdeck-elasticsearch   # keys ELASTICSEARCH_USERNAME and ELASTICSEARCH_PASSWORD
  config: {}                                # extra Filebeat settings, appended to filebeat.yml
```

## ArgoCD deployment

For GitOps workflows, create an ArgoCD Application manifest:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: opsdeck
  namespace: argocd
spec:
  project: default
  source:
    repoURL: 'https://github.com/pixelotes/opsdeck.git'
    targetRevision: HEAD
    path: helm/
    helm:
      valueFiles:
        - values.yaml
  destination:
    server: 'https://kubernetes.default.svc'
    namespace: opsdeck
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
    syncOptions:
      - CreateNamespace=true
```

```bash
kubectl apply -f application.yaml
```

## Replicas and upgrades

The chart runs a single replica (`replicas: 1` is fixed in the template) with the `Recreate` deployment strategy. The logs and attachments PVCs are `ReadWriteOnce`, so two OpsDeck pods cannot share them during a rolling update; `Recreate` stops the old pod before starting the new one. Expect a short downtime on every upgrade while the new pod runs migrations and starts.

To add capacity, raise `GUNICORN_WORKERS` and `GUNICORN_THREADS` in `env` rather than adding replicas.

The OpsDeck container has fixed resources: requests `100m` CPU / `128Mi` memory, limits `500m` CPU / `512Mi` memory. The startup, liveness and readiness probes are TCP checks on port 5000.

## values.yaml reference

| Key | Default | Description |
|---|---|---|
| `image.repository` | `pixelotes/opsdeck` | Container image |
| `image.tag` | `latest` | Image tag |
| `image.pullPolicy` | `IfNotPresent` | Pull policy |
| `service.type` | `ClusterIP` | Service type |
| `service.port` | `5000` | Service port |
| `database.type` | `internal` | `internal` or `external` |
| `database.external.host` | `mi-aurora-db.aws.com` | External database host |
| `database.external.port` | `5432` | External database port |
| `database.external.username` | `admin` | External database user |
| `database.external.database` | `opsdeck_prod` | External database name |
| `database.external.existingSecret.name` | `secreto-kubernetes` | Secret holding the database password |
| `database.external.existingSecret.key` | `password` | Key of the password in that Secret |
| `postgresql.enabled` | `true` | Deploy the Bitnami PostgreSQL subchart (required by `database.type: internal`) |
| `postgresql.auth.username` | `opsdeck` | Database user (also used in `internal` mode) |
| `postgresql.auth.password` | `opsdeck_password` | Database password (also used in `internal` mode) |
| `postgresql.auth.database` | `opsdeck_db` | Database name (also used in `internal` mode) |
| `postgresql.primary.persistence.enabled` | `true` | Persist the subchart's data |
| `postgresql.primary.persistence.size` | `1Gi` | Subchart volume size |
| `persistence.logs.enabled` | `true` | Mount a PVC at `/app/logs` |
| `persistence.logs.size` | `500Mi` | Log volume size |
| `persistence.logs.storageClass` | `""` | Storage class (empty: cluster default) |
| `persistence.logs.existingClaim` | `""` | Use an existing PVC instead of creating one |
| `persistence.attachments.enabled` | `true` | Mount a PVC at `/app/data/attachments` |
| `persistence.attachments.size` | `5Gi` | Attachment volume size |
| `persistence.attachments.storageClass` | `""` | Storage class (empty: cluster default) |
| `persistence.attachments.existingClaim` | `""` | Use an existing PVC instead of creating one |
| `ingress.enabled` | `false` | Create an Ingress |
| `ingress.className` | `nginx` | Ingress class |
| `ingress.host` | `opsdeck.local` | Host name |
| `ingress.tls` | `[]` | TLS entries (`secretName`, `hosts`) |
| `gatewayApi.enabled` | `false` | Create a Gateway API HTTPRoute |
| `gatewayApi.gatewayName` | `my-gateway` | Name of the existing Gateway |
| `gatewayApi.namespace` | `default` | Namespace of the Gateway |
| `gatewayApi.hostname` | `opsdeck.example.com` | Host name of the route |
| `env` | `FLASK_ENV: production` | Extra environment variables, as a map |
| `existingSecret` | `""` | Secret loaded with `envFrom`; keys are environment variable names |
| `backup.enabled` | `false` | Create the backup CronJob |
| `backup.schedule` | `0 3 * * *` | Cron schedule (daily at 03:00) |
| `backup.image.repository` | `pixelotes/opsdeck-backup` | Backup image (Alpine with `pg_dump` and restic) |
| `backup.image.tag` | `latest` | Backup image tag |
| `backup.existingSecret` | `""` | Secret with `RESTIC_REPOSITORY`, `RESTIC_PASSWORD` and, without IRSA, `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` |
| `backup.aws.useIRSA` | `false` | Do not pass AWS keys; restic uses the IRSA web identity token instead |
| `backup.aws.region` | `""` | Sets `AWS_DEFAULT_REGION` when not empty |
| `backup.serviceAccount.create` | `false` | Create a ServiceAccount for the backup job |
| `backup.serviceAccount.name` | `""` | ServiceAccount name; defaults to `<release>-backup` when `create` is true. With `create: false`, the name of an existing ServiceAccount |
| `backup.serviceAccount.annotations` | `{}` | Annotations, such as `eks.amazonaws.com/role-arn` for IRSA |
| `backup.retention.keepDaily` | `7` | Daily snapshots kept |
| `backup.retention.keepWeekly` | `4` | Weekly snapshots kept |
| `backup.retention.keepMonthly` | `6` | Monthly snapshots kept |
| `backup.resources` | requests `100m`/`128Mi`, limits `500m`/`512Mi` | Backup container resources |
| `loggingSidecar.enabled` | `false` | Add the Filebeat sidecar |
| `loggingSidecar.image.repository` | `docker.elastic.co/beats/filebeat` | Filebeat image |
| `loggingSidecar.image.tag` | `8.5.1` | Filebeat image tag |
| `loggingSidecar.image.pullPolicy` | `IfNotPresent` | Pull policy |
| `loggingSidecar.elasticsearch.host` | `elasticsearch` | Elasticsearch host |
| `loggingSidecar.elasticsearch.port` | `9200` | Elasticsearch port |
| `loggingSidecar.elasticsearch.protocol` | `http` | `http` or `https` |
| `loggingSidecar.elasticsearch.existingSecret` | `""` | Secret with `ELASTICSEARCH_USERNAME` and `ELASTICSEARCH_PASSWORD` |
| `loggingSidecar.config` | `{}` | Extra Filebeat configuration appended to `filebeat.yml` |
