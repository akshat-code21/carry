import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    const rawUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8001";
    const cleanUrl = rawUrl.trim().replace(/\/$/, "");
    const destinationBase = cleanUrl.endsWith("/api") ? cleanUrl : `${cleanUrl}/api`;

    return [
      {
        source: "/api/:path*",
        destination: `${destinationBase}/:path*`,
      },
    ];
  },
};

export default nextConfig;

