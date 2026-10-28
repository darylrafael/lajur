"use client";

import React from "react";
import { Users, AlertCircle } from "lucide-react";
import { useI18n } from "../lib/i18n";
import { HandoffEvent } from "../types/protocol";

interface HandoffBannerProps {
  handoffData: HandoffEvent | null;
}

export function HandoffBanner({ handoffData }: HandoffBannerProps) {
  const { t } = useI18n();

  if (!handoffData) return null;

  return (
    <div
      role="alert"
      className="bg-rose-950/60 border-2 border-rose-600 rounded-2xl p-4 md:p-5 shadow-2xl animate-pulse motion-reduce:animate-none flex items-start gap-4"
    >
      <div className="w-10 h-10 rounded-xl bg-rose-600/30 text-rose-300 border border-rose-500 flex items-center justify-center shrink-0 mt-0.5">
        <Users className="w-5 h-5" />
      </div>
      <div className="flex-1">
        <div className="flex items-center gap-2 mb-1">
          <h3 className="text-sm font-bold text-rose-200">
            {t.handoffTitle}
          </h3>
          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-rose-900 text-rose-200 uppercase">
            Handoff Active
          </span>
        </div>
        <p className="text-xs md:text-sm text-rose-100 font-medium leading-relaxed">
          {handoffData.crew_message || t.crewSimulatedMsg}
        </p>
      </div>
    </div>
  );
}
