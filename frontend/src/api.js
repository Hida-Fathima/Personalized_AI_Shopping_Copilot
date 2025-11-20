// frontend/src/api.js
const BACKEND = "http://127.0.0.1:8000";

export async function register(email, password, name) {
  const form = new FormData();
  form.append("email", email);
  form.append("password", password);
  form.append("name", name || "");
  const res = await fetch(`${BACKEND}/register`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function login(email, password) {
  const form = new FormData();
  form.append("email", email);
  form.append("password", password);
  const res = await fetch(`${BACKEND}/login`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function search(query, min_price, max_price, file) {
  const form = new FormData();
  form.append("query", query);
  if (min_price) form.append("min_price", min_price);
  if (max_price) form.append("max_price", max_price);
  if (file) form.append("image", file);
  const res = await fetch(`${BACKEND}/search`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function chat(message, history) {
  const form = new FormData();
  form.append("message", message);
  if (history) form.append("history", history);
  const res = await fetch(`${BACKEND}/chat`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
