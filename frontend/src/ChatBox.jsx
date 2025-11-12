import React, { useState } from "react";
import axios from "axios";

export default function ChatBox() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [image, setImage] = useState(null);
  const backendURL = "http://127.0.0.1:8000/chat";

  const sendMessage = async () => {
    if (!input && !image) return;

    const newMsg = { sender: "user", text: input, image: image ? URL.createObjectURL(image) : null };
    setMessages([...messages, newMsg]);

    const formData = new FormData();
    formData.append("message", input);
    if (image) formData.append("image", image);

    setInput("");
    setImage(null);

    try {
      const res = await axios.post(backendURL, formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      const botReply = { sender: "bot", text: res.data.reply, products: res.data.products || [] };
      setMessages((prev) => [...prev, botReply]);

    } catch (error) {
      setMessages((prev) => [
        ...prev,
        { sender: "bot", text: "⚠️ Error: Unable to connect to AI service." }
      ]);
    }
  };

  return (
    <div style={styles.container}>
      <div style={styles.chatWindow}>
        {messages.map((msg, index) => (
          <div key={index} style={msg.sender === "user" ? styles.userBubble : styles.botBubble}>
            
            {msg.text && <p>{msg.text}</p>}

            {msg.image && <img src={msg.image} alt="" style={styles.imagePreview} />}

            {msg.products && msg.products.length > 0 && (
              <div style={styles.productsContainer}>
                {msg.products.map((p, i) => (
                  <div key={i} style={styles.productCard}>
                    <img src={p.image} alt="product" style={styles.productImage} />
                    <p style={styles.productTitle}>{p.title}</p>
                    <p style={styles.productPrice}>{p.price}</p>
                    <a href={p.link} target="_blank" rel="noreferrer" style={styles.buyBtn}>View</a>
                  </div>
                ))}
              </div>
            )}

          </div>
        ))}
      </div>

      <div style={styles.inputBar}>
        <input
          type="text"
          placeholder="Ask me about products, prices, or upload an image..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          style={styles.input}
        />

        <input type="file" accept="image/*" onChange={(e) => setImage(e.target.files[0])} style={{ display: "none" }} id="imgUpload" />
        <label htmlFor="imgUpload" style={styles.uploadBtn}>📷</label>

        <button onClick={sendMessage} style={styles.sendBtn}>Send</button>
      </div>
    </div>
  );
}

const styles = {
  container: { display: "flex", flexDirection: "column", height: "90vh" },
  chatWindow: {
    flex: 1,
    padding: "15px",
    overflowY: "auto",
    background: "#f5f6fa",
  },
  userBubble: {
    alignSelf: "flex-end",
    background: "#007bff",
    color: "white",
    padding: "10px",
    borderRadius: "10px",
    margin: "6px",
    maxWidth: "60%",
  },
  botBubble: {
    alignSelf: "flex-start",
    background: "#e6e9ee",
    padding: "10px",
    borderRadius: "10px",
    margin: "6px",
    maxWidth: "65%",
  },
  imagePreview: { width: "140px", marginTop: "8px", borderRadius: "8px" },
  productsContainer: {
    display: "flex",
    flexWrap: "wrap",
    gap: "10px",
    marginTop: "10px",
  },
  productCard: {
    width: "150px",
    border: "1px solid #ddd",
    borderRadius: "8px",
    background: "white",
    padding: "10px",
    textAlign: "center",
  },
  productImage: { width: "100%", borderRadius: "6px" },
  productTitle: { fontSize: "14px", fontWeight: "600" },
  productPrice: { fontSize: "14px", color: "green" },
  buyBtn: {
    display: "inline-block",
    marginTop: "6px",
    padding: "4px 8px",
    background: "#007bff",
    color: "white",
    borderRadius: "5px",
    textDecoration: "none",
  },
  inputBar: {
    display: "flex",
    padding: "10px",
    borderTop: "1px solid #ddd",
    background: "white",
  },
  input: { flex: 1, padding: "10px", borderRadius: "6px", border: "1px solid #ccc", marginRight: "8px" },
  uploadBtn: { cursor: "pointer", fontSize: "20px", marginRight: "10px" },
  sendBtn: { padding: "10px 16px", background: "#007bff", color: "white", borderRadius: "6px", border: "none" },
};
