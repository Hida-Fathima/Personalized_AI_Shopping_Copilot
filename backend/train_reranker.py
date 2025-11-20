import random
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from transformers import DistilBertTokenizer, DistilBertModel
from sklearn.metrics import classification_report, confusion_matrix
import joblib
from tqdm import tqdm

# ===========================================================
# 1. CREATE SYNTHETIC DATA (much faster set but still strong)
# ===========================================================

categories = {
    "red dress": [
        "Red Party Dress for Girls",
        "Women's Red Maxi Dress",
        "Girls Red Frock",
        "Red Evening Gown",
        "Red Floral Dress"
    ],
    "kurti": [
        "Women Cotton Printed Kurti",
        "Anarkali Kurti",
        "Office Wear Kurti",
        "Indo Western Kurti",
        "Printed Kurti"
    ],
    "shoes": [
        "Mens Leather Shoes",
        "Sports Running Shoes",
        "Formal Black Shoes",
        "Casual Walking Shoes",
        "Men's Sneakers"
    ],
    "mobile": [
        "Samsung Android Mobile",
        "Redmi Budget Smartphone",
        "Vivo 5G Mobile",
        "iPhone XR Smartphone",
        "Realme Camera Phone"
    ]
}

negative_noise = [
    "Plastic Plates Pack",
    "Toy Car for Kids",
    "Notebook for School",
    "Laptop Skin Sticker",
    "Hairband for Girls"
]

data = []

for query, titles in categories.items():
    for title in titles:
        for _ in range(50):  # 5 classes × 5 items × 50 → 1250 positives
            data.append((query, title, 1))

for _ in range(1500):  # negative samples
    q = random.choice(list(categories.keys()))
    t = random.choice(negative_noise)
    data.append((q, t, 0))

random.shuffle(data)
print(f"Total samples: {len(data)}")

# ===========================================================
# 2. DATASET + DATALOADER
# ===========================================================

tokenizer = DistilBertTokenizer.from_pretrained("distilbert-base-uncased")

class RerankerDataset(Dataset):
    def __init__(self, data):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        q, t, label = self.data[idx]
        return q, t, torch.tensor(label, dtype=torch.float32)

def collate(batch):
    queries = [item[0] for item in batch]
    titles = [item[1] for item in batch]
    labels = torch.stack([item[2] for item in batch])
    enc = tokenizer(queries, titles, padding=True, truncation=True, return_tensors="pt")
    return enc, labels

loader = DataLoader(RerankerDataset(data), batch_size=16, shuffle=True, collate_fn=collate)

# ===========================================================
# 3. MODEL
# ===========================================================

class CrossEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.bert = DistilBertModel.from_pretrained("distilbert-base-uncased")
        self.fc = nn.Linear(768, 1)

    def forward(self, enc):
        out = self.bert(**enc).last_hidden_state[:, 0, :]
        return torch.sigmoid(self.fc(out))

model = CrossEncoder()
device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

criterion = nn.BCELoss()
optimizer = torch.optim.Adam(model.parameters(), lr=2e-5)

# ===========================================================
# 4. TRAINING LOOP (FAST)
# ===========================================================

print("Training started...")

for epoch in range(2):
    epoch_loss = 0
    for enc, labels in tqdm(loader):
        enc = {k: v.to(device) for k, v in enc.items()}
        labels = labels.to(device)

        optimizer.zero_grad()
        scores = model(enc).squeeze()
        loss = criterion(scores, labels)
        loss.backward()
        optimizer.step()
        epoch_loss += loss.item()

    print("Epoch", epoch+1, "Loss:", epoch_loss/len(loader))

# ===========================================================
# 5. EVALUATION
# ===========================================================

y_true = []
y_pred = []

eval_loader = DataLoader(RerankerDataset(data), batch_size=32, shuffle=False, collate_fn=collate)

with torch.no_grad():
    for enc, labels in eval_loader:
        enc = {k: v.to(device) for k, v in enc.items()}
        scores = model(enc).squeeze().cpu()
        preds = (scores > 0.5).int().tolist()
        y_pred.extend(preds)
        y_true.extend(labels.tolist())

print("\n===== CLASSIFICATION REPORT =====")
print(classification_report(y_true, y_pred))

print("\n===== CONFUSION MATRIX =====")
print(confusion_matrix(y_true, y_pred))

# ===========================================================
# 6. SAVE MODEL
# ===========================================================

torch.save(model.state_dict(), "crossencoder_reranker.pt")
joblib.dump(tokenizer, "crossencoder_tokenizer.pkl")

print("\nModel saved successfully!")
