import React from "react";

export default function ImagePreview({ file, onCancel }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 12, marginTop: 10 }}>
      <img src={URL.createObjectURL(file)} alt="preview" style={{ width: 80, borderRadius: 8 }} />
      <button onClick={onCancel} style={{ padding: "6px 10px", background: "#ef4444", color: "white", borderRadius: 6 }}>
        Remove
      </button>
    </div>
  );
}
