import React, { useState } from "react";
import "./App.css";

function App() {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState("");
  const [selectedImage, setSelectedImage] = useState(null);
  const [previewImage, setPreviewImage] = useState(null);

  const sendMessage = async () => {
    if (!inputText.trim() && !selectedImage) return;

    const formData = new FormData();
    formData.append("message", inputText);
    if (selectedImage) formData.append("image", selectedImage);

    const response = await fetch("http://127.0.0.1:8000/chat", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    setMessages((prev) => [
      ...prev,
      { sender: "user", text: inputText, image: previewImage },
      { sender: "bot", text: data.reply, products: data.products },
    ]);

    setInputText("");
    setSelectedImage(null);
    setPreviewImage(null);
  };

  const handleImageUpload = (e) => {
    const file = e.target.files[0];
    setSelectedImage(file);
    setPreviewImage(URL.createObjectURL(file));
  };

  return (
    <div className="app-container">
      <h2 className="header">🛍️ Shopping Copilot</h2>

      <div className="chat-box">
        {messages.map((msg, index) => (
          <div
            key={index}
            className={`message ${msg.sender === "user" ? "user" : "bot"}`}
          >
            {msg.image && <img src={msg.image} className="chat-image" alt="user input" />}
            <p>{msg.text}</p>

            {msg.products && (
              <div className="product-grid">
                {msg.products.map((p, i) => (
                  <div className="product-card" key={i}>
                    <img src={p.image} alt={p.name} />
                    <h4>{p.name}</h4>
                    <p className="price">{p.price}</p>
                    <a href={p.link} target="_blank" rel="noreferrer">
                      <button className="view-btn">View</button>
                    </a>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="input-area">
        <input
          type="text"
          placeholder="Ask me about products, prices, or upload an image..."
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
        />

        <label className="image-upload">
          📷
          <input type="file" accept="image/*" onChange={handleImageUpload} hidden />
        </label>

        <button onClick={sendMessage} className="send-btn">Send</button>
      </div>
    </div>
  );
}

export default App;
