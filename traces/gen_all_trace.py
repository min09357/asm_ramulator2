from itertools import product
from pathlib import Path
import random


CH, RA, BG, BA, RO, CO = range(6)

ADDRESS_ORDER = [CH, RA, BG, BA, RO, CO]

LEVEL_NAMES = {
    CH: "Ch", RA: "Ra", BG: "Bg", BA: "Ba", RO: "Ro", CO: "Co",
}

# Row hit: Column changes before Row (row buffer hit)
# Row miss: Row changes before Column (row buffer miss)
ROW_HIT = [CH, RA, BG, BA, CO, RO]
ROW_MISS = [CH, RA, BG, BA, RO, CO]

REQUEST_TYPE = "R"

RANDOM_SEED = 42

TRACE_CONFIGS = [
    # (filename, level_counts, interleaving_sequence, mode)
    # mode: "sequential" | "random_interleaving" | "random"

    # DDR4_2933Y_1R
    ("DDR4_2933Y_1R_Rowhit.trace",                     {CH: 1, RA: 1, BG: 4, BA: 4, RO: 1 << 9, CO: 1 << 7}, ROW_HIT,  "sequential"),
    ("DDR4_2933Y_1R_Rowmiss.trace",                    {CH: 1, RA: 1, BG: 4, BA: 4, RO: 1 << 9, CO: 1 << 7}, ROW_MISS, "sequential"),
    ("DDR4_2933Y_1R_Rowhit_RandomInterleaving.trace",  {CH: 1, RA: 1, BG: 4, BA: 4, RO: 1 << 9, CO: 1 << 7}, ROW_HIT,  "random_interleaving"),
    ("DDR4_2933Y_1R_Rowmiss_RandomInterleaving.trace", {CH: 1, RA: 1, BG: 4, BA: 4, RO: 1 << 9, CO: 1 << 7}, ROW_MISS, "random_interleaving"),
    ("DDR4_2933Y_1R_Random.trace",                     {CH: 1, RA: 1, BG: 4, BA: 4, RO: 1 << 9, CO: 1 << 7}, ROW_MISS, "random"),

    # DDR4_2933Y_2R
    ("DDR4_2933Y_2R_Rowhit.trace",                     {CH: 1, RA: 2, BG: 4, BA: 4, RO: 1 << 9, CO: 1 << 7}, ROW_HIT,  "sequential"),
    ("DDR4_2933Y_2R_Rowmiss.trace",                    {CH: 1, RA: 2, BG: 4, BA: 4, RO: 1 << 9, CO: 1 << 7}, ROW_MISS, "sequential"),
    ("DDR4_2933Y_2R_Rowhit_RandomInterleaving.trace",  {CH: 1, RA: 2, BG: 4, BA: 4, RO: 1 << 9, CO: 1 << 7}, ROW_HIT,  "random_interleaving"),
    ("DDR4_2933Y_2R_Rowmiss_RandomInterleaving.trace", {CH: 1, RA: 2, BG: 4, BA: 4, RO: 1 << 9, CO: 1 << 7}, ROW_MISS, "random_interleaving"),
    ("DDR4_2933Y_2R_Random.trace",                     {CH: 1, RA: 2, BG: 4, BA: 4, RO: 1 << 9, CO: 1 << 7}, ROW_MISS, "random"),

    # DDR5_4800B_1R
    ("DDR5_4800B_1R_Rowhit.trace",                     {CH: 2, RA: 1, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 7}, ROW_HIT,  "sequential"),
    ("DDR5_4800B_1R_Rowmiss.trace",                    {CH: 2, RA: 1, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 7}, ROW_MISS, "sequential"),
    ("DDR5_4800B_1R_Rowhit_RandomInterleaving.trace",  {CH: 2, RA: 1, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 7}, ROW_HIT,  "random_interleaving"),
    ("DDR5_4800B_1R_Rowmiss_RandomInterleaving.trace", {CH: 2, RA: 1, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 7}, ROW_MISS, "random_interleaving"),
    ("DDR5_4800B_1R_Random.trace",                     {CH: 2, RA: 1, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 7}, ROW_MISS, "random"),

    # DDR5_4800B_2R
    ("DDR5_4800B_2R_Rowhit.trace",                     {CH: 2, RA: 2, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 7}, ROW_HIT,  "sequential"),
    ("DDR5_4800B_2R_Rowmiss.trace",                    {CH: 2, RA: 2, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 7}, ROW_MISS, "sequential"),
    ("DDR5_4800B_2R_Rowhit_RandomInterleaving.trace",  {CH: 2, RA: 2, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 7}, ROW_HIT,  "random_interleaving"),
    ("DDR5_4800B_2R_Rowmiss_RandomInterleaving.trace", {CH: 2, RA: 2, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 7}, ROW_MISS, "random_interleaving"),
    ("DDR5_4800B_2R_Random.trace",                     {CH: 2, RA: 2, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 7}, ROW_MISS, "random"),

    # DDR5_5600B_1R
    ("DDR5_5600B_1R_Rowhit.trace",                     {CH: 2, RA: 1, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 6}, ROW_HIT,  "sequential"),
    ("DDR5_5600B_1R_Rowmiss.trace",                    {CH: 2, RA: 1, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 6}, ROW_MISS, "sequential"),
    ("DDR5_5600B_1R_Rowhit_RandomInterleaving.trace",  {CH: 2, RA: 1, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 6}, ROW_HIT,  "random_interleaving"),
    ("DDR5_5600B_1R_Rowmiss_RandomInterleaving.trace", {CH: 2, RA: 1, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 6}, ROW_MISS, "random_interleaving"),
    ("DDR5_5600B_1R_Random.trace",                     {CH: 2, RA: 1, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 6}, ROW_MISS, "random"),

    # DDR5_5600B_1R variants
    ("DDR5_5600B_1R_Rowmiss_half.trace",                    {CH: 2, RA: 1, BG: 8, BA: 2, RO: 1 << 9, CO: 1 << 6}, ROW_MISS, "sequential"),
    ("DDR5_5600B_1R_Rowmiss_quarter.trace",                 {CH: 2, RA: 1, BG: 8, BA: 1, RO: 1 << 9, CO: 1 << 6}, ROW_MISS, "sequential"),
    ("DDR5_5600B_1R_Rowmiss_half_RandomInterleaving.trace", {CH: 2, RA: 1, BG: 8, BA: 2, RO: 1 << 9, CO: 1 << 6}, ROW_MISS, "random_interleaving"),
    ("DDR5_5600B_1R_Rowmiss_quarter_RandomInterleaving.trace", {CH: 2, RA: 1, BG: 8, BA: 1, RO: 1 << 9, CO: 1 << 6}, ROW_MISS, "random_interleaving"),
    ("DDR5_5600B_1R_half_Random.trace",                     {CH: 2, RA: 1, BG: 8, BA: 2, RO: 1 << 9, CO: 1 << 6}, ROW_MISS, "random"),
    ("DDR5_5600B_1R_quarter_Random.trace",                  {CH: 2, RA: 1, BG: 8, BA: 1, RO: 1 << 9, CO: 1 << 6}, ROW_MISS, "random"),

    # DDR5_5600B_2R
    ("DDR5_5600B_2R_Rowhit.trace",                     {CH: 2, RA: 2, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 6}, ROW_HIT,  "sequential"),
    ("DDR5_5600B_2R_Rowmiss.trace",                    {CH: 2, RA: 2, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 6}, ROW_MISS, "sequential"),
    ("DDR5_5600B_2R_Rowhit_RandomInterleaving.trace",  {CH: 2, RA: 2, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 6}, ROW_HIT,  "random_interleaving"),
    ("DDR5_5600B_2R_Rowmiss_RandomInterleaving.trace", {CH: 2, RA: 2, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 6}, ROW_MISS, "random_interleaving"),
    ("DDR5_5600B_2R_Random.trace",                     {CH: 2, RA: 2, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 6}, ROW_MISS, "random"),
]


def format_level_list(levels):
    return [LEVEL_NAMES[level] for level in levels]


def generate_address_vectors(level_counts, interleaving_sequence):
    ordered_ranges = [range(level_counts[level]) for level in reversed(interleaving_sequence)]

    for values in product(*ordered_ranges):
        addr_vec = {level: 0 for level in ADDRESS_ORDER}
        for level, value in zip(reversed(interleaving_sequence), values):
            addr_vec[level] = value
        yield [addr_vec[level] for level in ADDRESS_ORDER]


def generate_address_vectors_random_interleaving(level_counts, interleaving_sequence):
    """
    Generate address vectors with per-cycle randomized bank access order.
    Each cycle visits all bank combinations (CH x RA x BG x BA) once in shuffled order.
    The non-bank levels (RO, CO) progress in interleaving_sequence order across cycles.
    """
    bank_levels = {CH, RA, BG, BA}

    addr_sequence = [l for l in interleaving_sequence if l not in bank_levels]

    bank_level_list = [CH, RA, BG, BA]
    bank_combos = [
        dict(zip(bank_level_list, vals))
        for vals in product(*(range(level_counts[l]) for l in bank_level_list))
    ]

    addr_ranges = [range(level_counts[l]) for l in reversed(addr_sequence)]

    random.seed(RANDOM_SEED)

    for addr_vals in product(*addr_ranges):
        addr_map = dict(zip(reversed(addr_sequence), addr_vals))

        random.shuffle(bank_combos)

        for bank_map in bank_combos:
            merged = {**addr_map, **bank_map}
            yield [merged[l] for l in ADDRESS_ORDER]


def generate_address_vectors_random(level_counts):
    """
    Generate fully random address vectors.
    Each access independently picks CH, RA, BG, BA, RO, CO at random.
    Total count equals the full address space size (CH x RA x BG x BA x RO x CO).
    """
    total = 1
    for count in level_counts.values():
        total *= count

    random.seed(RANDOM_SEED)

    for _ in range(total):
        yield [random.randint(0, level_counts[level] - 1) for level in ADDRESS_ORDER]


def write_trace(file_path, level_counts, interleaving_sequence, mode="sequential"):
    total = 0

    if mode == "random":
        iterable = generate_address_vectors_random(level_counts)
    elif mode == "random_interleaving":
        iterable = generate_address_vectors_random_interleaving(level_counts, interleaving_sequence)
    else:
        iterable = generate_address_vectors(level_counts, interleaving_sequence)

    with open(file_path, "w", encoding="ascii") as f:
        for addr_vec in iterable:
            f.write(f"{REQUEST_TYPE} {','.join(map(str, addr_vec))}\n")
            total += 1
    return total


def main():
    output_dir = Path(__file__).parent / "test_output"
    output_dir.mkdir(exist_ok=True)

    for i, (filename, level_counts, interleaving_seq, mode) in enumerate(TRACE_CONFIGS, 1):
        output_path = output_dir / filename
        num_entries = write_trace(output_path, level_counts, interleaving_seq, mode)

        if mode == "random":
            mode_str = f"Random (seed={RANDOM_SEED})"
        elif mode == "random_interleaving":
            mode_str = f"Random Interleaving (seed={RANDOM_SEED})"
        else:
            mode_str = f"Interleaving: {format_level_list(interleaving_seq)}"

        print(
            f"[{i:2d}/{len(TRACE_CONFIGS)}] {filename:55s} "
            f"{num_entries:>10,} entries  "
            f"{mode_str}"
        )

    print(f"\nDone. Generated {len(TRACE_CONFIGS)} trace files in {output_dir}")


if __name__ == "__main__":
    main()
