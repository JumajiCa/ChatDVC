import os

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import util_funcs as util
from flask import jsonify
from dotenv import load_dotenv

def get_reg_date():

    """
    Retrieves the priority registration date/time for the Spring 2026 ('2026SP') term 
    by scraping the Contra Costa Community College District portal.

    This tool automates a full browser session using Selenium. It handles the 
    login process and automatically resolves the Email Multi-Factor Authentication (MFA) 
    challenge.

    IMPORTANT:
    - This tool ONLY retrieves data for the '2026SP' semester.
    - This is a slow operation (takes 10-20 seconds) as it launches a real browser.
    - Requires 'USERNAME' and 'PASSWORD' environment variables to be set.

    Returns:
        str: A JSON-formatted string containing the registration date.
             Example: '{"registration_date": "Nov 20, 2025 08:00 AM"}'
    """

    load_dotenv()
    name = os.getenv("USERNAME")
    pw = os.getenv("PASSWORD")

    driver = webdriver.Chrome()

    driver.get("https://webapps.4cd.edu/apps/registrationdates/default.aspx")

    def login_without_2fa():
        try:
            WebDriverWait(driver, 10).until(EC.title_is("Contra Costa Community College District - Portal Access"))
            # Now driver.title will be correct if the wait passes
            actual_title = driver.title
            time.sleep(1)
            print(f"Page title is: {actual_title}")
        except TimeoutException:
            print("Title did not match expected within the time limit")

        driver.implicitly_wait(0.5)

        username = driver.find_element(By.ID, "frmLogin_UserName")
        username.send_keys(name)

        driver.implicitly_wait(0.5)

        password = driver.find_element(By.ID, "frmLogin_Password")
        password.send_keys(pw)

        login_button = driver.find_element(By.ID, "btnLogin")
        login_button.click()

        time.sleep(1)

    login_without_2fa()

    heading = driver.find_element(By.ID, "lblOTPEntryTitle")
    print(heading.text)

    mfa_code = driver.find_element(By.ID, "OTPOTPEntry")
    mfa_code.send_keys(util.get_email_code())

    time.sleep(1)

    real_login_button = driver.find_element(By.ID, "btnOTPEntryLogin")
    real_login_button.click()

    time.sleep(1)

    registration_date = driver.find_element(
        By.XPATH,
        "//tr[td[contains(text(), '2026SP')]]/td[2]"
    ).text

    time.sleep(1)
    driver.quit()

    # print(registration_date)
    return json.dumps({"registration_date": registration_date})

print(get_reg_date())
