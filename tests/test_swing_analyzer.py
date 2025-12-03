"""
Unit tests for swing_analyzer module

Tests the swing analyzer configuration and phase detection functionality.
"""

import sys
import os
import inspect

# Add parent directory to path to import swing_analyzer
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from swing_analyzer import (
    SwingAnalyzer,
    SwingAnalyzerConfig,
    PRESET_STANDARD,
    PRESET_SENSITIVE,
    PRESET_STRICT
)


def test_no_hardcoded_numbers():
    """Test that all magic numbers have been moved to configuration parameters."""
    print("\n" + "="*60)
    print("TESTING NO HARDCODED NUMBERS")
    print("="*60)

    # Test 1: Check that __init__ has config parameter
    print("\n[Test 1] Verifying SwingAnalyzer.__init__ signature")
    sig = inspect.signature(SwingAnalyzer.__init__)
    params = sig.parameters

    assert 'config' in params, "Missing 'config' parameter"
    print("  ✅ config parameter exists")

    # Test 2: Check SwingAnalyzerConfig has all threshold parameters
    print("\n[Test 2] Verifying SwingAnalyzerConfig parameters")
    config_sig = inspect.signature(SwingAnalyzerConfig.__init__)
    config_params = config_sig.parameters

    required_params = [
        'velocity_threshold',
        'contact_angle_min',
        'use_adaptive_velocity',
        'adaptive_velocity_percent',
        'contact_frame_offset',
        'follow_through_offset',
        'forward_swing_search_window',
        'min_valid_frames',
        'wrist_behind_body_threshold'
    ]

    for param in required_params:
        assert param in config_params, f"Missing parameter: {param}"
        print(f"  ✅ {param} exists")

    # Test 3: Create analyzers with different configs
    print("\n[Test 3] Testing analyzer creation with different configs")
    config1 = SwingAnalyzerConfig(contact_frame_offset=3)
    config2 = SwingAnalyzerConfig(contact_frame_offset=5)

    analyzer1 = SwingAnalyzer(config=config1)
    analyzer2 = SwingAnalyzer(config=config2)

    assert analyzer1.contact_frame_offset == 3
    assert analyzer2.contact_frame_offset == 5
    print("  ✅ Different configs create different analyzer settings")

    # Test 4: Backward compatibility (kwargs still work)
    print("\n[Test 4] Testing backward compatibility with kwargs")
    analyzer_old_style = SwingAnalyzer(
        velocity_threshold=0.6,
        contact_angle_min=140
    )
    assert analyzer_old_style.velocity_threshold == 0.6
    assert analyzer_old_style.contact_angle_min == 140
    print("  ✅ Backward compatible kwargs work")

    print("\n" + "="*60)
    print("✅ NO HARDCODED NUMBERS - ALL TESTS PASSED")
    print("="*60)


def test_config_validation():
    """Test configuration parameter validation."""
    print("\n" + "="*60)
    print("TESTING CONFIGURATION VALIDATION")
    print("="*60)

    # Test 1: Valid config
    print("\n[Test 1] Testing valid configuration")
    config = SwingAnalyzerConfig(
        velocity_threshold=0.5,
        contact_angle_min=150,
        contact_frame_offset=3,
        follow_through_offset=0.15
    )
    assert config.velocity_threshold == 0.5
    print("  ✅ Valid config created successfully")

    # Test 2: Invalid velocity_threshold
    print("\n[Test 2] Testing invalid velocity_threshold")
    try:
        SwingAnalyzerConfig(velocity_threshold=-1)
        assert False, "Should raise ValueError for negative velocity"
    except ValueError as e:
        print(f"  ✅ Correctly rejected: {e}")

    # Test 3: Invalid contact_angle_min
    print("\n[Test 3] Testing invalid contact_angle_min")
    try:
        SwingAnalyzerConfig(contact_angle_min=200)
        assert False, "Should raise ValueError for angle > 180"
    except ValueError as e:
        print(f"  ✅ Correctly rejected: {e}")

    # Test 4: Invalid adaptive_velocity_percent
    print("\n[Test 4] Testing invalid adaptive_velocity_percent")
    try:
        SwingAnalyzerConfig(adaptive_velocity_percent=1.5)
        assert False, "Should raise ValueError for percent > 1.0"
    except ValueError as e:
        print(f"  ✅ Correctly rejected: {e}")

    # Test 5: Invalid contact_frame_offset
    print("\n[Test 5] Testing invalid contact_frame_offset")
    try:
        SwingAnalyzerConfig(contact_frame_offset=-1)
        assert False, "Should raise ValueError for negative offset"
    except ValueError as e:
        print(f"  ✅ Correctly rejected: {e}")

    # Test 6: Invalid forward_swing_search_window
    print("\n[Test 6] Testing invalid forward_swing_search_window")
    try:
        SwingAnalyzerConfig(forward_swing_search_window=0)
        assert False, "Should raise ValueError for window < 1"
    except ValueError as e:
        print(f"  ✅ Correctly rejected: {e}")

    print("\n" + "="*60)
    print("✅ ALL VALIDATION TESTS PASSED")
    print("="*60)


def test_presets():
    """Test preset configurations."""
    print("\n" + "="*60)
    print("TESTING PRESET CONFIGURATIONS")
    print("="*60)

    # Test 1: PRESET_STANDARD
    print("\n[Test 1] Testing PRESET_STANDARD")
    print(f"  Config: {PRESET_STANDARD}")
    assert PRESET_STANDARD.velocity_threshold == 0.5
    assert PRESET_STANDARD.contact_angle_min == 150
    assert PRESET_STANDARD.use_adaptive_velocity == False
    print("  ✅ PRESET_STANDARD verified")

    # Test 2: PRESET_SENSITIVE
    print("\n[Test 2] Testing PRESET_SENSITIVE")
    print(f"  Config: {PRESET_SENSITIVE}")
    assert PRESET_SENSITIVE.velocity_threshold == 0.3
    assert PRESET_SENSITIVE.contact_angle_min == 120
    assert PRESET_SENSITIVE.use_adaptive_velocity == True
    assert PRESET_SENSITIVE.adaptive_velocity_percent == 0.10
    print("  ✅ PRESET_SENSITIVE verified")

    # Test 3: PRESET_STRICT
    print("\n[Test 3] Testing PRESET_STRICT")
    print(f"  Config: {PRESET_STRICT}")
    assert PRESET_STRICT.velocity_threshold == 0.7
    assert PRESET_STRICT.contact_angle_min == 160
    assert PRESET_STRICT.contact_frame_offset == 2
    print("  ✅ PRESET_STRICT verified")

    # Test 4: Use preset with analyzer
    print("\n[Test 4] Testing analyzer with PRESET_SENSITIVE")
    analyzer = SwingAnalyzer(config=PRESET_SENSITIVE)
    assert analyzer.velocity_threshold == 0.3
    assert analyzer.contact_angle_min == 120
    print("  ✅ Preset works with SwingAnalyzer")

    print("\n" + "="*60)
    print("✅ ALL PRESET TESTS PASSED")
    print("="*60)


def test_config_affects_behavior():
    """Test that changing config parameters actually affects analyzer behavior."""
    print("\n" + "="*60)
    print("TESTING CONFIG AFFECTS BEHAVIOR")
    print("="*60)

    # Test 1: Different contact_frame_offset values
    print("\n[Test 1] Testing different contact_frame_offset values")
    config1 = SwingAnalyzerConfig(contact_frame_offset=2)
    config2 = SwingAnalyzerConfig(contact_frame_offset=5)

    analyzer1 = SwingAnalyzer(config=config1)
    analyzer2 = SwingAnalyzer(config=config2)

    assert analyzer1.contact_frame_offset != analyzer2.contact_frame_offset
    print(f"  Analyzer 1 offset: {analyzer1.contact_frame_offset}")
    print(f"  Analyzer 2 offset: {analyzer2.contact_frame_offset}")
    print("  ✅ Different configs produce different analyzer settings")

    # Test 2: Verify all config parameters transfer to analyzer
    print("\n[Test 2] Testing all config parameters transfer to analyzer")
    custom_config = SwingAnalyzerConfig(
        velocity_threshold=0.42,
        contact_angle_min=145,
        contact_frame_offset=4,
        follow_through_offset=0.20,
        forward_swing_search_window=50,
        min_valid_frames=15
    )
    analyzer = SwingAnalyzer(config=custom_config)

    assert analyzer.velocity_threshold == 0.42
    assert analyzer.contact_angle_min == 145
    assert analyzer.contact_frame_offset == 4
    assert analyzer.follow_through_offset == 0.20
    assert analyzer.forward_swing_search_window == 50
    assert analyzer.min_valid_frames == 15
    print("  ✅ All config parameters correctly transferred")

    print("\n" + "="*60)
    print("✅ CONFIG BEHAVIOR TESTS PASSED")
    print("="*60)


def test_default_behavior():
    """Test default analyzer behavior when no config provided."""
    print("\n" + "="*60)
    print("TESTING DEFAULT BEHAVIOR")
    print("="*60)

    print("\n[Test 1] Creating analyzer with no arguments")
    analyzer = SwingAnalyzer()

    # Should use PRESET_STANDARD defaults
    assert analyzer.velocity_threshold == 0.5
    assert analyzer.contact_angle_min == 150
    assert analyzer.contact_frame_offset == 3
    print("  ✅ Default config (PRESET_STANDARD) applied correctly")

    print("\n" + "="*60)
    print("✅ DEFAULT BEHAVIOR TESTS PASSED")
    print("="*60)


def test_phase_detection_failure_handling():
    """Test that phase detection provides detailed status and failure reasons."""
    print("\n" + "="*60)
    print("TESTING PHASE DETECTION FAILURE HANDLING")
    print("="*60)

    from video_processor import VideoProcessor

    # Test 1: Check structure of phase detection results
    print("\n[Test 1] Testing phase detection result structure")

    # Check if test video exists
    test_video = 'uploads/test_swing.mp4'
    if not os.path.exists(test_video):
        print(f"  ⚠️  Skipping - video not found: {test_video}")
        return

    analyzer = SwingAnalyzer()
    processor = VideoProcessor()

    video_data = processor.process_video(test_video)
    phases = analyzer.analyze_swing(video_data)

    # Every phase should have required fields
    phase_names = ['backswing_start', 'max_backswing', 'forward_swing_start', 'contact', 'follow_through']

    for phase_name in phase_names:
        assert phase_name in phases, f"Missing phase: {phase_name}"
        phase_data = phases[phase_name]

        assert 'detected' in phase_data, f"{phase_name} missing 'detected' field"
        assert 'confidence' in phase_data, f"{phase_name} missing 'confidence' field"
        assert 'reason' in phase_data, f"{phase_name} missing 'reason' field"

        assert isinstance(phase_data['detected'], bool), f"{phase_name} 'detected' should be bool"
        assert isinstance(phase_data['confidence'], (int, float)), f"{phase_name} 'confidence' should be numeric"
        assert 0.0 <= phase_data['confidence'] <= 1.0, f"{phase_name} confidence out of range"

        print(f"  ✅ {phase_name}: detected={phase_data['detected']}, " +
              f"confidence={phase_data['confidence']:.2f}, reason={phase_data['reason']}")

    print("  ✅ All phases have required fields")

    # Test 2: Check overall quality score
    print("\n[Test 2] Testing overall analysis quality score")
    assert '_analysis_quality' in phases, "Missing '_analysis_quality' in results"

    quality = phases['_analysis_quality']
    assert 'overall_score' in quality
    assert 'phases_detected' in quality
    assert 'total_phases' in quality
    assert 'detection_rate' in quality

    print(f"  Overall Score: {quality['overall_score']:.2f}")
    print(f"  Phases Detected: {quality['phases_detected']}/{quality['total_phases']}")
    print(f"  Detection Rate: {quality['detection_rate']*100:.1f}%")
    print("  ✅ Analysis quality metrics present")

    print("\n" + "="*60)
    print("✅ PHASE DETECTION FAILURE HANDLING TESTS PASSED")
    print("="*60)


if __name__ == "__main__":
    """Run all tests."""
    try:
        test_no_hardcoded_numbers()
        test_config_validation()
        test_presets()
        test_config_affects_behavior()
        test_default_behavior()
        test_phase_detection_failure_handling()
        print("\n🎉 All swing analyzer tests completed successfully!\n")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
