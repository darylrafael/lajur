import crypto from "node:crypto";
import { AccessToken, RoomAgentDispatch, RoomConfiguration } from "livekit-server-sdk";
import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
  // 1. Check Live Mode gate flag (default false everywhere)
  const isLiveEnabled = process.env.LIVE_MODE_ENABLED === "true";
  if (!isLiveEnabled) {
    return NextResponse.json(
      {
        error: "Live mode is disabled.",
        message:
          "Live voice sessions are currently disabled. Please use the interactive offline demo replay mode.",
      },
      { status: 403 }
    );
  }

  // =========================================================================
  // [MINGGU 9 SECURITY PLUG-IN PLACEHOLDER]
  // 1. IP Rate Limiting:
  //    const clientIp = req.headers.get("x-forwarded-for") || "unknown";
  //    if (!checkRateLimit(clientIp)) return NextResponse.json({ error: "Rate limit exceeded" }, { status: 429 });
  // 2. Cloudflare Turnstile Captcha:
  //    const captchaToken = req.headers.get("x-turnstile-token");
  //    if (!await verifyTurnstile(captchaToken)) return NextResponse.json({ error: "Invalid captcha" }, { status: 403 });
  // =========================================================================

  const apiKey = process.env.LIVEKIT_API_KEY;
  const apiSecret = process.env.LIVEKIT_API_SECRET;
  const livekitUrl = process.env.LIVEKIT_URL;

  if (!apiKey || !apiSecret || !livekitUrl) {
    return NextResponse.json(
      {
        error: "LiveKit server credentials are not configured in environment.",
        hint: "Please provide LIVEKIT_URL, LIVEKIT_API_KEY, and LIVEKIT_API_SECRET.",
      },
      { status: 500 }
    );
  }

  // Generate cryptographically random, unguessable room name and participant identity
  const randomSuffix = crypto.randomBytes(8).toString("hex");
  const roomName = `lajur-room-${randomSuffix}`;
  const participantIdentity = `user-${randomSuffix}`;

  // Short-lived token: 5 minutes (300s). Sufficient for the 3-minute max session limit.
  const at = new AccessToken(apiKey, apiSecret, {
    identity: participantIdentity,
    name: "Customer Guest",
    ttl: "5m",
  });

  at.addGrant({
    room: roomName,
    roomJoin: true,
    canPublish: true,
    canSubscribe: true,
    canPublishData: true,
  });

  // Explicitly dispatch the agent worker to this room
  at.roomConfig = new RoomConfiguration({
    agents: [new RoomAgentDispatch({ agentName: "lajur-voice-agent" })],
  });

  const token = await at.toJwt();

  return NextResponse.json({
    token,
    url: livekitUrl,
    roomName,
    participantIdentity,
  });
}
