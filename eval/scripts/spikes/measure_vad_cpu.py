import time
import tracemalloc

import numpy as np
from livekit.local_inference import VAD, VAD_WINDOW_SAMPLES

# Generate 10 seconds of 16kHz mono audio (mix of noise, speech, silence)
sr = 16000
duration_s = 10.0
total_samples = int(sr * duration_s)
# 16-bit PCM samples
np.random.seed(42)
samples = (np.random.randn(total_samples) * 1000).astype(np.int16)

chunk_len = VAD_WINDOW_SAMPLES  # 512 samples = 32ms
num_chunks = len(samples) // chunk_len

print(f"Testing LiveKit Local VAD on {duration_s:.1f} seconds of audio ({num_chunks} chunks of 32ms)...")

tracemalloc.start()
vad_inst = VAD()
vad_inst.reset()

# Warmup 5 chunks
for i in range(5):
    _ = vad_inst.predict(samples[i*chunk_len : (i+1)*chunk_len])

# Measure CPU time and Wall time
t_cpu_start = time.process_time()
t_wall_start = time.perf_counter()

predictions = []
for i in range(num_chunks):
    chunk = samples[i * chunk_len : (i + 1) * chunk_len]
    prob = vad_inst.predict(chunk)
    predictions.append(prob)

t_cpu_elapsed = time.process_time() - t_cpu_start
t_wall_elapsed = time.perf_counter() - t_wall_start
current_mem, peak_mem = tracemalloc.get_traced_memory()
tracemalloc.stop()

vad_inst.close()

cpu_time_per_sec_audio = t_cpu_elapsed / duration_s
wall_time_per_sec_audio = t_wall_elapsed / duration_s

# Compute RTF (Real-Time Factor)
# RTF = processing_time / audio_duration
# RTF on 1.0 CPU:
rtf_1cpu = cpu_time_per_sec_audio
# RTF on 0.1 CPU (where available CPU speed is scaled by 0.1):
rtf_01cpu = cpu_time_per_sec_audio / 0.1

print("\n--- MEASUREMENT RESULTS ---")
print(f"Audio Duration: {duration_s:.1f} s")
print(f"Total CPU Time: {t_cpu_elapsed * 1000:.2f} ms")
print(f"Total Wall Time: {t_wall_elapsed * 1000:.2f} ms")
print(f"CPU Time per 1 second of audio: {cpu_time_per_sec_audio * 1000:.2f} ms")
print(f"Peak Memory Allocated by VAD: {peak_mem / 1024:.2f} KB ({peak_mem / (1024*1024):.4f} MB)")
print(f"Real-Time Factor (1.0 CPU): {rtf_1cpu:.4f} (needs {rtf_1cpu*100:.2f}% of 1 core)")
print(f"Real-Time Factor (0.1 CPU limit): {rtf_01cpu:.4f} (needs {rtf_01cpu*100:.2f}% of 0.1 core quota)")
print(f"Keeps up with real-time audio on 0.1 CPU? {'YES (RTF < 1.0)' if rtf_01cpu < 1.0 else 'NO (RTF >= 1.0, buffer will overflow)'}")
