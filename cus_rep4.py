import os
import json
import tweepy
import streamlit as st

# ===================== إعداد ملف البيانات =====================
DATA_FILE = "replies.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ===================== إعداد الاتصال مع تويتر =====================
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("ACCESS_SECRET")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")

auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth)

# v2 client
client = tweepy.Client(bearer_token=BEARER_TOKEN,
                       consumer_key=API_KEY,
                       consumer_secret=API_SECRET,
                       access_token=ACCESS_TOKEN,
                       access_token_secret=ACCESS_SECRET)

# ===================== الواجهة =====================
st.set_page_config(page_title="Twitter Custom Bot", layout="wide")

tabs = st.tabs(["📋 إدارة الردود", "✍️ النشر", "📊 السجلات", "⚙️ الإعدادات"])

# --------------------- إدارة الردود ---------------------
with tabs[0]:
    st.header("إدارة الردود على مستخدمين محددين")

    data = load_data()
    st.subheader("إضافة رد جديد")
    username = st.text_input("اسم المستخدم (بدون @)")
    reply = st.text_area("الرد المخصص")

    if st.button("إضافة / تعديل"):
        if username.strip() and reply.strip():
            data[username.strip()] = reply.strip()
            save_data(data)
            st.success(f"تم حفظ الرد للمستخدم @{username}")
        else:
            st.error("يرجى إدخال اسم المستخدم والرد")

    st.subheader("قائمة الردود الحالية")
    if data:
        for user, rep in data.items():
            st.write(f"@{user} ➝ {rep}")
    else:
        st.info("لا يوجد ردود محفوظة حالياً")

# --------------------- النشر ---------------------
with tabs[1]:
    st.header("نشر تغريدة جديدة")
    tweet_text = st.text_area("محتوى التغريدة")
    if st.button("نشر التغريدة"):
        try:
            response = client.create_tweet(text=tweet_text)
            st.success(f"تم نشر التغريدة بنجاح ✅ (ID: {response.data['id']})")
        except Exception as e:
            st.error(f"فشل النشر ❌: {e}")
            st.info("⚠️ تحقق من مستوى الصلاحيات (Essential / Elevated) في حسابك على Twitter API.")

# --------------------- السجلات ---------------------
with tabs[2]:
    st.header("السجلات")
    st.write("هنا يمكن عرض السجلات (Logs) لاحقاً مثل الردود الناجحة أو الأخطاء.")
    st.info("لم يتم تفعيل حفظ السجلات بعد. يمكن تطويرها لتخزين كل عملية رد/نشر.")

# --------------------- الإعدادات ---------------------
with tabs[3]:
    st.header("إعدادات الاتصال")
    st.write("🔑 مفاتيح API المستخدمة (من متغيرات البيئة):")
    st.code(f"""
API_KEY = {API_KEY}
API_SECRET = {API_SECRET[:5]}...{'*' * 5 if API_SECRET else ''}
ACCESS_TOKEN = {ACCESS_TOKEN}
ACCESS_SECRET = {ACCESS_SECRET[:5]}...{'*' * 5 if ACCESS_SECRET else ''}
BEARER_TOKEN = {BEARER_TOKEN[:10]}...{'*' * 5 if BEARER_TOKEN else ''}
""")

    st.subheader("مستوى صلاحيات API")
    st.markdown("""
- **Essential**: قراءة التغريدات العامة فقط (محدودية عالية).  
- **Elevated**: يسمح بالنشر والردود (معظم الخصائص الأساسية).  
- **Academic Research**: وصول موسع للبحث والتحليل.  
    """)
    st.info("⚠️ إذا ظهر خطأ 403 عند النشر أو الرد، فهذا يعني أن الخطة الحالية لا تدعم العملية.")
