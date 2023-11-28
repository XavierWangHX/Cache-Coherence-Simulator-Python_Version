from Simulator import*
class Dragonsim(Simulator):
    def __init__(self, cache_size, assoc, block_size, core_traces):
        super().__init__(cache_size, assoc, block_size, core_traces)
        self.broadcasting_blocks={}
    
    def find_cache_source_available_time(self, cache_id, addr):
        available_time_from_oth = self.INF
        for oth_cache_id in range(len(self.caches)):
            if oth_cache_id == cache_id:
                continue
            oth_cache = self.caches[oth_cache_id]
            if oth_cache.has_entry(addr):
                available_time_from_oth = min(available_time_from_oth,
                                            max(oth_cache.get_addr_usable_time(addr), self.cur_time))
        return available_time_from_oth
    
    def find_mem_source_available_time(self, cache_id, addr):
        cache = self.caches[cache_id]
        block_num = cache.get_block_number(addr)
        available_time_from_mem = self.get_mem_block_available_time(block_num)
        return available_time_from_mem
    
    def find_source_available_time(self, cache_id, addr):
        available_time_from_mem = self.find_mem_source_available_time(cache_id, addr)
        available_time_from_cache = self.find_cache_source_available_time(cache_id, addr)
        return min(available_time_from_mem + 100, available_time_from_cache + 2 * self.bus.get_word_per_block())
    
    def count_oth_cache_hold(self, cache_id, addr):
        count_hold = 0
        for oth_cache_id, oth_cache in enumerate(self.caches):
            if oth_cache_id == cache_id:
                continue
            if oth_cache.has_entry(addr):
                count_hold += 1
        return count_hold
    
    def cache_receive_w(self, cache_id, addr, send_cycle):
        cache = self.caches[cache_id]
        assert cache.has_entry(addr), "Cache does not have entry for address"

        # 2 cycles to transmit updated word (after which block marked as valid)
        cache.set_block_valid_from(addr, send_cycle + 2)

        # Update stat 6
        self.bus.inc_traffic_word()

    def cache_receive_b(self, cache_id, addr, state):
        # Passive receipt of block
        cache = self.caches[cache_id]
        assert not cache.has_entry(addr), "Cache unexpectedly has entry for address"

        # Assuming cache controller can determine data source with lowest latency
        # between main memory and another cache
        cache_available_time = max(self.find_cache_source_available_time(cache_id, addr), self.cur_time)
        mem_available_time = max(self.find_mem_source_available_time(cache_id, addr), self.cur_time)

        # Serve from memory if no cache holds a copy, else perform C2C transfer
        available_time = cache_available_time if cache_available_time != self.INF else mem_available_time + 100
        available_time += 2 * self.bus.get_word_per_block()
            # Pre-condition: find an available line (evict one if none available)
        evicted_entry = cache.evict_entry(addr)
        # If entry is valid, this is the victim block (cache set conflict)
        if not evicted_entry.is_invalid():
            evicted_addr = cache.get_head_addr(evicted_entry)
            evicted_block_num = cache.get_block_number(evicted_addr)
            need_rewrite = (self.get_mem_block_available_time(evicted_block_num) == self.INF and 
                            self.count_oth_cache_hold(cache_id, evicted_addr) == 0)

            # Perform write-back to update mem if memory holds a stale copy and
            # the evicted line is the last copy amongst all caches
            if need_rewrite:
                self.cache_write_back_mem(cache_id, evicted_addr)

        cache.alloc_entry(addr, state, self.cur_time, available_time)

        # Update stat 6
        self.bus.inc_traffic_block()

    def broadcast_w_oth_cache(self, cache_id, addr, send_cycle):
        # Broadcast a word to other caches (update)
        count_hold = self.count_oth_cache_hold(cache_id, addr)
        head_addr = self.get_head_addr(addr)
        assert count_hold > 0, "No other cache holds the block"

        self.broadcasting_blocks[head_addr] = send_cycle + 2

        for oth_cache_id, oth_cache in enumerate(self.caches):
            if oth_cache_id == cache_id:
                continue
            if oth_cache.has_entry(addr):
                self.cache_receive_w(oth_cache_id, addr, send_cycle)
                oth_cache.set_block_state(addr, "Sc")

                # Update stat 7
                self.bus.inc_update_count()

    def simulate_read_hit(self, core_id, addr):
        cache = self.caches[core_id]
        #state = cache.get_block_state(addr)
        
        # Do nothing; set last used and done
        cache.set_block_last_used(addr, self.cur_time)

    def simulate_write_hit(self, core_id, addr):
        if self.get_head_addr(addr) in self.broadcasting_blocks.keys():
            self.early_ret = True
            return

        cache = self.caches[core_id]
        state = cache.get_block_state(addr)
        cache.set_block_last_used(addr, self.cur_time)

        if state == "M":
            # Do nothing
            pass

        if state in ["Sc", "Sm"]:
            # Check if cache should transition to 'M' or 'Sm'
            count_hold = self.count_oth_cache_hold(core_id, addr)
            addr_state = "M" if count_hold == 0 else "Sm"
            if addr_state == "Sm":
                # Broadcast the modified word to other caches
                self.broadcast_w_oth_cache(core_id, addr, self.cur_time)
            cache.set_block_state(addr, addr_state)

        if state == "E":
            # Transition to 'M'
            cache.set_block_state(addr, "M")

        # Mem does not hold an updated copy
        block_num = cache.get_block_number(addr)
        self.invalid_block[block_num] = self.INF

    def simulate_read_miss(self, core_id, addr):
        count_hold = self.count_oth_cache_hold(core_id, addr)
        state = "E" if count_hold == 0 else "Sc"
        self.cache_receive_b(core_id, addr, state)

    def simulate_write_miss(self, core_id, addr):
        cache = self.caches[core_id]
        count_hold = self.count_oth_cache_hold(core_id, addr)

        state = "M" if count_hold == 0 else "Sm"

        if state == "M":
            self.cache_receive_b(core_id, addr, "M")
        else:
            # Receive a block transfer, then broadcast the updated word to others
            self.cache_receive_b(core_id, addr, "Sm")

            send_time = cache.get_addr_usable_time(addr)
            self.broadcast_w_oth_cache(core_id, addr, send_time)

        # Memory does not hold latest copy of this block
        block_num = cache.get_block_number(addr)
        self.invalid_block[block_num] = self.INF
    
    def progressTime(self, new_time):
        for core in self.cores:
            core.progress(new_time - self.cur_time)

        self.cur_time = new_time
        self.check_mem()

        done_blocks = []
        for block, expiry in self.broadcasting_blocks.items():
            if self.cur_time >= expiry:
                # A block with a word broadcasted via BusUpd that completed
                done_blocks.append(block)

        # Resume bus transactions for blocks whose BusUpd completed
        for block in done_blocks:
            # print(f"Cycle {self.cur_time} done broadcast word of block {block}")
            del self.broadcasting_blocks[block]











