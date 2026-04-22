"""Plot the resource monitor CSV as a PNG."""
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

csv_path = Path(sys.argv[1] if len(sys.argv) > 1 else ".cache/monitor.csv")
df = pd.read_csv(csv_path)

fig, ax1 = plt.subplots(figsize=(10, 4))
ax1.set_xlabel("Time (s)")
ax1.set_ylabel("CPU %", color="tab:blue")
ax1.plot(df["time"], df["cpu_percent"], color="tab:blue", label="CPU")
ax1.tick_params(axis="y", labelcolor="tab:blue")

ax2 = ax1.twinx()
ax2.set_ylabel("RAM used (GB)", color="tab:red")
ax2.plot(df["time"], df["ram_used_gb"], color="tab:red", label="RAM")
ax2.tick_params(axis="y", labelcolor="tab:red")

plt.title("Video2Notes-AI resource usage")
fig.tight_layout()
plt.savefig("output/resource_usage.png", dpi=120)
print("Saved to output/resource_usage.png")