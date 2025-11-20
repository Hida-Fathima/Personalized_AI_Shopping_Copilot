import React, { useState } from "react";
import Container from "@mui/material/Container";
import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import ChatBox from "./ChatBox";
import Login from "./Login";

function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || null);
  const [username, setUsername] = useState(localStorage.getItem("username") || null);

  const handleLogin = ({ token, username }) => {
    localStorage.setItem("token", token);
    localStorage.setItem("username", username);
    setToken(token);
    setUsername(username);
  };

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    setToken(null);
    setUsername(null);
  };

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">🛍️ Shopping Copilot</Typography>
        <Box>
          {token ? (
            <>
              <Typography component="span" mr={2}>Welcome, {username}</Typography>
              <Button variant="outlined" color="secondary" onClick={handleLogout}>Logout</Button>
            </>
          ) : null}
        </Box>
      </Box>

      {!token ? (
        <Login onLogin={handleLogin} />
      ) : (
        <ChatBox token={token} username={username} />
      )}

      <Box mt={6} textAlign="center" color="text.secondary">
        <Typography variant="caption">Built with ScraperAPI + Material UI · Local demo</Typography>
      </Box>
    </Container>
  );
}

export default App;
