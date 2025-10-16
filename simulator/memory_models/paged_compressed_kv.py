"""
Paged KV-cache with compression gate.
"""

class PagedCompressedKV:
    
    def __init__(self, num_pages, page_size, compression_ratio, pressure_threshold):
        self.num_pages = num_pages
        self.page_size = page_size
        self.compression_ratio = float(compression_ratio)
        self.pressure_threshold = pressure_threshold
        self.pages = [0] * num_pages  # 0: free, 1: used, 2: compressed
        # LRU: per-page last access timestamp (higher = more recent). 0 = never used.
        self.last_access = [0] * num_pages


    def effective_usage_pages(self):
        """Return effective usage in page-equivalents: used pages count as 1, compressed count as compression_ratio."""
        used = sum(1 for s in self.pages if s == 1)
        compressed = sum(1 for s in self.pages if s == 2)
        return used + compressed * self.compression_ratio

    def allocate(self, num_blocks):
        # Check whether there's enough effective capacity
        if self.effective_usage_pages() + num_blocks > self.num_pages:
            # try to compress more to make room
            self.compress_cold_blocks(target_free=num_blocks)
            if self.effective_usage_pages() + num_blocks > self.num_pages:
                return False

        # Ensure there are enough physical free pages. If not, attempt to compress to free physical pages.
        free_pages = [i for i, s in enumerate(self.pages) if s == 0]
        if len(free_pages) < num_blocks:
            # attempt compression to free physical slots
            self.compress_cold_blocks(target_free=num_blocks - len(free_pages))
            free_pages = [i for i, s in enumerate(self.pages) if s == 0]
            if len(free_pages) < num_blocks:
                return False

        # Allocate into free pages
        for i in free_pages[:num_blocks]:
            self.pages[i] = 1
            self.last_access[i] = 0  # will be set by caller via touch
        # After allocation, check compression gate
        self.check_compression_gate()
        return True

    def free(self, num_blocks):
        # Free used pages first, then compressed pages
        freed = 0
        for i in range(self.num_pages):
            if self.pages[i] == 1:
                self.pages[i] = 0
                self.last_access[i] = 0
                freed += 1
                if freed == num_blocks:
                    return True
        for i in range(self.num_pages):
            if self.pages[i] == 2:
                self.pages[i] = 0
                self.last_access[i] = 0
                freed += 1
                if freed == num_blocks:
                    return True
        return False

    def check_compression_gate(self):
        pressure = self.effective_usage_pages() / self.num_pages
        if pressure > self.pressure_threshold:
            # compress to try to bring pressure down
            self.compress_cold_blocks()

    def touch_pages(self, indices, timestamp):
        """Mark given page indices as accessed at timestamp (for LRU)."""
        for i in indices:
            if 0 <= i < self.num_pages:
                self.last_access[i] = timestamp

    def compress_cold_blocks(self, target_free=0):
        """
        Compress cold/used pages to free up capacity.

        Strategy (heuristic): group several used pages into a single compressed page based on compression_ratio.
        For a compression_ratio r, group_size = int(round(1 / r)) pages can be packed into 1 compressed page.
        This will free group_size - 1 physical pages per group.

        If target_free > 0, we'll try to free at least that many physical pages by performing groups.
        """
        if self.compression_ratio <= 0 or self.compression_ratio >= 1:
            # no effective compression possible
            return

        group_size = max(2, int(round(1.0 / self.compression_ratio)))

        # indices of currently used pages
        used_indices = [i for i, s in enumerate(self.pages) if s == 1]
        if not used_indices:
            return

        freed_total = 0
        # For better results, sort used pages by last_access ascending (cold first)
        used_indices.sort(key=lambda x: self.last_access[x])

        # iterate in groups of group_size over cold pages first
        i = 0
        while i + group_size <= len(used_indices):
            group = used_indices[i:i+group_size]
            # compress the group into one compressed page: pick the coldest page as the compressed target
            group_sorted = sorted(group, key=lambda x: self.last_access[x])
            first = group_sorted[0]
            others = group_sorted[1:]
            self.pages[first] = 2
            # reset last_access for compressed page to recent (simulate compression activity)
            self.last_access[first] = max(self.last_access) + 1 if self.last_access else 1
            for idx in others:
                self.pages[idx] = 0
                self.last_access[idx] = 0
            freed_total += (group_size - 1)
            i += group_size
            if target_free and freed_total >= target_free:
                break

        # try compressing smaller leftover group into 1 compressed page
        if target_free and freed_total < target_free:
            # take remaining used pages if any
            remaining = [i for i, s in enumerate(self.pages) if s == 1]
            if remaining:
                # compress all remaining into one compressed page
                first = remaining[0]
                others = remaining[1:]
                self.pages[first] = 2
                for idx in others:
                    self.pages[idx] = 0
                freed_total += len(others)


