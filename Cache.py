

class CacheLine:
    def __init__(self, state='I', lastused=-1, blockNumber = -1, validFrom = -1):
        self.state = state
        self.lastused = lastused
        self.blockNumber = blockNumber
        self.validFrom = validFrom

    def is_invalid(self):
        return self.state == 'I'
    
    def is_modified(self):
        return self.state == 'M'
    
    def is_owner(self):
        return self.state == 'O'
    
    def is_exclusive(self):
        return self.state == 'E'
    
    def is_private(self):
        return self.state == "E" or self.state == "M"
    
    def set_last_used(self,lastused):
        self.lastused = lastused

    def set_state(self,state):
        self.state = state

    def set_valid_from(self,validFrom):
        self.validFrom = validFrom

    def __str__(self):
        return f"CacheLine: State={self.state}, LastUsed={self.lastused}, BlockNumber={self.blockNumber}, ValidFrom={self.validFrom}"

    


class Cache :
    def __init__(self, assoc, blocksize, cacheSize, ID):
        self.assoc = assoc
        self.blocksize = blocksize
        self.cacheSize = cacheSize
        self.ID = ID
        self.setNum = cacheSize // (assoc*blocksize)
        self.Caches = [[CacheLine() for i in range(self.assoc)] for j in range(self.setNum)]

    def __str__(self):
        cache_str = f"Cache {self.ID}:\n"
        for i, cache_set in enumerate(self.Caches):
            cache_str += f"Set {i}: " + ", ".join(str(line) for line in cache_set) + "\n"
        return cache_str

    def get_block_number(self,addr):
        return addr//self.blocksize
    
    def get_set_index(self,blockNumber):
        return blockNumber % self.setNum
    
    
    
    def get_assoc_number(self,addr):
        blockNumber = self.get_block_number(addr)
        setIndex = self.get_set_index(blockNumber)
        currentSet = self.Caches[setIndex]
        for num, line in enumerate(currentSet):
            if not line.is_invalid() and line.blockNumber == blockNumber:
                return num
        return None
    
    def has_entry(self, addr):
        return self.get_assoc_number(addr) != None
    
    def get_evicted_assoc_number(self, set_index):
        current_set = self.Caches[set_index]

        # Select invalid entry if any exist
        for num, entry in enumerate(current_set):
            if entry.is_invalid():
                return num

        # Otherwise use LRU policy to select oldest block
        oldest_entry_num = min(range(self.assoc), key=lambda num: current_set[num].lastused)
        return oldest_entry_num
    
    def get_entry(self, addr):
        assert self.has_entry(addr)
        block_number = self.get_block_number(addr)
        set_index = self.get_set_index(block_number)
        assoc_number = self.get_assoc_number(addr)
        return self.Caches[set_index][assoc_number]
    
    def get_head_addr(self, cacheline):
        return cacheline.blockNumber * self.blocksize

    def set_block_last_used(self, addr, last_used):
        self.get_entry(addr).set_last_used(last_used)

    def set_block_valid_from(self, addr, valid_from):
        self.get_entry(addr).set_valid_from(valid_from)

    def set_block_state(self, addr, state):
        self.get_entry(addr).set_state(state)

    def get_block_state(self, addr):
        return self.get_entry(addr).state

    def is_addr_dirty(self, addr):
        return self.get_entry(addr).is_modified()

    def is_addr_owner(self, addr):
        return self.get_entry(addr).is_owner()
    
    def is_addr_exclusive(self, addr):
        return self.get_entry(addr).is_exclusive()

    def is_addr_private(self, addr):
        return self.get_entry(addr).is_private()

    def is_addr_invalid(self, addr):
        if not self.has_entry(addr):
            return True
        return self.get_entry(addr).is_invalid()

    def get_addr_usable_time(self, addr):
        return self.get_entry(addr).validFrom

    def evict_entry(self, addr):
        assert not self.has_entry(addr)
        block_number = self.get_block_number(addr)
        set_index = self.get_set_index(block_number)
        evicted_assoc_number = self.get_evicted_assoc_number(set_index)

        evicted_entry = self.Caches[set_index][evicted_assoc_number]
        self.Caches[set_index][evicted_assoc_number] = CacheLine()
        return evicted_entry

    def alloc_entry(self, addr, state, last_used, valid_from):
        assert not self.has_entry(addr)
        block_number = self.get_block_number(addr)
        set_index = self.get_set_index(block_number)
        evicted_assoc_number = self.get_evicted_assoc_number(set_index)

        assert self.Caches[set_index][evicted_assoc_number].is_invalid()
        self.Caches[set_index][evicted_assoc_number] = CacheLine(state, last_used, block_number, valid_from)

'''cache = Cache(2,16,4096,0)
print(cache)'''

if __name__ == "__main__":
    cache = Cache(assoc=2, blocksize=16, cacheSize=4096, ID=1)
    print("Initial Cache State:")
    print(cache)

    # Test adding an entry
    addr = 32
    state = 'M'
    last_used = 10
    valid_from = 5
    cache.alloc_entry(addr, state, last_used, valid_from)

    addr = 4800
    state = 'M'
    last_used = 9
    valid_from = 6
    cache.alloc_entry(addr, state, last_used, valid_from)


    print("\nCache State after adding an entry:")
    print(cache)

    # Test checking if an address is in the cache
    print("\nIs address 32 in the cache?", cache.has_entry(32))
    print("Is address 4800 in the cache?", cache.has_entry(4800))