import os

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import util_funcs as util
from dotenv import load_dotenv
def get_reg_date():
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

    # mfa = driver.find_element(By.XPATH, "//a[@href='javascript:displayOTPResendPopup()']")
    # mfa.click()
    #
    # time.sleep(2)
    #
    # send_email = driver.find_element(By.XPATH, "//a[@href=\"javascript:resendOTP('OTPEntryForm', 'submitOTPEntry()', 3, 0)\"]")
    # send_email.click()
    #
    # time.sleep(2)
    #
    # successful = driver.find_element(By.CLASS_NAME, "successdiv")
    # print(successful.text)

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
    print(registration_date)
    # return jsonify({"registration_date": registration_date})

get_reg_date()