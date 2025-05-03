from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import time

from dotenv import load_dotenv
import os

load_dotenv()
uci_id = os.getenv("UCI_ID")
uci_password = os.getenv("UCI_PASSWORD")

# Setup Chrome options
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

# Use Service object
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Open the pickleball booking page
driver.get("https://my.campusrec.uci.edu/booking")

wait = WebDriverWait(driver, 20)

# STEP 2: Click on the pickleball image
wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "container-image-link-item"))).click()

# STEP 3: Click the UCI NetID login button
try:
    uci_button = wait.until(EC.element_to_be_clickable((
        By.CSS_SELECTOR, "button.btn-sso-shibboleth"
    )))
    uci_button.click()
except Exception as e:
    print("❌ Could not find or click UCI NetID login button")
    driver.save_screenshot("error_login_button.png")
    raise e

# Wait for UCI login page to load and fill credentials manually
print("🔐 Please complete UCI login and approve Duo request on your phone...")
try:
    wait.until(EC.presence_of_element_located((By.ID, "j_username"))).send_keys(uci_id)  # Replace with your UCInetID
    wait.until(EC.presence_of_element_located((By.ID, "j_password"))).send_keys(uci_password)  # Replace securely
    wait.until(EC.element_to_be_clickable((By.NAME, "submit_form"))).click()
    print("🔐 Submitted UCInetID and password.")
except Exception as e:
    print("❌ Failed to submit UCI credentials.")
    driver.save_screenshot("error_ucinetid_login.png")
    raise e


try:
    print("📲 Waiting for Duo push approval...")
    WebDriverWait(driver, 180).until(
        EC.element_to_be_clickable((By.ID, "trust-browser-button"))
    ).click()
    print("🔒 Clicked 'Yes, this is my device'")
except Exception as e:
    print("⚠️ 'Yes, this is my device' button not shown or click failed (possibly already trusted).")
    driver.save_screenshot("duo_device_trust_failed.png")

print("✅ Duo approved and dashboard loaded")

# Wait until correct date is selected (e.g., tomorrow or specific date)
# Optional: Modify this to dynamically click the appropriate date tab
time.sleep(20)
wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "container-image-link-item"))).click()
time.sleep(20)

facility_buttons = driver.find_elements(By.CSS_SELECTOR, "#tabBookingFacilities button")
print(f"🛠️ Found {len(facility_buttons)} facilities to check...")

preferred_times = ["7 - 8 PM", "8 - 9 PM", "9 - 9:55 PM"]

for i in range(len(facility_buttons)):
    try:
        # Re-locate buttons in case DOM refreshed
        facility_buttons = driver.find_elements(By.CSS_SELECTOR, "#tabBookingFacilities button")
        facility_buttons[i].click()
        print(f"\n🔍 Checking facility {i+1}/{len(facility_buttons)}...")

        # Wait extra time for DOM + network latency
        time.sleep(2.5)

        # Ensure booking slots are loaded
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CLASS_NAME, "booking-slot-item"))
        )

        slots = driver.find_elements(By.CLASS_NAME, "booking-slot-item")
        print(f"📦 Found {len(slots)} booking slots.")

        for slot in slots:
            try:
                time_label = slot.find_element(By.TAG_NAME, "p").text.strip()
                print(f"🕒 Slot time: {time_label}")
                if any(pref in time_label for pref in preferred_times):
                    button = slot.find_element(By.CLASS_NAME, "booking-slot-action-item").find_element(By.TAG_NAME, "button")
                    if "disabled" not in button.get_attribute("class"):
                        print(f"🎯 Available slot for '{time_label}' — booking...")
                        button.click()
                        print("✅ Slot booked. Exiting.")
                        exit(0)
            except (StaleElementReferenceException, TimeoutException):
                print("⚠️ Slot became stale or failed to load.")
                continue

    except Exception as e:
        print(f"⚠️ Error on facility tab {i+1}: {e}")
        continue

print("\n❌ No available slots found in any facility.")

# Optional: send email/notification on success or failure
# Cleanup
# driver.quit()
