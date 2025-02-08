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

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(token=BOT_TOKEN)

app = Flask(__name__)

MS_USERNAME = os.getenv("kingslyrufus.23cs@kct.ac.in")
MS_PASSWORD = os.getenv("Kingsly7532")
FORM_URL = "https://forms.office.com/pages/responsepage.aspx?id=loKLa_-92EqTrYS8vzhC9bKvBXTN0gZBlDaTlvDYFn5UOFhEN05BMzFYNzBDQVdDRjY1WTYzRUxZTS4u"

options = webdriver.ChromeOptions()
options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

def fill_form(text1, text2, date, dropdown):
    try:
        driver = webdriver.Chrome(options=options)
        driver.get(FORM_URL)

        # ✅ Login
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "loginfmt"))).send_keys(MS_USERNAME)
        driver.find_element(By.ID, "idSIButton9").click()
        time.sleep(2)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "passwd"))).send_keys(MS_PASSWORD)
        driver.find_element(By.ID, "idSIButton9").click()
        time.sleep(3)

        # ✅ Autofill Static Fields
        default_fields = ["Kingsly Rufus K J", "23BCS073", "9942555337", "207"]
        for idx, value in enumerate(default_fields):
            input_field = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "-as-68"))
            )[idx]
            input_field.send_keys(value)
            time.sleep(0.5)

        # ✅ Autofill User Fields
        user_fields = [text1, text2]
        for idx, value in enumerate(user_fields, start=4):
            input_field = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "-as-68"))
            )[idx]
            input_field.send_keys(value)
            time.sleep(0.5)

        # ✅ Select Dropdowns
        dropdown_1 = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@aria-labelledby, 'r29db15822bde4c848cfcd465dad7b0b5')]"))
        )
        dropdown_1.click()
        time.sleep(1)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='option'][2]"))
        ).click()

        dropdown_2 = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//div[contains(@aria-labelledby, 're944ec370e9b4cada53745fb23ddc612')]"))
        )
        dropdown_2.click()
        time.sleep(1)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[@role='option'][1]"))
        ).click()

        # ✅ Fill Date Field
        date_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//input[@aria-label='Date picker']"))
        )
        date_field.send_keys(date)

        logging.info("✅ Form filled successfully.")
        driver.quit()
    except Exception as e:
        logging.error(f"❌ Error filling form: {e}")

# Telegram Bot Commands
def schedule_fill(update, context):
    args = context.args
    if len(args) < 4:
        update.message.reply_text("Usage: /schedule <text1> <text2> <date> <dropdown>")
        return

    text1, text2, date, dropdown = args[0], args[1], args[2], args[3]
    schedule.every().day.at("10:00").do(fill_form, text1, text2, date, dropdown)
    update.message.reply_text(f"✅ Scheduled form autofill for {date} at 10:00 AM.")

# Flask API
@app.route("/schedule", methods=["POST"])
def api_schedule():
    data = request.json
    fill_form(data.get("text1", ""), data.get("text2", ""), data.get("date", ""), data.get("dropdown", ""))
    return jsonify({"status": "Form scheduled successfully."})

def start_telegram_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("schedule", schedule_fill))
    updater.start_polling()

if __name__ == "__main__":
    threading.Thread(target=start_telegram_bot).start()
    app.run(host="0.0.0.0", port=5000)
