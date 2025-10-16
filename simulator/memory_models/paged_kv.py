"""
Paged KV-cache model.
"""

class PagedKV:
    def __init__(self, num_pages, page_size):
        self.num_pages = num_pages
        self.page_size = page_size
        self.pages = [0] * num_pages  # 0: free, 1: used

    def allocate(self, num_blocks):
        allocated = 0
        for i in range(self.num_pages):
            if self.pages[i] == 0:
                self.pages[i] = 1
                allocated += 1
                if allocated == num_blocks:
                    return True
        return False

    def free(self, num_blocks):
        freed = 0
        for i in range(self.num_pages):
            if self.pages[i] == 1:
                self.pages[i] = 0
                freed += 1
                if freed == num_blocks:
                    return True
        return False
