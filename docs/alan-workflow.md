# Alan's Workflow Guide

## Overview

Alan is the primary user of the AT System. His job is to review incoming fence leads, approve estimates, and send packages to customers via GHL (Go High Level).

---

## 1. Finding Pending Work

### Queue Tab (Recommended for daily triage)
- Go to the **Leads** page and click **Queue**
- Leads are sorted by priority: **HOT → HIGH → MEDIUM → LOW**
- Within the same priority, newest submitted leads appear first
- Work top-to-bottom — highest priority leads first

### Kanban Tab (Good for visualizing pipeline)
- Each column represents a lead's current status:

| Column | Meaning |
|---|---|
| **No Address** | Lead came in without a street address — can't estimate |
| **Needs Info** | Missing required data (name, phone, etc.) |
| **Pending** | Has enough data, estimate not yet generated |
| **Green Zone** | In service area, estimate ready |
| **Yellow Zone** | Further out zone, estimate ready |
| **Red Zone** | Far zone, estimate ready |
| **Follow Up** | Previously contacted, waiting |
| **Estimate Sent** | All 3 packages sent to customer, waiting on response |

- Cards are sorted **newest submitted first** within each column

---

## 2. Reviewing a Lead

Click any lead card to open the **Lead Detail Page**.

### What to check:
1. **Contact Info** — Is the name, phone, and address correct?
2. **Zone & Estimate** — Did the system auto-generate an estimate? Is the zone right?
3. **GHL Messages** — Has the customer replied?
4. **Additional Services** — Were extras (gates, removal, etc.) pulled in correctly from GHL?

---

## 3. Editing a Lead

### Contact Info (name, phone, address)
1. In the **Contact Info** card, click **Edit**
2. Update name, phone, and/or address
3. Click **Save**
   - If the address changed, the system automatically re-extracts the zip code and re-runs the estimate

### Additional Services (gates, removal, etc.)
1. In the **Additional Services** card, check the **Edit** checkbox
2. Override any auto-populated values from GHL
3. Values save when you leave the field (or submit the estimate)

---

## 4. Sending Estimates

### Normal flow (customer has responded)
1. Open the lead detail page
2. Review the 3 tier cards: **Essential**, **Signature**, **Legacy**
   - Each shows a total price and a monthly price (total ÷ 21)
3. If `customer_responded` is marked true in GHL, the **"Approve & Send All Packages"** button is active
4. Click the button — all 3 tiers are sent to the customer via GHL

### Force send (override — customer hasn't responded yet)
1. Check the **"Force send"** checkbox on the estimate page
2. The approve button becomes active regardless of customer response status
3. Click **"Approve & Send All Packages"**

---

## 5. Estimate History

- Scroll to the **Estimate History** card on the lead detail page
- Click **Load History** to see all previous estimates for that lead
- Useful for checking when estimates were last run and what prices were sent

---

## 6. Common Scenarios

### Lead came in with no address
- Lead lands in **No Address** column
- Alan contacts the customer to get the address
- Once address is added via Edit → Save, the system re-estimates and re-routes the kanban column automatically

### Customer is in an unexpected zone
- Open the lead, check the **Zone** shown on the estimate
- If the address looks wrong, edit it to correct the zip
- The estimate re-runs automatically on save

### Need to send before customer replies
- Use the **Force send** checkbox to bypass the guard
- Use sparingly — intended for follow-up outreach or special cases

### Estimate looks wrong
- Check that **Additional Services** values pulled in from GHL are accurate
- Use the Edit override if needed, then re-run the estimate from the estimate detail page
