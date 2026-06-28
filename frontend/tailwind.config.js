/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,js}"],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: "#E5572A",
          secondary: "#FF6B4A",
          accent: "#C4451F",
        },
        cosmic: {
          success: "#00D4AA",
          warning: "#F59E0B",
          danger: "#EF4444",
          dark: "#1E293B",
          muted: "#475569",
          border: "#E2E8F0",
          bg: "#F0F4F8",
        },
      },
      borderRadius: {
        card: "12px",
        btn: "8px",
        input: "10px",
      },
      boxShadow: {
        card: "0 4px 24px rgba(0,0,0,0.08)",
        btn: "0 4px 15px rgba(229,87,42,0.2)",
      },
    },
  },
  plugins: [],
};
