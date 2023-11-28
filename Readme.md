![title](https://github.com/XavierWangHX/Cache-Coherence-Simulator/blob/main/img/title.png) 

Run Demo：python main.py MESI overlap 4096 2 16

Cycles 0
7 10 1 1

Stat 1: (Exec time)
Core 0: 507 cycle(s) | Core 1: 1011 cycle(s) | Core 2: 1 cycle(s) | Core 3: 50 cycle(s) |
Total: 1011 cycle(s)

Stat 2: (Compute time)
Core 0: 3 cycle(s) | Core 1: 7 cycle(s) | Core 2: 1 cycle(s) | Core 3: 50 cycle(s) |

Stat 3: (Load/Store)
Core 0: 1 load(s), 3 store(s) | Core 1: 1 load(s), 5 store(s) | Core 2: 0 load(s), 0 store(s) | Core 3: 0 load(s), 0 store(s) |

Stat 4: (Idle time)
Core 0: 504 cycle(s) | Core 1: 1004 cycle(s) | Core 2: 0 cycle(s) | Core 3: 0 cycle(s) |

Stat 5: (Cache miss rate)
Core 0: 100.00% | Core 1: 100.00% | Core 2: Nan  | Core 3: Nan  |

Stat 6: (Bus traffic amount)
272 byte(s)

Stat 7: (Invalidation / Update / Write-back)
Invalidation: 2 time(s) | Update: 0 time(s) | Write-back: 7 time(s) |

Stat 8: (Private access distribution)
Core 0: 4 / 4 = 100.00% | Core 1: 5 / 6 = 83.33% | Core 2: 0 / 0 = Nan | Core 3: 0 / 0 = Nan |
Total : 9 / 10 = 90.00%

![black](https://github.com/XavierWangHX/Cache-Coherence-Simulator/blob/main/img/black.png) 
![body](https://github.com/XavierWangHX/Cache-Coherence-Simulator/blob/main/img/body.png) 
![fluid](https://github.com/XavierWangHX/Cache-Coherence-Simulator/blob/main/img/fluid.png) 
