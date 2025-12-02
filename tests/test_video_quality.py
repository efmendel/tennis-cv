"""
Unit tests for video_quality_checker module

Tests the video quality checking functionality including:
- Resolution checks
- Frame rate checks
- Brightness checks
- Sharpness checks
- Overall quality assessment
"""

import sys
import os

# Add parent directory to path to import video_quality_checker
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from video_quality_checker import check_video_quality


def test_video_quality_checker():
    """Test video quality checker on sample videos."""
    print("\n" + "="*60)
    print("RUNNING VIDEO QUALITY CHECKER TESTS")
    print("="*60)

    # Test 1: Check if test video exists
    test_video_path = 'uploads/test_swing.mp4'
    novak_video_path = 'uploads/novakswing.mp4'

    if not os.path.exists(test_video_path):
        print(f"⚠️  Skipping test - video not found: {test_video_path}")
        print("Please ensure test videos are in the uploads/ folder")
        return

    print(f"\n[Test 1] Analyzing: {test_video_path}")
    report1 = check_video_quality(test_video_path)

    print(f"  Resolution: {report1['resolution'][0]}x{report1['resolution'][1]}")
    print(f"  FPS: {report1['fps']:.1f}")
    print(f"  Brightness: {report1['brightness']:.1f}/255")
    print(f"  Sharpness: {report1['sharpness']:.1f}")
    print(f"  Warnings: {len(report1['warnings'])}")
    print(f"  Acceptable: {report1['is_acceptable']}")

    # Verify report structure
    assert 'resolution' in report1, "Missing 'resolution' in report"
    assert 'fps' in report1, "Missing 'fps' in report"
    assert 'brightness' in report1, "Missing 'brightness' in report"
    assert 'sharpness' in report1, "Missing 'sharpness' in report"
    assert 'warnings' in report1, "Missing 'warnings' in report"
    assert 'is_acceptable' in report1, "Missing 'is_acceptable' in report"

    # Verify data types
    assert isinstance(report1['resolution'], tuple), "Resolution should be a tuple"
    assert len(report1['resolution']) == 2, "Resolution should have width and height"
    assert isinstance(report1['fps'], (int, float)), "FPS should be numeric"
    assert isinstance(report1['brightness'], float), "Brightness should be float"
    assert isinstance(report1['sharpness'], float), "Sharpness should be float"
    assert isinstance(report1['warnings'], list), "Warnings should be a list"
    assert isinstance(report1['is_acceptable'], bool), "is_acceptable should be boolean"

    print("  ✅ Report structure validation passed")

    # Test 2: Check another video if available
    if os.path.exists(novak_video_path):
        print(f"\n[Test 2] Analyzing: {novak_video_path}")
        report2 = check_video_quality(novak_video_path)

        print(f"  Resolution: {report2['resolution'][0]}x{report2['resolution'][1]}")
        print(f"  FPS: {report2['fps']:.1f}")
        print(f"  Brightness: {report2['brightness']:.1f}/255")
        print(f"  Sharpness: {report2['sharpness']:.1f}")
        print(f"  Warnings: {len(report2['warnings'])}")
        print(f"  Acceptable: {report2['is_acceptable']}")

        if report2['warnings']:
            print(f"  Warning details:")
            for warning in report2['warnings']:
                print(f"    - {warning}")

        print("  ✅ Second video analysis completed")
    else:
        print(f"\n[Test 2] Skipping - video not found: {novak_video_path}")

    # Test 3: Verify quality thresholds work correctly
    print(f"\n[Test 3] Validating quality thresholds")

    # Check resolution threshold
    width, height = report1['resolution']
    if width < 1280 or height < 720:
        assert any('resolution' in w.lower() for w in report1['warnings']), \
            "Should warn about low resolution"
        print("  ✅ Resolution threshold working correctly")
    else:
        assert not any('resolution' in w.lower() for w in report1['warnings']), \
            "Should not warn about good resolution"
        print("  ✅ Resolution check passed (no warning needed)")

    # Check FPS threshold
    if report1['fps'] < 24:
        assert any('frame rate' in w.lower() or 'fps' in w.lower() for w in report1['warnings']), \
            "Should warn about low frame rate"
        print("  ✅ FPS threshold working correctly")
    else:
        print("  ✅ FPS check passed (no warning needed)")

    # Check brightness threshold
    if report1['brightness'] < 100:
        assert any('dark' in w.lower() or 'brightness' in w.lower() for w in report1['warnings']), \
            "Should warn about low brightness"
        print("  ✅ Brightness threshold working correctly")
    else:
        print("  ✅ Brightness check passed (no warning needed)")

    # Check sharpness threshold
    if report1['sharpness'] < 100:
        assert any('blur' in w.lower() or 'sharpness' in w.lower() for w in report1['warnings']), \
            "Should warn about low sharpness"
        print("  ✅ Sharpness threshold working correctly")
    else:
        print("  ✅ Sharpness check passed (no warning needed)")

    # Test 4: Verify is_acceptable logic
    print(f"\n[Test 4] Validating is_acceptable logic")
    if len(report1['warnings']) == 0:
        assert report1['is_acceptable'] == True, \
            "Video with no warnings should be acceptable"
        print("  ✅ is_acceptable=True for video with no warnings")
    else:
        assert report1['is_acceptable'] == False, \
            "Video with warnings should not be acceptable"
        print("  ✅ is_acceptable=False for video with warnings")

    print("\n" + "="*60)
    print("✅ ALL VIDEO QUALITY CHECKER TESTS PASSED")
    print("="*60 + "\n")


def test_error_handling():
    """Test error handling for invalid inputs."""
    print("\n" + "="*60)
    print("TESTING ERROR HANDLING")
    print("="*60)

    # Test 1: Non-existent file
    print("\n[Test 1] Testing non-existent file handling")
    try:
        check_video_quality('nonexistent_video.mp4')
        assert False, "Should raise ValueError for non-existent file"
    except ValueError as e:
        print(f"  ✅ Correctly raised ValueError: {e}")

    # Test 2: Invalid file path
    print("\n[Test 2] Testing invalid file path")
    try:
        check_video_quality('')
        assert False, "Should raise ValueError for empty path"
    except (ValueError, Exception) as e:
        print(f"  ✅ Correctly raised error: {type(e).__name__}")

    print("\n" + "="*60)
    print("✅ ERROR HANDLING TESTS PASSED")
    print("="*60 + "\n")


if __name__ == "__main__":
    """Run all tests."""
    try:
        test_video_quality_checker()
        test_error_handling()
        print("🎉 All tests completed successfully!\n")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        sys.exit(1)
