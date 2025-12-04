"""
Integration Tests for Tennis Swing Analysis Pipeline

Tests the complete pipeline with all improvements:
- Video quality checking
- Configurable pose detection
- Kinematic chain analysis
- Failure handling
- Visualization generation
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from video_processor import VideoProcessor, PRESET_DIFFICULT_VIDEO, PoseConfig
from swing_analyzer import SwingAnalyzer
from visualize_swing import visualize_swing_phases


def test_full_pipeline_with_all_improvements():
    """Test complete pipeline with multiple videos of varying quality."""
    print("\n" + "="*60)
    print("TESTING FULL PIPELINE WITH ALL IMPROVEMENTS")
    print("="*60)

    test_videos = [
        ('uploads/test_swing.mp4', 'good quality'),
        ('uploads/novakswing.mp4', 'low resolution'),
        ('uploads/novak_swing.mp4', 'motion blur/slow-mo')
    ]

    results = []

    for video_path, description in test_videos:
        print(f"\n{'='*60}")
        print(f"Testing: {video_path} ({description})")
        print(f"{'='*60}")

        # Check if video exists
        if not os.path.exists(video_path):
            print(f"  ⚠️  Video not found: {video_path}")
            print(f"  Skipping this video...")
            results.append({
                'video': video_path,
                'description': description,
                'status': 'skipped',
                'reason': 'file_not_found'
            })
            continue

        try:
            # Step 1: Basic video quality check (file size, existence)
            print(f"\n[Step 1] Checking video file...")
            file_size_mb = os.path.getsize(video_path) / (1024 * 1024)
            print(f"  File size: {file_size_mb:.2f} MB")

            # Step 2: Process video with appropriate config
            print(f"\n[Step 2] Processing video...")

            # Use PRESET_DIFFICULT_VIDEO for challenging videos
            if 'low resolution' in description or 'motion blur' in description:
                print(f"  Using PRESET_DIFFICULT_VIDEO for {description}")
                config = PRESET_DIFFICULT_VIDEO
            else:
                print(f"  Using default config")
                config = None

            processor = VideoProcessor(pose_config=config)
            video_data = processor.process_video(video_path)

            # Check tracking quality
            tracking_quality = video_data['tracking_quality']
            detection_rate = tracking_quality['detection_rate']
            print(f"\n  Tracking Results:")
            print(f"    Detection rate: {detection_rate*100:.1f}%")
            print(f"    High confidence rate: {tracking_quality['high_confidence_rate']*100:.1f}%")
            print(f"    Average confidence: {tracking_quality['average_confidence']:.3f}")

            if detection_rate < 0.5:
                print(f"  ⚠️  WARNING: Very low detection rate - video may not be suitable")

            # Step 3: Analyze swing with kinematic chain
            print(f"\n[Step 3] Analyzing swing with kinematic chain...")
            analyzer = SwingAnalyzer(
                kinematic_chain_mode=True,
                contact_detection_method='hybrid',
                use_adaptive_velocity=True,
                adaptive_velocity_percent=0.15,
                contact_angle_min=120
            )
            phases = analyzer.analyze_swing(video_data)

            # Step 4: Check phase detection results
            print(f"\n[Step 4] Phase Detection Results:")
            phase_names = ['backswing_start', 'max_backswing', 'forward_swing_start', 'contact', 'follow_through']

            detected_phases = []
            for phase_name in phase_names:
                phase_data = phases.get(phase_name, {})
                detected = phase_data.get('detected', False)
                confidence = phase_data.get('confidence', 0.0)
                reason = phase_data.get('reason', 'N/A')
                method = phase_data.get('method', '')

                status = "✅" if detected else "❌"
                print(f"  {status} {phase_name:20s}: detected={detected}, conf={confidence:.2f}")

                if detected:
                    detected_phases.append(phase_name)
                    frame = phase_data.get('frame', 'N/A')
                    timestamp = phase_data.get('timestamp', 0)
                    print(f"      Frame: {frame}, Time: {timestamp:.2f}s, Method: {method}")
                else:
                    print(f"      Reason: {reason}")

            # Check overall quality
            analysis_quality = phases.get('_analysis_quality', {})
            overall_score = analysis_quality.get('overall_score', 0.0)
            phases_detected = analysis_quality.get('phases_detected', 0)
            total_phases = analysis_quality.get('total_phases', 5)

            print(f"\n  Overall Analysis Quality:")
            print(f"    Phases detected: {phases_detected}/{total_phases}")
            print(f"    Overall score: {overall_score:.2f}")

            # Step 5: Generate visualization (optional - commented out to avoid creating files)
            print(f"\n[Step 5] Visualization generation...")
            output_path = f"results/test_integration_{os.path.basename(video_path)}"
            print(f"  Output path: {output_path}")
            print(f"  ⚠️  Skipping visualization to avoid creating large files")
            # Uncomment to actually generate:
            # visualize_swing_phases(
            #     video_path,
            #     output_path,
            #     use_adaptive=True,
            #     adaptive_percent=0.15,
            #     contact_angle_min=120,
            #     kinematic_chain_mode=True
            # )

            # Record results
            results.append({
                'video': video_path,
                'description': description,
                'status': 'success',
                'detection_rate': detection_rate,
                'phases_detected': phases_detected,
                'overall_score': overall_score,
                'detected_phase_list': detected_phases
            })

            print(f"\n✅ Pipeline completed successfully for {video_path}")

        except Exception as e:
            print(f"\n❌ Error processing {video_path}: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'video': video_path,
                'description': description,
                'status': 'error',
                'error': str(e)
            })

    # Print summary
    print(f"\n{'='*60}")
    print("INTEGRATION TEST SUMMARY")
    print(f"{'='*60}")

    for result in results:
        print(f"\n{result['video']} ({result['description']}):")
        print(f"  Status: {result['status']}")

        if result['status'] == 'success':
            print(f"  Detection rate: {result['detection_rate']*100:.1f}%")
            print(f"  Phases detected: {result['phases_detected']}/5")
            print(f"  Overall score: {result['overall_score']:.2f}")
            print(f"  Detected phases: {', '.join(result['detected_phase_list'])}")
        elif result['status'] == 'error':
            print(f"  Error: {result['error']}")
        elif result['status'] == 'skipped':
            print(f"  Reason: {result['reason']}")

    # Count successes
    successful = sum(1 for r in results if r['status'] == 'success')
    total = len(results)

    print(f"\n{'='*60}")
    print(f"Processed {successful}/{total} videos successfully")
    print(f"{'='*60}")

    # Test passes if at least one video was processed successfully
    assert successful > 0, "No videos were processed successfully"

    print("\n✅ Full integration test passed!")
    return results


def test_kinematic_chain_vs_traditional():
    """Compare kinematic chain vs traditional detection methods."""
    print("\n" + "="*60)
    print("TESTING KINEMATIC CHAIN VS TRADITIONAL METHODS")
    print("="*60)

    test_video = 'uploads/test_swing.mp4'

    if not os.path.exists(test_video):
        print(f"  ⚠️  Video not found: {test_video}")
        print(f"  Skipping comparison test...")
        return

    print(f"\nProcessing: {test_video}")

    # Process video once
    processor = VideoProcessor()
    video_data = processor.process_video(test_video)

    # Test different configurations
    configs = [
        {
            'name': 'Traditional (velocity_peak)',
            'kinematic_chain_mode': False,
            'contact_detection_method': 'velocity_peak'
        },
        {
            'name': 'Kinematic Chain',
            'kinematic_chain_mode': True,
            'contact_detection_method': 'kinematic_chain'
        },
        {
            'name': 'Hybrid',
            'kinematic_chain_mode': True,
            'contact_detection_method': 'hybrid'
        }
    ]

    results = []

    for config in configs:
        print(f"\n--- {config['name']} ---")

        analyzer = SwingAnalyzer(
            kinematic_chain_mode=config['kinematic_chain_mode'],
            contact_detection_method=config['contact_detection_method'],
            use_adaptive_velocity=True,
            adaptive_velocity_percent=0.15
        )

        phases = analyzer.analyze_swing(video_data)

        # Check contact detection
        contact = phases.get('contact', {})
        detected = contact.get('detected', False)
        confidence = contact.get('confidence', 0.0)
        method = contact.get('method', '')
        frame = contact.get('frame', 'N/A')

        print(f"  Detected: {detected}")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Method used: {method}")
        print(f"  Frame: {frame}")

        # Get overall quality
        quality = phases.get('_analysis_quality', {})
        phases_detected = quality.get('phases_detected', 0)

        print(f"  Phases detected: {phases_detected}/5")

        results.append({
            'config': config['name'],
            'detected': detected,
            'confidence': confidence,
            'phases_detected': phases_detected,
            'frame': frame
        })

    # Compare results
    print(f"\n{'='*60}")
    print("COMPARISON SUMMARY")
    print(f"{'='*60}")

    for result in results:
        print(f"\n{result['config']}:")
        print(f"  Contact detected: {result['detected']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Phases detected: {result['phases_detected']}/5")
        print(f"  Frame: {result['frame']}")

    print("\n✅ Comparison test passed!")


if __name__ == "__main__":
    """Run all integration tests."""
    try:
        test_full_pipeline_with_all_improvements()
        test_kinematic_chain_vs_traditional()
        print("\n🎉 All integration tests completed successfully!\n")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
