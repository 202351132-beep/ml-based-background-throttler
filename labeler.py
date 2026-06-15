import json, csv, argparse
from pathlib import Path
from utils import load_config

parser = argparse.ArgumentParser()
parser.add_argument('--config', default='config.yaml')
args = parser.parse_args()

CFG = load_config(args.config)
LOG_FILE = CFG.get('log_file', 'samples/collected.jsonl')
LABELED_CSV = CFG.get('labeled_csv', 'samples/labeled_samples.csv')

BACKGROUND_CPU_THRESHOLD = 10.0
SYSTEM_LOAD_MULT = 0.5
WHITELIST_CMD = set(['sshd', 'init', 'systemd'])

def is_background(cmdline, username):
    if username == 'root':
        return False
    if not cmdline or len(cmdline) == 0:
        return True
    if any(x in ' '.join(cmdline).lower() for x in ['gnome', 'chrome', 'firefox', 'code']):
        return False
    return True

def label_line(entry):
    proc = entry['proc']
    sys = entry['system']
    load1 = sys.get('load1', 0.0)
    cpu = proc.get('cpu_percent', 0.0)
    name = proc.get('name','') or ''
    user = proc.get('user','') or ''
    if name in WHITELIST_CMD:
        return 100
    if is_background(proc.get('cmdline'), user) and cpu >= BACKGROUND_CPU_THRESHOLD and load1 >= SYSTEM_LOAD_MULT:
        return 30
    return 100

def run():
    Path(LABELED_CSV).parent.mkdir(parents=True, exist_ok=True)
    with open(LABELED_CSV, 'w', newline='') as csvf:
        writer = csv.writer(csvf)
        header = ['ts','pid','name','exe','user','cpu_percent','memory_percent','num_threads','proc_age','system_load1','label_quota']
        writer.writerow(header)
        with open(LOG_FILE) as f:
            for line in f:
                try:
                    entry = json.loads(line)
                    proc = entry['proc']
                    sys = entry['system']
                    ts = sys['ts']
                    proc_age = ts - proc.get('create_time', ts)
                    label = label_line(entry)
                    row = [ts, proc.get('pid'), proc.get('name'), proc.get('exe'), proc.get('user'), proc.get('cpu_percent'), proc.get('memory_percent'), proc.get('num_threads'), proc_age, sys.get('load1'), label]
                    writer.writerow(row)
                except Exception:
                    continue

if __name__ == '__main__':
    run()
