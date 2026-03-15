


./ramulator2 -f DDR4.yaml -p Frontend.path=traces/DDR4_2933Y_1R_Rowhit.trace -p MemorySystem.Controller.RowPolicy.impl=OpenRowPolicy
./ramulator2 -f DDR4.yaml -p Frontend.path=traces/DDR4_2933Y_1R_Rowhit.trace -p MemorySystem.Controller.RowPolicy.impl=OpenRowPolicy


./ramulator2 -f DDR4.yaml -p Frontend.path=traces/DDR4_2933Y_2R_Rowhit.trace -p MemorySystem.Controller.RowPolicy.impl=OpenRowPolicy
./ramulator2 -f DDR4.yaml -p Frontend.path=traces/DDR4_2933Y_2R_Rowmiss.trace -p MemorySystem.Controller.RowPolicy.impl=OpenRowPolicy


./ramulator2 -f DDR4.yaml -p Frontend.path=traces/DDR4_2933Y_2R_Rowhit.trace -p MemorySystem.Controller.RowPolicy.impl=ClosedRowPolicy
./ramulator2 -f DDR4.yaml -p Frontend.path=traces/DDR4_2933Y_2R_Rowmiss.trace -p MemorySystem.Controller.RowPolicy.impl=ClosedRowPolicy


./ramulator2 -f DDR4.yaml -p Frontend.path=traces/DDR4_2933Y_2R_Rowhit.trace -p MemorySystem.Controller.RowPolicy.impl=ClosedWithAutoPrecharge
./ramulator2 -f DDR4.yaml -p Frontend.path=traces/DDR4_2933Y_2R_Rowmiss.trace -p MemorySystem.Controller.RowPolicy.impl=ClosedWithAutoPrecharge




./ramulator2 -f DDR5.yaml -p MemorySystem.DRAM.org.preset=DDR5_16Gb_x8 -p MemorySystem.DRAM.org.rank=1 -p MemorySystem.DRAM.timing.preset=DDR5_5600B -p Frontend.path=traces/DDR5_4800B_1R_Rowmiss.trace -p MemorySystem.Controller.RowPolicy.impl=ClosedRowPolicy
