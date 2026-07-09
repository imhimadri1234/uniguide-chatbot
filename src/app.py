import re
import os
import io
import fitz  # PyMuPDF
import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from dotenv import load_dotenv
from groq import Groq

import easyocr
_ocr_reader = None
from streamlit_mic_recorder import speech_to_text


from gtts import gTTS
import base64

def text_to_speech(text, lang='en'):
    """Convert text to speech and return base64 audio"""
    try:
        clean_text = re.sub(r'[*#_`]', '', text)
        clean_text = clean_text[:500]
        tts = gTTS(text=clean_text, lang=lang, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        audio_base64 = base64.b64encode(audio_buffer.read()).decode()
        return audio_base64
    except Exception as e:
        st.error(f"TTS Error: {str(e)}")
        return None
    
def get_ocr_reader():
    global _ocr_reader
    if _ocr_reader is None:
        _ocr_reader = easyocr.Reader(['en'], gpu=False)
    return _ocr_reader


from pathlib import Path

env_path = Path("C:/Users/Himadri/OneDrive/Documents/Desktop/rag_university_chatbot/.env")
load_dotenv(dotenv_path=env_path, override=True)
os.environ["HUGGINGFACEHUB_API_TOKEN"] = os.getenv("HF_TOKEN", "")

# ─── PAGE CONFIG ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="UniGuide — West Bengal University Chatbot",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CUSTOM CSS ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Sora', sans-serif;
}

/* Background */
.stApp {
    background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    min-height: 100vh;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: rgba(255,255,255,0.04) !important;
    border-right: 1px solid rgba(255,255,255,0.08);
    backdrop-filter: blur(20px);
}

[data-testid="stSidebar"] * {
    color: #e0e0e0 !important;
}

/* Main container */
.main .block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 900px;
}

/* Title */
.hero-title {
    font-size: 2.2rem;
    font-weight: 700;
    background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.2rem;
}

.hero-sub {
    color: rgba(255,255,255,0.5);
    font-size: 0.95rem;
    margin-bottom: 1.5rem;
    font-weight: 300;
}

/* Chat messages */
.msg-user {
    display: flex;
    justify-content: flex-end;
    margin: 0.6rem 0;
}
.msg-user .bubble {
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: white;
    padding: 0.75rem 1.1rem;
    border-radius: 18px 18px 4px 18px;
    max-width: 75%;
    font-size: 0.92rem;
    line-height: 1.6;
    box-shadow: 0 4px 20px rgba(99,102,241,0.3);
}
.msg-bot {
    display: flex;
    justify-content: flex-start;
    margin: 0.6rem 0;
    gap: 0.6rem;
    align-items: flex-start;
}
.bot-avatar {
    width: 32px;
    height: 32px;
    background: linear-gradient(135deg, #34d399, #059669);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.9rem;
    flex-shrink: 0;
    margin-top: 2px;
}
.msg-bot .bubble {
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.1);
    color: #e8e8f0;
    padding: 0.75rem 1.1rem;
    border-radius: 4px 18px 18px 18px;
    max-width: 80%;
    font-size: 0.92rem;
    line-height: 1.7;
    backdrop-filter: blur(10px);
}

/* Suggestion chips */
.chip-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
    margin: 0.8rem 0;
}
.chip {
    background: rgba(99,102,241,0.15);
    border: 1px solid rgba(99,102,241,0.4);
    color: #a78bfa;
    padding: 0.3rem 0.75rem;
    border-radius: 20px;
    font-size: 0.78rem;
    cursor: pointer;
    transition: all 0.2s;
    font-family: 'Sora', sans-serif;
}
.chip:hover {
    background: rgba(99,102,241,0.3);
    border-color: #a78bfa;
}

/* Input */
.stChatInput > div {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 14px !important;
}
.stChatInput input {
    color: white !important;
    font-family: 'Sora', sans-serif !important;
}
/* Info cards */
.info-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 12px;
    padding: 1rem;
    margin: 0.5rem 0;
}
.info-card h4 {
    color: #a78bfa;
    margin: 0 0 0.4rem 0;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.info-card p {
    color: #c4c4d4;
    margin: 0;
    font-size: 0.88rem;
}

/* Divider */
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
    margin: 1rem 0;
}

/* Scrollable chat area */
.chat-container {
    height: 45vh;
    overflow-y: auto;
    padding: 0.5rem;
    scrollbar-width: thin;
    scrollbar-color: rgba(99,102,241,0.4) transparent;
}
.chat-container::-webkit-scrollbar { width: 4px; }
.chat-container::-webkit-scrollbar-thumb {
    background: rgba(99,102,241,0.4);
    border-radius: 4px;
}

/* PDF upload area */
[data-testid="stFileUploader"] {
    background: rgba(255,255,255,0.03) !important;
    border: 1px dashed rgba(255,255,255,0.15) !important;
    border-radius: 12px !important;
    color: #a0a0b0 !important;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #6366f1, #8b5cf6) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Sora', sans-serif !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(99,102,241,0.4) !important;
}

/* Selectbox */
[data-testid="stSelectbox"] > div > div {
    background: rgba(255,255,255,0.06) !important;
    border-color: rgba(255,255,255,0.15) !important;
    color: white !important;
    border-radius: 10px !important;
}

/* Tags */
.tag-green {
    background: rgba(52,211,153,0.15);
    color: #34d399;
    border: 1px solid rgba(52,211,153,0.3);
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}
.tag-blue {
    background: rgba(96,165,250,0.15);
    color: #60a5fa;
    border: 1px solid rgba(96,165,250,0.3);
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
}
.tag-purple {
    background: rgba(167,139,250,0.15);
    color: #a78bfa;
    border: 1px solid rgba(167,139,250,0.3);
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
}

/* Welcome box */
.welcome-box {
    background: linear-gradient(135deg, rgba(99,102,241,0.1), rgba(139,92,246,0.05));
    border: 1px solid rgba(99,102,241,0.25);
    border-radius: 16px;
    padding: 1.4rem;
    margin-bottom: 1rem;
}
.welcome-box h3 {
    color: #a78bfa;
    margin: 0 0 0.5rem 0;
    font-size: 1.1rem;
}
.welcome-box p {
    color: rgba(255,255,255,0.6);
    margin: 0;
    font-size: 0.88rem;
    line-height: 1.6;
}

/* Auth */
.auth-box {
    max-width: 400px;
    margin: 8vh auto;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 20px;
    padding: 2.5rem;
    backdrop-filter: blur(20px);
}

/* Make mic button align perfectly with chat input */
div[data-testid="stHorizontalBlock"] {
    align-items: flex-end !important;
    gap: 4px !important;
    margin-bottom: -3.2rem !important;
    margin-bottom: -1rem !important;
}
div[data-testid="stHorizontalBlock"] button[kind="secondary"] {
    background: rgba(255,255,255,0.06) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    border-radius: 12px !important;
    color: white !important;
    height: 44px !important;
    font-size: 1.1rem !important;
    padding: 0 !important;
    margin-bottom: 0 !important;
}
div[data-testid="stHorizontalBlock"] button[kind="secondary"]:hover {
    background: rgba(99,102,241,0.3) !important;
    border-color: #a78bfa !important;
}
</style>
""", unsafe_allow_html=True)

# ─── AUTHENTICATION ──────────────────────────────────────────────────────────
import sys
sys.path.append(os.path.dirname(__file__))
from login_page import show_login_page
from register_page import show_register_page

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_page" not in st.session_state:
    st.session_state.current_page = "login"

if not st.session_state.logged_in:
    if st.session_state.current_page == "login":
        show_login_page()
    else:
        show_register_page()
    st.stop()

# ─── GROQ CLIENT ────────────────────────────────────────────────────────────
@st.cache_resource
def get_groq_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))
# ─── LANGUAGE TRANSLATION ────────────────────────────────────────────────────
from deep_translator import GoogleTranslator

def detect_bengali(text):
    bengali_range = range(0x0980, 0x09FF)
    return any(ord(char) in bengali_range for char in text)

def translate_to_english(text):
    try:
        return GoogleTranslator(source='bn', target='en').translate(text)
    except Exception as e:
        return text

def translate_to_bengali(text):
    try:
        # Pre-replace technical terms before translation
        replacements = {
            "University of Calcutta": "কলকাতা বিশ্ববিদ্যালয়",
            "Calcutta University": "কলকাতা বিশ্ববিদ্যালয়",
            "Jadavpur University": "যাদবপুর বিশ্ববিদ্যালয়",
            "University of Kalyani": "কল্যাণী বিশ্ববিদ্যালয়",
            "Kalyani University": "কল্যাণী বিশ্ববিদ্যালয়",
            "West Bengal": "পশ্চিমবঙ্গ",
            "MBA": "এমবিএ",
            "MCA": "এমসিএ",
            "M.Tech": "এম.টেক",
            "B.Tech": "বি.টেক",
            "M.Sc": "এম.এস.সি",
            "B.Sc": "বি.এস.সি",
            "M.A": "এম.এ",
            "B.A": "বি.এ",
            "B.Ed": "বি.এড",
            "M.Ed": "এম.এড",
            "M.Phil": "এম.ফিল",
            "Ph.D": "পিএইচডি",
            "PhD": "পিএইচডি",
            "LLM": "এলএলএম",
            "LLB": "এলএলবি",
            "BCA": "বিসিএ",
            "BBA": "বিবিএ",
            "M.Com": "এম.কম",
            "B.Com": "বি.কম",
            "B.Pharm": "বি.ফার্ম",
            "M.Pharm": "এম.ফার্ম",
            "Physics": "পদার্থবিজ্ঞান",
            "Computer Science": "কম্পিউটার বিজ্ঞান",
            "Mathematics": "গণিত",
            "Chemistry": "রসায়ন",
            "Biology": "জীববিজ্ঞান",
            "Engineering": "ইঞ্জিনিয়ারিং",
            "Management": "ম্যানেজমেন্ট",
            "Data Science": "ডেটা সায়েন্স",
            "seats": "আসন",
            "fees": "ফি",
            "eligibility": "যোগ্যতা",
            "admission": "ভর্তি",
            "duration": "সময়কাল",
            "GATE": "গেট",
            "WBJEE": "ডব্লিউবিজেইই",
            "NET": "নেট",
            "SET": "সেট",
        }
        for eng, bn in replacements.items():
            text = text.replace(eng, bn)

        max_chunk = 2000
        if len(text) <= max_chunk:
            translated = GoogleTranslator(source='en', target='bn').translate(text)
            translated = translated if translated else text
        else:
            chunks = [text[i:i+max_chunk] for i in range(0, len(text), max_chunk)]
            translated = " ".join([GoogleTranslator(source='en', target='bn').translate(c) for c in chunks])

        # Fix post-translation errors
        post_fixes = {
            # University name fixes
            "রাজনীতি বিশ্ববিদ্যালয়": "কলকাতা বিশ্ববিদ্যালয়",
            "কল্যাণী কলেজ": "কল্যাণী বিশ্ববিদ্যালয়",
            "যাদবপুর কলেজ": "যাদবপুর বিশ্ববিদ্যালয়",
            "কলকাতা কলেজ": "কলকাতা বিশ্ববিদ্যালয়",
            "কলকাতার বিশ্ববিদ্যালয়": "কলকাতা বিশ্ববিদ্যালয়",
            "কল্যাণের বিশ্ববিদ্যালয়": "কল্যাণী বিশ্ববিদ্যালয়",
            "জাদবপুর বিশ্ববিদ্যালয়": "যাদবপুর বিশ্ববিদ্যালয়",

            # Subject name fixes
            "প্রযুক্তিবিদ্যায়": "পদার্থবিজ্ঞানে",
            "প্রযুক্তি বিজ্ঞান": "পদার্থবিজ্ঞান",
            "শারীরিক বিজ্ঞান": "পদার্থবিজ্ঞান",
            "ভৌত বিজ্ঞান": "পদার্থবিজ্ঞান",
            "পদার্থবিদ্যা": "পদার্থবিজ্ঞান",
            "কম্পিউটার বিজ্ঞান বিজ্ঞান": "কম্পিউটার বিজ্ঞান",
            "তথ্য বিজ্ঞান": "ডেটা সায়েন্স",
            "ব্যবস্থাপনা বিজ্ঞান": "ম্যানেজমেন্ট",
            "আইন বিজ্ঞান": "আইন",
            "ঔষধ বিজ্ঞান": "ফার্মেসি",
            "রসায়ন বিজ্ঞান": "রসায়ন",
            "গণিত বিজ্ঞান": "গণিত",

            # Course name fixes
            "মাস্টার অফ বিজনেস অ্যাডমিনিস্ট্রেশন": "এমবিএ",
            "মাস্টার অফ কম্পিউটার অ্যাপ্লিকেশন": "এমসিএ",
            "ব্যাচেলর অফ টেকনোলজি": "বি.টেক",
            "মাস্টার অফ টেকনোলজি": "এম.টেক",
            "ডক্টর অফ ফিলোসফি": "পিএইচডি",
            "স্নাতকোত্তর": "পিজি",
            "স্নাতক": "ইউজি",

            # Common wrong translations
            "আসন সংখ্যা সংখ্যা": "আসন সংখ্যা",
            "ফি ফি": "ফি",
            "যোগ্যতা যোগ্যতা": "যোগ্যতা",
            "ভর্তি ভর্তি": "ভর্তি",
            "বিশ্ববিদ্যালয় বিশ্ববিদ্যালয়": "বিশ্ববিদ্যালয়",
        }
        for wrong, correct in post_fixes.items():
            translated = translated.replace(wrong, correct)

        return translated
    except Exception as e:
        return text
# ─── HELPERS ────────────────────────────────────────────────────────────────
def normalize(text):
    text = text.lower()
    text = re.sub(r'[^a-z0-9 ]', '', text)
    return text

def word_match(word, text):
    return re.search(r'\b' + re.escape(word) + r'\b', text) is not None

# ─── COURSE ALIASES ─────────────────────────────────────────────────────────
course_alias = {
    "ba": ["ba", "b.a", "bachelor of arts","B.A."],
    "bsc": ["bsc", "b.sc", "bachelor of science"],
    "bcom": ["bcom", "b.com", "bachelor of commerce"],
    "btech": ["btech", "b.tech", "b tech"],
    "be": ["be", "b.e"],
    "bca": ["bca"],
    "bba": ["bba"],
    "bed": ["bed", "b.ed", "B.Ed.","bachelor of education", "b.ed."],
    "bpharm": ["bpharm", "b.pharm"],
    "llb": ["llb"],
    "ma": ["ma", "m.a","M.A."],
    "msc": ["msc", "m.sc"],
    "mcom": ["mcom", "m.com"],
    "mtech": ["mtech", "m.tech"],
    "me": ["me", "m.e"],
    "mba": ["mba"],
    "mca": ["mca", "master of computer application"],
    "med": ["med", "m.ed","M.Ed."],
    "mpharm": ["mpharm", "m.pharm"],
    "llm": ["llm"],
    "mphil": ["mphil", "m.phil"],
    "mbbs": ["mbbs", "medical"],
    "phd": ["phd", "ph.d","Ph.D."],
    "blibisc": ["bachelor of library and information science","B.Lib.I.Sc.","b.lib.i.sc."],
    "mlibisc": ["Master of Library & Information Science","M.Lib.I.Sc.","m.lib.i.sc"]
}

INTEREST_SUGGESTIONS = {
    "computers": ["What are the best CS courses in KU?", "Compare MCA in KU and JU", "Fees for M.Tech CSE in KU"],
    "engineering": ["B.Tech options in Jadavpur University", "Compare M.E. courses in JU", "GATE based admissions in JU"],
    "arts": ["M.A. Bengali in CU fees", "Compare MA English in JU and CU", "PhD in Bengali admission process"],
    "science": ["MSc Physics seats in CU", "MSc Data Science in KU", "Compare MSc courses across universities"],
    "management": ["MBA fees in KU", "Which university is better for MBA?", "MBA eligibility and admission"],
    "education": ["B.Ed in JU and KU comparison", "M.Ed eligibility in Jadavpur", "PhD Education admission process"],
    "pharmacy": ["B.Pharm in Jadavpur fees", "M.Pharm eligibility in JU", "Pharmaceutical Technology courses"],
    "law": ["LL.M. fees in KU", "Law courses available in KU", "LLM admission process"],
}

# ─── LOAD DATA ───────────────────────────────────────────────────────────────
@st.cache_resource
def load_rag_system():
    data_files = {
        "calcutta": "data/cu.txt",
        "jadavpur": "data/ju.txt",
        "kalyani": "data/ku.txt",
    }
    documents = []
    for uni, path in data_files.items():
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        courses = re.split(r"\n\s*\n+", text)
        for c in courses:
            c = c.strip()
            if len(c) > 50:
                documents.append(Document(page_content=c))

    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    db = FAISS.from_documents(documents, embeddings)
    return db

# ─── PARSE COURSE ─────────────────────────────────────────────────────────
def parse_course(text):
    data = {}
    for line in text.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            if key in ["university name", "university"]:
                data["university"] = value
            else:
                data[key] = value
    return data

# ─── FILTER COURSES ───────────────────────────────────────────────────────
def filter_courses(courses, universities=None, detected_course=None):
    filtered = []
    for data in courses:
        uni = normalize(data.get("university", ""))
        course = normalize(data.get("course name", ""))
        if universities:
            if not any(u in uni for u in universities):
                continue
        if detected_course:
            aliases = [normalize(a) for a in course_alias[detected_course]]
            if not any(word_match(a, course) for a in aliases):
                continue
        filtered.append(data)
    return filtered

# ─── DETECT ENTITIES ──────────────────────────────────────────────────────
def detect_entities(query):
    nq = normalize(query)
    universities = []
    if re.search(r'\bcu\b', nq) or "calcutta" in nq:
        universities.append("calcutta")
    if re.search(r'\bju\b', nq) or "jadavpur" in nq:
        universities.append("jadavpur")
    if re.search(r'\bku\b', nq) or "kalyani" in nq:
        universities.append("kalyani")

    detected_course = None
    for key, aliases in course_alias.items():
        for alias in aliases:
            if word_match(normalize(alias), nq):
                detected_course = key
                break
        if detected_course:
            break

    intent_map = {
        "eligibility": "eligibility", "fees": "fees", "seat": "seats",
        "duration": "duration", "admission": "admission", "level": "level",
        "department": "department", "category": "course category",
        "application": "application fees", "source": "source",
    }
    intents = list({field for kw, field in intent_map.items() if kw in nq})
    return universities, detected_course, intents

# ─── DETECT INTEREST ──────────────────────────────────────────────────────
def detect_interest(query):
    nq = query.lower()
    for topic, suggestions in INTEREST_SUGGESTIONS.items():
        if topic in nq:
            return topic, suggestions
    keyword_map = {
        "computers": ["computer", "cs", "cse", "mca", "software", "coding", "programming", "it", "data science"],
        "engineering": ["engineer", "btech", "b.tech", "mtech", "m.tech", "gate", "mechanical", "civil", "electrical"],
        "arts": ["arts", "literature", "bengali", "english", "history", "language"],
        "science": ["physics", "chemistry", "biology", "science", "msc", "zoology", "botany"],
        "management": ["management", "mba", "business", "finance", "marketing"],
        "education": ["education", "teaching", "b.ed", "m.ed", "teacher"],
        "pharmacy": ["pharmacy", "pharma", "drug", "medicine", "b.pharm", "m.pharm"],
        "law": ["law", "llm", "llb", "legal"],
    }
    for topic, keywords in keyword_map.items():
        if any(kw in nq for kw in keywords):
            return topic, INTEREST_SUGGESTIONS[topic]
    return None, []

# ─── GROQ ANSWER ──────────────────────────────────────────────────────────
def ask_groq(question, context, chat_history=None):
    client = get_groq_client()
    history_text = ""
    if chat_history:
        for msg in chat_history[-4:]:
            role = "Student" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content']}\n"

    system_prompt = """You are UniGuide, an intelligent and friendly university admission assistant for West Bengal universities — University of Calcutta (CU), Jadavpur University (JU), and University of Kalyani (KU).

Your job:
- Answer ONLY what the student specifically asked — if they ask fees, give ONLY fees. If they ask admission, give ONLY admission. Do NOT add extra fields they didn't ask for.
- If multiple questions are asked, answer ALL of them one by one clearly
- ONLY use the data provided below — never guess or say "typically"
- When multiple courses of same type exist (e.g. multiple B.Tech branches), list ALL of them
- If data is missing for a specific course, say "Data not available in our records" — do NOT say "check the official website" as the main answer
- Compare universities honestly when asked
- Suggest the best option with reasons when asked
- Use a warm, helpful, advisor-like tone
- Format your answers with clear structure (use bullet points or sections when needed)
- Always end with a helpful next step suggestion"""
    prompt = f"""{history_text}

University Data:
{context}

Student Question: {question}

Important: If the University Data contains a "PDF Context" section with the student's marks/grades, use that information to give a personalized eligibility answer. Check their percentage, degree, and subject against the course eligibility criteria.

Answer:"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        max_tokens=1024,
        temperature=0.7,
    )
    return response.choices[0].message.content

# ─── PDF EXTRACTION ────────────────────────────────────────────────────────
def extract_pdf_text(uploaded_file):
    try:
        file_bytes = uploaded_file.read()
        file_name = uploaded_file.name.lower()

        # -------- If image file (JPG/PNG) → use EasyOCR directly --------
        if file_name.endswith(('.jpg', '.jpeg', '.png')):
            reader = get_ocr_reader()
            result = reader.readtext(file_bytes)
            text = ""
            for detection in result:
                text += detection[1] + "\n"
            return text[:3000] if text.strip() else "Could not extract text from image."

        # -------- If PDF file --------
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        text = ""

        # First try normal text extraction
        for page in doc:
            page_text = page.get_text("text")
            text += page_text + "\n"

        text = "\n".join(dict.fromkeys(text.splitlines()))

        # If very little text → use EasyOCR on PDF pages
        if len(text.replace("\n", "").strip()) < 50:
            text = ""
            reader = get_ocr_reader()
            for page in doc:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
                img_bytes = pix.tobytes("png")
                result = reader.readtext(img_bytes)
                for detection in result:
                    text += detection[1] + "\n"

        return text[:3000] if text.strip() else "Could not extract text from PDF."

    except Exception as e:
        return f"File Error: {str(e)}"

# ─── MAIN QUERY HANDLER ───────────────────────────────────────────────────
def handle_query(query, db, chat_history, pdf_context=""):
    # Detect Bengali and translate to English for processing
    is_bengali_query = detect_bengali(query)
    original_query = query
    if is_bengali_query:
        query = translate_to_english(query)
    # ── Prompt injection guard ──
    injection_phrases = [
        "ignore previous instructions", "ignore all instructions",
        "forget previous", "you are now", "act as",
        "pretend you are", "disregard", "override",
        "system prompt", "new instructions",
    ]
    nq_lower = query.lower()
    if any(phrase in nq_lower for phrase in injection_phrases):
        return "🎓 I'm UniGuide — I can only help with university admission queries for CU, JU and KU. Please ask me about courses, fees, eligibility or admissions!"

    # ── Future prediction guard ──
    future_phrases = ["will be in 20", "predict", "forecast", "future fees", "in 2030", "in 2025", "in 2026"]
    if any(phrase in nq_lower for phrase in future_phrases):
        return "📊 I only have current data and cannot predict future fees or admission details. Please ask me about current courses, fees and eligibility!"
    # ── List all courses guard ──
    list_all_phrases = ["list every", "list all courses", "all courses offered", 
                        "every single course", "every course", "all the courses"]
    if any(phrase in nq_lower for phrase in list_all_phrases):
        return """📚 I have 700+ courses across CU, JU and KU — too many to list all at once!

Instead try asking:
- "What Computer Science courses are in JU?"
- "What Engineering courses does KU offer?"
- "What Management courses are available in CU?"
- "List all PG courses in KU"

This way I can give you a focused and useful answer! 🎓"""

    # ── Unknown/fictional course guard ──
    # This is handled by the RAG system automatically
    # But improve the error message

    # ── Strip irrelevant parts from compound queries ──
    irrelevant_phrases = [
        "history of", "explain the entire", "tell me the story",
        "tell me a joke", "what is the capital", "who invented",
        "tell me about world", "general knowledge"
    ]
    cleaned_query = query
    for phrase in irrelevant_phrases:
        if phrase in nq_lower:
            cleaned_query = re.sub(re.escape(phrase) + r'[^,?.]*', '', cleaned_query, flags=re.IGNORECASE)
    query = cleaned_query.strip()
    # Remove filler phrases that confuse entity detection
    clean_query = query.lower()
    clean_query = clean_query.replace("tell me about", "")
    clean_query = clean_query.replace("tell me", "")
    clean_query = clean_query.replace("what is", "")
    clean_query = clean_query.replace("what are", "")
    clean_query = clean_query.replace("can you tell me", "")
    clean_query = clean_query.replace("i want to know about", "")
    clean_query = clean_query.replace("give me information about", "")
    clean_query = clean_query.replace("give me details about", "")
    clean_query = clean_query.strip()

    universities, detected_course, intents = detect_entities(clean_query)
    nq = normalize(query)
    is_compare = "compare" in nq or "difference" in nq or "vs" in nq
    is_best = "best" in nq or "lowest" in nq or "cheapest" in nq or "better" in nq
    is_recommend = any(w in query.lower() for w in ["which university", "recommend", "should i choose", "which is better", "suggest"])

    # Split multiple questions and search for each separately
    import re as _re
    sub_questions = _re.split(r'\?', query)
    sub_questions = [q.strip() for q in sub_questions if len(q.strip()) > 5]

    all_results = []
    # Always search full query first
    all_results = db.similarity_search(query, k=40)
    
    # Also search each comma-separated part separately
    comma_parts = [p.strip() for p in query.split(',') if len(p.strip()) > 3]
    if len(comma_parts) > 1:
        for part in comma_parts:
            results = db.similarity_search(part, k=20)
            all_results.extend(results)
    
    # Also search sub-questions split by ?
    if len(sub_questions) > 1:
        for sq in sub_questions:
            results = db.similarity_search(sq, k=20)
            all_results.extend(results)

    # Deduplicate results
    seen = set()
    unique_results = []
    for r in all_results:
        if r.page_content not in seen:
            seen.add(r.page_content)
            unique_results.append(r)

    parsed = [parse_course(r.page_content) for r in unique_results]

    # Strict course filter
    if detected_course:
        strict = []
        for c in parsed:
            course_name = normalize(c.get("course name", ""))
            aliases = [normalize(a) for a in course_alias[detected_course]]
            if any(word_match(a, course_name) for a in aliases):
                strict.append(c)
            else:
                pass
        if strict:
            parsed = strict
        else:
            parsed=parsed

    # For multi-university queries, don't filter by university
    comma_parts = [p.strip() for p in query.split(',') if len(p.strip()) > 3]
    is_multi_uni_query = len(comma_parts) > 1

    if is_multi_uni_query:
        # Don't filter — let Groq handle all results
        filtered = parsed
    else:
        filtered = filter_courses(parsed, universities, detected_course)
        if detected_course and len(filtered) == 0:
            return f"🔍 This course doesn't appear to be available in our records for the selected universities. This could mean:\n\n• The course is not offered by CU, JU or KU\n• The course name might be spelled differently\n\nTry asking without specifying a university, or check the official university websites."
        if not filtered:
            filtered = parsed

    # Build context for Groq
    context = ""
    limit = 20 if detected_course else 15
    for c in filtered[:limit]:
        for k, v in c.items():
            context += f"{k}: {v}\n"
        context += "\n"

    if pdf_context:
        context = f"PDF Context:\n{pdf_context}\n\n" + context

    # Always use Groq for natural, conversational answers
    answer = ask_groq(query, context, chat_history)

    # Translate answer back to Bengali if user asked in Bengali
    if is_bengali_query:
        answer = translate_to_bengali(answer)

    return answer

# ─── SIDEBAR ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding: 0.5rem 0 1rem 0;">
        <div style="font-size:1.4rem; font-weight:700; background: linear-gradient(90deg, #a78bfa, #60a5fa); -webkit-background-clip:text; -webkit-text-fill-color:transparent;">🎓 UniGuide</div>
        <div style="color:rgba(255,255,255,0.4); font-size:0.75rem;">Logged in as <b style="color:#a78bfa">{st.session_state.username}</b></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # University filter
    st.markdown('<p style="color:rgba(255,255,255,0.5); font-size:0.8rem; text-transform:uppercase; letter-spacing:0.05em;">Filter University</p>', unsafe_allow_html=True)
    uni_filter = st.multiselect(
        "",
        ["Calcutta University (CU)", "Jadavpur University (JU)", "Kalyani University (KU)"],
        label_visibility="collapsed"
    )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # PDF Upload
    st.markdown('<p style="color:rgba(255,255,255,0.5); font-size:0.8rem; text-transform:uppercase; letter-spacing:0.05em;">📄 Upload PDF</p>', unsafe_allow_html=True)
    uploaded_pdf = st.file_uploader("Upload marksheet / document", type=["pdf", "jpg", "jpeg", "png"], label_visibility="collapsed")
    if "pdf_context" not in st.session_state:
        st.session_state.pdf_context = ""
    if uploaded_pdf:
        st.session_state.pdf_context = extract_pdf_text(uploaded_pdf)
        st.markdown('<span class="tag-green">✓ PDF loaded</span>', unsafe_allow_html=True)
        st.markdown(f'<p style="color:rgba(255,255,255,0.4); font-size:0.75rem; margin-top:0.3rem">{len(st.session_state.pdf_context)} chars extracted</p>', unsafe_allow_html=True)
    else:
        st.session_state.pdf_context = ""

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Quick topics
    st.markdown('<p style="color:rgba(255,255,255,0.5); font-size:0.8rem; text-transform:uppercase; letter-spacing:0.05em;">Quick Topics</p>', unsafe_allow_html=True)
    topics = ["💻 Computer Science", "⚙️ Engineering", "📚 Arts & Humanities", "🔬 Science", "💼 Management", "🏛️ Education", "💊 Pharmacy", "⚖️ Law"]
    for topic in topics:
        if st.button(topic, use_container_width=True, key=f"topic_{topic}"):
            st.session_state.pending_query = topic.split(" ", 1)[1] + " courses"

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

    # Stats
    st.markdown("""
    <div style="margin-top:1rem">
        <p style="color:rgba(255,255,255,0.3); font-size:0.72rem; text-align:center;">
            3 Universities · 700+ Courses<br>CU · JU · KU
        </p>
    </div>
    """, unsafe_allow_html=True)

# ─── MAIN AREA ───────────────────────────────────────────────────────────
col_main, col_info = st.columns([3, 1.1])

with col_main:
    st.markdown("""
    <div>
        <div class="hero-title">UniGuide 🎓</div>
        <div class="hero-sub">Your AI-powered West Bengal University Admission Assistant</div>
    </div>
    """, unsafe_allow_html=True)

    # Load RAG
    with st.spinner("Loading knowledge base..."):
        try:
            db = load_rag_system()
        except Exception as e:
            st.error(f"Error loading data: {e}. Make sure data/cu.txt, ju.txt, ku.txt exist.")
            st.stop()

    # Init session
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Welcome box (only when no messages)
    if not st.session_state.messages:
        st.markdown("""
        <div class="welcome-box">
            <h3>👋 Welcome! I can help you with:</h3>
            <p>
            🔍 Course details, fees, eligibility & seats<br>
            ⚖️ Compare courses across CU, JU & KU<br>
            📄 Analyze your marksheet PDF for eligibility<br>
            🎯 Recommend the best university based on your interests<br>
            💬 Multi-turn conversations — I remember context!
            </p>
        </div>
        """, unsafe_allow_html=True)

        # Sample questions
        st.markdown('<div class="chip-row">', unsafe_allow_html=True)
        sample_qs = [
            "MBA fees in KU",
            "Compare M.Ed in JU and KU",
            "Best CSE courses in JU",
            "MCA eligibility in Kalyani",
            "PhD admission in CU",
            "Which university for Engineering?",
        ]
        for i, q in enumerate(sample_qs):
            if st.button(q, key=f"sample_{i}"):
                st.session_state.pending_query = q
        st.markdown('</div>', unsafe_allow_html=True)

    # Chat history display
    chat_html = '<div class="chat-container" id="chat-box">'
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            chat_html += f'<div class="msg-user"><div class="bubble">{msg["content"]}</div></div>'
        else:
            chat_html += f'<div class="msg-bot"><div class="bot-avatar">🤖</div><div class="bubble">{msg["content"]}</div></div>'
    chat_html += '</div>'
    st.markdown(chat_html, unsafe_allow_html=True)

    # Voice output for last bot message
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        last_msg = st.session_state.messages[-1]["content"]
        msg_index = len(st.session_state.messages)

        col_v1, col_v2 = st.columns([1, 5])
        with col_v1:
            if st.button("🔊 Listen", key=f"voice_btn_{msg_index}"):
                st.session_state.voice_counter = st.session_state.get('voice_counter', 0) + 1
                st.session_state.audio_for_msg = msg_index
                lang_code = 'bn' if detect_bengali(last_msg) else 'en'
                with st.spinner("Generating audio..."):
                    audio_b64 = text_to_speech(last_msg, lang=lang_code)
                st.session_state.current_audio = audio_b64

        # Only play audio if it belongs to the CURRENT last message
        if (st.session_state.get("current_audio")
                and st.session_state.get("audio_for_msg") == msg_index):
            counter = st.session_state.get('voice_counter', 0)
            st.markdown(f"""
            <audio autoplay id="audio_{counter}">
                <source src="data:audio/mp3;base64,{st.session_state.current_audio}" type="audio/mp3">
            </audio>
            """, unsafe_allow_html=True)

    # Auto-scroll
    st.markdown("""
    <script>
    const chatBox = document.getElementById('chat-box');
    if (chatBox) chatBox.scrollTop = chatBox.scrollHeight;
    </script>
    """, unsafe_allow_html=True)

    # Interest-based suggestions after responses
    if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
        last_user = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"), "")
        topic, suggestions = detect_interest(last_user)
        if suggestions:
            st.markdown(f'<p style="color:rgba(255,255,255,0.35); font-size:0.78rem; margin:0.5rem 0 0.3rem 0;">💡 Related questions about <b style="color:#a78bfa">{topic}</b>:</p>', unsafe_allow_html=True)
            cols = st.columns(len(suggestions[:3]))
            for i, sug in enumerate(suggestions[:3]):
                with cols[i]:
                    if st.button(sug, key=f"sug_{i}_{len(st.session_state.messages)}"):
                        st.session_state.pending_query = sug

    # Handle pending query (from chips/buttons)
    if "pending_query" in st.session_state:
        st.session_state.current_audio = None  # Clear old audio
        pending = st.session_state.pop("pending_query")
        st.session_state.messages.append({"role": "user", "content": pending})
        with st.spinner("Thinking..."):
            # Apply university filter from sidebar
            query_with_filter = pending
            if uni_filter:
                uni_map = {"Calcutta University (CU)": "calcutta", "Jadavpur University (JU)": "jadavpur", "Kalyani University (KU)": "kalyani"}
                uni_names = [uni_map[u] for u in uni_filter if u in uni_map]
                filter_str = " ".join(uni_names)
                query_with_filter = pending + " in " + filter_str

            response = handle_query(query_with_filter, db, st.session_state.messages[:-1], st.session_state.pdf_context)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()
    # Voice Input - positioned beside chat input
    col_chat, col_mic = st.columns([11, 1])
    with col_chat:
        st.markdown('<div style="height:0px"></div>', unsafe_allow_html=True)
    with col_mic:
        voice_text = speech_to_text(
            language='en',
            start_prompt="🎙️",
            stop_prompt="⏹",
            just_once=True,
            use_container_width=True,
            key='voice_input'
        )

    if voice_text:
        st.session_state.current_audio = None
        st.session_state.messages.append({"role": "user", "content": voice_text})
        with st.spinner("Thinking..."):
            query_with_filter = voice_text
            if uni_filter:
                uni_map = {"Calcutta University (CU)": "calcutta", "Jadavpur University (JU)": "jadavpur", "Kalyani University (KU)": "kalyani"}
                uni_names = [uni_map[u] for u in uni_filter if u in uni_map]
                filter_str = " ".join(uni_names)
                query_with_filter = voice_text + " in " + filter_str
            response = handle_query(query_with_filter, db, st.session_state.messages[:-1], st.session_state.pdf_context)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

    # Chat input
    if prompt := st.chat_input("Ask about courses, fees, eligibility, admissions..."):
        st.session_state.current_audio = None  # Clear old audio
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.spinner("Thinking..."):
            query_with_filter = prompt
            if uni_filter:
                uni_map = {"Calcutta University (CU)": "calcutta", "Jadavpur University (JU)": "jadavpur", "Kalyani University (KU)": "kalyani"}
                uni_names = [uni_map[u] for u in uni_filter if u in uni_map]
                filter_str = " ".join(uni_names)
                query_with_filter = prompt + " in " + filter_str
            response = handle_query(query_with_filter, db, st.session_state.messages[:-1], st.session_state.pdf_context)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

# ─── RIGHT INFO PANEL ────────────────────────────────────────────────────
with col_info:
    st.markdown('<br>', unsafe_allow_html=True)
    st.markdown("""
    <div class="info-card">
        <h4>🏛️ Universities</h4>
        <p><span class="tag-blue">CU</span> University of Calcutta</p>
        <p style="margin-top:0.4rem"><span class="tag-purple">JU</span> Jadavpur University</p>
        <p style="margin-top:0.4rem"><span class="tag-green">KU</span> Kalyani University</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-card" style="margin-top:0.6rem">
        <h4>💬 Try Asking</h4>
        <p style="font-size:0.8rem; color:rgba(255,255,255,0.45); line-height:1.8">
        • "Compare MBA in KU and JU"<br>
        • "Best engineering courses?"<br>
        • "PhD admission process CU"<br>
        • "I like computers, suggest courses"<br>
        • "Fees for MSc Physics CU"
        </p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="info-card" style="margin-top:0.6rem">
        <h4>📄 PDF Feature</h4>
        <p style="font-size:0.8rem; color:rgba(255,255,255,0.45); line-height:1.6">
        Upload your marksheet and ask "Am I eligible for MBA in KU?" — I'll check your scores!
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Chat stats
    if st.session_state.messages:
        user_msgs = sum(1 for m in st.session_state.messages if m["role"] == "user")
        st.markdown(f"""
        <div class="info-card" style="margin-top:0.6rem">
            <h4>📊 Session</h4>
            <p style="font-size:0.8rem; color:rgba(255,255,255,0.45)">
            {user_msgs} questions asked<br>
            {len(st.session_state.messages)} messages total
            </p>
        </div>
        """, unsafe_allow_html=True)
