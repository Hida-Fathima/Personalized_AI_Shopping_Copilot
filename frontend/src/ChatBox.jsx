import React, { useState, useRef } from "react";
import axios from "axios";
import Paper from "@mui/material/Paper";
import Box from "@mui/material/Box";
import TextField from "@mui/material/TextField";
import Button from "@mui/material/Button";
import Typography from "@mui/material/Typography";
import Grid from "@mui/material/Grid";
import Card from "@mui/material/Card";
import CardMedia from "@mui/material/CardMedia";
import CardContent from "@mui/material/CardContent";
import CardActions from "@mui/material/CardActions";
import IconButton from "@mui/material/IconButton";
import SendIcon from "@mui/icons-material/Send";
import ImageIcon from "@mui/icons-material/Image";

export default function ChatBox({ token, username }) {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [file, setFile] = useState(null);
  const API = process.env.REACT_APP_API || "http://127.0.0.1:8000";
  const fileRef = useRef();

  const send = async () => {
    if (!input && !file) return;
    const userText = input || (file ? "Image uploaded" : "");
    setMessages(prev => [...prev, { who: "user", text: userText }]);
    setInput("");

    const fd = new FormData();
    fd.append("message", userText);
    if (file) fd.append("file", file);
    if (token) fd.append("token", token);

    try {
      const res = await axios.post(`${API}/chat`, fd, {
        headers: { "Content-Type": "multipart/form-data" },
        timeout: 60000
      });
      const { reply, products } = res.data;
      setMessages(prev => [...prev, { who: "bot", text: reply, products }]);
      setFile(null);
      if (fileRef.current) fileRef.current.value = "";
      window.scrollTo(0, document.body.scrollHeight);
    } catch (err) {
      console.error(err);
      setMessages(prev => [...prev, { who: "bot", text: "Sorry — something went wrong while contacting backend." }]);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 2 }}>
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle1">Chat with your Shopping Copilot</Typography>
        <Typography variant="caption" color="text.secondary">You can upload an image and/or enter text (both together work).</Typography>
      </Box>

      <Box sx={{ minHeight: 250, maxHeight: 520, overflow: "auto", p: 1 }}>
        {messages.length === 0 && <Typography color="text.secondary">Start by asking about a product or upload an image of what you want.</Typography>}

        {messages.map((m, i) => (
          <Box key={i} mb={2} display="flex" flexDirection={m.who==="user" ? "row-reverse" : "row"}>
            <Paper sx={{ p: 1.5, maxWidth: "80%" }}>
              <Typography variant="body2" sx={{ whiteSpace: "pre-wrap" }}>{m.text}</Typography>

              {m.products && m.products.length > 0 && (
                <Grid container spacing={2} mt={1}>
                  {m.products.map((p, idx) => (
                    <Grid item xs={12} sm={6} md={4} key={idx}>
                      <Card variant="outlined" sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
                        {p.image ? (
                          <CardMedia component="img" image={p.image} alt={p.title} sx={{ height: 160, objectFit: "contain", background: "#fafafa" }} />
                        ) : (
                          <Box sx={{ height:160, display:"flex", alignItems:"center", justifyContent:"center", background:"#fafafa" }}>
                            <ImageIcon sx={{ fontSize: 48, color: "grey.400" }} />
                          </Box>
                        )}
                        <CardContent sx={{ flexGrow:1 }}>
                          <Typography variant="subtitle2">{p.title}</Typography>
                          <Typography variant="body2" color="primary" sx={{ mt: 1 }}>{p.price}</Typography>
                          <Typography variant="caption" color="text.secondary">{p.source}</Typography>
                        </CardContent>
                        <CardActions>
                          <Button size="small" target="_blank" rel="noreferrer" href={p.url}>Open</Button>
                        </CardActions>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              )}
            </Paper>
          </Box>
        ))}
      </Box>

      <Box display="flex" gap={1} alignItems="center" mt={2}>
        <TextField fullWidth placeholder="Ask about products or upload image..." value={input} onChange={(e)=>setInput(e.target.value)} />
        <input ref={fileRef} type="file" accept="image/*" style={{ display: "none" }} id="file-input" onChange={(e)=>setFile(e.target.files[0])} />
        <label htmlFor="file-input">
          <IconButton component="span" color={file ? "primary" : "default"}>
            <ImageIcon />
          </IconButton>
        </label>
        <IconButton onClick={send} color="primary" sx={{ bgcolor: "primary.main", color: "white" }}>
          <SendIcon />
        </IconButton>
      </Box>
    </Paper>
  );
}

