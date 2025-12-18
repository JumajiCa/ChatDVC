# util_funcs.py
import json
import os

COOKIE_FILE = "insite_cookies.json"


def save_cookies(driver):
    cookies = driver.get_cookies()
    with open(COOKIE_FILE, 'w') as file:
        json.dump(cookies, file)
    print("Cookies saved successfully.")


def load_cookies(driver, domain_url):
    if not os.path.exists(COOKIE_FILE):
        return False

    try:
        # Selenium requires you to be on the domain before adding cookies
        driver.get(domain_url)
        with open(COOKIE_FILE, 'r') as file:
            cookies = json.load(file)
            for cookie in cookies:
                try:
                    driver.add_cookie(cookie)
                except Exception as e:
                    print(f"Error adding cookie: {e}")
        return True
    except Exception as e:
        print(f"Error loading cookies: {e}")
        return False


def clean(s):
    if not s: return ""
    return " ".join(s.replace("\n", " ").split())



# def get_email_code():
#     return input("Please input your 4-digit code sent to your email!")
#
# def clean(s):
#     return " ".join(s.replace("\n", " ").split())