"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import {
  WebProtocolEvent,
  CartSnapshot,
  DialogState,
  PendingQuestionEvent,
  HandoffEvent,
} from "../types/protocol";
import replaysData from "../data/replays.json";

export type SimulatorMode = "live" | "replay";

export type SimulatorStatus =
  | "idle"
  | "connecting"
  | "listening"
  | "thinking"
  | "speaking"
  | "awaiting_choice"
  | "handoff"
  | "error";

export interface TranscriptEntry {
  id: string;
  speaker: "user" | "bot";
  text: string;
  timestampMs?: number;
}

const emptyCart: CartSnapshot = {
  items: [],
  total_price: 0,
  total_item_count: 0,
  status: "empty",
};

export function useSimulator(initialMode: SimulatorMode = "live", defaultScenarioId = "simple") {
  const [mode, setMode] = useState<SimulatorMode>(initialMode);
  const [status, setStatus] = useState<SimulatorStatus>("idle");
  const [dialogState, setDialogState] = useState<DialogState>("ordering");
  const [cart, setCart] = useState<CartSnapshot>(emptyCart);
  const [partialTranscript, setPartialTranscript] = useState<string>("");
  const [finalTranscript, setFinalTranscript] = useState<string>("");
  const [transcriptHistory, setTranscriptHistory] = useState<TranscriptEntry[]>([]);
  const [botReply, setBotReply] = useState<string>("");
  const [pendingQuestion, setPendingQuestion] = useState<PendingQuestionEvent | null>(null);
  const [handoffData, setHandoffData] = useState<HandoffEvent | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [cartUpdatedCue, setCartUpdatedCue] = useState<boolean>(false);
  const [sessionLimits, setSessionLimits] = useState({
    turns_used: 0,
    max_turns: 12,
    time_elapsed_seconds: 0,
    time_limit_seconds: 180,
  });

  // Replay specific states
  const [selectedScenario, setSelectedScenario] = useState<string>(defaultScenarioId);
  const [isReplaying, setIsReplaying] = useState<boolean>(false);
  const replayTimersRef = useRef<NodeJS.Timeout[]>([]);
  const cartCueTimerRef = useRef<NodeJS.Timeout | null>(null);

  const resetState = useCallback(() => {
    setStatus("idle");
    setDialogState("ordering");
    setCart(emptyCart);
    setPartialTranscript("");
    setFinalTranscript("");
    setTranscriptHistory([]);
    setBotReply("");
    setPendingQuestion(null);
    setHandoffData(null);
    setErrorMessage(null);
    setCartUpdatedCue(false);
    setSessionLimits({
      turns_used: 0,
      max_turns: 12,
      time_elapsed_seconds: 0,
      time_limit_seconds: 180,
    });
  }, []);

  // Ingest any Web Protocol v1 Event
  const processEvent = useCallback((event: WebProtocolEvent) => {
    switch (event.type) {
      case "partial_transcript": {
        setPartialTranscript(event.text);
        setStatus("listening");
        break;
      }

      case "final_transcript": {
        setFinalTranscript(event.text);
        setPartialTranscript("");
        setStatus("thinking");
        setTranscriptHistory((prev) => [
          ...prev,
          {
            id: `usr_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
            speaker: "user",
            text: event.text,
            timestampMs: event.timestamp_ms,
          },
        ]);
        break;
      }

      case "intent_applied": {
        setCart(event.cart);
        setDialogState(event.state);

        // Flash cart updated cue
        setCartUpdatedCue(true);
        if (cartCueTimerRef.current) clearTimeout(cartCueTimerRef.current);
        cartCueTimerRef.current = setTimeout(() => {
          setCartUpdatedCue(false);
        }, 1800);

        if (event.state === "awaiting_choice") {
          setStatus("awaiting_choice");
        } else if (event.state === "handoff") {
          setStatus("handoff");
        } else {
          setPendingQuestion(null);
        }
        break;
      }

      case "pending_question": {
        setPendingQuestion(event);
        setStatus("awaiting_choice");
        break;
      }

      case "handoff": {
        setHandoffData(event);
        setStatus("handoff");
        break;
      }

      case "bot_reply_text": {
        setBotReply(event.text);
        setTranscriptHistory((prev) => [
          ...prev,
          {
            id: `bot_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
            speaker: "bot",
            text: event.text,
            timestampMs: event.timestamp_ms,
          },
        ]);
        break;
      }

      case "bot_speaking_start": {
        setStatus("speaking");
        break;
      }

      case "bot_speaking_end": {
        setStatus((current) => {
          if (dialogState === "awaiting_choice" || current === "awaiting_choice") {
            return "awaiting_choice";
          }
          if (dialogState === "handoff" || current === "handoff") {
            return "handoff";
          }
          return "listening";
        });
        break;
      }

      case "session_limits": {
        setSessionLimits({
          turns_used: event.turns_used,
          max_turns: event.max_turns,
          time_elapsed_seconds: event.time_elapsed_seconds,
          time_limit_seconds: event.time_limit_seconds,
        });
        break;
      }

      case "error": {
        setErrorMessage(event.message);
        setStatus("error");
        break;
      }
    }
  }, [dialogState]);

  // Clean up timers
  const clearReplayTimers = useCallback(() => {
    replayTimersRef.current.forEach((t) => clearTimeout(t));
    replayTimersRef.current = [];
    setIsReplaying(false);
  }, []);

  useEffect(() => {
    return () => {
      clearReplayTimers();
      if (cartCueTimerRef.current) clearTimeout(cartCueTimerRef.current);
    };
  }, [clearReplayTimers]);

  // Start replay playback for a chosen scenario
  const startReplay = useCallback(
    (scenarioId?: string) => {
      clearReplayTimers();
      resetState();

      const scId = scenarioId || selectedScenario;
      if (scenarioId) setSelectedScenario(scenarioId);

      const scenario = (replaysData as Record<string, any>)[scId];
      if (!scenario || !Array.isArray(scenario.events)) {
        setErrorMessage(`Scenario fixture '${scId}' not found.`);
        return;
      }

      setIsReplaying(true);
      setStatus("connecting");

      let cumulativeDelay = 0;
      scenario.events.forEach((item: { delay_ms: number; event: WebProtocolEvent }, idx: number) => {
        cumulativeDelay += item.delay_ms;
        const timer = setTimeout(() => {
          processEvent(item.event);
          if (idx === scenario.events.length - 1) {
            setIsReplaying(false);
          }
        }, cumulativeDelay);
        replayTimersRef.current.push(timer);
      });
    },
    [clearReplayTimers, resetState, selectedScenario, processEvent]
  );

  const pauseReplay = useCallback(() => {
    clearReplayTimers();
  }, [clearReplayTimers]);

  const restartReplay = useCallback(() => {
    startReplay(selectedScenario);
  }, [startReplay, selectedScenario]);

  return {
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
    // Replay controls
    selectedScenario,
    setSelectedScenario,
    isReplaying,
    startReplay,
    pauseReplay,
    restartReplay,
  };
}
