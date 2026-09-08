from __future__ import annotations

import os
import subprocess
import sys
import time
from datetime import datetime

INTERVAL_SECONDS = int(os.getenv("COLLECTOR_INTERVAL_SECONDS", "3600"))


def run_script(script_name: str) -> int:
    result = subprocess.run(
        [sys.executable, script_name],
        text=True,
        capture_output=False,
    )
    return result.returncode


def run_once():
    print(f"[collector-loop] start {datetime.now():%Y-%m-%d %H:%M:%S}", flush=True)

    # 기존 스냅샷에서 KBO/로또/경기일정 등 비상품 검색어를 먼저 제거
    sanitize_code = run_script("sanitize_snapshots.py")
    print(
        f"[collector-loop] sanitize code={sanitize_code} "
        f"{datetime.now():%Y-%m-%d %H:%M:%S}",
        flush=True,
    )

    collect_code = run_script("collector.py")
    print(
        f"[collector-loop] collector code={collect_code} "
        f"{datetime.now():%Y-%m-%d %H:%M:%S}",
        flush=True,
    )

    # 새 수집 결과까지 다시 검증해 비상품 데이터가 남지 않게 함
    sanitize_after_code = run_script("sanitize_snapshots.py")
    print(
        f"[collector-loop] sanitize-after code={sanitize_after_code} "
        f"{datetime.now():%Y-%m-%d %H:%M:%S}",
        flush=True,
    )


if __name__ == "__main__":
    # 서버 시작 직후 1회 실행하고 이후 지정 간격마다 반복
    while True:
        try:
            run_once()
        except Exception as exc:
            print(f"[collector-loop] error: {exc}", flush=True)
        time.sleep(INTERVAL_SECONDS)
