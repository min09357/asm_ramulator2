from itertools import product
from pathlib import Path
import random


# FILE_NAME = "DDR4_2933Y_1R_Rowhit.trace"
# FILE_NAME = "DDR4_2933Y_1R_Rowmiss.trace"

# FILE_NAME = "DDR4_2933Y_2R_Rowhit.trace"
# FILE_NAME = "DDR4_2933Y_2R_Rowmiss.trace"


# FILE_NAME = "DDR5_4800B_1R_Rowhit.trace"
# FILE_NAME = "DDR5_4800B_1R_Rowmiss.trace"

# FILE_NAME = "DDR5_4800B_2R_Rowhit.trace"
# FILE_NAME = "DDR5_4800B_2R_Rowmiss.trace"

# FILE_NAME = "DDR5_5600B_1R_Rowhit.trace"
FILE_NAME = "DDR5_5600B_1R_Rowmiss.trace"
# FILE_NAME = "DDR5_5600B_1R_Rowmiss_half.trace"
# FILE_NAME = "DDR5_5600B_1R_Rowmiss_quarter.trace"

# FILE_NAME = "DDR5_5600B_2R_Rowhit.trace"
# FILE_NAME = "DDR5_5600B_2R_Rowmiss.trace"

REQUEST_TYPE = "R"

# TRACE_MODE = "sequential"          # Deterministic bank interleaving
# TRACE_MODE = "random_interleaving" # Per-cycle randomized bank order
TRACE_MODE = "random"                # Fully random: each access picks all levels independently
RANDOM_SEED = 42                     # Seed for reproducibility (random_interleaving / random)


CH, RA, BG, BA, RO, CO = range(6)

LEVEL_NAMES = {
    CH: "Ch",
    RA: "Ra",
    BG: "Bg",
    BA: "Ba",
    RO: "Ro",
    CO: "Co",
}

# Ramulator address-vector order.
ADDRESS_ORDER = [CH, RA, BG, BA, RO, CO]

# Organization size per address level.
LEVEL_COUNTS = {
    # CH: 1, RA: 1, BG: 4, BA: 4, RO: 1 << 9, CO: 1 << 7, # DDR4_2933Y_1R
    # CH: 1, RA: 2, BG: 4, BA: 4, RO: 1 << 9, CO: 1 << 7, # DDR4_2933Y_2R
    # CH: 2, RA: 1, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 7, # DDR5_4800B_1R
    # CH: 2, RA: 2, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 7, # DDR5_4800B_2R

    CH: 2, RA: 1, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 6, # DDR5_5600B_1R
    # CH: 2, RA: 1, BG: 8, BA: 2, RO: 1 << 9, CO: 1 << 6, # DDR5_5600B_1R_half
    # CH: 2, RA: 1, BG: 8, BA: 1, RO: 1 << 9, CO: 1 << 6, # DDR5_5600B_1R_quarter

    # CH: 2, RA: 2, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 6, # DDR5_5600B_2R

}

# Fastest-changing to slowest-changing order.
# INTERLEAVING_SEQUENCE = [CH, RA, BG, BA, CO, RO]    # Row hit rank first
INTERLEAVING_SEQUENCE = [CH, RA, BG, BA, RO, CO]    # Row miss rank first

# INTERLEAVING_SEQUENCE = [CH, BG, RA, BA, CO, RO]    # Row hit bank group first
# INTERLEAVING_SEQUENCE = [CH, BG, RA, BA, RO, CO]    # Row miss bank group first

# INTERLEAVING_SEQUENCE = [CH, BG, BA, RA, CO, RO]    # Row hit rank last
# INTERLEAVING_SEQUENCE = [CH, BG, BA, RA, RO, CO]    # Row miss rank last


def validate_configuration():
    missing_levels = [level for level in ADDRESS_ORDER if level not in LEVEL_COUNTS]
    if missing_levels:
        raise ValueError(f"Missing LEVEL_COUNTS entries for: {missing_levels}")

    sequence_set = set(INTERLEAVING_SEQUENCE)
    address_set = set(ADDRESS_ORDER)
    if sequence_set != address_set:
        raise ValueError(
            "INTERLEAVING_SEQUENCE must contain each address level exactly once. "
            f"Expected {format_level_list(ADDRESS_ORDER)}, "
            f"got {format_level_list(INTERLEAVING_SEQUENCE)}"
        )


def format_level_list(levels):
    return [LEVEL_NAMES[level] for level in levels]


def generate_address_vectors():
    """
    Generate full address vectors where the first entry in INTERLEAVING_SEQUENCE
    changes fastest.
    """
    ordered_ranges = [range(LEVEL_COUNTS[level]) for level in reversed(INTERLEAVING_SEQUENCE)]

    for values in product(*ordered_ranges):
        addr_vec = {level: 0 for level in ADDRESS_ORDER}

        for level, value in zip(reversed(INTERLEAVING_SEQUENCE), values):
            addr_vec[level] = value

        yield [addr_vec[level] for level in ADDRESS_ORDER]


def generate_address_vectors_random_interleaving():
    """
    Generate address vectors with per-cycle randomized bank access order.
    Each cycle visits all bank combinations (CH x RA x BG x BA) once in shuffled order.
    The non-bank levels (RO, CO) progress in INTERLEAVING_SEQUENCE order across cycles.
    """
    bank_levels = {CH, RA, BG, BA}

    addr_sequence = [l for l in INTERLEAVING_SEQUENCE if l not in bank_levels]

    bank_level_list = [CH, RA, BG, BA]
    bank_combos = [
        dict(zip(bank_level_list, vals))
        for vals in product(*(range(LEVEL_COUNTS[l]) for l in bank_level_list))
    ]

    addr_ranges = [range(LEVEL_COUNTS[l]) for l in reversed(addr_sequence)]

    random.seed(RANDOM_SEED)

    for addr_vals in product(*addr_ranges):
        addr_map = dict(zip(reversed(addr_sequence), addr_vals))

        random.shuffle(bank_combos)

        for bank_map in bank_combos:
            merged = {**addr_map, **bank_map}
            yield [merged[l] for l in ADDRESS_ORDER]


def generate_address_vectors_random():
    """
    Generate fully random address vectors.
    Each access independently picks CH, RA, BG, BA, RO, CO at random.
    Total count equals the full address space size (CH x RA x BG x BA x RO x CO).
    """
    total = 1
    for count in LEVEL_COUNTS.values():
        total *= count

    random.seed(RANDOM_SEED)

    for _ in range(total):
        yield [random.randint(0, LEVEL_COUNTS[level] - 1) for level in ADDRESS_ORDER]


def write_trace(file_path):
    total = 0

    if TRACE_MODE == "random":
        iterable = generate_address_vectors_random()
    elif TRACE_MODE == "random_interleaving":
        iterable = generate_address_vectors_random_interleaving()
    else:
        iterable = generate_address_vectors()

    with open(file_path, "w", encoding="ascii") as trace_file:
        for addr_vec in iterable:
            trace_file.write(f"{REQUEST_TYPE} {','.join(map(str, addr_vec))}\n")
            total += 1
    return total


def main():
    validate_configuration()

    if TRACE_MODE == "random":
        import re
        base = re.sub(r"_(Rowhit|Rowmiss)", "", FILE_NAME.replace(".trace", ""))
        name = f"{base}_Random_seed{RANDOM_SEED}.trace"
    elif TRACE_MODE == "random_interleaving":
        name = FILE_NAME.replace(".trace", f"_RandomInterleaving_seed{RANDOM_SEED}.trace")
    else:
        name = FILE_NAME

    output_path = Path(__file__).with_name(name)
    num_entries = write_trace(output_path)

    print(f"Generated {num_entries} trace entries")
    print(f"Output: {output_path}")
    print(f"Address order: {format_level_list(ADDRESS_ORDER)}")
    print(f"Level count: { {LEVEL_NAMES[level]: count for level, count in LEVEL_COUNTS.items()} }")
    if TRACE_MODE == "random":
        print(f"Mode: Random (seed={RANDOM_SEED})")
    elif TRACE_MODE == "random_interleaving":
        print(f"Mode: Random Interleaving (seed={RANDOM_SEED})")
    else:
        print(
            "Interleaving order (fastest -> slowest): "
            f"{format_level_list(INTERLEAVING_SEQUENCE)}"
        )


if __name__ == "__main__":
    main()
