import React from "react";

export default function ProductGrid({ products }) {
  return (
    <div style={{ display: "flex", gap: 20, overflowX: "auto", padding: "10px 0" }}>
      {products.map((p, index) => (
        <div key={index} style={{ minWidth: 180, background: "white", padding: 12, borderRadius: 8, textAlign: "center", border: "1px solid #ddd" }}>
          <img src={p.image} alt={p.name} style={{ width: "100%", height: 140, objectFit: "cover", borderRadius: 6 }} />
          <h4 style={{ fontSize: 15, marginTop: 8 }}>{p.name}</h4>
          <p style={{ color: "green", fontWeight: "bold" }}>₹{p.price}</p>
          <a href={p.url} target="_blank" rel="noopener noreferrer">
            <button style={{ marginTop: 8, padding: "8px 14px", background: "#2563eb", color: "white", borderRadius: 6 }}>
              View
            </button>
          </a>
        </div>
      ))}
    </div>
  );
}
