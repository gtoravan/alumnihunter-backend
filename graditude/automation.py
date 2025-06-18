# graditude/automation.py

import csv
from datetime import datetime, timedelta
from graditude.csv_utils import get_csv_path, ensure_csv_columns
from graditude.twilio_handler import start_call

def run_automation(filename: str) -> dict:
    path = get_csv_path(filename)
    required_columns = ["Last Called", "Amount Donated", "Answered"]
    ensure_csv_columns(path, required_columns)

    today_str = datetime.today().strftime('%Y-%m-%d')
    five_days_ago = datetime.today() - timedelta(days=5)
    updated_rows = []
    calls_made = 0
    MAX_CALLS = 5

    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            last_called = row.get("Last Called", "")
            last_called_dt = None
            if last_called:
                try:
                    last_called_dt = datetime.strptime(last_called, "%Y-%m-%d")
                except ValueError:
                    pass

            should_call = not last_called_dt or last_called_dt < five_days_ago

            if should_call and calls_made < MAX_CALLS:
                try:
                    sid = start_call(row["Phone"])
                    print(f"Call started for {row['Name']} – SID: {sid}")
                    row["Answered"] = "Yes"  # Initially assume yes (can update later via webhook)
                except Exception as e:
                    print(f"Call failed for {row['Name']} – {e}")
                    row["Answered"] = "No"

                row["Last Called"] = today_str
                row["Amount Donated"] = "0"
                calls_made += 1

            updated_rows.append(row)

    with open(path, "w", newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_rows)

    return {
        "calls_made": calls_made,
        "message": f"Automation run on {filename}, {calls_made} calls triggered."
    }
