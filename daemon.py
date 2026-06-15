import time, joblib, psutil, argparse, signal, warnings, pandas as pd
from pathlib import Path
from utils import load_config
from cgroup_control import add_pid, set_cpu_quota_for_pid, remove_pid_group

warnings.filterwarnings("ignore", message="X does not have valid feature names")

parser = argparse.ArgumentParser()
parser.add_argument('--config', default='config.yaml')
parser.add_argument('--dry-run', action='store_true', help='Simulate throttling decisions without applying them')
args = parser.parse_args()

CFG = load_config(args.config)
MODEL_PATH = CFG.get('model_path', 'models/bgthrottle_rf.pkl')
SAMPLE_INTERVAL = float(CFG.get('sample_interval', 1.0))
CGROUP_ROOT = CFG.get('cgroup_root', '/sys/fs/cgroup/bgthrottle')
WHITELIST = set(CFG.get('whitelist', []))
BLACKLIST = set(CFG.get('blacklist', []))
MIN_CPU_TO_CONSIDER = float(CFG.get('enforcement', {}).get('min_cpu_to_consider', 2.0))
RATE_LIMIT_SECONDS = float(CFG.get('enforcement', {}).get('rate_limit_seconds', 5.0))
PER_PID = bool(CFG.get('enforcement', {}).get('per_pid_cgroup', True))

_last_set = {}
_running = True


def handle_sigterm(signum, frame):
    global _running
    _running = False


signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)


def load_model():
    p = Path(MODEL_PATH)
    if not p.exists():
        print('model not found:', MODEL_PATH)
        return None
    return joblib.load(MODEL_PATH)


def features_from_proc(p, load1):
    try:
        info = p.as_dict(attrs=['pid', 'name', 'username', 'cpu_percent',
                                'memory_percent', 'create_time', 'num_threads'])
    except Exception:
        return None
    cpu = float(info.get('cpu_percent') or 0.0)
    mem = float(info.get('memory_percent') or 0.0)
    threads = int(info.get('num_threads') or 0)
    proc_age = time.time() - float(info.get('create_time') or time.time())
    return [cpu, mem, threads, proc_age, load1]


def should_consider(p):
    try:
        if p.username() == 'root':
            return False
    except Exception:
        return False
    try:
        exe = p.exe() or ''
        if any(exe.startswith(w) for w in WHITELIST):
            return False
    except Exception:
        pass
    try:
        name = p.name() or ''
        if any(b in name for b in BLACKLIST):
            return True
    except Exception:
        pass
    return True


def enforce(pid, quota, dry_run=False):
    nowt = time.time()
    if nowt - _last_set.get(pid, 0) < RATE_LIMIT_SECONDS:
        return False  # not enforced this time
    try:
        if dry_run:
            print(f"[DRY] would apply quota {quota}% to pid {pid}")
        else:
            add_pid(pid)
            set_cpu_quota_for_pid(pid, quota)
            print(f"applied quota {quota}% to pid {pid}")
        _last_set[pid] = nowt
        return True
    except PermissionError:
        print(f"[WARN] Skipped pid {pid}: Permission denied for cgroup write.")
    except Exception as e:
        print(f"[WARN] Skipped pid {pid}: {e}")
    return False


def rollback_all():
    print('rolling back: removing pid cgroups (best-effort)')
    for pid in list(_last_set.keys()):
        try:
            remove_pid_group(pid)
        except Exception:
            pass


def main_loop():
    model = load_model()
    if model is None:
        print('no model — exiting')
        return

    FEATURES = ['cpu_percent', 'memory_percent', 'num_threads', 'proc_age', 'system_load1']
    global _running

    print("Daemon started — monitoring processes every", SAMPLE_INTERVAL, "seconds.")
    print("Press Ctrl + C to stop.\n")

    while _running:
        try:
            load1 = psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else 0.0
            throttled = 0
            scanned = 0

            for p in psutil.process_iter(['pid', 'username', 'cpu_percent']):
                scanned += 1
                try:
                    if not should_consider(p):
                        continue

                    cpu = p.info.get('cpu_percent') or 0.0
                    if cpu < MIN_CPU_TO_CONSIDER:
                        if p.pid in _last_set and cpu < 1.0:
                            remove_pid_group(p.pid)
                            _last_set.pop(p.pid, None)
                        continue

                    fv = features_from_proc(p, load1)
                    if fv is None:
                        continue

                    pred = model.predict(pd.DataFrame([fv], columns=FEATURES))[0]
                    quota = int(max(10, min(100, pred)))

                    if quota < 100:
                        success = enforce(p.pid, quota, dry_run=args.dry_run)
                        if success:
                            throttled += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Always print status line
            print(f"[INFO] load={load1:.2f}, scanned={scanned}, throttled={throttled}")
            time.sleep(SAMPLE_INTERVAL)

        except Exception as e:
            print(f"[WARN] daemon loop error: {e}")

    rollback_all()
    print('daemon stopped')


if __name__ == '__main__':
    main_loop()

