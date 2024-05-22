import threading

import numpy as np
from fastapi import FastAPI, BackgroundTasks, HTTPException
import os
from fastapi.middleware.cors import CORSMiddleware

from chatgpt_processing import refine_job_listings
from linkedin_scraper import run_data
from fastapi.responses import JSONResponse, FileResponse
import csv
from test import scrape_example_website
import threading
import logging
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import csv
import time
import os
import pandas as pd

app = FastAPI(ssl_keyfile="/etc/letsencrypt/live/api.alumnihunter.com/privkey.pem", ssl_certfile="/etc/letsencrypt/live/api.alumnihunter.com/fullchain.pem")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can replace "*" with your frontend domain
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

verification_code = None

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


# Add another endpoint to download the CSV file
@app.get("/download_csv")
async def download_csv():
    # Define the file path where the CSV file is located
    file_path = "data.csv"

    # Read the data from the CSV file
    with open(file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        data = [row for row in csv_reader]

    # Return the data as JSON
    return JSONResponse(content={"data": data})


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}

# operational method
@app.get("/run_data/{pages}")
async def root(pages: int):
    # Get data from run_data function
    thread = threading.Thread(target=run_data, args=(pages,))
    thread.start()
    # Return the data as JSON
    return {"message": "Scraping process started"}


@app.get("/test")
async def test_endpoint():
    return {"message": scrape_example_website()}

@app.get("/start_refinement")
async def start_refinement():
    try:
        # Start a new thread to run refine_job_listings
        thread = threading.Thread(target=refine_job_listings)
        thread.start()
        # Immediately return a response while the thread runs in the background
        return {"message": "Refinement process started successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred starting the refinement process: {e}")

@app.get("/get_refined_data")
async def get_refined_data():
    try:
        # Read the refined data from CSV
        refined_data = pd.read_csv('refined_data.csv')

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
