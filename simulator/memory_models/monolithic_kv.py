"""
Monolithic KV-cache model (baseline).
"""

class MonolithicKV:
    def __init__(self, size):
        self.size = size
        self.usage = 0

    def allocate(self, amount):
        if self.usage + amount <= self.size:
            self.usage += amount
            return True
        return False

    def free(self, amount):
        self.usage = max(0, self.usage - amount)



        
