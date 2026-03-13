## Project Overview

**LCLS Data Broker** — a config-driven system for registering scientific datasets
(HDF5 or Zarr) into a [Tiled](https://blueskyproject.io/tiled/) catalog. Forked
from [tiled-catalog-broker](https://github.com/carbonscott/tiled-catalog-broker)
with added Zarr v3 support for LCLS/SFX crystallography data on Frontier.

**Hierarchy:** Dataset → Entity → Artifact
- **Datasets** are top-level containers with provenance metadata
- **Entities** are containers with queryable metadata (e.g. per-frame stats)
- **Artifacts** are array children of their parent entity

**Dual-mode access:**
- **Mode A (Expert):** Query metadata for file paths, load directly
- **Mode B (Visualizer):** Access arrays via Tiled HTTP adapters (chunked)

The broker is **dataset-agnostic**. The Parquet manifest is the contract.

## Directory Structure

```
lcls-data-broker/
├── CLAUDE.md              # This file
├── .gitignore
└── tiled_poc/             # Main implementation
    ├── config.yml         # Server configuration (port 8005)
    ├── pyproject.toml     # Package metadata
    ├── ingest.py          # CLI: bulk ingest into catalog.db
    ├── register.py        # CLI: HTTP register into running server
    └── broker/            # Core library
        ├── cli.py         # CLI entry points (broker-ingest, broker-register)
        ├── config.py      # YAML config loading
        ├── utils.py       # Shared helpers (JSON safe, shape/dtype cache)
        ├── bulk_register.py   # SQLAlchemy bulk registration
        ├── http_register.py   # HTTP registration via Tiled client
        └── catalog.py     # Catalog creation + dataset containers
```

## How to Run

```bash
cd tiled_poc

# Bulk ingest Zarr datasets from config YAMLs
python ingest.py --mimetype application/x-zarr --is-directory datasets/*.yaml

# Start Tiled server
uv run --with 'tiled[server]' tiled serve config config.yml --api-key secret

# HTTP register (incremental, into running server)
python register.py --mimetype application/x-zarr --is-directory datasets/*.yaml
```

## Key Differences from Upstream

- **Zarr v3 support:** `--mimetype` and `--is-directory` CLI flags
- **Dynamic dtype detection:** reads dtype from data files instead of hardcoding float64
- Upstream VDP/EDRIXS/Multimodal examples, tests, and docs removed
