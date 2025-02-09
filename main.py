import os
import time
import logging
import schedule
import threading
from flask import Flask, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from telegram import Bot
from telegram.ext import Updater, CommandHandler

# Logging
logging.basicConfig(level=logging.INFO)

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN")
MS_USERNAME = os.getenv("MS_USERNAME")
MS_PASSWORD = os.getenv("MS_PASSWORD")
FORM_URL = os.getenv("FORM_URL")
DEFAULT_SCHEDULE_TIME = os.getenv("SCHEDULE_TIME", "10:00")

# Telegram Bot
bot = Bot(token=BOT_TOKEN)

# Flask App
app = Flask(__name__)

# Setup WebDriver (Headless Mode for Cloud)
options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

def fill_form(date, return_date, outing_time, return_time, purpose_option):
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(FORM_URL)

        # ✅ Login to Microsoft Forms
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "loginfmt"))).send_keys(MS_USERNAME)
        driver.find_element(By.ID, "idSIButton9").click()
        time.sleep(2)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "passwd"))).send_keys(MS_PASSWORD)
        driver.find_element(By.ID, "idSIButton9").click()
        time.sleep(3)

        # ✅ Fill Text Fields
        text_fields = driver.find_elements(By.CLASS_NAME, "-as-68")
        text_fields[0].send_keys("Kingsly Rufus K J")
        text_fields[1].send_keys("23BCS073")
        text_fields[2].send_keys("9942555337")
        text_fields[3].send_keys("207")
        text_fields[4].send_keys(outing_time)
        text_fields[5].send_keys(return_time)

        # ✅ Select Dropdown Options
        hostel_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@aria-labelledby='QuestionId_r29db15822bde4c848cfcd465dad7b0b5 QuestionInfo_r29db15822bde4c848cfcd465dad7b0b5']"))
        )
        hostel_dropdown.click()
        time.sleep(1)
        driver.find_element(By.XPATH, "//div[@role='option'][2]").click()

        outing_register_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@aria-labelledby='QuestionId_re944ec370e9b4cada53745fb23ddc612 QuestionInfo_re944ec370e9b4cada53745fb23ddc612']"))
        )
        outing_register_dropdown.click()
        time.sleep(1)
        driver.find_element(By.XPATH, "//div[@role='option'][1]").click()

        purpose_dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@aria-labelledby='QuestionId_rc485d02d818d43a9ae2d851a4f3e4afe QuestionInfo_rc485d02d818d43a9ae2d851a4f3e4afe']"))
        )
        purpose_dropdown.click()
        time.sleep(1)
        driver.find_element(By.XPATH, f"//div[@role='option'][{purpose_option}]").click()

        # ✅ Fill Date Fields
        outing_date_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id='DatePicker0-label']"))
        )
        outing_date_field.send_keys(date)

        return_date_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id='DatePicker7-label']"))
        )
        return_date_field.send_keys(return_date)

        # ✅ Submit Form
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Submit')]"))
        )
        submit_button.click()
        time.sleep(3)

        logging.info("✅ Form filled and submitted successfully.")
        driver.quit()
    except Exception as e:
        logging.error(f"❌ Error filling form: {e}")

# Telegram Command to Schedule

def schedule_fill(update, context):
    args = context.args
    if len(args) < 5:
        update.message.reply_text("Usage: /schedule <outing_date> <return_date> <outing_time> <return_time> <purpose_option> <schedule_time>")
        return

    date, return_date, outing_time, return_time, purpose_option, schedule_time = args[0], args[1], args[2], args[3], int(args[4]), args[5]

    schedule.every().day.at(schedule_time).do(fill_form, date, return_date, outing_time, return_time, purpose_option)
    update.message.reply_text(f"✅ Scheduled form autofill for {date} at {schedule_time}.")

# Flask API to Trigger Form
@app.route("/schedule", methods=["POST"])
def api_schedule():
    data = request.json
    date = data.get("outing_date", "")
    return_date = data.get("return_date", "")
    outing_time = data.get("outing_time", "")
    return_time = data.get("return_time", "")
    purpose_option = int(data.get("purpose_option", 1))
    schedule_time = data.get("schedule_time", DEFAULT_SCHEDULE_TIME)

    schedule.every().day.at(schedule_time).do(fill_form, date, return_date, outing_time, return_time, purpose_option)
    return jsonify({"status": "Form scheduled successfully.", "schedule_time": schedule_time})

# Start Telegram Bot
def start_telegram_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("schedule", schedule_fill))
    updater.start_polling()

if __name__ == "__main__":
    threading.Thread(target=start_telegram_bot).start()
    app.run(host="0.0.0.0", port=5000)
