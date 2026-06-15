import matplotlib.pyplot as plt
import psutil
import time
import argparse
from pathlib import Path
from utils import load_config

parser = argparse.ArgumentParser(description='Generate CPU utilization comparison graph')
parser.add_argument('--config', default='config.yaml', help='Config file path')
parser.add_argument('--duration', type=int, default=20, help='Monitoring duration in seconds')
parser.add_argument('--interval', type=float, default=0.5, help='Sampling interval in seconds')
parser.add_argument('--output', default='graph.png', help='Output graph filename')
parser.add_argument('--baseline', default='samples/baseline_data.txt', help='Baseline data file (without throttler)')
parser.add_argument('--mode', choices=['baseline', 'throttled', 'compare'], default='compare',
                    help='Mode: baseline (save without throttler), throttled (measure with throttler), compare (load and compare)')
args = parser.parse_args()

CFG = load_config(args.config)

def collect_cpu_data(duration, interval):
    """Collect CPU utilization data over time"""
    time_points = []
    cpu_values = []
    
    print(f"\n{'='*50}")
    print(f"Collecting CPU data for {duration} seconds...")
    print(f"Sampling interval: {interval}s")
    print(f"{'='*50}\n")
    
    # Initial CPU reading to initialize
    psutil.cpu_percent(interval=None)
    time.sleep(0.1)
    
    start_time = time.time()
    
    while time.time() - start_time < duration:
        elapsed = time.time() - start_time
        cpu_percent = psutil.cpu_percent(interval=None)
        
        time_points.append(elapsed)
        cpu_values.append(cpu_percent)
        
        print(f"[{elapsed:5.1f}s] CPU: {cpu_percent:5.1f}%", end='\r')
        
        # Sleep for interval
        time.sleep(interval)
    
    print(f"\n\nCollection complete! Collected {len(time_points)} data points.")
    return time_points, cpu_values

def save_data(filename, time_points, cpu_values):
    """Save collected data to file"""
    Path(filename).parent.mkdir(parents=True, exist_ok=True)
    with open(filename, 'w') as f:
        f.write("time,cpu\n")
        for t, c in zip(time_points, cpu_values):
            f.write(f"{t:.2f},{c:.2f}\n")
    print(f"\n✓ Data saved to {filename}")

def load_data(filename):
    """Load data from file"""
    time_points = []
    cpu_values = []
    
    if not Path(filename).exists():
        return None, None
    
    with open(filename, 'r') as f:
        lines = f.readlines()[1:]  # Skip header
        for line in lines:
            parts = line.strip().split(',')
            if len(parts) == 2:
                time_points.append(float(parts[0]))
                cpu_values.append(float(parts[1]))
    
    return time_points, cpu_values

def plot_comparison(time_without, cpu_without, time_with, cpu_with, output_file):
    """Create comparison plot"""
    plt.figure(figsize=(10, 6))
    
    if time_without and cpu_without:
        plt.plot(time_without, cpu_without, label="Without Throttler", 
                linewidth=2.5, linestyle='--', marker='o', markersize=3, alpha=0.8)
    
    if time_with and cpu_with:
        plt.plot(time_with, cpu_with, label="With Throttler", 
                linewidth=2.5, marker='s', markersize=3, alpha=0.8)
    
    plt.title("CPU Utilization Over Time", fontsize=16, fontweight='bold')
    plt.xlabel("Time (seconds)", fontsize=13)
    plt.ylabel("CPU Utilization (%)", fontsize=13)
    plt.legend(fontsize=12, loc='best')
    plt.grid(True, linestyle="--", alpha=0.4)
    plt.ylim(0, 105)
    
    # Add statistics box if both datasets exist
    if cpu_without and cpu_with:
        avg_without = sum(cpu_without) / len(cpu_without)
        avg_with = sum(cpu_with) / len(cpu_with)
        max_without = max(cpu_without)
        max_with = max(cpu_with)
        reduction = ((avg_without - avg_with) / avg_without * 100) if avg_without > 0 else 0
        
        stats_text = f"Statistics:\n"
        stats_text += f"─────────────────────\n"
        stats_text += f"Without Throttler:\n"
        stats_text += f"  Avg: {avg_without:.1f}%  Max: {max_without:.1f}%\n\n"
        stats_text += f"With Throttler:\n"
        stats_text += f"  Avg: {avg_with:.1f}%  Max: {max_with:.1f}%\n\n"
        stats_text += f"CPU Reduction: {reduction:.1f}%"
        
        plt.text(0.98, 0.97, stats_text, transform=plt.gca().transAxes,
                fontsize=9, verticalalignment='top', horizontalalignment='right',
                bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.7),
                family='monospace')
    
    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"\n✓ Graph saved to {output_file}")
    
    # Try to display the graph
    try:
        plt.show()
    except:
        print("  (Unable to display graph - saved to file only)")

def print_instructions():
    """Print workflow instructions"""
    print("\n" + "="*60)
    print("   ML-Based Background Process Throttler - Graph Generator")
    print("="*60)
    print("\nWORKFLOW:")
    print("─────────")
    print("\n1. BASELINE (Without Throttler):")
    print("   Terminal 1: (daemon should NOT be running)")
    print("   Terminal 2: stress-ng --cpu 4 --timeout 20s")
    print("   Terminal 3: python create_graph.py --mode baseline")
    print("\n2. THROTTLED (With Throttler):")
    print("   Terminal 1: sudo python daemon.py (should be running)")
    print("   Terminal 2: stress-ng --cpu 4 --timeout 20s")
    print("   Terminal 3: python create_graph.py --mode throttled")
    print("\n3. COMPARE (Generate graph from saved data):")
    print("   python create_graph.py --mode compare")
    print("\n" + "="*60 + "\n")

def main():
    if args.mode == 'baseline':
        print_instructions()
        print("\n🔵 BASELINE MODE - Measuring WITHOUT Throttler")
        print("─────────────────────────────────────────────────")
        print("⚠️  IMPORTANT: Make sure daemon.py is NOT running!")
        print("⚠️  Start stress-ng in another terminal NOW\n")
        
        input("Press ENTER when stress-ng is ready to start... ")
        
        time_points, cpu_values = collect_cpu_data(args.duration, args.interval)
        save_data(args.baseline, time_points, cpu_values)
        
        avg_cpu = sum(cpu_values) / len(cpu_values)
        max_cpu = max(cpu_values)
        print(f"\nBaseline Results: Avg CPU = {avg_cpu:.1f}%, Max CPU = {max_cpu:.1f}%")
        print("\n" + "─"*60)
        print("NEXT STEP:")
        print("1. Start daemon: sudo python daemon.py")
        print("2. Run: python create_graph.py --mode throttled")
        print("─"*60 + "\n")
        
    elif args.mode == 'throttled':
        print_instructions()
        print("\n🟢 THROTTLED MODE - Measuring WITH Throttler")
        print("─────────────────────────────────────────────────")
        print("⚠️  IMPORTANT: Make sure daemon.py IS running!")
        print("⚠️  Start stress-ng in another terminal NOW\n")
        
        input("Press ENTER when stress-ng is ready to start... ")
        
        time_points, cpu_values = collect_cpu_data(args.duration, args.interval)
        throttled_file = args.baseline.replace('baseline', 'throttled')
        save_data(throttled_file, time_points, cpu_values)
        
        avg_cpu = sum(cpu_values) / len(cpu_values)
        max_cpu = max(cpu_values)
        print(f"\nThrottled Results: Avg CPU = {avg_cpu:.1f}%, Max CPU = {max_cpu:.1f}%")
        
        # Load baseline and create comparison
        time_baseline, cpu_baseline = load_data(args.baseline)
        if time_baseline and cpu_baseline:
            print("\n" + "─"*60)
            print("Creating comparison graph...")
            print("─"*60)
            plot_comparison(time_baseline, cpu_baseline, time_points, cpu_values, args.output)
            print("\n✅ Complete! Check graph.png for results.")
        else:
            print(f"\n⚠️  Baseline data not found at {args.baseline}")
            print("Run with --mode baseline first.")
            
    elif args.mode == 'compare':
        print("\n🔄 COMPARE MODE - Regenerating graph from saved data")
        print("─────────────────────────────────────────────────────\n")
        
        # Load both datasets
        time_baseline, cpu_baseline = load_data(args.baseline)
        throttled_file = args.baseline.replace('baseline', 'throttled')
        time_throttled, cpu_throttled = load_data(throttled_file)
        
        if not (time_baseline and cpu_baseline):
            print(f"❌ Baseline data not found at {args.baseline}")
            print("\nRun: python create_graph.py --mode baseline")
            print_instructions()
            return
        
        if not (time_throttled and cpu_throttled):
            print(f"❌ Throttled data not found at {throttled_file}")
            print("\nRun: python create_graph.py --mode throttled")
            print_instructions()
            return
        
        print(f"✓ Loaded baseline data: {len(cpu_baseline)} points")
        print(f"✓ Loaded throttled data: {len(cpu_throttled)} points\n")
        
        plot_comparison(time_baseline, cpu_baseline, time_throttled, cpu_throttled, args.output)
        print("\n✅ Graph regenerated successfully!")

if __name__ == '__main__':
    main()
