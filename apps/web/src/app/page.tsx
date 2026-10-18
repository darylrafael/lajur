"use client";

import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  LiveKitRoom,
  RoomAudioRenderer,
  StartAudio,
  useConnectionState,
  useDataChannel,
  useLocalParticipant,
} from "@livekit/components-react";
import { ConnectionState } from "livekit-client";
import { Mic, MicOff, PhoneOff, Radio, Activity, Volume2, ShieldAlert } from "lucide-react";

interface TokenResponse {
  token: string;
  url: string;
  roomName: string;
  participantIdentity: string;
  error?: string;
  hint?: string;
}

export default function HomePage() {
  const [token, setToken] = useState<string | null>(null);
  const [livekitUrl, setLivekitUrl] = useState<string | null>(null);
  const [roomName, setRoomName] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const startSession = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const res = await fetch("/api/token");
      const data: TokenResponse = await res.json();
      if (!res.ok || data.error) {
        throw new Error(data.error || "Gagal memperoleh token LiveKit.");
      }
      setToken(data.token);
      setLivekitUrl(data.url);
      setRoomName(data.roomName);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Terjadi kesalahan koneksi";
      setErrorMessage(msg);
    } finally {
      setLoading(false);
    }
  };

  const endSession = () => {
    setToken(null);
    setLivekitUrl(null);
    setRoomName("");
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between p-4 md:p-8">
      {/* Header */}
      <header className="max-w-4xl w-full mx-auto flex items-center justify-between pb-6 border-b border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            <Radio className="text-emerald-400 w-6 h-6 animate-pulse" />
            Lajur Voice Ordering
          </h1>
          <p className="text-xs md:text-sm text-slate-400">
            Demo WebRTC Drive-thru Assistant (Minggu 1: Walking Skeleton Echo)
          </p>
        </div>
        <div className="text-right">
          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-emerald-950 text-emerald-400 border border-emerald-800">
            Preview v0.1.0
          </span>
        </div>
      </header>

      {/* Main Container */}
      <div className="max-w-2xl w-full mx-auto my-auto py-8">
        {errorMessage && (
          <div className="mb-6 p-4 rounded-lg bg-rose-950/50 border border-rose-800 text-rose-200 flex items-start gap-3">
            <ShieldAlert className="w-5 h-5 text-rose-400 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-semibold">{errorMessage}</p>
              <p className="text-xs text-rose-300 mt-1">
                Pastikan kredensial LIVEKIT_URL, LIVEKIT_API_KEY, dan LIVEKIT_API_SECRET telah disetel di environment server.
              </p>
            </div>
          </div>
        )}

        {!token || !livekitUrl ? (
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-8 text-center shadow-xl">
            <div className="w-16 h-16 bg-emerald-500/10 border border-emerald-500/20 rounded-full flex items-center justify-center mx-auto mb-4 text-emerald-400">
              <Mic className="w-8 h-8" />
            </div>
            <h2 className="text-xl font-semibold mb-2">Siap untuk Memulai Sesi Suara</h2>
            <p className="text-slate-400 text-sm max-w-md mx-auto mb-8">
              Klik tombol di bawah untuk membuka koneksi audio WebRTC dua arah langsung dengan agent worker.
              Di fase Minggu 1 ini, worker akan memantulkan pesan data dan audio echo.
            </p>
            <button
              onClick={startSession}
              disabled={loading}
              className="w-full sm:w-auto px-8 py-3.5 bg-emerald-600 hover:bg-emerald-500 text-white font-medium rounded-xl transition duration-200 shadow-lg shadow-emerald-900/30 disabled:opacity-50"
            >
              {loading ? "Menyiapkan Sesi..." : "Mulai Sesi (Start Session)"}
            </button>
          </div>
        ) : (
          <LiveKitRoom
            token={token}
            serverUrl={livekitUrl}
            audio={true}
            video={false}
            onDisconnected={endSession}
            className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl flex flex-col gap-6"
          >
            <SessionController roomName={roomName} onEndSession={endSession} />
            <RoomAudioRenderer />
            <StartAudio label="Klik untuk mengizinkan audio speaker" className="w-full py-2 bg-sky-950/60 border border-sky-800 text-sky-300 text-xs rounded-xl hover:bg-sky-900 transition" />
          </LiveKitRoom>
        )}
      </div>

      {/* Footer / Telemetry Indicator */}
      <footer className="max-w-4xl w-full mx-auto pt-6 border-t border-slate-900 text-center text-xs text-slate-500">
        Lajur Portfolio Project · Arsitektur Cascade Streaming Pipeline · Zero Audio Persistence (ADR-0005)
      </footer>
    </main>
  );
}

function SessionController({
  roomName,
  onEndSession,
}: {
  roomName: string;
  onEndSession: () => void;
}) {
  const connectionState = useConnectionState();
  const { isMicrophoneEnabled, localParticipant } = useLocalParticipant();
  const [latencyMs, setLatencyMs] = useState<number | null>(null);
  const [echoMessage, setEchoMessage] = useState<string>("Menunggu respons agent...");
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Data channel for real application ping-pong roundtrip latency
  const { send } = useDataChannel("lajur-control", (msg) => {
    try {
      const str = new TextDecoder().decode(msg.payload);
      const data = JSON.parse(str);
      if (data.type === "pong" && data.client_time) {
        const rtt = Math.round(performance.now() - data.client_time);
        setLatencyMs(rtt);
      } else if (data.type === "echo") {
        setEchoMessage(data.payload || str);
      }
    } catch {
      // Non-json payload
    }
  });

  const sendPing = useCallback(() => {
    if (connectionState === ConnectionState.Connected && send) {
      const payload = JSON.stringify({
        type: "ping",
        client_time: performance.now(),
      });
      send(new TextEncoder().encode(payload), { reliable: false });
    }
  }, [connectionState, send]);

  useEffect(() => {
    if (connectionState === ConnectionState.Connected) {
      sendPing();
      pingIntervalRef.current = setInterval(sendPing, 2000);
    }
    return () => {
      if (pingIntervalRef.current) clearInterval(pingIntervalRef.current);
    };
  }, [connectionState, sendPing]);

  const toggleMic = async () => {
    if (localParticipant) {
      await localParticipant.setMicrophoneEnabled(!isMicrophoneEnabled);
    }
  };

  const getStatusBadge = () => {
    switch (connectionState) {
      case ConnectionState.Connected:
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            Connected
          </span>
        );
      case ConnectionState.Connecting:
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            Connecting...
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
            Disconnected
          </span>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Status Bar */}
      <div className="flex items-center justify-between pb-4 border-b border-slate-800">
        <div>
          <span className="text-xs text-slate-400 block mb-1">Status Koneksi</span>
          {getStatusBadge()}
        </div>
        <div className="text-right">
          <span className="text-xs text-slate-400 block mb-1">Round-Trip Latency (RTT)</span>
          <div className="flex items-center justify-end gap-1.5 text-sm font-mono font-medium">
            <Activity className="w-4 h-4 text-emerald-400" />
            {latencyMs !== null ? (
              <span className={latencyMs < 150 ? "text-emerald-400" : "text-amber-400"}>
                {latencyMs} ms
              </span>
            ) : (
              <span className="text-slate-500">Mengukur...</span>
            )}
          </div>
        </div>
      </div>

      {/* Room Details & Echo Feed */}
      <div className="bg-slate-950/60 rounded-xl p-4 border border-slate-800 text-xs font-mono space-y-2">
        <div className="flex justify-between text-slate-400">
          <span>Active Room:</span>
          <span className="text-slate-200">{roomName}</span>
        </div>
        <div className="flex justify-between text-slate-400">
          <span>Microphone State:</span>
          <span className={isMicrophoneEnabled ? "text-emerald-400" : "text-rose-400"}>
            {isMicrophoneEnabled ? "Aktif (Unmuted)" : "Muted"}
          </span>
        </div>
        <div className="pt-2 border-t border-slate-800/80">
          <div className="flex items-center gap-1.5 text-slate-400 mb-1">
            <Volume2 className="w-3.5 h-3.5 text-sky-400" />
            <span>Agent Data Channel Feedback:</span>
          </div>
          <p className="text-slate-300 italic">{echoMessage}</p>
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center justify-center gap-4 pt-2">
        <button
          onClick={toggleMic}
          className={`px-5 py-2.5 rounded-xl text-sm font-medium flex items-center gap-2 border transition ${
            isMicrophoneEnabled
              ? "bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-700"
              : "bg-rose-950/40 hover:bg-rose-900/50 text-rose-300 border-rose-800"
          }`}
        >
          {isMicrophoneEnabled ? (
            <>
              <Mic className="w-4 h-4 text-emerald-400" />
              Mute Mic
            </>
          ) : (
            <>
              <MicOff className="w-4 h-4 text-rose-400" />
              Unmute Mic
            </>
          )}
        </button>

        <button
          onClick={onEndSession}
          className="px-5 py-2.5 rounded-xl text-sm font-medium bg-rose-600 hover:bg-rose-500 text-white flex items-center gap-2 transition shadow-lg shadow-rose-950/50"
        >
          <PhoneOff className="w-4 h-4" />
          Akhiri Sesi
        </button>
      </div>
    </div>
  );
}
