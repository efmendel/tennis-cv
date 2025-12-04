"""
Test API Flow - Complete Pipeline Test

Tests the complete tennis swing analysis pipeline:
1. Video processing with VideoProcessor
2. Swing analysis with SwingAnalyzer
3. Results validation with SwingAnalysisResults
4. Visualization generation with visualize_swing_phases
5. JSON output verification

Tests with multiple videos of varying quality to ensure robustness.
"""

import os
import sys
import json
from pathlib import Path

from video_processor import VideoProcessor, PRESET_DIFFICULT_VIDEO
from swing_analyzer import SwingAnalyzer
from analysis_results import SwingAnalysisResults
from visualize_swing import visualize_swing_phases


def validate_swing_results(results: SwingAnalysisResults, video_path: str) -> dict:
    """
    Validate that SwingAnalysisResults contains all expected fields.

    Args:
        results: SwingAnalysisResults object to validate
        video_path: Path to video file (for reporting)

    Returns:
        dict: Validation report with status and details
    """
    print("\n[Validation] Checking SwingAnalysisResults structure...")

    validation_report = {
        'video': video_path,
        'valid': True,
        'issues': [],
        'warnings': []
    }

    results_dict = results.to_dict()

    # Check phases
    if 'phases' not in results_dict:
        validation_report['valid'] = False
        validation_report['issues'].append("Missing 'phases' key")
    else:
        phases = results_dict['phases']
        expected_phases = ['unit_turn', 'backswing', 'forward_swing', 'contact', 'follow_through']

        for phase_name in expected_phases:
            if phase_name not in phases:
                validation_report['valid'] = False
                validation_report['issues'].append(f"Missing phase: {phase_name}")
            else:
                phase_data = phases[phase_name]
                if phase_data is None:
                    validation_report['warnings'].append(f"Phase {phase_name} is None")
                elif isinstance(phase_data, dict):
                    # Check required fields
                    required_fields = ['detected', 'confidence']
                    for field in required_fields:
                        if field not in phase_data:
                            validation_report['valid'] = False
                            validation_report['issues'].append(
                                f"Phase {phase_name} missing field: {field}"
                            )

    # Check engine metrics
    if 'engine' not in results_dict:
        validation_report['valid'] = False
        validation_report['issues'].append("Missing 'engine' key")
    else:
        engine = results_dict['engine']
        expected_engine_fields = ['hip_shoulder_separation', 'max_shoulder_rotation', 'max_hip_rotation']
        for field in expected_engine_fields:
            if field not in engine:
                validation_report['warnings'].append(f"Engine missing field: {field}")

    # Check tempo metrics
    if 'tempo' not in results_dict:
        validation_report['valid'] = False
        validation_report['issues'].append("Missing 'tempo' key")
    else:
        tempo = results_dict['tempo']
        expected_tempo_fields = ['backswing_duration', 'forward_swing_duration', 'swing_rhythm_ratio']
        for field in expected_tempo_fields:
            if field not in tempo:
                validation_report['warnings'].append(f"Tempo missing field: {field}")

    # Check kinetic chain metrics
    if 'kinetic_chain' not in results_dict:
        validation_report['valid'] = False
        validation_report['issues'].append("Missing 'kinetic_chain' key")
    else:
        kc = results_dict['kinetic_chain']
        expected_kc_fields = ['peak_velocity_sequence', 'chain_lag', 'confidence']
        for field in expected_kc_fields:
            if field not in kc:
                validation_report['warnings'].append(f"Kinetic chain missing field: {field}")

    # Check tracking quality
    if 'tracking_quality' not in results_dict:
        validation_report['warnings'].append("Missing 'tracking_quality' key")

    # Print validation results
    if validation_report['valid']:
        print("  ✅ Structure validation passed")
    else:
        print("  ❌ Structure validation FAILED")
        for issue in validation_report['issues']:
            print(f"     - {issue}")

    if validation_report['warnings']:
        print("  ⚠️  Warnings:")
        for warning in validation_report['warnings']:
            print(f"     - {warning}")

    return validation_report


def print_statistics(results: SwingAnalysisResults, video_path: str):
    """
    Print comprehensive statistics from SwingAnalysisResults.

    Args:
        results: SwingAnalysisResults object
        video_path: Path to video file (for reporting)
    """
    print("\n" + "="*60)
    print(f"STATISTICS FOR: {video_path}")
    print("="*60)

    results_dict = results.to_dict()

    # Overall quality
    phases_detected = results.get_phases_detected_count()
    overall_confidence = results.get_overall_confidence()

    print(f"\n📊 Overall Quality:")
    print(f"   Phases Detected: {phases_detected}/5")
    print(f"   Overall Confidence: {overall_confidence:.2%}")

    # Phase details
    print(f"\n🎯 Phase Detection:")
    phases = results_dict['phases']
    for phase_name in ['unit_turn', 'backswing', 'forward_swing', 'contact', 'follow_through']:
        phase_data = phases.get(phase_name, {})
        if phase_data and isinstance(phase_data, dict):
            detected = phase_data.get('detected', False)
            confidence = phase_data.get('confidence', 0.0)

            if detected:
                frame = phase_data.get('frame', 'N/A')
                timestamp = phase_data.get('timestamp', 0)
                print(f"   ✅ {phase_name:15s}: frame {frame:4}, time {timestamp:.2f}s, conf {confidence:.2%}")
            else:
                reason = phase_data.get('reason', 'Unknown')
                print(f"   ❌ {phase_name:15s}: {reason}")

    # Engine metrics
    engine = results_dict['engine']
    if engine.get('hip_shoulder_separation'):
        print(f"\n💪 Engine Metrics:")
        hip_shoulder = engine['hip_shoulder_separation']
        print(f"   Hip-Shoulder Separation: {hip_shoulder.get('max_value', 0):.1f}° "
              f"(frame {hip_shoulder.get('frame', 'N/A')})")

        if engine.get('max_shoulder_rotation'):
            shoulder_rot = engine['max_shoulder_rotation']
            print(f"   Max Shoulder Rotation: {shoulder_rot.get('value', 0):.1f}° "
                  f"(frame {shoulder_rot.get('frame', 'N/A')})")

        if engine.get('max_hip_rotation'):
            hip_rot = engine['max_hip_rotation']
            print(f"   Max Hip Rotation: {hip_rot.get('value', 0):.1f}° "
                  f"(frame {hip_rot.get('frame', 'N/A')})")

    # Tempo metrics
    tempo = results_dict['tempo']
    if tempo.get('backswing_duration') is not None:
        print(f"\n⏱️  Tempo Metrics:")
        print(f"   Backswing Duration: {tempo['backswing_duration']:.3f}s")

        if tempo.get('forward_swing_duration'):
            print(f"   Forward Swing Duration: {tempo['forward_swing_duration']:.3f}s")

        if tempo.get('swing_rhythm_ratio'):
            print(f"   Swing Rhythm Ratio: {tempo['swing_rhythm_ratio']:.2f}")

    # Kinetic chain metrics
    kc = results_dict['kinetic_chain']
    if kc.get('peak_velocity_sequence'):
        print(f"\n⛓️  Kinetic Chain:")
        sequence = kc['peak_velocity_sequence']

        for segment in ['hip', 'shoulder', 'elbow', 'wrist']:
            if segment in sequence and sequence[segment]:
                data = sequence[segment]
                print(f"   {segment.capitalize():8s} peak: frame {data.get('frame', 'N/A'):4}, "
                      f"time {data.get('timestamp', 0):.2f}s, "
                      f"vel {data.get('velocity', 0):.1f}")

        if kc.get('chain_lag'):
            lag = kc['chain_lag']
            print(f"\n   Lag Times:")
            if 'hip_to_shoulder' in lag:
                print(f"      Hip → Shoulder: {lag['hip_to_shoulder']:.3f}s")
            if 'shoulder_to_elbow' in lag:
                print(f"      Shoulder → Elbow: {lag['shoulder_to_elbow']:.3f}s")
            if 'elbow_to_wrist' in lag:
                print(f"      Elbow → Wrist: {lag['elbow_to_wrist']:.3f}s")

        if kc.get('confidence') is not None:
            print(f"\n   Sequencing Confidence: {kc['confidence']:.2%}")

    # Tracking quality
    if results_dict.get('tracking_quality'):
        tq = results_dict['tracking_quality']
        print(f"\n📹 Tracking Quality:")
        print(f"   Detection Rate: {tq.get('detection_rate', 0):.2%}")
        print(f"   High Confidence Rate: {tq.get('high_confidence_rate', 0):.2%}")
        print(f"   Average Confidence: {tq.get('average_confidence', 0):.2%}")


def test_pipeline(video_path: str, output_dir: str = "test_results") -> dict:
    """
    Test complete pipeline on a single video.

    Args:
        video_path: Path to input video
        output_dir: Directory for output files

    Returns:
        dict: Test results with status and paths
    """
    print("\n" + "="*70)
    print(f"TESTING PIPELINE: {video_path}")
    print("="*70)

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    test_results = {
        'video': video_path,
        'status': 'pending',
        'error': None,
        'validation': None,
        'output_video': None,
        'json_output': None
    }

    try:
        # Check if video exists
        if not os.path.exists(video_path):
            test_results['status'] = 'skipped'
            test_results['error'] = f"Video not found: {video_path}"
            print(f"⚠️  Skipping - video not found: {video_path}")
            return test_results

        # Step 1: Process video
        print("\n[Step 1] Processing video with VideoProcessor...")
        processor = VideoProcessor(pose_config=PRESET_DIFFICULT_VIDEO)
        video_data = processor.process_video(video_path)
        print(f"  ✅ Processed {video_data['frame_count']} frames at {video_data['fps']} fps")

        # Step 2: Analyze swing
        print("\n[Step 2] Analyzing swing with SwingAnalyzer...")
        analyzer = SwingAnalyzer(
            kinematic_chain_mode=True,
            contact_detection_method='kinematic_chain',
            use_adaptive_velocity=True,
            adaptive_velocity_percent=0.15,
            contact_angle_min=120
        )
        results = analyzer.analyze_swing(video_data)
        print(f"  ✅ Analysis complete")
        print(f"     Phases detected: {results.get_phases_detected_count()}/5")
        print(f"     Overall confidence: {results.get_overall_confidence():.2%}")

        # Step 3: Validate results
        print("\n[Step 3] Validating SwingAnalysisResults...")
        validation = validate_swing_results(results, video_path)
        test_results['validation'] = validation

        if not validation['valid']:
            test_results['status'] = 'failed'
            test_results['error'] = 'Validation failed'
            return test_results

        # Step 4: Create visualization
        print("\n[Step 4] Creating annotated video...")
        video_filename = os.path.basename(video_path)
        output_video_path = os.path.join(output_dir, f"annotated_{video_filename}")

        returned_path = visualize_swing_phases(
            video_path=video_path,
            analysis_results=results,
            output_path=output_video_path
        )

        test_results['output_video'] = returned_path
        print(f"  ✅ Video saved to: {returned_path}")

        # Step 5: Generate JSON output
        print("\n[Step 5] Generating JSON output...")
        json_output_path = os.path.join(output_dir, f"analysis_{video_filename}.json")

        json_data = results.to_dict()
        with open(json_output_path, 'w') as f:
            json.dump(json_data, f, indent=2)

        test_results['json_output'] = json_output_path
        print(f"  ✅ JSON saved to: {json_output_path}")

        # Step 6: Print statistics
        print_statistics(results, video_path)

        # Step 7: Print example JSON (first 50 lines)
        print("\n[Example JSON Output - First 50 lines]")
        print("-" * 60)
        json_str = results.to_json(indent=2)
        lines = json_str.split('\n')
        for i, line in enumerate(lines[:50]):
            print(line)
        if len(lines) > 50:
            print(f"... ({len(lines) - 50} more lines)")
        print("-" * 60)

        test_results['status'] = 'success'
        print("\n✅ Pipeline test completed successfully!")

    except Exception as e:
        test_results['status'] = 'error'
        test_results['error'] = str(e)
        print(f"\n❌ Error during pipeline test: {e}")
        import traceback
        traceback.print_exc()

    return test_results


def test_all_videos():
    """Test pipeline with all three test videos."""
    print("\n" + "="*70)
    print("TESTING COMPLETE PIPELINE WITH ALL VIDEOS")
    print("="*70)

    test_videos = [
        ('uploads/test_swing.mp4', 'good quality'),
        ('uploads/novakswing.mp4', 'low resolution'),
        ('uploads/novak_swing.mp4', 'motion blur/slow-mo')
    ]

    results = []

    for video_path, description in test_videos:
        print(f"\n\n{'='*70}")
        print(f"Testing: {video_path} ({description})")
        print(f"{'='*70}")

        result = test_pipeline(video_path)
        result['description'] = description
        results.append(result)

    # Print summary
    print("\n\n" + "="*70)
    print("SUMMARY - ALL VIDEOS")
    print("="*70)

    for result in results:
        print(f"\n{result['video']} ({result['description']}):")
        print(f"  Status: {result['status']}")

        if result['status'] == 'success':
            validation = result['validation']
            print(f"  Validation: {'✅ Passed' if validation['valid'] else '❌ Failed'}")
            if validation['warnings']:
                print(f"  Warnings: {len(validation['warnings'])}")
            print(f"  Output Video: {result['output_video']}")
            print(f"  JSON Output: {result['json_output']}")
        elif result['status'] == 'skipped':
            print(f"  Reason: {result['error']}")
        elif result['status'] in ['failed', 'error']:
            print(f"  Error: {result['error']}")

    # Count successes
    successful = sum(1 for r in results if r['status'] == 'success')
    total = len(results)

    print("\n" + "="*70)
    print(f"Results: {successful}/{total} videos processed successfully")
    print("="*70)

    return results


if __name__ == "__main__":
    """Run complete pipeline tests."""

    # Check if user wants to test single video or all
    if len(sys.argv) > 1:
        # Test single video
        video_path = sys.argv[1]
        print(f"\nTesting single video: {video_path}")
        result = test_pipeline(video_path)

        if result['status'] == 'success':
            print("\n✅ Test passed!")
            sys.exit(0)
        else:
            print(f"\n❌ Test failed: {result['error']}")
            sys.exit(1)
    else:
        # Test all videos
        results = test_all_videos()

        # Exit with appropriate code
        failed = sum(1 for r in results if r['status'] in ['failed', 'error'])
        if failed > 0:
            print(f"\n❌ {failed} test(s) failed")
            sys.exit(1)
        else:
            print("\n✅ All tests passed!")
            sys.exit(0)
