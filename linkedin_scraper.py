import time
import pandas as pd
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

import gspread
from gspread_dataframe import set_with_dataframe
from oauth2client.service_account import ServiceAccountCredentials

# ---------- CONFIG ----------
EMAIL = "   " # <---- your linkedin email
PASSWORD = "   " #<---- your linkedin password
SEARCH_QUERY = "Hiring AI interns"
SCROLL_COUNT = 5  #<-- how many times it should scroll down 
SERVICE_ACCOUNT_FILE = "  "  #It's a googlesheets JSON file generated from Google Cloud Console.It contains credentials used to authenticate your code (usually a backend script) to access Google APIs
GOOGLE_SHEET_NAME = "LinkedIn Job Posts"  # <-- your Google Sheet name which you create
# ----------------------------

def linkedin_scraper():
    # Launch browser
    options = uc.ChromeOptions()
    driver = uc.Chrome(options=options)

    driver.get("https://www.linkedin.com/login")
    time.sleep(3)

    # Login
    driver.find_element(By.ID, "username").send_keys(EMAIL)
    driver.find_element(By.ID, "password").send_keys(PASSWORD + Keys.RETURN)

    # CAPTCHA wait [usually it wont ask as we used undectected chrome if it ask set the sleep time and solve it manually or by using paid serives like anticaptcha you can skip the captcha]
    print("Please solve CAPTCHA manually... waiting 10 seconds.")
    time.sleep(10)

    # Go to content search
    search_url = f"https://www.linkedin.com/search/results/content/?keywords={SEARCH_QUERY.replace(' ', '%20')}"
    driver.get(search_url)
    time.sleep(5)

    # Scroll
    for i in range(SCROLL_COUNT):
        print(f"Scrolling... {i + 1}/{SCROLL_COUNT}")
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(4)

    # Scrape
    posts = driver.find_elements(By.CSS_SELECTOR, 'div[data-urn*="urn:li:activity"]')
    data = []

    for i, post in enumerate(posts, 1):
        try:
            post_text = post.text.strip()
            a_tags = post.find_elements(By.TAG_NAME, "a")
            emails = []

            for a in a_tags:
                href = a.get_attribute("href") or ""
                if href.startswith("mailto:"):
                    emails.append(href.replace("mailto:", ""))

            if emails:
                data.append({
                    "Post Text": post_text,
                    "Emails": ", ".join(emails)
                })

        except Exception as e:
            print(f"Error scraping post {i}: {e}")

    driver.quit()

    # DataFrame
    df = pd.DataFrame(data, columns=["Post Text", "Emails"])

    print(f"\nScraped {len(df)} posts with emails.")

    # ----------------------------
    # Append unique data to Google Sheets

    # Define the scope for Google Sheets and Drive API
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

    # Authenticate using the service account JSON
    creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
    client = gspread.authorize(creds)

    # Open your Google Sheet by name
    spreadsheet = client.open(GOOGLE_SHEET_NAME)
    worksheet = spreadsheet.sheet1  

    # Read existing data from sheet into DataFrame (if sheet is empty, create empty df)
    existing_records = worksheet.get_all_records()
    if existing_records:
        df_existing = pd.DataFrame(existing_records)
    else:
        df_existing = pd.DataFrame(columns=["Post Text", "Emails"])

    # Combine old and new data
    df_combined = pd.concat([df_existing, df], ignore_index=True)

    # Drop duplicates based on "Emails" column (you can adjust this if needed)
    df_combined.drop_duplicates(subset=["Emails"], inplace=True)

    # Clear and write back unique combined data
    worksheet.clear()
    set_with_dataframe(worksheet, df_combined)

    print("Data appended with unique entries to Google Sheet successfully!")

if __name__ == "__main__":
    linkedin_scraper()
