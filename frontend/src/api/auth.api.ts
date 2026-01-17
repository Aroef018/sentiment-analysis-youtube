import api from "./axios";

export const loginApi = (email: string, password: string) =>
  api.post("/auth/login", { email, password });

export const registerApi = (
  email: string,
  full_name: string,
  password: string
) =>
  api.post("/auth/register", {
    email,
    full_name,
    password,
  });

export const meApi = () => api.get("/auth/me");

export const googleLoginApi = (idToken: string) =>
  api.post("/auth/google", { token: idToken });

export const logoutApi = () => api.post("/auth/logout");
