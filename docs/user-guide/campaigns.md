# Campaigns

Send one-off emails to many users at once, for example announcements, policy communications or awareness reminders.

Campaigns are part of the **Communications** module.

## Creating a campaign

1. Navigate to **Communications → Campaigns**.
2. Click **New Campaign**.
3. Fill in the four sections:
    1. **Email Content**: **Campaign Title**, **Email Subject** and **Email Body** (rich text). The **Template Variables** panel lists the placeholders you can use, such as `{{ user.name }}`, `{{ user.email }}`, `{{ user.job_title }}`, `{{ user.department }}` and `{{ today }}`.
    2. **Audience**: tick **Send to All Active Users**, or select users and groups.
    3. **Schedule**: a **Send Date & Time**. Leave it empty to send as soon as the campaign is scheduled.
    4. **Tags** (optional).
4. Click **Create Draft**.

## Sending

A campaign starts as a draft, which you can still edit. From the campaign page:

- **Schedule & Send** queues one email per recipient for the chosen time.
- **Send Now** sends a scheduled campaign immediately.
- **Cancel** stops emails that have not been sent yet.
- **Retry Failed** queues the failed emails again.
- **Finish** closes an ongoing campaign.

The campaign page shows how many emails are in total, sent, pending and failed, the list of recipients with their delivery status, and an email preview. Emails are sent by the background scheduler through the configured SMTP server.

| Status | Meaning |
|---|---|
| **Draft** | Being prepared. Can be edited. |
| **Scheduled** | Queued for sending. |
| **Ongoing** | Emails are being sent. |
| **Finished** | All emails processed. |
| **Archived** | Hidden from the active list. |

To reuse a campaign, use **Clone** in the campaign list.

## Email templates

Reusable emails, for example those sent by onboarding role profiles, are managed in **Communications → Email Templates**. Campaigns do not use templates: each campaign has its own subject and body.
