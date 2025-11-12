# backend/product_embs.py
import os
import json
import numpy as np
import pandas as pd
from tqdm import tqdm
from PIL import Image
import requests
from io import BytesIO

from sentence_transformers import SentenceTransformer
from transformers import CLIPProcessor, CLIPModel
import torch

DATA_CSV = "flipkart_com-ecommerce_sample.csv"  # your CSV
OUT_JSON = "products_meta.json"
OUT_EMB = "product_embs.npz"

# Models (small for CPU)
txt_model = SentenceTransformer("all-MiniLM-L6-v2")
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
device = "cpu"
clip_model.to(device)

def download_image(url):
    try:
        r = requests.get(url, timeout=5)
        r.raise_for_status()
        return Image.open(BytesIO(r.content)).convert("RGB")
    except:
        return None

def main():
    df = pd.read_csv(DATA_CSV, nrows=5000)  # limit for speed; increase if you can
    products = []
    txt_embs = []
    img_embs = []

    for _, row in tqdm(df.iterrows(), total=min(len(df),5000)):
        title = str(row.get("product_name", "") or row.get("title", ""))
        desc = str(row.get("description", "") or "")
        price = row.get("price", None) or row.get("selling_price", None) or None
        category = str(row.get("category", "") or row.get("sub_category", "") or "").strip()
        image_url = row.get("image", "") if "image" in row else row.get("image_url", "")

        # build text for embedding
        text = (title + " — " + desc).strip()

        # text embedding
        t_emb = txt_model.encode(text, show_progress_bar=False)
        txt_embs.append(t_emb)

        # image embedding (optional)
        if image_url and isinstance(image_url, str) and image_url.startswith("http"):
            pil = download_image(image_url)
            if pil:
                inputs = clip_processor(images=pil, return_tensors="pt").to(device)
                with torch.no_grad():
                    img_feats = clip_model.get_image_features(**inputs).cpu().numpy()[0]
                img_embs.append(img_feats)
            else:
                img_embs.append(np.zeros(512))
        else:
            img_embs.append(np.zeros(512))

        products.append({
            "title": title,
            "description": desc,
            "price": float(price) if pd.notna(price) else None,
            "category": category,
            "image": image_url if image_url and isinstance(image_url, str) else None
        })

    np.savez_compressed(OUT_EMB, txt_embs=np.vstack(txt_embs), img_embs=np.vstack(img_embs))
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(products, f, ensure_ascii=False, indent=2)
    print("Saved", OUT_JSON, OUT_EMB)

if __name__ == "__main__":
    main()
