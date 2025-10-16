import sys
from pathlib import Path

# Ensure the project root is on sys.path so local imports work when running this script
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from utils.helpers import generate_synthetic_trace
from memory_models.monolithic_kv import MonolithicKV
from memory_models.paged_kv import PagedKV
from memory_models.paged_compressed_kv import PagedCompressedKV

CONFIG = {
    'simulation_steps': 10,
    'monolithic_kv_size': 100,
    'paged_kv_num_pages': 10,
    'paged_kv_page_size': 10,
    'compression_ratio': 0.5,
    'pressure_threshold': 0.8,
}

trace = generate_synthetic_trace(CONFIG['simulation_steps'], 'mixed')
print('Generated trace:', trace)

m = MonolithicKV(CONFIG['monolithic_kv_size'])
p = PagedKV(CONFIG['paged_kv_num_pages'], CONFIG['paged_kv_page_size'])
pc = PagedCompressedKV(
    CONFIG['paged_kv_num_pages'], CONFIG['paged_kv_page_size'],
    CONFIG['compression_ratio'], CONFIG['pressure_threshold']
)

print('\nSimulating allocations:')
for i, req in enumerate(trace):
    m_ok = m.allocate(req)
    p_ok = p.allocate(req // CONFIG['paged_kv_page_size'] + 1)
    pc_ok = pc.allocate(req // CONFIG['paged_kv_page_size'] + 1)
    print(f"Step {i}: req={req:2d} | Monolithic: ok={m_ok:5} usage={m.usage:3d} | Paged: ok={p_ok:5} used_pages={sum(p.pages)} | PagedCompressed: ok={pc_ok:5} used_pages={sum(1 for x in pc.pages if x!=0)}")
