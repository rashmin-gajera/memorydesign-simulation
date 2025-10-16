"""
Command-line interface for the simulator.
"""
import argparse

def parse_args():
    parser = argparse.ArgumentParser(description='KV-cache Simulator')
    parser.add_argument('--config', type=str, default='../config/default_config.yaml', help='Path to config file')
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    print(f"Using config: {args.config}")
    # TODO: Load config and run simulation
