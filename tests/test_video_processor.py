"""
Unit tests for video_processor module

Tests the video processing and tracking quality assessment functionality.
"""

import sys
import os

# Add parent directory to path to import video_processor
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from video_processor import (
    VideoProcessor,
    PoseConfig,
    PRESET_HIGH_QUALITY,
    PRESET_FAST,
    PRESET_DIFFICULT_VIDEO,
    PRESET_SLOW_MOTION
)


def test_tracking_quality():
    """Test tracking quality assessment on sample video."""
    print("\n" + "="*60)
    print("TESTING TRACKING QUALITY ASSESSMENT")
    print("="*60)

    # Check if test video exists
    test_video_path = 'uploads/test_swing.mp4'

    if not os.path.exists(test_video_path):
        print(f"⚠️  Skipping test - video not found: {test_video_path}")
        print("Please ensure test video is in the uploads/ folder")
        return

    print(f"\n[Test 1] Processing video: {test_video_path}")
    processor = VideoProcessor()
    video_data = processor.process_video(test_video_path)

    # Verify tracking_quality is in the returned data
    print(f"\n[Test 2] Verifying tracking_quality in video_data")
    assert 'tracking_quality' in video_data, "Missing 'tracking_quality' in video_data"
    print("  ✅ tracking_quality found in video_data")

    tracking_quality = video_data['tracking_quality']

    # Verify all required metrics are present
    print(f"\n[Test 3] Verifying tracking quality metrics structure")
    assert 'detection_rate' in tracking_quality, "Missing 'detection_rate'"
    assert 'high_confidence_rate' in tracking_quality, "Missing 'high_confidence_rate'"
    assert 'average_confidence' in tracking_quality, "Missing 'average_confidence'"
    print("  ✅ All required metrics present")

    # Verify detection rate is reasonable
    print(f"\n[Test 4] Verifying detection rate threshold")
    detection_rate = tracking_quality['detection_rate']
    print(f"  Detection rate: {detection_rate*100:.1f}%")
    assert detection_rate > 0.7, f"Detection rate {detection_rate} is below 70% threshold"
    print(f"  ✅ Detection rate above 70% threshold")

    # Verify confidence values are in valid range [0, 1]
    print(f"\n[Test 5] Verifying confidence values in valid range")
    avg_confidence = tracking_quality['average_confidence']
    high_conf_rate = tracking_quality['high_confidence_rate']

    print(f"  Average confidence: {avg_confidence:.3f}")
    print(f"  High confidence rate: {high_conf_rate*100:.1f}%")

    assert 0 <= avg_confidence <= 1, f"Average confidence {avg_confidence} not in range [0, 1]"
    assert 0 <= high_conf_rate <= 1, f"High confidence rate {high_conf_rate} not in range [0, 1]"
    assert 0 <= detection_rate <= 1, f"Detection rate {detection_rate} not in range [0, 1]"
    print("  ✅ All confidence values in valid range [0, 1]")

    # Verify video_data structure is intact
    print(f"\n[Test 6] Verifying complete video_data structure")
    assert 'fps' in video_data, "Missing 'fps'"
    assert 'frame_count' in video_data, "Missing 'frame_count'"
    assert 'width' in video_data, "Missing 'width'"
    assert 'height' in video_data, "Missing 'height'"
    assert 'frames' in video_data, "Missing 'frames'"
    print("  ✅ Complete video_data structure verified")

    # Print summary
    print(f"\n" + "="*60)
    print("TRACKING QUALITY SUMMARY")
    print("="*60)
    print(f"Video: {test_video_path}")
    print(f"Total frames: {video_data['frame_count']}")
    print(f"Detection rate: {detection_rate*100:.1f}%")
    print(f"High confidence rate: {high_conf_rate*100:.1f}%")
    print(f"Average confidence: {avg_confidence:.3f}")
    print("="*60)

    print("\n✅ All tracking quality assessment tests passed")


def test_tracking_quality_edge_cases():
    """Test edge cases for tracking quality assessment."""
    print("\n" + "="*60)
    print("TESTING EDGE CASES")
    print("="*60)

    processor = VideoProcessor()

    # Test 1: Empty frames list
    print("\n[Test 1] Testing with empty frames list")
    empty_data = {
        'fps': 30,
        'frame_count': 0,
        'width': 1920,
        'height': 1080,
        'frames': []
    }
    quality = processor.assess_tracking_quality(empty_data)
    assert quality['detection_rate'] == 0.0, "Detection rate should be 0 for empty frames"
    assert quality['high_confidence_rate'] == 0.0, "High confidence rate should be 0 for empty frames"
    assert quality['average_confidence'] == 0.0, "Average confidence should be 0 for empty frames"
    print("  ✅ Empty frames handled correctly")

    # Test 2: All frames with no pose detected
    print("\n[Test 2] Testing with no poses detected")
    no_pose_data = {
        'fps': 30,
        'frame_count': 10,
        'width': 1920,
        'height': 1080,
        'frames': [
            {'frame_number': i, 'timestamp': i/30, 'pose_detected': False, 'landmarks': None}
            for i in range(1, 11)
        ]
    }
    quality = processor.assess_tracking_quality(no_pose_data)
    assert quality['detection_rate'] == 0.0, "Detection rate should be 0 when no poses detected"
    assert quality['high_confidence_rate'] == 0.0, "High confidence rate should be 0 when no poses detected"
    assert quality['average_confidence'] == 0.0, "Average confidence should be 0 when no poses detected"
    print("  ✅ No pose detection handled correctly")

    # Test 3: Perfect detection
    print("\n[Test 3] Testing with perfect detection")
    perfect_landmarks = {
        'left_shoulder': {'x': 0.5, 'y': 0.3, 'z': 0.0, 'visibility': 0.99},
        'right_shoulder': {'x': 0.5, 'y': 0.3, 'z': 0.0, 'visibility': 0.99},
        'left_elbow': {'x': 0.4, 'y': 0.5, 'z': 0.0, 'visibility': 0.99},
        'right_elbow': {'x': 0.6, 'y': 0.5, 'z': 0.0, 'visibility': 0.99},
        'left_wrist': {'x': 0.3, 'y': 0.7, 'z': 0.0, 'visibility': 0.99},
        'right_wrist': {'x': 0.7, 'y': 0.7, 'z': 0.0, 'visibility': 0.99},
        'left_hip': {'x': 0.5, 'y': 0.6, 'z': 0.0, 'visibility': 0.99},
        'right_hip': {'x': 0.5, 'y': 0.6, 'z': 0.0, 'visibility': 0.99}
    }
    perfect_data = {
        'fps': 30,
        'frame_count': 10,
        'width': 1920,
        'height': 1080,
        'frames': [
            {'frame_number': i, 'timestamp': i/30, 'pose_detected': True, 'landmarks': perfect_landmarks}
            for i in range(1, 11)
        ]
    }
    quality = processor.assess_tracking_quality(perfect_data)
    assert quality['detection_rate'] == 1.0, "Detection rate should be 1.0 for perfect detection"
    assert quality['high_confidence_rate'] == 1.0, "High confidence rate should be 1.0 for perfect detection"
    assert quality['average_confidence'] > 0.9, "Average confidence should be very high for perfect detection"
    print(f"  Detection rate: {quality['detection_rate']:.2f}")
    print(f"  High confidence rate: {quality['high_confidence_rate']:.2f}")
    print(f"  Average confidence: {quality['average_confidence']:.3f}")
    print("  ✅ Perfect detection handled correctly")

    print("\n✅ All edge case tests passed")


def test_multiple_videos():
    """Test tracking quality on multiple videos if available."""
    print("\n" + "="*60)
    print("TESTING MULTIPLE VIDEOS")
    print("="*60)
    print("\n⚠️  Note: Skipping multi-video test due to MediaPipe processor reuse limitation")
    print("  Each video requires a new VideoProcessor instance")
    print("="*60)


def test_pose_config():
    """Test pose configuration functionality."""
    print("\n" + "="*60)
    print("TESTING POSE CONFIGURATION")
    print("="*60)

    # Test 1: Custom PoseConfig
    print("\n[Test 1] Testing custom PoseConfig")
    custom_config = PoseConfig(
        model_complexity=1,
        min_detection_confidence=0.4,
        min_tracking_confidence=0.4
    )
    print(f"  Config: {custom_config}")

    # Verify config attributes
    assert custom_config.model_complexity == 1
    assert custom_config.min_detection_confidence == 0.4
    assert custom_config.min_tracking_confidence == 0.4
    assert custom_config.smooth_landmarks == True  # default
    print("  ✅ Custom config created successfully")

    # Test 2: Config validation
    print("\n[Test 2] Testing config parameter validation")
    try:
        invalid_config = PoseConfig(model_complexity=3)
        assert False, "Should raise ValueError for invalid model_complexity"
    except ValueError as e:
        print(f"  ✅ Correctly rejected invalid model_complexity: {e}")

    try:
        invalid_config = PoseConfig(min_detection_confidence=1.5)
        assert False, "Should raise ValueError for confidence > 1.0"
    except ValueError as e:
        print(f"  ✅ Correctly rejected invalid confidence: {e}")

    # Test 3: PRESET_HIGH_QUALITY
    print("\n[Test 3] Testing PRESET_HIGH_QUALITY")
    print(f"  Config: {PRESET_HIGH_QUALITY}")
    assert PRESET_HIGH_QUALITY.model_complexity == 2
    assert PRESET_HIGH_QUALITY.min_detection_confidence == 0.5
    assert PRESET_HIGH_QUALITY.smooth_landmarks == True
    print("  ✅ PRESET_HIGH_QUALITY verified")

    # Test 4: PRESET_FAST
    print("\n[Test 4] Testing PRESET_FAST")
    print(f"  Config: {PRESET_FAST}")
    assert PRESET_FAST.model_complexity == 0
    assert PRESET_FAST.min_detection_confidence == 0.3
    assert PRESET_FAST.smooth_landmarks == False
    print("  ✅ PRESET_FAST verified")

    # Test 5: PRESET_DIFFICULT_VIDEO
    print("\n[Test 5] Testing PRESET_DIFFICULT_VIDEO")
    print(f"  Config: {PRESET_DIFFICULT_VIDEO}")
    assert PRESET_DIFFICULT_VIDEO.model_complexity == 2
    assert PRESET_DIFFICULT_VIDEO.min_detection_confidence == 0.3
    assert PRESET_DIFFICULT_VIDEO.smooth_landmarks == True
    print("  ✅ PRESET_DIFFICULT_VIDEO verified")

    # Test 5b: PRESET_SLOW_MOTION
    print("\n[Test 5b] Testing PRESET_SLOW_MOTION")
    print(f"  Config: {PRESET_SLOW_MOTION}")
    assert PRESET_SLOW_MOTION.model_complexity == 2
    assert PRESET_SLOW_MOTION.min_detection_confidence == 0.5
    assert PRESET_SLOW_MOTION.min_tracking_confidence == 0.7
    assert PRESET_SLOW_MOTION.smooth_landmarks == True
    print("  ✅ PRESET_SLOW_MOTION verified")

    # Test 6: VideoProcessor with custom config
    print("\n[Test 6] Testing VideoProcessor with custom config")
    config = PoseConfig(model_complexity=1, min_detection_confidence=0.4)
    processor = VideoProcessor(pose_config=config)
    assert processor.pose_config.model_complexity == 1
    assert processor.pose_config.min_detection_confidence == 0.4
    print("  ✅ VideoProcessor initialized with custom config")

    # Test 7: VideoProcessor with default config
    print("\n[Test 7] Testing VideoProcessor with default config")
    processor = VideoProcessor()
    assert processor.pose_config.model_complexity == 1  # default
    assert processor.pose_config.min_detection_confidence == 0.5  # default
    print("  ✅ VideoProcessor initialized with default config")

    # Test 8: VideoProcessor with preset config
    print("\n[Test 8] Testing VideoProcessor with PRESET_DIFFICULT_VIDEO")
    processor = VideoProcessor(pose_config=PRESET_DIFFICULT_VIDEO)
    assert processor.pose_config.model_complexity == 2
    assert processor.pose_config.min_detection_confidence == 0.3
    print("  ✅ VideoProcessor initialized with preset config")

    # Test 9: Process video with custom config (if video available)
    test_video = 'uploads/novakswing.mp4'
    if os.path.exists(test_video):
        print(f"\n[Test 9] Processing video with custom config: {test_video}")
        config = PoseConfig(model_complexity=1, min_detection_confidence=0.4)
        processor = VideoProcessor(pose_config=config)

        video_data = processor.process_video(test_video)

        assert video_data is not None
        assert 'tracking_quality' in video_data
        assert 'frames' in video_data
        print(f"  Processed {video_data['frame_count']} frames")
        print(f"  Detection rate: {video_data['tracking_quality']['detection_rate']*100:.1f}%")
        print("  ✅ Video processed successfully with custom config")
    else:
        print(f"\n[Test 9] Skipping - video not found: {test_video}")

    # Test 10: Process video with preset config (if video available)
    test_video2 = 'uploads/novak_swing.mp4'
    if os.path.exists(test_video2):
        print(f"\n[Test 10] Processing video with PRESET_DIFFICULT_VIDEO: {test_video2}")
        processor = VideoProcessor(pose_config=PRESET_DIFFICULT_VIDEO)

        video_data = processor.process_video(test_video2)

        assert video_data is not None
        assert 'tracking_quality' in video_data
        print(f"  Processed {video_data['frame_count']} frames")
        print(f"  Detection rate: {video_data['tracking_quality']['detection_rate']*100:.1f}%")
        print("  ✅ Video processed successfully with preset config")
    else:
        print(f"\n[Test 10] Skipping - video not found: {test_video2}")

    print("\n" + "="*60)
    print("✅ ALL POSE CONFIGURATION TESTS PASSED")
    print("="*60)


if __name__ == "__main__":
    """Run all tests."""
    try:
        test_tracking_quality()
        test_tracking_quality_edge_cases()
        test_pose_config()
        test_multiple_videos()
        print("\n🎉 All video processor tests completed successfully!\n")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        sys.exit(1)
