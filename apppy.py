import streamlit as st
import google.generativeai as genai
import json
import os
from PIL import Image
import speech_recognition as sr

# ==============================
# API KEY (AN TOÀN)
# ==============================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("❌ Thiếu GEMINI_API_KEY (vào Streamlit Secrets để thêm)")
    st.stop()

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash-latest")

# ==============================
# PAGE CONFIG
# ==============================

st.set_page_config(
    page_title="AI Learning Debugger",
    page_icon="🧠",
    layout="wide"
)

# ==============================
# CSS (CHỮ RÕ + ĐẸP)
# ==============================

st.markdown("""
<style>

/* BACKGROUND */
.stApp {
    background: linear-gradient(135deg, #020617, #0f172a);
    color: #f8fafc;
}

/* TEXT */
p, span, label {
    color: #e2e8f0 !important;
    font-size: 16px;
}

/* INPUT */
textarea, input {
    background: #020617 !important;
    color: #f8fafc !important;
    border: 1px solid #38bdf8 !important;
}

/* HEADER */
h1, h2, h3 {
    color: #f1f5f9 !important;
}

/* TITLE */
h1 {
    text-align: center;
    font-weight: 700;
    background: linear-gradient(90deg,#38bdf8,#818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

/* CARD */
.card {
    background: rgba(30, 41, 59, 0.7);
    backdrop-filter: blur(12px);
    padding: 20px;
    border-radius: 16px;
    margin-bottom: 20px;
    border: 1px solid rgba(148,163,184,0.2);
}

/* BUTTON */
.stButton>button {
    width: 100%;
    background: linear-gradient(90deg,#22c55e,#4ade80);
    border-radius: 12px;
    padding: 12px;
    font-weight: 600;
    border: none;
}
.stButton>button:hover {
    transform: scale(1.05);
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: #020617;
}

</style>
""", unsafe_allow_html=True)

# ==============================
# TITLE
# ==============================

st.title("🧠 AI Learning Debugger")

# ==============================
# MEMORY SYSTEM
# ==============================

MEMORY_FILE = "mistakes.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE,"r",encoding="utf-8") as f:
            return json.load(f)
    return []

def save_memory(data):
    with open(MEMORY_FILE,"w",encoding="utf-8") as f:
        json.dump(data,f,ensure_ascii=False,indent=2)

memory = load_memory()

# ==============================
# SESSION
# ==============================

if "selected_memory" not in st.session_state:
    st.session_state.selected_memory = None

# ==============================
# SIDEBAR
# ==============================

with st.sidebar:
    st.markdown("## 🧠 Mistake Memory")

    for i, m in enumerate(reversed(memory)):
        short = m["problem"][:25] + "..."
        if st.button(f"📄 {short}", key=f"mem_{i}"):
            st.session_state.selected_memory = m

# ==============================
# INPUT MODE
# ==============================

st.header("1️⃣ Nhập đề bài")

mode = st.radio("", ["Text", "Image", "Audio"], horizontal=True)

problem = ""
audio_text = ""

# ==============================
# INPUT
# ==============================

st.markdown('<div class="card">', unsafe_allow_html=True)

if mode == "Text":
    problem = st.text_area("Nhập đề bài", height=150)

elif mode == "Image":
    image = st.file_uploader("Upload ảnh", type=["png","jpg","jpeg"])
    if image:
        img = Image.open(image)
        st.image(img)

elif mode == "Audio":
    audio_file = st.file_uploader("Upload audio", type=["wav","mp3","m4a"])
    if audio_file:
        st.audio(audio_file)

        r = sr.Recognizer()
        with open("temp.wav","wb") as f:
            f.write(audio_file.read())

        try:
            with sr.AudioFile("temp.wav") as source:
                data = r.record(source)
                audio_text = r.recognize_google(data, language="vi-VN")
            st.success(audio_text)
        except:
            st.warning("Không nhận dạng được audio")

st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# SOLUTION
# ==============================

st.header("2️⃣ Cách suy nghĩ")
solution = st.text_area("", height=200)

# ==============================
# AI ANALYZE (FIX LỖI)
# ==============================

def analyze(problem, solution, audio_text):

    full_problem = problem + "\n" + audio_text

    prompt = f"""
Bạn là AI phân tích lỗi tư duy học tập.

ĐỀ BÀI:
{full_problem}

CÁCH SUY NGHĨ:
{solution}

Ngắn gọn:

1. Sai ở đâu
2. Vì sao sai
3. Hổng gì
4. 2 bài luyện
5. Cách đúng
"""

    try:
        response = model.generate_content(prompt)

        if hasattr(response, "text") and response.text:
            return response.text
        else:
            return "⚠️ AI không trả về nội dung"

    except Exception as e:
        return f"❌ Lỗi AI: {str(e)}"

# ==============================
# BUTTON
# ==============================

if st.button("🔍 Phân tích"):

    if not solution:
        st.warning("⚠️ Nhập cách suy nghĩ")
    else:

        with st.spinner("Đang phân tích..."):
            result = analyze(problem, solution, audio_text)

        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 📊 Kết quả")
        st.write(result)
        st.markdown('</div>', unsafe_allow_html=True)

        memory.append({
            "problem": problem if problem else audio_text,
            "solution": solution,
            "analysis": result
        })

        save_memory(memory)

# ==============================
# MEMORY VIEW
# ==============================

if st.session_state.selected_memory:

    m = st.session_state.selected_memory

    st.markdown('<div class="card">', unsafe_allow_html=True)

    st.markdown("### 📌 Đề bài")
    st.write(m["problem"])

    st.markdown("### 💭 Suy nghĩ")
    st.write(m["solution"])

    st.markdown("### 🔍 Phân tích")
    st.write(m["analysis"])

    if st.button("❌ Đóng"):
        st.session_state.selected_memory = None
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)