"""
Unit tests for kinematic_chain_utils module

Tests all kinematic chain calculation functions with various scenarios.
"""

import sys
import os
import math

# Add parent directory to path to import kinematic_chain_utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from kinematic_chain_utils import (
    calculate_hip_rotation,
    calculate_shoulder_rotation,
    calculate_knee_bend,
    calculate_trunk_lean,
    calculate_upper_arm_angle,
    create_sample_landmarks
)


def test_hip_rotation():
    """Test hip rotation calculations."""
    print("\n" + "="*60)
    print("TESTING HIP ROTATION")
    print("="*60)

    # Test 1: Neutral position (hips parallel to camera)
    print("\n[Test 1] Testing neutral hip position")
    landmarks = {
        'left_hip': {'x': 0.4, 'y': 0.5, 'z': 0.0},
        'right_hip': {'x': 0.6, 'y': 0.5, 'z': 0.0}
    }
    angle = calculate_hip_rotation(landmarks)
    assert abs(angle) < 5, f"Expected ~0°, got {angle:.2f}°"
    print(f"  Hip rotation: {angle:.2f}° ✅ (neutral position)")

    # Test 2: Right hip forward (positive rotation)
    print("\n[Test 2] Testing right hip forward")
    landmarks = {
        'left_hip': {'x': 0.4, 'y': 0.5, 'z': 0.1},
        'right_hip': {'x': 0.6, 'y': 0.5, 'z': -0.1}
    }
    angle = calculate_hip_rotation(landmarks)
    assert angle < 0, f"Expected negative angle (right hip forward), got {angle:.2f}°"
    print(f"  Hip rotation: {angle:.2f}° ✅ (right hip forward)")

    # Test 3: Left hip forward (negative rotation)
    print("\n[Test 3] Testing left hip forward")
    landmarks = {
        'left_hip': {'x': 0.4, 'y': 0.5, 'z': -0.1},
        'right_hip': {'x': 0.6, 'y': 0.5, 'z': 0.1}
    }
    angle = calculate_hip_rotation(landmarks)
    assert angle > 0, f"Expected positive angle (left hip forward), got {angle:.2f}°"
    print(f"  Hip rotation: {angle:.2f}° ✅ (left hip forward)")

    # Test 4: Missing landmarks
    print("\n[Test 4] Testing missing landmarks")
    landmarks = {'left_hip': {'x': 0.4, 'y': 0.5, 'z': 0}}
    angle = calculate_hip_rotation(landmarks)
    assert angle == 0.0, f"Expected 0° for missing landmark, got {angle:.2f}°"
    print(f"  Hip rotation: {angle:.2f}° ✅ (handles missing data)")

    # Test 5: Valid range
    print("\n[Test 5] Testing angle range")
    assert -180 <= angle <= 180, "Angle should be in range [-180, 180]"
    print(f"  ✅ Angle in valid range")

    print("\n" + "="*60)
    print("✅ HIP ROTATION TESTS PASSED")
    print("="*60)


def test_shoulder_rotation():
    """Test shoulder rotation calculations."""
    print("\n" + "="*60)
    print("TESTING SHOULDER ROTATION")
    print("="*60)

    # Test 1: Neutral position
    print("\n[Test 1] Testing neutral shoulder position")
    landmarks = {
        'left_shoulder': {'x': 0.4, 'y': 0.3, 'z': 0.0},
        'right_shoulder': {'x': 0.6, 'y': 0.3, 'z': 0.0}
    }
    angle = calculate_shoulder_rotation(landmarks)
    assert abs(angle) < 5, f"Expected ~0°, got {angle:.2f}°"
    print(f"  Shoulder rotation: {angle:.2f}° ✅ (neutral)")

    # Test 2: Right shoulder forward
    print("\n[Test 2] Testing right shoulder forward")
    landmarks = {
        'left_shoulder': {'x': 0.4, 'y': 0.3, 'z': 0.15},
        'right_shoulder': {'x': 0.6, 'y': 0.3, 'z': -0.15}
    }
    angle = calculate_shoulder_rotation(landmarks)
    assert angle < 0, f"Expected negative (right forward), got {angle:.2f}°"
    print(f"  Shoulder rotation: {angle:.2f}° ✅ (right forward)")

    # Test 3: Left shoulder forward
    print("\n[Test 3] Testing left shoulder forward")
    landmarks = {
        'left_shoulder': {'x': 0.4, 'y': 0.3, 'z': -0.15},
        'right_shoulder': {'x': 0.6, 'y': 0.3, 'z': 0.15}
    }
    angle = calculate_shoulder_rotation(landmarks)
    assert angle > 0, f"Expected positive (left forward), got {angle:.2f}°"
    print(f"  Shoulder rotation: {angle:.2f}° ✅ (left forward)")

    # Test 4: Missing landmarks
    print("\n[Test 4] Testing missing landmarks")
    landmarks = {}
    angle = calculate_shoulder_rotation(landmarks)
    assert angle == 0.0, f"Expected 0° for missing landmarks, got {angle:.2f}°"
    print(f"  ✅ Handles missing data")

    print("\n" + "="*60)
    print("✅ SHOULDER ROTATION TESTS PASSED")
    print("="*60)


def test_knee_bend():
    """Test knee bend calculations."""
    print("\n" + "="*60)
    print("TESTING KNEE BEND")
    print("="*60)

    # Test 1: Straight leg
    print("\n[Test 1] Testing straight leg")
    landmarks = {
        'right_hip': {'x': 0.6, 'y': 0.5, 'z': 0},
        'right_knee': {'x': 0.6, 'y': 0.7, 'z': 0},
        'right_ankle': {'x': 0.6, 'y': 0.9, 'z': 0}
    }
    angle = calculate_knee_bend(landmarks, side='right')
    assert 170 < angle <= 180, f"Expected ~180° (straight), got {angle:.2f}°"
    print(f"  Knee angle: {angle:.2f}° ✅ (straight leg)")

    # Test 2: 90-degree bend
    print("\n[Test 2] Testing 90-degree knee bend")
    landmarks = {
        'right_hip': {'x': 0.6, 'y': 0.5, 'z': 0},
        'right_knee': {'x': 0.6, 'y': 0.7, 'z': 0},
        'right_ankle': {'x': 0.7, 'y': 0.7, 'z': 0}  # Ankle at same height as knee
    }
    angle = calculate_knee_bend(landmarks, side='right')
    assert 85 < angle < 95, f"Expected ~90°, got {angle:.2f}°"
    print(f"  Knee angle: {angle:.2f}° ✅ (90-degree bend)")

    # Test 3: Left leg
    print("\n[Test 3] Testing left leg")
    landmarks = {
        'left_hip': {'x': 0.4, 'y': 0.5, 'z': 0},
        'left_knee': {'x': 0.4, 'y': 0.7, 'z': 0},
        'left_ankle': {'x': 0.4, 'y': 0.9, 'z': 0}
    }
    angle = calculate_knee_bend(landmarks, side='left')
    assert 170 < angle <= 180, f"Expected ~180° (straight), got {angle:.2f}°"
    print(f"  Left knee angle: {angle:.2f}° ✅")

    # Test 4: Missing landmarks
    print("\n[Test 4] Testing missing landmarks")
    landmarks = {'right_hip': {'x': 0.6, 'y': 0.5, 'z': 0}}
    angle = calculate_knee_bend(landmarks, side='right')
    assert angle == 180.0, f"Expected 180° default, got {angle:.2f}°"
    print(f"  ✅ Handles missing data (defaults to straight)")

    # Test 5: Valid range
    print("\n[Test 5] Testing angle range")
    assert 0 <= angle <= 180, "Knee angle should be in range [0, 180]"
    print(f"  ✅ Angle in valid range")

    print("\n" + "="*60)
    print("✅ KNEE BEND TESTS PASSED")
    print("="*60)


def test_trunk_lean():
    """Test trunk lean calculations."""
    print("\n" + "="*60)
    print("TESTING TRUNK LEAN")
    print("="*60)

    # Test 1: Upright posture
    print("\n[Test 1] Testing upright posture")
    landmarks = {
        'left_hip': {'x': 0.4, 'y': 0.5, 'z': 0.0},
        'right_hip': {'x': 0.6, 'y': 0.5, 'z': 0.0},
        'left_shoulder': {'x': 0.4, 'y': 0.3, 'z': 0.0},
        'right_shoulder': {'x': 0.6, 'y': 0.3, 'z': 0.0}
    }
    angle = calculate_trunk_lean(landmarks)
    assert abs(angle) < 10, f"Expected ~0° (upright), got {angle:.2f}°"
    print(f"  Trunk lean: {angle:.2f}° ✅ (upright)")

    # Test 2: Forward lean
    print("\n[Test 2] Testing forward lean")
    landmarks = {
        'left_hip': {'x': 0.4, 'y': 0.5, 'z': 0.0},
        'right_hip': {'x': 0.6, 'y': 0.5, 'z': 0.0},
        'left_shoulder': {'x': 0.4, 'y': 0.3, 'z': -0.1},  # Shoulders forward
        'right_shoulder': {'x': 0.6, 'y': 0.3, 'z': -0.1}
    }
    angle = calculate_trunk_lean(landmarks)
    assert angle < 0, f"Expected negative (forward lean), got {angle:.2f}°"
    print(f"  Trunk lean: {angle:.2f}° ✅ (forward)")

    # Test 3: Backward lean
    print("\n[Test 3] Testing backward lean")
    landmarks = {
        'left_hip': {'x': 0.4, 'y': 0.5, 'z': 0.0},
        'right_hip': {'x': 0.6, 'y': 0.5, 'z': 0.0},
        'left_shoulder': {'x': 0.4, 'y': 0.3, 'z': 0.1},  # Shoulders back
        'right_shoulder': {'x': 0.6, 'y': 0.3, 'z': 0.1}
    }
    angle = calculate_trunk_lean(landmarks)
    assert angle > 0, f"Expected positive (backward lean), got {angle:.2f}°"
    print(f"  Trunk lean: {angle:.2f}° ✅ (backward)")

    # Test 4: Missing landmarks
    print("\n[Test 4] Testing missing landmarks")
    landmarks = {'left_hip': {'x': 0.4, 'y': 0.5, 'z': 0}}
    angle = calculate_trunk_lean(landmarks)
    assert angle == 0.0, f"Expected 0° for missing data, got {angle:.2f}°"
    print(f"  ✅ Handles missing data")

    print("\n" + "="*60)
    print("✅ TRUNK LEAN TESTS PASSED")
    print("="*60)


def test_upper_arm_angle():
    """Test upper arm angle calculations."""
    print("\n" + "="*60)
    print("TESTING UPPER ARM ANGLE")
    print("="*60)

    # Test 1: Arm hanging down
    print("\n[Test 1] Testing arm hanging down")
    landmarks = {
        'right_shoulder': {'x': 0.6, 'y': 0.3, 'z': 0},
        'right_elbow': {'x': 0.6, 'y': 0.5, 'z': 0},
        'right_hip': {'x': 0.6, 'y': 0.6, 'z': 0}
    }
    angle = calculate_upper_arm_angle(landmarks, side='right')
    assert angle < 20, f"Expected ~0° (arm down), got {angle:.2f}°"
    print(f"  Upper arm angle: {angle:.2f}° ✅ (arm down)")

    # Test 2: Arm horizontal
    print("\n[Test 2] Testing arm horizontal")
    landmarks = {
        'right_shoulder': {'x': 0.6, 'y': 0.3, 'z': 0},
        'right_elbow': {'x': 0.8, 'y': 0.3, 'z': 0},  # Same height
        'right_hip': {'x': 0.6, 'y': 0.6, 'z': 0}
    }
    angle = calculate_upper_arm_angle(landmarks, side='right')
    assert 80 < angle < 100, f"Expected ~90° (horizontal), got {angle:.2f}°"
    print(f"  Upper arm angle: {angle:.2f}° ✅ (horizontal)")

    # Test 3: Arm raised up
    print("\n[Test 3] Testing arm raised up")
    landmarks = {
        'right_shoulder': {'x': 0.6, 'y': 0.3, 'z': 0},
        'right_elbow': {'x': 0.6, 'y': 0.1, 'z': 0},  # Above shoulder
        'right_hip': {'x': 0.6, 'y': 0.6, 'z': 0}
    }
    angle = calculate_upper_arm_angle(landmarks, side='right')
    assert angle > 160, f"Expected ~180° (arm up), got {angle:.2f}°"
    print(f"  Upper arm angle: {angle:.2f}° ✅ (arm up)")

    # Test 4: Left arm
    print("\n[Test 4] Testing left arm")
    landmarks = {
        'left_shoulder': {'x': 0.4, 'y': 0.3, 'z': 0},
        'left_elbow': {'x': 0.4, 'y': 0.5, 'z': 0},
        'left_hip': {'x': 0.4, 'y': 0.6, 'z': 0}
    }
    angle = calculate_upper_arm_angle(landmarks, side='left')
    assert angle < 20, f"Expected ~0° (arm down), got {angle:.2f}°"
    print(f"  Left arm angle: {angle:.2f}° ✅")

    # Test 5: Missing landmarks
    print("\n[Test 5] Testing missing landmarks")
    landmarks = {}
    angle = calculate_upper_arm_angle(landmarks, side='right')
    assert angle == 0.0, f"Expected 0° for missing data, got {angle:.2f}°"
    print(f"  ✅ Handles missing data")

    # Test 6: Valid range
    print("\n[Test 6] Testing angle range")
    assert 0 <= angle <= 180, "Upper arm angle should be in range [0, 180]"
    print(f"  ✅ Angle in valid range")

    print("\n" + "="*60)
    print("✅ UPPER ARM ANGLE TESTS PASSED")
    print("="*60)


def test_sample_landmarks():
    """Test the sample landmarks helper function."""
    print("\n" + "="*60)
    print("TESTING SAMPLE LANDMARKS HELPER")
    print("="*60)

    landmarks = create_sample_landmarks()

    # Check that all required landmarks are present
    required_landmarks = [
        'left_hip', 'right_hip',
        'left_shoulder', 'right_shoulder',
        'left_elbow', 'right_elbow',
        'left_wrist', 'right_wrist',
        'left_knee', 'right_knee',
        'left_ankle', 'right_ankle'
    ]

    for landmark_name in required_landmarks:
        assert landmark_name in landmarks, f"Missing {landmark_name}"
        landmark = landmarks[landmark_name]
        assert 'x' in landmark and 'y' in landmark and 'z' in landmark
        assert 'visibility' in landmark

    print(f"  ✅ All {len(required_landmarks)} landmarks present")
    print(f"  ✅ All landmarks have x, y, z, visibility")

    # Test that these landmarks work with all functions
    print("\n  Testing sample landmarks with all functions:")
    hip_rot = calculate_hip_rotation(landmarks)
    shoulder_rot = calculate_shoulder_rotation(landmarks)
    knee = calculate_knee_bend(landmarks)
    trunk = calculate_trunk_lean(landmarks)
    arm = calculate_upper_arm_angle(landmarks)

    print(f"    Hip rotation: {hip_rot:.2f}°")
    print(f"    Shoulder rotation: {shoulder_rot:.2f}°")
    print(f"    Knee bend: {knee:.2f}°")
    print(f"    Trunk lean: {trunk:.2f}°")
    print(f"    Upper arm: {arm:.2f}°")
    print("  ✅ All functions work with sample landmarks")

    print("\n" + "="*60)
    print("✅ SAMPLE LANDMARKS TESTS PASSED")
    print("="*60)


def test_edge_cases():
    """Test edge cases and error handling."""
    print("\n" + "="*60)
    print("TESTING EDGE CASES")
    print("="*60)

    # Test with empty dict
    print("\n[Test 1] Testing with empty dictionary")
    empty = {}
    assert calculate_hip_rotation(empty) == 0.0
    assert calculate_shoulder_rotation(empty) == 0.0
    assert calculate_knee_bend(empty) == 180.0
    assert calculate_trunk_lean(empty) == 0.0
    assert calculate_upper_arm_angle(empty) == 0.0
    print("  ✅ All functions handle empty dict")

    # Test with None values
    print("\n[Test 2] Testing with None values")
    none_landmarks = {'left_hip': None, 'right_hip': None}
    assert calculate_hip_rotation(none_landmarks) == 0.0
    print("  ✅ Handles None values")

    # Test with malformed data
    print("\n[Test 3] Testing with malformed data")
    bad_landmarks = {'left_hip': {'x': 'invalid'}}
    assert calculate_hip_rotation(bad_landmarks) == 0.0
    print("  ✅ Handles malformed data")

    # Test with extreme values
    print("\n[Test 4] Testing with extreme z-values")
    extreme = {
        'left_hip': {'x': 0.4, 'y': 0.5, 'z': 10.0},
        'right_hip': {'x': 0.6, 'y': 0.5, 'z': -10.0}
    }
    angle = calculate_hip_rotation(extreme)
    assert isinstance(angle, float)
    assert -180 <= angle <= 180
    print(f"  Hip rotation with extreme z: {angle:.2f}° ✅")

    print("\n" + "="*60)
    print("✅ EDGE CASE TESTS PASSED")
    print("="*60)


if __name__ == "__main__":
    """Run all tests."""
    try:
        test_hip_rotation()
        test_shoulder_rotation()
        test_knee_bend()
        test_trunk_lean()
        test_upper_arm_angle()
        test_sample_landmarks()
        test_edge_cases()
        print("\n🎉 All kinematic chain tests completed successfully!\n")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
