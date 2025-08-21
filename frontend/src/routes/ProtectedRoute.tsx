import { Navigate, Outlet, useLocation } from "react-router-dom";
import { isTokenExpired } from "../utils/jwt";

export default function ProtectedRoute() {
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
  const expired = token ? isTokenExpired(token) : true;
  const location = useLocation();

  if (!token || expired) {
    if (expired) {
      localStorage.removeItem("access_token");
    }
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
}


