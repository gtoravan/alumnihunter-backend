import threading
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import csv
import pandas as pd
import boto3
from botocore.exceptions import ClientError
from typing import List
import uuid
import linkedin_scraper
import chatgpt_processing

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can replace "*" with your frontend domain
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# DynamoDB client
dynamodb = boto3.resource('dynamodb', region_name='us-east-2')
favorite_jobs_table = dynamodb.Table('FavoriteJobs')
jobs_table = dynamodb.Table('universityatbuffalo_jobs')

class Code(BaseModel):
    code: str

class FavoriteJob(BaseModel):
    user_id: str
    job_id: str
    job_title: str
    company_name: str
    level: str
    description: str
    essential_skills: str
    salary_info: str
    alumni_profile_link: str
    job_link: str

class Job(BaseModel):
    job_id: str
    job_title: str
    company_name: str
    level: str
    description: str
    essential_skills: str
    salary_info: str
    alumni_profile_link: str
    job_link: str

@app.post("/submit_code/")
async def submit_code(code: Code):
    with open("code.txt", "w") as f:
        f.write(code.code)
    return {"message": "Verification code received"}

@app.post("/favorites")
async def add_favorite_job(favorite_job: FavoriteJob):
    try:
        favorite_jobs_table.put_item(Item=favorite_job.dict())
        return {"message": "Job added to favorites"}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Error adding favorite job: {e.response['Error']['Message']}")

@app.get("/favorites/{user_id}")
async def get_favorite_jobs(user_id: str):
    try:
        response = favorite_jobs_table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('user_id').eq(user_id)
        )
        return {"favorites": response.get('Items', [])}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving favorite jobs: {e.response['Error']['Message']}")

@app.delete("/favorites/{user_id}/{job_id}")
async def delete_favorite_job(user_id: str, job_id: str):
    try:
        favorite_jobs_table.delete_item(
            Key={
                'user_id': user_id,
                'job_id': job_id
            }
        )
        return {"message": "Job removed from favorites"}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Error removing favorite job: {e.response['Error']['Message']}")

@app.get("/")
async def root():
    return {"message": "Hello World. Welcome to FastAPI!"}

@app.get("/download_csv")
async def download_csv(university_name: str):
    file_path = f"data/{university_name}/data.csv"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Data not found for the specified university.")
    with open(file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        data = [row for row in csv_reader]
    return JSONResponse(content={"data": data})

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

@app.get("/run_data/{page_number}")
async def run_data_endpoint(page_number: int):
    # Ensure directory exists
    os.makedirs(f"data/university1", exist_ok=True)
    # Get data from run_data function
    thread = threading.Thread(target=linkedin_scraper.run_data, args=(page_number,))
    thread.start()
    return {"message": f"Scraping process for {page_number} started"}

@app.get("/start_refinement/{university_name}")
async def start_refinement(university_name: str):
    try:
        # Start a new thread to run refine_job_listings
        thread = threading.Thread(target=chatgpt_processing.refine_job_listings, args=(university_name,))
        thread.start()
        return {"message": f"Refinement process for {university_name} started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred starting the refinement process: {e}")

@app.get("/get_refined_data")
async def get_refined_data():
    try:
        # Read the refined data from CSV
        refined_data = pd.read_csv('output_with_ids.csv')

        # Convert non-finite numbers (NaN, +inf, -inf) to a suitable string
        refined_data = refined_data.replace([np.inf, -np.inf], np.nan)  # Optional: Replace infinities with NaN first
        refined_data = refined_data.fillna("NA")  # Replace NaN with "NA"

        # Convert the DataFrame to a list of dictionaries for JSON response
        data_dict = refined_data.to_dict(orient='records')

        # Ensure all data is JSON serializable
        for record in data_dict:
            for key, value in record.items():
                if isinstance(value, (np.float64, float)):
                    # Convert floats, check if they aren't finite, replace them
                    if not np.isfinite(value):
                        record[key] = "NA"
                    else:
                        # Optional: format the float if needed
                        record[key] = round(value, 2)  # Keep two decimals

        return {"data": data_dict}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read the refined data: {e}")

@app.get("/get_refined_data_new")
async def get_refined_data(university_name: str):
    try:
        file_path = f"data/{university_name}/refined_data.csv"
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Refined data not found for the specified university.")
        refined_data = pd.read_csv(file_path)
        refined_data = refined_data.replace([np.inf, -np.inf], np.nan)
        refined_data = refined_data.fillna("NA")
        data_dict = refined_data.to_dict(orient='records')
        for record in data_dict:
            for key, value in record.items():
                if isinstance(value, (np.float64, float)):
                    if not np.isfinite(value):
                        record[key] = "NA"
                    else:
                        record[key] = round(value, 2)
        return {"data": data_dict}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read the refined data: {e}")

@app.get("/check_data_status")
async def check_data_status(university_name: str):
    data_exists = os.path.exists(f"data/{university_name}/data.csv")
    refined_data_exists = os.path.exists(f"data/{university_name}/refined_data.csv")
    return {
        "university_name": university_name,
        "data_exists": data_exists,
        "refined_data_exists": refined_data_exists
    }

@app.get("/verify_university_name")
async def verify_university_name(university_name: str):
    # Placeholder for university verification logic
    return {"message": "University verification logic will be implemented here"}

@app.post("/add_jobs")
async def add_jobs_to_db():
    try:
        # Load data from CSV
        jobs_df = pd.read_csv('output_with_ids.csv')
        jobs_df.fillna("NA", inplace=True)

        for index, row in jobs_df.iterrows():
            job = Job(
                job_id=row['job_id'],
                job_title=row['Job Title'],
                company_name=row['Company Name'],
                level=row['Level'],
                description=row['Description'],
                essential_skills=row['Essential Skills'],
                salary_info=row['Salary Info'],
                alumni_profile_link=row['Alumni Profile Link'],
                job_link=row['Job Link']
            )
            jobs_table.put_item(Item=job.dict())
        return {"message": "Jobs added to DynamoDB"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding jobs to DynamoDB: {str(e)}")

@app.get("/jobs")
async def get_all_jobs():
    try:
        response = jobs_table.scan()
        return {"jobs": response.get('Items', [])}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving jobs: {e.response['Error']['Message']}")
