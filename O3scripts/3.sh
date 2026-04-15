set -e

cd ..


NUM_EXPECTED_INSTS=500000

NUMCORES=1
NUMBUBBLES=0

FRONTEND_RATIO=8
MEMORYSYSTEM_RATIO=3

RANK=1
RANK=2

LLC_PER_CORE="8MB"
LLC_ASSOCIATIVITY=8
MSHR_PER_CORE=512
INST_WINDOW_DEPTH=1024
READ_BUFFER_SIZE=512

ROW_POLICY="OpenRowPolicy"
# ROW_POLICY="ClosedRowPolicy"



# CONTROLLER="PerRank"
# REFRESH="PerRank"

REFRESH="AllBank"
CONTROLLER="Generic"




TRACE="Rowhit"
TRACE="Rowmiss"
TRACE="Random"




DDR_GEN=4
TRANSFER_RATE="2933Y"

CHIP_SIZE=8

DQ=4

RAS=47
RP=21



# DDR_GEN=5
# TRANSFER_RATE="4800B"

# CHIP_SIZE=16

# DQ=8

# RAS=77
# RP=39



# DDR_GEN=5
# TRANSFER_RATE="5600B"

# CHIP_SIZE=16

# DQ=8

# RAS=90
# RP=45



TIMING_PRESET="DDR${DDR_GEN}_${TRANSFER_RATE}"
DRAM_ORG_PRESET="DDR${DDR_GEN}_${CHIP_SIZE}Gb_x$DQ"

YAML="./yaml/DDR${DDR_GEN}.yaml"






TRACE_DIR="./traces/SimpleO3/${TIMING_PRESET}_${RANK}Rx${DQ}/${TRACE}/${NUMCORES}cores/${NUMBUBBLES}bubbles"



TRACE_ARGS=""
for i in $(seq 0 $((NUMCORES - 1))); do
  TRACE_ARGS="$TRACE_ARGS -p Frontend.traces[$i]=$TRACE_DIR/core$i.trace"
done

# RAS=77
# RP=39
RC=$((RAS + RP))
CMD="./ramulator2 -f $YAML -p Frontend.num_expected_insts=$NUM_EXPECTED_INSTS $TRACE_ARGS -p MemorySystem.DRAM.org.preset=$DRAM_ORG_PRESET -p MemorySystem.DRAM.timing.preset=$TIMING_PRESET \
 -p MemorySystem.DRAM.timing.nRAS=$RAS -p MemorySystem.DRAM.timing.nRP=$RP -p MemorySystem.DRAM.timing.nRC=$RC \
 -p Frontend.clock_ratio=$FRONTEND_RATIO -p MemorySystem.clock_ratio=$MEMORYSYSTEM_RATIO \
 -p MemorySystem.Controller.impl=$CONTROLLER -p MemorySystem.Controller.RefreshManager.impl=$REFRESH \
 -p MemorySystem.DRAM.org.rank=$RANK -p MemorySystem.Controller.RowPolicy.impl=$ROW_POLICY -p MemorySystem.Controller.read_buffer_size=$READ_BUFFER_SIZE \
 -p Frontend.llc_capacity_per_core=$LLC_PER_CORE -p Frontend.llc_associativity=$LLC_ASSOCIATIVITY -p Frontend.llc_num_mshr_per_core=$MSHR_PER_CORE -p Frontend.inst_window_depth=$INST_WINDOW_DEPTH \
 "
echo "--------------------------------------------------------"
echo "$CMD"
echo "--------------------------------------------------------"
eval $CMD


