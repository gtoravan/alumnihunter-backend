import threading

from fastapi import FastAPI, BackgroundTasks, HTTPException
import os
from fastapi.middleware.cors import CORSMiddleware
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



app = FastAPI()

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

