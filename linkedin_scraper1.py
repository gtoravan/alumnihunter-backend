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
    chrome_options.add_argument("--remote-debugging-port=9222")
    chrome_prefs = {}
    chrome_options.experimental_options["prefs"] = chrome_prefs
    chrome_prefs["profile.default_content_settings"] = {"images": 2}
    driver = webdriver.Chrome(options=chrome_options, service=ChromeService(ChromeDriverManager().install()))
    driver.set_page_load_timeout(120)
    driver.set_script_timeout(120)
    return driver

def scrape_job_info(job_link, browser):
    try:
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

def scroll_page(browser):
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
            while len(profile_links) < alumni_count:
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
                logging.info(profile_links)

            job_data = {}
            for profile in profile_links:
                logging.info(profile)
                browser.get(profile)
                time.sleep(5)
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
                    if job_info:
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
            if attempt < retries - 1:
                logging.info("Retrying...")
                time.sleep(10)
            else:
                logging.error("All retries failed")
                return []

def run_data(university_name):
    logging.info("Starting scraping process")
    browser = create_webdriver()
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
    job_list = run_page(base_url, browser)

    browser.quit()
    os.makedirs("output", exist_ok=True)
    logging.info(f"Saving data to data/{university_name}/refined_data.csv")

    output_file = os.path.join("output", f"data/{university_name}/refined_data.csv")
    with open(output_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['Title', 'Salary', 'Skills', 'Description', 'Alumni Profile Link', 'Job Link', 'Location', 'Level', 'Company'])
        for job in job_list:
            writer.writerow([job['title'], job['salary'], job['skills'], job['description'], job['alumni_profile_link'], job['job_link'], job['location'], job['level'], job['company']])
    logging.info("Scraping process completed successfully")
    logging.info(f"Data saved to {output_file}")

def docker_driver():
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # Initialize the Chrome driver with options
    service = ChromeService(executable_path=ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# if __name__ == "__main__":
#     run_data("university-of-georgia")