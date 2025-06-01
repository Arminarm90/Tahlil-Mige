import gspread
from datetime import datetime, timedelta
from oauth2client.service_account import ServiceAccountCredentials

# اتصال اولیه
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("n8n-user-access-cbb88f774dbe.json", scope)
client = gspread.authorize(creds)
sheet = client.open("subscriptions").worksheet("Sheet1")  # اسم دقیق شیت


# فقط اگه کاربر جدید باشه، اضافه می‌کنه. اگر قبلاً بوده کاری نمی‌کنه
def add_user_if_not_exists(user_id, phone):
    today = datetime.today().date()
    expire = today + timedelta(days=30)

    records = sheet.get_all_records()
    for record in records:
        if str(record["user_id"]) == str(user_id):
            return  # کاربر قبلاً ثبت شده، پس هیچی نکن

    # کاربر جدید → اضافه کن
    sheet.append_row([str(user_id), phone, str(today), str(expire), "TRUE"])


def check_subscription_active(user_id):
    records = sheet.get_all_records()
    today = datetime.today().date()
    for record in records:
        if str(record["user_id"]) == str(user_id):
            expire = datetime.strptime(record["expire_date"], "%Y-%m-%d").date()
            if today <= expire and record["active"].upper() == "TRUE":
                return True
    return False


def days_left(user_id):
    records = sheet.get_all_records()
    today = datetime.today().date()
    for record in records:
        if str(record["user_id"]) == str(user_id):
            expire = datetime.strptime(record["expire_date"], "%Y-%m-%d").date()
            return max((expire - today).days, 0)
    return 0
