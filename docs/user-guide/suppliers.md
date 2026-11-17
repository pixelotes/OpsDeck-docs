# Suppliers

The supplier management module tracks your vendors, their compliance status, contacts, and linked contracts and subscriptions.

## Adding a supplier

1. Navigate to **Vendors → Suppliers**.
2. Click **Add Supplier**.
3. Provide: company name, website, category, and description.
4. Set the **Owner**: the user or group accountable for the relationship. The owner is shown on the supplier list and detail page, and fills in the supplier's periodic reviews.
5. Optionally set **Review every** and **Next review** to schedule periodic reviews (see [Supplier Reviews](supplier-reviews.md)).
6. Set the **compliance status**: Approved, Pending Review, Rejected, or Not Assessed.
7. Add notes about the vendor relationship.

## Supplier contacts

Each supplier can have multiple contacts:

1. From the supplier detail page, click **Add Contact**.
2. Provide name, email, phone, and role.
3. Contacts are used for communication tracking and contract management.

## Importing owners from CSV

The supplier CSV import accepts an optional `owner` column: an active user's email or a group name. The API exposes the owner as `owner_type` (`User` or `Group`) and `owner_id`.

## Periodic reviews

Suppliers with a review interval are reviewed automatically by their owner. See [Supplier Reviews](supplier-reviews.md).

## Compliance status tracking

Supplier compliance status reflects whether the vendor meets your security and regulatory requirements:

| Status | Meaning |
|---|---|
| **Approved** | Vendor has passed security review |
| **Pending Review** | Review in progress or scheduled |
| **Rejected** | Vendor does not meet requirements |
| **Not Assessed** | No review has been conducted |

## Linking to compliance controls

Suppliers can be linked to framework controls as evidence of vendor management practices (e.g., ISO 27001 A.15 — Supplier relationships):

1. On the supplier detail page, scroll to **Compliance Links**.
2. Link to the relevant controls.
3. Add context notes about the supplier's role in satisfying the requirement.
