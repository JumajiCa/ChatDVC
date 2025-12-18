import json
import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select

COOKIES_DIR = "user_cookies"
os.makedirs(COOKIES_DIR, exist_ok=True)


class InsiteService:
    def __init__(self):
        self.active_drivers = {}

    def get_cookie_path(self, user_id):
        return os.path.join(COOKIES_DIR, f"cookies_{user_id}.json")

    def start_driver(self):
        options = webdriver.ChromeOptions()
        # Headless settings
        # options.add_argument("--headless=new")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--log-level=3")
        return webdriver.Chrome(options=options)

    def close_driver(self, user_id):
        if user_id in self.active_drivers:
            try:
                self.active_drivers[user_id].quit()
            except:
                pass
            del self.active_drivers[user_id]

    def login_step_1(self, user_id, username, password):
        base_url = "https://webapps.4cd.edu/apps/registrationdates/default.aspx"

        # 1. Check existing driver
        driver = self.active_drivers.get(user_id)
        if driver:
            try:
                driver.get(base_url)
                time.sleep(1)
                if "Portal Access" not in driver.title:
                    return "LOGGED_IN"
            except:
                self.close_driver(user_id)
                driver = None

        # 2. Start new driver
        if not driver:
            driver = self.start_driver()
            self.active_drivers[user_id] = driver
            driver.get(base_url)

            # Try cookies
            cookie_path = self.get_cookie_path(user_id)
            if os.path.exists(cookie_path):
                try:
                    with open(cookie_path, 'r') as f:
                        cookies = json.load(f)
                    for c in cookies: driver.add_cookie(c)
                    driver.get(base_url)
                    time.sleep(1)
                    if "Portal Access" not in driver.title:
                        return "LOGGED_IN"
                except:
                    pass

        # 3. Manual Login
        try:
            wait = WebDriverWait(driver, 5)
            if "Portal Access" not in driver.title:
                driver.get(base_url)

            wait.until(EC.presence_of_element_located((By.ID, "frmLogin_UserName")))
            driver.find_element(By.ID, "frmLogin_UserName").send_keys(username)
            driver.find_element(By.ID, "frmLogin_Password").send_keys(password)
            driver.find_element(By.ID, "btnLogin").click()

            time.sleep(2)

            if "OTPEntry" in driver.page_source or "lblOTPEntryTitle" in driver.page_source:
                return "2FA_REQUIRED"

            self.save_cookies(user_id)
            return "LOGGED_IN"

        except Exception as e:
            self.close_driver(user_id)
            raise e

    def login_step_2_submit_code(self, user_id, code):
        driver = self.active_drivers.get(user_id)
        if not driver:
            return False, "Session timeout"

        try:
            driver.find_element(By.ID, "OTPOTPEntry").send_keys(code)
            driver.find_element(By.ID, "btnOTPEntryLogin").click()
            time.sleep(4)

            if "Portal Access" in driver.title:
                return False, "Invalid code"

            self.save_cookies(user_id)
            return True, "Success"
        except Exception as e:
            return False, str(e)

    def save_cookies(self, user_id):
        driver = self.active_drivers.get(user_id)
        if driver:
            with open(self.get_cookie_path(user_id), 'w') as f:
                json.dump(driver.get_cookies(), f)

    def fetch_data(self, user_id):
        driver = self.active_drivers.get(user_id)
        if not driver:
            raise Exception("No browser active.")

        # --- GET REG DATE ---
        reg_date = "Not found"
        try:
            driver.get("https://webapps.4cd.edu/apps/registrationdates/default.aspx")
            time.sleep(1.5)
            reg_date = driver.find_element(By.XPATH, "//tr[td[contains(text(), '2026SP')]]/td[2]").text
        except Exception as e:
            pass

        # --- GET SCHEDULE (TARGETED SCRAPING) ---
        schedule_text = "No schedule found"
        try:
            driver.get("https://webapps.4cd.edu/apps/courseschedulesearch/schedule.aspx")
            wait = WebDriverWait(driver, 10)

            # 1. Select Term
            term_dropdown = wait.until(EC.presence_of_element_located((By.ID, "ctl00_PlaceHolderMain_ddlTerm")))
            select = Select(term_dropdown)
            select.select_by_visible_text("2026SP")

            # 2. Wait for the MAIN grid to load
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "courses-grid")))

            # 3. Iterate through the main Course Rows
            # The structure is Table.courses-grid -> tr -> td -> divs for Title/Date + Table for details
            main_grid = driver.find_element(By.CLASS_NAME, "courses-grid")
            course_rows = main_grid.find_elements(By.XPATH, "./tbody/tr")  # Get direct rows

            all_courses = []

            for row in course_rows:
                # Based on your screenshot, the ID ends with 'lblCourse'
                # We use specific XPATHs relative to the 'row' to be precise
                try:
                    # -- Get Title --
                    # Looks for span with id ending in 'lblCourse'
                    title_el = row.find_element(By.XPATH, ".//span[contains(@id, 'lblCourse')]")
                    title = title_el.text.strip()

                    # -- Get Date Range --
                    # Looks for span with id ending in 'lblDates'
                    date_el = row.find_element(By.XPATH, ".//span[contains(@id, 'lblDates')]")
                    date_range = date_el.text.strip()

                    # -- Get Details (Location & Faculty) --
                    # Nested table with class 'course-details-grid'
                    details = []
                    detail_table = row.find_element(By.CLASS_NAME, "course-details-grid")
                    detail_rows = detail_table.find_elements(By.TAG_NAME, "tr")

                    for dr in detail_rows:
                        # Location is in a span ending with 'lblLocation'
                        try:
                            loc = dr.find_element(By.XPATH, ".//span[contains(@id, 'lblLocation')]").text
                        except:
                            loc = ""

                        # Faculty names are in table with class 'grid-faculty-names'
                        faculty = []
                        try:
                            fac_els = dr.find_elements(By.CSS_SELECTOR, "table.grid-faculty-names td")
                            faculty = [f.text.strip() for f in fac_els if f.text.strip()]
                        except:
                            pass

                        # Sometimes 'Days/Times' are just text inside the row or parent div.
                        # The safest way to catch "M T W 9:00AM" is to just grab the full text of this detail row
                        # and let the AI parse it, as it will contain the Location + Faculty + Times combined.
                        full_detail_text = dr.text.replace("\n", " ").strip()

                        details.append(full_detail_text)

                    all_courses.append({
                        "course": title,
                        "dates": date_range,
                        "details": details
                    })

                except Exception as e:
                    # This block handles spacer rows or rows that don't match the course structure
                    continue

            if all_courses:
                schedule_text = json.dumps(all_courses, indent=2)
            else:
                schedule_text = "No classes registered for 2026SP."

        except Exception as e:
            print(f"Schedule Error: {e}")
            schedule_text = f"Error retrieving schedule: {str(e)}"

        return reg_date, schedule_text


insite_manager = InsiteService()