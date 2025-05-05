#!/usr/bin/env python3

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
import time
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from dotenv import load_dotenv
import os

load_dotenv()
uci_id = os.getenv("UCI_ID")
uci_password = os.getenv("UCI_PASSWORD")

# Setup Chrome options
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")

# # Setup Chrome options for headless environment
# options = webdriver.ChromeOptions()
# options.add_argument('--headless')
# options.add_argument('--no-sandbox')
# options.add_argument('--disable-dev-shm-usage')
# options.add_argument('--disable-gpu')
# options.add_argument('--window-size=1920,1080')

# Use Service object
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=options)

# Open the pickleball booking page
driver.get("https://my.campusrec.uci.edu/booking")

wait = WebDriverWait(driver, 10)

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
time.sleep(1)
wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "container-image-link-item"))).click()
time.sleep(1)

# Get today's date and add 2 days
# book_for_date = 5
from datetime import datetime, timedelta
today = datetime.now()
book_for_date = (today + timedelta(days=2)).day
# book_for_date = 7
print(f"📅 Booking for date: {book_for_date}")


# date_buttons = driver.find_elements(By.CLASS_NAME, "d-flex justify-content-center buttons")
date_buttons = driver.find_elements(By.CSS_SELECTOR, "div.d-flex.justify-content-center button.single-date-select-button")
# if last element of date_buttons attribute value is < book_for_date then reload the page and get date_buttons again
latest_date = int(date_buttons[-1].get_attribute("data-day"))
while latest_date < book_for_date:
    print(f"⚠️ Latest date {latest_date} is less than {book_for_date}. Reloading page...")
    driver.refresh()
    time.sleep(1)
    date_buttons = driver.find_elements(By.CSS_SELECTOR, "div.d-flex.justify-content-center button.single-date-select-button")
    latest_date = int(date_buttons[-1].get_attribute("data-day"))

print(f"📅 Found {len(date_buttons)} date buttons.")
# reverse for loop on date_buttons
button = date_buttons[-1]
button.get_attribute("data-day")
print(f"📅 Clicking date button for {button.get_attribute('data-day')}")
button.click()
time.sleep(1)

facility_buttons = driver.find_elements(By.CSS_SELECTOR, "#tabBookingFacilities button")
print(f"🛠️ Found {len(facility_buttons)} facilities to check...")

booked_slots_count = 0
max_slots_to_book = 10
booked_times = []  # Track which times have been booked

preferred_times = ["5 - 6 PM", "6 - 7 PM", "7 - 8 PM", "8 - 9 PM", "9 - 9:55 PM"]

for i in range(len(facility_buttons)):
    try:
        # Re-locate buttons in case DOM refreshed
        facility_buttons = driver.find_elements(By.CSS_SELECTOR, "#tabBookingFacilities button")
        facility_buttons[i].click()
        print(f"\n🔍 Checking facility {i+1}/{len(facility_buttons)}...")

        # Wait extra time for DOM + network latency
        time.sleep(1)

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
                if any(pref in time_label for pref in preferred_times) and time_label not in booked_times:
                    button = slot.find_element(By.CLASS_NAME, "booking-slot-action-item").find_element(By.TAG_NAME, "button")
                    if "disabled" not in button.get_attribute("class"):
                        print(f"🎯 Available slot for '{time_label}' — booking...")
                        button.click()
                        booked_times.append(time_label)
                        print(f"✅ Slot booked ({booked_slots_count + 1}/{max_slots_to_book}).")
                        booked_slots_count += 1
                        if booked_slots_count >= max_slots_to_book:
                            print(f"🎉 Successfully booked {booked_slots_count} slots. Exiting.")
                            exit(0)
                        else:
                            print(f"🔍 Continuing to search for {max_slots_to_book - booked_slots_count} more slots...")
                            # Wait for page to update after booking
                            continue  # Move to next slot
                elif time_label in booked_times:
                    print(f"⏭️ Skipping '{time_label}' - already booked a slot at this time.")

            except (StaleElementReferenceException, TimeoutException):
                print("⚠️ Slot became stale or failed to load.")
                continue

    except Exception as e:
        print(f"⚠️ Error on facility tab {i+1}: {e}")
        continue

# 3. Add this at the end of your script
if booked_slots_count > 0:
    print(f"✓ Booking completed with {booked_slots_count}/{max_slots_to_book} slots booked.")
else:
    print("\n❌ No available slots found in any facility.")

# Optional: send email/notification on success or failure
# Cleanup
# driver.quit()


def send_email(subject, message, recipients, only_to_you_on_failure=False):
    """
    Send email notification about booking results

    Parameters:
    - subject: Email subject line
    - message: Email body content
    - recipients: List of email addresses to send to
    - only_to_you_on_failure: If True and 'failure' is in subject, only send to first recipient
    """
    sender_email = os.getenv("EMAIL_ADDRESS")  # Add this to your .env file
    sender_password = os.getenv("EMAIL_PASSWORD")  # Add this to your .env file

    # Check if this is a failure message and only_to_you_on_failure is True
    if only_to_you_on_failure and "failure" in subject.lower():
        recipients = [recipients[0]]  # Only send to your email (first in list)

    # Create message
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = ", ".join(recipients)
    msg['Subject'] = subject

    # Attach message body
    msg.attach(MIMEText(message, 'plain'))

    try:
        # Gmail SMTP server and port
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Enable TLS encryption

        # Login with your Gmail credentials
        server.login(sender_email, sender_password)

        # Send email
        server.sendmail(sender_email, recipients, msg.as_string())
        server.quit()
        print(f"✉️ Email notification sent to {', '.join(recipients)}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

# Email recipients
your_email = "moniln@uci.edu"  # Replace with your email
friend_email = "shubhij1@uci.edu"  # Replace with your friend's email
recipients = [your_email, friend_email]

# Summary and email notification
if booked_slots_count > 0:
    # Success message
    success_message = f"✓ Pickleball Booking Completed!\n\n"
    success_message += f"Successfully booked {booked_slots_count} slots:\n\n"

    # Add details for each booked slot
    for i, time_slot in enumerate(booked_times):
        success_message += f"{i+1}. Time: {time_slot}\n"

    print(success_message)

    # Send success email to both you and your friend
    send_email(
        subject="Pickleball Court Booking Success",
        message=success_message,
        recipients=recipients
    )
else:
    # Failure message
    failure_message = "❌ No available slots found in any facility."
    print(failure_message)

    # Send failure email only to you
    send_email(
        subject="Pickleball Court Booking Failure",
        message=failure_message,
        recipients=recipients,
        only_to_you_on_failure=True
    )



