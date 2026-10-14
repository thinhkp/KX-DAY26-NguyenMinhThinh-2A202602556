"""Run steps 01–03 and save redacted, genuine execution transcripts."""
import html
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from datetime import datetime, timezone
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"
EVIDENCE.mkdir(exist_ok=True)
ENV = os.environ.copy()
ENV.update({"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})
KEYS = dotenv_values(ROOT / ".env")


def redact(text):
    for key, value in KEYS.items():
        if value and ("KEY" in key or "TOKEN" in key):
            text = text.replace(value, "[REDACTED]")
    return text


def save(name, command, output, returncode):
    output = redact(output)
    stamp = datetime.now(timezone.utc).isoformat()
    displayed = output
    if name == "03a-auth-fail":
        displayed = "[Last 25 lines; full transcript is saved in the .txt file]\n" + "\n".join(output.splitlines()[-25:])
    (EVIDENCE / f"{name}.txt").write_text(output, encoding="utf-8")
    (EVIDENCE / f"{name}.json").write_text(json.dumps({
        "command": command, "exit_code": returncode, "captured_at_utc": stamp,
        "source": "actual subprocess stdout/stderr",
    }, indent=2), encoding="utf-8")
    (EVIDENCE / f"{name}.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Lab 26 execution evidence</title>'
        '<style>body{margin:24px;background:#101725;color:#edf3ff;font:15px Consolas,monospace;}'
        'h1{font:24px Arial}p{color:#b6c5df}pre{white-space:pre-wrap;overflow-wrap:anywhere;line-height:1.45}</style>'
        f'<h1>Lab 26 · {html.escape(name)}</h1><p>Actual captured process output · '
        f'Exit code {returncode} · {stamp}<br>Command: {html.escape(command)}<br>'
        'This page displays a saved execution transcript; it is not a terminal screenshot.</p>'
        f'<pre>{html.escape(displayed)}</pre>', encoding="utf-8")
    print(f"{name}: exit={returncode}")


def run(name, folder, script, *args, env=None):
    command = [sys.executable, script, *args]
    result = subprocess.run(command, cwd=ROOT / folder, env=env or ENV,
                            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
    save(name, "python " + " ".join([script, *args]), result.stdout + result.stderr, result.returncode)
    print(redact(result.stdout + result.stderr), flush=True)
    return result.returncode


if __name__ == "__main__":
    run("01-function-calling", "01-function-calling", "weather_function_calling.py",
        "Dùng tool get_weather lấy dữ liệu minh họa thời tiết Hà Nội và Đà Nẵng hôm nay. Nói rõ dữ liệu giả lập.")
    run("02-mcp-client", "02-mcp-basics", "weather_client.py")
    run("03b-registry", "03-production", "registry_client.py")
    run("03c-versioning", "03-production", "versioned_client.py")
    server_log = EVIDENCE / "03a-auth-server.txt"
    with server_log.open("w", encoding="utf-8") as log:
        process = subprocess.Popen([sys.executable, "auth_server.py"], cwd=ROOT / "03-production",
                                   env=ENV, stdout=log, stderr=log)
        try:
            import socket
            for _ in range(50):
                if process.poll() is not None:
                    raise RuntimeError("Auth server exited; see evidence/03a-auth-server.txt")
                try:
                    with socket.create_connection(("localhost", 8000), timeout=0.2):
                        break
                except OSError:
                    time.sleep(0.2)
            run("03a-auth-ok", "03-production", "auth_client.py")
            run("03a-auth-fail", "03-production", "auth_client.py", env={**ENV, "MCP_AUTH_TOKEN": "wrong-token"})
        finally:
            process.terminate()
            process.wait(timeout=10)
