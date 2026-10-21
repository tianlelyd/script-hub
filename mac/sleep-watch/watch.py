#!/usr/bin/env python3
"""只读监控 SleepDisabled 的采样值变化。"""
import datetime, json, pathlib, re, signal, subprocess, time
import argparse
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir', type=pathlib.Path, default=pathlib.Path(__file__).resolve().parent / 'logs')
parser.add_argument('--duration', type=float, default=86400, help='最长运行秒数，默认 24 小时')
options = parser.parse_args()
if not 0 < options.duration <= 86400:
    parser.error('--duration 必须大于 0 且不超过 86400 秒')
ROOT = options.output_dir.expanduser().resolve()
ROOT.mkdir(parents=True, exist_ok=True)
import fcntl
lock = (ROOT / 'watch.lock').open('a')
try:
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError:
    raise SystemExit('State monitor is already running in this output directory')
running = True

def stop(*_):
    global running
    running = False

for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
    signal.signal(sig, stop)

def command(args, timeout=5):
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if result.returncode:
        raise RuntimeError(result.stderr[:1000])
    return result.stdout

def record(kind, **data):
    path = ROOT / 'events.jsonl'
    if path.exists() and path.stat().st_size > 5_000_000:
        path.replace(ROOT / 'events.previous.jsonl')
    with path.open('a') as file:
        file.write(json.dumps(dict(time=datetime.datetime.now().astimezone().isoformat(), event=kind, **data), ensure_ascii=False) + '\n')

heartbeat = time.monotonic()
previous = None
last_error = None
deadline = time.monotonic() + options.duration
record('started', interval_seconds=2, maximum_seconds=options.duration, attribution='state only; run audit.py separately for pmset exec attribution')
try:
    while running and time.monotonic() < deadline:
        try:
            state = command(['/usr/bin/pmset', '-g'])
            match = re.search(r'^\s*SleepDisabled\s+(\d+)\s*$', state, re.M)
            if not match:
                raise RuntimeError('SleepDisabled field missing')
            value = int(match.group(1))
            if value != previous:
                record('initial' if previous is None else 'changed', old=previous, new=value, pmset=state)
                changed = previous is not None
                previous = value
                try:
                    record('assertions', text=command(['/usr/bin/pmset', '-g', 'assertions']))
                except Exception as error:
                    record('context_error', message='assertions: ' + str(error))
                if changed:
                    try:
                        text = command(['/usr/bin/log', 'show', '--last', '20s', '--style', 'compact', '--info', '--predicate', 'process == "powerd" AND (eventMessage CONTAINS[c] "sleep" OR eventMessage CONTAINS[c] "setting")'], timeout=8)
                        record('power_log_context_not_attribution', text=text[-24000:])
                    except Exception as error:
                        record('context_error', message=str(error)[:1000])
            last_error = None
        except Exception as error:
            message = str(error)[:1000]
            if message != last_error:
                record('error', message=message)
                last_error = message
        if time.monotonic() - heartbeat >= 10:
            record('heartbeat', last_value=previous)
            heartbeat = time.monotonic()
        time.sleep(2)
finally:
    record('stopped', last_value=previous)
