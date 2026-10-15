"""Unit and integration tests for Phase 6: Dataset Engineering, Evaluation, and QLoRA Guardrails."""

import json
from pathlib import Path
from typing import Any, Dict, List
import pytest

from backend.tests.fixtures.metrics import (
    calculate_iou,
    character_error_rate,
    word_error_rate,
)
from scripts.evaluate_pipeline import calculate_price_association_accuracy
from scripts.train_qlora import check_gpu_resources, format_multimodal_dataset


@pytest.fixture
def project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def dataset_dir(project_root: Path) -> Path:
    return project_root / "data" / "training"


def test_dataset_files_exist(dataset_dir: Path):
    """Verify that train, val, test, and manifest files exist."""
    assert (dataset_dir / "train.json").exists(), "train.json must exist"
    assert (dataset_dir / "val.json").exists(), "val.json must exist"
    assert (dataset_dir / "test.json").exists(), "test.json must exist"
    assert (dataset_dir / "dataset_manifest.json").exists(), "dataset_manifest.json must exist"


def test_zero_leakage_between_splits(dataset_dir: Path):
    """Verify strict restaurant-family and menu isolation between train, val, and test splits."""
    train_menus = json.loads((dataset_dir / "train.json").read_text(encoding="utf-8"))
    val_menus = json.loads((dataset_dir / "val.json").read_text(encoding="utf-8"))
    test_menus = json.loads((dataset_dir / "test.json").read_text(encoding="utf-8"))

    train_rests = {m["restaurant_id"] for m in train_menus}
    val_rests = {m["restaurant_id"] for m in val_menus}
    test_rests = {m["restaurant_id"] for m in test_menus}

    train_menus_ids = {m["menu_id"] for m in train_menus}
    val_menus_ids = {m["menu_id"] for m in val_menus}
    test_menus_ids = {m["menu_id"] for m in test_menus}

    # Verify menu ID uniqueness
    assert train_menus_ids.isdisjoint(val_menus_ids), "Menu ID leakage between train and val"
    assert train_menus_ids.isdisjoint(test_menus_ids), "Menu ID leakage between train and test"
    assert val_menus_ids.isdisjoint(test_menus_ids), "Menu ID leakage between val and test"

    # Verify restaurant family partition
    assert train_rests.isdisjoint(val_rests), "Restaurant family leakage between train and val"
    assert train_rests.isdisjoint(test_rests), "Restaurant family leakage between train and test"
    assert val_rests.isdisjoint(test_rests), "Restaurant family leakage between val and test"


def test_bounding_box_coordinate_constraints(dataset_dir: Path):
    """Verify all bounding boxes are within [0.0, 1.0] and have valid geometric ordering."""
    for split_file in ["train.json", "val.json", "test.json"]:
        menus = json.loads((dataset_dir / split_file).read_text(encoding="utf-8"))
        for menu in menus:
            for item in menu["items"]:
                box_2d = item["box_2d"]
                ymin, xmin, ymax, xmax = box_2d
                assert 0.0 <= ymin <= 1.0, f"Invalid ymin: {ymin}"
                assert 0.0 <= xmin <= 1.0, f"Invalid xmin: {xmin}"
                assert 0.0 <= ymax <= 1.0, f"Invalid ymax: {ymax}"
                assert 0.0 <= xmax <= 1.0, f"Invalid xmax: {xmax}"
                assert ymin < ymax, f"ymin must be < ymax for item {item['dish_id']}"
                assert xmin < xmax, f"xmin must be < xmax for item {item['dish_id']}"

                # Pixel box check
                px = item["pixel_box"]
                assert px[0] < px[2], f"pixel_xmin must be < pixel_xmax for {item['dish_id']}"
                assert px[1] < px[3], f"pixel_ymin must be < pixel_ymax for {item['dish_id']}"


def test_reading_order_integrity(dataset_dir: Path):
    """Verify reading order starts at 1 and increases sequentially."""
    test_menus = json.loads((dataset_dir / "test.json").read_text(encoding="utf-8"))
    for menu in test_menus:
        orders = [item["reading_order"] for item in menu["items"]]
        assert orders == sorted(orders), f"Reading order not sorted in {menu['menu_id']}"
        assert orders[0] == 1, f"Reading order must start at 1 in {menu['menu_id']}"


def test_iou_metric_calculation():
    """Verify IoU calculation on identical, overlapping, and disjoint boxes."""
    box_a = {"xmin": 0.1, "ymin": 0.1, "xmax": 0.5, "ymax": 0.5}
    # Identical box -> IoU = 1.0
    assert calculate_iou(box_a, box_a) == 1.0

    # Disjoint box -> IoU = 0.0
    box_b = {"xmin": 0.6, "ymin": 0.6, "xmax": 0.9, "ymax": 0.9}
    assert calculate_iou(box_a, box_b) == 0.0

    # Half overlap
    box_c = {"xmin": 0.1, "ymin": 0.1, "xmax": 0.3, "ymax": 0.5}
    iou = calculate_iou(box_a, box_c)
    assert 0.0 < iou < 1.0


def test_cer_and_wer_metrics():
    """Verify CER and WER metrics for perfect match, single-char edit, and completely different string."""
    assert character_error_rate("Margherita", "Margherita") == 0.0
    assert word_error_rate("Pizza Margherita", "Pizza Margherita") == 0.0

    # 1 edit in 10-char word
    cer = character_error_rate("Margherita", "Margherito")
    assert 0.05 < cer <= 0.15

    # Completely different
    assert character_error_rate("ABC", "XYZ") == 1.0
    assert word_error_rate("hello world", "goodbye earth") == 1.0


def test_price_association_metric():
    """Verify price association logic strips whitespace and compares correctly."""
    gt_map = {
        "Pizza Margherita": ("€8.50", {}),
        "Tiramisu": ("€6.00", {}),
    }
    pred_map = {
        "Pizza Margherita": ("€ 8.50", {}),  # with extra space
        "Tiramisu": ("€6.00", {}),
    }
    acc = calculate_price_association_accuracy(gt_map, pred_map)
    assert acc == 1.0

    # Mismatched price
    pred_map_wrong = {
        "Pizza Margherita": ("€9.00", {}),
        "Tiramisu": ("€6.00", {}),
    }
    acc_wrong = calculate_price_association_accuracy(gt_map, pred_map_wrong)
    assert acc_wrong == 0.5


def test_qlora_chatml_formatting(dataset_dir: Path):
    """Verify multimodal ChatML instruction format for QLoRA fine-tuning."""
    train_menus = json.loads((dataset_dir / "train.json").read_text(encoding="utf-8"))[:2]
    formatted = format_multimodal_dataset(train_menus, dataset_dir / "images")

    assert len(formatted) == len(train_menus)
    for sample in formatted:
        assert "messages" in sample
        messages = sample["messages"]
        assert len(messages) == 3
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"

        user_content = messages[1]["content"]
        assert any(c.get("type") == "image" for c in user_content)
        assert any(c.get("type") == "text" for c in user_content)

        assistant_text = messages[2]["content"][0]["text"]
        payload = json.loads(assistant_text)
        assert "items" in payload
        assert len(payload["items"]) > 0


def test_qlora_resource_guardrail_safe_execution():
    """Verify check_gpu_resources executes safely and returns a tuple (bool, str)."""
    passed, message = check_gpu_resources(min_vram_gb=14.0)
    assert isinstance(passed, bool)
    assert isinstance(message, str)
    assert len(message) > 0
