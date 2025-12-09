import os

from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import util_funcs as util
from dotenv import load_dotenv

def get_schedule():

    load_dotenv()

    name = os.getenv("USERNAME")
    pw = os.getenv("PASSWORD")

    driver = webdriver.Chrome()

    driver.get("https://webapps.4cd.edu/apps/courseschedulesearch/schedule.aspx")

    wait = WebDriverWait(driver, 15)

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

    # Wait for dropdown
    term_dropdown = wait.until(
        EC.presence_of_element_located((By.ID, "ctl00_PlaceHolderMain_ddlTerm"))
    )

    select = Select(term_dropdown)

    # # Step 1: Select the placeholder (optional)
    # select.select_by_visible_text("-- Select Term --")

    # Step 2: Select "2026SP"
    select.select_by_visible_text("2026SP")

    # Step 3: Wait for page to refresh + table to load
    wait.until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "table.course-details-grid")
        )
    )

    courses_table = driver.find_element(By.ID, "ctl00_PlaceHolderMain_dgCourses")
    rows = courses_table.find_elements(By.XPATH, "./tbody/tr")

    courses = []

    def clean(t):
        return " ".join(t.replace("\n", " ").split())

    for row in rows:
        td = row.find_element(By.TAG_NAME, "td")

        # Title — bold span
        title = td.find_element(
            By.CSS_SELECTOR, "span[id*='_lblCourse']"
        ).text

        # Date range — italic span
        date_range = td.find_element(
            By.CSS_SELECTOR, "span[id*='_lblDates']"
        ).text

        # All "Bldg/Room" sections
        locations = td.find_elements(By.CSS_SELECTOR, "span[id*='_lblLocation']")
        location_labels = [loc.text for loc in locations]

        # Instructor tables under each location
        instructor_tables = td.find_elements(By.CSS_SELECTOR, "table.grid-faculty-names")
        instructor_lists = []
        for table in instructor_tables:
            names = [clean(td.text) for td in table.find_elements(By.TAG_NAME, "td")]
            instructor_lists.append(names)

        courses.append({
            "title": clean(title),
            "date_range": clean(date_range),
            "rooms": location_labels,
            "instructors": instructor_lists
        })

    print(courses)

    driver.quit()
    # return jsonify(courses)
