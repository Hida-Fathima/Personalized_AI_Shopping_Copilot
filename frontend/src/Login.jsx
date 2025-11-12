import React, { useState } from "react";
import axios from "axios";

export default function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [isSignup, setIsSignup] = useState(false);
  const [error, setError] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    setError("");
    const form = new FormData();
    form.append("email", email);
    form.append("password", password);
    if (isSignup) form.append("name", name);
    try {
      const res = await axios.post(`http://127.0.0.1:8000/auth/${isSignup ? "signup" : "login"}`, form);
      localStorage.setItem("token", res.data.token);
      localStorage.setItem("user", JSON.stringify(res.data.user));
      onLogin(res.data.user);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed");
    }
  };

  return (
    <div className="flex justify-center items-center h-screen bg-gray-100">
      <div className="bg-white shadow-lg rounded-lg p-8 w-96">
        <h2 className="text-center text-2xl font-bold mb-4 text-blue-600">
          {isSignup ? "Create Account" : "Welcome Back"}
        </h2>
        <form onSubmit={submit} className="flex flex-col gap-3">
          {isSignup && <input placeholder="Name" value={name} onChange={(e) => setName(e.target.value)} required />}
          <input placeholder="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <input placeholder="Password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
          <button type="submit" className="bg-blue-600 text-white py-2 rounded mt-2 hover:bg-blue-700 transition">
            {isSignup ? "Sign up" : "Login"}
          </button>
        </form>
        {error && <p className="text-red-600 mt-2">{error}</p>}
        <p className="text-center mt-4">
          {isSignup ? "Already have an account?" : "New user?"}{" "}
          <button onClick={() => setIsSignup(!isSignup)} className="text-blue-600 underline">
            {isSignup ? "Login" : "Sign up"}
          </button>
        </p>
      </div>
    </div>
  );
}
