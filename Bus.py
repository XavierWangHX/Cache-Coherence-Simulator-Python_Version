class Bus:
    def __init__(self, block_size):
        self.block_size = block_size
        self.traffic_data = 0
        self.invalidate_count = 0
        self.update_count = 0
        self.writeback_count = 0

    def get_word_per_block(self):
        return self.block_size // 4  # Assuming a word is 4 bytes

    def get_traffic_data(self):
        return self.traffic_data

    def inc_traffic_block(self, num_block=1):
        self.traffic_data += num_block * self.block_size
    def inc_traffic_word(self, num_word=1):
        self.traffic_data += num_word*4

    def inc_invalidate_count(self):
        self.invalidate_count += 1

    def get_invalidate_count(self):
        return self.invalidate_count

    def inc_update_count(self):
        self.update_count += 1

    def get_update_count(self):
        return self.update_count

    def inc_writeback_count(self):
        self.writeback_count += 1

    def get_writeback_count(self):
        return self.writeback_count
