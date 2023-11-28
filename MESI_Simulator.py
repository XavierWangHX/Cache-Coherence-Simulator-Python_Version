from Simulator import*


class MESIsim(Simulator):
    def __init__(self, cache_size, assoc, block_size, core_traces):
        super().__init__(cache_size, assoc, block_size, core_traces)

    def cacheAllocAddr(self,id,addr,addrstate):
        cache = self.caches[id]
        blockNumer = cache.get_block_number(addr)
        availableTime = self.get_mem_block_available_time(blockNumer) + 100
        evicted_line = cache.evict_entry(addr)
        if (not evicted_line.is_invalid()) :
            
            if (evicted_line.state == "M") :
                evictedAddr = cache.get_head_addr(evicted_line)
                self.cache_write_back_mem(id, evictedAddr)

        cache.alloc_entry(addr, addrstate, self.cur_time, availableTime)
        return True

    def invalidateO(self,cacheID,  addr,  needWriteBack): 
        # Invalidate all other copies in other caches
        for othCacheID in range(len(self.caches)):
            if (othCacheID == cacheID) :
                continue
            othCache = self.caches[othCacheID]

            if (othCache.has_entry(addr)) :
                # If copy is dirty ('M' state) - only one process holds line
                if (othCache.is_addr_dirty(addr) and needWriteBack) :
                    self.cache_write_back_mem(othCacheID, addr)
                # Otherwise immediately invalidate that entry, whatever its state
                othCache.set_block_state(addr, "I")
                # Update stat 7
                self.bus.inc_invalidate_count()
            
        
    

    def simulate_read_hit(self, core_id, addr):
        cache = self.caches[core_id]
        cache.set_block_last_used(addr,self.cur_time)

    def simulate_write_hit(self,coreID, addr): 
        
        cache = self.caches[coreID]
        #blockState = cache.get_block_state(addr)

        cache.set_block_last_used(addr, self.cur_time)
        cache.set_block_state(addr, "M")

        # Should have no other copies in 'M'/'E' so this will only invalidate them
        # No write-back needed
        self.invalidateO(coreID, addr, False)

        # Mem does not hold an updated copy
        blockNum = cache.get_block_number(addr)
        self.invalid_block[blockNum] = self.INF
          
    # Similarly implement other methods
    def simulate_read_miss(self,coreID, addr): 
        #Check if any cache holds modified address
        for othCacheID in range(len(self.caches)): 
            if (othCacheID == coreID) :
                continue
            othCache = self.caches[othCacheID]
            if (othCache.has_entry(addr)) :
                if (othCache.is_addr_dirty(addr)) :
                    # Snooped response triggers flush in cache with M state
                    self.cache_write_back_mem(othCacheID, addr)
                    othCache.set_block_state(addr, "S")
            
                if (othCache.is_addr_exclusive(addr)) :
                        # Snooped response triggers flush in cache with M state
                        #self.cache_write_back_mem(othCacheID, addr)
                        othCache.set_block_state(addr, "S")

        countHold = 0
        for othCacheID in range(len(self.caches)): 
            if (othCacheID == coreID) :
                continue
            othCache = self.caches[othCacheID]
            if (othCache.has_entry(addr)) :
                countHold+=1
        

        addrState = "E" if countHold==0 else "S"
        self.cacheAllocAddr(coreID, addr, addrState)

        # Update stat 6 + 7
        self.bus.inc_traffic_block()

    def simulate_write_miss(self,coreID,  addr) :
    
        cache = self.caches[coreID]

        # Invalidate with write-back if another cache a copy in 'M' state
        self.invalidateO(coreID, addr, True)

        # Transition to 'M' state
        addrState = "M"
        self.cacheAllocAddr(coreID, addr, addrState)

        # Memory does not hold an updated copy
        blockNum = cache.get_block_number(addr)
        self.invalid_block[blockNum] = self.INF

        # Update stat 6 + 7
        self.bus.inc_traffic_block()

    def progressTime(self, newTime) :
        
        for core in self.cores: 
            core.progress(newTime - self.cur_time)
        self.cur_time = newTime
        self.check_mem()
    

                
            
        






    