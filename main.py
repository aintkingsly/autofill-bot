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
BOT_TOKEN = os.getenv("7608530963:AAFWfKSsE1rG7XwHVJwjaU2iJ9C6MS6Y5rw")
MS_USERNAME = os.getenv("kingslyrufus.23cs@kct.ac.in")
MS_PASSWORD = os.getenv("Kingsly7532")
FORM_URL = "https://forms.office.com/pages/responsepage.aspx?id=loKLa_-92EqTrYS8vzhC9bKvBXTN0gZBlDaTlvDYFn5UOFhEN05BMzFYNzBDQVdDRjY1WTYzRUxZTS4u"

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

# Function to fill and submit the form
def fill_form(date, dropdown_option):
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

        # ✅ Select User-Provided Dropdown Option (UPDATED)
        dropdown = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@aria-labelledby='QuestionId_r29db15822bde4c848cfcd465dad7b0b5 QuestionInfo_r29db15822bde4c848cfcd465dad7b0b5']"))
        )
        dropdown.click()
        time.sleep(1)

        selected_option = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, f"//div[@role='option'][{dropdown_option}]"))
        )
        selected_option.click()

        # ✅ Fill User-Provided Date Field (UPDATED)
        date_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@id='DatePicker0-label']"))
        )
        date_field.send_keys(date)
        time.sleep(1)

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
    if len(args) < 3:
        update.message.reply_text("Usage: /schedule <date> <dropdown_option> <time>")
        return

    date, dropdown_option, schedule_time = args[0], int(args[1]), args[2]

    schedule.every().day.at(schedule_time).do(fill_form, date, dropdown_option)
    update.message.reply_text(f"✅ Scheduled form autofill for {date} at {schedule_time}.")

# Flask API to Trigger Form
@app.route("/schedule", methods=["POST"])
def api_schedule():
    data = request.json
    date = data.get("date", "")
    dropdown_option = int(data.get("dropdown_option", 1))
    schedule_time = data.get("schedule_time", "10:00")

    schedule.every().day.at(schedule_time).do(fill_form, date, dropdown_option)
    return jsonify({"status": "Form submission scheduled successfully."})

# Start Telegram Bot
def start_telegram_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("schedule", schedule_fill))
    updater.start_polling()

if __name__ == "__main__":
    threading.Thread(target=start_telegram_bot).start()
    app.run(host="0.0.0.0", port=5000)
