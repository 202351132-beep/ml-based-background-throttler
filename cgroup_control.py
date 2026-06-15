import os, shutil
from pathlib import Path

CGROUP_ROOT = '/sys/fs/cgroup/bgthrottle'
PERIOD = 100000  # 100ms

def ensure_root(root=CGROUP_ROOT):
    Path(root).mkdir(parents=True, exist_ok=True)

def pid_cgroup_path(pid, root=CGROUP_ROOT):
    return Path(root) / f'pid_{pid}'

def ensure_pid_group(pid, root=CGROUP_ROOT):
    ensure_root(root)
    p = pid_cgroup_path(pid, root)
    if not p.exists():
        p.mkdir(parents=True, exist_ok=True)
    return p

def add_pid(pid, root=CGROUP_ROOT):
    p = ensure_pid_group(pid, root)
    with open(p / 'cgroup.procs', 'w') as f:
        f.write(str(int(pid)))

def set_cpu_quota_for_pid(pid, percent, root=CGROUP_ROOT):
    p = ensure_pid_group(pid, root)
    cpu_max = p / 'cpu.max'
    val = 'max' if percent >= 100 else f"{int(max(1, (percent * PERIOD) / 100.0))} {PERIOD}"
    with open(cpu_max, 'w') as f:
        f.write(val)

def remove_pid_group(pid, root=CGROUP_ROOT):
    p = pid_cgroup_path(pid, root)
    try:
        procs = p / 'cgroup.procs'
        if procs.exists():
            with open(procs) as f:
                lines = f.read().strip().splitlines()
            root_procs = Path(root) / 'cgroup.procs'
            for line in lines:
                if line.strip():
                    with open(root_procs, 'w') as rf:
                        rf.write(line.strip())
        shutil.rmtree(p, ignore_errors=True)
    except Exception:
        pass
