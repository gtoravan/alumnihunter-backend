# graditude/csv_utils.py

import os
import csv
from datetime import datetime

STORAGE_DIR = "graditude/storage"

def get_csv_path(filename: str) -> str:
    return os.path.join(STORAGE_DIR, filename)

def ensure_csv_columns(path: str, required_columns: list):
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []

    updated = False
    for col in required_columns:
        if col not in fieldnames:
            fieldnames.append(col)
            updated = True
            for row in rows:
                row[col] = ""

    if updated:
        with open(path, "w", newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

def list_uploaded_files():
    return [f for f in os.listdir(STORAGE_DIR) if f.endswith(".csv")]
