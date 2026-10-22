# Draft Intent Schema (Spike 03 — LLM Intent Parsing)

**Document:** `docs/spikes/intent-schema-draft.md`  
**Status:** DRAFT (Spike 03 Exploration)  
**Final Schema Milestone:** Minggu 3 (Cart State Machine Integration)  
**Author:** Lajur Engineering  
**Version:** 0.1-draft

---

## 1. Overview and Intent Design

In accordance with [ADR-0002](file:///c:/Users/Lenovo/Downloads/drivethru/docs/decisions/0002-deterministic-cart-state-machine.md), the LLM **never** mutates the cart directly and **never** invents prices or items. Instead, the LLM parses the customer's conversational turn into a structured, validated JSON intent stream. The deterministic `CartStateMachine` is the sole authority executing state transitions and enforcing menu constraints.

This draft defines the initial intent types evaluated during **Spike 03** (comparing Gemini Flash/Flash-Lite vs GPT-4o-mini).

---

## 2. Intent Specifications

Every intent payload produced by the LLM conforms to an envelope schema:

```json
{
  "intents": [
    {
      "type": "<intent_type>",
      "params": { ... }
    }
  ],
  "bot_reply": "<short conversational response in Indonesian>"
}
```

### 2.1 `add_item`
Adds one or more units of a menu item or combo to the order.

```json
{
  "type": "add_item",
  "params": {
    "item_id": "burger_sapi_keju",
    "quantity": 2,
    "size": "size_regular",
    "modifiers": [
      {
        "modifier_id": "mod_burger_custom",
        "option_id": "opt_no_onion"
      }
    ],
    "combo_choices": []
  }
}
```

### 2.2 `remove_item`
Removes an existing item or decrements its quantity.

```json
{
  "type": "remove_item",
  "params": {
    "item_id": "kentang_goreng",
    "quantity": 1
  }
}
```

### 2.3 `modify_item`
Applies modifiers, size changes, or customizations to an existing cart line.

```json
{
  "type": "modify_item",
  "params": {
    "target_item_id": "es_teh_manis",
    "size": "size_large",
    "add_modifiers": [
      {
        "modifier_id": "mod_ice",
        "option_id": "ice_less"
      }
    ],
    "remove_modifiers": []
  }
}
```

### 2.4 `undo`
Reverts the last action performed in the conversation (e.g. customer changed their mind).

```json
{
  "type": "undo",
  "params": {
    "steps": 1
  }
}
```

### 2.5 `confirm`
Explicit customer confirmation that the order is complete (e.g. *"itu aja mas"*, *"sudah cukup"*).

```json
{
  "type": "confirm",
  "params": {
    "payment_method": null
  }
}
```

### 2.6 `handoff`
Triggers immediate transfer to a human drive-thru crew member (e.g. customer requests a manager, system fails repeatedly, or severe acoustic distortion).

```json
{
  "type": "handoff",
  "params": {
    "reason": "customer_requested"
  }
}
```

### 2.7 `ask_info`
Queries regarding menu items, prices, operating hours (breakfast vs regular), or ingredient questions.

```json
{
  "type": "ask_info",
  "params": {
    "query_type": "operating_hours",
    "target_item_id": "bubur_ayam"
  }
}
```

### 2.8 `unknown`
Fallback intent when the user utterance cannot be resolved to any ordering action (e.g. background chit-chat, nonsense, or non-ordering banter).

```json
{
  "type": "unknown",
  "params": {
    "raw_text": "eh motor kamu keren juga ya",
    "reason": "off_topic"
  }
}
```

---

## 3. Minggu 3 Integration Notes
During Minggu 3, this schema will be codified into formal Pydantic models in `packages/cart` and connected directly to state transitions in `CartStateMachine`.
