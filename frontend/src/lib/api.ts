import axios from "axios";

// Centralized Axios instance for API calls
// - baseURL comes from Vite env (frontend/.env)
// - withCredentials: true to include cookies if needed
// - Authorization header populated from localStorage token
// - 401 handling: clear token and redirect to /login

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000",
  withCredentials: true,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token) {
    config.headers = config.headers ?? {};
    config.headers["Authorization"] = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem("access_token");
      // Avoid redirect loops if already on login
      if (typeof window !== "undefined" && !window.location.pathname.includes("/login")) {
        window.location.assign("/login");
      }
    }
    return Promise.reject(error);
  }
);

export default api;


