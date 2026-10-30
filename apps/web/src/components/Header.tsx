"use client";

import React from "react";
import { Radio, Globe, PlayCircle, Mic } from "lucide-react";
import { useI18n } from "../lib/i18n";
import { SimulatorMode } from "../hooks/useSimulator";

interface HeaderProps {
  mode: SimulatorMode;
  onModeChange: (mode: SimulatorMode) => void;
}

export function Header({ mode, onModeChange }: HeaderProps) {
  const { t, locale, setLocale } = useI18n();

  return (
    <header className="max-w-7xl w-full mx-auto pb-4 border-b border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-4">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 shrink-0">
          <Radio className="w-5 h-5 animate-pulse" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl md:text-2xl font-bold tracking-tight text-white">
              {t.appTitle}
            </h1>
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-950/80 text-emerald-400 border border-emerald-800">
              {t.previewBadge}
            </span>
          </div>
          <p className="text-xs text-slate-400">{t.appSubtitle}</p>
        </div>
      </div>

      <div className="flex items-center gap-3 self-end md:self-auto flex-wrap">
        {/* Mode Selector */}
        <div
          role="radiogroup"
          aria-label="Simulator Mode"
          className="flex items-center p-1 bg-slate-900 border border-slate-800 rounded-xl"
        >
          <button
            type="button"
            role="radio"
            aria-checked={mode === "replay"}
            onClick={() => onModeChange("replay")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition ${
              mode === "replay"
                ? "bg-amber-600 text-white shadow-sm font-semibold"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <PlayCircle className="w-3.5 h-3.5" />
            {t.modeReplay}
          </button>
          <button
            type="button"
            role="radio"
            aria-checked={mode === "live"}
            onClick={() => onModeChange("live")}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium flex items-center gap-1.5 transition ${
              mode === "live"
                ? "bg-emerald-600 text-white shadow-sm font-semibold"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            <Mic className="w-3.5 h-3.5" />
            {t.modeLive}
          </button>
        </div>

        {/* Language Toggle */}
        <div
          role="group"
          aria-label="Language selection"
          className="flex items-center p-1 bg-slate-900 border border-slate-800 rounded-xl"
        >
          <Globe className="w-3.5 h-3.5 text-slate-400 ml-1.5 mr-1" />
          <button
            type="button"
            onClick={() => setLocale("id")}
            aria-pressed={locale === "id"}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition ${
              locale === "id"
                ? "bg-slate-800 text-white font-semibold"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            ID
          </button>
          <button
            type="button"
            onClick={() => setLocale("en")}
            aria-pressed={locale === "en"}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition ${
              locale === "en"
                ? "bg-slate-800 text-white font-semibold"
                : "text-slate-400 hover:text-slate-200"
            }`}
          >
            EN
          </button>
        </div>
      </div>
    </header>
  );
}
