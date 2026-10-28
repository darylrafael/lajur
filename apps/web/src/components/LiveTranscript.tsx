"use client";

import React, { useRef, useEffect } from "react";
import { MessageSquare, Mic, Sparkles, User, Bot } from "lucide-react";
import { useI18n } from "../lib/i18n";
import { TranscriptEntry } from "../hooks/useSimulator";

interface LiveTranscriptProps {
  partialTranscript: string;
  finalTranscript: string;
  transcriptHistory: TranscriptEntry[];
  isListening: boolean;
}

export function LiveTranscript({
  partialTranscript,
  finalTranscript,
  transcriptHistory,
  isListening,
}: LiveTranscriptProps) {
  const { t } = useI18n();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [partialTranscript, finalTranscript, transcriptHistory]);

  return (
    <section
      aria-labelledby="live-transcript-heading"
      className="bg-slate-900 border border-slate-800 rounded-2xl p-4 md:p-5 flex flex-col h-full shadow-lg"
    >
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-emerald-400" />
          <h2 id="live-transcript-heading" className="text-sm font-semibold text-white">
            {t.liveTranscriptTitle}
          </h2>
        </div>
        {isListening && (
          <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-emerald-950/80 text-emerald-400 border border-emerald-800/80">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping" />
            {t.listeningIndicator}
          </span>
        )}
      </div>

      {/* Transcript Scroll Area with ARIA live region */}
      <div
        ref={scrollRef}
        role="log"
        tabIndex={0}
        aria-live="polite"
        aria-relevant="additions text"
        aria-atomic="false"
        className="flex-1 overflow-y-auto space-y-3 pr-1 min-h-[140px] max-h-[300px] md:max-h-[380px] text-xs font-mono focus:outline-none focus:ring-1 focus:ring-emerald-500/50 rounded-xl"
      >
        {transcriptHistory.length === 0 && !partialTranscript && (
          <div className="h-full flex flex-col items-center justify-center text-center p-6 text-slate-500">
            <Mic className="w-8 h-8 mb-2 stroke-1 text-slate-600" />
            <p className="max-w-xs">{t.emptyTranscript}</p>
          </div>
        )}

        {/* History of exchanges */}
        {transcriptHistory.map((item) => (
          <div
            key={item.id}
            className={`flex items-start gap-2.5 p-2.5 rounded-xl border ${
              item.speaker === "user"
                ? "bg-slate-950/80 border-slate-800 ml-3"
                : "bg-emerald-950/30 border-emerald-900/40 text-emerald-200 mr-3"
            }`}
          >
            <div
              className={`w-6 h-6 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
                item.speaker === "user"
                  ? "bg-slate-800 text-slate-300"
                  : "bg-emerald-800/60 text-emerald-300"
              }`}
            >
              {item.speaker === "user" ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
            </div>
            <div className="flex-1">
              <span className="text-[10px] uppercase tracking-wider font-semibold block mb-0.5 opacity-60">
                {item.speaker === "user" ? "Pelanggan / Customer" : "Lajur Bot"}
              </span>
              <p className="text-slate-200 leading-relaxed font-sans">{item.text}</p>
            </div>
          </div>
        ))}

        {/* Live Partial Transcript (Streaming while user speaks) */}
        {partialTranscript && (
          <div className="flex items-start gap-2.5 p-2.5 rounded-xl bg-sky-950/40 border border-sky-800/60 text-sky-200 ml-3 animate-pulse">
            <div className="w-6 h-6 rounded-full bg-sky-800/60 text-sky-300 flex items-center justify-center shrink-0 mt-0.5">
              <Sparkles className="w-3.5 h-3.5" />
            </div>
            <div className="flex-1 font-sans">
              <span className="text-[10px] uppercase tracking-wider font-semibold text-sky-400 block mb-0.5 flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-sky-400 animate-ping" />
                Live Partial Input
              </span>
              <p className="text-sky-100 italic font-medium leading-relaxed">
                &ldquo;{partialTranscript}&rdquo;
              </p>
            </div>
          </div>
        )}
      </div>

      <div className="pt-2 mt-2 border-t border-slate-800/60 text-[11px] text-slate-500">
        {t.liveTranscriptHint}
      </div>
    </section>
  );
}
