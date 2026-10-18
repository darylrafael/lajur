import { AccessToken, RoomAgentDispatch, RoomConfiguration } from "livekit-server-sdk";
import { NextRequest, NextResponse } from "next/server";

export async function GET(req: NextRequest) {
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

  // Generate unique room name and participant identity
  const randomSuffix = Math.random().toString(36).substring(2, 10);
  const roomName = `lajur-room-${randomSuffix}`;
  const participantIdentity = `user-${randomSuffix}`;

  // Short-lived token: 10 minutes (600s)
  const at = new AccessToken(apiKey, apiSecret, {
    identity: participantIdentity,
    name: "Customer Guest",
    ttl: "10m",
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
    agents: [new RoomAgentDispatch({ agentName: "lajur-echo-agent" })],
  });

  const token = await at.toJwt();

  return NextResponse.json({
    token,
    url: livekitUrl,
    roomName,
    participantIdentity,
  });
}
