from collections import deque


class Core():
    def __init__(self, traces, ID):
        self.state = 0  # 0 for free, 1 for busy_wait, 2 for busy
        self.next_free = -1
        self.ID = ID
        self.lastBusAccess = -1
        self.execCycles = 0
        self.compCycles = 0
        self.idleCycles = 0
        self.loadCount = 0
        self.storeCount = 0
        self.cacheMissCount = 0
        self.privateAccessCount = 0
        self.traceQ = deque(traces)

    def set_busy_wait(self):
        self.next_free = int(2e9+10)
        self.state = 1

    def set_busy(self, next_free):
        self.next_free = next_free
        self.state = 2

    def set_free(self):
        self.next_free = -1
        self.state = 0

    def is_free(self):
        return self.state == 0

    def is_busy_wait(self):
        return self.state == 1

    def is_busy(self):
        return self.state == 2

    def get_next_free(self):
        return self.next_free

    def refresh(self, cur_time):
        if self.state == 2 and cur_time >= self.get_next_free():
            self.set_free()

    def is_finish(self):
        return self.is_free() and len(self.traceQ)==0

    def peek_trace(self):
        assert len(self.traceQ) != 0 
        return self.traceQ[0] 

    def pop_trace(self):
        if self.traceQ:
            return self.traceQ.popleft()

    def get_ID(self):
        return self.ID

    def get_last_bus_access(self):
        return self.lastBusAccess

    def set_last_bus_access(self, time):
        self.lastBusAccess = time

    def inc_load_count(self):
        self.loadCount += 1

    def get_load_count(self):
        return self.loadCount

    def inc_store_count(self):
        self.storeCount += 1

    def get_store_count(self):
        return self.storeCount

    def inc_cache_miss_count(self):
        self.cacheMissCount += 1

    def get_cache_miss_count(self):
        return self.cacheMissCount

    def inc_private_access_count(self):
        self.privateAccessCount += 1

    def get_private_access_count(self):
        return self.privateAccessCount

    def get_exec_cycles(self):
        return self.execCycles

    def inc_exec_cycles(self, cycles):
        self.execCycles += cycles

    def get_idle_cycles(self):
        return self.idleCycles

    def inc_idle_cycles(self, cycles):
        self.idleCycles += cycles

    def get_comp_cycles(self):
        return self.compCycles

    def inc_comp_cycles(self, cycles):
        self.compCycles += cycles

    def progress(self, cycles):
        if self.is_finish():
            return  # Freeze finished core

        assert cycles > 0
        self.inc_exec_cycles(cycles)  # Stat 1

if __name__ == "__main__":
    # 1. 创建一个 Core 实例
    traces = [(1, 100), (2, 20), (0, 300)]  # 示例跟踪数据
    core = Core(traces, ID=1)
    print(core.traceQ)
    core.pop_trace()
    print(core.traceQ)
    
    # 2. 调用 Core 方法
    '''core.set_busy(10)  # 假设核心在时间 10 变为忙碌状态
    core.inc_exec_cycles(5)  # 增加 5 个执行周期
    core.inc_load_count()  # 增加一个加载操作
    core.inc_store_count()  # 增加一个存储操作
    core.inc_cache_miss_count()  # 增加一个缓存未命中
    core.inc_private_access_count()  # 增加一个私有访问
    core.progress(3)  # 进行 3 个周期的进度
    
    # 3. 检查 Core 的状态和统计信息
    print("Core ID:", core.get_ID())
    print("Is Core Free?", core.is_free())
    print("Execution Cycles:", core.get_exec_cycles())
    print("Load Count:", core.get_load_count())
    print("Store Count:", core.get_store_count())
    print("Cache Miss Count:", core.get_cache_miss_count())
    print("Private Access Count:", core.get_private_access_count())
'''