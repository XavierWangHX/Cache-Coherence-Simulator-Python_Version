from Core import*
from Cache import*
from Bus import*
import heapq
class Simulator:
    def __init__(self, cache_size, assoc, block_size, core_traces):
        self.earlyRet = False
        self.cur_time = 0
        self.block_size = block_size
        self.cores = [Core(trace, i) for i, trace in enumerate(core_traces)]
        self.caches = [Cache(assoc, block_size, cache_size, i) for i in range(len(core_traces))]
        self.bus = Bus(block_size)
        self.invalid_block = {}
        self.active_blocks = {}
        self.INF = 100000000
        
        

    def get_head_addr(self, addr):
        return (addr // self.block_size) * self.block_size

    def get_mem_block_available_time(self, block_num):
        return self.invalid_block.get(block_num, self.cur_time)

    def cache_write_back_mem(self, cache_id, addr):
        cache = self.caches[cache_id]
        block_num = cache.get_block_number(addr)
        self.invalid_block[block_num] = self.cur_time + 100
        self.bus.inc_writeback_count()
        self.bus.inc_traffic_block()

    def check_mem(self):
        '''for i in self.invalid_block.items():
            print(i[0],i[1])
        print()
'''


        '''unfreeze_blocks = []

        for i in self.invalid_block.items():
            if i[1] == self.cur_time:
                unfreeze_blocks.append(i[0])
        for i in unfreeze_blocks:
            del self.invalid_block[i]'''
        


        unfreeze_blocks = [block for block, time in self.invalid_block.items() if time == self.cur_time]
        for block in unfreeze_blocks:
            del self.invalid_block[block]

    def print_stat(self):

        print("Stat 1: (Exec time)")
        print("| ",end="")
        max_exec_time = -1
        for core_id, core in enumerate(self.cores):
            core_exec_time = core.get_exec_cycles()
            max_exec_time = max(max_exec_time, core_exec_time)
            print(f"Core {core_id}: {core_exec_time} cycle(s)",end=" | ")
        print()
        print(f"Total: {max_exec_time} cycle(s)")

        print("------------------------------------")

        print("Stat 2: (Compute time)")
        print("| ",end="")
        for core_id, core in enumerate(self.cores):
            print(f"Core {core_id}: {core.get_comp_cycles()} cycle(s)",end=" | ")
        print()

        print("------------------------------------")

        print("Stat 3: (Load/Store)")
        print("| ",end="")
        for core_id, core in enumerate(self.cores):
            print(f"Core {core_id}: {core.get_load_count()} load(s), {core.get_store_count()} store(s)",end=" | ")
        print()

        print("------------------------------------")

        print("Stat 4: (Idle time)")
        print("| ",end="")
        for core_id, core in enumerate(self.cores):
            idle_cycles = core.get_idle_cycles()
            print(f"Core {core_id}: {idle_cycles} cycle(s)",end=" | ")
            #print(f"Idle Cycles: {idle_cycles}, Comp Cycles: {comp_cycles}, Exec Cycles: {exec_cycles}")
            assert idle_cycles + core.get_comp_cycles() == core.get_exec_cycles()
        print()

        print("------------------------------------")

        print("Stat 5: (Cache miss rate)")
        print("| ",end="")
        for core_id, core in enumerate(self.cores):
            total_accesses = core.get_load_count() + core.get_store_count()
            if total_accesses != 0:
                ratio = core.get_cache_miss_count() / total_accesses
                print(f"Core {core_id}: {ratio:.2%}",end=" | ")
            else:
                ratio = 'Nan'
                print(f"Core {core_id}: {ratio} ",end=" | ")
        print()

        print("------------------------------------")

        print("Stat 6: (Bus traffic amount)")
        print("| ",end="")
        print(f"{self.bus.get_traffic_data()} byte(s)",end=" |")
        print()

        print("------------------------------------")

        print("Stat 7: (Invalidation / Update / Write-back)")
        print("| ",end="")
        print(f"Invalidation: {self.bus.get_invalidate_count()} time(s)",end=" | ")
        print(f"Update: {self.bus.get_update_count()} time(s)",end=" | ")
        print(f"Write-back: {self.bus.get_writeback_count()} time(s)",end=" | \n")

        print("------------------------------------")

        print("Stat 8: (Private access distribution)")
        total_priv = total_acc = 0
        print("| ",end="")
        for core_id, core in enumerate(self.cores):
            priv = core.get_private_access_count()
            tot = core.get_load_count() + core.get_store_count()
            if tot != 0:
                ratio = priv / tot
                print(f"Core {core_id}: {priv} / {tot} = {ratio:.2%}",end=" | ")
            else:
                print(f"Core {core_id}: {priv} / {tot} = Nan",end=" | ")
            total_priv += priv
            total_acc += tot
        print()
        
        if total_acc != 0:
            total_ratio = total_priv / total_acc 
            print(f"Total : {total_priv} / {total_acc} = {total_ratio:.2%}")
        else:
            print(f"Total : {total_priv} / {total_acc} = Nan")

    def is_all_finish(self):
        return all(core.is_finish() for core in self.cores)


    def check_release_core(self):
        exist = False
        for core_id, core in enumerate(self.cores):
            if core.is_finish():
                continue  # Freeze finished core
            core.refresh(self.cur_time)

            if core.is_free():
                exist = True

        # Directly iterate and delete from the active_blocks dictionary
        for block in list(self.active_blocks.keys()):  # Create a static list of keys to avoid RuntimeError during iteration
            core_id = self.active_blocks[block]
            if self.cores[core_id].is_free() or self.cores[core_id].is_finish():
                del self.active_blocks[block]

        return exist
    
 

    def check_core_req(self):
    # 使用优先队列来管理核心请求
        core_queue = [(core.get_next_free(), core_id) for core_id, core in enumerate(self.cores) if not core.is_finish()]
        heapq.heapify(core_queue)

        exist = False
        serve_cache_req = False  # 追踪是否有缓存请求正在服务

        while core_queue:
            next_free, core_id = heapq.heappop(core_queue)
            core = self.cores[core_id]

            if core.is_finish() or not core.is_free():
                continue

            exist = True
            trace_type, addr = core.peek_trace()

            if trace_type in (0, 1):  # Load/store instruction
                cache = self.caches[core_id]

                if cache.has_entry(addr):
                    exist = True
                    # Read hit
                    if trace_type == 0:
                        core.pop_trace()
                        
                        self.simulate_read_hit(cache.ID, addr)
                    # Write hit
                    elif trace_type == 1:
                        
                        if self.get_head_addr(addr) not in self.active_blocks:
                            self.earlyRet = False
                            self.simulate_write_hit(cache.ID, addr)
                            if (self.earlyRet) :
                                core.inc_idle_cycles(1)
                                continue
                            core.pop_trace()
                            
                        else:
                            core.inc_idle_cycles(1)
                            continue
                else:
                    
                    if serve_cache_req or self.get_head_addr(addr) in self.active_blocks:
                        core.inc_idle_cycles(1)
                        continue

                    serve_cache_req = True
                    exist = True
                    core.pop_trace()
                    
                    core.inc_cache_miss_count()
                    self.active_blocks[self.get_head_addr(addr)] = core_id
                    core.set_last_bus_access(self.cur_time)

                    if trace_type == 0:
                        self.simulate_read_miss(cache.ID, addr)
                    elif trace_type == 1:
                        self.simulate_write_miss(cache.ID, addr)

                if cache.is_addr_private(addr):
                    core.inc_private_access_count()

                if trace_type == 0:
                    core.inc_load_count()
                elif trace_type == 1:
                    core.inc_store_count()

                next_free = max(self.cur_time, cache.get_addr_usable_time(addr)) + 1
                core.inc_idle_cycles(next_free - self.cur_time)
                core.set_busy(next_free)

            elif trace_type == 2:  # Compute instruction

                exist = True
                core.pop_trace()
                
                core.set_busy(self.cur_time + addr)
                core.inc_comp_cycles(addr)

        return exist

    def progressTime(self, new_time):
        pass

    def simulate(self):
        while not self.is_all_finish():
            
                
            if self.cur_time % 1000000 == 0:
                print("Cycles", self.cur_time)
                print(*[len(core.traceQ) for core in self.cores])

            
            
            self.check_release_core()
            self.check_core_req()
            
            self.progressTime(self.cur_time + 1)


        self.print_stat()

