import React, { useState } from "react";
import axios from "axios";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";

export default function Login({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const API = process.env.REACT_APP_API || "http://127.0.0.1:8000";

  const submit = async () => {
    setError("");
    try {
      if (mode === "register") {
        await axios.post(`${API}/register`, { username, password, email });
        setMode("login");
        alert("Registered — please login");
        return;
      }
      const res = await axios.post(`${API}/login`, { username, password });
      onLogin({ token: res.data.token, username: res.data.username });
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    }
  };

  return (
    <Paper elevation={3} sx={{ maxWidth: 540, mx: "auto", p: 4 }}>
      <Typography variant="h6" gutterBottom>
        {mode === "login" ? "Login" : "Create account"}
      </Typography>

      {mode === "register" && (
        <TextField label="Email" value={email} onChange={(e)=>setEmail(e.target.value)} fullWidth margin="normal" />
      )}
      <TextField label="Username" value={username} onChange={(e)=>setUsername(e.target.value)} fullWidth margin="normal" />
      <TextField label="Password" value={password} onChange={(e)=>setPassword(e.target.value)} type="password" fullWidth margin="normal" />

      {error && <Typography color="error" mt={1}>{error}</Typography>}

      <Box mt={2} display="flex" gap={2}>
        <Button variant="contained" onClick={submit}>{mode === "login" ? "Login" : "Register"}</Button>
        <Button variant="outlined" onClick={()=>setMode(mode==="login" ? "register" : "login")}>
          {mode==="login" ? "Create Account" : "Back to login"}
        </Button>
      </Box>
    </Paper>
  );
}
