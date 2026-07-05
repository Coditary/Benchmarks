import json
import os
import csv
import sys
import subprocess
import platform
import psutil

def get_system_info():
    """Gathers detailed hardware context, distinguishing cores and threads."""
    cpu_model = "unknown"
    physical_cores = 0
    logical_threads = 0

    mem = psutil.virtual_memory()

    governor = "unknown"
    if os.path.exists("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"):
        with open("/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor", "r") as f:
            governor = f.read().strip()

    load_avg = os.getloadavg()[0]
    
    if os.path.exists("/proc/cpuinfo"):
        with open("/proc/cpuinfo", "r") as f:
            lines = f.readlines()
            # Get CPU Model Name
            for line in lines:
                if "model name" in line:
                    cpu_model = line.split(":")[1].strip()
                    break
            
            # Count logical processors (threads)
            logical_threads = len([l for l in lines if "processor" in l])
            
            # Count physical cores (unique core IDs)
            core_ids = set()
            for line in lines:
                if "core id" in line:
                    core_ids.add(line.split(":")[1].strip())
            physical_cores = len(core_ids)
            # Fallback for systems where core id is not reported
            if physical_cores == 0: physical_cores = logical_threads // 2

    return {
        "hostname": platform.node(),
        "os": f"{platform.system()} {platform.release()}",
        "cpu_model": cpu_model,
        "physical_cores": physical_cores,
        "logical_threads": logical_threads,
        "total_ram_mb": mem.total,
        "cpu_governor": governor,
        "system_load_1min": load_avg,
        "is_ci": os.getenv("CI") == "true",
        "runner_name": os.getenv("RUNNER_NAME", "local")
    }

def get_git_hash():
    """Retrieve the current short git hash for reproducibility."""
    try:
        return subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD']).decode('ascii').strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"

def collect_data(target_dirs):
    """Aggregates all benchmark artifacts into a unified report.json."""
    report = []
    git_hash = get_git_hash()
    
    for dir_path in target_dirs:
        # Define paths
        meta_path = os.path.join(dir_path, "metadata.json")
        metrics_path = os.path.join(dir_path, "artifacts", "metrics.json")
        csv_path = os.path.join(dir_path, "artifacts", "results.csv")
        
        # 1. Read metadata
        with open(meta_path, 'r') as f:
            meta = json.load(f)
        
        # 2. Read metrics
        metrics = {}
        if os.path.exists(metrics_path):
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
        
        # 3. Parse Hyperfine CSV results
        hyperfine_data = []
        if os.path.exists(csv_path):
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                hyperfine_data = [row for row in reader]
        
        # 4. Construct the result object
        # Expected structure: benchmarks/domain/test/lang/impl
        parts = dir_path.split(os.sep)
        
        result = {
            'domain': parts[1] if len(parts) > 1 else "unknown",
            'test': parts[2] if len(parts) > 2 else "unknown",
            'lang': parts[3] if len(parts) > 3 else "unknown",
            'impl': parts[4] if len(parts) > 4 else "unknown",
            'git_hash': git_hash,
            'tags': meta.get('tags', []),
            'notes': meta.get('notes', ''),
            'env': get_system_info(),
            'metrics': {
                'lines_of_code': metrics.get('lines_of_code', 0),
                'artifact_size_bytes': metrics.get('artifact_size_bytes', 0),
                'build_time_ms': round(metrics.get('build_time_seconds', 0) * 1000, 4),
                'hyperfine_results': hyperfine_data
            }
        }
        report.append(result)

    # Write the unified report
    with open("report.json", "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"✔ Successfully aggregated {len(report)} benchmarks into report.json")

if __name__ == "__main__":
    # sys.argv[1:] contains the list of paths passed from the bash wrapper
    collect_data(sys.argv[1:])
