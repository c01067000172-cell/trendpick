from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime

INTERVAL_SECONDS = int(os.getenv("COLLECTOR_INTERVAL_SECONDS", "3600"))

def run_once():
    print(f"[collector-loop] start {datetime.now():%Y-%m-%d %H:%M:%S}", flush=True)
    result = subprocess.run(
        [sys.executable, "collector.py"],
        text=True,
        capture_output=False,
    )
    print(
        f"[collector-loop] finished code={result.returncode} "
        f"{datetime.now():%Y-%m-%d %H:%M:%S}",
        flush=True,
    )

if __name__ == "__main__":
    # 서버 시작 직후 1회 수집
    while True:
        try:
            run_once()
        except Exception as exc:
            print(f"[collector-loop] error: {exc}", flush=True)
        time.sleep(INTERVAL_SECONDS)
