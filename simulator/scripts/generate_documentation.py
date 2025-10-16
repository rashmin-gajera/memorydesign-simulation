#!/usr/bin/env python3
"""
Generate a PDF documentation file that includes code and explanations for the simulator.

This script reads the main project files and composes a document explaining each file and
function, then writes a PDF to `docs/simulator_documentation.pdf` using reportlab.
"""
import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.units import inch


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / 'docs'
OUT_DIR.mkdir(exist_ok=True)
OUT_PDF = OUT_DIR / 'simulator_documentation.pdf'


def read_file(path):
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return f'Could not read {path}: {e}'


def make_doc():
    doc = SimpleDocTemplate(str(OUT_PDF), pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    story = []

    title = Paragraph('KV-Cache Simulator — Code documentation', styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))

    intro = Paragraph(
        'This document contains the main source files and explanations for the KV-cache simulator. ' 
        'Each file is followed by a short description of the purpose and a per-function summary where applicable.',
        styles['BodyText']
    )
    story.append(intro)
    story.append(Spacer(1, 12))

    files = [
        ('main.py', 'Top-level runner: loads config, generates trace, runs simulation loop, logs results and writes plots.'),
        ('utils/helpers.py', 'Synthetic trace generator. Produces alloc/free events with configurable lifetimes.'),
        ('memory_models/monolithic_kv.py', 'Monolithic allocator model: single scalar usage, allocate/free.'),
        ('memory_models/paged_kv.py', 'Paged allocator: fixed pages, allocate/free by blocks.'),
        ('memory_models/paged_compressed_kv.py', 'Paged allocator with compression gate and LRU-informed compression.'),
        ('results/logger.py', 'Logger: collects per-step records and saves text + CSV output.'),
        ('results/plotter.py', 'Plotter: creates PNG comparison plots for memory, fragmentation, and throughput.'),
        ('results/stats.py', 'Aggregate statistics computation for each model.'),
        ('examples/demo_payload.py', 'Small demo script that generates a short trace and prints allocation results.'),
        ('config/default_config.yaml', 'Default simulation configuration values.'),
        ('README.md', 'Project README (also present in repo).'),
    ]

    for rel, desc in files:
        path = ROOT / rel
        story.append(Paragraph(f'<b>{rel}</b>', styles['Heading2']))
        story.append(Paragraph(desc, styles['BodyText']))
        story.append(Spacer(1, 6))

        code = read_file(path)
        # Add code as preformatted block
        story.append(Preformatted(code, styles['Code']))
        story.append(Spacer(1, 12))

        # Add an auto-summary section (brief, generic) for functions
        story.append(Paragraph('Function summaries:', styles['Heading3']))
        # Provide hand-crafted summaries for the main components
        summaries = FUNCTION_SUMMARIES.get(rel, [])
        if summaries:
            for s in summaries:
                story.append(Paragraph(f"<b>{s[0]}</b>: {s[1]}", styles['BodyText']))
        else:
            story.append(Paragraph('No additional function summaries available.', styles['BodyText']))

        story.append(Spacer(1, 12))

    doc.build(story)


FUNCTION_SUMMARIES = {
    'main.py': [
        ('load_config(path)', 'Load YAML config file and return dict.'),
        ('main(config_path)', 'Main entry: loads config, instantiates models, processes trace events, logs state, computes stats, and plots results.'),
    ],
    'utils/helpers.py': [
        ('generate_synthetic_trace(num_steps, workload_type, free_probability, lifetime_range)',
         'Generates a sequence of allocation/free events; allocations are given IDs and frees scheduled after a random lifetime.'),
    ],
    'memory_models/monolithic_kv.py': [
        ('MonolithicKV.__init__(size)', 'Create monolithic allocator with capacity `size`.'),
        ('MonolithicKV.allocate(amount)', 'Attempt to allocate `amount`; increments usage if enough capacity and returns True/False.'),
        ('MonolithicKV.free(amount)', 'Frees `amount` by decreasing usage, not below zero.'),
    ],
    'memory_models/paged_kv.py': [
        ('PagedKV.__init__(num_pages, page_size)', 'Initialize pages and sizes.'),
        ('PagedKV.allocate(num_blocks)', 'Find free pages and mark them used for `num_blocks`; return True if allocated.'),
        ('PagedKV.free(num_blocks)', 'Free up to `num_blocks` used pages.'),
    ],
    'memory_models/paged_compressed_kv.py': [
        ('PagedCompressedKV.__init__', 'Initialize pages, compression_ratio, pressure_threshold, and LRU timestamps.'),
        ('effective_usage_pages()', 'Return effective pages used accounting for compressed pages.'),
        ('allocate(num_blocks)', 'Attempt allocation: may compress cold pages to make room; returns True/False.'),
        ('free(num_blocks)', 'Free used pages then compressed pages.'),
        ('compress_cold_blocks(target_free=0)', 'Perform LRU-guided grouping compression to free physical pages.'),
        ('touch_pages(indices, timestamp)', 'Update LRU timestamps for pages when accessed.'),
    ],
    'results/logger.py': [
        ('Logger.log(data)', 'Append a record to in-memory list.'),
        ('Logger.save(filename)', 'Write text log and CSV derived from records.'),
    ],
    'results/plotter.py': [
        ('plot_records(records, out_dir)', 'Render three PNGs for memory, fragmentation, throughput and save to out_dir.'),
    ],
    'results/stats.py': [
        ('compute_stats(records)', 'Calculate peak/avg memory per model, average fragmentation and throughput.'),
    ],
}


if __name__ == '__main__':
    print('Generating PDF documentation to', OUT_PDF)
    make_doc()
    print('Done')
