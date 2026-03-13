#!/usr/bin/env python
"""
Generic manifest generator CLI (thin wrapper).

See broker.cli.generate_main for the full implementation.

Usage:
    python generate.py datasets/my_experiment.yml -n 10
    python generate.py datasets/run001.yml datasets/run002.yml -n 10
"""
from broker.cli import generate_main

if __name__ == "__main__":
    generate_main()
