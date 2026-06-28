import { ref } from "vue";
import client from "../api/client.js";

const user = ref(null);
const token = ref(localStorage.getItem("token") || "");

if (token.value) {
  try {
    user.value = JSON.parse(localStorage.getItem("user") || "null");
  } catch {
    user.value = null;
  }
}

export function useAuth() {
  async function init() {
    const storedToken = localStorage.getItem("token");
    if (!storedToken) return;
    token.value = storedToken;
    try {
      const { data } = await client.get("/auth/me");
      user.value = data;
      localStorage.setItem("user", JSON.stringify(data));
    } catch (err) {
      logout();
    }
  }

  async function login(username, password) {
    const params = new URLSearchParams();
    params.append("username", username);
    params.append("password", password);
    const { data } = await client.post("/auth/login", params, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    token.value = data.access_token;
    user.value = data.user;
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("user", JSON.stringify(data.user));
    return data;
  }

  async function register(payload) {
    return await client.post("/auth/register", payload);
  }

  function logout() {
    token.value = "";
    user.value = null;
    localStorage.removeItem("token");
    localStorage.removeItem("user");
  }

  function isLoggedIn() {
    return !!token.value;
  }

  return { user, token, init, login, register, logout, isLoggedIn };
}
