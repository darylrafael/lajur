/**
 * Shared TypeScript definitions for Lajur Web Protocol v1.
 * WebRTC Data Channel contract between Agent Worker and Next.js Web Simulator.
 */

export type ProtocolVersion = "v1";

export type DialogState = "ordering" | "awaiting_choice" | "confirming" | "done" | "handoff";

export type CartStatus = "in_progress" | "confirmed" | "rejected" | "empty" | "handoff";

export type ItemSize = "regular" | "medium" | "large";

export interface CartLineSnapshot {
  line_id: string;
  item_id: string;
  name_id?: string;
  name_en?: string;
  quantity: number;
  size: ItemSize;
  unit_price?: number;
  price: number; // total line price in IDR
  modifiers: string[];
  slots: Record<string, string>;
  upsell_rules?: string[];
}

export interface CartSnapshot {
  items: CartLineSnapshot[];
  total_price: number;
  total_item_count: number;
  status: CartStatus;
}

export interface RejectionInfo {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface SpeechFactsSnapshot {
  intent_handled: string;
  items_added: Array<Record<string, unknown>>;
  items_removed: Array<Record<string, unknown>>;
  items_modified: Array<Record<string, unknown>>;
  items_replaced: Array<Record<string, unknown>>;
  rejections: RejectionInfo[];
  cart_item_count: number;
  cart_total_price: number;
  dialog_state: DialogState;
  requires_confirmation: boolean;
}

export interface BaseProtocolEvent {
  version: ProtocolVersion;
  timestamp_ms?: number;
}

export interface PartialTranscriptEvent extends BaseProtocolEvent {
  type: "partial_transcript";
  text: string;
  is_final: false;
}

export interface FinalTranscriptEvent extends BaseProtocolEvent {
  type: "final_transcript";
  text: string;
  is_final: true;
}

export interface IntentAppliedEvent extends BaseProtocolEvent {
  type: "intent_applied";
  state: DialogState;
  state_from?: DialogState;
  cart: CartSnapshot;
  speech_facts: SpeechFactsSnapshot;
}

export interface BotReplyTextEvent extends BaseProtocolEvent {
  type: "bot_reply_text";
  text: string;
}

export interface BotSpeakingStartEvent extends BaseProtocolEvent {
  type: "bot_speaking_start";
}

export interface BotSpeakingEndEvent extends BaseProtocolEvent {
  type: "bot_speaking_end";
}

export interface PendingQuestionChoice {
  id: string;
  name_id: string;
  name_en: string;
  price_delta?: number;
}

export interface PendingQuestionEvent extends BaseProtocolEvent {
  type: "pending_question";
  kind: "combo_slot" | "required_modifier" | "ambiguity";
  prompt: string;
  target_line_id?: string | null;
  slot_id?: string | null;
  allowed_choices: string[];
  choices?: PendingQuestionChoice[];
}

export interface HandoffEvent extends BaseProtocolEvent {
  type: "handoff";
  reason: string;
  crew_message: string;
}

export interface ErrorEvent extends BaseProtocolEvent {
  type: "error";
  code: string;
  message: string;
  recoverable: boolean;
}

export interface SessionLimitsEvent extends BaseProtocolEvent {
  type: "session_limits";
  turns_used: number;
  max_turns: number;
  time_elapsed_seconds: number;
  time_limit_seconds: number;
}

/**
 * Union of all downstream events published by the Agent Worker over data channel.
 */
export type WebProtocolEvent =
  | PartialTranscriptEvent
  | FinalTranscriptEvent
  | IntentAppliedEvent
  | BotReplyTextEvent
  | BotSpeakingStartEvent
  | BotSpeakingEndEvent
  | PendingQuestionEvent
  | HandoffEvent
  | ErrorEvent
  | SessionLimitsEvent;

/**
 * Upstream messages sent from Web Client to Agent Worker over data channel.
 */
export interface PingMessage {
  type: "ping";
  client_time: number;
}

export interface PongMessage {
  type: "pong";
  client_time: number;
}

export interface UserTranscriptMessage {
  type: "user_transcript";
  text: string;
}

export interface ResetSessionMessage {
  type: "reset_session";
}

export type ClientProtocolMessage =
  | PingMessage
  | PongMessage
  | UserTranscriptMessage
  | ResetSessionMessage;
