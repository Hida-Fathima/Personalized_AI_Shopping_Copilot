import os
import io
import requests
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import cohere
from PIL import Image
from bs4 import BeautifulSoup

# -----------------------------
# 🧩 Setup
# -----------------------------
load_dotenv()

COHERE_API_KEY = os.getenv("COHERE_API_KEY")
if not COHERE_API_KEY:
    raise ValueError("❌ COHERE_API_KEY not found in .env file")

co = cohere.Client(COHERE_API_KEY)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------
# 🧠 AI Personality
# -----------------------------
SYSTEM_PROMPT = """
You are **Shopping Copilot**, a friendly, witty, and stylish AI shopping assistant.
You talk casually like a human — smart, empathetic, and fun.
You help users find products from Amazon, Flipkart, Myntra, etc.
When users upload an image, describe it and suggest visually similar items.
Always include small friendly phrases like “Here’s what I found for you 👇” or “This might match your vibe 😎”.
If a product is requested under a price, show affordable options.
"""

# -----------------------------
# 🔍 Real Product Search
# -----------------------------
def scrape_products_amazon(query, limit=5):
    """Simple Amazon product scraper (public HTML version)"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    }
    url = f"https://www.amazon.in/s?k={query.replace(' ', '+')}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    products = []
    for item in soup.select(".s-result-item")[:limit]:
        name = item.select_one("h2")
        image = item.select_one("img")
        price = item.select_one(".a-price-whole")
        link = item.select_one("a.a-link-normal")

        if name and image and price and link:
            products.append({
                "name": name.text.strip(),
                "image": image["src"],
                "price": f"₹{price.text.strip()}",
                "link": "https://www.amazon.in" + link["href"]
            })

    return products


def scrape_products_flipkart(query, limit=5):
    """Simple Flipkart product scraper"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    }
    url = f"https://www.flipkart.com/search?q={query.replace(' ', '+')}"
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")

    products = []
    for item in soup.select("._1AtVbE")[:limit]:
        name = item.select_one("a.IRpwTa, .s1Q9rs, ._4rR01T")
        image = item.select_one("img")
        price = item.select_one("._30jeq3")
        link = item.select_one("a")

        if name and image and price and link:
            products.append({
                "name": name.text.strip(),
                "image": image["src"],
                "price": price.text.strip(),
                "link": "https://www.flipkart.com" + link["href"]
            })

    return products


# -----------------------------
# 💬 Chat Endpoint
# -----------------------------
@app.post("/chat")
async def chat_with_copilot(message: str = Form(...), image: UploadFile = File(None)):
    image_description = ""

    if image:
        img_bytes = await image.read()
        img = Image.open(io.BytesIO(img_bytes))
        image_description = f"The user uploaded an image with size {img.size} and mode {img.mode}. Suggest visually similar fashion products."

    prompt = f"{SYSTEM_PROMPT}\n\nUser: {message}\n{image_description}\nAssistant:"

    try:
    # ✅ Latest Cohere model (as of Nov 2025)
      response = co.chat(
         model="command-r-plus-08-2024",
         message=prompt
      )
      ai_reply = response.text
    except Exception as e:
      ai_reply = f"⚠️ AI service error: {e}"

    # 🔍 Combine live product data
    amazon_products = scrape_products_amazon(message)
    flipkart_products = scrape_products_flipkart(message)
    products = amazon_products + flipkart_products

    return {"reply": ai_reply, "products": products}


@app.get("/")
def home():
    return {"message": "🛍️ Shopping Copilot is running with real product search!"}
