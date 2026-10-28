"use client";

import React from "react";
import { Play, Pause, RotateCcw, AlertTriangle, Sparkles, CheckCircle } from "lucide-react";
import { useI18n } from "../lib/i18n";
import replaysData from "../data/replays.json";

interface ReplayControllerProps {
  selectedScenario: string;
  isReplaying: boolean;
  onSelectScenario: (scenarioId: string) => void;
  onPlay: () => void;
  onPause: () => void;
  onRestart: () => void;
}

export function ReplayController({
  selectedScenario,
  isReplaying,
  onSelectScenario,
  onPlay,
  onPause,
  onRestart,
}: ReplayControllerProps) {
  const { t, locale } = useI18n();

  const scenarios = Object.entries(replaysData).map(([id, sc]: [string, any]) => ({
    id,
    title: locale === "en" ? sc.title_en : sc.title_id,
    turnsCount: sc.turns_count,
  }));

  return (
    <div
      role="region"
      aria-labelledby="replay-mode-heading"
      className="bg-amber-950/30 border border-amber-800/60 rounded-2xl p-4 md:p-5 shadow-lg space-y-4"
    >
      {/* Replay Banner Warning */}
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded-xl bg-amber-500/20 text-amber-400 border border-amber-500/30 flex items-center justify-center shrink-0 mt-0.5">
          <AlertTriangle className="w-4 h-4" />
        </div>
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-0.5">
            <h2 id="replay-mode-heading" className="text-sm font-bold text-amber-300">
              {t.replayBannerTitle}
            </h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-900/60 text-amber-200 border border-amber-700/60">
              100% Offline
            </span>
          </div>
          <p className="text-xs text-amber-200/80 leading-relaxed">
            {t.replayBannerDesc}
          </p>
        </div>
      </div>

      {/* Scenario Selection & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pt-2 border-t border-amber-900/40">
        <div className="flex-1 min-w-[240px]">
          <label htmlFor="scenario-select" className="block text-[11px] font-semibold text-amber-200 mb-1.5">
            {t.selectScenario}
          </label>
          <select
            id="scenario-select"
            value={selectedScenario}
            onChange={(e) => onSelectScenario(e.target.value)}
            disabled={isReplaying}
            className="w-full bg-slate-900 border border-amber-800/80 rounded-xl px-3 py-2 text-xs text-amber-100 font-medium focus:outline-none focus:ring-2 focus:ring-amber-500 disabled:opacity-60"
          >
            {scenarios.map((sc) => (
              <option key={sc.id} value={sc.id}>
                {sc.title} ({sc.turnsCount} turns)
              </option>
            ))}
          </select>
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-2 self-end sm:self-end pt-1">
          {!isReplaying ? (
            <button
              type="button"
              onClick={onPlay}
              className="px-5 py-2.5 rounded-xl text-xs font-bold bg-amber-600 hover:bg-amber-500 text-white shadow-md shadow-amber-950/40 transition flex items-center gap-1.5"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              {t.playReplay}
            </button>
          ) : (
            <button
              type="button"
              onClick={onPause}
              className="px-5 py-2.5 rounded-xl text-xs font-bold bg-amber-700 hover:bg-amber-600 text-white shadow-md shadow-amber-950/40 transition flex items-center gap-1.5"
            >
              <Pause className="w-3.5 h-3.5 fill-current" />
              {t.pauseReplay}
            </button>
          )}

          <button
            type="button"
            onClick={onRestart}
            className="p-2.5 rounded-xl text-xs font-semibold bg-slate-900 hover:bg-slate-800 text-amber-300 border border-amber-800/80 transition"
            title={t.restartReplay}
            aria-label={t.restartReplay}
          >
            <RotateCcw className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
