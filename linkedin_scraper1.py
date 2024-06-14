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
from concurrent.futures import ThreadPoolExecutor, as_completed

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping.log'),
        logging.StreamHandler()
    ]
)

def create_webdriver():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Comment out this line to run in non-headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_prefs = {}
    chrome_options.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    driver = webdriver.Chrome(options=chrome_options, service=ChromeService(ChromeDriverManager().install()))
    driver.set_page_load_timeout(240)
    driver.set_script_timeout(240)
    return driver

def scrape_job_info(job_link):
    try:
        browser = create_webdriver()
        browser.get(job_link)
        time.sleep(5)  # Adding a delay to ensure the page loads completely
        html_content = browser.page_source
        soup = BeautifulSoup(html_content, "html.parser")

        # Check if the job is no longer accepting applications
        closed_job_tag = soup.find("div", class_="jobs-details-top-card__apply-error")
        if closed_job_tag and "No longer accepting applications" in closed_job_tag.text:
            logging.info(f"Job is closed: {job_link}")
            return None  # Skip this job

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
        return None
    finally:
        if 'browser' in locals():
            browser.quit()

def scroll_page(browser):
    try:
        # Scroll down to load more profiles
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(5)

        # Click "Show more results" button if it appears
        try:
            show_more_button = browser.find_element(By.XPATH, '//button[contains(@class, "scaffold-finite-scroll__load-button")]')
            if show_more_button:
                show_more_button.click()
                logging.info("Show more results button found and clicked")
                time.sleep(5)
        except Exception as e:
            logging.info("No 'Show more results' button found")
    except Exception as e:
        logging.error(f"Error in scroll_page: {e}")

def run_page(url, browser):
    retries = 3
    for attempt in range(retries):
        try:
            logging.info(f"Attempting to load page {url} (Attempt {attempt + 1}/{retries})")
            browser.get(url)
            time.sleep(10)
            content = browser.page_source
            soup = BeautifulSoup(content, 'html.parser')

            alumni_count_tag = soup.find('h2', class_='text-heading-xlarge')
            if not alumni_count_tag:
                logging.error("Failed to find alumni count on page")
                return []

            alumni_count = int(re.sub(r'[^\d]', '', alumni_count_tag.text))
            logging.info(f"Found {alumni_count} alumni")

            profile_links = set()
            while len(profile_links) < 1500:
                scroll_page(browser)
                content = browser.page_source
                soup = BeautifulSoup(content, 'html.parser')
                all_sections = soup.find_all('li', {'class': 'org-people-profile-card__profile-card-spacing'})

                for link in all_sections:
                    a_tag = link.find('a', class_='app-aware-link')
                    if a_tag:
                        href_value = a_tag['href']
                        profile_links.add(href_value)
                logging.info(f"Collected {len(profile_links)} profile links")

            return profile_links
        except Exception as e:
            logging.error(f"Error in run_page: {e}")
            if attempt < retries - 1:
                logging.info("Retrying...")
                time.sleep(10)
            else:
                logging.error("All retries failed")
                return []

def run_data(university_name):
    try:
        logging.info("Starting scraping process")
        browser = create_webdriver()  # Use create_webdriver to allow browser pop-up
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

            # Add a sleep call to give you time to verify on the phone
            logging.info("Please verify the login attempt on your phone...")
            time.sleep(20)  # 20 seconds pause for phone verification

            # Check if login was successful after phone verification
            if "feed" not in browser.current_url:
                logging.error("Verification failed")
                logging.info("HTML content of the page:")
                logging.info(browser.page_source)
                return
            else:
                logging.info("Verification successful via phone")

        base_url = f"https://www.linkedin.com/school/{university_name}/people/"
        profile_links = run_page(base_url, browser)

        browser.quit()
    except Exception as e:
        logging.error(f"Error in run_data: {e}")
        return

    # Save profile links to profiles.csv
    try:
        os.makedirs(f"data/{university_name}", exist_ok=True)
        profiles_file = f"data/{university_name}/profiles.csv"
        with open(profiles_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Profile Link'])
            for link in profile_links:
                writer.writerow([link])
        logging.info(f"Profile links saved to {profiles_file}")
    except Exception as e:
        logging.error(f"Error in saving profile links: {e}")

    job_data = {}
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_url = {executor.submit(scrape_job_info, profile): profile for profile in profile_links}
        for future in as_completed(future_to_url):
            profile = future_to_url[future]
            try:
                job_info = future.result()
                if job_info:
                    job_data[profile] = job_info
            except Exception as e:
                logging.error(f"Error occurred while processing profile {profile}: {e}")

    job_list = []
    for profile_url, job_info in job_data.items():
        job_object = {
            "title": job_info.get("job_title"),
            "salary": job_info.get("salary_range"),
            "skills": job_info.get("skills"),
            "description": job_info.get("job_description"),
            "alumni_profile_link": profile_url,
            "job_link": job_info.get("job_link"),
            "location": job_info.get("location"),
            "level": job_info.get("level"),
            "company": job_info.get("company")
        }
        job_list.append(job_object)
    logging.info(f"Job list: {job_list}")

    try:
        output_file = f"data/{university_name}/refined_data.csv"
        with open(output_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow(['Title', 'Salary', 'Skills', 'Description', 'Alumni Profile Link', 'Job Link', 'Location', 'Level', 'Company'])
            for job in job_list:
                writer.writerow([job['title'], job['salary'], job['skills'], job['description'], job['alumni_profile_link'], job['job_link'], job['location'], job['level'], job['company']])
        logging.info("Scraping process completed successfully")
        logging.info(f"Data saved to {output_file}")
    except Exception as e:
        logging.error(f"Error in saving job data: {e}")

if __name__ == "__main__":
    run_data("university-of-georgia")
