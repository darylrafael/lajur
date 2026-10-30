"use client";

import React from "react";
import { Volume2, VolumeX, Bot, Sparkles } from "lucide-react";
import { useI18n } from "../lib/i18n";

interface BotReplyCardProps {
  botReply: string;
  isSpeaking: boolean;
}

export function BotReplyCard({ botReply, isSpeaking }: BotReplyCardProps) {
  const { t } = useI18n();

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 md:p-5 shadow-lg flex flex-col justify-between">
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
        <div className="flex items-center gap-2">
          <Bot className="w-4 h-4 text-emerald-400" />
          <h2 className="text-sm font-semibold text-white">{t.botReplyTitle}</h2>
        </div>
        <div>
          {isSpeaking ? (
            <span className="flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 animate-pulse">
              <Volume2 className="w-3.5 h-3.5 text-emerald-400 animate-bounce motion-reduce:animate-none" />
              {t.statusSpeaking}
            </span>
          ) : (
            <span className="flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] text-slate-500 bg-slate-950 border border-slate-800">
              <VolumeX className="w-3 h-3 text-slate-600" />
              Standby
            </span>
          )}
        </div>
      </div>

      <div className="min-h-[64px] flex items-center p-3 rounded-xl bg-slate-950/60 border border-slate-800/80">
        {botReply ? (
          <p className="text-sm text-emerald-100 font-medium leading-relaxed flex items-start gap-2">
            <Sparkles className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
            <span>&ldquo;{botReply}&rdquo;</span>
          </p>
        ) : (
          <p className="text-xs text-slate-500 italic">{t.botWaiting}</p>
        )}
      </div>
    </div>
  );
}
