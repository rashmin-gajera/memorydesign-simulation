"""Plotting utilities for simulation results.
Saves one image per comparison metric into an output directory.
"""
import os
import matplotlib.pyplot as plt


def plot_records(records, out_dir='results'):
    os.makedirs(out_dir, exist_ok=True)

    steps = [r['step'] for r in records]

    # Memory over time for each model
    mem_mono = [r['memory_monolithic'] for r in records]
    mem_paged = [r['memory_paged'] for r in records]
    mem_pc = [r['memory_paged_compressed'] for r in records]

    plt.figure(figsize=(10, 6))
    plt.plot(steps, mem_mono, label='Monolithic')
    plt.plot(steps, mem_paged, label='Paged')
    plt.plot(steps, mem_pc, label='Paged+Compressed')
    plt.xlabel('Step')
    plt.ylabel('Memory usage (units)')
    plt.title('Memory usage over time')
    plt.legend()
    plt.grid(True)
    mem_path = os.path.join(out_dir, 'memory_usage_comparison.png')
    plt.savefig(mem_path)
    plt.close()

    # Fragmentation comparison
    frag_mono = [r['fragmentation_monolithic'] for r in records]
    frag_paged = [r['fragmentation_paged'] for r in records]
    frag_pc = [r['fragmentation_paged_compressed'] for r in records]

    plt.figure(figsize=(10, 6))
    plt.plot(steps, frag_mono, label='Monolithic')
    plt.plot(steps, frag_paged, label='Paged')
    plt.plot(steps, frag_pc, label='Paged+Compressed')
    plt.xlabel('Step')
    plt.ylabel('Fragmentation (fraction)')
    plt.title('Fragmentation over time')
    plt.legend()
    plt.grid(True)
    frag_path = os.path.join(out_dir, 'fragmentation_comparison.png')
    plt.savefig(frag_path)
    plt.close()

    # Throughput over time
    throughput = [r['throughput'] for r in records]
    plt.figure(figsize=(10, 6))
    plt.plot(steps, throughput, label='Throughput')
    plt.xlabel('Step')
    plt.ylabel('Request size')
    plt.title('Request sizes (throughput) over time')
    plt.grid(True)
    thr_path = os.path.join(out_dir, 'throughput.png')
    plt.savefig(thr_path)
    plt.close()

    print(f"Saved plots: {mem_path}, {frag_path}, {thr_path}")
