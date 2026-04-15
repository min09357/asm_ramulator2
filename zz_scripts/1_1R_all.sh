set -e

cd ..

YAML="./yaml/DDR5_4800B_1Rx8.yaml"
TRACE="./traces/ReadWriteTrace/DDR5_4800B_1Rx8_Rowmiss.trace"


RAS=77
RP=39
RC=$((RAS + RP))
CMD="./ramulator2 -f $YAML -p MemorySystem.DRAM.timing.nRAS=$RAS -p MemorySystem.DRAM.timing.nRP=$RP -p MemorySystem.DRAM.timing.nRC=$RC -p Frontend.path=$TRACE"
echo "--------------------------------------------------------"
echo "$CMD"
echo "--------------------------------------------------------"
eval $CMD


# RAS=77
# RP=59
# RC=$((RAS + RP))
# CMD="./ramulator2 -f $YAML -p MemorySystem.DRAM.timing.nRAS=$RAS -p MemorySystem.DRAM.timing.nRP=$RP -p MemorySystem.DRAM.timing.nRC=$RC -p Frontend.path=$TRACE"
# echo "--------------------------------------------------------"
# echo "$CMD"
# echo "--------------------------------------------------------"
# eval $CMD


# RAS=77
# RP=79
# RC=$((RAS + RP))
# CMD="./ramulator2 -f $YAML -p MemorySystem.DRAM.timing.nRAS=$RAS -p MemorySystem.DRAM.timing.nRP=$RP -p MemorySystem.DRAM.timing.nRC=$RC -p Frontend.path=$TRACE"
# echo "--------------------------------------------------------"
# echo "$CMD"
# echo "--------------------------------------------------------"
# eval $CMD


# RAS=77
# RP=99
# RC=$((RAS + RP))
# CMD="./ramulator2 -f $YAML -p MemorySystem.DRAM.timing.nRAS=$RAS -p MemorySystem.DRAM.timing.nRP=$RP -p MemorySystem.DRAM.timing.nRC=$RC -p Frontend.path=$TRACE"
# echo "--------------------------------------------------------"
# echo "$CMD"
# echo "--------------------------------------------------------"
# eval $CMD


# RAS=77
# RP=119
# RC=$((RAS + RP))
# CMD="./ramulator2 -f $YAML -p MemorySystem.DRAM.timing.nRAS=$RAS -p MemorySystem.DRAM.timing.nRP=$RP -p MemorySystem.DRAM.timing.nRC=$RC -p Frontend.path=$TRACE"
# echo "--------------------------------------------------------"
# echo "$CMD"
# echo "--------------------------------------------------------"
# eval $CMD


# RAS=90
# RP=126
# RC=$((RAS + RP))
# CMD="./ramulator2 -f $YAML -p MemorySystem.DRAM.timing.nRAS=$RAS -p MemorySystem.DRAM.timing.nRP=$RP -p MemorySystem.DRAM.timing.nRC=$RC -p Frontend.path=$TRACE"
# echo "--------------------------------------------------------"
# echo "$CMD"
# echo "--------------------------------------------------------"
# eval $CMD


# RAS=110
# RP=126
# RC=$((RAS + RP))
# CMD="./ramulator2 -f $YAML -p MemorySystem.DRAM.timing.nRAS=$RAS -p MemorySystem.DRAM.timing.nRP=$RP -p MemorySystem.DRAM.timing.nRC=$RC -p Frontend.path=$TRACE"
# echo "--------------------------------------------------------"
# echo "$CMD"
# echo "--------------------------------------------------------"
# eval $CMD

# RAS=130
# RP=126
# RC=$((RAS + RP))
# CMD="./ramulator2 -f $YAML -p MemorySystem.DRAM.timing.nRAS=$RAS -p MemorySystem.DRAM.timing.nRP=$RP -p MemorySystem.DRAM.timing.nRC=$RC -p Frontend.path=$TRACE"
# echo "--------------------------------------------------------"
# echo "$CMD"
# echo "--------------------------------------------------------"
# eval $CMD

# RAS=150
# RP=126
# RC=$((RAS + RP))
# CMD="./ramulator2 -f $YAML -p MemorySystem.DRAM.timing.nRAS=$RAS -p MemorySystem.DRAM.timing.nRP=$RP -p MemorySystem.DRAM.timing.nRC=$RC -p Frontend.path=$TRACE"
# echo "--------------------------------------------------------"
# echo "$CMD"
# echo "--------------------------------------------------------"
# eval $CMD

# RAS=170
# RP=126
# RC=$((RAS + RP))
# CMD="./ramulator2 -f $YAML -p MemorySystem.DRAM.timing.nRAS=$RAS -p MemorySystem.DRAM.timing.nRP=$RP -p MemorySystem.DRAM.timing.nRC=$RC -p Frontend.path=$TRACE"
# echo "--------------------------------------------------------"
# echo "$CMD"
# echo "--------------------------------------------------------"
# eval $CMD

# RAS=190
# RP=126
# RC=$((RAS + RP))
# CMD="./ramulator2 -f $YAML -p MemorySystem.DRAM.timing.nRAS=$RAS -p MemorySystem.DRAM.timing.nRP=$RP -p MemorySystem.DRAM.timing.nRC=$RC -p Frontend.path=$TRACE"
# echo "--------------------------------------------------------"
# echo "$CMD"
# echo "--------------------------------------------------------"
# eval $CMD