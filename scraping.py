from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

# Setup Chrome options
options = Options()
options.add_argument("--headless")  # Ensure GUI is off
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--disable-infobars")
options.add_argument("--disable-extensions")
options.add_argument("--start-maximized")
options.add_argument("--disable-software-rasterizer")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

# Initialize the WebDriver instance with the path to the ChromeDriver binary
service = Service("/opt/homebrew/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=options)

# URL for New Jersey business listings
nj_url = "https://www.bizbuysell.com/new-jersey-businesses-for-sale/?q=bHQ9MzAsNDAsODA%3D"

# Open the URL
driver.get(nj_url)

try:
    # Wait for the main container element to be present
    main_container = WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, "listing-container"))
    )

    # Scroll down to ensure all dynamic content is loaded
    scroll_pause_time = 2
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(scroll_pause_time)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    # Get the page source
    page_source = driver.page_source

    # Parse the HTML content
    soup = BeautifulSoup(page_source, 'html.parser')

    # Print the formatted HTML content for inspection
    print(soup.prettify())
except Exception as e:
    print(f"Error occurred: {e}")
finally:
    # Close the browser
    driver.quit()
