import { test, expect } from "@playwright/test";
import { GET } from "../src/app/api/token/route";
import { NextRequest } from "next/server";

test.describe("Token Route Unit Logic (No Network)", () => {
  test("generates valid token, 5m TTL, and unguessable room when LIVE_MODE_ENABLED=true", async () => {
    const originalLive = process.env.LIVE_MODE_ENABLED;
    const originalUrl = process.env.LIVEKIT_URL;
    const originalKey = process.env.LIVEKIT_API_KEY;
    const originalSecret = process.env.LIVEKIT_API_SECRET;

    process.env.LIVE_MODE_ENABLED = "true";
    process.env.LIVEKIT_URL = "wss://mock-test.livekit.cloud";
    process.env.LIVEKIT_API_KEY = "devkey";
    process.env.LIVEKIT_API_SECRET = "secretsecretsecretsecretsecretsecret32";

    try {
      const req = new NextRequest("http://localhost:3000/api/token");
      const resp = await GET(req);
      expect(resp.status).toBe(200);

      const data = await resp.json();
      expect(data.token).toBeDefined();
      expect(typeof data.token).toBe("string");
      expect(data.url).toBe("wss://mock-test.livekit.cloud");
      // Verify cryptographically unguessable hex suffix (16 hex chars = 8 bytes entropy)
      expect(data.roomName).toMatch(/^lajur-room-[a-f0-9]{16}$/);
      expect(data.participantIdentity).toMatch(/^user-[a-f0-9]{16}$/);
    } finally {
      if (originalLive !== undefined) process.env.LIVE_MODE_ENABLED = originalLive;
      else delete process.env.LIVE_MODE_ENABLED;
      if (originalUrl !== undefined) process.env.LIVEKIT_URL = originalUrl;
      else delete process.env.LIVEKIT_URL;
      if (originalKey !== undefined) process.env.LIVEKIT_API_KEY = originalKey;
      else delete process.env.LIVEKIT_API_KEY;
      if (originalSecret !== undefined) process.env.LIVEKIT_API_SECRET = originalSecret;
      else delete process.env.LIVEKIT_API_SECRET;
    }
  });

  test("returns 403 when LIVE_MODE_ENABLED is false or unset", async () => {
    const originalLive = process.env.LIVE_MODE_ENABLED;
    process.env.LIVE_MODE_ENABLED = "false";

    try {
      const req = new NextRequest("http://localhost:3000/api/token");
      const resp = await GET(req);
      expect(resp.status).toBe(403);

      const data = await resp.json();
      expect(data.error).toBe("Live mode is disabled.");
      expect(data.message).toContain("Live voice sessions are currently disabled");
    } finally {
      if (originalLive !== undefined) process.env.LIVE_MODE_ENABLED = originalLive;
      else delete process.env.LIVE_MODE_ENABLED;
    }
  });
});
