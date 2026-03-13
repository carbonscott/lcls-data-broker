# LCLS Data Broker

A config-driven system for registering scientific datasets (HDF5 or Zarr) into a
[Tiled](https://blueskyproject.io/tiled/) catalog and retrieving them via two
access modes:

- **Mode A (Expert):** Query metadata for file paths, load directly -- fast, ideal for ML pipelines.
- **Mode B (Visualizer):** Access arrays as Tiled children via HTTP -- chunked, interactive.

The broker is **dataset-agnostic**. The Parquet manifest is the contract: no
parameter names, artifact types, or file layouts are hardcoded.

---

## Prerequisites

- Python >= 3.10
- [`uv`](https://docs.astral.sh/uv/) (manages dependencies inline -- no install step)

---

## Workflow Overview

The three CLI scripts form a pipeline:

```
generate.py          ingest.py             tiled serve
  (manifests)   --->   (catalog.db)   --->   (HTTP API)
                       [offline bulk]        [serve queries]

                     register.py
                       [online HTTP]  --->   (running server)
```

| Script | Purpose | Server needed? |
|--------|---------|----------------|
| `generate.py` | Scan data files, produce Parquet manifests | No |
| `ingest.py` | Bulk-load manifests into `catalog.db` (SQLAlchemy) | No |
| `register.py` | Register manifests into a running server (HTTP) | Yes |

**When to use which registration method:**

| Scenario | Use | Speed |
|----------|-----|-------|
| Initial load of 1K+ entities | `ingest.py` | ~2,250 nodes/sec |
| Incremental updates to a live server | `register.py` | ~5 nodes/sec |

---

## Usage

### Bulk Ingest (HDF5)

```bash
python ingest.py datasets/*.yaml
```

### Bulk Ingest (Zarr)

```bash
python ingest.py --mimetype application/x-zarr --is-directory datasets/*.yaml
```

### Start Tiled Server

```bash
uv run --with 'tiled[server]' tiled serve config config.yml --api-key secret
```

### HTTP Registration (Incremental)

```bash
# HDF5 (default)
python register.py datasets/*.yaml

# Zarr
python register.py --mimetype application/x-zarr --is-directory datasets/*.yaml

# Limit to 5 entities per dataset
python register.py -n 5 datasets/*.yaml
```

---

## Adding a New Dataset

Two things are needed:

### 1. Dataset Config (`datasets/mydata.yml`)

```yaml
key: mydata_run001
label: My Dataset Run 001
base_dir: /path/to/data/root
metadata:
  experiment: my_experiment
  description: Run 001
```

- `key` -- Unique identifier for the dataset container in the catalog.
- `label` -- Human-readable name (for logging).
- `base_dir` -- Root directory. All file paths in the manifest are relative to this.
- `metadata` -- Arbitrary metadata dict for the dataset container.

### 2. Parquet Manifests (`manifests/`)

**Entity manifest** (`mydata_run001_entities.parquet`) -- one row per entity:

| Column | Required | Description |
|--------|----------|-------------|
| `uid` | Yes | Unique identifier |
| `key` | Yes | Tiled container key (human-readable) |
| *(any others)* | No | Become container metadata automatically |

**Artifact manifest** (`mydata_run001_artifacts.parquet`) -- one row per artifact:

| Column | Required | Description |
|--------|----------|-------------|
| `uid` | Yes | Links to parent entity |
| `type` | Yes | Artifact type key (e.g. `assembled`, `peaknet`) |
| `file` | Yes | Relative path to data file (from `base_dir`) |
| `dataset` | Yes | Internal dataset path (e.g. `/data` for Zarr, `/entry/data` for HDF5) |
| `index` | No | Row index for batched arrays |
| *(any others)* | No | Become artifact metadata automatically |

### 3. Server Config

Add your `base_dir` to `readable_storage` in `config.yml`:

```yaml
readable_storage:
  - "/path/to/data/root"
```

---

## Troubleshooting

### Port already in use
```bash
lsof -ti :8005 | xargs kill
```

### Re-ingesting data
`ingest.py` is **additive** -- running it twice creates duplicates. To
re-ingest, delete `catalog.db` first. `register.py` is **incremental** and
safe to run multiple times.
