# backend/firestore_setup.py
import os
from sentence_transformers import SentenceTransformer
import firebase_admin
from firebase_admin import credentials, firestore

# set path to your key
KEY = "serviceAccountKey.json"
cred = credentials.Certificate(KEY)
firebase_admin.initialize_app(cred)
db = firestore.client()

sbert = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# Example product list (or load CSV)
products = [
    {"id": "p1", "title": "Blue casual shirt", "description": "Men's full-sleeve denim blue shirt", "price": 1299, "image_url": "" },
    {"id": "p2", "title": "Black leather wallet", "description": "Compact genuine leather wallet for men", "price": 599, "image_url": "" },
    {"id": "p3", "title": "Analog wrist watch", "description": "Classic analog watch with leather strap", "price": 2499, "image_url": "" },
]

for p in products:
    text = (p["title"] + " " + p["description"]).strip()
    emb = sbert.encode(text, convert_to_numpy=True).tolist()
    doc_ref = db.collection("products").document(p["id"])
    doc_ref.set({
        "title": p["title"],
        "description": p["description"],
        "price": p["price"],
        "image_url": p["image_url"],
        "embedding": emb,
    })
    print("Uploaded", p["id"])
