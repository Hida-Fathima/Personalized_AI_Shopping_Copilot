import React from "react";

const ChatMessage = ({ role, text, image }) => {
  const isUser = role === "user";

  return (
    <div
      style={{
        background: isUser ? "#3b82f6" : "#e5e7eb",
        color: isUser ? "white" : "black",
        padding: 12,
        borderRadius: 10,
        margin: "10px 0",
        maxWidth: "70%",
        marginLeft: isUser ? "auto" : "0",
      }}
    >
      {image && <img src={image} alt="" style={{ width: 120, borderRadius: 8, marginBottom: 8 }} />}
      <div>{text}</div>
    </div>
  );
};

export default ChatMessage;
