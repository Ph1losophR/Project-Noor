import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Throwaway demo: /api/* proxies to the Python process on the same machine
  // (ADR 0006 — one machine, one file, no network gap). A static export served
  // by that same process uses same-origin /api/* and needs no proxy.
  async rewrites() {
    return [
      { source: "/api/:path*", destination: "http://localhost:8000/api/:path*" },
    ];
  },
};

export default nextConfig;
