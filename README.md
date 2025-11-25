# Personalized AI Shopping Copilot

**A Multimodal, RAG-based AI Assistant for Zero-Hallucination E-Commerce Discovery.**

---
### Project Overview:

The **AI Shopping Copilot** is designed to solve the "Paradox of Choice" in online retail. Unlike standard chatbots that rely on static databases or "hallucinate" fake products, this system implements a **Real-Time Retrieval-Augmented Generation (RAG)** pipeline.

It acts as an intelligent personal stylist that understands user intent through both **Natural Language** (Text) and **Computer Vision** (Images). By scraping live data from major platforms (Amazon/Flipkart) and rigorously filtering it through a semantic re-ranker, the Copilot ensures that every recommendation is 100% factually accurate, in-stock, and hyper-relevant to the user's specific "vibe."

---
### Core Features:

* **Conversational Search:** Go beyond keywords. Ask complex queries like, *"I need a floral dress for a summer beach wedding under ₹2000."*
* **Visual Search (Multimodal):** Can't describe it? Upload a photo. Our integrated **BLIP Model** analyzes the image to find visually similar items available for purchase.
* **Real-Time Grounding:** No stale data. The system fetches live pricing and stock status via **ScraperAPI**, ensuring you never see an "Out of Stock" recommendation.
* **Semantic Re-Ranking:** A custom-trained **Cross-Encoder** filters out irrelevant "keyword matches" (e.g., removing "Phone Cases" when you search for "iPhone"), ensuring high precision.
* **Zero-Hallucination:** The AI is strictly grounded; it can only recommend products that have been verified by the scraper.
* **Trust Interface:** A clean **React Material UI** that separates the AI's advice (chat bubbles) from the factual product data (interactive cards).

---

### The AI Engine Explained:
Our architecture moves beyond simple "Generative AI" to a robust **Neuro-Symbolic** approach:

1.  **The Eyes (Vision):** Powered by **BLIP (Bootstrapping Language-Image Pre-training)**. It converts user-uploaded images into rich textual descriptions (e.g., *"Red silk saree with gold border"*).
2.  **The Brain (Logic):** Powered by **Cohere Command R+**. It acts as the reasoning engine, rewriting vague user intents into precise, search-optimized queries.
3.  **The Hands (Retrieval):** Powered by **ScraperAPI & BeautifulSoup**. It executes parallel, real-time searches across multiple e-commerce platforms to fetch raw inventory data.
4.  **The Filter (Precision):** Powered by a fine-tuned **DistilBERT Cross-Encoder**. It scores every scraped product against the user's query, rejecting "hard negatives" to ensure top-tier relevance.

---

### Technology & Architecture (Planned):


This project is built on a high-performance, microservices-style architecture:

| Component | Technology Used |
| :--- | :--- |
| **Frontend** | React.js, Material UI, Axios |
| **Backend** | Python FastAPI, Uvicorn |
| **AI Models** | PyTorch, Transformers (HuggingFace), Sentence-Transformers |
| **LLM Service** | Cohere API (Command R+) |
| **Data Pipeline** | ScraperAPI, BeautifulSoup4 |
| **Database** | SQLite (User Sessions), Vector Store (Context Memory) |
| **Version Control** | Git & GitHub |

---


### Frontend Setup

cd ../frontend

 Install Node modules

 
npm install

 Start the React App

 
npm start


### Project Workflow:
This project will be developed in distinct phases to ensure a structured and agile workflow.

1. Ingestion: User uploads an image or text.


2. Expansion: AI rewrites the query for better searchability.


3. Retrieval: Scraper fetches raw HTML from Amazon/Flipkart.


4. Parsing: Unstructured HTML is converted to Structured JSON.


5. Re-Ranking: DistilBERT scores products; low scores are discarded.


6. Generation: Cohere synthesizes the final response using valid products.



### Team Members:
- Hida Fathima  P H  (20221CAI0002)

- Ruchitha A S  (20221CSE0291)

- Manasa B S  (20221ECE0134)
