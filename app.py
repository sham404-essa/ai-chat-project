"""
שלב ב – עטיפה בממשק Streamlit
ממשק צ'אט ויזואלי שעוטף את לוגיקת הצ'אט מול ה-API של המכללה.
המפתח נטען מקובץ .env (לא נשמר בקוד).

הרצה:
    streamlit run app.py
"""

import os
import requests
import streamlit as st
from dotenv import load_dotenv

# טעינת המפתח מקובץ .env
load_dotenv()
API_KEY = os.getenv("IAC_API_KEY")

# ----------------------------------------------------------------------
# הגדרות בסיס
# ----------------------------------------------------------------------
CHAT_URL = "https://server.iac.ac.il/api/v1/studentapi/chat/completions"
MAX_COMPLETION_TOKENS = 1000
REQUEST_TIMEOUT = 60


# ----------------------------------------------------------------------
# שליחת הודעה ל-API
# ----------------------------------------------------------------------
def send_message(messages: list):
    """שולח את כל היסטוריית ההודעות ומחזיר (תשובה, הודעת שגיאה)."""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "messages": messages,
        "max_completion_tokens": MAX_COMPLETION_TOKENS,
    }
    try:
        resp = requests.post(
            CHAT_URL, json=payload, headers=headers, timeout=REQUEST_TIMEOUT
        )
        if resp.status_code == 401:
            return None, "מפתח לא תקין או שפג תוקפו (401)."
        if resp.status_code == 429:
            return None, "חרגת ממכסת הטוקנים / יותר מדי בקשות (429). חכה ונסה שוב."
        resp.raise_for_status()

        data = resp.json()
        answer = data["choices"][0]["message"]["content"]

        # שמירת מצב המכסה להצגה בצד
        st.session_state.quota = data.get("iac_quota_status")

        # טיפול במקרה שהתשובה ריקה
        if not answer:
            return None, "המודל החזיר תשובה ריקה. נסה שוב או נסח מחדש."
        return answer, None

    except requests.exceptions.ConnectionError:
        return None, "בעיית רשת – לא ניתן להגיע לשרת."
    except requests.exceptions.Timeout:
        return None, "השרת לא הגיב בזמן (timeout)."
    except (KeyError, IndexError):
        return None, "מבנה התשובה לא צפוי."
    except Exception as e:
        return None, f"שגיאה לא צפויה: {e}"


# ----------------------------------------------------------------------
# אתחול ה-state (שמירה בין הרצות)
# ----------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "quota" not in st.session_state:
    st.session_state.quota = None


# ----------------------------------------------------------------------
# כותרת
# ----------------------------------------------------------------------
st.title("💬 AI Chat")
st.caption("צ'אט מול מודל השפה של המכללה (IAC Student API)")

# בדיקה שיש מפתח
if not API_KEY:
    st.error("לא נמצא מפתח API. ודא שקיים קובץ .env עם IAC_API_KEY.")
    st.stop()


# ----------------------------------------------------------------------
# סרגל צד – איפוס ומכסה
# ----------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ אפשרויות")

    if st.button("🗑️ איפוס שיחה"):
        st.session_state.messages = []
        st.rerun()

    if st.session_state.quota:
        st.divider()
        st.subheader("📊 מכסה")
        st.json(st.session_state.quota)


# ----------------------------------------------------------------------
# הצגת היסטוריית השיחה
# ----------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])


# ----------------------------------------------------------------------
# שדה קלט ושליחה
# ----------------------------------------------------------------------
prompt = st.chat_input("כתוב הודעה...")

if prompt:
    # הצגת והוספת הודעת המשתמש
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # שליחה ל-API וקבלת תשובה
    with st.chat_message("assistant"):
        with st.spinner("חושב..."):
            answer, err = send_message(st.session_state.messages)
        if answer:
            st.markdown(answer)
            st.session_state.messages.append(
                {"role": "assistant", "content": answer}
            )
        else:
            st.error(err)
            st.session_state.messages.pop()