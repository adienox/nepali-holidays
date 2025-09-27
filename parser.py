#!/usr/bin/env -S uv run --script
#
# /// script
# requires-python = ">=3.13"
# dependencies = [
#     "pandas",
#     "html5lib",
#     "beautifulsoup4",
#     "icalendar",
#     "requests",
# ]
# ///

import os
from datetime import timedelta

import pandas as pd
import requests
from dateutil import parser
from icalendar import Calendar, Event

url = "https://en.wikipedia.org/wiki/Public_holidays_in_Nepal"

headers = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)
response.raise_for_status()

tables = pd.read_html(response.text, attrs={"class": "wikitable"}, flavor="bs4")

final_df = pd.concat(tables, ignore_index=True)

cal = Calendar()
cal.calendar_name = "Nepali Holidays"
cal.description = "Nepali holidays extracted from Wikipedia"

for _, row in final_df.iterrows():
    date_ad = row.get(("Date", "Date (A.D.)"))
    date_bs = row.get(("Date", "Date (B.S.)"))
    name_eng = row.get(("Name", "English"))
    name_nep = row.get(("Name", "Nepali"))
    remarks = row.get(("Remarks", "Remarks"))

    try:
        # Parse A.D. date (e.g. "May 1")
        event_date = parser.parse(date_ad).date()
    except Exception:
        print(f"Skipping invalid date: {date_ad}")
        continue

    if isinstance(name_nep, str):
        summary = f"{name_eng} ({name_nep})"
    else:
        summary = name_eng

    if isinstance(remarks, str) and isinstance(date_bs, str):
        description = f"{remarks} ({date_bs})"
    elif isinstance(remarks, str):
        description = remarks
    elif isinstance(date_bs, str):
        description = date_bs
    else:
        description = ""

    event = Event()
    event.add("summary", summary)
    event.add("description", description)
    event.add("dtstart", event_date)
    event.add("dtend", event_date + timedelta(days=1))

    cal.add_component(event)

os.makedirs("public", exist_ok=True)
with open("public/nepali-holidays.ics", "wb") as f:
    f.write(cal.to_ical())

print("✅ nepali-holidays.ics created")
