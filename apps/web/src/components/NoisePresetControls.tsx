"use client";

import React, { useState, useEffect, useRef } from "react";
import { Volume2, VolumeX, Sliders, ShieldAlert, Sparkles, Wind, CloudRain, Bike } from "lucide-react";
import { useI18n } from "../lib/i18n";

export type NoisePreset = "clean" | "motor_idle" | "rain_traffic" | "helmet";

interface NoisePresetControlsProps {
  mode: "live" | "replay";
  activePreset: NoisePreset;
  onPresetChange: (preset: NoisePreset) => void;
  noiseVolume: number;
  onVolumeChange: (vol: number) => void;
}

export function NoisePresetControls({
  mode,
  activePreset,
  onPresetChange,
  noiseVolume,
  onVolumeChange,
}: NoisePresetControlsProps) {
  const { locale } = useI18n();
  const audioContextRef = useRef<AudioContext | null>(null);
  const sourceNodeRef = useRef<AudioBufferSourceNode | null>(null);
  const gainNodeRef = useRef<GainNode | null>(null);
  const volumeRef = useRef(noiseVolume);
  volumeRef.current = noiseVolume;
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  // Play synthetic/CC0 looping noise buffer in browser when preset changes
  useEffect(() => {
    if (activePreset === "clean" || mode !== "live") {
      if (sourceNodeRef.current) {
        try {
          sourceNodeRef.current.stop();
        } catch {
          // ignore already stopped
        }
        sourceNodeRef.current = null;
      }
      setIsPlayingAudio(false);
      return;
    }

    let isMounted = true;
    const playPresetSound = async () => {
      try {
        if (!audioContextRef.current) {
          audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
        }
        const ctx = audioContextRef.current;
        if (ctx.state === "suspended") {
          await ctx.resume();
        }

        const fileName =
          activePreset === "motor_idle"
            ? "/audio/noise/motor_idle.wav"
            : activePreset === "rain_traffic"
            ? "/audio/noise/rain_traffic.wav"
            : "/audio/noise/helmet_ambient.wav";

        const res = await fetch(fileName);
        const arrayBuf = await res.arrayBuffer();
        const audioBuf = await ctx.decodeAudioData(arrayBuf);

        if (!isMounted) return;

        // Stop prior source
        if (sourceNodeRef.current) {
          try {
            sourceNodeRef.current.stop();
          } catch {}
        }

        const source = ctx.createBufferSource();
        source.buffer = audioBuf;
        source.loop = true;

        const gain = ctx.createGain();
        gain.gain.value = volumeRef.current;
        gainNodeRef.current = gain;

        if (activePreset === "helmet") {
          const filter = ctx.createBiquadFilter();
          filter.type = "lowpass";
          filter.frequency.value = 900;
          filter.Q.value = 1.5;
          source.connect(filter);
          filter.connect(gain);
        } else {
          source.connect(gain);
        }

        gain.connect(ctx.destination);
        source.start();
        sourceNodeRef.current = source;
        setIsPlayingAudio(true);
      } catch (err) {
        console.warn("[NoisePresets] Audio preview playback failed:", err);
      }
    };

    playPresetSound();

    return () => {
      isMounted = false;
      if (sourceNodeRef.current) {
        try {
          sourceNodeRef.current.stop();
        } catch {}
        sourceNodeRef.current = null;
      }
    };
  }, [activePreset, mode]);

  // Update gain when slider changes
  useEffect(() => {
    if (gainNodeRef.current) {
      gainNodeRef.current.gain.value = noiseVolume;
    }
  }, [noiseVolume]);

  const presets: Array<{
    id: NoisePreset;
    labelId: string;
    labelEn: string;
    descId: string;
    descEn: string;
    icon: React.ReactNode;
  }> = [
    {
      id: "clean",
      labelId: "Bersih",
      labelEn: "Clean",
      descId: "Input mic asli tanpa tambahan noise",
      descEn: "Pure microphone input without added noise",
      icon: <Sparkles className="w-3.5 h-3.5 text-emerald-400" />,
    },
    {
      id: "motor_idle",
      labelId: "Motor Idle",
      labelEn: "Motor Idle",
      descId: "Simulasi knalpot motor stasioner 4-tak (OpenSLR 17)",
      descEn: "Simulated 4-stroke idling engine (OpenSLR 17)",
      icon: <Bike className="w-3.5 h-3.5 text-amber-400" />,
    },
    {
      id: "rain_traffic",
      labelId: "Hujan & Lalu Lintas",
      labelEn: "Rain & Traffic",
      descId: "Simulasi hujan jalan raya dan lalu lintas (FSD50K)",
      descEn: "Simulated road rain shower & traffic wash (FSD50K)",
      icon: <CloudRain className="w-3.5 h-3.5 text-sky-400" />,
    },
    {
      id: "helmet",
      labelId: "Helm Muffled",
      labelEn: "Helmet Muffled",
      descId: "Filter akustik rongga helm tertutup (Low-pass 900Hz)",
      descEn: "Enclosed helmet acoustic filter (Low-pass 900Hz)",
      icon: <Wind className="w-3.5 h-3.5 text-indigo-400" />,
    },
  ];

  return (
    <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-3.5 space-y-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sliders className="w-4 h-4 text-emerald-400" />
          <span className="text-xs font-bold text-slate-200">
            {locale === "id" ? "Preset Kebisingan (Simulasi)" : "Noise Presets (Simulated)"}
          </span>
          <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-slate-400 font-medium">
            {mode === "live"
              ? locale === "id"
                ? "Aktif di Mode Langsung"
                : "Active in Live Mode"
              : locale === "id"
              ? "Nonaktif (Mode Replay)"
              : "Inactive (Replay Mode)"}
          </span>
        </div>
      </div>

      {/* Preset Select Buttons */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
        {presets.map((p) => {
          const isSelected = activePreset === p.id;
          return (
            <button
              key={p.id}
              type="button"
              onClick={() => onPresetChange(p.id)}
              className={`p-2 rounded-xl text-left border transition flex flex-col gap-1 ${
                isSelected
                  ? "bg-slate-800 border-emerald-500/80 shadow-sm shadow-emerald-950"
                  : "bg-slate-950/60 border-slate-800/80 hover:bg-slate-800/50 text-slate-400"
              }`}
            >
              <div className="flex items-center gap-1.5 font-semibold text-xs text-slate-200">
                {p.icon}
                <span>{locale === "id" ? p.labelId : p.labelEn}</span>
              </div>
              <p className="text-[10px] text-slate-400 leading-tight">
                {locale === "id" ? p.descId : p.descEn}
              </p>
            </button>
          );
        })}
      </div>

      {/* Volume / Intensity Slider */}
      {activePreset !== "clean" && (
        <div className="flex items-center gap-3 pt-1 border-t border-slate-800/80">
          <Volume2 className="w-3.5 h-3.5 text-slate-400 shrink-0" />
          <label htmlFor="noise-volume-slider" className="text-[11px] text-slate-400 shrink-0">
            {locale === "id" ? "Intensitas Noise:" : "Noise Level:"} {Math.round(noiseVolume * 100)}%
          </label>
          <input
            id="noise-volume-slider"
            type="range"
            min="0"
            max="1"
            step="0.05"
            value={noiseVolume}
            onChange={(e) => onVolumeChange(parseFloat(e.target.value))}
            className="w-full accent-emerald-500 h-1.5 bg-slate-800 rounded-lg cursor-pointer"
          />
        </div>
      )}

      {/* Transparency Note */}
      <p className="text-[10px] text-slate-400 leading-normal">
        {locale === "id"
          ? "Catatan: Preset kebisingan disimulasikan di browser via Web Audio API. Hanya aktif pada mode langsung dan tidak mempengaruhi data rekaman mode replay."
          : "Note: Noise presets are simulated in-browser via Web Audio API. Active only during live microphone mode, not in replay mode."}
      </p>
    </div>
  );
}
