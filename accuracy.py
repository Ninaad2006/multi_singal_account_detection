# ─────────────────────────────────────────────
#  accuracy.py  —  Prediction accuracy tracker
#
#  Mirrors the cricket predictor accuracy module.
#
#  Workflow:
#    1. Every prediction is saved to f1_predictions.json
#    2. User records actual race winner post-race
#    3. Stats (overall %, per-circuit, per-confidence) computed on demand
# ─────────────────────────────────────────────

import json
import uuid
from datetime import datetime
from pathlib  import Path

from api import RacePrediction

PREDICTIONS_FILE = Path("f1_predictions.json")


# ── Data helpers ──────────────────────────────────────────────────────────────

def _load() -> list[dict]:
    if not PREDICTIONS_FILE.exists():
        return []
    try:
        return json.loads(PREDICTIONS_FILE.read_text())
    except (json.JSONDecodeError, OSError):
        return []


def _save(records: list[dict]) -> None:
    PREDICTIONS_FILE.write_text(json.dumps(records, indent=2))


# ── Public API ────────────────────────────────────────────────────────────────

def log_prediction(
    driver_a: str,
    driver_b: str,
    circuit: str,
    pred: RacePrediction,
) -> str:
    """
    Persist a new prediction and return its unique ID.
    actual_winner stays None until record_result() is called.
    """
    records = _load()
    record  = {
        "id":                str(uuid.uuid4())[:8],
        "timestamp":         datetime.now().isoformat(timespec="seconds"),
        "driver_a":          driver_a,
        "driver_b":          driver_b,
        "circuit":           circuit,
        "predicted_winner":  pred.winner,
        "predicted_podium":  pred.podium,
        "pole_prediction":   pred.pole_prediction,
        "winner_win_pct":    pred.winner_win_pct,
        "confidence":        pred.confidence,
        "upset_alert":       pred.upset_alert,
        "actual_winner":     None,   # filled via record_result()
        "correct":           None,   # True / False / None (pending)
        "pole_correct":      None,   # True / False / None
    }
    records.append(record)
    _save(records)
    return record["id"]


def record_result(
    prediction_id: str,
    actual_winner: str,
    actual_pole: str = "",
) -> bool:
    """
    Set the actual race winner (and optionally pole sitter) for a logged prediction.
    Marks prediction correct/wrong.
    Returns True if record found and updated, False otherwise.
    """
    records = _load()
    for r in records:
        if r["id"] == prediction_id:
            r["actual_winner"] = actual_winner
            r["correct"]       = (actual_winner == r["predicted_winner"])
            if actual_pole:
                r["actual_pole"]  = actual_pole
                r["pole_correct"] = (actual_pole == r["pole_prediction"])
            _save(records)
            return True
    return False


def get_stats() -> dict:
    """
    Compute accuracy statistics over all resolved predictions.

    Returns:
      total, resolved, pending, correct, wrong,
      overall_pct, pole_pct,
      by_confidence  { High/Medium/Low: {total, correct, pct} },
      by_circuit     { circuit: {predicted, correct, pct} },
      by_driver      { driver: {predicted, correct, pct} }
    """
    records  = _load()
    resolved = [r for r in records if r["correct"] is not None]
    pending  = [r for r in records if r["correct"] is None]

    correct = sum(1 for r in resolved if r["correct"])
    wrong   = len(resolved) - correct
    overall = round(correct / len(resolved) * 100, 1) if resolved else 0.0

    pole_resolved = [r for r in resolved if r.get("pole_correct") is not None]
    pole_correct  = sum(1 for r in pole_resolved if r.get("pole_correct"))
    pole_pct      = round(pole_correct / len(pole_resolved) * 100, 1) if pole_resolved else 0.0

    # By confidence level
    by_conf: dict[str, dict] = {}
    for level in ("High", "Medium", "Low"):
        subset = [r for r in resolved if r["confidence"] == level]
        corr   = sum(1 for r in subset if r["correct"])
        by_conf[level] = {
            "total":   len(subset),
            "correct": corr,
            "pct":     round(corr / len(subset) * 100, 1) if subset else 0.0,
        }

    # By circuit
    by_circuit: dict[str, dict] = {}
    for r in resolved:
        c = r["circuit"]
        if c not in by_circuit:
            by_circuit[c] = {"predicted": 0, "correct": 0}
        by_circuit[c]["predicted"] += 1
        if r["correct"]:
            by_circuit[c]["correct"] += 1
    for c, d in by_circuit.items():
        d["pct"] = round(d["correct"] / d["predicted"] * 100, 1) if d["predicted"] else 0.0

    # By predicted driver
    by_driver: dict[str, dict] = {}
    for r in resolved:
        drv = r["predicted_winner"]
        if drv not in by_driver:
            by_driver[drv] = {"predicted": 0, "correct": 0}
        by_driver[drv]["predicted"] += 1
        if r["correct"]:
            by_driver[drv]["correct"] += 1
    for drv, d in by_driver.items():
        d["pct"] = round(d["correct"] / d["predicted"] * 100, 1) if d["predicted"] else 0.0

    return {
        "total":         len(records),
        "resolved":      len(resolved),
        "pending":       len(pending),
        "correct":       correct,
        "wrong":         wrong,
        "overall_pct":   overall,
        "pole_pct":      pole_pct,
        "by_confidence": by_conf,
        "by_circuit":    by_circuit,
        "by_driver":     by_driver,
    }


def list_pending() -> list[dict]:
    """Return all predictions awaiting a result."""
    return [r for r in _load() if r["correct"] is None]


def list_all() -> list[dict]:
    """Return every logged prediction."""
    return _load()
