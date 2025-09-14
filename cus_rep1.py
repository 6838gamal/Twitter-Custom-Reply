import streamlit as st
import tweepy
import json
import os
import threading
import time
from dotenv import load_dotenv
from datetime import datetime, timedelta

# === تحميل المفاتيح من البيئة ===
load_dotenv()
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("ACCESS_TOKEN_SECRET")

# تسجيل الدخول لتويتر
auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
api = tweepy.API(auth)

DATA_FILE = "replies.json"

# دوال إدارة البيانات
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, ensure_ascii=False, indent=2)

activity_log = []
reply_times = {}  # لتحديد حالة المستخدم (تم الرد/جديد/بدون رد)

# === البوت في الخلفية ===
def run_bot():
    replied_ids = set()
    while True:
        try:
            mentions = api.mentions_timeline(count=20, tweet_mode="extended")
            data = load_data()
            for mention in mentions:
                user = mention.user.screen_name.lower()
                tweet_id = mention.id

                if tweet_id in replied_ids:
                    continue

                if user in data:
                    reply_text = f"@{user} {data[user]}"
                    api.update_status(status=reply_text, in_reply_to_status_id=tweet_id)
                    log_entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ✅ Replied to @{user}"
                    activity_log.append(log_entry)
                    reply_times[user] = datetime.now()
                    replied_ids.add(tweet_id)
        except Exception as e:
            activity_log.append(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ⚠️ Error: {e}")
        time.sleep(30)

# تشغيل البوت في Thread منفصل
threading.Thread(target=run_bot, daemon=True).start()

# === واجهة Streamlit ===
st.set_page_config(page_title="لوحة تحكم بوت تويتر", layout="wide")
st.title("💻 لوحة تحكم بوت تويتر الاحترافية")

data = load_data()

# ---- إدارة الردود ----
st.subheader("إدارة الردود")
col1, col2 = st.columns([2,1])
with col1:
    username = st.text_input("اسم المستخدم (بدون @)").lower().strip()
    reply = st.text_area("الرد المخصص")
with col2:
    if st.button("إضافة / تحديث"):
        if username and reply:
            data[username] = reply
            save_data(data)
            st.success(f"✅ تمت إضافة/تحديث الرد للمستخدم @{username}")
        else:
            st.warning("⚠️ أدخل جميع البيانات")

    if st.button("حذف المستخدم"):
        if username in data:
            del data[username]
            save_data(data)
            st.success(f"🗑️ تم حذف @{username}")
        else:
            st.warning("⚠️ المستخدم غير موجود")

# ---- فلترة حسب الحالة ----
st.subheader("عرض الردود حسب الحالة")
status_filter = st.selectbox("اختر الحالة", ["الكل","تم الرد 🟢","بدون رد 🟡","جديد 🔵"])

def get_user_status(user):
    now = datetime.now()
    if user in reply_times:
        delta = now - reply_times[user]
        if delta < timedelta(hours=24):
            return "تم الرد 🟢"
        else:
            return "بدون رد 🟡"
    else:
        return "جديد 🔵"

filtered_users = {}
for u,r in data.items():
    status = get_user_status(u)
    if status_filter=="الكل" or status_filter==status:
        filtered_users[u] = (r, status)

if filtered_users:
    for user, (reply_text, status) in filtered_users.items():
        color = "green" if status=="تم الرد 🟢" else "orange" if status=="بدون رد 🟡" else "blue"
        st.markdown(f"<span style='color:{color}'>**@{user}** → {reply_text} ({status})</span>", unsafe_allow_html=True)
else:
    st.write("لا يوجد ردود مطابقة للفلتر")

# ---- إحصائيات ----
st.subheader("إحصائيات")
st.metric("عدد الردود الحالية", len(data))
st.metric("عدد الأحداث في السجل", len(activity_log))

# ---- سجل النشاط ----
st.subheader("سجل النشاط (آخر 20 حدث)")
if activity_log:
    for log in reversed(activity_log[-20:]):
        st.write(log)
else:
    st.write("لا يوجد نشاط حتى الآن.")
