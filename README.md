# KV-Cache Simulator — Memory Design & Implementation

This repository contains a small simulator to experiment with different in-memory key-value cache layouts and memory management policies. It provides three kernel memory models (monolithic, paged, and paged + compression gate), a synthetic trace generator, logging, and plotting utilities for comparing behavior.

## Project structure

```
simulator/
├── main.py                   # Main entry point to run the simulation
├── README.md                 # This file
├── config/
│   └── default_config.yaml   # Default simulation parameters
├── core/
│   └── engine.py             # Simulation engine scaffold (event loop placeholder)
├── examples/
│   └── demo_payload.py       # Small demo script that prints a sample trace and allocations
├── interface/
│   └── cli.py                # Simple CLI parser (placeholder)
├── memory_models/
│   ├── monolithic_kv.py      # Monolithic (single block) allocator model
│   ├── paged_kv.py           # Simple fixed-page allocator model
│   └── paged_compressed_kv.py# Paged allocator with compression gate (improved)
├── results/
│   ├── logger.py             # Simple logger that records step-by-step state
│   ├── plotter.py            # Plotting helper that saves PNG comparisons
│   └── stats.py              # Aggregated stats calculator
├── utils/
│   └── helpers.py            # Trace generator and small utilities
├── examples/                 # Example scripts
└── results.txt               # Output log produced by the simulation
```

## How payloads are generated

Payloads in this simulator are synthetic events (allocations and frees). The generator is
`utils/helpers.py::generate_synthetic_trace(num_steps, workload_type, free_probability, lifetime_range)` and it produces a list of event dicts rather than raw integers.

Event format:
- Allocation: `{'op': 'alloc', 'id': <int>, 'size': <int>}`
- Free: `{'op': 'free', 'id': <int>}`

Behavior:
- The generator schedules frees for previously allocated IDs after a randomly chosen lifetime (within `lifetime_range`).
- `free_probability` controls whether a given allocation will be scheduled to be freed at all (so you can tune churn).

Workload types still control the size distribution for allocation events:
- `short`: small allocations (random 1..4)
- `long`: larger allocations (random 8..32)
- `mixed`: random 1..32 (default used by `main.py`)

Each allocation's `size` is treated as a request size (in abstract units). For the paged models this size is converted to page blocks using ceil division by the page size.

## Memory model details

### MonolithicKV (file: `memory_models/monolithic_kv.py`)

- Concept: single contiguous pool of memory tracked by `usage` and `size`.
- API: `allocate(amount)` and `free(amount)`
  - `allocate(amount)` succeeds if `usage + amount <= size`, then increments `usage`.
  - `free(amount)` reduces `usage` but never below zero.
- Behavior: simple and fast; no fragmentation tracking, no paging or compression.
- Use cases: baseline for measuring raw memory consumption and peak usage.

### PagedKV (file: `memory_models/paged_kv.py`)

- Concept: divide the pool into `num_pages` pages, each of `page_size` units.
- State: `pages` list stores state per page: `0` = free, `1` = used.
- Allocation: requests are converted to `num_blocks = ceil(request / page_size)` (main uses the correct ceil formula). The allocator scans for free pages and marks pages used until the requested number of blocks is allocated.
- Fragmentation: can be approximated by counting free vs used pages.
- Limitations: greedy allocation (first free pages), no reuse pattern beyond simple `free`.

### PagedCompressedKV (file: `memory_models/paged_compressed_kv.py`)

- Concept: similar to `PagedKV` but supports a compression gate which packs several used pages into fewer physical pages by compressing them.
- States per page: `0` = free, `1` = used (uncompressed), `2` = compressed.
- Compression model (implemented):
  - `compression_ratio` is a fraction in (0,1). A compressed page counts as `compression_ratio` page-equivalents for effective usage.
  - The model uses an LRU-informed compression policy: each page records a `last_access` timestamp. When compression is triggered, colder (less recently used) pages are prioritized.
  - A heuristic groups `group_size = round(1 / compression_ratio)` used pages and packs them into a single compressed page, freeing `group_size - 1` physical pages. The coldest pages are grouped first.
  - The allocator checks `effective_usage_pages = used + compressed * compression_ratio` and attempts to compress (guided by LRU) to satisfy allocation requests if needed.
- Freeing: `free` prefers to free uncompressed used pages and then compressed pages.
- Notes: This is still a heuristic model but now respects recency via LRU timestamps and preferentially compresses cold pages.

## Configuration

Default config is in `config/default_config.yaml`. Typical keys:
- `simulation_steps`: number of steps to simulate
- `monolithic_kv_size`: capacity of monolithic model (units)
- `paged_kv_num_pages`: number of pages used by page-based models
- `paged_kv_page_size`: page size in units
- `compression_ratio`: compression savings for compressed page (0 < r < 1)
- `pressure_threshold`: fraction of usage above which compression is triggered

## Running the simulator

Install dependencies (recommended in a virtualenv):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Then run the simulation:

```bash
python3 main.py              # uses config/default_config.yaml by default
python3 main.py config/default_config.yaml
```

Outputs:
- `results.txt` (text log of per-step records)
- `results.csv` (CSV with one row per step: step,event,throughput,memory_monolithic,memory_paged,memory_paged_compressed,fragmentation_*)
- Plots saved in `results/`:
  - `memory_usage_comparison.png`
  - `fragmentation_comparison.png`
  - `throughput.png`

## Files of interest

- `main.py`: glue code — loads config, generates trace, instantiates models, logs state each step, computes stats and writes plots.
- `utils/helpers.py`: the synthetic trace generator.
- `memory_models/*`: three memory models.
- `results/plotter.py`: plotting helper using matplotlib to generate PNGs.
- `results/stats.py`: computes aggregated per-model stats (peak and average).

## Example workflow and experiments

- Compare different compression ratios: change `compression_ratio` in `config/default_config.yaml` and re-run `python3 main.py`.
-- Add deallocation/lifetimes: the project already includes event-based traces (alloc/free). You can tune `free_probability` and `lifetime_range` when calling `generate_synthetic_trace` to explore churn.
-- LRU-based compression is implemented in `memory_models/paged_compressed_kv.py`. Try varying `compression_ratio` and `pressure_threshold` to see how compression affects steady-state memory usage.
-- Export CSV: the logger now writes `results.csv` alongside `results.txt` for easy analysis.

## Notes & limitations

- The simulator is intentionally small and illustrative. The PagedCompressedKV compression is a heuristic, not a faithful implementation of a real compressor.
- The engine (`core/engine.py`) is a scaffold; it does not currently process events or simulate time beyond stepping through the trace in `main.py`.


