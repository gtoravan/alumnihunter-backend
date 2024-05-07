from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from extract import *
import os
from fastapi.middleware.cors import CORSMiddleware
from linkedin_scraper import run_data
from fastapi.responses import JSONResponse, FileResponse
import csv



SECRET = os.getenv("SECRET")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # You can replace "*" with your frontend domain
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)


class Msg(BaseModel):
    msg: str
    secret: str

@app.get("/")

async def root():
    return {"message": "Hello World. Welcome to FastAPI!"}


@app.get("/homepage")
async def demo_get():
    driver=createDriver()

    homepage = getGoogleHomepage(driver)
    driver.close()
    return homepage

@app.post("/backgroundDemo")
async def demo_post(inp: Msg, background_tasks: BackgroundTasks):
    
    background_tasks.add_task(doBackgroundTask, inp)
    return {"message": "Success, background task started"}


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
    data = run_data(pages)

    # Define the file path where the CSV file will be saved
    file_path = "data.csv"

    # Write the data to a CSV file
    with open(file_path, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=data[0].keys())  # Assuming data is a list of dictionaries
        writer.writeheader()
        writer.writerows(data)

    # Return the data as JSON
    return {"data": data}
    


