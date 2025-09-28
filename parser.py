#!/usr/bin/env -S uv run --script
#
# /// script
# dependencies = [
#     "pandas",
#     "html5lib",
#     "beautifulsoup4",
#     "icalendar",
#     "requests",
#     "python-dateutil",
# ]
# ///

import os
import sys
from datetime import timedelta
from io import StringIO

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dateutil import parser
from icalendar import Calendar, Event

URL = "https://en.wikipedia.org/wiki/Public_holidays_in_Nepal"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

DEBUG_HTML_PATH = "debug.html"


def fetch_wikitable_html(url: str) -> str:
    """Fetch HTML for the first table with class 'wikitable'."""
    resp = requests.get(url, headers=HEADERS)
    resp.raise_for_status()

    # Save debug HTML for GitHub Actions inspection
    with open(DEBUG_HTML_PATH, "w", encoding="utf-8") as f:
        f.write(resp.text)

    soup = BeautifulSoup(resp.text, "html.parser")
    table = soup.find_all("table", {"class": "wikitable"})

    if not table:
        raise ValueError("No table with class 'wikitable' found on the page.")

    return str(table)


def parse_table(html: str) -> pd.DataFrame:
    """Parse HTML table into a DataFrame."""
    tables = pd.read_html(StringIO(html), flavor="html5lib")
    if not tables:
        raise ValueError("No tables could be parsed from HTML.")
    return pd.concat(tables, ignore_index=True)


def create_calendar(df: pd.DataFrame) -> Calendar:
    cal = Calendar()
    cal.add("prodid", "-//Nepali Holidays//example.com//")
    cal.add("version", "2.0")
    cal.add("X-WR-CALNAME", "Nepali Holidays")
    cal.add("X-WR-CALDESC", "Nepali holidays extracted from Wikipedia")

    for _, row in df.iterrows():
        date_ad = row.get(("Date", "Date (A.D.)"))
        date_bs = row.get(("Date", "Date (B.S.)"))
        name_eng = row.get(("Name", "English"))
        name_nep = row.get(("Name", "Nepali"))
        remarks = row.get(("Remarks", "Remarks"))

        if not date_ad or not name_eng:
            continue

        try:
            event_date = parser.parse(str(date_ad)).date()
        except Exception:
            print(f"⚠️ Skipping invalid date: {date_ad}")
            continue

        summary = f"{name_eng} ({name_nep})" if isinstance(name_nep, str) else name_eng

        description_parts = []
        if isinstance(remarks, str):
            description_parts.append(remarks)
        if isinstance(date_bs, str):
            description_parts.append(date_bs)
        description = " — ".join(description_parts)

        event = Event()
        event.add("summary", summary)
        event.add("description", description)
        event.add("dtstart", event_date)
        event.add("dtend", event_date + timedelta(days=1))

        cal.add_component(event)

    return cal


def main():
    os.makedirs("public", exist_ok=True)

    try:
        table_html = fetch_wikitable_html(URL)
        df = parse_table(table_html)
    except Exception as e:
        print(f"❌ Error fetching or parsing table: {e}")
        sys.exit(1)

    calendar = create_calendar(df)

    output_path = "public/nepali-holidays.ics"
    with open(output_path, "wb") as f:
        f.write(calendar.to_ical())

    print(f"✅ {output_path} created successfully.")


if __name__ == "__main__":
    main()
