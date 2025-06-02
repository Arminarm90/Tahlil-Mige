# handlers.py
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import requests
from utils.storage import save_phone, get_phone, normalize_phone_number, load_users, load_user_steps, save_user_steps
from config import CHECK_PHONE_URL, DAY_CONTENT_BASE_URL, YOUR_TELEGRAM_ID, N8N_SUPPORT_WEBHOOK_URL
from services.subs import add_user_if_not_exists, days_left, check_subscription_active

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /start command, requests the user's phone number.
    """
    button = KeyboardButton("📱 ارسال شماره", request_contact=True)
    reply_markup = ReplyKeyboardMarkup([[button]], resize_keyboard=True, one_time_keyboard=True)
    await update.message.reply_text("برای شروع روی ارسال شماره کلیک کن 👇", reply_markup=reply_markup)

async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the shared contact, normalizes the phone number, and checks user allowance.
    """
    raw_phone = update.message.contact.phone_number
    phone = normalize_phone_number(raw_phone)
    user_id = update.effective_user.id
    
    save_phone(user_id, phone)
    
    try:
        res = requests.post(CHECK_PHONE_URL, json={"phone": phone})
        allowed = res.json().get("allowed")
    except Exception as e:
        await update.message.reply_text(f"❌ خطا در بررسی شماره. لطفاً دوباره امتحان کن. Error: {e}")
        return

    if allowed:
        add_user_if_not_exists(user_id, phone)
        if not check_subscription_active(update.effective_user.id):
            await update.message.reply_text("⛔️ اشتراک شما به پایان رسیده. لطفاً تمدید کنید.")
            return
        
        context.user_data["is_allowed"] = True
        welcome_text = f"""
    سلام {update.message.from_user.first_name} شما عضو باشگاه هستی،
    خوش اومدی 😎

    🔰 هر جا نیاز به کمک داشتی /support رو بزن
    🔰 و کانال اطلاع‌رسانی /channel رو دنبال کن تا رویدادهای باشگاه‌ رو از دست ندی!
    🔰 برای شروع تحلیل کسب‌وکارت روی /begin بزن.
        """
        await update.message.reply_text(welcome_text)
    else:
        await update.message.reply_text("❌ شما مجاز به استفاده از ربات نیستید. \n روی /support  بزن و مشکلت رو باهامون مطرح کن. ✋")
        
async def handle_main_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles selections from the main menu (text messages that are not commands).
    """
    text = update.message.text
    if not check_subscription_active(update.effective_user.id):
        await update.message.reply_text("⛔️ اشتراک شما به پایان رسیده. لطفاً تمدید کنید.")
        return
    
    if text == "📅 قدم‌ها":
        user_id = update.effective_user.id
        phone_number = get_phone(user_id)

        if not phone_number:
            await update.message.reply_text("اگه قدم هارو ندیدی دوباره بات رو /start  و شمارتو وارد کن. ❤️")
            return
        
        try:
            response = requests.post(CHECK_PHONE_URL, json={"phone": phone_number})
            data = response.json()
            
            active_steps = data.get("steps", [])

            if isinstance(active_steps, str):
                active_steps = [s.strip() for s in active_steps.split(",")]

            step_buttons = []
            for step in active_steps:
                step_number = step.replace("step ", "").strip()
                label = f"📅 قدم {step_number}"
                step_buttons.append([InlineKeyboardButton(label, callback_data=step_number)])

            await update.message.reply_text(
                "یکی از قدم‌ها رو انتخاب کن 👇",
                reply_markup=InlineKeyboardMarkup(step_buttons)
            )
        except Exception as e:
            await update.message.reply_text(f"خطا در دریافت قدم‌ها. لطفاً دوباره امتحان کن. Error: {e}")

    elif text == "📊 شروع":
        step_buttons = [
            [InlineKeyboardButton("📅 قدم اول", callback_data="1")],
        ]
        await update.message.reply_text("قدم اول، زیرساخت بقیه‌ی راهه؛ هرچی با دقت و حوصله‌ی بیشتری پیش بری، تحلیل  چیزهای بیشتری بهت می‌گه و نتیجه‌ی پایدارتری می‌سازی.", reply_markup=InlineKeyboardMarkup(step_buttons))
    
    elif text == "🆘 پشتیبانی":
        context.user_data["mode"] = "support"
        await update.message.reply_text("❓ سوالت رو برام بفرست، به زودی جواب می‌دیم.")

    elif text == "📢 کانال اطلاع‌رسانی":
        await update.message.reply_text("📢 به کانال ما بپیوند:\nhttps://t.me/tahlilmige")   
         
    elif text == "📤 ارسال تَسک":
        context.user_data["mode"] = "homework"
        await update.message.reply_text("📤 فایلت رو ارسال کن تا بررسی بشه.")
        
    elif text == "🕒 وضعیت اشتراک":
            user_id = update.effective_user.id
            if check_subscription_active(user_id):
                left = days_left(user_id)
                await update.message.reply_text(f"✅ اشتراک شما فعال است.\n🕒 {left} روز باقی‌مانده.")
            else:
                await update.message.reply_text("❌ اشتراک شما به پایان رسیده. برای تمدید با پشتیبانی تماس بگیر.")

async def handle_day_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles callback queries for day selection and fetches content.
    """
    query = update.callback_query
    await query.answer()
    selected_day = query.data

    if not check_subscription_active(update.effective_user.id):
        await context.bot.send_message(chat_id=query.message.chat.id, text="⛔️ اشتراک شما به پایان رسیده. لطفاً تمدید کنید.")
        return
    try:
        # Assuming DAY_CONTENT_BASE_URL expects the selected_day as a path parameter or in query
        # Based on the original code, it was sending it in json body, which is unusual for GET.
        # Let's adjust to common GET practice or maintain original if that's how the webhook works.
        # Original: res = requests.get(DAY_CONTENT_BASE_URL, json=selected_day)
        # If it's a GET, it's more likely to be a query parameter or path variable.
        # Sticking to the original behavior:
        res = requests.get(DAY_CONTENT_BASE_URL, json=selected_day)
        data = res.json()

        content = data.get("content", "دیتایی موحود نیست!")
    
        if content:
            await context.bot.send_message(chat_id=query.message.chat.id, text=content)
        else:
            await context.bot.send_message(chat_id=query.message.chat.id, text="محتوایی برای این قدم پیدا نشد.")

    except Exception as e:
        await context.bot.send_message(chat_id=query.message.chat.id, text=f"خطا در دریافت محتوا. لطفاً بعداً امتحان کن. Error: {e}")

async def main_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name

    # تنها پیام‌های متنی را به AI ارسال می‌کنیم
    if update.message.text: 
        message_text = update.message.text
    else:
        # اگر پیام متنی نبود (فایل، عکس، ویس و غیره)، به AI نمی‌فرستیم
        # می‌توانید تصمیم بگیرید که به ادمین فوروارد کنید یا پیام خطا بدهید
        if mode == "support":
            await update.message.reply_text("🤖 متاسفم، در حال حاضر فقط می‌توانم به پیام‌های متنی پاسخ دهم.")
            context.user_data["mode"] = None # خروج از حالت پشتیبانی AI
            return

    if mode == "support":
        # 1. پیام را به n8n Webhook ارسال کنید
        payload = {
            "user_id": user_id,
            "username": username,
            "first_name": first_name,
            "message": message_text,
            "chat_id": update.message.chat.id # برای بازگشت پاسخ به همین چت
        }

        try:
            # ارسال غیرهمزمان به n8n برای جلوگیری از بلوکه شدن ربات
            # از requests.post استفاده می‌کنیم، اما اگر می‌خواهید کاملاً async باشد، باید از aiohttp استفاده کنید.
            # برای سادگی، requests.post را استفاده می‌کنیم و پاسخ اولیه را سریع می‌دهیم.
            requests.post(N8N_SUPPORT_WEBHOOK_URL, json=payload, timeout=5) # timeout اضافه کنید

            await update.message.reply_text("✅ سوال شماارسال شد. لطفا منتظر پاسخ باشید.")

            context.user_data["mode"] = None # حالت را به حالت عادی برگردانید

        except requests.exceptions.RequestException as e:
            print(f"Error sending message to n8n webhook: {e}")
            await update.message.reply_text(f"❌ خطایی رخ داد. لطفاً دوباره امتحان کنید.")
            # Optional: Forward to YOUR_TELEGRAM_ID for manual review
            await context.bot.send_message(
                chat_id=YOUR_TELEGRAM_ID,
                text=f"AI integration failed for user {user_id}. Message: {message_text}\nError: {e}"
            )
            context.user_data["mode"] = None
    else:
        # کدهای موجود برای "homework" و "handle_main_menu_selection"
        # ... (همانند قبل)
        if mode == "homework":
            try:
                if update.message.text or update.message.document or update.message.photo or update.message.voice:
                    await context.bot.forward_message(
                        chat_id=YOUR_TELEGRAM_ID,
                        from_chat_id=update.message.chat.id,
                        message_id=update.message.message_id
                    )
                    await update.message.reply_text("✅ با موفقیت ارسال شد.")
                else:
                    await update.message.reply_text("❗ لطفاً متن، عکس یا فایل ارسال کن.")
                context.user_data["mode"] = None
            except Exception as e:
                await update.message.reply_text(f"❌ خطا در ارسال. لطفاً دوباره امتحان کن. Error: {e}")
        else:
            await handle_main_menu_selection(update, context)

async def begin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /begin command.
    """
    if not context.user_data.get("is_allowed"):
        await update.message.reply_text("❌ شما مجاز به استفاده از این دستور نیستید. لطفاً ابتدا شماره‌ت رو ارسال کن.")
        return
    if not check_subscription_active(update.effective_user.id):
        await update.message.reply_text("⛔️ اشتراک شما به پایان رسیده. لطفاً تمدید کنید.")
        return
    step_buttons = [
        [InlineKeyboardButton("📅 قدم اول", callback_data="1")],
    ]
    await update.message.reply_text("قدم اول، زیرساخت بقیه‌ی راهه؛ هرچی با دقت و حوصله‌ی بیشتری پیش بری، تحلیل  چیزهای بیشتری بهت می‌گه و نتیجه‌ی پایدارتری می‌سازی.", reply_markup=InlineKeyboardMarkup(step_buttons))
    
async def steps_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /steps command, showing active steps.
    """
    if not context.user_data.get("is_allowed"):
        await update.message.reply_text("❌ شما مجاز به استفاده از این دستور نیستید. لطفاً ابتدا شماره‌ت رو ارسال کن.")
        return
    if not check_subscription_active(update.effective_user.id):
        await update.message.reply_text("⛔️ اشتراک شما به پایان رسیده. لطفاً تمدید کنید.")
        return
        
    user_id = update.effective_user.id
    phone_number = get_phone(user_id)

    if not phone_number:
        await update.message.reply_text("اگه قدم هارو ندیدی دوباره بات رو /start  و شمارتو وارد کن. ❤️")
        return
        
    try:
        response = requests.post(CHECK_PHONE_URL, json={"phone": phone_number})
        data = response.json()
            
        active_steps = data.get("steps", [])

        if isinstance(active_steps, str):
            active_steps = [s.strip() for s in active_steps.split(",")]

        step_buttons = []
        for step in active_steps:
            step_number = step.replace("step ", "").strip()
            label = f"📅 قدم {step_number}"
            step_buttons.append([InlineKeyboardButton(label, callback_data=step_number)])

        await update.message.reply_text(
            "یکی از قدم‌ها رو انتخاب کن 👇",
            reply_markup=InlineKeyboardMarkup(step_buttons)
        )
    except Exception as e:
        await update.message.reply_text(f"خطا در دریافت قدم‌ها. لطفاً دوباره امتحان کن. Error: {e}")

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /support command.
    """
    context.user_data["mode"] = "support"
    await update.message.reply_text("❓ سوالت رو برام بفرست، به زودی جواب می‌دیم.")

async def channel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /channel command.
    """
    if not context.user_data.get("is_allowed"):
        await update.message.reply_text("❌ شما مجاز به استفاده از این دستور نیستید. لطفاً ابتدا شماره‌ت رو ارسال کن.")
        return
    await update.message.reply_text("📢 به کانال ما بپیوند:\nhttps://t.me/tahlilmige")

async def homework_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /homework command.
    """
    if not context.user_data.get("is_allowed"):
        await update.message.reply_text("❌ شما مجاز به استفاده از این دستور نیستید. لطفاً ابتدا شماره‌ت رو ارسال کن.")
        return
    context.user_data["mode"] = "homework"
    await update.message.reply_text("📤 فایلت رو ارسال کن تا بررسی بشه.")     
    
async def subscription_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles the /subscription command, showing subscription status.
    """
    user_id = update.effective_user.id
    if check_subscription_active(user_id):
        days = days_left(user_id)
        await update.message.reply_text(f"✅ اشتراک شما فعاله.\n🗓 {days} روز تا پایان باقی‌ست.")
    else:
        await update.message.reply_text("❌ اشتراک شما به پایان رسیده یا غیرفعاله.")