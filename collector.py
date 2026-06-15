import psutil, time, argparse
from utils import write_jsonl, load_config
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--config', default='config.yaml')
args = parser.parse_args()

CFG = load_config(args.config)
SAMPLE_INTERVAL = float(CFG.get("sample_interval", 1.0))
LOG_FILE = CFG.get("log_file", "samples/collected.jsonl")

print("Collector started... Press Ctrl+C to stop.")

for p in psutil.process_iter():
    try:
        p.cpu_percent(interval=None)
    except Exception:
        pass

def sample_once():
    system = {
        "ts": time.time(),
        "load1": psutil.getloadavg()[0] if hasattr(psutil, "getloadavg") else 0.0,
        "mem": psutil.virtual_memory()._asdict(),
    }
    for p in psutil.process_iter(['pid','name','username','cpu_percent','memory_percent','create_time','cpu_times','io_counters','num_threads','uids','nice','cmdline','exe']):
        try:
            info = p.info
            proc = {
                'pid': info.get('pid'),
                'name': info.get('name'),
                'exe': info.get('exe'),
                'user': info.get('username'),
                'cpu_percent': float(info.get('cpu_percent') or 0.0),
                'memory_percent': float(info.get('memory_percent') or 0.0),
                'create_time': float(info.get('create_time') or 0.0),
                'cpu_times_user': float(info.get('cpu_times').user) if info.get('cpu_times') else 0.0,
                'cpu_times_system': float(info.get('cpu_times').system) if info.get('cpu_times') else 0.0,
                'io_read_bytes': int(info.get('io_counters').read_bytes) if info.get('io_counters') else 0,
                'io_write_bytes': int(info.get('io_counters').write_bytes) if info.get('io_counters') else 0,
                'num_threads': int(info.get('num_threads') or 0),
                'nice': int(info.get('nice') or 0),
                'cmdline': info.get('cmdline') or [],
            }
            write_jsonl(LOG_FILE, {'system': system, 'proc': proc})
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

if __name__ == '__main__':
    Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
    try:
        while True:
            sample_once()
            time.sleep(SAMPLE_INTERVAL)
    except KeyboardInterrupt:
        print('collector stopped')
