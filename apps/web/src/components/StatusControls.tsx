"use client";

import React from "react";
import {
  Mic,
  MicOff,
  PhoneOff,
  RotateCcw,
  Clock,
  Hash,
  AlertCircle,
  HelpCircle,
  Sparkles,
  Users,
  ShieldAlert,
} from "lucide-react";
import { useI18n } from "../lib/i18n";
import { SimulatorStatus } from "../hooks/useSimulator";

interface StatusControlsProps {
  status: SimulatorStatus;
  isActive: boolean;
  isMicMuted?: boolean;
  turnsUsed: number;
  maxTurns: number;
  timeElapsedSeconds: number;
  timeLimitSeconds: number;
  errorMessage?: string | null;
  onStart: () => void;
  onEnd: () => void;
  onStartOver: () => void;
  onToggleMic?: () => void;
}

export function StatusControls({
  status,
  isActive,
  isMicMuted = false,
  turnsUsed,
  maxTurns,
  timeElapsedSeconds,
  timeLimitSeconds,
  errorMessage,
  onStart,
  onEnd,
  onStartOver,
  onToggleMic,
}: StatusControlsProps) {
  const { t } = useI18n();

  const remainingSeconds = Math.max(0, Math.round(timeLimitSeconds - timeElapsedSeconds));
  const minutes = Math.floor(remainingSeconds / 60);
  const seconds = remainingSeconds % 60;
  const formattedTimeLeft = `${minutes.toString().padStart(2, "0")}:${seconds.toString().padStart(2, "0")}`;

  const renderStatusBadge = () => {
    switch (status) {
      case "listening":
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            {t.statusListening}
          </span>
        );
      case "thinking":
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-sky-500/10 text-sky-400 border border-sky-500/20">
            <span className="w-2 h-2 rounded-full bg-sky-400 animate-pulse" />
            {t.statusThinking}
          </span>
        );
      case "speaking":
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30">
            <Sparkles className="w-3.5 h-3.5 text-emerald-400 animate-spin motion-reduce:animate-none" />
            {t.statusSpeaking}
          </span>
        );
      case "awaiting_choice":
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-300 border border-amber-500/30 animate-pulse">
            <HelpCircle className="w-3.5 h-3.5 text-amber-400" />
            {t.statusAwaitingChoice}
          </span>
        );
      case "handoff":
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold bg-rose-500/20 text-rose-300 border border-rose-500/40">
            <Users className="w-3.5 h-3.5 text-rose-400" />
            {t.statusHandoff}
          </span>
        );
      case "connecting":
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20">
            <span className="w-2 h-2 rounded-full bg-amber-400 animate-pulse" />
            {t.statusConnecting}
          </span>
        );
      case "error":
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20">
            <AlertCircle className="w-3.5 h-3.5 text-rose-400" />
            {t.statusError}
          </span>
        );
      default:
        return (
          <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
            <span className="w-2 h-2 rounded-full bg-slate-500" />
            {t.statusIdle}
          </span>
        );
    }
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 md:p-5 shadow-lg space-y-4">
      {/* Top Status & Limits Row */}
      <div className="flex flex-wrap items-center justify-between gap-3 pb-3 border-b border-slate-800">
        <div>
          <span className="text-[10px] text-slate-400 uppercase tracking-wider block mb-1">
            Status Asisten
          </span>
          {renderStatusBadge()}
        </div>

        {/* Session Limits (NFR-03 & §11.2) */}
        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="text-right">
            <span className="text-[10px] text-slate-500 uppercase tracking-wider block mb-0.5">
              {t.turnsUsed}
            </span>
            <div className="flex items-center justify-end gap-1 text-slate-200 font-bold">
              <Hash className="w-3.5 h-3.5 text-slate-400" />
              <span>
                {turnsUsed} / {maxTurns}
              </span>
            </div>
          </div>
          <div className="text-right">
            <span className="text-[10px] text-slate-500 uppercase tracking-wider block mb-0.5">
              {t.timeLeft}
            </span>
            <div className="flex items-center justify-end gap-1 font-bold text-amber-400">
              <Clock className="w-3.5 h-3.5 text-amber-400" />
              <span>{formattedTimeLeft}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Error message alert */}
      {errorMessage && (
        <div
          role="alert"
          className="p-3 rounded-xl bg-rose-950/60 border border-rose-800 text-rose-200 text-xs flex items-start gap-2.5"
        >
          <ShieldAlert className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold">{errorMessage}</p>
          </div>
        </div>
      )}

      {/* Buttons Controls */}
      <div className="flex flex-wrap items-center gap-2 pt-1">
        {!isActive ? (
          <button
            type="button"
            onClick={onStart}
            className="flex-1 min-w-[160px] py-3 px-6 bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-sm rounded-xl transition duration-150 shadow-lg shadow-emerald-950/40 flex items-center justify-center gap-2"
          >
            <Mic className="w-4 h-4" />
            {t.startSession}
          </button>
        ) : (
          <>
            {onToggleMic && (
              <button
                type="button"
                onClick={onToggleMic}
                aria-pressed={isMicMuted}
                className={`py-2.5 px-4 rounded-xl text-xs font-semibold flex items-center gap-2 border transition ${
                  isMicMuted
                    ? "bg-rose-950/40 hover:bg-rose-900/50 text-rose-300 border-rose-800"
                    : "bg-slate-800 hover:bg-slate-700 text-slate-200 border-slate-700"
                }`}
              >
                {isMicMuted ? (
                  <>
                    <MicOff className="w-4 h-4 text-rose-400" />
                    {t.unmuteMic}
                  </>
                ) : (
                  <>
                    <Mic className="w-4 h-4 text-emerald-400" />
                    {t.muteMic}
                  </>
                )}
              </button>
            )}

            <button
              type="button"
              onClick={onStartOver}
              className="py-2.5 px-4 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 transition flex items-center gap-1.5"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              {t.startOver}
            </button>

            <button
              type="button"
              onClick={onEnd}
              className="py-2.5 px-4 rounded-xl text-xs font-semibold bg-rose-600 hover:bg-rose-500 text-white transition flex items-center gap-1.5 ml-auto shadow-sm shadow-rose-950/50"
            >
              <PhoneOff className="w-3.5 h-3.5" />
              {t.endSession}
            </button>
          </>
        )}
      </div>
    </div>
  );
}
