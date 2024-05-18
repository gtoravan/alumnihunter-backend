import csv
import os
import re
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import logging
import time

logging.basicConfig(level=logging.INFO)


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


def scrape_job_info(job_link, browser):
    try:
        browser.get(job_link)
        time.sleep(3)  # Adding a delay to ensure the page loads completely
        html_content = browser.page_source
        soup = BeautifulSoup(html_content, "html.parser")

        # Extract job title
        title_tag = soup.find("title")
        job_title = title_tag.text.strip() if title_tag else None

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

        logging.info(f"Job info: {job_info}")
        return job_info
    except Exception as e:
        logging.error(f"Error in scrape_job_info: {e}")
        return {}

def run_page(url, browser):
    try:
        browser.get(url)
        time.sleep(5)
        content = browser.page_source
        soup = BeautifulSoup(content, 'html.parser')

        all_sections = soup.find_all('li', {'class': 'reusable-search__result-container'})
        logging.info(f"Found {len(all_sections)} sections")

        profilesID = []
        for link in all_sections:
            if link is None:
                continue  # Skip None elements
            soup = BeautifulSoup(str(link), 'html.parser')
            a_tag = soup.find('div', class_='display-flex').find('a')
            if a_tag:
                href_value = a_tag['href']
                profilesID.append(href_value)
        logging.info(f"Profile IDs: {profilesID}")

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
                    job_links = soup.find_all("a", class_="job-card-container__link")
                    job_posting_links = [link["href"] for link in job_links]
                    for job_link in job_posting_links:
                        if re.match(r".*/jobs/view/.*", job_link):
                            job_link = "https://www.linkedin.com" + job_link
                            profile_job_data.append(job_link)
            job_data[profile] = profile_job_data
        logging.info(f"Job data: {job_data}")

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
        logging.info(f"Job list: {job_list}")

        return job_list
    except Exception as e:
        logging.error(f"Error in run_page: {e}")
        return []

def run_data(pages):
    logging.info("Starting scraping process")
    browser = docker_driver()
    browser.get("https://www.linkedin.com/login")

    # Read credentials from config.txt
    with open("config.txt") as file:
        lines = file.readlines()
        username = lines[0].strip()
        password = lines[1].strip()

    elementID = browser.find_element(By.ID, 'username')
    elementID.send_keys(username)
    logging.info("Entered username")

    elementID = browser.find_element(By.ID, 'password')
    elementID.send_keys(password)
    logging.info("Entered password")

    elementID.submit()
    logging.info("Submitted login form")

    if "checkpoint" in browser.current_url:
        logging.info("Security verification required")
        logging.info("Waiting for 30 seconds to fetch the verification code")
        time.sleep(30)
        while not os.path.exists("code.txt"):
            time.sleep(1)
        with open("code.txt", "r") as file:
            pin = file.read().strip()
        try:
            pin_input = browser.find_element(By.ID, 'input__email_verification_pin')
            pin_input.send_keys(pin)
            submit_button = browser.find_element(By.ID, 'email-pin-submit-button')
            submit_button.click()
            logging.info("Submitted verification code")
            time.sleep(5)
        except Exception as e:
            logging.error(f"Failed to submit verification code: {e}")
            logging.info("HTML content of the page:")
            logging.info(browser.page_source)
            return

        if "feed" not in browser.current_url:
            logging.error("Verification failed")
            logging.info("HTML content of the page:")
            logging.info(browser.page_source)
            return
        else:
            logging.info("Verification successful")

    base_url = "https://www.linkedin.com/search/results/people/?activelyHiring=%22true%22&heroEntityKey=urn%3Ali%3Aorganization%3A6502&keywords=University%20at%20Buffalo&origin=FACETED_SEARCH&page={}&sid=2ET"

    main_list = []
    for page_number in range(1, pages + 1):
        url = base_url.format(page_number)
        logging.info(f"Scraping page {page_number}: {url}")
        page_job_list = run_page(url, browser)
        main_list.extend(page_job_list)

    if not main_list:
        logging.warning("No data was scraped.")
        return

    # Define the file path where the CSV file will be saved
    file_path = "data.csv"

    # Write the data to a CSV file
    try:
        with open(file_path, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=main_list[0].keys())  # Assuming data is a list of dictionaries
            writer.writeheader()
            writer.writerows(main_list)
        logging.info(f"Data successfully written to {file_path}")
    except IndexError as e:
        logging.error("Failed to write data to CSV file: main_list is empty")
    except Exception as e:
        logging.error(f"An error occurred while writing data to CSV file: {e}")

    browser.quit()
    logging.info("Scraping process completed")

def docker_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # Initialize the Chrome driver with options
    service = ChromeService(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver
