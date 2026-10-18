"""Evaluation metrics for visual menu extraction: IoU, CER, WER, and price association."""

from typing import Any, Dict, List, Tuple


def calculate_iou(box_a: Dict[str, float], box_b: Dict[str, float]) -> float:
    """Compute Intersection over Union (IoU) between two bounding boxes with keys xmin, ymin, xmax, ymax."""
    x_left = max(box_a["xmin"], box_b["xmin"])
    y_top = max(box_a["ymin"], box_b["ymin"])
    x_right = min(box_a["xmax"], box_b["xmax"])
    y_bottom = min(box_a["ymax"], box_b["ymax"])

    if x_right < x_left or y_bottom < y_top:
        return 0.0

    intersection_area = (x_right - x_left) * (y_bottom - y_top)

    area_a = (box_a["xmax"] - box_a["xmin"]) * (box_a["ymax"] - box_a["ymin"])
    area_b = (box_b["xmax"] - box_b["xmin"]) * (box_b["ymax"] - box_b["ymin"])
    union_area = area_a + area_b - intersection_area

    if union_area <= 0:
        return 0.0

    return round(float(intersection_area / union_area), 4)


def levenshtein_distance(s1: str, s2: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def character_error_rate(reference: str, hypothesis: str) -> float:
    """Compute Character Error Rate (CER)."""
    ref = reference.strip()
    hyp = hypothesis.strip()
    if not ref:
        return 0.0 if not hyp else 1.0
    dist = levenshtein_distance(ref, hyp)
    return round(min(1.0, float(dist / len(ref))), 4)


def word_error_rate(reference: str, hypothesis: str) -> float:
    """Compute Word Error Rate (WER)."""
    ref_words = reference.strip().split()
    hyp_words = hypothesis.strip().split()
    if not ref_words:
        return 0.0 if not hyp_words else 1.0

    ref_len = len(ref_words)
    hyp_len = len(hyp_words)
    dp = [[0] * (hyp_len + 1) for _ in range(ref_len + 1)]

    for i in range(ref_len + 1):
        dp[i][0] = i
    for j in range(hyp_len + 1):
        dp[0][j] = j

    for i in range(1, ref_len + 1):
        for j in range(1, hyp_len + 1):
            cost = 0 if ref_words[i - 1].lower() == hyp_words[j - 1].lower() else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,      # deletion
                dp[i][j - 1] + 1,      # insertion
                dp[i - 1][j - 1] + cost  # substitution
            )

    return round(min(1.0, float(dp[ref_len][hyp_len] / ref_len)), 4)


def evaluate_extraction_batch(
    predicted_items: List[Dict[str, Any]],
    ground_truth_items: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compare extracted dish blocks with ground truth annotations.
    Computes exact matches, mean IoU, price association, and error rates.
    """
    total_gt = len(ground_truth_items)
    if total_gt == 0:
        return {"error": "Empty ground truth"}

    matched_dishes = 0
    correct_prices = 0
    ious: List[float] = []
    cers: List[float] = []
    wers: List[float] = []

    for gt in ground_truth_items:
        gt_name = gt["original_name"].lower()
        gt_price = (gt.get("price_display") or "").replace(" ", "")
        gt_box = gt.get("ground_truth_box")

        # Find best matching predicted dish
        best_pred = None
        best_name_sim = 1.0

        for pred in predicted_items:
            pred_name = (pred.get("original_name") or "").lower()
            cer = character_error_rate(gt_name, pred_name)
            if cer < best_name_sim:
                best_name_sim = cer
                best_pred = pred

        if best_pred and best_name_sim <= 0.2:  # Tolerant name match (CER <= 20%)
            matched_dishes += 1
            cers.append(best_name_sim)
            wers.append(word_error_rate(gt_name, (best_pred.get("original_name") or "").lower()))

            # Check price association
            pred_price = (best_pred.get("price_display") or "").replace(" ", "")
            if gt_price and pred_price and gt_price == pred_price:
                correct_prices += 1

            # Check bounding box IoU if coordinates are present
            if gt_box and "bounding_box" in best_pred:
                pbox = best_pred["bounding_box"]
                pbox_dict = {
                    "xmin": pbox.xmin if hasattr(pbox, "xmin") else pbox.get("xmin", 0),
                    "ymin": pbox.ymin if hasattr(pbox, "ymin") else pbox.get("ymin", 0),
                    "xmax": pbox.xmax if hasattr(pbox, "xmax") else pbox.get("xmax", 1),
                    "ymax": pbox.ymax if hasattr(pbox, "ymax") else pbox.get("ymax", 1),
                }
                ious.append(calculate_iou(gt_box, pbox_dict))

    return {
        "ground_truth_count": total_gt,
        "predicted_count": len(predicted_items),
        "dish_match_rate": round(matched_dishes / total_gt, 3),
        "price_association_accuracy": round(correct_prices / max(1, matched_dishes), 3),
        "mean_iou": round(sum(ious) / max(1, len(ious)), 3) if ious else 0.0,
        "mean_cer": round(sum(cers) / max(1, len(cers)), 3) if cers else 0.0,
        "mean_wer": round(sum(wers) / max(1, len(wers)), 3) if wers else 0.0,
    }
