"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from "react";

export type Locale = "id" | "en";

export interface Translations {
  appTitle: string;
  appSubtitle: string;
  previewBadge: string;
  modeLive: string;
  modeReplay: string;
  tabMenu: string;
  tabTranscript: string;
  tabCart: string;
  startSession: string;
  connecting: string;
  endSession: string;
  startOver: string;
  muteMic: string;
  unmuteMic: string;
  allowAudio: string;
  statusIdle: string;
  statusConnecting: string;
  statusListening: string;
  statusThinking: string;
  statusSpeaking: string;
  statusAwaitingChoice: string;
  statusHandoff: string;
  statusError: string;
  liveTranscriptTitle: string;
  liveTranscriptHint: string;
  listeningIndicator: string;
  emptyTranscript: string;
  cartTitle: string;
  cartEmpty: string;
  cartUpdatedCue: string;
  unitPrice: string;
  subtotal: string;
  tax: string;
  total: string;
  itemsCount: string;
  pendingChoiceTitle: string;
  chooseOption: string;
  botReplyTitle: string;
  botWaiting: string;
  sessionLimitsTitle: string;
  turnsUsed: string;
  timeLeft: string;
  handoffTitle: string;
  crewSimulatedMsg: string;
  menuTitle: string;
  menuSubtitle: string;
  outOfStock: string;
  outsideHours: string;
  breakfastOnly: string;
  regularOnly: string;
  allDay: string;
  replayBannerTitle: string;
  replayBannerDesc: string;
  selectScenario: string;
  playReplay: string;
  pauseReplay: string;
  restartReplay: string;
  liveNoticeTitle: string;
  liveNoticeDesc: string;
  permissionDenied: string;
  unsupportedBrowser: string;
  footerNote: string;
  liveModeDisabledNotice: string;
}

const idTranslations: Translations = {
  appTitle: "Lajur Voice Ordering",
  appSubtitle: "Simulator Web Drive-thru Cerdas (Real-Time WebRTC & Offline Replay)",
  previewBadge: "Minggu 5 — Simulator Web",
  modeLive: "Mode Live Suara",
  modeReplay: "Mode Demo Replay (Offline)",
  tabMenu: "Papan Menu",
  tabTranscript: "Transkrip Suara",
  tabCart: "Layar Pesanan",
  startSession: "Mulai Sesi Suara",
  connecting: "Menghubungkan...",
  endSession: "Akhiri Sesi",
  startOver: "Ulangi Pesanan",
  muteMic: "Bisukan Mic",
  unmuteMic: "Nyalakan Mic",
  allowAudio: "Klik untuk mengaktifkan audio speaker",
  statusIdle: "Siap Dipesan",
  statusConnecting: "Menghubungkan Server...",
  statusListening: "Mendengarkan Anda...",
  statusThinking: "Memproses Pesanan...",
  statusSpeaking: "Bot Sedang Berbicara...",
  statusAwaitingChoice: "Menunggu Pilihan Anda...",
  statusHandoff: "Eskalasi ke Kru Kasir",
  statusError: "Terjadi Kendala",
  liveTranscriptTitle: "Transkrip Suara Langsung (NFR-07)",
  liveTranscriptHint: "Transkrip teks muncul seketika saat Anda berbicara.",
  listeningIndicator: "Sedang mendengarkan ucapan...",
  emptyTranscript: "Belum ada suara. Mulai berbicara setelah menekan Mulai Sesi.",
  cartTitle: "Ringkasan Keranjang Pesanan",
  cartEmpty: "Keranjang masih kosong. Silakan sebutkan pesanan Anda.",
  cartUpdatedCue: "Keranjang Diperbarui",
  unitPrice: "Harga Satuan",
  subtotal: "Subtotal",
  tax: "Pajak (PB1 10%)",
  total: "Total Pembayaran",
  itemsCount: "item",
  pendingChoiceTitle: "Pilihan Wajib yang Perlu Ditentukan:",
  chooseOption: "Pilih",
  botReplyTitle: "Balasan Suara Asisten",
  botWaiting: "Menunggu pesanan dari Anda...",
  sessionLimitsTitle: "Batas Sesi Pemesanan",
  turnsUsed: "Giliran Percakapan",
  timeLeft: "Sisa Waktu Sesi",
  handoffTitle: "Eskalasi Staf Kasir Drive-thru",
  crewSimulatedMsg: "Mohon tunggu sebentar ya kak, kasir manusia kami di konter akan segera melayani Anda.",
  menuTitle: "Papan Menu Drive-thru",
  menuSubtitle: "Daftar menu resmi, harga, dan ketersediaan stok secara real-time.",
  outOfStock: "Stok Habis (86'd)",
  outsideHours: "Di Luar Jam Operasional",
  breakfastOnly: "Khusus Sarapan (05:00 - 11:00)",
  regularOnly: "Menu Reguler (11:00 - 05:00)",
  allDay: "Sepanjang Hari",
  replayBannerTitle: "DEMO REPLAY (Rekaman Peristiwa Offline)",
  replayBannerDesc: "Memutar ulang rekaman peristiwa data-channel otentik tanpa koneksi LiveKit atau panggilan API vendor.",
  selectScenario: "Pilih Skenario Replay:",
  playReplay: "Putar Replay",
  pauseReplay: "Jeda",
  restartReplay: "Mulai Ulang",
  liveNoticeTitle: "Pemberitahuan Mode Live Publik",
  liveNoticeDesc: "Endpoint token LiveKit belum dilengkapi captcha dan rate limit (dijadwalkan Minggu 9). Mode Replay direkomendasikan untuk uji coba publik.",
  permissionDenied: "Izin akses mikrofon ditolak oleh browser. Mohon izinkan mikrofon untuk menggunakan fitur suara.",
  unsupportedBrowser: "Browser Anda tidak mendukung WebRTC atau perekaman audio. Gunakan Chrome atau Safari versi terbaru.",
  liveModeDisabledNotice: "Suara langsung dinonaktifkan; silakan coba demo replay",
  footerNote: "Lajur Portfolio Project · Arsitektur Cascade Streaming Pipeline · Zero Audio Persistence (ADR-0005)",
};

const enTranslations: Translations = {
  appTitle: "Lajur Voice Ordering",
  appSubtitle: "Intelligent Drive-thru Web Simulator (Real-Time WebRTC & Offline Replay)",
  previewBadge: "Week 5 — Web Simulator",
  modeLive: "Live Voice Mode",
  modeReplay: "Demo Replay Mode (Offline)",
  tabMenu: "Menu Board",
  tabTranscript: "Voice Transcript",
  tabCart: "Order Summary",
  startSession: "Start Voice Session",
  connecting: "Connecting...",
  endSession: "End Session",
  startOver: "Start Over",
  muteMic: "Mute Mic",
  unmuteMic: "Unmute Mic",
  allowAudio: "Click to enable speaker audio",
  statusIdle: "Ready to Order",
  statusConnecting: "Connecting to Server...",
  statusListening: "Listening to you...",
  statusThinking: "Processing Order...",
  statusSpeaking: "Bot Speaking...",
  statusAwaitingChoice: "Awaiting Your Choice...",
  statusHandoff: "Escalated to Human Crew",
  statusError: "System Issue",
  liveTranscriptTitle: "Live Voice Transcript (NFR-07)",
  liveTranscriptHint: "Live partial transcript appears in real time while you speak.",
  listeningIndicator: "Listening to voice input...",
  emptyTranscript: "No speech recorded yet. Start speaking after clicking Start Session.",
  cartTitle: "Order Cart Summary",
  cartEmpty: "Your cart is empty. Please state what you would like to order.",
  cartUpdatedCue: "Cart Updated",
  unitPrice: "Unit Price",
  subtotal: "Subtotal",
  tax: "Tax (10%)",
  total: "Total Amount",
  itemsCount: "items",
  pendingChoiceTitle: "Required Selection Needed:",
  chooseOption: "Select",
  botReplyTitle: "Assistant Voice Reply",
  botWaiting: "Waiting for your order...",
  sessionLimitsTitle: "Session Limits",
  turnsUsed: "Turn Counter",
  timeLeft: "Time Remaining",
  handoffTitle: "Drive-thru Crew Escalation",
  crewSimulatedMsg: "Please wait a moment, our human cashier will assist you shortly at the window.",
  menuTitle: "Drive-thru Menu Board",
  menuSubtitle: "Official menu items, verified prices, and real-time stock availability.",
  outOfStock: "Out of Stock (86'd)",
  outsideHours: "Outside Operating Hours",
  breakfastOnly: "Breakfast Only (05:00 - 11:00)",
  regularOnly: "Regular Menu (11:00 - 05:00)",
  allDay: "All Day",
  replayBannerTitle: "DEMO REPLAY (Offline Recorded Events)",
  replayBannerDesc: "Replaying authentic data-channel event sequences without LiveKit connection or vendor API calls.",
  selectScenario: "Select Replay Scenario:",
  playReplay: "Play Replay",
  pauseReplay: "Pause",
  restartReplay: "Restart",
  liveNoticeTitle: "Public Live Mode Notice",
  liveNoticeDesc: "Live token route currently has no captcha or rate limiting (scheduled for Week 9). Replay Mode is recommended for public evaluation.",
  permissionDenied: "Microphone permission was denied by your browser. Please grant microphone access to use voice.",
  unsupportedBrowser: "Your browser does not support WebRTC audio. Please use the latest Chrome or Safari.",
  liveModeDisabledNotice: "Live voice is off; try the demo replay",
  footerNote: "Lajur Portfolio Project · Cascading Streaming Pipeline Architecture · Zero Audio Persistence (ADR-0005)",
};

interface I18nContextType {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  t: Translations;
}

const I18nContext = createContext<I18nContextType>({
  locale: "id",
  setLocale: () => {},
  t: idTranslations,
});

export function I18nProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("id");

  useEffect(() => {
    const saved = localStorage.getItem("lajur_locale") as Locale | null;
    if (saved === "id" || saved === "en") {
      setLocaleState(saved);
    }
  }, []);

  const setLocale = (newLocale: Locale) => {
    setLocaleState(newLocale);
    try {
      localStorage.setItem("lajur_locale", newLocale);
    } catch {
      // Local storage disabled or unavailable
    }
  };

  const t = locale === "id" ? idTranslations : enTranslations;

  return (
    <I18nContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </I18nContext.Provider>
  );
}

export function useI18n() {
  return useContext(I18nContext);
}
