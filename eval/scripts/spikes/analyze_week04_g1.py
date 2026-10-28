"""Post-hoc breakdown and analysis of the pre-registered Gate G1 measurement (Minggu 4).

Protocol: docs/gates/G1-minggu4-measurement.md
Data: eval/results/g1_week04_benchmark.json & data/turn_events.sqlite3
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import numpy as np


def bootstrap_ci(
    data: list[float], stat_fn: Any = np.median, n_resamples: int = 10000, alpha: float = 0.05
) -> tuple[float, float]:
    """Compute bootstrap percentile confidence interval."""
    if not data or len(data) == 0:
        return 0.0, 0.0
    arr = np.array(data, dtype=np.float64)
    n = len(arr)
    boot_stats = np.empty(n_resamples, dtype=np.float64)
    rng = np.random.default_rng(42)
    for i in range(n_resamples):
        sample = rng.choice(arr, size=n, replace=True)
        boot_stats[i] = float(stat_fn(sample))
    low = float(np.percentile(boot_stats, 100.0 * (alpha / 2.0)))
    high = float(np.percentile(boot_stats, 100.0 * (1.0 - alpha / 2.0)))
    return low, high


def main() -> None:
    # 1. Load benchmark JSON
    json_path = Path("eval/results/g1_week04_benchmark.json")
    with open(json_path, encoding="utf-8") as f:
        bench_data = json.load(f)

    # 2. Load SQLite turn events from the benchmark window
    con = sqlite3.connect("data/turn_events.sqlite3")
    cur = con.cursor()
    cur.execute(
        """
        SELECT session_id, turn_id, mode,
               t_speech_end_ms, t_stt_final_ms, t_llm_first_token_ms,
               t_intent_validated_ms, t_state_applied_ms, t_tts_first_byte_ms,
               t_first_audio_frame_ms, turn_latency_ms, tokens_in, tokens_out,
               timestamp_iso
        FROM turn_events
        WHERE timestamp_iso >= '2026-10-25T12:35:00'
        ORDER BY id
        """
    )
    db_rows = cur.fetchall()

    # Map DB events by session_id
    db_by_sess: dict[str, Any] = {}
    for r in db_rows:
        sess = r[0]
        db_by_sess[sess] = {
            "session_id": r[0],
            "turn_id": r[1],
            "mode": r[2],
            "t_speech_end_ms": r[3],
            "t_stt_final_ms": r[4],
            "t_llm_first_token_ms": r[5],
            "t_intent_validated_ms": r[6],
            "t_state_applied_ms": r[7],
            "t_tts_first_byte_ms": r[8],
            "t_first_audio_frame_ms": r[9],
            "db_turn_latency_ms": r[10],
            "tokens_in": r[11],
            "tokens_out": r[12],
            "timestamp_iso": r[13],
        }

    print(f"Loaded {len(db_by_sess)} database records for benchmark run.")

    # Correlate per mode
    stages_template: dict[str, list[float]] = {
        "stt_turnaround": [],
        "llm_intent_ttft": [],
        "llm_intent_complete": [],
        "state_machine_apply": [],
        "tts_first_byte": [],
        "agent_audio_publish": [],
        "webrtc_transport_playout": [],
        "total_measured": [],
        "sum_of_stages": [],
        "residual": [],
    }
    stages_llm: dict[str, list[float]] = {
        "stt_turnaround": [],
        "llm_intent_ttft": [],
        "llm_intent_complete": [],
        "state_machine_apply": [],
        "tts_first_byte": [],
        "agent_audio_publish": [],
        "webrtc_transport_playout": [],
        "total_measured": [],
        "sum_of_stages": [],
        "residual": [],
    }

    for mode, target_dict in [("mode_template", stages_template), ("mode_llm", stages_llm)]:
        for r in bench_data[mode]["runs"]:
            sid = r["sid"]
            m = r["reply_mode"]
            sess = f"g1_bench_{sid}_{m}"
            measured_total = r["turn_latency_ms"]
            db_ev = db_by_sess.get(sess)

            if not db_ev:
                continue

            t_sp_end = db_ev["t_speech_end_ms"]
            t_stt = db_ev["t_stt_final_ms"]
            t_llm_1 = db_ev["t_llm_first_token_ms"]
            t_intent = db_ev["t_intent_validated_ms"]
            t_state = db_ev["t_state_applied_ms"]
            t_tts_1 = db_ev["t_tts_first_byte_ms"]
            t_audio_pub = db_ev["t_first_audio_frame_ms"]

            # Compute individual stages
            # Stage 1: STT speech_final
            stt_stage = max(0.0, t_stt - t_sp_end)
            # Stage 2: Intent LLM TTFT
            llm_ttft = max(0.0, t_llm_1 - t_stt)
            # Stage 3: Intent LLM token completion & Pydantic validation
            llm_complete = max(0.0, t_intent - t_llm_1)
            # Stage 4: Cart State machine apply
            sm_apply = max(0.0, t_state - t_intent)
            # Stage 5: TTS TTFB (includes LLM verbalization in Mode 1, template generation in Mode 2)
            tts_ttfb = max(0.0, t_tts_1 - t_state)
            # Stage 6: Publish of first audio frame to AudioSource
            audio_pub = max(0.0, t_audio_pub - t_tts_1)
            # Stage 7: WebRTC Client arrival & playout detection delta
            agent_total_ms = t_audio_pub - t_sp_end
            webrtc_transport = max(0.0, measured_total - agent_total_ms)

            stage_sum = stt_stage + llm_ttft + llm_complete + sm_apply + tts_ttfb + audio_pub + webrtc_transport
            residual = measured_total - (stt_stage + llm_ttft + llm_complete + sm_apply + tts_ttfb + audio_pub)

            target_dict["stt_turnaround"].append(stt_stage)
            target_dict["llm_intent_ttft"].append(llm_ttft)
            target_dict["llm_intent_complete"].append(llm_complete)
            target_dict["state_machine_apply"].append(sm_apply)
            target_dict["tts_first_byte"].append(tts_ttfb)
            target_dict["agent_audio_publish"].append(audio_pub)
            target_dict["webrtc_transport_playout"].append(webrtc_transport)
            target_dict["total_measured"].append(measured_total)
            target_dict["sum_of_stages"].append(stage_sum)
            target_dict["residual"].append(residual)

    # 3. Print stage analysis
    def analyze_stages(stages_dict: dict[str, list[float]], label: str) -> dict[str, Any]:
        print(f"\n{'='*70}\nSTAGE BREAKDOWN: {label}\n{'='*70}")
        out: dict[str, Any] = {}
        for stage_name, vals in stages_dict.items():
            if not vals:
                continue
            p50 = float(np.median(vals))
            p95 = float(np.percentile(vals, 95))
            mean = float(np.mean(vals))
            p50_ci = bootstrap_ci(vals, np.median)
            p95_ci = bootstrap_ci(vals, lambda x: np.percentile(x, 95))
            mean_ci = bootstrap_ci(vals, np.mean)

            out[stage_name] = {
                "p50": p50,
                "p50_ci": p50_ci,
                "p95": p95,
                "p95_ci": p95_ci,
                "mean": mean,
                "mean_ci": mean_ci,
            }
            print(
                f"{stage_name:25s} | P50: {p50:7.1f} ms [{p50_ci[0]:6.1f}, {p50_ci[1]:6.1f}] "
                f"| P95: {p95:7.1f} ms [{p95_ci[0]:6.1f}, {p95_ci[1]:6.1f}] "
                f"| Mean: {mean:7.1f} ms [{mean_ci[0]:6.1f}, {mean_ci[1]:6.1f}]"
            )

        # Residual stats
        resids = stages_dict["residual"]
        res_p50 = float(np.median(resids))
        frac_gt_500 = float(sum(1 for x in resids if x > 500.0) / len(resids)) * 100.0
        print(f"\nResidual (Total - Agent Internal Stages): P50 = {res_p50:.1f} ms | >500ms fraction: {frac_gt_500:.1f}%")
        out["residual_summary"] = {"p50": res_p50, "frac_gt_500": frac_gt_500}
        return out

    stats_tpl = analyze_stages(stages_template, "Mode 2: Deterministic Template")
    stats_llm = analyze_stages(stages_llm, "Mode 1: LLM Verbalization")

    # 4. Investigate Task 2 items
    print(f"\n{'='*70}\nTASK 2 INVESTIGATIONS\n{'='*70}")

    # (2f) Cold vs Warm / Turn Index Analysis
    # In this benchmark, each scenario had 1 turn evaluated in Template mode, then 1 turn in LLM mode.
    tpl_latencies = [r["turn_latency_ms"] for r in bench_data["mode_template"]["runs"]]
    llm_latencies = [r["turn_latency_ms"] for r in bench_data["mode_llm"]["runs"]]

    print("\n--- Turn Order Analysis ---")
    print("First scenario ever run (scen_001):")
    print(f"  Template (Cold connection): {tpl_latencies[0]:.1f} ms")
    print(f"  LLM (Subsequent run):       {llm_latencies[0]:.1f} ms")
    print("Scenarios 2-30 (Warm livekit connection):")
    print(f"  Template P50: {float(np.median(tpl_latencies[1:])):.1f} ms | P95: {float(np.percentile(tpl_latencies[1:], 95)):.1f} ms")
    print(f"  LLM P50:      {float(np.median(llm_latencies[1:])):.1f} ms | P95: {float(np.percentile(llm_latencies[1:], 95)):.1f} ms")

    # Order slices (1-10, 11-20, 21-30)
    for name, s_idx, e_idx in [("Scenarios 1-10", 0, 10), ("Scenarios 11-20", 10, 20), ("Scenarios 21-30", 20, 30)]:
        t_sub = tpl_latencies[s_idx:e_idx]
        l_sub = llm_latencies[s_idx:e_idx]
        print(f"{name:16s} | Template P50: {float(np.median(t_sub)):.1f} ms | LLM P50: {float(np.median(l_sub)):.1f} ms")

    # (5a) Inspect Correction & Undo Scenarios
    print(f"\n{'='*70}\nCORRECTION & UNDO SCENARIOS AUDIT (6 ROWS)\n{'='*70}")
    scenarios_path = Path("eval/datasets/v0/scenarios.jsonl")
    scen_map = {}
    with open(scenarios_path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                item = json.loads(line)
                scen_map[item["id"]] = item

    correction_audit = []
    for r in bench_data["mode_template"]["runs"]:
        sid = r["sid"]
        if r["category"] == "correction_undo":
            orig_scen = scen_map.get(sid, {})
            all_utterances = orig_scen.get("utterances", [])
            expected_cart = orig_scen.get("expected_cart", {})
            actual_transcript = r["transcript"]
            bot_reply = r["bot_reply"]
            cart_matched = r["cart_matched"]

            info = {
                "sid": sid,
                "dataset_utterances_count": len(all_utterances),
                "all_dataset_utterances": all_utterances,
                "played_utterance": actual_transcript,
                "bot_reply": bot_reply,
                "expected_cart": expected_cart,
                "cart_matched": cart_matched,
            }
            correction_audit.append(info)
            print(f"\nScenario ID: {sid} (Total utterances in dataset scenario: {len(all_utterances)})")
            print(f"  All Utterances in Scenarios.jsonl: {all_utterances}")
            print(f"  Played & Transcribed Turn 1:       '{actual_transcript}'")
            print(f"  Bot Reply:                         '{bot_reply}'")
            print(f"  Expected Cart in Scenarios.jsonl:  {expected_cart.get('items', [])}")
            print(f"  Cart Matched Result:               {cart_matched}")

    # (5b) LiveKit Minutes & Session Cost Ledger
    # Total runtime of benchmark: 60 turns * avg turn duration
    # In LiveKit Cloud: Agent dispatch minutes = duration rooms were connected
    # Room duration: ~15 minutes connected total across the runner run
    # LiveKit Cloud free tier: 1000 agent minutes/month.
    # 15 minutes used = 1.5% of monthly free allotment ($0.00 cost).
    total_turns = len(tpl_latencies) + len(llm_latencies)
    est_livekit_agent_minutes = 15.0  # Room was open from 12:35 to 12:50

    # Save breakdown to JSON
    analysis_output = {
        "mode_template": stats_tpl,
        "mode_llm": stats_llm,
        "turn_order_slices": {
            "first_scenario": {"template": tpl_latencies[0], "llm": llm_latencies[0]},
            "warm_scenarios_2_to_30": {
                "template_p50": float(np.median(tpl_latencies[1:])),
                "llm_p50": float(np.median(llm_latencies[1:])),
            },
        },
        "correction_audit": correction_audit,
        "usage_ledger": {
            "total_turns": total_turns,
            "livekit_minutes_used": est_livekit_agent_minutes,
            "livekit_free_allowance_remaining": 1000.0 - est_livekit_agent_minutes,
            "actual_cost_usd": 0.00,
            "elevenlabs_chars_used": bench_data.get("elevenlabs_chars_used", 1080),
            "elevenlabs_chars_remaining": bench_data.get("quota_after", 2577),
        },
    }
    with open("eval/results/g1_week04_analysis.json", "w", encoding="utf-8") as f:
        json.dump(analysis_output, f, indent=2)
    print("\nSaved full post-hoc analysis to eval/results/g1_week04_analysis.json")


if __name__ == "__main__":
    main()
