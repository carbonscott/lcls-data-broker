"""Tests for broker.bulk_register — prepare_node_data, bulk_register, round-trip."""

import pandas as pd
import pytest
from sqlalchemy import create_engine, text

from broker.bulk_register import (
    compute_structure_id,
    init_database,
    prepare_node_data,
    bulk_register,
)
from broker.utils import _load_artifact_info


# --- compute_structure_id ---

def test_compute_structure_id_deterministic():
    structure = {"shape": [4, 4], "chunks": [[4], [4]]}
    id1 = compute_structure_id(structure)
    id2 = compute_structure_id(structure)
    assert id1 == id2
    assert isinstance(id1, str)
    assert len(id1) == 32  # MD5 hex digest


def test_compute_structure_id_differs():
    s1 = {"shape": [4, 4], "chunks": [[4], [4]]}
    s2 = {"shape": [8, 8], "chunks": [[8], [8]]}
    assert compute_structure_id(s1) != compute_structure_id(s2)


# --- prepare_node_data ---

def test_prepare_node_data(tiny_zarr, sample_manifests):
    _load_artifact_info.__defaults__[0].clear()
    ent_df, art_df = sample_manifests

    ent_nodes, art_nodes, art_data_sources = prepare_node_data(
        ent_df, art_df, max_entities=3, base_dir=str(tiny_zarr)
    )

    assert len(ent_nodes) == 3
    assert len(art_nodes) == 6  # 2 artifacts per entity
    assert len(art_data_sources) == 6

    # Check entity node structure
    ent0 = ent_nodes[0]
    assert ent0["structure_family"] == "container"
    assert "path_image" in ent0["metadata"]
    assert "path_label" in ent0["metadata"]

    # Check artifact node structure
    art0 = art_nodes[0]
    assert art0["structure_family"] == "array"
    assert "shape" in art0["metadata"]


def test_prepare_node_data_missing_key_column(tiny_zarr):
    ent_df = pd.DataFrame({"uid": ["a"], "value": [1]})  # no 'key' column
    art_df = pd.DataFrame(columns=["uid", "type", "file", "dataset", "index"])

    with pytest.raises(ValueError, match="missing required 'key' column"):
        prepare_node_data(ent_df, art_df, max_entities=1, base_dir=str(tiny_zarr))


# --- bulk_register round-trip ---

def test_bulk_register_round_trip(tiny_zarr, sample_manifests, tmp_path_factory):
    _load_artifact_info.__defaults__[0].clear()
    ent_df, art_df = sample_manifests
    db_tmp = tmp_path_factory.mktemp("db")
    db_path = str(db_tmp / "test_catalog.db")

    # Step 1: init database
    engine = init_database(db_path)

    # Step 2: prepare node data
    ent_nodes, art_nodes, art_data_sources = prepare_node_data(
        ent_df, art_df, max_entities=3, base_dir=str(tiny_zarr)
    )

    # Step 3: bulk register
    dataset_key = "test_dataset"
    dataset_metadata = {"description": "test"}
    bulk_register(
        engine, ent_nodes, art_nodes, art_data_sources,
        dataset_key=dataset_key,
        dataset_metadata=dataset_metadata,
        mimetype="application/x-zarr",
        is_directory=1,
    )

    # Step 4: verify counts
    with engine.connect() as conn:
        # Tiled root + dataset container + 3 entities + 6 artifacts = 11 nodes
        node_count = conn.execute(text("SELECT COUNT(*) FROM nodes")).fetchone()[0]
        assert node_count == 11

        # Verify closure table has entries
        closure_count = conn.execute(
            text("SELECT COUNT(*) FROM nodes_closure")
        ).fetchone()[0]
        assert closure_count > 0

        # Verify dataset container exists with correct key
        ds_row = conn.execute(
            text("SELECT key FROM nodes WHERE parent = 0 AND key = :key"),
            {"key": dataset_key},
        ).fetchone()
        assert ds_row is not None
        assert ds_row[0] == dataset_key

        # Verify data sources were created
        ds_count = conn.execute(
            text("SELECT COUNT(*) FROM data_sources")
        ).fetchone()[0]
        assert ds_count == 6
