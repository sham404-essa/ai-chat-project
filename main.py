"""
שלב א – לולאת צ'אט בסיסית (CLI)
אפליקציית צ'אט מול ה-API של המכללה (IAC Student API).
"""

import sys
import requests

# ----------------------------------------------------------------------
# הגדרות בסיס
# ----------------------------------------------------------------------
BASE_URL = "https://server.iac.ac.il/api/v1/studentapi"
GENERATE_KEY_URL = f"{BASE_URL}/generate_key"
CHAT_URL = f"{BASE_URL}/chat/completions"

MAX_COMPLETION_TOKENS = 500   # הגבלת אורך התשובה
REQUEST_TIMEOUT = 60          # שניות עד ניתוק הבקשה
EXIT_WORDS = {"exit", "quit", "bye", "خروج", "יציאה"}


# ----------------------------------------------------------------------
# 1. הפקת מפתח גישה
# ----------------------------------------------------------------------
def generate_key(user_id: str, password: str):
    """שולח ת.ז + סיסמה ומחזיר מפתח גישה (sk-std-...) או None במקרה כישלון."""
    try:
        resp = requests.post(
            GENERATE_KEY_URL,
            json={"id": user_id, "password": password},
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        data = resp.json()
        key = data.get("key") or data.get("api_key") or data.get("token")
        if not key:
            print("⚠️  התקבלה תשובה אך לא נמצא מפתח. תשובת השרת:")
            print(data)
            return None
        return key
    except requests.exceptions.HTTPError:
        print(f"❌ שגיאת אימות / שרת ({resp.status_code}). בדוק ת.ז וסיסמה.")
    except requests.exceptions.ConnectionError:
        print("❌ בעיית רשת – אין חיבור לשרת.")
    except requests.exceptions.Timeout:
        print("❌ השרת לא הגיב בזמן (timeout).")
    except Exception as e:
        print(f"❌ שגיאה לא צפויה: {e}")
    return None


def get_api_key():
    """נותן למשתמש לבחור: להדביק מפתח קיים או להפיק חדש."""
    print("בחר אופן התחברות:")
    print("  1 = יש לי כבר מפתח (sk-std-...)")
    print("  2 = הפק מפתח חדש (ת.ז + סיסמת פורטל)")
    choice = input("בחירה: ").strip()

    if choice == "1":
        return input("הדבק את המפתח: ").strip()

    user_id = input("תעודת זהות: ").strip()
    password = input("סיסמת פורטל: ").strip()
    key = generate_key(user_id, password)
    if not key:
        sys.exit("לא ניתן היה להפיק מפתח. צא ונסה שוב.")
    print("✅ מפתח הופק בהצלחה.\n")
    return key


# ----------------------------------------------------------------------
# 2. שליחת הודעה ל-API
# ----------------------------------------------------------------------
def send_message(api_key: str, messages: list):
    """שולח את כל היסטוריית ההודעות ומחזיר את תוכן התשובה של המודל."""
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {
        "messages": messages,
        "max_completion_tokens": MAX_COMPLETION_TOKENS,
    }

    try:
        resp = requests.post(
            CHAT_URL, json=payload, headers=headers, timeout=REQUEST_TIMEOUT
        )

        if resp.status_code == 401:
            print("❌ מפתח לא תקין או שפג תוקפו (401).")
            return None
        if resp.status_code == 429:
            print("⚠️  חרגת ממכסת הטוקנים / יותר מדי בקשות (429). חכה ונסה שוב.")
            return None
        resp.raise_for_status()

        data = resp.json()
        answer = data["choices"][0]["message"]["content"]

        quota = data.get("iac_quota_status")
        if quota:
            print(f"\n📊 מכסה: {quota}")

        return answer

    except requests.exceptions.ConnectionError:
        print("❌ בעיית רשת – לא ניתן להגיע לשרת.")
    except requests.exceptions.Timeout:
        print("❌ השרת לא הגיב בזמן (timeout).")
    except (KeyError, IndexError):
        print("❌ מבנה התשובה לא צפוי:")
        print(resp.text)
    except Exception as e:
        print(f"❌ שגיאה לא צפויה: {e}")
    return None


# ----------------------------------------------------------------------
# 3. לולאת הצ'אט הראשית
# ----------------------------------------------------------------------
def chat_loop(api_key: str):
    messages = []  # היסטוריית השיחה
    print("=" * 50)
    print("💬 צ'אט עם המודל. הקלד 'exit' כדי לצאת.")
    print("=" * 50)

    while True:
        user_input = input("\n👤 אתה: ").strip()

        if not user_input:
            continue
        if user_input.lower() in EXIT_WORDS:
            print("👋 להתראות!")
            break

        messages.append({"role": "user", "content": user_input})

        answer = send_message(api_key, messages)

        if answer is None:
            messages.pop()
            continue

        print(f"\n🤖 מודל: {answer}")
        messages.append({"role": "assistant", "content": answer})


# ----------------------------------------------------------------------
# נקודת הכניסה
# ----------------------------------------------------------------------
def main():
    api_key = get_api_key()
    chat_loop(api_key)


if __name__ == "__main__":
    main()