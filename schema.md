# Airtable Schema Reference

This document describes the **minimum Airtable table and field structure required** for the Eventbrite → Airtable data pipeline to function correctly.

Only tables and fields **directly used by the integration script** are fully specified here. Additional tables may exist in the production base but are not required to run this pipeline.

---

## Table: Events

Stores high-level information about each Eventbrite event.

### Fields

| Field Name | Type | Example | Notes |
|-----------|------|--------|------|
| Event Name | Single line text | Bassline Surge | Primary event identifier |
| Event Date | Date | 10-11-2024 | Date of Event |
| Venue | Linked record → Venues | Glendinning Rock Garden | Many events → one venue |
| Artists | Linked record → Artists | Prozey | One event → many artists |
| Promoters | Linked record → Promoters | Shane G | Many events → many promoters |
| Subcontractors | Linked record → Subcontractors | Photographer | Many events → many subcontractors |
| Online Tickets Sold | Roll Up → Tickets Sales | 100 | Counts the number of tickets sold for an event |
| Online Ticket Sales | Roll Up → Tickets Sales | $1000.00 | Sums the total amount made from ticket sales for an event |

---

## Table: Venues

Stores unique venues associated with events.

### Fields

| Field Name | Type | Example | Notes |
|-----------|------|--------|------|
| Venue Name | Single line text | The Fillmore Philadelphia | Used for upsert logic |
| Address | Long text | 29 E Allen St | |
| Capacity | Numeric | 200 | |
| Rental Cost | Currency | $800.00 | |
| Contact Name | Single line text | US | |
| Contact Email | Email |  |  |
| Contact Phone | Phone |  |  |
| Events Hosted | Linked record → Events | Bassline Surge | Reverse relationship |
| Contracts | Linked record → Contracts | File | One Venue → Many Contracts |

---

## Table: Ticket Sales

Stores ticket sales grouped at the order level.

### Fields

| Field Name | Type | Example | Notes |
|-----------|------|--------|------|
| Order ID | Single line text | ABC123XYZ | EventBrite Order ID |
| ID | Single line text | ABC123XYZ | Fractal Factory Order ID |
| First Name | Single line text | John |  |
| Last Name | Single line text | Doe |  |
| Email | Email |  |  |
| Event | Linked record → Events | Fractal Factory: Summer Showcase | One ticket → one event |
| Ticket Type | Single line text | TIER 1 | |
| Quantity | Number | 2 | |
| Gross Revenue | Currency | 50.00 | Supports free & paid |
| Channel | Single line text | Eventbrite | |
| Purchase Date | Date | 2025-05-31 | |

---

## Relationships Overview

- One **Venue** can host many **Events**
- One **Event** can have many **Ticket Sales**
- Ticket Sales are linked to Events via Airtable linked records

---

## Contextual Tables (Not Required by Script)

The production Airtable base may also include additional tables such as:

- Expenses
- Marketing Campaigns
- Artists
- Promoters
- Contacts
- Equipment
- Subcontractors
- Expenses

These tables are **not required** for the data pipeline described in this repository and are therefore not fully specified here.

---

## Notes

- Field names are case-sensitive where referenced by the script.
- Linked-record relationships must already exist in Airtable prior to running the pipeline.
- Additional fields may exist in the base without impacting script execution.
