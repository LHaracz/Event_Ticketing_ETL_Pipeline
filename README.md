# Fractal Factory Productions — Eventbrite → Airtable Data Pipeline

This repository contains a Python-based data integration pipeline that synchronizes **events, venues, and ticket sales data** from Eventbrite into a structured Airtable database used by Fractal Factory Productions.

The pipeline was built to replace manual data entry and create a **centralized operational database** for event operations, performance tracking, and downstream analytics.

---

## Project Overview

Fractal Factory Productions uses Eventbrite for ticketing and Airtable as an internal operations database. Prior to this pipeline, event, venue, and ticket data were manually transferred between platforms, leading to delays, inconsistencies, and duplicate records.

This project implements a **repeatable ETL-style workflow** that programmatically pulls data from Eventbrite, normalizes it, and inserts it into relational Airtable tables with deduplication and integrity checks.

---

## What the Pipeline Does

- Retrieves active and historical **events** from Eventbrite
- Extracts and normalizes **venue information**
- Inserts or updates venues in Airtable using deduplication logic
- Retrieves **ticket sales and orders**, including free and paid tickets
- Groups ticket records by **Order ID** to prevent duplication
- Creates relational links between **Events**, **Venues**, and **Ticket Sales**
- Safely handles missing or optional API fields

---

## Data Flow

Eventbrite API
├── Events
├── Venues
└── Orders / Attendees
↓
Normalization & Deduplication
↓
Airtable Base
├── Events
├── Venues
└── Ticket Sales


---

## Key Design Decisions

- **Deduplication strategy**  
  Ticket sales are grouped and deduplicated using `Order ID` prior to insertion.

- **Upsert logic for venues**  
  Venues are matched by name before new records are created.

- **Relational data modeling**  
  Airtable linked-record fields maintain referential integrity across tables.

- **Production-safe secrets handling**  
  API keys and credentials are loaded via environment variables and excluded from version control.

- **Resilient parsing**  
  The script tolerates missing or inconsistent API fields without failing the pipeline.

---

## Technologies Used

- Python
- Eventbrite REST API
- Airtable REST API
- `requests`
- `python-dotenv`
- `dateutil`
