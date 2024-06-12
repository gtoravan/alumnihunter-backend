import threading
import numpy as np
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import os
import csv
import pandas as pd
from chatgpt_processing1 import refine_job_listings
from linkedin_scraper import run_data

app = FastAPI(ssl_keyfile="/etc/letsencrypt/live/api.alumnihunter.com/privkey.pem", ssl_certfile="/etc/letsencrypt/live/api.alumnihunter.com/fullchain.pem")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can replace "*" with your frontend domain
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

class Code(BaseModel):
    code: str

@app.post("/submit_code/")
async def submit_code(code: Code):
    with open("code.txt", "w") as f:
        f.write(code.code)
    return {"message": "Verification code received"}

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

@app.get("/run_data/{university_name}")
async def run_data_endpoint(university_name: str):
    # Ensure directory exists
    os.makedirs(f"data/{university_name}", exist_ok=True)
    # Get data from run_data function
    thread = threading.Thread(target=run_data, args=(university_name,))
    thread.start()
    return {"message": f"Scraping process for {university_name} started"}

@app.get("/start_refinement/{university_name}")
async def start_refinement(university_name: str):
    try:
        # Start a new thread to run refine_job_listings
        thread = threading.Thread(target=refine_job_listings, args=(university_name,))
        thread.start()
        return {"message": f"Refinement process for {university_name} started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred starting the refinement process: {e}")

@app.get("/get_refined_data")
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
