"""
Statistics computation for simulation results.
"""

def compute_stats(records):
    if not records:
        return {}

    def peak_avg(values):
        return {'peak': max(values), 'avg': sum(values) / len(values)}

    mem_mono = [r['memory_monolithic'] for r in records]
    mem_paged = [r['memory_paged'] for r in records]
    mem_pc = [r['memory_paged_compressed'] for r in records]

    frag_mono = [r['fragmentation_monolithic'] for r in records]
    frag_paged = [r['fragmentation_paged'] for r in records]
    frag_pc = [r['fragmentation_paged_compressed'] for r in records]

    throughput = [r['throughput'] for r in records]

    return {
        'monolithic': peak_avg(mem_mono),
        'paged': peak_avg(mem_paged),
        'paged_compressed': peak_avg(mem_pc),
        'fragmentation': {
            'monolithic': sum(frag_mono) / len(frag_mono),
            'paged': sum(frag_paged) / len(frag_paged),
            'paged_compressed': sum(frag_pc) / len(frag_pc),
        },
        'throughput_avg': sum(throughput) / len(throughput),
    }
