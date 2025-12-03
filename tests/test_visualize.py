"""
Unit tests for visualize_swing module

Tests the visualization with detection failures and confidence scoring.
"""

import sys
import os

# Add parent directory to path to import visualize_swing
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from visualize_swing import _assign_phases_to_frames, _get_phase_color


def test_assign_phases_with_all_detected():
    """Test phase assignment when all phases are detected."""
    print("\n" + "="*60)
    print("TESTING PHASE ASSIGNMENT - ALL DETECTED")
    print("="*60)

    phases = {
        "backswing_start": {
            "detected": True,
            "confidence": 0.85,
            "frame": 10,
            "timestamp": 0.33
        },
        "max_backswing": {
            "detected": True,
            "confidence": 0.92,
            "frame": 30,
            "timestamp": 1.0
        },
        "forward_swing_start": {
            "detected": True,
            "confidence": 0.78,
            "frame": 50,
            "timestamp": 1.67
        },
        "contact": {
            "detected": True,
            "confidence": 0.88,
            "frame": 70,
            "timestamp": 2.33
        },
        "follow_through": {
            "detected": True,
            "confidence": 0.65,
            "frame": 90,
            "timestamp": 3.0
        }
    }

    total_frames = 100
    frame_phases = _assign_phases_to_frames(phases, total_frames)

    # Test 1: Check frame_phases is a dict
    print("\n[Test 1] Verifying frame_phases structure")
    assert isinstance(frame_phases, dict), "frame_phases should be a dict"
    print("  ✅ frame_phases is a dict")

    # Test 2: Check all frames have assignments
    print("\n[Test 2] Verifying all frames have phase assignments")
    assert len(frame_phases) == total_frames, f"Expected {total_frames} frames, got {len(frame_phases)}"
    print(f"  ✅ All {total_frames} frames have assignments")

    # Test 3: Check tuples contain (phase_name, confidence)
    print("\n[Test 3] Verifying phase data format")
    for frame_num, phase_info in frame_phases.items():
        assert isinstance(phase_info, tuple), f"Frame {frame_num} should have tuple"
        assert len(phase_info) == 2, f"Frame {frame_num} tuple should have 2 elements"
        phase_name, confidence = phase_info
        assert isinstance(phase_name, str), f"Phase name should be string"
        assert isinstance(confidence, (int, float)), f"Confidence should be numeric"
        assert 0.0 <= confidence <= 1.0, f"Confidence should be in [0, 1]"
    print("  ✅ All frames have correct (phase_name, confidence) format")

    # Test 4: Check specific phase assignments
    print("\n[Test 4] Verifying specific phase assignments")

    # Frame 5 should be Ready Position
    assert frame_phases[5][0] == "Ready Position"
    assert frame_phases[5][1] == 1.0  # Always confident
    print("  ✅ Ready Position assigned correctly")

    # Frame 15 should be BACKSWING with backswing_start confidence
    assert frame_phases[15][0] == "BACKSWING"
    assert frame_phases[15][1] == 0.85
    print("  ✅ BACKSWING assigned with correct confidence")

    # Frame 40 should be LOADING with max_backswing confidence
    assert frame_phases[40][0] == "LOADING"
    assert frame_phases[40][1] == 0.92
    print("  ✅ LOADING assigned with correct confidence")

    # Frame 60 should be FORWARD SWING with forward_swing_start confidence
    assert frame_phases[60][0] == "FORWARD SWING"
    assert frame_phases[60][1] == 0.78
    print("  ✅ FORWARD SWING assigned with correct confidence")

    # Frame 70 should be *** CONTACT *** with contact confidence
    assert frame_phases[70][0] == "*** CONTACT ***"
    assert frame_phases[70][1] == 0.88
    print("  ✅ CONTACT assigned with correct confidence")

    # Frame 80 should be FOLLOW THROUGH with contact confidence
    assert frame_phases[80][0] == "FOLLOW THROUGH"
    assert frame_phases[80][1] == 0.88  # Uses contact confidence
    print("  ✅ FOLLOW THROUGH assigned with correct confidence")

    # Frame 95 should be FINISH with follow_through confidence
    assert frame_phases[95][0] == "FINISH"
    assert frame_phases[95][1] == 0.65
    print("  ✅ FINISH assigned with correct confidence")

    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED - ALL DETECTED")
    print("="*60)


def test_assign_phases_with_failures():
    """Test phase assignment when some phases are not detected."""
    print("\n" + "="*60)
    print("TESTING PHASE ASSIGNMENT - WITH FAILURES")
    print("="*60)

    phases = {
        "backswing_start": {
            "detected": False,
            "confidence": 0.0,
            "reason": "insufficient_velocity"
        },
        "max_backswing": {
            "detected": False,
            "confidence": 0.0,
            "reason": "insufficient_velocity"
        },
        "forward_swing_start": {
            "detected": False,
            "confidence": 0.0,
            "reason": "insufficient_velocity"
        },
        "contact": {
            "detected": True,
            "confidence": 0.45,
            "frame": 50,
            "timestamp": 1.67
        },
        "follow_through": {
            "detected": False,
            "confidence": 0.0,
            "reason": "contact_not_detected"
        }
    }

    total_frames = 100
    frame_phases = _assign_phases_to_frames(phases, total_frames)

    # Test 1: When no backswing detected, all frames should be "Analyzing..."
    print("\n[Test 1] Verifying behavior when early phases not detected")
    # Since backswing_start is not detected (frame = 0), all frames become "Analyzing..."
    assert frame_phases[1][0] == "Analyzing..."
    assert frame_phases[1][1] == 0.0
    assert frame_phases[50][0] == "Analyzing..."
    assert frame_phases[50][1] == 0.0
    print("  ✅ All frames show 'Analyzing...' when backswing not detected")

    print("\n" + "="*60)
    print("✅ FAILURE HANDLING TESTS PASSED")
    print("="*60)


def test_assign_phases_partial_detection():
    """Test phase assignment when only some phases are detected."""
    print("\n" + "="*60)
    print("TESTING PHASE ASSIGNMENT - PARTIAL DETECTION")
    print("="*60)

    phases = {
        "backswing_start": {
            "detected": True,
            "confidence": 0.75,
            "frame": 10,
            "timestamp": 0.33
        },
        "max_backswing": {
            "detected": True,
            "confidence": 0.68,
            "frame": 30,
            "timestamp": 1.0
        },
        "forward_swing_start": {
            "detected": False,
            "confidence": 0.0,
            "reason": "insufficient_velocity"
        },
        "contact": {
            "detected": False,
            "confidence": 0.0,
            "reason": "arm_not_extended"
        },
        "follow_through": {
            "detected": False,
            "confidence": 0.0,
            "reason": "contact_not_detected"
        }
    }

    total_frames = 100
    frame_phases = _assign_phases_to_frames(phases, total_frames)

    print("\n[Test 1] Verifying partial detection behavior")
    # Ready position before backswing
    assert frame_phases[5][0] == "Ready Position"
    assert frame_phases[5][1] == 1.0
    print("  ✅ Ready Position assigned correctly")

    # Backswing phase
    assert frame_phases[15][0] == "BACKSWING"
    assert frame_phases[15][1] == 0.75
    print("  ✅ BACKSWING assigned with correct confidence")

    # Since forward_swing_start not detected (0), frames after max_backswing become LOADING indefinitely
    assert frame_phases[40][0] == "LOADING"
    assert frame_phases[40][1] == 0.68
    print("  ✅ LOADING extends when forward swing not detected")

    print("\n" + "="*60)
    print("✅ PARTIAL DETECTION TESTS PASSED")
    print("="*60)


def test_get_phase_color_confidence_levels():
    """Test that phase colors change based on confidence levels."""
    print("\n" + "="*60)
    print("TESTING PHASE COLOR BY CONFIDENCE")
    print("="*60)

    # Test 1: High confidence (>0.8) should be green
    print("\n[Test 1] Testing high confidence (>0.8) - Green")
    color = _get_phase_color("BACKSWING", confidence=0.9)
    assert color == (0, 255, 0), f"High confidence should be green, got {color}"
    print("  ✅ High confidence returns green (0, 255, 0)")

    # Test 2: Medium confidence (0.5-0.8) should be yellow
    print("\n[Test 2] Testing medium confidence (0.5-0.8) - Yellow")
    color = _get_phase_color("BACKSWING", confidence=0.65)
    assert color == (0, 255, 255), f"Medium confidence should be yellow, got {color}"
    print("  ✅ Medium confidence returns yellow (0, 255, 255)")

    # Test 3: Low confidence (<0.5) should be red
    print("\n[Test 3] Testing low confidence (<0.5) - Red")
    color = _get_phase_color("BACKSWING", confidence=0.3)
    assert color == (0, 0, 255), f"Low confidence should be red, got {color}"
    print("  ✅ Low confidence returns red (0, 0, 255)")

    # Test 4: Zero confidence should be gray
    print("\n[Test 4] Testing zero confidence - Gray")
    color = _get_phase_color("BACKSWING", confidence=0.0)
    assert color == (128, 128, 128), f"Zero confidence should be gray, got {color}"
    print("  ✅ Zero confidence returns gray (128, 128, 128)")

    # Test 5: "Analyzing..." should always be gray
    print("\n[Test 5] Testing 'Analyzing...' phase - Gray")
    color = _get_phase_color("Analyzing...", confidence=1.0)
    assert color == (128, 128, 128), f"'Analyzing...' should be gray, got {color}"
    print("  ✅ 'Analyzing...' returns gray (128, 128, 128)")

    # Test 6: Contact phase should be red-ish
    print("\n[Test 6] Testing CONTACT phase - Red with intensity")
    color = _get_phase_color("*** CONTACT ***", confidence=0.8)
    assert color[0] == 0, "Contact R channel should be 0"
    assert color[1] == 0, "Contact G channel should be 0"
    assert color[2] > 200, "Contact B channel should be high"
    print(f"  ✅ CONTACT returns red-ish {color}")

    print("\n" + "="*60)
    print("✅ COLOR CONFIDENCE TESTS PASSED")
    print("="*60)


def test_get_phase_color_edge_cases():
    """Test edge cases for phase color function."""
    print("\n" + "="*60)
    print("TESTING PHASE COLOR EDGE CASES")
    print("="*60)

    # Test 1: Boundary values
    print("\n[Test 1] Testing boundary confidence values")

    # Exactly 0.8 should be yellow (>= 0.5, not > 0.8)
    color = _get_phase_color("BACKSWING", confidence=0.8)
    assert color == (0, 255, 255), "Confidence 0.8 should be yellow"
    print("  ✅ Confidence 0.8 returns yellow")

    # Exactly 0.5 should be yellow (>= 0.5)
    color = _get_phase_color("BACKSWING", confidence=0.5)
    assert color == (0, 255, 255), "Confidence 0.5 should be yellow"
    print("  ✅ Confidence 0.5 returns yellow")

    # Just above 0.8 should be green
    color = _get_phase_color("BACKSWING", confidence=0.81)
    assert color == (0, 255, 0), "Confidence 0.81 should be green"
    print("  ✅ Confidence 0.81 returns green")

    # Test 2: Default confidence parameter
    print("\n[Test 2] Testing default confidence parameter")
    color = _get_phase_color("BACKSWING")  # Should default to 1.0
    assert color == (0, 255, 0), "Default confidence should be green"
    print("  ✅ Default confidence returns green")

    # Test 3: Very high confidence
    print("\n[Test 3] Testing very high confidence")
    color = _get_phase_color("BACKSWING", confidence=1.0)
    assert color == (0, 255, 0), "Confidence 1.0 should be green"
    print("  ✅ Confidence 1.0 returns green")

    print("\n" + "="*60)
    print("✅ EDGE CASE TESTS PASSED")
    print("="*60)


def test_empty_phases():
    """Test behavior with empty phases dict."""
    print("\n" + "="*60)
    print("TESTING EMPTY PHASES")
    print("="*60)

    phases = {}
    total_frames = 50
    frame_phases = _assign_phases_to_frames(phases, total_frames)

    print("\n[Test 1] Verifying all frames are 'Analyzing...'")
    for frame_num in range(1, total_frames + 1):
        assert frame_phases[frame_num][0] == "Analyzing..."
        assert frame_phases[frame_num][1] == 0.0
    print("  ✅ All frames are 'Analyzing...' with 0 confidence")

    print("\n" + "="*60)
    print("✅ EMPTY PHASES TESTS PASSED")
    print("="*60)


if __name__ == "__main__":
    """Run all tests."""
    try:
        test_assign_phases_with_all_detected()
        test_assign_phases_with_failures()
        test_assign_phases_partial_detection()
        test_get_phase_color_confidence_levels()
        test_get_phase_color_edge_cases()
        test_empty_phases()
        print("\n🎉 All visualization tests completed successfully!\n")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
