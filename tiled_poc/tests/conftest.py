"""Shared test fixtures for lcls-data-broker tests."""

import numpy as np
import pandas as pd
import pytest
import zarr


@pytest.fixture
def tiny_zarr(tmp_path):
    """Create a minimal Zarr store with images and labels arrays.

    Returns tmp_path which acts as base_dir for the broker functions.
    """
    store_path = tmp_path / "test_exp_r0001.0000.zarr"
    root = zarr.open(str(store_path), mode="w")
    root.create_array("images", data=np.ones((3, 4, 4), dtype=np.float32))
    root.create_array("labels", data=np.zeros((3, 4, 4), dtype=np.int8))
    return tmp_path


@pytest.fixture
def sample_manifests(tiny_zarr):
    """Build entity and artifact DataFrames that reference the tiny Zarr store.

    Returns (ent_df, art_df).
    """
    zarr_rel = "test_exp_r0001.0000.zarr"

    ent_rows = []
    art_rows = []
    for i in range(3):
        uid = f"uid_{i:04d}"
        ent_rows.append({
            "uid": uid,
            "key": f"entity_{i:04d}",
            "frame_index": i,
            "mean_intensity": float(i) * 1.5,
        })
        art_rows.append({
            "uid": uid,
            "type": "image",
            "file": zarr_rel,
            "dataset": "images",
            "index": i,
        })
        art_rows.append({
            "uid": uid,
            "type": "label",
            "file": zarr_rel,
            "dataset": "labels",
            "index": i,
        })

    ent_df = pd.DataFrame(ent_rows)
    art_df = pd.DataFrame(art_rows)
    return ent_df, art_df


@pytest.fixture
def sample_config(tmp_path):
    """Write a minimal config.yml and return its path."""
    config_path = tmp_path / "config.yml"
    config_path.write_text(
        "broker:\n"
        '  service_dir: "."\n'
        '  data_dir: "."\n'
        '  schema_version: "data"\n'
        "  max_entities: 10\n"
    )
    return config_path
