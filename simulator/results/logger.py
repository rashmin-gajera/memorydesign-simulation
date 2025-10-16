"""
Logger for simulation results.
"""

class Logger:
    def __init__(self):
        self.records = []

    def log(self, data):
        self.records.append(data)

    def save(self, filename):
        # Save human-readable text log
        with open(filename, 'w') as f:
            for record in self.records:
                f.write(f"{record}\n")

        # Save CSV for easier analysis
        csv_name = filename.replace('.txt', '.csv')
        import csv
        if not self.records:
            return
        # determine headers from first record
        headers = []
        # flatten event keys
        first = self.records[0]
        for k in ['step', 'event', 'throughput', 'memory_monolithic', 'memory_paged', 'memory_paged_compressed', 'fragmentation_monolithic', 'fragmentation_paged', 'fragmentation_paged_compressed']:
            if k in first:
                headers.append(k)

        with open(csv_name, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            for r in self.records:
                # convert event dict to string for CSV
                row = {k: r.get(k, '') for k in headers}
                if 'event' in row and isinstance(row['event'], dict):
                    row['event'] = str(row['event'])
                writer.writerow(row)
