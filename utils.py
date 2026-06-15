import time, os, json, yaml
from pathlib import Path

def now():
    return time.time()

def load_config(path="config.yaml"):
    p = Path(path)
    if not p.exists():
        return {}
    with open(p) as f:
        return yaml.safe_load(f)

def ensure_dir(path):
    Path(path).expanduser().mkdir(parents=True, exist_ok=True)

def write_jsonl(path, obj):
    ensure_dir(Path(path).parent)
    with open(path, "a") as f:
        f.write(json.dumps(obj) + "\n")
