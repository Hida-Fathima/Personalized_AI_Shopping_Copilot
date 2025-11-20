import torch
import torch.nn as nn
from transformers import DistilBertModel
import joblib

class CrossEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.bert = DistilBertModel.from_pretrained("distilbert-base-uncased")
        self.fc = nn.Linear(768, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, queries, products, tokenizer):
        encoded = tokenizer(
            queries,
            products,
            padding=True,
            truncation=True,
            return_tensors="pt"
        )
        outputs = self.bert(
            input_ids=encoded["input_ids"],
            attention_mask=encoded["attention_mask"]
        )
        cls = outputs.last_hidden_state[:, 0, :]
        return self.sigmoid(self.fc(cls))

# Load tokenizer + model

tokenizer = joblib.load("crossencoder_tokenizer.pkl")
reranker = CrossEncoder()
reranker.load_state_dict(torch.load("crossencoder_reranker.pt", map_location="cpu"))
reranker.eval()

def compute_relevance(query, title):
    with torch.no_grad():
        score = reranker([query], [title], tokenizer).item()
    return score
