import axios from "axios";
import type { AxiosError, AxiosResponse } from "axios";

// API base URL dari environment variable atau default
const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

// Create axios instance dengan default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 seconds timeout
  headers: {
    "Content-Type": "application/json",
  },
});

/**
 * Request interceptor - Add auth token to all requests
 */
api.interceptors.request.use(
  (config) => {
    // Get token dari localStorage (bisa 'token' atau 'accessToken')
    const token =
      localStorage.getItem("accessToken") || localStorage.getItem("token");
    if (token) {
      config.headers = config.headers ?? {};
      config.headers["Authorization"] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response interceptor - Handle errors and token expiration
 */
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error: AxiosError) => {
    // Handle 401 Unauthorized (token expired or invalid)
    if (error.response?.status === 401) {
      const errorData = error.response?.data as any;
      const errorDetail = errorData?.detail || "";

      // Check if it's a token expiration issue
      if (
        errorDetail.toLowerCase().includes("expired") ||
        errorDetail.includes("Invalid token") ||
        errorDetail.includes("User not found") ||
        errorDetail.toLowerCase().includes("invalid or expired")
      ) {
        console.warn(
          "Token expired or invalid, clearing auth and redirecting to login"
        );

        // Clear auth data from localStorage
        localStorage.removeItem("accessToken");
        localStorage.removeItem("token");
        localStorage.removeItem("user");

        // Redirect to login page
        setTimeout(() => {
          window.location.href = "/login";
        }, 1000);

        return Promise.reject({
          ...error,
          message: "Session expired. Please login again.",
          isAuthError: true,
        });
      }
    }

    // Handle 429 Too Many Requests (rate limited)
    if (error.response?.status === 429) {
      const retryAfter = error.response.headers["retry-after"] || "60";
      console.warn(`Rate limited. Retry after ${retryAfter} seconds`);

      return Promise.reject({
        ...error,
        message: `Too many requests. Please wait ${retryAfter} seconds before trying again.`,
        isRateLimited: true,
      });
    }

    // Handle 413 Request Entity Too Large
    if (error.response?.status === 413) {
      return Promise.reject({
        ...error,
        message: "Request is too large. Please try with smaller data.",
      });
    }

    // Handle 500 Server Error
    if (error.response?.status === 500) {
      return Promise.reject({
        ...error,
        message: "Server error. Please try again later.",
      });
    }

    // Handle 400 Bad Request
    if (error.response?.status === 400) {
      const errorData = error.response?.data as any;
      return Promise.reject({
        ...error,
        message:
          errorData?.detail || "Invalid request. Please check your input.",
      });
    }

    // Handle 404 Not Found
    if (error.response?.status === 404) {
      const errorData = error.response?.data as any;
      return Promise.reject({
        ...error,
        message: errorData?.detail || "Resource not found.",
      });
    }

    // Handle network timeout
    if (error.code === "ECONNABORTED") {
      return Promise.reject({
        ...error,
        message:
          "Request timeout. The server took too long to respond. Please try again.",
        isTimeout: true,
      });
    }

    // Handle network errors (no response from server)
    if (!error.response) {
      return Promise.reject({
        ...error,
        message:
          "Network error. Please check your internet connection and try again.",
        isNetworkError: true,
      });
    }

    return Promise.reject(error);
  }
);

export default api;
