from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

def scrape_example_website():
    # Set up Chrome options
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")  # Ensures Chrome runs in headless mode
    chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    chrome_options.add_argument("--disable-gpu")  # Applicable to windows os only
    chrome_options.add_argument("--remote-debugging-port=9222")  # This is important!
    print("hi")
    # Use ChromeDriverManager to manage the driver installation
    service = webdriver.chrome.service.Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Navigate to the website and perform actions
    driver.get("https://www.example.com")
    print("Title:", driver.title)

    # Clean up: close the browser window
    driver.quit()
    return driver.title
