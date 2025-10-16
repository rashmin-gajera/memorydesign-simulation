"""
Main entry point for the KV-cache simulator.
"""
import yaml
from core.engine import SimulatorEngine
from memory_models.monolithic_kv import MonolithicKV
from memory_models.paged_kv import PagedKV
from memory_models.paged_compressed_kv import PagedCompressedKV
from results.logger import Logger
from results.stats import compute_stats
from results.plotter import plot_records
from utils.helpers import generate_synthetic_trace
import sys


def load_config(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)


def main(config_path):
    config = load_config(config_path)
    logger = Logger()
    trace = generate_synthetic_trace(config['simulation_steps'], 'mixed')

    # Baseline: Monolithic KV
    monolithic = MonolithicKV(config['monolithic_kv_size'])
    # Paged KV
    paged = PagedKV(config['paged_kv_num_pages'], config['paged_kv_page_size'])
    # Paged + Compression Gate
    paged_compressed = PagedCompressedKV(
        config['paged_kv_num_pages'],
        config['paged_kv_page_size'],
        config['compression_ratio'],
        config['pressure_threshold']
    )

    # Track allocations by id so we can free them later per model
    alloc_table = {}  # alloc_id -> size
    allocs_monolithic = {}  # alloc_id -> amount
    allocs_paged = {}  # alloc_id -> num_blocks
    allocs_paged_compressed = {}  # alloc_id -> num_blocks

    # Run simulation for each model and record per-step state for all three
    for step, event in enumerate(trace):
        if event['op'] == 'alloc':
            alloc_id = event['id']
            size = event['size']

            # Monolithic allocate
            ok_m = monolithic.allocate(size)
            if ok_m:
                allocs_monolithic[alloc_id] = size

            # Paged allocations use ceil conversion
            page_size = config['paged_kv_page_size']
            blocks_needed = (size + page_size - 1) // page_size
            ok_p = paged.allocate(blocks_needed)
            if ok_p:
                allocs_paged[alloc_id] = blocks_needed

            ok_pc = paged_compressed.allocate(blocks_needed)
            if ok_pc:
                allocs_paged_compressed[alloc_id] = blocks_needed
                # mark the newly allocated pages as accessed at this step for LRU
                # find indices of pages allocated (state==1) that have last_access==0
                allocated_indices = [i for i, s in enumerate(paged_compressed.pages) if s == 1 and paged_compressed.last_access[i] == 0]
                paged_compressed.touch_pages(allocated_indices, step)

            alloc_table[alloc_id] = size

        elif event['op'] == 'free':
            alloc_id = event['id']
            # free for monolithic
            if alloc_id in allocs_monolithic:
                monolithic.free(allocs_monolithic.pop(alloc_id))
            # free for paged
            if alloc_id in allocs_paged:
                paged.free(allocs_paged.pop(alloc_id))
            # free for paged_compressed
            if alloc_id in allocs_paged_compressed:
                paged_compressed.free(allocs_paged_compressed.pop(alloc_id))

        # Compute memory usage for paged models in bytes (or same units as req)
        page_size = config['paged_kv_page_size']
        paged_used_pages = sum(1 for x in paged.pages if x == 1)
        mem_paged = paged_used_pages * page_size

        pc_used_pages = sum(1 for x in paged_compressed.pages if x == 1)
        pc_compressed_pages = sum(1 for x in paged_compressed.pages if x == 2)
        mem_paged_compressed = pc_used_pages * page_size + pc_compressed_pages * page_size * config['compression_ratio']

        # Fragmentation: fraction of free pages (for paged models), monolithic placeholder 0
        frag_paged = (paged.num_pages - paged_used_pages) / paged.num_pages
        frag_paged_compressed = (paged_compressed.num_pages - (pc_used_pages + pc_compressed_pages)) / paged_compressed.num_pages
        frag_monolithic = 0.0

        throughput_val = event['size'] if event['op'] == 'alloc' else 0

        logger.log({
            'step': step,
            'event': event,
            'throughput': throughput_val,
            'memory_monolithic': monolithic.usage,
            'memory_paged': mem_paged,
            'memory_paged_compressed': mem_paged_compressed,
            'fragmentation_monolithic': frag_monolithic,
            'fragmentation_paged': frag_paged,
            'fragmentation_paged_compressed': frag_paged_compressed,
        })

    # Compute aggregated statistics and produce comparison plots
    stats = compute_stats(logger.records)
    print('Simulation stats:', stats)
    logger.save('results.txt')

    # Create comparison plots (saved to results/)
    plot_records(logger.records, out_dir='results')

if __name__ == '__main__':
    config_path = sys.argv[1] if len(sys.argv) > 1 else 'config/default_config.yaml'
    main(config_path)
