# Leads Kanban & Queue Page — Logic Reference

**File:** `frontend/app/(dashboard)/leads/page.tsx`

---

## Overview

The Leads page is the main command centre. It shows all active (non-archived) leads in two views:
- **Kanban** — drag-and-drop board with 8 columns
- **Queue** — prioritised flat list with inline approve action

Both views pull from the same `leads` + `estimates` data loaded on mount.

---

## Data Loading

On mount, two API calls fire in parallel:

```
GET /api/leads?limit=200     → all non-archived leads
GET /api/estimates?limit=200 → all estimates (newest first, one per lead)
```

The estimates are reduced into a `Map<lead_id, Estimate>` (`estimateMap`). Only the **most recent** estimate per lead is kept (first one seen per `lead_id`).

A background `setInterval` re-runs both calls every **5 minutes** to stay current without a manual refresh.

---

## Column Assignment — `getKanbanStatus(lead, estimateMap)`

This function determines which column a lead belongs to. Rules run **top to bottom, first match wins**:

| Priority | Condition | Column |
|---|---|---|
| 1 | `lead.status === "sent"` OR `lead.status === "approved"` OR `estimate.status === "approved"` | **Estimate Sent** |
| 2 | `lead.kanban_column` is set (manual drag override) | **That column** |
| 3 | `lead.address` is blank | **No Address** |
| 4 | Any tag in `NEEDS_INFO_TAGS` | **Needs More Information** |
| 5 | Any tag in `FOLLOW_UP_TAGS` | **Follow Up Quote** |
| 6 | No estimate exists | **New / Untouched** |
| 7 | `estimate._approval_status === "green"` | **Ready to Send** |
| 8 | `estimate._approval_status === "yellow"` | **Add-ons Pending** |
| 9 | `estimate._approval_status === "red"` | **Needs Review** |
| 10 | Estimate exists but no approval status | **New / Untouched** |

> **Known issue / potential improvement:** Rule 1 (sent/approved) is a hard override but it fires *before* the manual `kanban_column` drag override (rule 2). This is intentional — sent leads are locked to the Sent column. However, if a lead gets re-estimated after being sent (e.g. the VA recalculates), the `lead.status` may still be `"sent"` even though a fresh pending estimate exists. The lead will stay stuck in the Sent column visually until the status is manually changed.

---

## Columns (left to right)

| Key | Label | Color | Description |
|---|---|---|---|
| `gray` | New / Untouched | Grey | No estimate calculated yet |
| `no_address` | No Address | Purple | Missing address — zone can't be determined |
| `needs_info` | Needs More Information | Orange | Tagged: fence height, age, etc. missing |
| `green` | Ready to Send | Green | All auto-send criteria met |
| `yellow` | Add-ons Pending | Yellow | Fence quote ready, add-ons need separate pricing |
| `red` | Needs Review | Red | Outside zone, too small, 15+ yrs fence, or VA not confident |
| `follow_up` | Follow Up Quote | Sky blue | Manually tagged for follow-up |
| `sent` | Estimate Sent | Emerald | Estimate approved and delivered to customer |

### Tags that trigger column routing

```
NEEDS_INFO_TAGS  = ["Needs height", "Age of the Fence", "Needs Info", "needs_info"]
FOLLOW_UP_TAGS   = ["Follow Up Quote", "follow_up_quote", "Follow Up"]
```

These come from the GHL pipeline sync — stages and manual tags set in GHL.

---

## Kanban View

- Columns are 260px wide, horizontally scrollable
- Cards sorted within each column by **priority** (HOT → HIGH → MEDIUM → LOW)
- Drag-and-drop powered by `@dnd-kit/core` with both pointer and touch sensors
  - Drag activation: 8px distance (pointer) / 250ms delay (touch)
  - Dropping onto a column calls `PUT /api/leads/{id}/column` to persist the override
  - Optimistic update: column moves immediately in UI, reverts on API failure

### Card contents

Each card shows (when available):
1. **NEW** badge — if the lead was created after the VA's last visit
2. Contact name (or "—")
3. Priority badge (HOT / HIGH / MEDIUM / LOW)
4. Address (truncated)
5. Tier prices — E / S / L in emerald text (only if estimate has tier data)
6. Rejection reason — red text, only in the "Needs Review" column
7. GHL pipeline tags
8. Footer: "Responded" tick OR creation date + **View** button

---

## Queue View

Flat list sorted by:
1. Priority (HOT first)
2. Then column urgency order: green → yellow → needs_info → no_address → gray → follow_up → red → sent

Each row shows: priority badge · name & address · column status badge · E/S/L prices · rejection reason (red only) · customer responded indicator · action button

### Queue action button logic

| Condition | What appears |
|---|---|
| `lead.status === "sent"` or `estimate.status === "approved"` | "✓ Sent" label |
| Green/Yellow column + customer responded + estimate pending | **Approve** button |
| Green/Yellow column + no customer response | "Awaiting reply" text |
| Any other state | Nothing |

The **Approve** button in the queue calls `POST /api/estimates/{id}/approve` directly (no force-send, no tier selection — sends all 3 packages). It does NOT work if the customer hasn't responded yet — there is no force-send bypass in the queue view (only on the lead detail page).

---

## Banners

### HOT Leads Banner
Appears when any lead has `priority === "HOT"` and `status !== "sent"` and `status !== "approved"`.
- Shows count of urgent leads
- "View in Queue →" link switches to queue view

### New Leads Banner
Compares `lead.created_at` against a timestamp stored in `localStorage` (`atSystemLastVisitAt`).
- Any lead created after the last visit gets a **NEW** ring highlight on its card and a count in the banner
- The timestamp is written to localStorage 5 seconds after page load (so brief visits don't reset it) and again on unmount
- Dismissed by clicking "Dismiss" — clears badge highlights immediately

---

## Potential Improvements

### 1. Sent leads stuck in Sent column after re-estimate
If a lead is re-estimated after being sent (VA updates linear feet), `lead.status` stays `"sent"` so the new pending estimate is invisible on the kanban. **Fix:** Add a "Re-open" action to reset `lead.status` back to `"estimated"` when a new estimate is calculated.

### 2. Quick Approve in Queue ignores force-send
The queue's Approve button only fires when `lead.customer_responded === true`. There is no way to force-send from the queue — the VA must open the lead detail page. This is intentional as a safeguard but may slow down the workflow for hot leads. **Improvement:** Add a tooltip or link explaining why the button isn't showing.

### 3. Manual drag overrides persist past their usefulness
If a VA drags a lead to "Follow Up" manually, it stays there even after the customer responds and a new estimate is calculated — because rule 2 (manual column) fires before rules 6–9 (estimate-based). **Fix:** The only exception already in place is rule 1 (sent/approved always wins). Consider also clearing `kanban_column` override when a new estimate is saved.

### 4. estimateMap only keeps the most recent estimate
Only the first estimate seen per `lead_id` is stored in the map. This is fine for display but means if a lead has multiple estimates and the most recent one is `rejected`, it could appear in "Needs Review" even if there's a valid older approved one. **Fix:** Filter `estimateMap` to prefer `pending` estimates over `rejected` ones when building the map.

### 5. No live push — 5-minute polling only
New leads from GHL won't appear until the next auto-refresh or manual "Sync Now". The HOT banner only updates on refresh. **Improvement:** Add a WebSocket or Server-Sent Event channel for real-time new lead notifications.

### 6. Queue "Approve" doesn't update the Kanban column
After quick-approving in the queue, `lead.status` updates to `"sent"` locally, but if the user switches to Kanban the card is already in the right column (Estimate Sent) due to the status check. This is correct behaviour — just worth noting that both views stay in sync via the same state.
