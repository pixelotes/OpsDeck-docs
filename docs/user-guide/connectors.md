# API Connectors

API connectors pull data from external services on a schedule and store each run as a **report**. You can browse and compare reports, and use them as a data source for [User Access Reviews](uar.md).

Connectors are under **Settings → API Connectors** and require the `settings` module permission.

## Available connectors

| Connector | What it fetches | Credentials |
|---|---|---|
| **Google Workspace** | Users, groups, ChromeOS and endpoint devices | Service account JSON and a delegated admin email |
| **Microsoft 365** | Users and groups (Microsoft Graph) | This server's Entra ID app registration, or a separate tenant ID, client ID and secret |
| **GitHub** | Organization members, repositories, outside collaborators | Organization name and a personal access token |
| **JumpCloud** | Users and systems | API key, plus an optional organization ID |
| **Atlassian** | Jira users and projects, Confluence spaces | Site URL, email and API token |
| **AWS** | IAM users and roles, S3 buckets, Secrets Manager secrets | Access key ID, secret access key and region |

`seed-db-prod` (or `flask seed-connectors`) creates one connector per service. They start **disabled**, with no credentials.

## Setting up a connector

1. Open the connector and click **Configure Credentials**. Each service's form explains how to get the credentials and which permissions they need.
2. Set the **polling interval** (5 minutes to 7 days).
3. **Enable** the connector, or use **Run now** to fetch once.

A connector cannot run until its credentials are configured. When you edit the credentials later, leave a secret field blank to keep the stored secret.

### Microsoft 365 without a stored secret

If the server has the `AZURE_OAUTH_*` variables set (see [Microsoft Entra ID](entra-id.md)), tick **Use the Entra ID app registration of this server**. The connector then uses that registration, and no Microsoft secret is stored in the database. The app registration needs the Graph application permissions for the data it fetches, such as `User.Read.All` and `Group.Read.All`.

## Reports

- A background job checks every 5 minutes and runs each enabled connector whose interval has elapsed.
- Every run of every endpoint is stored as a report and compared with the previous one, so you can see what was **added, removed or changed** between runs.
- You can browse reports per endpoint and open them full screen.
- In a User Access Review, choose **Connector Report** as the data source of a dataset to compare, for example, GitHub members against your HR users.

## Credential storage

Connector secrets (client secrets, tokens, API keys, AWS secret keys and service-account keys) are **encrypted at rest**. They are never shown again after saving. Set a dedicated `DATA_ENCRYPTION_KEY` in production; see [Security Hardening](../deployment/security-hardening.md#encryption-of-stored-secrets).
