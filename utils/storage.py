# utils.py
import json
import os

def save_phone(user_id, phone):
    """
    Saves the user's phone number to a JSON file.
    """
    data = {}
    if os.path.exists("users.json"):
        with open("users.json", "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                pass
    data[str(user_id)] = phone
    with open("users.json", "w", encoding="utf-8") as f:
        json.dump(data, f)

def get_phone(user_id):
    """
    Retrieves the user's phone number from the JSON file.
    """
    if not os.path.exists("users.json"):
        return None
    with open("users.json", "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
            return data.get(str(user_id))
        except json.JSONDecodeError:
            return None

def save_user_steps(user_steps: dict, file_path="user_step_log.json"):
    """
    Saves the user's steps to a JSON log file.
    """
    data = {}
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {}

    for user_id, steps in user_steps.items():
        data[user_id] = steps

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def normalize_phone_number(phone):
    """
    Normalizes a phone number to the '901...' format.
    """
    phone = phone.strip().replace(" ", "")
    if phone.startswith("+98"):
        phone = phone[3:]
    elif phone.startswith("0"):
        phone = phone[1:]
    elif phone.startswith("98"):
        phone = phone[2:]
    return phone

def load_users():
    """
    Loads all users from the users.json file.
    Returns an empty dictionary if the file does not exist or is empty/corrupted.
    """
    file_path = "users.json"
    if not os.path.exists(file_path):
        return {} # Return an empty dictionary if the file doesn't exist

    with open(file_path, "r", encoding="utf-8") as f:
        try:
            # Check if file is empty before loading JSON
            content = f.read()
            if not content:
                return {}
            return json.loads(content)
        except json.JSONDecodeError:
            # Handle cases where the JSON file is corrupted or malformed
            print(f"Warning: users.json is corrupted or empty. Returning empty dictionary.")
            return {}

def load_user_steps(file_path="user_step_log.json"):
    """
    Loads user steps from the user_step_log.json file.
    Returns an empty dictionary if the file does not exist or is empty/corrupted.
    """
    if not os.path.exists(file_path):
        return {}
    with open(file_path, "r", encoding="utf-8") as f:
        try:
            content = f.read()
            if not content:
                return {}
            return json.loads(content)
        except json.JSONDecodeError:
            print(f"Warning: {file_path} is corrupted or empty. Returning empty dictionary.")
            return {}