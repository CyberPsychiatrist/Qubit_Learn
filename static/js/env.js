window.env = {
  BACKEND_URL:
    window.location.hostname === "localhost"
      ? "http://127.0.0.1:8000"
      : "https://your-production-backend-url.com"
};
