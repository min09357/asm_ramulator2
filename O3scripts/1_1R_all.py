#!/usr/bin/env python3
import argparse
import concurrent.futures
import io
import os
import re
import subprocess
import sys
import threading

os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

NUM_EXPECTED_INSTS = 500000

NUMCORES = 4
NUMBUBBLES = 1

FRONTEND_RATIO = 8
MEMORYSYSTEM_RATIO = 3

SHUFFLE_CORES = "true"

LLC_PER_CORE = "8MB"
LLC_ASSOCIATIVITY = 8
MSHR_PER_CORE = 64
INST_WINDOW_DEPTH = 128
READ_BUFFER_SIZE = 64

ROW_POLICY = "OpenRowPolicy"

CONTROLLER = "PerRank"
REFRESH = "PerRank"

# CONTROLLER = "Generic"
# REFRESH = "AllBank"

# Sweep configurations
DDR_CONFIGS = [
    # (DDR_GEN, TRANSFER_RATE, CHIP_SIZE, DQ, RAS, RP)
    (4, "2933Y", 8, 4, 47, 21),
    (5, "4800B", 16, 8, 77, 39),
    (5, "5600B", 16, 8, 90, 45),
]
RANKS = [1, 2]
TRACES = ["Rowhit", "Rowmiss", "Random"]
# TRACES = ["Rowhit"]

# Metrics to collect from ramulator2 stdout. Each item is matched as a line
# of the form "<key>: <value>" (value is the first token after the colon).
METRICS = [
    "bandwidth_utilization (%)",
    "dram_hit_rate_0 (%)",
    "llc_hit_rate (%)",
]


_print_lock = threading.Lock()
_done_count = 0
_total_count = 0


def _progress(msg):
    with _print_lock:
        sys.stdout.write(msg + "\n")
        sys.stdout.flush()


def _bump_done():
    global _done_count
    with _print_lock:
        _done_count += 1
        return _done_count, _total_count


def run_one(idx, ddr_gen, transfer_rate, chip_size, dq, ras, rp, rank, trace):
    timing_preset = f"DDR{ddr_gen}_{transfer_rate}"
    dram_org_preset = f"DDR{ddr_gen}_{chip_size}Gb_x{dq}"
    yaml_path = f"./yaml/DDR{ddr_gen}.yaml"
    trace_dir = f"./traces/SimpleO3/{timing_preset}_{rank}Rx{dq}/{trace}/{NUMCORES}cores/{NUMBUBBLES}bubbles"
    rc = ras + rp
    label = f"DDR{ddr_gen} {transfer_rate} {chip_size}Gb x{dq}  rank={rank}  trace={trace}"

    cmd = ["./ramulator2", "-f", yaml_path,
           "-p", f"Frontend.num_expected_insts={NUM_EXPECTED_INSTS}"]

    for i in range(NUMCORES):
        cmd += ["-p", f"Frontend.traces[{i}]={trace_dir}/core{i}.trace"]

    cmd += [
        "-p", f"MemorySystem.DRAM.org.preset={dram_org_preset}",
        "-p", f"MemorySystem.DRAM.timing.preset={timing_preset}",
        "-p", f"MemorySystem.DRAM.timing.nRAS={ras}",
        "-p", f"MemorySystem.DRAM.timing.nRP={rp}",
        "-p", f"MemorySystem.DRAM.timing.nRC={rc}",
        "-p", f"Frontend.shuffle_cores={SHUFFLE_CORES}",
        "-p", f"Frontend.clock_ratio={FRONTEND_RATIO}",
        "-p", f"MemorySystem.clock_ratio={MEMORYSYSTEM_RATIO}",
        "-p", f"MemorySystem.Controller.impl={CONTROLLER}",
        "-p", f"MemorySystem.Controller.RefreshManager.impl={REFRESH}",
        "-p", f"MemorySystem.DRAM.org.rank={rank}",
        "-p", f"MemorySystem.Controller.RowPolicy.impl={ROW_POLICY}",
        "-p", f"MemorySystem.Controller.read_buffer_size={READ_BUFFER_SIZE}",
        "-p", f"Frontend.llc_capacity_per_core={LLC_PER_CORE}",
        "-p", f"Frontend.llc_associativity={LLC_ASSOCIATIVITY}",
        "-p", f"Frontend.llc_num_mshr_per_core={MSHR_PER_CORE}",
        "-p", f"Frontend.inst_window_depth={INST_WINDOW_DEPTH}",
    ]

    _progress(f"[START] {label}")

    buf = io.StringIO()
    buf.write("-" * 56 + "\n")
    buf.write(f"[RUN] {label}\n")
    buf.write(" ".join(cmd) + "\n")
    buf.write("-" * 56 + "\n")

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    buf.write(result.stdout)

    values = {}
    if result.returncode == 0:
        for key in METRICS:
            pat = r"^\s*" + re.escape(key) + r":\s*(\S+)"
            m = re.search(pat, result.stdout, re.MULTILINE)
            if m:
                values[key] = m.group(1)

    bw_disp = values.get("bandwidth_utilization (%)", "N/A")
    done, total = _bump_done()
    buf.write(f"[PROGRESS] {done}/{total} complete\n")
    _progress(f"[DONE]  {label}  bw={bw_disp}  ({done}/{total})"
              + (f"  (returncode={result.returncode})" if result.returncode != 0 else ""))

    return idx, label, buf.getvalue(), values, result.returncode


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-j", "--jobs", type=int, default=None,
                        help="parallel workers (default: $JOBS or cpu_count())")
    args = parser.parse_args()
    jobs = args.jobs or int(os.environ.get("JOBS", 0)) or (os.cpu_count() or 1)

    tasks = []
    for ddr in DDR_CONFIGS:
        for rank in RANKS:
            for trace in TRACES:
                tasks.append((*ddr, rank, trace))
    total = len(tasks)
    results = [{} for _ in range(total)]
    global _total_count
    _total_count = total

    print(f"[INFO] {total} runs, jobs={jobs}", flush=True)

    fail_rc = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as ex:
        futs = [ex.submit(run_one, i, *t) for i, t in enumerate(tasks)]
        for fut in concurrent.futures.as_completed(futs):
            idx, label, stdout_block, values, rc = fut.result()
            with _print_lock:
                sys.stdout.write(stdout_block)
                sys.stdout.flush()
            results[idx] = values
            if rc != 0 and fail_rc == 0:
                fail_rc = rc
                for f in futs:
                    f.cancel()

    print("-" * 56)
    for key in METRICS:
        row = []
        for r in results:
            v = r.get(key)
            if v is None:
                row.append("NaN")
            else:
                try:
                    row.append(f"{round(float(v), 3)}")
                except ValueError:
                    row.append(v)
        print(f"{key}: {','.join(row)}")

    sys.exit(fail_rc)


if __name__ == "__main__":
    main()
