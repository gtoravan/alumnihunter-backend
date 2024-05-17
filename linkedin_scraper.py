import csv

from bs4 import BeautifulSoup
import re
import time

from selenium.webdriver.common.by import By

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def scrape_job_info(job_link, browser):
    browser.get(job_link)
    time.sleep(3)  # Adding a delay to ensure page loads completely
    html_content = browser.page_source
    soup = BeautifulSoup(html_content, "html.parser")

    # Extract job title
    title_tag = soup.find("title")
    job_title = title_tag.text.strip()

    # Extract salary range
    salary_tag = soup.find("div", class_="mt2 mb2")
    salary_range = salary_tag.text.strip() if salary_tag else None

    # Extract job description
    description_tag = soup.find("div", class_="jobs-description__content")
    job_description = description_tag.text.strip() if description_tag else None

    # Extract skills needed (if available)
    skills_tag = soup.find("div", class_="job-details-jobs-unified-top-card__job-insight")
    skills = skills_tag.text.strip() if skills_tag else None

    # Extract location (if available)
    location_tag = soup.find("div", class_="job-details-jobs-unified-top-card__primary-description-container")
    location = location_tag.text.strip().split("·")[0].strip() if location_tag else None

    # Extract level (if available)
    level_tag = soup.find("span", class_="job-details-jobs-unified-top-card__job-insight-view-model-secondary")
    level = level_tag.text.strip() if level_tag else None

    # Extract company name (if available)
    company_tag = soup.find("div", class_="job-details-jobs-unified-top-card__company-name")
    company = company_tag.find("a").text.strip() if company_tag and company_tag.find("a") else None

    # Create a dictionary to hold job information
    job_info = {
        "job_title": job_title,
        "salary_range": salary_range,
        "job_description": job_description,
        "skills": skills,
        "job_link": job_link,
        "location": location,
        "level": level,
        "company": company
    }

    return job_info



def run_page(url,browser):
    browser.get(url)
    time.sleep(5)
    content = browser.page_source
    soup = BeautifulSoup(content, 'html.parser')

    all_sections = soup.find_all('li', {'class': 'reusable-search__result-container'})

    profilesID = []
    for link in all_sections:
        if link is None:
            continue  # Skip None elements
        soup = BeautifulSoup(str(link), 'html.parser')
        a_tag = soup.find('div', class_='display-flex').find('a')
        if a_tag:
            href_value = a_tag['href']
            profilesID.append(href_value)
    print(profilesID)

    job_data = {}
    for profile in profilesID:
        browser.get(profile)
        time.sleep(3)
        html_content = browser.page_source
        soup = BeautifulSoup(html_content, "html.parser")
        job_section = soup.find("section", class_="artdeco-card pv-open-to-carousel-card pv-open-to-carousel-card--enrolled pv-open-to-carousel-card--single")
        profile_job_data = []
        if job_section:
            job_link_element = job_section.find("a", class_="app-aware-link")
            if job_link_element:
                job_link = job_link_element["href"]
                if re.match(r".*/jobs/view/.*", job_link):
                    profile_job_data.append(job_link)
            else:
                browser.get(job_link)
                time.sleep(3)
                html_content = browser.page_source
                soup = BeautifulSoup(html_content, "html.parser")
                job_links = soup.find_all("a", class_="job-card-container__link")
                job_posting_links = [link["href"] for link in job_links]
                for job_link in job_posting_links:
                    if re.match(r".*/jobs/view/.*", job_link):
                        job_link = "https://www.linkedin.com" + job_link
                        profile_job_data.append(job_link)
        job_data[profile] = profile_job_data
    print(job_data)

    job_info_dict = {}
    for profile_url, job_urls in job_data.items():
        for job_url in job_urls:
            job_info = scrape_job_info(job_url, browser)
            job_info_dict[job_url] = job_info

    job_list = []
    for profile_url, job_urls in job_data.items():
        for job_url in job_urls:
            if job_url in job_info_dict:
                job_info = job_info_dict[job_url]
                job_object = {
                    "title": job_info.get("job_title"),
                    "salary": job_info.get("salary_range"),
                    "skills": job_info.get("skills"),
                    "description": job_info.get("job_description"),
                    "alumni_profile_link": profile_url,
                    "job_link": job_url,
                    "location": job_info.get("location"),
                    "level": job_info.get("level"),
                    "company": job_info.get("company")
                }
                job_list.append(job_object)

    return job_list

def create_webdriver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_prefs = {}
    chrome_options.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    driver = webdriver.Chrome(options=chrome_options)
    return driver

def run_data(pages):
    # Set up Chrome options
    browser = docker_driver()
    browser.get("https://www.linkedin.com/login")

    file = open("config.txt")
    line = file.readlines()
    username = line[0]
    password = line[1]

    elementID = browser.find_element(By.ID, 'username')
    elementID.send_keys(username)

    elementID = browser.find_element(By.ID, 'password')
    elementID.send_keys(password)

    elementID.submit()

    base_url = "https://www.linkedin.com/search/results/people/?activelyHiring=%22true%22&heroEntityKey=urn%3Ali%3Aorganization%3A6502&keywords=University%20at%20Buffalo&origin=FACETED_SEARCH&page={}&sid=2ET"

    main_list = []
    for page_number in range(1,pages):
        url = base_url.format(page_number)
        page_job_list = run_page(url,browser)
        main_list.extend(page_job_list)

    if not main_list:
        print("No data was scraped.")

    # Define the file path where the CSV file will be saved
    file_path = "data.csv"

    # Write the data to a CSV file
    with open(file_path, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=main_list[0].keys())  # Assuming data is a list of dictionaries
        writer.writeheader()
        writer.writerows(main_list)

    return main_list

def docker_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run headless if you don't need a GUI
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver_path = '/usr/bin/chromedriver'
    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver
