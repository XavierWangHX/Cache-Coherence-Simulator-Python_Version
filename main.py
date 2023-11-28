# Define the function to read benchmark data

import os
import sys
from MESI_Simulator import*
from Dragon_Simulator import*
from MESIF_Simulator import*
#from MOESIRunner import*
from collections import deque


def read_benchmark(benchmark):
    number_of_cores = 4
    core_ops = [deque([]) for _ in range(number_of_cores)]

    for core in range(number_of_cores):
        file_name = f"{benchmark}_{core}.data"
        file_path = f"benchmarks/{benchmark}_four/{file_name}"
        
        
        if not os.path.isfile(file_path):
            print(f"Trace file {file_path} does not exist!\n")
            exit(-1)
            
        with open(file_path, 'r') as file:
            for line in file:
                parts = line.split()
                if len(parts) != 2:
                    continue
                ops_type = int(parts[0])
                addr = int(parts[1], 16)  # Convert address to integer assuming it's in hexadecimal
                core_ops[core].append((ops_type, addr))
                
    return core_ops

def simulate(protocol, cache_size, assoc, block_size, ops):
    if protocol.lower() == "mesi":
        runner = MESIsim(cache_size, assoc, block_size, ops)
    
    elif protocol.lower() == "dragon":
        runner = Dragonsim(cache_size, assoc, block_size, ops)

    #elif protocol.lower() == "moesi":
        #runner = MOESIRunner(cache_size, assoc, block_size, ops)

    elif protocol.lower() == "mesif":
        runner = MESIFsim(cache_size, assoc, block_size, ops)
    else:
        print(f"Unknown coherence protocol (should be MESI, Dragon or MESIF): {protocol}")
        exit(-1)

    runner.simulate()



def main():
    if len(sys.argv) != 6:
        print("Expect arguments in form: protocol benchmark cache_size associativity block_size")
        sys.exit(-1)

    protocol = sys.argv[1]
    benchmark = sys.argv[2]
    
    cache_size = int(sys.argv[3], 0)
    assoc = int(sys.argv[4], 0)
    block_size = int(sys.argv[5], 0)

    

    # Cache and block sizes should be multiples of word size (4 bytes)
    # This ensures word-aligned accesses
    assert cache_size > 0 and cache_size % 4 == 0, "Cache size must be a positive multiple of 4"
    assert block_size > 0 and block_size % 4 == 0, "Block size must be a positive multiple of 4"

    # Associativity should divide cache into integer number of sets
    assert assoc > 0 and cache_size % (assoc * block_size) == 0, "Associativity must divide cache into integer number of sets"

    ops = read_benchmark(benchmark)
    

    '''for core, opslist in enumerate(ops):
        print('core '+str(core)+' :')
        print(opslist)'''

        
    simulate(protocol, cache_size, assoc, block_size, ops)

if __name__ == "__main__":
    main()

'''# Read benchmark data again
core_operations = read_benchmark('overlap')

# Display the first few operations for each core
print({f"Core {core}": ops[:5] for core, ops in enumerate(core_operations)})'''


