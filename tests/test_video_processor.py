"""
Unit tests for video_processor module

Tests the video processing and tracking quality assessment functionality.
"""

import sys
import os

# Add parent directory to path to import video_processor
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from video_processor import VideoProcessor


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

    video_paths = [
        'uploads/test_swing.mp4',
        'uploads/novak_swing.mp4',
        'uploads/novakswing.mp4'
    ]

    processor = VideoProcessor()
    results = []

    for video_path in video_paths:
        if not os.path.exists(video_path):
            print(f"\n⚠️  Skipping {video_path} - not found")
            continue

        print(f"\n{'='*60}")
        print(f"Processing: {video_path}")
        print('='*60)

        try:
            video_data = processor.process_video(video_path)
            results.append({
                'path': video_path,
                'tracking_quality': video_data['tracking_quality']
            })
            print(f"✅ Successfully processed")
        except Exception as e:
            print(f"❌ Error processing: {e}")

    # Print comparison
    if len(results) > 1:
        print(f"\n{'='*60}")
        print("COMPARISON ACROSS VIDEOS")
        print('='*60)
        print(f"\n{'Video':<30} {'Detection':<12} {'High Conf':<12} {'Avg Conf':<12}")
        print("-" * 60)
        for result in results:
            video_name = os.path.basename(result['path'])
            tq = result['tracking_quality']
            print(f"{video_name:<30} {tq['detection_rate']*100:>10.1f}% {tq['high_confidence_rate']*100:>10.1f}% {tq['average_confidence']:>10.3f}")
        print('='*60)


if __name__ == "__main__":
    """Run all tests."""
    try:
        test_tracking_quality()
        test_tracking_quality_edge_cases()
        test_multiple_videos()
        print("\n🎉 All video processor tests completed successfully!\n")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        sys.exit(1)
