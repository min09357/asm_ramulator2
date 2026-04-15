#!/usr/bin/env python3
"""
SimpleO3 Trace Generator
Generates per-core memory traces for Ramulator2 SimpleO3 frontend.

Address mapping : ChRaBaRoCo (physical addresses, NoTranslation)
Output format   : <NUM_BUBBLES> <load_addr>  (decimal, one per line)
Output path     : ./{chip_type}/{trace_type}/{num_cores}cores/{NUM_BUBBLES}bubbles/core{N}.trace  (relative to this file)
"""

from itertools import product
from pathlib import Path
import shutil
import random

# ============================================================
# Level index constants
# ============================================================
CH, RA, BG, BA, RO, CO = range(6)
_LEVELS = [CH, RA, BG, BA, RO, CO]

# ============================================================
# Trace type constants
# ============================================================
ROW_HIT  = "ROW_HIT"
ROW_MISS = "ROW_MISS"
RANDOM   = "RANDOM"

# ============================================================
# User-configurable settings
# ============================================================

NUM_ROW           = 1 << 9   # Number of rows to use per config (sweep range)
NUM_CORES_LIST    = [1, 2, 4, 8]        # Sweep values for number of cores
NUM_BUBBLES_LIST  = [0, 1, 2]     # Sweep values for non-memory instructions inserted before each access
RANDOM_SEED       = 42

# TX_OFFSET = log2(transaction bytes)
# DDR4: prefetch=8,  channel_width=64 bit  →  8*64/8 = 64 B = 2^6
# DDR5: prefetch=16, channel_width=32 bit  → 16*32/8 = 64 B = 2^6
TX_OFFSET = 6

# Address mapping order (MSB → LSB)
ChRaBaRoCo = [CH, RA, BG, BA, RO, CO]
RoBaRaCoCh = [RO, BA, BG, RA, CO, CH]

# ADDR_ORDER = ChRaBaRoCo
ADDR_ORDER = RoBaRaCoCh

# Sweep order for the bank-level dimensions in ROW_HIT / ROW_MISS
# Listed innermost → outermost (innermost = fastest-changing).
# Reorder freely, e.g. [BA, BG, RA, CH] to make BA the fastest-changing dimension.
BANK_ORDER = [CH, RA, BG, BA]

# ============================================================
# Address bit-width presets (chip organization → bits per level)
#
# These specify how many bits each level occupies in the physical address.
# Independent of level_counts (sweep range) — e.g. sweeping only 2 banks
# still requires 2 bits for BA if the chip has 4 banks.
#
# CO bits are the effective (prefetch-reduced) column bits:
#   DDR4 x4/x8 : raw 2^10 col / prefetch 8  = 2^7  → CO: 7
#   DDR5 x4    : raw 2^11 col / prefetch 16 = 2^7  → CO: 7
#   DDR5 x8    : raw 2^10 col / prefetch 16 = 2^6  → CO: 6
# ============================================================
BITS_DDR4_1Rx4 = {CH: 0, RA: 0, BG: 2, BA: 2, RO: 17, CO: 7}
BITS_DDR4_2Rx4 = {CH: 0, RA: 1, BG: 2, BA: 2, RO: 17, CO: 7}
BITS_DDR5_1Rx4 = {CH: 1, RA: 0, BG: 3, BA: 2, RO: 16, CO: 7}
BITS_DDR5_2Rx4 = {CH: 1, RA: 1, BG: 3, BA: 2, RO: 16, CO: 7}
BITS_DDR5_1Rx8 = {CH: 1, RA: 0, BG: 3, BA: 2, RO: 16, CO: 6}
BITS_DDR5_2Rx8 = {CH: 1, RA: 1, BG: 3, BA: 2, RO: 16, CO: 6}

# ============================================================
# Configs  (add entries below)
#
# Format: (chip_name, trace_name, level_counts, addr_bits, trace_type)
#   chip_name   : top-level output directory  (e.g. "DDR4_2933Y_1Rx4")
#   trace_name  : second-level output directory  (e.g. "Rowhit")
#   level_counts: {CH:…, RA:…, BG:…, BA:…, RO:…, CO:…}  ← sweep range
#   addr_bits   : {CH:…, RA:…, BG:…, BA:…, RO:…, CO:…}  ← bits per level in physical address
#   trace_type  : ROW_HIT | ROW_MISS | RANDOM
#
# num_cores and num_bubbles are swept via NUM_CORES_LIST / NUM_BUBBLES_LIST.
# ============================================================
configs = [
    ("DDR4_2933Y_1Rx4", "Rowhit",  {CH:1, RA:1, BG:4, BA:4, RO:NUM_ROW, CO:1<<7}, BITS_DDR4_1Rx4, ROW_HIT),
    ("DDR4_2933Y_1Rx4", "Rowmiss", {CH:1, RA:1, BG:4, BA:4, RO:NUM_ROW, CO:1<<7}, BITS_DDR4_1Rx4, ROW_MISS),
    ("DDR4_2933Y_1Rx4", "Random",  {CH:1, RA:1, BG:4, BA:4, RO:NUM_ROW, CO:1<<7}, BITS_DDR4_1Rx4, RANDOM),

    ("DDR4_2933Y_2Rx4", "Rowhit",  {CH:1, RA:2, BG:4, BA:4, RO:NUM_ROW, CO:1<<7}, BITS_DDR4_2Rx4, ROW_HIT),
    ("DDR4_2933Y_2Rx4", "Rowmiss", {CH:1, RA:2, BG:4, BA:4, RO:NUM_ROW, CO:1<<7}, BITS_DDR4_2Rx4, ROW_MISS),
    ("DDR4_2933Y_2Rx4", "Random",  {CH:1, RA:2, BG:4, BA:4, RO:NUM_ROW, CO:1<<7}, BITS_DDR4_2Rx4, RANDOM),


    ("DDR5_4800B_1Rx4", "Rowhit",      {CH:2, RA:1, BG:8, BA:4, RO:NUM_ROW, CO:1<<7}, BITS_DDR5_1Rx4, ROW_HIT),
    ("DDR5_4800B_1Rx4", "Rowmiss",     {CH:2, RA:1, BG:8, BA:4, RO:NUM_ROW, CO:1<<7}, BITS_DDR5_1Rx4, ROW_MISS),
    ("DDR5_4800B_1Rx4", "Random",      {CH:2, RA:1, BG:8, BA:4, RO:NUM_ROW, CO:1<<7}, BITS_DDR5_1Rx4, RANDOM),
    ("DDR5_4800B_1Rx4", "Rowmiss_BA2", {CH:2, RA:1, BG:8, BA:2, RO:NUM_ROW, CO:1<<7}, BITS_DDR5_1Rx4, ROW_MISS),
    ("DDR5_4800B_1Rx4", "Rowmiss_BA1", {CH:2, RA:1, BG:8, BA:1, RO:NUM_ROW, CO:1<<7}, BITS_DDR5_1Rx4, ROW_MISS),

    ("DDR5_4800B_2Rx4", "Rowhit",      {CH:2, RA:2, BG:8, BA:4, RO:NUM_ROW, CO:1<<7}, BITS_DDR5_2Rx4, ROW_HIT),
    ("DDR5_4800B_2Rx4", "Rowmiss",     {CH:2, RA:2, BG:8, BA:4, RO:NUM_ROW, CO:1<<7}, BITS_DDR5_2Rx4, ROW_MISS),
    ("DDR5_4800B_2Rx4", "Random",      {CH:2, RA:2, BG:8, BA:4, RO:NUM_ROW, CO:1<<7}, BITS_DDR5_2Rx4, RANDOM),
    ("DDR5_4800B_2Rx4", "Rowmiss_BA2", {CH:2, RA:2, BG:8, BA:2, RO:NUM_ROW, CO:1<<7}, BITS_DDR5_2Rx4, ROW_MISS),
    ("DDR5_4800B_2Rx4", "Rowmiss_BA1", {CH:2, RA:2, BG:8, BA:1, RO:NUM_ROW, CO:1<<7}, BITS_DDR5_2Rx4, ROW_MISS),


    ("DDR5_4800B_1Rx8", "Rowhit",      {CH:2, RA:1, BG:8, BA:4, RO:NUM_ROW, CO:1<<6}, BITS_DDR5_1Rx8, ROW_HIT),
    ("DDR5_4800B_1Rx8", "Rowmiss",     {CH:2, RA:1, BG:8, BA:4, RO:NUM_ROW, CO:1<<6}, BITS_DDR5_1Rx8, ROW_MISS),
    ("DDR5_4800B_1Rx8", "Random",      {CH:2, RA:1, BG:8, BA:4, RO:NUM_ROW, CO:1<<6}, BITS_DDR5_1Rx8, RANDOM),
    ("DDR5_4800B_1Rx8", "Rowmiss_BA2", {CH:2, RA:1, BG:8, BA:2, RO:NUM_ROW, CO:1<<6}, BITS_DDR5_1Rx8, ROW_MISS),
    ("DDR5_4800B_1Rx8", "Rowmiss_BA1", {CH:2, RA:1, BG:8, BA:1, RO:NUM_ROW, CO:1<<6}, BITS_DDR5_1Rx8, ROW_MISS),

    ("DDR5_4800B_2Rx8", "Rowhit",      {CH:2, RA:2, BG:8, BA:4, RO:NUM_ROW, CO:1<<6}, BITS_DDR5_2Rx8, ROW_HIT),
    ("DDR5_4800B_2Rx8", "Rowmiss",     {CH:2, RA:2, BG:8, BA:4, RO:NUM_ROW, CO:1<<6}, BITS_DDR5_2Rx8, ROW_MISS),
    ("DDR5_4800B_2Rx8", "Random",      {CH:2, RA:2, BG:8, BA:4, RO:NUM_ROW, CO:1<<6}, BITS_DDR5_2Rx8, RANDOM),
    ("DDR5_4800B_2Rx8", "Rowmiss_BA2", {CH:2, RA:2, BG:8, BA:2, RO:NUM_ROW, CO:1<<6}, BITS_DDR5_2Rx8, ROW_MISS),
    ("DDR5_4800B_2Rx8", "Rowmiss_BA1", {CH:2, RA:2, BG:8, BA:1, RO:NUM_ROW, CO:1<<6}, BITS_DDR5_2Rx8, ROW_MISS),


    ("DDR5_5600B_1Rx8", "Rowhit",      {CH:2, RA:1, BG:8, BA:4, RO:NUM_ROW, CO:1<<6}, BITS_DDR5_1Rx8, ROW_HIT),
    ("DDR5_5600B_1Rx8", "Rowmiss",     {CH:2, RA:1, BG:8, BA:4, RO:NUM_ROW, CO:1<<6}, BITS_DDR5_1Rx8, ROW_MISS),
    ("DDR5_5600B_1Rx8", "Random",      {CH:2, RA:1, BG:8, BA:4, RO:NUM_ROW, CO:1<<6}, BITS_DDR5_1Rx8, RANDOM),
    ("DDR5_5600B_1Rx8", "Rowmiss_BA2", {CH:2, RA:1, BG:8, BA:2, RO:NUM_ROW, CO:1<<6}, BITS_DDR5_1Rx8, ROW_MISS),
    ("DDR5_5600B_1Rx8", "Rowmiss_BA1", {CH:2, RA:1, BG:8, BA:1, RO:NUM_ROW, CO:1<<6}, BITS_DDR5_1Rx8, ROW_MISS),

    ("DDR5_5600B_2Rx8", "Rowhit",      {CH:2, RA:2, BG:8, BA:4, RO:NUM_ROW, CO:1<<6}, BITS_DDR5_2Rx8, ROW_HIT),
    ("DDR5_5600B_2Rx8", "Rowmiss",     {CH:2, RA:2, BG:8, BA:4, RO:NUM_ROW, CO:1<<6}, BITS_DDR5_2Rx8, ROW_MISS),
    ("DDR5_5600B_2Rx8", "Random",      {CH:2, RA:2, BG:8, BA:4, RO:NUM_ROW, CO:1<<6}, BITS_DDR5_2Rx8, RANDOM),
    ("DDR5_5600B_2Rx8", "Rowmiss_BA2", {CH:2, RA:2, BG:8, BA:2, RO:NUM_ROW, CO:1<<6}, BITS_DDR5_2Rx8, ROW_MISS),
    ("DDR5_5600B_2Rx8", "Rowmiss_BA1", {CH:2, RA:2, BG:8, BA:1, RO:NUM_ROW, CO:1<<6}, BITS_DDR5_2Rx8, ROW_MISS),
]


# ============================================================
# Internal helpers
# ============================================================

def _bits_list(addr_bits: dict) -> list:
    """Convert addr_bits dict to an ordered list [CH, RA, BG, BA, RO, CO]."""
    return [addr_bits[lvl] for lvl in _LEVELS]


def _compute_addr(addr_vec: list, bits: list) -> int:
    """
    Shift-and-or each level in ADDR_ORDER (MSB→LSB), then append TX_OFFSET zero bits.
    addr_vec and bits are indexed 0=CH … 5=CO.
    """
    addr = 0
    for i in ADDR_ORDER:
        addr = (addr << bits[i]) | addr_vec[i]
    return addr << TX_OFFSET


def _core_row_range(core_id: int, total_rows: int, num_cores: int):
    """Return (ro_start, rows_per_core); remainder rows are discarded."""
    rows_per_core = total_rows // num_cores
    return core_id * rows_per_core, rows_per_core


# ============================================================
# Address generators
# ============================================================

def _sweep_order(trace_type: str) -> list:
    """
    Innermost(fastest) → outermost(slowest) sweep order.
      ROW_HIT  : BANK_ORDER + [CO, RO]  →  banks fastest, CO before RO → row hit
      ROW_MISS : BANK_ORDER + [RO, CO]  →  banks fastest, RO before CO → row miss
    """
    if trace_type == ROW_HIT:
        return BANK_ORDER + [CO, RO]
    else:
        return BANK_ORDER + [RO, CO]


def _gen_sequential(level_counts: dict, addr_bits: dict,
                    trace_type: str, ro_start: int, ro_count: int):
    """Yield physical addresses in deterministic sweep order."""
    bits  = _bits_list(addr_bits)
    order = _sweep_order(trace_type)

    ranges = [
        range(ro_start, ro_start + ro_count) if lvl == RO else range(level_counts[lvl])
        for lvl in order
    ]

    # product expects outermost(slowest) first → reverse since order is innermost-first
    rev_order  = order[::-1]
    rev_ranges = ranges[::-1]

    for values in product(*rev_ranges):
        level_to_val = dict(zip(rev_order, values))
        addr_vec = [level_to_val[lvl] for lvl in _LEVELS]
        yield _compute_addr(addr_vec, bits)


def _gen_random(level_counts: dict, addr_bits: dict) -> list:
    """
    Return a list of physical addresses covering the entire address space
    exactly once, in a random (shuffled) order.
    """
    bits = _bits_list(addr_bits)

    eff = [level_counts[lvl] for lvl in _LEVELS]
    total = 1
    for c in eff:
        total *= c

    indices = list(range(total))
    random.Random(RANDOM_SEED).shuffle(indices)
    random.Random(RANDOM_SEED+1).shuffle(indices)
    random.Random(RANDOM_SEED+2).shuffle(indices)

    addrs = []
    for idx in indices:
        addr_vec = [0] * 6
        remaining = idx
        for lvl in reversed(_LEVELS):
            addr_vec[lvl]  = remaining % eff[lvl]
            remaining     //= eff[lvl]
        addrs.append(_compute_addr(addr_vec, bits))
    return addrs


# ============================================================
# Trace writer
# ============================================================

def _write_trace(out_path: Path, addr_gen, num_bubbles: int) -> int:
    count = 0
    with out_path.open("w", encoding="ascii") as f:
        for addr in addr_gen:
            f.write(f"{num_bubbles} {addr}\n")
            count += 1
    return count


# ============================================================
# Main
# ============================================================

def main():
    script_dir  = Path(__file__).parent
    total_files = sum(NUM_CORES_LIST) * len(NUM_BUBBLES_LIST) * len(configs)
    done        = 0

    for num_cores in NUM_CORES_LIST:
        for chip_name, trace_name, level_counts, addr_bits, trace_type in configs:
            ro_total = level_counts[RO]

            # Address generation is independent of num_bubbles, so build once per (num_cores, config)
            # and reuse across every num_bubbles value.
            if trace_type == RANDOM:
                all_addrs  = _gen_random(level_counts, addr_bits)
                chunk_size = len(all_addrs) // num_cores
                per_core   = [
                    all_addrs[cid * chunk_size : (cid + 1) * chunk_size]
                    for cid in range(num_cores)
                ]
            else:
                per_core = [
                    list(_gen_sequential(level_counts, addr_bits, trace_type,
                                         *_core_row_range(cid, ro_total, num_cores)))
                    for cid in range(num_cores)
                ]

            for num_bubbles in NUM_BUBBLES_LIST:
                out_dir = script_dir / chip_name / trace_name / f"{num_cores}cores" / f"{num_bubbles}bubbles"
                shutil.rmtree(out_dir, ignore_errors=True)
                out_dir.mkdir(parents=True, exist_ok=True)

                for core_id, chunk in enumerate(per_core):
                    out_path = out_dir / f"core{core_id}.trace"
                    count    = _write_trace(out_path, chunk, num_bubbles)
                    done    += 1
                    print(f"[{done:>{len(str(total_files))}}/{total_files}] "
                          f"{out_path.relative_to(script_dir)}  ({count:,} entries)")

    print(f"\nDone. Generated {total_files} trace file(s).")


if __name__ == "__main__":
    main()
