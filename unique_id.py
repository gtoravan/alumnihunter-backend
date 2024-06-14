import csv
import uuid

def add_job_ids(input_file, output_file):
    with open(input_file, mode='r', newline='', encoding='utf-8') as infile, open(output_file, mode='w', newline='', encoding='utf-8') as outfile:
        reader = csv.DictReader(infile)
        fieldnames = ['job_id'] + reader.fieldnames
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)

        writer.writeheader()

        for row in reader:
            row['job_id'] = str(uuid.uuid4())
            writer.writerow(row)

if __name__ == "__main__":
    input_csv = 'refined_data.csv'
    output_csv = 'output_with_ids.csv'
    add_job_ids(input_csv, output_csv)
    print(f"Job IDs added to {output_csv}")
