import pandas as pd
import boto3

dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
jobs_table = dynamodb.Table('universityatbuffalo_jobs')

def add_jobs_to_db():
    try:
        jobs_df = pd.read_csv('output_with_ids.csv')
        jobs_df.fillna("NA", inplace=True)

        with jobs_table.batch_writer() as batch:
            for index, row in jobs_df.iterrows():
                job = {
                    'job_id': row['job_id'],
                    'job_title': row['Job Title'],
                    'company_name': row['Company Name'],
                    'level': row['Level'],
                    'description': row['Description'],
                    'essential_skills': row['Essential Skills'],
                    'salary_info': row['Salary Info'],
                    'alumni_profile_link': row['Alumni Profile Link'],
                    'job_link': row['Job Link']
                }
                batch.put_item(Item=job)

        print("Jobs added to DynamoDB")
    except Exception as e:
        print(f"Error adding jobs to DynamoDB: {str(e)}")

if __name__ == "__main__":
    add_jobs_to_db()
