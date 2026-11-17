# Supplier Reviews

Periodic supplier reviews are a short questionnaire answered by the supplier's **owner**. OpsDeck opens each review before it is due, reminds the owner until it is done, and uses the completed reviews as compliance evidence.

## Before you start

On each supplier you want reviewed (**Vendors → Suppliers → Edit**):

1. Set the **Owner**: a user or a group. With a group, any member can fill in the review, and all of them are notified.
2. Set **Review every** to 3, 6, 12 or 24 months.
3. Optionally set **Next review**. If you leave it empty, OpsDeck calculates it from the last completed review, or uses today if there is none.

A supplier without a review interval is never scheduled. Start with the critical suppliers.

## How reviews are scheduled

A daily job (08:30) does the following:

- **Opens** a review for every active supplier whose next review is due within **14 days**, and emails the owner a link to it.
- **Reminds** the owner every **7 days** once a review is past its due date.

A supplier never has more than one open review at a time. You can also run the job by hand:

```bash
flask schedule-supplier-reviews
```

Set `APP_BASE_URL` (see [Environment Variables](../deployment/environment-variables.md)) so that the links in these emails work.

## Filling in a review

Owners find their open reviews in three places:

- A task on **My Dashboard**.
- **My Supplier Reviews** in the user menu.
- The **Reviews & Assessments** card on the supplier page. **Start review** opens one immediately, without waiting for the schedule.

Owners can fill in reviews without having access to the Compliance module.

The default questionnaire has two parts.

**1. Check**

| Question | Answers |
|---|---|
| Is the supplier still active? | Yes / No |
| Is the supplier critical? | Yes / No |

**2. Review**: seven points, each answered **OK**, **Not OK** or **N/A**, with a comment:

- Issues with the supplier
- Certifications held
- Price increases
- Changes to terms and conditions
- Data breaches
- SLAs met
- Other problems

A **Not OK** answer needs a comment.

### What happens when you submit

- The supplier's **critical** flag is updated from the check.
- The review status becomes:

  | Status | When |
  |---|---|
  | **Approved** | Every review point is OK or N/A. |
  | **Issues Found** | At least one review point is Not OK. |
  | **Supplier Inactive** | The supplier is no longer active. The review points are optional, and you can tick **Archive the supplier** to archive it on submit. |

- The **next review date** moves forward by the supplier's review interval.

Completed reviews are read-only. They keep their own copy of the questions, so later changes to a template never alter past answers.

## Review templates

Compliance editors can manage the questionnaires under **Compliance → Supplier Review Templates**:

- **Create** a template or **edit** one: add, reorder and remove questions. Each question is either a *check* or a *review* point, with optional help text. A template needs at least one review point.
- **Make default**: new reviews use the default template.
- **Archive** templates that are no longer used. The default template cannot be archived.

## Compliance evidence

Supplier reviews are stored as supplier security assessments, so they appear in the supplier's **Reviews & Assessments** card, in the security assessments list, in audit snapshots and in compliance automation rules.

- Reviews that are **open but not filled in do not count** as evidence.
- The supplier assessment rule on a control has a **Which suppliers** option:

  | Option | The control passes when… |
  |---|---|
  | Any supplier | The most recent completed review is within the frequency (previous behaviour). |
  | Every active critical supplier | Each active critical supplier has a completed review within the frequency. |
  | Every active supplier | Each active supplier has a completed review within the frequency. |

## Logging an assessment by hand

Free-text assessments can still be recorded with **Log Assessment** on the supplier page, for example to attach a third-party audit report.
