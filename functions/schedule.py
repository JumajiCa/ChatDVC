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

    course_tables = driver.find_elements(By.CSS_SELECTOR, "table.course-details-grid")

    all_courses = []

    for course in course_tables:
        course_info = {}

        # ----- Title -----
        title_el = course.find_element(By.XPATH, ".//preceding-sibling::div[1]")
        course_info["title"] = title_el.text.strip()

        # ----- Date Range -----
        date_el = course.find_element(By.XPATH, ".//tbody/tr[1]/td")
        course_info["date_range"] = date_el.text.strip()

        # ----- Rooms -----
        room_cells = course.find_elements(
            By.XPATH, ".//td[contains(., 'Bldg/Room')]"
        )
        rooms = []
        for r in room_cells:
            rooms.append(r.text.replace("Bldg/Room:", "").strip())
        course_info["rooms"] = rooms

        # ----- Instructors -----
        # instructors are inside <td> tags under the room block
        instructor_cells = course.find_elements(
            By.XPATH, ".//tr/td[not(contains(., 'Bldg/Room')) and string-length(normalize-space()) > 0]"
        )
        instructors = [x.text.strip() for x in instructor_cells]
        course_info["instructors"] = instructors

        all_courses.append(course_info)

    cleaned_courses = []
    for c in all_courses:
        cleaned = {
            "title": util.clean(c["title"]),
            "date_range": util.clean(c["date_range"]),
            "rooms": [util.clean(r) for r in c["rooms"]],
            "instructors": [util.clean(i) for i in c["instructors"]],
        }
        cleaned_courses.append(cleaned)

    # print(cleaned_courses)

    driver.quit()
    # print(registration_date)
    return jsonify(cleaned_courses)

get_schedule()