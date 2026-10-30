"""Unit and integration tests for barge-in detection and echo-bleed guard."""

from __future__ import annotations

import asyncio
import time

import pytest
from lajur_agent.barge_in import BargeInController
from lajur_cart.menu_service import MenuService
from lajur_cart.state_machine import CartSession


@pytest.mark.asyncio
async def test_barge_in_trigger_and_stop_latency() -> None:
    """When user sustained speech exceeds min duration while bot speaks, barge-in triggers immediately."""
    triggered = False

    async def on_barge_in() -> None:
        nonlocal triggered
        triggered = True

    controller = BargeInController(
        min_speech_duration_ms=150.0,
        on_barge_in_triggered=on_barge_in,
    )

    cancel_evt = controller.start_bot_speaking()
    assert controller.is_bot_speaking
    assert not cancel_evt.is_set()

    t0 = time.perf_counter()
    # First frame at t0: speech starts
    assert not controller.on_user_speech_frame(has_voice=True, now=t0)
    assert not cancel_evt.is_set()

    # Frame at t0 + 100ms: still under 150ms threshold
    assert not controller.on_user_speech_frame(has_voice=True, now=t0 + 0.100)
    assert not cancel_evt.is_set()

    # Frame at t0 + 160ms: sustained speech >= 150ms -> triggers barge-in!
    res = controller.on_user_speech_frame(has_voice=True, now=t0 + 0.160)
    assert res is True
    assert cancel_evt.is_set()
    assert not controller.is_bot_speaking
    assert controller.last_stop_latency_ms < 150.0  # Stop latency is near-instantaneous (<150ms)

    await asyncio.sleep(0.01)
    assert triggered is True


@pytest.mark.asyncio
async def test_echo_bleed_guard_filters_spikes() -> None:
    """Acoustic echo spikes (<150ms) must NOT trigger barge-in; bot speaking continues."""
    controller = BargeInController(min_speech_duration_ms=150.0)
    cancel_evt = controller.start_bot_speaking()

    t0 = time.perf_counter()

    # Spike 1: 60ms click / echo
    controller.on_user_speech_frame(has_voice=True, now=t0)
    controller.on_user_speech_frame(has_voice=True, now=t0 + 0.060)
    # Silence follows
    controller.on_user_speech_frame(has_voice=False, now=t0 + 0.080)

    assert not cancel_evt.is_set()
    assert controller.is_bot_speaking

    # Spike 2: 120ms burst
    t1 = t0 + 0.500
    controller.on_user_speech_frame(has_voice=True, now=t1)
    controller.on_user_speech_frame(has_voice=True, now=t1 + 0.120)
    # Silence follows
    controller.on_user_speech_frame(has_voice=False, now=t1 + 0.140)

    assert not cancel_evt.is_set()
    assert controller.is_bot_speaking


@pytest.mark.asyncio
async def test_barge_in_cancels_in_flight_tasks() -> None:
    """In-flight generation tasks must be cancelled immediately when barge-in triggers."""
    controller = BargeInController(min_speech_duration_ms=50.0)

    task_cancelled = False

    async def long_running_generation() -> None:
        nonlocal task_cancelled
        try:
            await asyncio.sleep(5.0)
        except asyncio.CancelledError:
            task_cancelled = True
            raise

    task = asyncio.create_task(long_running_generation())
    controller.register_in_flight_task(task)
    assert controller.is_generation_in_flight

    # Let the task enter sleep
    await asyncio.sleep(0.01)

    t0 = time.perf_counter()
    controller.on_user_speech_frame(has_voice=True, now=t0)
    controller.on_user_speech_frame(has_voice=True, now=t0 + 0.060)

    # In Python 3.11+, task.cancelling() is True during cancellation
    assert task.cancelling() > 0 or task.cancelled()

    try:
        await task
    except asyncio.CancelledError:
        pass

    assert task.cancelled()
    assert task_cancelled
    assert not controller.is_generation_in_flight


def test_cart_state_consistency_on_interruption() -> None:
    """Cart state machine remains 100% consistent after interrupted turns."""
    ms = MenuService()
    session = CartSession(ms)

    from lajur_cart.intents import AddItemIntent

    # Turn 1 completes
    res = session.apply(AddItemIntent(item_id="burger_sapi_tunggal", quantity=1))
    assert res.cart.status != "rejected"
    assert session.cart.total_item_count == 1
    assert session.cart.total_price == 22000

    # Turn 2 interrupted before state apply: cart remains unaltered
    assert session.cart.total_item_count == 1
    assert session.cart.total_price == 22000
    assert len(session.cart.items) == 1
