import type { NextConfig } from "next";

const allowedOrigins = ["192.168.1.5", "192.168.1.46", "localhost"];
if (process.env.FRONTEND_ORIGIN) {
  try {
    const url = new URL(process.env.FRONTEND_ORIGIN);
    allowedOrigins.push(url.host);
  } catch {
    allowedOrigins.push(process.env.FRONTEND_ORIGIN.replace(/^https?:\/\//, ''));
  }
}

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // @ts-ignore - Ignore type error if NextConfig hasn't updated its types
  allowedDevOrigins: allowedOrigins,
  typescript: {
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
