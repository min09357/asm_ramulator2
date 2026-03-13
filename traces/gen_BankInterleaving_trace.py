from itertools import product
from pathlib import Path


# FILE_NAME = "DDR4_2933Y_1R_Rowhit.trace"
FILE_NAME = "DDR4_2933Y_2R_Rowhit.trace"
# FILE_NAME = "DDR5_4800B_1R_Rowhit.trace"
# FILE_NAME = "DDR5_4800B_2R_Rowhit.trace"
# FILE_NAME = "DDR5_5600B_1R_Rowhit.trace"
# FILE_NAME = "DDR5_5600B_2R_Rowhit.trace"

# FILE_NAME = "DDR4_2933Y_1R_Rowmiss.trace"
# FILE_NAME = "DDR4_2933Y_2R_Rowmiss.trace"
# FILE_NAME = "DDR5_4800B_1R_Rowmiss.trace"
# FILE_NAME = "DDR5_4800B_2R_Rowmiss.trace"
# FILE_NAME = "DDR5_5600B_1R_Rowmiss.trace"
# FILE_NAME = "DDR5_5600B_2R_Rowmiss.trace"

REQUEST_TYPE = "R"


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
    CH: 1, RA: 2, BG: 4, BA: 4, RO: 1 << 9, CO: 1 << 7, # DDR4_2933Y_2R
    # CH: 2, RA: 1, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 7, # DDR5_4800B_1R
    # CH: 2, RA: 2, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 7, # DDR5_4800B_2R
    # CH: 2, RA: 1, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 6, # DDR5_5600B_1R
    # CH: 2, RA: 2, BG: 8, BA: 4, RO: 1 << 9, CO: 1 << 6, # DDR5_5600B_2R

}

# Fastest-changing to slowest-changing order.
# INTERLEAVING_SEQUENCE = [CH, RA, BG, BA, CO, RO]    # Row hit
# INTERLEAVING_SEQUENCE = [CH, BG, RA, BA, CO, RO]    # Row hit
INTERLEAVING_SEQUENCE = [CH, BG, BA, RA, CO, RO]    # Row hit
# INTERLEAVING_SEQUENCE = [CH, BG, RA, BA, RO, CO]    # Row miss


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


def write_trace(file_path):
    total = 0
    with open(file_path, "w", encoding="ascii") as trace_file:
        for addr_vec in generate_address_vectors():
            trace_file.write(f"{REQUEST_TYPE} {','.join(map(str, addr_vec))}\n")
            total += 1
    return total


def main():
    validate_configuration()

    output_path = Path(__file__).with_name(FILE_NAME)
    num_entries = write_trace(output_path)

    print(f"Generated {num_entries} trace entries")
    print(f"Output: {output_path}")
    print(f"Address order: {format_level_list(ADDRESS_ORDER)}")
    print(f"Level count: { {LEVEL_NAMES[level]: count for level, count in LEVEL_COUNTS.items()} }")
    print(
        "Interleaving order (fastest -> slowest): "
        f"{format_level_list(INTERLEAVING_SEQUENCE)}"
    )


if __name__ == "__main__":
    main()
