import os
import time
import sqlite3
import json
import urllib.parse
from pathlib import Path

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from passlib.context import CryptContext

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import cohere

from crossencoder import compute_relevance
from memory_manager import memory
from vector_memory import vector_memory

from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image


# ================================================================
# ENV + CONFIG
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
# SYSTEM PROMPT
# ================================================================
SYSTEM_PROMPT = """
You are Shopping Copilot — a stylish, friendly, modern AI shopping assistant.

STYLE RULES:
- You must NOT use markdown.
- Do NOT use bold (** **), stars, underscores, hyphens, numbered lists, bullet lists, or markdown headers.
- Keep the text clean, readable, and formatted naturally for UI display.
- Separate product suggestions using short line breaks or sentences, not bullet points.
- Use emojis naturally (1–3 per response), not more.
- Keep explanations short, warm, and helpful.

HOW YOU TALK:
- Friendly, human-like, and conversational.
- Stylish but not cringe.
- Confident and concise.
- Add subtle phrases like:
  “Here’s what I found for you 👇”
  “This might match your vibe 😎”
  “Let me pick a few great options for you ✨”
- Always focus on clarity.

WHEN PRODUCTS ARE PROVIDED:
- Summarize findings naturally in plain text.
- For each product, write a single short descriptive sentence:
    Product Name – short highlight of the style, use case, or look.
- Do NOT format them as lists.
- Do NOT add any URLs; the UI handles that.

IMAGE INPUT:
- If the user uploads an image, describe it in one elegant line.
- Then recommend visually similar items.

NO INVENTING PRODUCTS:
- Only refer to products included in the provided list.
- If the list is small or empty, say so politely and suggest trying a different angle.

YOUR GOAL:
- Make users feel like they have a personal fashion assistant.
- Be helpful, stylish, and easy to read.
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
# Pydantic Models
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
# BLIP LAZY LOADING
# ================================================================
blip_processor = None
blip_model = None


def ensure_blip_loaded():
    global blip_processor, blip_model
    if blip_processor is None or blip_model is None:
        print("Loading BLIP image captioning model...")
        blip_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
        blip_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
        print("BLIP model loaded.")


def caption_image(image_path: str) -> str:
    try:
        ensure_blip_loaded()
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
# SCRAPER
# ================================================================
SCRAPER_BASE = "http://api.scraperapi.com"


def fetch(url):
    params = {
        "api_key": SCRAPER_API_KEY,
        "url": url,
        "keep_headers": "true"
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    try:
        r = requests.get(SCRAPER_BASE, params=params, headers=headers, timeout=40)
        r.raise_for_status()
        return r.text
    except Exception:
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
                "title": title,
                "price": "",
                "image": image,
                "url": url,
                "source": "Amazon"
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
                "title": title,
                "price": "",
                "image": image,
                "url": url,
                "source": "Flipkart"
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
                "title": title,
                "price": "",
                "image": image,
                "url": url,
                "source": "Myntra"
            })

        if len(items) >= 6:
            break

    return items


def search_all(query):
    q = urllib.parse.quote_plus(query)
    results = []

    a = fetch(f"https://www.amazon.in/s?k={q}")
    if a:
        results += parse_products(a, "Amazon")

    f = fetch(f"https://www.flipkart.com/search?q={q}")
    if f:
        results += parse_products(f, "Flipkart")

    m = fetch(f"https://www.myntra.com/{q}")
    if m:
        results += parse_products(m, "Myntra")

    return results[:10]


# ================================================================
# RE-RANKER
# ================================================================
def rerank_products(query, products):
    ranked = []
    for p in products:
        title = p["title"]
        score = compute_relevance(query, title)
        ranked.append((score, p))

    ranked.sort(reverse=True, key=lambda x: x[0])
    return [item[1] for item in ranked[:5]]


# ================================================================
# SMART QUERY REWRITER
# ================================================================
def generate_smart_query(history_messages, current_msg: str) -> str:
    """
    Uses Cohere to refine the search query based on short-term memory.
    history_messages: list of recent user messages (strings)
    current_msg: combined topic/message text
    """
    if not history_messages:
        return current_msg

    history_str = "\n".join(history_messages[-3:])

    prompt = f"""
Recent Conversation:
{history_str}

User Input: "{current_msg}"

TASK:
Rewrite the user's input into a clean keyword search query
for Amazon / Flipkart / Myntra.

RULES:
- Merge with relevant context from conversation.
- Example: history has "red dress", user says "under 500" → "red dress under 500".
- If the user starts a completely new topic, ignore old context.
- Output ONLY the final keyword phrase. No quotes. No full sentences.
"""

    try:
        resp = co.chat(
            model=COHERE_MODEL,
            message=prompt,
            temperature=0.1
        )
        clean_query = resp.text.strip()
        print(f"SMART QUERY: '{current_msg}' -> '{clean_query}'")
        return clean_query or current_msg
    except Exception as e:
        print("Smart Query Error:", e)
        return current_msg


# ================================================================
# FASTAPI APP
# ================================================================
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
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

    token = f"tok-{user['id']}-{int(time.time())}"
    return {"token": token, "username": user["username"]}


# ================================================================
# CHAT ENDPOINT
# ================================================================
@app.post("/chat")
async def chat(
    message: str = Form(""),
    history: str = Form("[]"),
    file: UploadFile = File(None)
):
    # 1. Parse frontend chat history (not primary memory, but kept)
    try:
        chat_history_list = json.loads(history)
    except Exception:
        chat_history_list = []

    # 2. Add current text into Memory V2 + Vector Memory V3
    if message.strip():
        memory.add_message(message)
        memory.update_topic(message)
        vector_memory.add_memory(message)

    # 3. Handle image upload + BLIP caption
    saved_image = None
    image_caption = ""

    if file and file.filename:
        safe_name = file.filename.replace(" ", "_").replace("/", "_")
        fname = f"{int(time.time())}_{safe_name}"
        out = UPLOAD_DIR / fname

        content = await file.read()
        out.write_bytes(content)

        saved_image = f"/static/uploads/{fname}"
        local_path = "." + saved_image

        # BLIP caption
        image_caption = caption_image(local_path)

        if image_caption:
            # Feed image description into memories
            memory.update_topic(image_caption)
            memory.add_message(image_caption)
            vector_memory.add_memory(image_caption)

    # 4. Vector Memory Recall (Memory V3)
    recalled = []
    if message.strip():
        recalled = vector_memory.search_memory(message, top_k=2)
    recalled_text = " ".join([t for score, t in recalled]) if recalled else ""

    # 5. Build base query using topic memory (Memory V2)
    base_query = memory.build_query_context(message or image_caption or "")

    # 6. Combine base query + semantic recall
    combined_query = f"{base_query} {recalled_text}".strip() or (message or image_caption or "")

    # 7. Smart Query Rewriter with recent memory
    smart_query = generate_smart_query(memory.last_messages, combined_query)

    # 8. Decide whether to trigger scraper
    shopping_words = [
        "show", "find", "buy", "dress", "shirt",
        "price", "frock", "jeans", "mobile", "saree",
        "shoes", "sandals", "kurti", "tshirt"
    ]

    products = []

    should_search = (
        any(w in (message.lower() if message else "") for w in shopping_words)
        or bool(image_caption)
    )

    if should_search and smart_query.strip():
        products = search_all(smart_query)
        if products:
            products = rerank_products(smart_query, products)

    # 9. Build input for Cohere LLM
    user_input = message or ""
    if image_caption:
        user_input += f"\nUser uploaded an image showing: {image_caption}"

    if products:
        prod_summary = "\n".join([
            f"{p['source']}: {p['title']} - {p['url']}"
            for p in products
        ])
        user_input += f"\n\nProducts found:\n{prod_summary}"

    # 10. Build LLM chat_history from short-term + recalled memory
    llm_history_msgs = memory.last_messages.copy()
    llm_history_msgs += [t for (_, t) in recalled]

    llm_chat_history = [
        {"role": "USER", "message": m}
        for m in llm_history_msgs
    ]

    # 11. Cohere chat
    try:
        resp = co.chat(
            model=COHERE_MODEL,
            message=user_input or "Help the user with shopping.",
            preamble=SYSTEM_PROMPT,
            chat_history=llm_chat_history
        )
        reply = resp.text
    except Exception as e:
        print("COHERE ERROR:", e)
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
