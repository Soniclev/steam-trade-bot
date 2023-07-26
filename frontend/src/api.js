export const API_URL =
  process.env.NODE_ENV === "production"
    ? "https://example.com/api/v1"
    : "http://localhost:8000/api/v1";
