"use client";

import React, { Suspense, useState, useEffect, useCallback, useRef } from "react";
import { useSearchParams } from "next/navigation";
import {
  LiveKitRoom,
  RoomAudioRenderer,
  StartAudio,
  useConnectionState,
  useDataChannel,
  useLocalParticipant,
} from "@livekit/components-react";
import { ConnectionState } from "livekit-client";
import { ShieldAlert, AlertTriangle, Radio } from "lucide-react";

import { I18nProvider, useI18n } from "../lib/i18n";
import { useSimulator, SimulatorMode } from "../hooks/useSimulator";
import { Header } from "../components/Header";
import { LiveTranscript } from "../components/LiveTranscript";
import { CartPanel } from "../components/CartPanel";
import { MenuBoard } from "../components/MenuBoard";
import { BotReplyCard } from "../components/BotReplyCard";
import { StatusControls } from "../components/StatusControls";
import { ReplayController } from "../components/ReplayController";
import { NoisePresetControls, NoisePreset } from "../components/NoisePresetControls";
import { HandoffBanner } from "../components/HandoffBanner";
import { WebProtocolEvent } from "../types/protocol";

export default function Page() {
  return (
    <I18nProvider>
      <Suspense fallback={<SimulatorLoading />}>
        <SimulatorApp />
      </Suspense>
    </I18nProvider>
  );
}

function SimulatorLoading() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 flex items-center justify-center p-4">
      <div className="flex items-center gap-3">
        <Radio className="w-6 h-6 text-emerald-400 animate-pulse" />
        <span className="text-sm font-medium">Memuat Lajur Simulator...</span>
      </div>
    </div>
  );
}

function SimulatorApp() {
  const searchParams = useSearchParams();
  const replayParam = searchParams.get("replay");
  const modeParam = searchParams.get("mode");

  const initialMode: SimulatorMode = modeParam === "live" ? "live" : "replay"; // Default to safe replay for public preview
  const initialScenario = replayParam || "simple";

  const {
    mode,
    setMode,
    status,
    setStatus,
    dialogState,
    cart,
    partialTranscript,
    finalTranscript,
    transcriptHistory,
    botReply,
    pendingQuestion,
    handoffData,
    errorMessage,
    setErrorMessage,
    sessionLimits,
    cartUpdatedCue,
    processEvent,
    resetState,
    selectedScenario,
    setSelectedScenario,
    isReplaying,
    startReplay,
    pauseReplay,
    restartReplay,
  } = useSimulator(initialMode, initialScenario);

  const { t } = useI18n();

  // Mobile navigation tabs
  const [mobileTab, setMobileTab] = useState<"menu" | "transcript" | "cart">("transcript");

  // Client-side noise preset state
  const [noisePreset, setNoisePreset] = useState<NoisePreset>("clean");
  const [noiseVolume, setNoiseVolume] = useState<number>(0.4);

  // LiveKit connection state
  const [liveToken, setLiveToken] = useState<string | null>(null);
  const [liveUrl, setLiveUrl] = useState<string | null>(null);
  const [isConnectingLive, setIsConnectingLive] = useState<boolean>(false);
  const isLiveModeEnabled = process.env.LIVE_MODE_ENABLED === "true";

  // Set mode / scenario from search params
  useEffect(() => {
    if (modeParam === "live") {
      setMode("live");
    } else if (modeParam === "replay" || replayParam) {
      setMode("replay");
    }
    if (replayParam) {
      setSelectedScenario(replayParam);
    }
  }, [modeParam, replayParam, setMode, setSelectedScenario]);

  const handleStartLiveSession = async () => {
    setIsConnectingLive(true);
    setErrorMessage(null);
    resetState();
    setStatus("connecting");

    try {
      const res = await fetch("/api/token");
      const data = await res.json();
      if (!res.ok || data.error) {
        throw new Error(data.message || data.error || "Gagal memperoleh token LiveKit dari server.");
      }
      setLiveToken(data.token);
      setLiveUrl(data.url);
      setStatus("listening");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Terjadi kesalahan koneksi";
      setErrorMessage(msg);
      setStatus("error");
    } finally {
      setIsConnectingLive(false);
    }
  };

  const handleEndLiveSession = () => {
    setLiveToken(null);
    setLiveUrl(null);
    resetState();
  };

  const handleSelectPendingChoice = (choiceId: string) => {
    if (mode === "live") {
      // In live mode, user can also speak or click choice
      processEvent({
        version: "v1",
        type: "partial_transcript",
        text: choiceId.replace(/_/g, " "),
        is_final: false,
      });
    }
  };

  return (
    <main className="min-h-screen bg-slate-950 text-slate-100 flex flex-col justify-between p-3 md:p-6 font-sans">
      <div className="max-w-7xl w-full mx-auto space-y-4">
        {/* Header */}
        <Header
          mode={mode}
          onModeChange={(newMode) => {
            if (newMode !== mode) {
              if (mode === "live") handleEndLiveSession();
              if (mode === "replay") pauseReplay();
              setMode(newMode);
            }
          }}
        />

        {/* Public Notice Banner if Live Mode */}
        {mode === "live" && !liveToken && (
          <div
            role="note"
            className="p-3.5 rounded-2xl bg-slate-900 border border-slate-800 text-xs text-slate-300 flex items-start gap-3"
          >
            <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold text-amber-300 block mb-0.5">
                {t.liveNoticeTitle}
              </span>
              <p className="text-slate-400">{t.liveNoticeDesc}</p>
            </div>
          </div>
        )}

        {/* Replay Controller Banner if Replay Mode */}
        {mode === "replay" && (
          <ReplayController
            selectedScenario={selectedScenario}
            isReplaying={isReplaying}
            onSelectScenario={(scId) => {
              setSelectedScenario(scId);
              startReplay(scId);
            }}
            onPlay={() => startReplay(selectedScenario)}
            onPause={pauseReplay}
            onRestart={restartReplay}
          />
        )}

        {/* Handoff Banner if Active */}
        <HandoffBanner handoffData={handoffData} />

        {/* Mobile Tab Selector (Visible only on small viewports) */}
        <div className="flex md:hidden items-center p-1 bg-slate-900 border border-slate-800 rounded-xl">
          <button
            type="button"
            onClick={() => setMobileTab("menu")}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition ${
              mobileTab === "menu" ? "bg-slate-800 text-white" : "text-slate-400"
            }`}
          >
            {t.tabMenu}
          </button>
          <button
            type="button"
            onClick={() => setMobileTab("transcript")}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition ${
              mobileTab === "transcript" ? "bg-slate-800 text-white" : "text-slate-400"
            }`}
          >
            {t.tabTranscript}
          </button>
          <button
            type="button"
            onClick={() => setMobileTab("cart")}
            className={`flex-1 py-2 text-xs font-semibold rounded-lg transition flex items-center justify-center gap-1 ${
              mobileTab === "cart" ? "bg-slate-800 text-white" : "text-slate-400"
            }`}
          >
            <span>{t.tabCart}</span>
            {cart.total_item_count > 0 && (
              <span className="w-4 h-4 rounded-full bg-emerald-500 text-slate-950 text-[10px] font-bold flex items-center justify-center">
                {cart.total_item_count}
              </span>
            )}
          </button>
        </div>

        {/* Main Grid: Responsive 3 Columns on Desktop */}
        <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
          {/* Column 1: Menu Board */}
          <div
            className={`md:col-span-4 ${
              mobileTab !== "menu" ? "hidden md:block" : "block"
            }`}
          >
            <MenuBoard />
          </div>

          {/* Column 2: Live Transcript & Bot Reply */}
          <div
            className={`md:col-span-4 space-y-4 ${
              mobileTab !== "transcript" ? "hidden md:block" : "block"
            }`}
          >
            <BotReplyCard
              botReply={botReply}
              isSpeaking={status === "speaking"}
            />
            <LiveTranscript
              partialTranscript={partialTranscript}
              finalTranscript={finalTranscript}
              transcriptHistory={transcriptHistory}
              isListening={status === "listening"}
            />
          </div>

          {/* Column 3: Cart Confirmation & Controls */}
          <div
            className={`md:col-span-4 space-y-4 ${
              mobileTab !== "cart" ? "hidden md:block" : "block"
            }`}
          >
            <CartPanel
              cart={cart}
              dialogState={dialogState}
              pendingQuestion={pendingQuestion}
              cartUpdatedCue={cartUpdatedCue}
              onSelectPendingChoice={handleSelectPendingChoice}
            />

            {/* Client-Side Simulated Noise Presets (Live Mode) */}
            <NoisePresetControls
              mode={mode}
              activePreset={noisePreset}
              onPresetChange={setNoisePreset}
              noiseVolume={noiseVolume}
              onVolumeChange={setNoiseVolume}
            />

            {/* Live Mode Controls vs Replay Mode Controls */}
            {mode === "live" ? (
              liveToken && liveUrl ? (
                <LiveKitRoom
                  token={liveToken}
                  serverUrl={liveUrl}
                  audio={true}
                  video={false}
                  onDisconnected={handleEndLiveSession}
                  className="contents"
                >
                  <LiveRoomDataBridge
                    onEvent={processEvent}
                    status={status}
                    turnsUsed={sessionLimits.turns_used}
                    maxTurns={sessionLimits.max_turns}
                    timeElapsedSeconds={sessionLimits.time_elapsed_seconds}
                    timeLimitSeconds={sessionLimits.time_limit_seconds}
                    errorMessage={errorMessage}
                    onEndSession={handleEndLiveSession}
                    onStartOver={resetState}
                  />
                  <RoomAudioRenderer />
                  <StartAudio
                    label={t.allowAudio}
                    className="w-full py-2 bg-sky-950/60 border border-sky-800 text-sky-300 text-xs rounded-xl hover:bg-sky-900 transition mt-2 font-medium"
                  />
                </LiveKitRoom>
              ) : (
                <StatusControls
                  status={status}
                  isActive={false}
                  isLiveModeDisabled={!isLiveModeEnabled}
                  turnsUsed={sessionLimits.turns_used}
                  maxTurns={sessionLimits.max_turns}
                  timeElapsedSeconds={sessionLimits.time_elapsed_seconds}
                  timeLimitSeconds={sessionLimits.time_limit_seconds}
                  errorMessage={errorMessage}
                  onStart={handleStartLiveSession}
                  onEnd={handleEndLiveSession}
                  onStartOver={resetState}
                />
              )
            ) : (
              <StatusControls
                status={status}
                isActive={isReplaying}
                turnsUsed={sessionLimits.turns_used}
                maxTurns={sessionLimits.max_turns}
                timeElapsedSeconds={sessionLimits.time_elapsed_seconds}
                timeLimitSeconds={sessionLimits.time_limit_seconds}
                errorMessage={errorMessage}
                onStart={() => startReplay(selectedScenario)}
                onEnd={pauseReplay}
                onStartOver={restartReplay}
              />
            )}
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="max-w-7xl w-full mx-auto pt-6 pb-2 border-t border-slate-900 text-center text-[11px] text-slate-500">
        {t.footerNote}
      </footer>
    </main>
  );
}

interface LiveRoomDataBridgeProps {
  onEvent: (event: WebProtocolEvent) => void;
  status: any;
  turnsUsed: number;
  maxTurns: number;
  timeElapsedSeconds: number;
  timeLimitSeconds: number;
  errorMessage?: string | null;
  onEndSession: () => void;
  onStartOver: () => void;
}

function LiveRoomDataBridge({
  onEvent,
  status,
  turnsUsed,
  maxTurns,
  timeElapsedSeconds,
  timeLimitSeconds,
  errorMessage,
  onEndSession,
  onStartOver,
}: LiveRoomDataBridgeProps) {
  const { isMicrophoneEnabled, localParticipant } = useLocalParticipant();

  // WebRTC Data Channel receiver
  const { send } = useDataChannel("lajur-control", (msg) => {
    try {
      const text = new TextDecoder().decode(msg.payload);
      const parsed = JSON.parse(text);

      // Handle Web Protocol v1 events
      if (parsed.version === "v1" && parsed.type) {
        onEvent(parsed as WebProtocolEvent);
      } else if (parsed.type === "cart_update") {
        // Backwards compatibility with legacy messages
        onEvent({
          version: "v1",
          type: "intent_applied",
          state: parsed.dialog_state || "ordering",
          cart: parsed.cart,
          speech_facts: {
            intent_handled: "legacy_update",
            items_added: [],
            items_removed: [],
            items_modified: [],
            items_replaced: [],
            rejections: parsed.rejections || [],
            cart_item_count: parsed.cart?.total_item_count || 0,
            cart_total_price: parsed.cart?.total_price || 0,
            dialog_state: parsed.dialog_state || "ordering",
            requires_confirmation: false,
          },
        });
        if (parsed.bot_reply) {
          onEvent({
            version: "v1",
            type: "bot_reply_text",
            text: parsed.bot_reply,
          });
        }
      }
    } catch {
      // Non-json payload
    }
  });

  const toggleMic = async () => {
    if (localParticipant) {
      await localParticipant.setMicrophoneEnabled(!isMicrophoneEnabled);
    }
  };

  const handleReset = () => {
    if (send) {
      const payload = JSON.stringify({ type: "reset_session" });
      send(new TextEncoder().encode(payload), { reliable: true });
    }
    onStartOver();
  };

  return (
    <StatusControls
      status={status}
      isActive={true}
      isMicMuted={!isMicrophoneEnabled}
      turnsUsed={turnsUsed}
      maxTurns={maxTurns}
      timeElapsedSeconds={timeElapsedSeconds}
      timeLimitSeconds={timeLimitSeconds}
      errorMessage={errorMessage}
      onStart={() => {}}
      onEnd={onEndSession}
      onStartOver={handleReset}
      onToggleMic={toggleMic}
    />
  );
}
