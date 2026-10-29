"""
Quick smoke test for the detector in mock mode (no trained model required).
Run with:  python -m pytest tests/test_detector.py
"""

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from detection.detector import ParkingDetector


def test_mock_mode_returns_bay_states():
    detector = ParkingDetector()
    results = detector.process_frame(None)
    assert isinstance(results, list)
    assert len(results) > 0
    for bay in results:
        assert "bay_id" in bay
        assert "occupied" in bay
        assert isinstance(bay["occupied"], bool)
