import os

import psutil
from dotenv import load_dotenv

load_dotenv()

p = psutil.Process(os.getpid())
rss_baseline = p.memory_info().rss / (1024 * 1024)

# 1. Imports
from lajur_agent.adapters.deepgram import DeepgramSTTAdapter  # noqa: E402
from lajur_agent.adapters.edge_tts import EdgeTTSAdapter  # noqa: E402
from lajur_agent.adapters.gemini import GeminiLLMAdapter  # noqa: E402
from lajur_cart.menu_service import MenuService  # noqa: E402
from lajur_cart.models import Cart  # noqa: E402

rss_after_imports = p.memory_info().rss / (1024 * 1024)

# 2. Initialization
menu_service = MenuService("eval/menu/menu.json")
stt = DeepgramSTTAdapter()
llm = GeminiLLMAdapter()
tts = EdgeTTSAdapter()
cart = Cart()

rss_initialized = p.memory_info().rss / (1024 * 1024)

print("=" * 60)
print("AGENT WORKER WHOLE-PROCESS MEMORY MEASUREMENT (RSS)")
print("=" * 60)
print("Environment: Windows 11 Host, Python 3.12 (uv venv)")
print(f"1. Baseline Python Process RSS      : {rss_baseline:.2f} MB")
print(f"2. RSS After Full Module Imports     : {rss_after_imports:.2f} MB")
print(f"3. RSS Initialized (Adapters & Menu) : {rss_initialized:.2f} MB")
print(f"Fits within 512 MB RAM limit?        : {'YES' if rss_initialized < 512 else 'NO'} ({rss_initialized:.1f} MB / 512 MB, ~{rss_initialized/512*100:.1f}% used)")

