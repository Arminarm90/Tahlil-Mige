# tasks.py
import asyncio
import time
import requests
import os
from utils.storage import load_users, load_user_steps, save_user_steps
from config import CHECK_PHONE_URL

async def check_and_notify_steps(application):
    """
    Periodically checks for new active steps for users and notifies them.
    """
    first_time = False

    if not os.path.exists("user_step_log.json"):
        print("⚠️ اولین اجرا - قدم‌ها ثبت می‌شن ولی نوتیف نمی‌فرسته.")
        users = load_users()
        initial_steps = {}
        for user_id, phone in users.items():
            try:
                response = requests.post(CHECK_PHONE_URL, json={"phone": phone})
                data = response.json()
                raw_steps = data.get("steps", [])
                if isinstance(raw_steps, str):
                    steps = [s.strip() for s in raw_steps.split(",")]
                elif isinstance(raw_steps, list):
                    steps = raw_steps
                else:
                    steps = []
                initial_steps[user_id] = steps
            except Exception as e:
                print(f"Error initializing steps for user {user_id}: {e}")
                continue
        save_user_steps(initial_steps)
        first_time = True

    while True:
        if first_time:
            first_time = False
            # برای اولین اجرا، 30 ثانیه (یا 24 ساعت واقعی 86400) صبر کنید
            await asyncio.sleep(86400) # For testing, use 30; for production, use 86400
            continue

        users = load_users()
        previous_steps = load_user_steps()
        updated_steps = {}

        for user_id, phone in users.items():
            try:
                response = requests.post(CHECK_PHONE_URL, json={"phone": phone})
                data = response.json()

                raw_steps = data.get("steps", [])

                if isinstance(raw_steps, str):
                    active_steps = [s.strip() for s in raw_steps.split(",")]
                elif isinstance(raw_steps, list):
                    active_steps = raw_steps
                else:
                    active_steps = []

                old_steps = previous_steps.get(user_id, [])
                new_steps = list(set(active_steps) - set(old_steps))

                for step in new_steps:
                    step_number = step.replace("step ", "").strip()
                    
                    # اضافه کردن شرط برای جلوگیری از ارسال نوتیفیکیشن برای "step 1"
                    if step_number == "1":
                        print(f"Skipping notification for step 1 for user {user_id}")
                        continue # از این گام صرف‌نظر کرده و به گام بعدی می‌رود
                        
                    await application.bot.send_message(
                        chat_id=int(user_id),
                        text=f"✅ قدم {step_number} برات فعال شده. بدو سراغش 📢"
                    )
                    time.sleep(0.5) # Small delay to avoid hitting rate limits

                updated_steps[user_id] = active_steps

            except Exception as e:
                print(f"خطا برای یوزر {user_id}: {e}")
        save_user_steps(updated_steps)
        # برای اجرای واقعی، از 86400 ثانیه (24 ساعت) استفاده کنید
        await asyncio.sleep(86400)  # For testing, use 30; for production, use 86400