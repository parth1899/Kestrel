#!/usr/bin/env python3
# analytics-service/scripts/train_baseline.py
"""
Train one IsolationForest baseline per event type (process, file, network, system).

The script:
1. Scans tests/fixtures/enriched_*.json
2. Calls the *same* feature-extractor that the streaming detector uses
3. Trains an IsolationForest (contamination=0.1) on the numeric feature vector
4. Persists the model as models/isolation_forest_<type>.pkl
"""

import json
from pathlib import Path
from typing import List

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

# --------------------------------------------------------------------------- #
# Runtime feature-extractor factory – imported *once* at the top level
# --------------------------------------------------------------------------- #
from features import get_extractor          # <-- safe: only features → no core
from core.models import EnrichedEvent        # <-- safe: Pydantic model only

# --------------------------------------------------------------------------- #
# Configurable constants
# --------------------------------------------------------------------------- #
CONTAMINATION = 0.1
RANDOM_STATE = 42
MODEL_DIR = Path(__file__).parent.parent / "models"
MODEL_DIR.mkdir(parents=True, exist_ok=True)


def _load_events(fixture_dir: Path) -> List[EnrichedEvent]:
    """Read every ``enriched_*.json`` file and return Pydantic objects."""
    events: List[EnrichedEvent] = []
    for p in fixture_dir.glob("enriched_*.json"):
        with open(p, "r", encoding="utf-8") as f:
            raw = json.load(f)
            events.append(EnrichedEvent(**raw))
    return events


def _train_one_type(event_type: str, events: List[EnrichedEvent]) -> None:
    """Train and persist an IsolationForest for a single event type."""
    extractor = get_extractor(event_type)

    vectors: List[List[float]] = []
    for ev in events:
        if ev.event_type != event_type:
            continue
        feats = extractor.extract(ev)

        # Keep **only numeric** values (int / float / bool → 0/1)
        vec = [
            float(v) for v in feats.values()
            if isinstance(v, (int, float, bool))
        ]
        if vec:
            vectors.append(vec)

    if not vectors:
        print(f"[WARN] No numeric features for event_type={event_type!r} – skipping.")
        return

    X = np.array(vectors, dtype=np.float32)
    print(f"[TRAIN] {event_type!r}: {X.shape[0]} samples, {X.shape[1]} features")

    model = IsolationForest(
        contamination=CONTAMINATION,
        random_state=RANDOM_STATE,
        n_jobs=-1,
    )
    model.fit(X)

    out_path = MODEL_DIR / f"isolation_forest_{event_type}.pkl"
    joblib.dump(model, out_path)
    print(f"[SAVED] → {out_path}")


def main() -> None:
    fixture_dir = Path(__file__).parent.parent / "tests" / "fixtures"
    if not fixture_dir.is_dir():
        raise RuntimeError(f"Fixture directory missing: {fixture_dir}")

    print(f"[INFO] Loading enriched events from {fixture_dir}")
    events = _load_events(fixture_dir)
    print(f"[INFO] Loaded {len(events)} enriched events")

    seen = {ev.event_type for ev in events}
    for et in sorted(seen):
        _train_one_type(et, events)

    print("[SUCCESS] All baseline models saved in models/")


if __name__ == "__main__":
    main()