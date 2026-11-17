# Microsoft Entra ID

OpsDeck can use Microsoft Entra ID in two independent ways:

- **Sign in with Microsoft**: SSO for people who already have an OpsDeck account.
- **User sync**: create and update OpsDeck users from Entra groups.

Both use the same app registration, configured with the `AZURE_OAUTH_*` environment variables.

## App registration

In the Entra admin center, go to **App registrations → New registration**:

1. **Supported account types**: *Accounts in this organizational directory only* (single tenant).
2. **Redirect URI** (Web): `https://your-domain/login/azure/authorized`.
3. Under **Certificates & secrets**, create a client secret.
4. Set these environment variables:

   | Variable | Value |
   |---|---|
   | `AZURE_OAUTH_TENANT_ID` | Directory (tenant) ID |
   | `AZURE_OAUTH_CLIENT_ID` | Application (client) ID |
   | `AZURE_OAUTH_CLIENT_SECRET` | The client secret value |

Only single-tenant setups are supported. A tenant ID of `common`, `organizations` or `consumers` disables Microsoft sign-in and logs a warning.

## Sign in with Microsoft

Once the variables are set, the login page shows **Sign in with Microsoft** next to the Google button, if Google is configured.

- SSO **does not create accounts**. The person must already exist in OpsDeck, either created by hand or by the user sync.
- On the first sign-in, the account is matched by the Entra `userPrincipalName` against the user's email. The admin-editable `mail` attribute is never used. OpsDeck then stores the Entra object ID and matches by it from then on.
- Archived and *directory-only* users are refused (see [Users & Groups](users.md#directory-only-users)).

## User sync

The sync reads the members of one or more Entra groups (nested groups included) through Microsoft Graph and reconciles OpsDeck users against them. It is a pull sync run by OpsDeck, not SCIM.

### Graph permissions

Add these **application** permissions to the app registration and grant admin consent:

- `User.Read.All`
- `GroupMember.Read.All`

### Settings

Configure the sync under **Administration → Entra ID Sync**. It is disabled by default.

| Setting | Description |
|---|---|
| **Groups** | Object IDs of the Entra groups whose members are synced. |
| **Default role** | Role given to users the sync creates. |
| **New users can sign in** | Off by default: new users are *directory only*. They can be linked to assets, licences and suppliers, but cannot sign in. Changing this setting never changes existing users. |
| **Access groups** | Optional. When set, members of these groups can sign in and every other synced user is directory only. Each sign-in change is shown in the preview with a warning. |
| **Schedule** | Off, daily at HH:MM, or every N hours. |
| **Safety threshold** | A scheduled run aborts without changes, and emails the admins, if it would archive (or remove sign-in access from) more than this percentage of synced users. Default 10%. |

### What a run does

- **Creates** missing users with the default role and no password. No email is sent to them.
- **Updates** the name, department, job title and manager.
- **Archives** Entra-linked users who left the groups or were disabled in Entra. Users are never deleted, and they are unarchived if they come back.
- Leaves **local accounts** that were never linked to Entra, such as the break-glass admin, untouched.

If any configured group cannot be read, the run aborts. A Graph outage can never look like "everyone left".

### Running it

- **Sync now** on the settings page first shows a **dry-run preview** of every create, update, archive and unarchive, with the per-user changes. It applies them only when you confirm. If Entra changed in the meantime, it refuses and asks you to preview again.
- Scheduled runs apply directly, within the safety threshold.
- From the command line:

  ```bash
  flask entra-sync --dry-run
  flask entra-sync
  ```

  `--force` skips the safety threshold.

Every run is listed in the run history on the settings page and recorded in the audit log.
