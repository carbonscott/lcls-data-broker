"""Tests for broker.utils — pure functions and Zarr/HDF5 helpers."""

import numpy as np

from broker.utils import (
    to_json_safe,
    make_artifact_key,
    get_artifact_shape,
    get_artifact_dtype,
    _load_artifact_info,
)


# --- to_json_safe ---

def test_to_json_safe_numpy_int():
    result = to_json_safe(np.int64(42))
    assert result == 42
    assert isinstance(result, int)


def test_to_json_safe_numpy_float():
    result = to_json_safe(np.float32(3.14))
    assert isinstance(result, float)
    assert abs(result - 3.14) < 0.01


def test_to_json_safe_numpy_array():
    result = to_json_safe(np.array([1, 2]))
    assert result == [1, 2]
    assert isinstance(result, list)


def test_to_json_safe_nan():
    result = to_json_safe(float("nan"))
    assert result is None


def test_to_json_safe_passthrough():
    assert to_json_safe("hello") == "hello"
    assert to_json_safe(42) == 42


# --- make_artifact_key ---

def test_make_artifact_key():
    assert make_artifact_key({"type": "image"}) == "image"


def test_make_artifact_key_with_prefix():
    assert make_artifact_key({"type": "image"}, prefix="path_") == "path_image"


# --- get_artifact_shape / get_artifact_dtype (Zarr) ---

def test_get_artifact_shape_zarr(tiny_zarr):
    # Clear cache to avoid cross-test interference
    _load_artifact_info.__defaults__[0].clear()
    shape = get_artifact_shape(str(tiny_zarr), "test_exp_r0001.0000.zarr", "images")
    assert shape == [3, 4, 4]


def test_get_artifact_shape_with_index(tiny_zarr):
    _load_artifact_info.__defaults__[0].clear()
    shape = get_artifact_shape(
        str(tiny_zarr), "test_exp_r0001.0000.zarr", "images", index=0
    )
    assert shape == [4, 4]


def test_get_artifact_dtype_zarr(tiny_zarr):
    _load_artifact_info.__defaults__[0].clear()
    dtype = get_artifact_dtype(str(tiny_zarr), "test_exp_r0001.0000.zarr", "images")
    assert dtype == np.float32
