
def login_without_2fa():
    try:
        WebDriverWait(driver, 10).until(EC.title_is("Contra Costa Community College District - Portal Access"))
        # Now driver.title will be correct if the wait passes
        actual_title = driver.title
        time.sleep(2)
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

    time.sleep(2)
