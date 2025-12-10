import requests
import os
from dotenv import load_dotenv
from dateutil import parser

# Load environment variables
load_dotenv()

# API tokens & base
EVENTBRITE_TOKEN = ""
AIRTABLE_TOKEN = ""
AIRTABLE_BASE_ID = ""

# Airtable endpoints
AIRTABLE_EVENTS_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Events"
AIRTABLE_VENUES_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Venues"
AIRTABLE_TICKETS_URL = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/Ticket Sales"

# Headers
EB_HEADERS = {"Authorization": f"Bearer {EVENTBRITE_TOKEN}"}
AT_HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}",
    "Content-Type": "application/json"
}

def get_eventbrite_org_id():
    url = "https://www.eventbriteapi.com/v3/users/me/organizations/"
    res = requests.get(url, headers=EB_HEADERS)
    res.raise_for_status()
    orgs = res.json()["organizations"]
    for org in orgs:
        print(f"Organization: {org['name']} – ID: {org['id']}")
    return orgs[0]["id"] if orgs else None

def get_eventbrite_events():
    organization_id = get_eventbrite_org_id()
    if not organization_id:
        raise ValueError("No organizations found for this account/token.")
    url = f"https://www.eventbriteapi.com/v3/organizations/{organization_id}/events/?status=all"
    res = requests.get(url, headers=EB_HEADERS)
    res.raise_for_status()
    events = res.json()["events"]
    events = [e for e in events if e.get("status") != "canceled"]
    print(f"Retrieved {len(events)} events from Eventbrite (excluding canceled)")
    return events

def get_eventbrite_venue(venue_id):
    url = f"https://www.eventbriteapi.com/v3/venues/{venue_id}/"
    res = requests.get(url, headers=EB_HEADERS)
    res.raise_for_status()
    return res.json()

def find_or_create_venue(venue_data):
    name = venue_data.get("name", "")
    address = venue_data["address"].get("localized_address_display", "")
    capacity = venue_data.get("capacity", "")

    params = {"filterByFormula": f"{{Venue Name}} = '{name}'"}
    search = requests.get(AIRTABLE_VENUES_URL, headers=AT_HEADERS, params=params)
    records = search.json().get("records", [])
    if records:
        return records[0]["id"]

    data = {
        "fields": {
            "Venue Name": name,
            "Address": address,
            "Capacity": capacity,
            "Contact Name": "",
            "Contact Email": "",
            "Contact Phone": ""
        }
    }
    res = requests.post(AIRTABLE_VENUES_URL, headers=AT_HEADERS, json=data)
    res.raise_for_status()
    print(f"Created new venue: {name}")
    return res.json()["id"]

def create_event_in_airtable(event, venue_id=None):
    name = event["name"]["text"]
    raw_date = event["start"]["local"]
    parsed_date = parser.parse(raw_date)
    formatted_date = parsed_date.strftime("%Y-%m-%d")

    params = {"filterByFormula": f"{{Event Name}} = '{name}'"}
    existing = requests.get(AIRTABLE_EVENTS_URL, headers=AT_HEADERS, params=params)
    if existing.json().get("records"):
        print(f"Event '{name}' already exists in Airtable. Skipping.")
        return

    fields = {
        "Event Name": name,
        "Event Date": formatted_date
    }

    if venue_id:
        fields["Venue"] = [venue_id]

    data = {"fields": fields}

    res = requests.post(AIRTABLE_EVENTS_URL, headers=AT_HEADERS, json=data)
    if not res.ok:
        print(f"Airtable Error: {res.status_code} – {res.text}")
    res.raise_for_status()
    print(f"Event '{name}' created.")

def get_airtable_event_id(event_name):
    params = {"filterByFormula": f"{{Event Name}} = '{event_name}'"}
    res = requests.get(AIRTABLE_EVENTS_URL, headers=AT_HEADERS, params=params)
    records = res.json().get("records", [])
    if records:
        return records[0]["id"]
    return None

from collections import defaultdict

def sync_ticket_sales(event):
    event_id = event["id"]
    event_name = event["name"]["text"]
    airtable_event_id = get_airtable_event_id(event_name)
    if not airtable_event_id:
        print(f"No Airtable match for Event '{event_name}' – skipping ticket sales.")
        return

    url = f"https://www.eventbriteapi.com/v3/events/{event_id}/attendees/"
    response = requests.get(url, headers=EB_HEADERS)
    response.raise_for_status()
    attendees = response.json().get("attendees", [])

    # Group by order ID
    orders = defaultdict(list)
    for attendee in attendees:
        orders[attendee["order_id"]].append(attendee)

    for order_id, order_attendees in orders.items():
        first_attendee = order_attendees[0]
        profile = first_attendee.get("profile", {})
        first_name = profile.get("first_name", "")
        last_name = profile.get("last_name", "")
        email = profile.get("email", "")
        ticket_class = first_attendee.get("ticket_class_name", "Unknown")
        channel = "Eventbrite"
        quantity = len(order_attendees)

        # Total price for this order
        gross_cents = sum(
            a.get("costs", {}).get("gross", {}).get("value", 0)
            for a in order_attendees
        )
        gross = float(gross_cents) / 100 if gross_cents else 0.0
        price = gross  # total price

        if not order_id or not email:
            continue

        # Check for duplicates
        params = {"filterByFormula": f"{{Order ID}} = '{order_id}'"}
        existing = requests.get(AIRTABLE_TICKETS_URL, headers=AT_HEADERS, params=params)
        if existing.json().get("records"):
            continue

        data = {
            "fields": {
                "Order ID": order_id,
                "First Name": first_name,
                "Last Name": last_name,
                "Email": email,
                "Event": [airtable_event_id],
                "Ticket Type": ticket_class,
                "Price": price,
                "Quantity": quantity,
                "Channel": channel
            }
        }

        res = requests.post(AIRTABLE_TICKETS_URL, headers=AT_HEADERS, json=data)
        if res.ok:
            print(f"Synced order {order_id}: {first_name} {last_name} – {quantity} tickets for ${price:.2f}")
        else:
            print(f"Ticket Sync Error: {res.status_code} – {res.text}")

def sync_events_and_venues():
    events = get_eventbrite_events()
    for event in events:
        event_name = event["name"]["text"]
        venue_id = event.get("venue_id")
        airtable_venue_id = None

        try:
            if venue_id:
                venue_data = get_eventbrite_venue(venue_id)
                airtable_venue_id = find_or_create_venue(venue_data)
            else:
                print(f"'{event_name}' has no venue ID – continuing without venue.")

            create_event_in_airtable(event, airtable_venue_id)
            sync_ticket_sales(event)
        except Exception as e:
            print(f"Error processing '{event_name}': {e}")

if __name__ == "__main__":
    sync_events_and_venues()