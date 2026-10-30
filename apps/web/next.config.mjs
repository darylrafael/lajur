import path from "node:path";
import { fileURLToPath } from "node:url";
import nextEnv from "@next/env";

const { loadEnvConfig } = nextEnv;
const __dirname = path.dirname(fileURLToPath(import.meta.url));
// Load root .env into Next.js environment
loadEnvConfig(path.resolve(__dirname, "../../"));

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    LIVE_MODE_ENABLED: process.env.LIVE_MODE_ENABLED || "false",
  },
};

export default nextConfig;
