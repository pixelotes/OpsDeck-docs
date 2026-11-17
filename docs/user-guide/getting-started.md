# Getting Started

This guide walks you through your first steps after deploying OpsDeck — from logging in to understanding the core navigation and setting up your organization.

## First login

After deployment, open your OpsDeck instance and log in with the admin credentials configured during installation:

- **Default email:** `admin@example.com`
- **Default password:** `admin123`

You'll be asked to change the default password before you can continue. If Google OAuth is configured, the login page also shows a Google sign-in button.

## Navigation overview

OpsDeck's interface is organized around a left sidebar. You only see the sections your permissions allow. Click a section heading to expand it; one section is open at a time.

| Section | What you'll find |
|---|---|
| **Health Dashboard** | Organisation-wide risk, compliance and operations overview (see [Dashboard](dashboard.md)) |
| **Procurement** | Requirements, evaluations, suppliers, contacts, contracts |
| **Core Inventory** | Services, assets, peripherals, brands, models, software, licenses, subscriptions, CMDB, credentials, certificates |
| **Operations** | Ops & Finance dashboard, renewals, warranties, asset reports, changes, requests, incidents, maintenance, disposals, erasure log, security activities, BCDR |
| **Roadmaps** | Strategic roadmaps with goals and initiatives (see [Roadmaps](roadmaps.md)) |
| **Risk & Governance** | Risk dashboard, risk register, risk catalog, risk assessments, audits |
| **Compliance** | Compliance dashboard, frameworks, asset inventory, policy acknowledgements, vendor compliance, supplier review templates, user access review, UAR automation, drift detection |
| **Knowledge & Policy** | Documentation, links, policies, courses |
| **Finance** | Purchases, budgets, cost centers, payment methods, spend analysis, depreciation, exchange rates |
| **HR & People** | HR dashboard, onboarding and offboarding, role profiles, checklists, history, org chart, hiring |
| **Communications** | Campaigns, email templates |
| **Administration** | Users, groups, permissions, locations, tags, data import, Entra ID sync, audit log, tree view |
| **Settings** | Organization, custom properties, notifications, event rules, API connectors |

When the enterprise edition is enabled, an **Enterprise** section also appears for administrators.

**Collapsing the sidebar.** On desktop, click the handle on the sidebar's edge to collapse it and give pages more room. While it is collapsed, move the pointer to the left edge of the screen to show it temporarily. OpsDeck remembers whether the sidebar was collapsed, and which section was open, the next time you load a page. On mobile, open the sidebar with the menu button in the top bar; it opens over the page, and you close it by tapping outside it or pressing Esc.

The top bar contains:

- **Search**: universal search across assets, users, risks and other records.
- **Notification bell**: items that need your action (see [Dashboard](dashboard.md#notification-bell)).
- **Theme toggle**: switch between light and dark mode.
- **User menu** (your name):

    | Item | Purpose |
    |---|---|
    | **My Dashboard** | Your personal tasks, tickets and resources. |
    | **My Courses** | Your assigned training. |
    | **Change Password** | Change your password. |
    | **My Supplier Reviews** | Supplier review questionnaires you own (see [Supplier Reviews](supplier-reviews.md)). |
    | **My Policies** | Policies you have to read and acknowledge. |
    | **API Key** | Generate a token for the [REST API](api.md). |
    | **Logout** | Sign out. |

## Core concepts

Before diving in, understand these concepts that appear throughout OpsDeck:

**Compliance links.** Any entity (asset, policy, service, supplier) can be linked to a framework control as evidence. This is the backbone of compliance management — link evidence continuously, not just during audits.

**Tags.** Flexible labels that can be attached to most entities for custom categorization and filtering.

**Custom properties.** Assets, users, and peripherals support custom fields defined at the organization level (**Settings → Custom Properties**).

**Audit trail.** Every creation, update, and deletion is logged with the user, timestamp, and changed fields. This trail is immutable and cannot be deleted from the UI.

## Initial configuration checklist

Complete these steps to set up your organization:

### 1. Organization settings

Navigate to **Settings → Organization** and set:

- Legal information: legal name and tax ID.
- Domain configuration: your primary domain and email domains.

Then configure email and webhook notifications in **Settings → Notifications**.

### 2. Locations

Navigate to **Administration → Locations** and create your physical and logical locations:

- Office sites (HQ, branches, data centers).
- Remote locations if tracking remote worker assets.
- Each location has an address and a timezone.

### 3. Cost centers

Navigate to **Finance → Cost Centers** and create departments or budget centers:

- Used for asset assignment, budget allocation, and reporting.
- Map to your organization's financial structure.

### 4. Users and groups

Navigate to **Administration → Users** and create your team:

1. Click **Add User** and provide name, email and the other details. See [Users](users.md).
2. Create **Groups** (**Administration → Groups**) and grant them module access in **Administration → Permissions**.
3. If using Google OAuth, users can log in immediately with their Google email.

### 5. Compliance frameworks

Navigate to **Compliance → Frameworks** to set up your compliance requirements:

1. Click **Create New Framework** to create one (for example ISO 27001, SOC 2, or your own).
2. Review the controls — each one represents a requirement you need evidence for.
3. Start linking existing assets, policies, and services to controls.

### 6. Suppliers

Navigate to **Procurement → Suppliers** and register your key vendors:

1. Add supplier details, compliance status, and contacts.
2. Link contracts and subscriptions.
3. Set up renewal tracking.

## What's next

With the basics configured, explore these workflows:

- **[Hardware Assets](assets.md)** — start tracking your asset inventory.
- **[Compliance Dashboard](compliance.md)** — understand your compliance posture.
- **[User Access Reviews](uar.md)** — automate access governance.
- **[Data Import (CLI)](data-import.md)** — bulk import existing data from CSV.
