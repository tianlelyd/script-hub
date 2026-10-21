#!/usr/bin/env python3
"""使用 eslogger 审计 pmset 调用；需要 root 和完全磁盘访问权限。"""
import os, sys, json, time, signal, pathlib, subprocess, select, tty, datetime
import argparse
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir', type=pathlib.Path, default=pathlib.Path('/var/log/sleep-watch'))
parser.add_argument('--duration', type=float, default=86400, help='最长运行秒数，默认 24 小时')
options = parser.parse_args()
if not 0 < options.duration <= 86400:
    parser.error('--duration 必须大于 0 且不超过 86400 秒')
if os.geteuid() != 0:
    sys.exit('Requires administrator authentication')
# Pin a root-owned directory; a caller cannot redirect later writes by renaming it.
import stat, fcntl
ROOT = options.output_dir.expanduser().absolute()
ROOT.mkdir(parents=True, exist_ok=True)
directory_fd = os.open(ROOT, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
info = os.fstat(directory_fd)
if info.st_uid != 0 or info.st_mode & 0o022:
    sys.exit('Audit output directory must be root-owned and not group/world writable')
os.fchdir(directory_fd)
os.close(directory_fd)
ROOT = pathlib.Path('.')
OUTPUT = ROOT / 'caller-audit.jsonl'

def secure_open(name, truncate=False):
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o644)
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or info.st_uid != 0 or info.st_nlink != 1:
        os.close(fd)
        raise RuntimeError('Unsafe audit output file: ' + str(name))
    if truncate:
        os.ftruncate(fd, 0)
    return os.fdopen(fd, 'a')

lock = secure_open('caller-audit.lock')
try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
except BlockingIOError: sys.exit('Caller audit is already running')
alive = True
child = None

def record(kind, **data):
    row = json.dumps(dict(time=datetime.datetime.now().astimezone().isoformat(), event=kind, **data), ensure_ascii=False) + '\n'
    paths = [OUTPUT]
    if kind == 'pmset_exec' and data.get('classification') != 'query':
        paths.append(ROOT / 'writer-audit.jsonl')
    for path in paths:
        if path.exists() and path.stat().st_size > 5_000_000:
            path.replace(path.with_name(path.stem + '.previous.jsonl'))
        with secure_open(path) as stream:
            stream.write(row)

def stop(*args):
    global alive
    alive = False

def pid(p):
    return p.get('audit_token', {}).get('pid')

def metadata(p):
    return {k:p[k] for k in ['audit_token','ppid','original_ppid','parent_audit_token','responsible_audit_token','executable','signing_id','team_id'] if k in p}

for s in [signal.SIGTERM, signal.SIGINT, signal.SIGHUP]: signal.signal(s, stop)
if os.geteuid() != 0: sys.exit('Requires administrator authentication')
with secure_open('caller-audit.pid', truncate=True) as stream:
    stream.write(str(os.getpid()))
master, slave = os.openpty(); tty.setraw(slave)
import codecs
utf8 = codecs.getincrementaldecoder('utf-8')('replace')
cache = {}; buffer = ''; decoder=json.JSONDecoder(); count=0; matched=0; failures=0; last_seq=None; sequence_gaps=0
try:
    with secure_open('caller-audit-eslogger.stderr') as err:
        child=subprocess.Popen(['/usr/bin/eslogger','exec'],stdout=slave,stderr=err,start_new_session=True)
        os.close(slave); slave = None
        record('started',pid=os.getpid(),eslogger_pid=child.pid,scope='pmset exec only; no direct API attribution')
        deadline=time.monotonic()+options.duration; heartbeat=time.monotonic()
        while alive and time.monotonic()<deadline:
            if child.poll() is not None:
                record('error',message='eslogger exited',exit_code=child.returncode);failures=1;break
            if select.select([master],[],[],1)[0]:
                try: raw=os.read(master,65536)
                except OSError as error:
                    record('error', message='eslogger PTY read failed: ' + str(error));failures=1;break
                if not raw:
                    record('error', message='eslogger stream ended unexpectedly');failures=1;break
                buffer+=utf8.decode(raw)
                while buffer.strip():
                    buffer=buffer.lstrip()
                    try: obj,end=decoder.raw_decode(buffer)
                    except json.JSONDecodeError: break
                    buffer=buffer[end:];count+=1
                    seq=obj.get('seq_num')
                    if isinstance(seq, int):
                        if last_seq is not None and seq > last_seq + 1:
                            sequence_gaps += seq-last_seq-1
                            record('sequence_gap', previous=last_seq, current=seq)
                        last_seq=seq
                    actor=obj.get('process',{}); event=obj.get('event',{}).get('exec',{});target=event.get('target',{})
                    for p in [actor,target]:
                        if pid(p):cache[pid(p)]=metadata(p)
                    if len(cache)>8192:
                        for key in list(cache)[:4096]: del cache[key]
                    if target.get('executable',{}).get('path')=='/usr/bin/pmset':
                        matched+=1
                        args=event.get('args',[])
                        parent=target.get('ppid')
                        record('pmset_exec',target=metadata(target),actor=metadata(actor),args=args,
                               parent=(cache.get(parent) if cache.get(parent, {}).get('audit_token') == target.get('parent_audit_token') else None),es_time=obj.get('time'),
                               classification='query' if len(args) > 1 and args[1] == '-g' else 'potential_write_review_arguments',
                               raw_exec={k:v for k,v in event.items() if k not in ['env','target','args']})
                if len(buffer)>4_000_000:
                    record('error',message='Unparsed JSON exceeds buffer limit');failures=1;break
            if time.monotonic()-heartbeat>=10:
                record('heartbeat',seen_exec=count,matched_pmset=matched,eslogger_alive=child.poll() is None,sequence_gaps=sequence_gaps);heartbeat=time.monotonic()
except Exception as error:
    failures=1
    record('error', message=str(error))
finally:
    if slave is not None:
        os.close(slave)
    if child and child.poll() is None:
        child.terminate()
        try:child.wait(timeout=5)
        except subprocess.TimeoutExpired:child.kill();child.wait(timeout=5)
    os.close(master)
    (ROOT/'caller-audit.pid').unlink(missing_ok=True)
    record('stopped',seen_exec=count,matched_pmset=matched)

sys.exit(failures)
