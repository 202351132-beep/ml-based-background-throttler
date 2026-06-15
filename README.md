
# ML-Based Background Process Throttler

An intelligent system that uses machine learning to automatically throttle background processes based on system load and process characteristics, improving system responsiveness while maintaining performance.

## 🚀 Complete Setup & Evaluation Workflow

### Step 0: Virtual Environment Setup

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

---

### Step 1: Initial Setup (Run Once)

**Terminal 1 - Setup Environment:**

```bash
# Activate virtual environment
source .venv/bin/activate

# Prepare cgroup environment
sudo systemd-run --unit=bgthrottle-scope --scope -p "Delegate=yes" bash
echo "+cpu" > /sys/fs/cgroup/cgroup.subtree_control
mkdir -p /sys/fs/cgroup/bgthrottle
echo "+cpu" > /sys/fs/cgroup/bgthrottle/cgroup.subtree_control
chmod -R 755 /sys/fs/cgroup/bgthrottle
```

**Data Collection and Training:**

```bash
python collector.py
python labeler.py
python trainer.py
```

---

### Step 2: Performance Evaluation

#### 📊 Baseline Measurement (WITHOUT Throttler)

Terminal 1 - Ensure daemon is NOT running  
Terminal 2 - Generate Load:

```bash
source .venv/bin/activate
stress-ng --cpu 4 --timeout 20s
```

Terminal 3 - Collect Baseline Data:

```bash
source .venv/bin/activate
python create_graph.py --mode baseline --duration 20
```

Expected Output:

```
🔵 BASELINE MODE - Measuring WITHOUT Throttler
[ 19.5s] CPU: 50.5%
✓ Data saved to samples/baseline_data.txt
```

---

#### 🎯 Throttled Measurement (WITH Throttler)

**Terminal 1 - Start Daemon:**

```bash
source .venv/bin/activate
sudo .venv/bin/python3 daemon.py
```

**Terminal 2 - Generate Load:**

```bash
source .venv/bin/activate
stress-ng --cpu 4 --timeout 20s
```

**Terminal 3 - Collect Throttled Data:**

```bash
source .venv/bin/activate
python create_graph.py --mode throttled --duration 20
```

Expected Output:

```
🟢 THROTTLED MODE - Measuring WITH Throttler
[ 19.5s] CPU: 41.4%
✓ Data saved to samples/throttled_data.txt
✓ Graph saved to graph.png
```

---

### Step 3: Generate Comparison Graph

```bash
source .venv/bin/activate
python create_graph.py --mode compare
```

**Expected Results:**  
- Baseline Avg CPU: ~75% | Max: ~95%  
- Throttled Avg CPU: ~57% | Max: ~89%  
- CPU Reduction: ~23%

---

## 🔧 Virtual Environment Management

```bash
# Create and activate
python3 -m venv .venv
source .venv/bin/activate

# Deactivate when done
deactivate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Verify setup:

```bash
python -c "import psutil, pandas, sklearn; print('All imports successful')"
```

---

## ⚠️ Troubleshooting

### Common Issues & Fixes

**1️⃣ Daemon not running**
```bash
ps aux | grep daemon.py
```

**2️⃣ Incorrect cgroup setup**
```bash
ls -la /sys/fs/cgroup/bgthrottle/
```

**3️⃣ Model not found**
```bash
python -c "import joblib; joblib.load('models/bgthrottle_rf.pkl'); print('Model OK')"
```

---

## ⚙️ Configuration (config.yaml)

```yaml
model_path: "models/bgthrottle_rf.pkl"
sample_interval: 1.0
cgroup_root: "/sys/fs/cgroup/bgthrottle"

whitelist: ["/usr/bin/sshd", "/sbin/init"]
blacklist: ["stress-ng", "make", "gcc"]

enforcement:
  min_cpu_to_consider: 2.0
  rate_limit_seconds: 5.0
  per_pid_cgroup: true
```

---

## 🎯 How It Works

- **Monitoring:** Tracks running processes
- **Feature Extraction:** CPU %, Memory %, Threads, Age, Load Avg
- **ML Prediction:** Random Forest model predicts CPU quota (10–100%)
- **Enforcement:** Applies via cgroups v2 dynamically

---

## 📈 Model Training

1. Collect real-time system data → `collector.py`  
2. Label data automatically → `labeler.py`  
3. Train Random Forest → `trainer.py`

---

## 🔧 Advanced Usage

**Dry Run Mode:**
```bash
sudo python daemon.py --dry-run
```

**Custom Monitoring Duration:**
```bash
python create_graph.py --mode baseline --duration 30 --interval 0.2
```

**Manual cgroup Control:**
```python
from cgroup_control import add_pid, set_cpu_quota_for_pid
add_pid(1234)
set_cpu_quota_for_pid(1234, 50)
```

---

## 📝 License
This project is for educational and research purposes. Modify and extend freely.

## 🤝 Contributing
Contributions welcome! Submit pull requests or open issues for improvements.


## 👨‍💻 Authors
Soham Naukudkar 

Siddhikesh Gavit 

Shreyash Borkar 

📍 IIIT Vadodara – Gandhinagar Campus
