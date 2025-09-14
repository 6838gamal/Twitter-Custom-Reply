import os
import json
import tweepy
import streamlit as st
import threading
import time
from datetime import datetime

# =========================
# إعدادات المفاتيح
# =========================
API_KEY = os.getenv("TWITTER_API_KEY")
API_KEY_SECRET = os.getenv("TWITTER_API_KEY_SECRET")
BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
ACCESS_TOKEN_SECRET = os.getenv("TWITTER_ACCESS_TOKEN_SECRET")

DATA_FILE = "replies.json"
LOG_FILE = "activity.log"

# =========================
# وظائف التخزين
# =========================
def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def log_event(event: str):
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {event}\n")

# =========================
# إعداد تويتر
# =========================
def create_client():
    try:
        client = tweepy.Client(
            bearer_token=BEARER_TOKEN,
            consumer_key=API_KEY,
            consumer_secret=API_KEY_SECRET,
            access_token=ACCESS_TOKEN,
            access_token_secret=ACCESS_TOKEN_SECRET,
            wait_on_rate_limit=True
        )
        return client
    except Exception as e:
        st.error(f"❌ خطأ في إنشاء الاتصال: {e}")
        return None

client = create_client()

def get_access_level():
    try:
        client.get_me()
        return "Elevated"
    except Exception as e:
        if "403" in str(e):
            return "Basic"
        return "Unknown"

access_level = get_access_level()

# =========================
# الخدمة الخلفية (مراقبة وردود)
# =========================
auto_reply_running = False

def auto_reply_worker():
    global auto_reply_running
    if access_level != "Elevated":
        log_event("⚠️ الرد التلقائي غير مفعل لأن الخطة Basic.")
        return

    last_seen_id = None
    auto_reply_running = True
    log_event("🚀 تم تشغيل خدمة الرد التلقائي")

    while auto_reply_running:
        try:
            me = client.get_me().data
            mentions = client.get_users_mentions(me.id, since_id=last_seen_id, tweet_fields=["author_id"])
            if mentions and mentions.data:
                data = load_data()
                for mention in reversed(mentions.data):
                    username = client.get_user(id=mention.author_id).data.username.lower()
                    if username in data:
                        reply_text = f"@{username} {data[username]}"
                        client.create_tweet(in_reply_to_tweet_id=mention.id, text=reply_text)
                        log_event(f"✅ تم الرد على @{username}: {reply_text}")
                    last_seen_id = mention.id
        except Exception as e:
            log_event(f"❌ خطأ في الخدمة الخلفية: {e}")

        time.sleep(30)  # كل نصف دقيقة

# =========================
# واجهة Streamlit
# =========================
st.set_page_config(page_title="Twitter Bot Dashboard", layout="wide")
st.title("🤖 Twitter Custom Reply Bot")

# مستوى الوصول
if access_level == "Elevated":
    st.success("✅ لديك Elevated Access: يمكن الرد + التغريد تلقائيًا")
elif access_level == "Basic":
    st.warning("⚠️ لديك Basic Access: قراءة فقط، لا يمكن الرد أو التغريد تلقائيًا")
else:
    st.error("❓ لم أستطع تحديد الخطة")

# تحميل الردود
data = load_data()

# إدارة الردود
st.subheader("📌 إدارة الردود")
with st.form("add_reply_form"):
    username = st.text_input("اسم المستخدم (بدون @)")
    reply = st.text_area("الرد المخصص")
    submitted = st.form_submit_button("إضافة/تحديث")
    if submitted and username and reply:
        data[username.lower()] = reply
        save_data(data)
        st.success(f"تم حفظ الرد للمستخدم: {username}")
        log_event(f"✏️ تحديث الرد لـ @{username}")

if data:
    st.write("### الردود الحالية")
    st.json(data)

# التغريد
st.subheader("📝 إرسال تغريدة")
if access_level == "Elevated":
    tweet_text = st.text_area("اكتب تغريدتك هنا")
    if st.button("نشر"):
        try:
            client.create_tweet(text=tweet_text)
            st.success("✅ تم النشر")
            log_event(f"📝 نشر تغريدة: {tweet_text}")
        except Exception as e:
            st.error(f"❌ خطأ: {e}")
else:
    st.info("ℹ️ غير متاح إلا مع Elevated Access")

# التحكم في الرد التلقائي
st.subheader("🤝 الرد التلقائي")
if access_level == "Elevated":
    col1, col2 = st.columns(2)
    with col1:
        if st.button("تشغيل الرد التلقائي"):
            if not auto_reply_running:
                threading.Thread(target=auto_reply_worker, daemon=True).start()
                st.success("🚀 الرد التلقائي قيد التشغيل")
            else:
                st.info("✅ الرد التلقائي يعمل بالفعل")
    with col2:
        if st.button("إيقاف الرد التلقائي"):
            auto_reply_running = False
            st.warning("🛑 تم إيقاف الرد التلقائي")
else:
    st.info("⚠️ يتطلب Elevated Access")

# سجل الأحداث
st.subheader("📜 سجل الأنشطة")
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        logs = f.read().splitlines()
        st.text_area("Activity Log", "\n".join(logs[-20:]), height=200)
else:
    st.info("لا يوجد سجل بعد.")

# رفع / تنزيل الردود
st.subheader("📂 النسخ الاحتياطي للردود")
col1, col2 = st.columns(2)
with col1:
    uploaded = st.file_uploader("رفع ملف replies.json", type="json")
    if uploaded:
        new_data = json.load(uploaded)
        save_data(new_data)
        st.success("✅ تم استيراد الردود بنجاح")
with col2:
    st.download_button("تنزيل الردود الحالية", json.dumps(data, ensure_ascii=False, indent=2), "replies.json")
