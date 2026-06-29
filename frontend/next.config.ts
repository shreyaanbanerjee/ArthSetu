import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // This might be the correct placement for Next.js 16+
  // @ts-ignore - Ignore type error if NextConfig hasn't updated its types
  allowedDevOrigins: ["192.168.1.5:3000", "localhost:3000"],
};

export default nextConfig;
