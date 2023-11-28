from Simulator import *

class MESIFsim(Simulator):
    def __init__(self, cache_size, assoc, block_size, core_traces):
        super().__init__(cache_size, assoc, block_size, core_traces)
        # Initialize any MOESI-specific data structures here

    def getCopiesWithForwarder(self, addr):
        num_copies = 0
        forwarder_state = "NO_FORWARDER"

        for cache_id in range(len(self.caches)):
            cache = self.caches[cache_id]

            if cache.has_entry(addr):
                num_copies += 1
                block_state = cache.get_block_state(addr)

                if block_state in ["M", "E"]:
                    return num_copies, block_state
                elif block_state == "F":
                    # Only 'F' state cache forwards - 'S' state caches are silent
                    forwarder_state = block_state

        return num_copies, forwarder_state

    def fetchAndAlloc(self, cache_id, addr, new_state, forwarder_state):
        cache = self.caches[cache_id]
        block_num = cache.get_block_number(addr)

        # Determine earliest time requested block is available from memory
        available_time = self.get_mem_block_available_time(block_num) + 100

        # Evict a cache entry if necessary
        evicted_entry = cache.evict_entry(addr)
        if not evicted_entry.is_invalid():
            if evicted_entry.state == "M":
                evicted_addr = cache.get_head_addr(evicted_entry)
                self.cache_write_back_mem(cache_id, evicted_addr)

        # Check if faster to serve from forwarding cache
        if forwarder_state != "NO_FORWARDER":
            cache_transfer_time = self.cur_time + 2 * self.bus.get_word_per_block()
            available_time = min(available_time, cache_transfer_time)

        cache.alloc_entry(addr, new_state, self.cur_time, available_time)
        return True
    

    def invalidateO(self, cache_id, addr, need_write_back):
        # Invalidate all other copies in other caches
        for oth_cache_id in range(len(self.caches)):
            if oth_cache_id == cache_id:
                continue

            oth_cache = self.caches[oth_cache_id]

            if oth_cache.has_entry(addr):
                # If copy is dirty ('M' state) - only one process holds line
                if need_write_back and oth_cache.is_addr_dirty(addr):
                    self.cache_write_back_mem(oth_cache_id, addr)

                # Invalidate that entry
                oth_cache.set_block_state(addr, "I")

                # Update invalidate count
                self.bus.inc_invalidate_count()


    def simulate_read_hit(self, core_id, addr):
        cache = self.caches[core_id]
        cache.set_block_last_used(addr, self.cur_time)

    def simulate_write_hit(self, core_id, addr):
        cache = self.caches[core_id]
        block_state = cache.get_block_state(addr)

        cache.set_block_last_used(addr, self.cur_time)
        cache.set_block_state(addr, "M")

        # Invalidate other copies without write-back
        self.invalidateO(core_id, addr, False)

        # Memory does not hold an updated copy
        block_num = cache.get_block_number(addr)
        self.invalid_block[block_num] = self.INF

    def simulate_read_miss(self, core_id, addr):
        num_copies, forwarder_state = self.getCopiesWithForwarder(addr)

        # Perform state change in forwarding cache
        if forwarder_state != "NO_FORWARDER":
            for cache_id in range(len(self.caches)):
                cache = self.caches[cache_id]

                if cache.has_entry(addr):
                    block_state = cache.get_block_state(addr)

                    if block_state == "S":
                        continue
                    assert block_state == forwarder_state

                    if block_state == "M":
                        # Forwarding cache is in 'M' state and holds a dirty copy
                        self.cache_write_back_mem(cache_id, addr)

                    # Forwarding cache has read-only copy, transitions to 'S'
                    cache.set_block_state(addr, "S")
                    break

        # Determine the new state for the requesting cache
        addr_state = "E" if num_copies == 0 else "F"
        self.fetchAndAlloc(core_id, addr, addr_state, forwarder_state)

        # Update traffic
        self.bus.inc_traffic_block()

    def simulate_write_miss(self, core_id, addr):
        num_copies, forwarder_state = self.getCopiesWithForwarder(addr)

        # Invalidate other copies with write-back if necessary
        self.invalidateO(core_id, addr, True)

        # Transition to 'M' state
        addr_state = "M"
        self.fetchAndAlloc(core_id, addr, addr_state, forwarder_state)

        # Memory does not hold an updated copy
        block_num = self.caches[core_id].get_block_number(addr)
        self.invalid_block[block_num] = self.INF

        # Update traffic
        self.bus.inc_traffic_block()

    def progressTime(self, new_time):
        time_difference = new_time - self.cur_time
        for core in self.cores:
            core.progress(time_difference)

        self.cur_time = new_time
        self.check_mem()
