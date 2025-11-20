import os
import time
import sqlite3
import json
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from passlib.context import CryptContext

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import urllib.parse
import cohere

from crossencoder import compute_relevance

# ---------------- BLIP IMPORTS ----------------
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image


# ================================================================
# LOAD ENVIRONMENT
# ================================================================
load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY", "")
SCRAPER_API_KEY = os.getenv("SCRAPER_API_KEY", "")
COHERE_MODEL = os.getenv("COHERE_MODEL", "command-r-plus-08-2024")

if not COHERE_API_KEY:
    print("⚠ WARNING: No Cohere API key in .env")
if not SCRAPER_API_KEY:
    print("⚠ WARNING: No ScraperAPI key in .env")

co = cohere.Client(COHERE_API_KEY)

pwdctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

UPLOAD_DIR = Path("./static/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = Path("data.db")


# ================================================================
# LOAD BLIP IMAGE CAPTIONING MODEL
# ================================================================
print("Loading BLIP image captioning model...")
blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
print("BLIP model loaded.")


# ================================================================
# SYSTEM PROMPT
# ================================================================
SYSTEM_PROMPT = """
You are Shopping Copilot — a stylish, friendly, modern AI shopping assistant.

STYLE RULES:
- You must NOT use markdown.
- Do NOT use bold (** **), stars, underscores, hyphens, lists.
- Keep the text clean for UI.
- Use 1–3 emojis maximum.

BEHAVIOR:
- Friendly, stylish, helpful.
- No URLs in the text (UI handles that).
- Summaries must be natural sentences.
- Image uploads: describe briefly and recommend based on it.
"""


# ================================================================
# DB INIT
# ================================================================
def get_conn():
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        email TEXT,
        password_hash TEXT,
        created_at REAL
    )
    """)
    conn.commit()
    conn.close()


init_db()


# ================================================================
# MODELS
# ================================================================
class Auth(BaseModel):
    username: str
    password: str
    email: str | None = None


# ================================================================
# UTILS
# ================================================================
def hash_pw(pw):
    return pwdctx.hash(pw)


def verify_pw(pw, hashed):
    return pwdctx.verify(pw, hashed)



# ================================================================
# SCRAPER
# ================================================================
SCRAPER_BASE = "http://api.scraperapi.com"


def fetch(url):
    params = {"api_key": SCRAPER_API_KEY, "url": url, "keep_headers": "true"}
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        r = requests.get(SCRAPER_BASE, params=params, headers=headers, timeout=40)
        r.raise_for_status()
        return r.text
    except:
        time.sleep(3)
        try:
            r = requests.get(SCRAPER_BASE, params=params, headers=headers, timeout=40)
            r.raise_for_status()
            return r.text
        except Exception as e:
            print("ScraperAPI FAILED:", e)
            return None


def parse_products(html, source):
    soup = BeautifulSoup(html, "html.parser")
    items = []

    for a in soup.find_all("a", href=True):
        href = a["href"]

        # Amazon
        if source == "Amazon":
            if "/dp/" not in href:
                continue
            url = "https://www.amazon.in" + href if href.startswith("/") else href
            title = a.get_text(strip=True) or "Product"
            img = a.find("img")
            image = img["src"] if img else None
            items.append({
                "title": title, "price": "", "image": image,
                "url": url, "source": "Amazon"
            })

        # Flipkart
        if source == "Flipkart":
            if "/p/" not in href:
                continue
            url = "https://www.flipkart.com" + href if href.startswith("/") else href
            title = a.get_text(strip=True) or "Product"
            img = a.find("img")
            image = img["src"] if img else None
            items.append({
                "title": title, "price": "", "image": image,
                "url": url, "source": "Flipkart"
            })

        # Myntra
        if source == "Myntra":
            if "myntra.com" not in href:
                continue
            url = href if href.startswith("http") else "https://www.myntra.com" + href
            title = a.get_text(strip=True) or "Product"
            img = a.find("img")
            image = img["src"] if img else None
            items.append({
                "title": title, "price": "", "image": image,
                "url": url, "source": "Myntra"
            })

        if len(items) >= 6:
            break

    return items


def search_all(query):
    q = urllib.parse.quote_plus(query)
    results = []

    a = fetch(f"https://www.amazon.in/s?k={q}")
    if a: results += parse_products(a, "Amazon")

    f = fetch(f"https://www.flipkart.com/search?q={q}")
    if f: results += parse_products(f, "Flipkart")

    m = fetch(f"https://www.myntra.com/{q}")
    if m: results += parse_products(m, "Myntra")

    return results[:10]


# ================================================================
# RERANKER
# ================================================================
def rerank_products(query, products):
    ranked = []
    for p in products:
        score = compute_relevance(query, p["title"])
        ranked.append((score, p))
    ranked.sort(reverse=True, key=lambda x: x[0])
    return [item[1] for item in ranked[:5]]


# ================================================================
# BLIP IMAGE CAPTION FUNCTION
# ================================================================
def caption_image(image_path: str) -> str:
    try:
        image = Image.open(image_path).convert("RGB")
        inputs = blip_processor(image, return_tensors="pt")
        output = blip_model.generate(**inputs, max_length=50)
        caption = blip_processor.decode(output[0], skip_special_tokens=True)
        print("BLIP Caption:", caption)
        return caption
    except Exception as e:
        print("BLIP ERROR:", e)
        return ""


# ================================================================
# AI QUERY REWRITER (SMART MEMORY)
# ================================================================
def generate_smart_query(history, current_msg):
    if not history:
        return current_msg

    prompt = f"""
    Chat History:
    {json.dumps(history[-3:])}

    User Input: "{current_msg}"

    TASK:
    Rewrite the user's message into a clean keyword search query.
    Rules:
    - Merge with history only when related.
    - If last query was "red dress" and user says "under 500", output "red dress under 500".
    - If user switches topic, ignore history.
    - Output ONLY the clean keyword string. No punctuation.
    """

    try:
        resp = co.chat(
            model=COHERE_MODEL,
            message=prompt,
            temperature=0.1
        )
        return resp.text.strip()
    except:
        return current_msg


# ================================================================
# FASTAPI INIT
# ================================================================
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

app.mount("/static", StaticFiles(directory="static"), name="static")


# ================================================================
# AUTH ENDPOINTS
# ================================================================
@app.post("/register")
def register(data: Auth):
    username = data.username.strip()
    pw = data.password

    conn = get_conn()
    c = conn.cursor()

    try:
        c.execute("""
        INSERT INTO users(username, email, password_hash, created_at)
        VALUES (?, ?, ?, ?)
        """, (username, data.email or "", hash_pw(pw), time.time()))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(400, "username already exists")
    finally:
        conn.close()

    return {"status": "ok"}


@app.post("/login")
def login(data: Auth):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=? OR email=?", (data.username, data.username))
    user = c.fetchone()
    conn.close()

    if not user:
        raise HTTPException(401, "invalid")

    if not verify_pw(data.password, user["password_hash"]):
        raise HTTPException(401, "invalid")

    return {"token": f"tok-{user['id']}-{int(time.time())}", "username": user["username"]}


# ================================================================
# CHAT ENDPOINT
# ================================================================
@app.post("/chat")
async def chat(
    message: str = Form(""),
    history: str = Form("[]"),
    file: UploadFile = File(None)
):

    # ---------------- Parse history ----------------
    try:
        chat_history_list = json.loads(history)
    except:
        chat_history_list = []

    # ---------------- Handle image upload ----------------
    saved_image = None
    image_caption = ""

    if file and file.filename:
        safe_name = file.filename.replace(" ", "_").replace("/", "_")
        fname = f"{int(time.time())}_{safe_name}"
        out = UPLOAD_DIR / fname

        content = await file.read()
        out.write_bytes(content)

        saved_image = f"/static/uploads/{fname}"

        # Convert URL → local path for BLIP
        local_path = "." + saved_image
        image_caption = caption_image(local_path)


    # ---------------- Smart Query Generation ----------------
    if image_caption:
        smart_query = generate_smart_query(chat_history_list, image_caption + " " + message)
    else:
        smart_query = generate_smart_query(chat_history_list, message)


    # ---------------- Scraping Logic ----------------
    shopping_words = [
        "show", "find", "buy", "dress", "shirt",
        "price", "frock", "jeans", "mobile", "saree"
    ]

    products = []

    if any(w in message.lower() for w in shopping_words) or image_caption:
        products = search_all(smart_query)

        if products:
            products = rerank_products(smart_query, products)


    # ---------------- Build LLM Input ----------------
    user_input = message

    if image_caption:
        user_input += f"\nUser uploaded an image showing: {image_caption}"

    if products:
        prod_summary = "\n".join([
            f"{p['source']}: {p['title']} - {p['url']}"
            for p in products
        ])
        user_input += f"\n\nProducts found:\n{prod_summary}"


    # ---------------- Cohere LLM Response ----------------
    try:
        resp = co.chat(
            model=COHERE_MODEL,
            message=user_input,
            preamble=SYSTEM_PROMPT,
            chat_history=chat_history_list
        )
        reply = resp.text
    except:
        reply = "Sorry, I couldn't process with AI right now."


    return {
        "reply": reply,
        "products": products,
        "saved_image": saved_image
    }


# ================================================================
# ROOT
# ================================================================
@app.get("/")
def root():
    return {"status": "ok"}
