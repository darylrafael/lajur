# Week 2 Human Action Checklist: Preparing for Spike Benchmarks

**Document:** `docs/spikes/week-02-human-checklist.md`  
**Phase:** Minggu 2a Completion &rarr; Minggu 2b Handoff  
**Time Commitment:** ~1 to 1.5 hours of human developer time  
**Budget Recommendation:** `SPIKE_BUDGET_USD=8.00` *(Dry-run estimate: $1.2120 across all 10 candidates; $8.00 gives a 6.6x safety buffer)*

---

## 1. High-Priority Action Items (Blocking vs Non-Blocking)

| Priority | Task | Blocking? | Estimated Time | Tool / Location |
|:---:|---|:---:|:---:|---|
| **P0** | **Record 40 Voice Utterances (Condition: `quiet`)** | **BLOCKING** | 25 mins | Microphone &rarr; `eval/audio/real/` |
| **P0** | **Run Audio Validation Script (`check_recordings.py`)** | **BLOCKING** | 2 mins | Terminal command |
| **P1** | **Obtain API Keys for Primary STT Candidates (Deepgram & Soniox)** | **BLOCKING** | 15 mins | Vendor web dashboards &rarr; `.env` |
| **P1** | **Obtain API Key for LLM Candidate (Gemini or OpenAI)** | **BLOCKING** | 5 mins | Google AI Studio / OpenAI |
| **P1** | **Spot-Check 20 Seeded Gold Intent Labels** | **BLOCKING** | 15 mins | `eval/datasets/v0/gold_intents.jsonl` |
| **P2** | Obtain API Keys for Backup STT (Gladia, Groq) & TTS (Azure / Cartesia) | Non-Blocking | 15 mins | Can run incrementally |
| **P3** | Record Optional Condition `noise` (Fan / TV background) | Non-Blocking | 15 mins | Smartphone / PC |
| **P4** | Record Optional Condition `helmet` (Muffled / Cloth) | Non-Blocking | 10 mins | Smartphone / PC |

---

## 2. Step-by-Step Audio Recording & Verification [P0 — BLOCKING]

1. **Read the Script:** Open [docs/spikes/recording-script.md](file:///c:/Users/Lenovo/Downloads/drivethru/docs/spikes/recording-script.md).
2. **Setup Environment:** Use your laptop or smartphone microphone in a quiet room.
3. **Record 40 Utterances:**
   - Format: **WAV (PCM 16-bit, Mono, 16 kHz or higher)**.
   - Speak naturally without exaggerating pronunciation.
   - Save files directly into `eval/audio/real/` using filenames:
     `real_001_quiet.wav` through `real_040_quiet.wav`.
4. **Validate Your Recordings:**
   Run the following terminal command from the project root:
   ```powershell
   uv run python eval/scripts/check_recordings.py
   ```
   - If any file is stereo, too short, or corrupted, the script will state the exact defect.
   - Ensure the output displays: `[OK] Condition 'quiet ': 40/40 passed`.

---

## 3. Candidate Vendor Credentials & Hard Spend Caps [P1 — BLOCKING]

Register for each vendor account below, retrieve the API key, and add the **key name only** to your local `.env` file.  
*(Never commit `.env` to git).*

| Candidate Vendor | Registration URL | Required `.env` Variable Name | Credit Card Required? | Free Trial Credit | Est. Spike Spend | Where to Set Spend Cap / Alert |
|---|---|---|:---:|:---:|:---:|---|
| **Deepgram (Nova-3)** | [console.deepgram.com/signup](https://console.deepgram.com/signup) | `DEEPGRAM_API_KEY` | No | $200 free credit | ~$0.16 | Settings &rarr; Billing &rarr; Spend Alerts |
| **Soniox** | [soniox.com](https://soniox.com/) | `SONIOX_API_KEY` | **Yes** *(anti-abuse)* | $0 *(pay-as-you-go)* | ~$0.04 | Dashboard &rarr; Billing &rarr; Monthly Budget Limit ($5) |
| **Gladia (Solaria-1)** | [app.gladia.io/auth/signup](https://app.gladia.io/auth/signup) | `GLADIA_API_KEY` | No | €50 free credit | ~$0.27 | Account &rarr; Billing & Usage Limits |
| **Groq (Whisper)** | [console.groq.com/keys](https://console.groq.com/keys) | `GROQ_API_KEY` | No | Free Tier (20 RPM) | $0.00 | Console &rarr; Limits |
| **Google Gemini (LLM)** | [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey) | `GEMINI_API_KEY` | No (Free) / Yes (Paid) | Tier berbayar $300 Cloud credit | ~$0.01 | Google Cloud &rarr; Billing &rarr; Budgets & Alerts ($5) |
| **OpenAI (GPT-4o-mini)** | [platform.openai.com/signup](https://platform.openai.com/signup) | `OPENAI_API_KEY` | Yes | $5 credit | ~$0.02 | Settings &rarr; Billing &rarr; Usage limits ($5 hard limit) |
| **Azure Speech (TTS)** | [portal.azure.com](https://portal.azure.com/#create/Microsoft.CognitiveServicesSpeechServices) | `AZURE_SPEECH_KEY`<br>`AZURE_SPEECH_REGION` | Yes | F0 free tier (500k char) | ~$0.12 | Cost Management &rarr; Budgets & Alerts ($5) |
| **Cartesia (TTS)** | [play.cartesia.ai](https://play.cartesia.ai/) | `CARTESIA_API_KEY` | No | Free starter | ~$0.22 | Settings &rarr; Billing &rarr; Monthly Cap |
| **ElevenLabs (TTS)** | [elevenlabs.io/sign-up](https://elevenlabs.io/sign-up) | `ELEVENLABS_API_KEY` | No | 10,000 free chars/mo | $0.00 | Subscription &rarr; Usage & Billing |

> [!IMPORTANT]
> **Budget Confirmation:** Please set or confirm `SPIKE_BUDGET_USD=8.0` in your environment. The automated harness will abort with a `BudgetExceededError` if cumulative benchmark calls exceed this threshold.

---

## 4. 20 Seeded Gold Intent Spot-Check [P1 — BLOCKING]

To ensure the automated evaluation dataset has not hallucinated intent parameters, please inspect the gold labels for the 20 seeded scenario IDs in [eval/datasets/v0/gold_intents.jsonl](file:///c:/Users/Lenovo/Downloads/drivethru/eval/datasets/v0/gold_intents.jsonl):

**Checklist of 20 Scenario IDs (Random Seed = 42):**
- [ ] `scen_007`: Verify item, quantity, and modifiers
- [ ] `scen_008`: Verify item and quantity
- [ ] `scen_009`: Verify item and quantity
- [ ] `scen_023`: Verify multi-item combo / quantity
- [ ] `scen_024`: Verify drink size and ice modifiers
- [ ] `scen_027`: Verify medium size modifier
- [ ] `scen_029`: Verify drinks and quantities
- [ ] `scen_036`: Verify burger customization modifier
- [ ] `scen_051`: Verify breakfast hours availability
- [ ] `scen_056`: Verify out-of-stock rejection intent
- [ ] `scen_057`: Verify modifier constraints
- [ ] `scen_058`: Verify burger modifier
- [ ] `scen_060`: Verify combo slot selection
- [ ] `scen_063`: Verify combo side substitution
- [ ] `scen_071`: Verify correction / undo of french fries to rice
- [ ] `scen_072`: Verify undo decrement from 2 to 1 burger
- [ ] `scen_108`: Verify code-switching English item name
- [ ] `scen_109`: Verify code-switching breakfast item
- [ ] `scen_115`: Verify helmet acoustic noise tags
- [ ] `scen_130`: Verify multi-turn final confirmation

*If any intent parameter differs from your expected cart logic, edit the corresponding line in `eval/datasets/v0/gold_intents.jsonl`.*

---

## 5. What You Do NOT Need to Do (Do Not Waste Time)

- ❌ **Do NOT write any adapter code:** The async streaming harness and fakes are already fully built and tested.
- ❌ **Do NOT call vendor APIs manually:** The runner script (`eval/scripts/spikes/runner.py`) will automatically execute all calls, record raw JSON, and compute KER/WER in Minggu 2b.
- ❌ **Do NOT record all 120 audio files:** Only the 40 `quiet` recordings are strictly required to unblock Gate G1. Background noise and helmet recordings can be added later.
- ❌ **Do NOT build the final cart state machine yet:** State machine completion is strictly scheduled for Minggu 3.
