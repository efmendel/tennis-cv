import json

import cv2  # pylint: disable=no-member
import mediapipe as mp

from swing_analyzer import SwingAnalyzer
from video_processor import VideoProcessor, PRESET_DIFFICULT_VIDEO
from analysis_results import SwingAnalysisResults


def visualize_swing_phases(video_path, analysis_results=None, output_path="output_annotated.mp4",
                          use_adaptive=False, velocity_threshold=0.5,
                          adaptive_percent=0.15, contact_angle_min=150,
                          kinematic_chain_mode=False, contact_detection_method='velocity_peak'):
    """
    Create annotated video with swing phases overlaid.

    Can accept pre-computed analysis results or perform analysis on the fly.

    Args:
        video_path: Path to input video
        analysis_results: SwingAnalysisResults object (optional, for pre-computed analysis)
        output_path: Path for output video
        use_adaptive: If True, uses adaptive velocity threshold (only if analysis_results is None)
        velocity_threshold: Fixed velocity threshold (only if analysis_results is None)
        adaptive_percent: Percentage of max velocity for threshold (only if analysis_results is None)
        contact_angle_min: Minimum elbow angle at contact in degrees (only if analysis_results is None)
        kinematic_chain_mode: If True, uses multi-joint biomechanical analysis (only if analysis_results is None)
        contact_detection_method: Method for contact detection (only if analysis_results is None)

    Returns:
        str: Path to the output video file
    """
    # If analysis_results is provided, use it. Otherwise, perform analysis
    if analysis_results is None:
        print("Processing video...")
        processor = VideoProcessor(pose_config=PRESET_DIFFICULT_VIDEO)
        video_data = processor.process_video(video_path)

        print("Analyzing swing phases...")
        analyzer = SwingAnalyzer(
            velocity_threshold=velocity_threshold,
            contact_angle_min=contact_angle_min,
            use_adaptive_velocity=use_adaptive,
            adaptive_velocity_percent=adaptive_percent,
            kinematic_chain_mode=kinematic_chain_mode,
            contact_detection_method=contact_detection_method
        )
        analysis_results = analyzer.analyze_swing(video_data)

        # Extract phases dict from SwingAnalysisResults for backward compatibility
        phases = analysis_results.to_dict()['phases']
    else:
        print("Using pre-computed analysis results...")
        # Extract phases from SwingAnalysisResults
        phases = analysis_results.to_dict()['phases']

        # We need to reprocess video to get frame count
        processor = VideoProcessor(pose_config=PRESET_DIFFICULT_VIDEO)
        video_data = processor.process_video(video_path)

    print("Creating annotated video...")

    # Open original video
    cap = cv2.VideoCapture(video_path)
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    # MediaPipe for drawing skeleton
    mp_pose = mp.solutions.pose
    mp_drawing = mp.solutions.drawing_utils
    pose = mp_pose.Pose()

    # Determine which phase each frame belongs to
    frame_phases = _assign_phases_to_frames(phases, video_data["frame_count"])

    frame_number = 0

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            break

        frame_number += 1

        # Process with MediaPipe to draw skeleton
        image_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(image_rgb)

        if results.pose_landmarks:
            # Draw skeleton
            mp_drawing.draw_landmarks(
                frame,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(0, 255, 0), thickness=2, circle_radius=3),
                mp_drawing.DrawingSpec(color=(0, 0, 255), thickness=2),
            )

        # Get current phase, confidence, and reason
        phase_info = frame_phases.get(frame_number, ("Analyzing...", 0.0, "Unknown"))
        current_phase, phase_confidence, phase_reason = phase_info
        timestamp = frame_number / fps

        # Draw semi-transparent background for text
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (700, 150), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        # Draw phase text with confidence
        phase_color = _get_phase_color(current_phase, phase_confidence)
        cv2.putText(
            frame,
            f"Phase: {current_phase}",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            phase_color,
            3,
        )

        # Draw confidence indicator if phase is detected
        if phase_confidence > 0.0:
            cv2.putText(
                frame,
                f"Confidence: {phase_confidence:.2f}",
                (20, 130),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                phase_color,
                2,
            )

        # Draw timestamp
        cv2.putText(
            frame,
            f"Time: {timestamp:.2f}s | Frame: {frame_number}",
            (20, 90),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
        )

        # Draw overall quality indicators in top right corner
        if 'tracking_quality' in video_data:
            tq = video_data['tracking_quality']
            detection_rate = tq.get('detection_rate', 0.0)

            # Draw semi-transparent background for quality info
            overlay_quality = frame.copy()
            cv2.rectangle(overlay_quality, (width - 350, 10), (width - 10, 130), (0, 0, 0), -1)
            cv2.addWeighted(overlay_quality, 0.6, frame, 0.4, 0, frame)

            # Draw tracking quality
            tracking_color = (0, 255, 0) if detection_rate > 0.7 else (0, 255, 255) if detection_rate > 0.5 else (0, 0, 255)
            cv2.putText(
                frame,
                f"Tracking: {detection_rate*100:.1f}%",
                (width - 340, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                tracking_color,
                2,
            )

            # Draw analysis quality using SwingAnalysisResults methods
            overall_confidence = analysis_results.get_overall_confidence()
            phases_detected = analysis_results.get_phases_detected_count()

            analysis_color = (0, 255, 0) if overall_confidence > 0.7 else (0, 255, 255) if overall_confidence > 0.5 else (0, 0, 255)
            cv2.putText(
                frame,
                f"Analysis: {overall_confidence*100:.1f}%",
                (width - 340, 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                analysis_color,
                2,
            )

            # Show phases detected count
            cv2.putText(
                frame,
                f"Phases: {phases_detected}/5",
                (width - 340, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 255),
                2,
            )

        # Draw engine metrics during backswing phases
        if "BACKSWING" in current_phase or "UNIT TURN" in current_phase:
            engine_data = analysis_results.to_dict()['engine']
            if engine_data.get('hip_shoulder_separation'):
                hip_shoulder_sep = engine_data['hip_shoulder_separation'].get('max_value', 0)

                # Draw semi-transparent background for engine metrics
                overlay_engine = frame.copy()
                cv2.rectangle(overlay_engine, (10, height - 120), (400, height - 10), (0, 0, 0), -1)
                cv2.addWeighted(overlay_engine, 0.6, frame, 0.4, 0, frame)

                cv2.putText(
                    frame,
                    f"Hip-Shoulder Sep: {hip_shoulder_sep:.1f}°",
                    (20, height - 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 100, 0),  # Blue
                    2,
                )

                if engine_data.get('max_shoulder_rotation'):
                    shoulder_rot = engine_data['max_shoulder_rotation'].get('value', 0)
                    cv2.putText(
                        frame,
                        f"Shoulder Rotation: {shoulder_rot:.1f}°",
                        (20, height - 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 100, 0),  # Blue
                        2,
                    )

                if engine_data.get('max_hip_rotation'):
                    hip_rot = engine_data['max_hip_rotation'].get('value', 0)
                    cv2.putText(
                        frame,
                        f"Hip Rotation: {hip_rot:.1f}°",
                        (20, height - 20),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.6,
                        (255, 100, 0),  # Blue
                        2,
                    )

        # Draw tempo metrics during finish phase
        if "FINISH" in current_phase:
            tempo_data = analysis_results.to_dict()['tempo']
            if tempo_data.get('backswing_duration') is not None:
                # Draw semi-transparent background for tempo metrics
                overlay_tempo = frame.copy()
                cv2.rectangle(overlay_tempo, (10, height - 120), (450, height - 10), (0, 0, 0), -1)
                cv2.addWeighted(overlay_tempo, 0.6, frame, 0.4, 0, frame)

                backswing_dur = tempo_data['backswing_duration']
                forward_dur = tempo_data.get('forward_swing_duration', 0)
                rhythm = tempo_data.get('swing_rhythm_ratio', 0)

                cv2.putText(
                    frame,
                    f"Backswing: {backswing_dur:.2f}s",
                    (20, height - 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 200, 255),  # Orange
                    2,
                )

                cv2.putText(
                    frame,
                    f"Forward Swing: {forward_dur:.2f}s",
                    (20, height - 50),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 200, 255),  # Orange
                    2,
                )

                cv2.putText(
                    frame,
                    f"Rhythm Ratio: {rhythm:.2f}",
                    (20, height - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 200, 255),  # Orange
                    2,
                )

        # Draw key phase markers
        key_frames = [
            p.get("frame") for p in phases.values() if p and isinstance(p, dict) and p.get("detected", False)
        ]
        if frame_number in key_frames:
            cv2.circle(frame, (width - 50, 160), 20, (0, 255, 255), -1)
            cv2.putText(
                frame,
                "KEY",
                (width - 80, 210),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2,
            )

        out.write(frame)

        # Progress
        if frame_number % 30 == 0:
            print(f"Annotating frame {frame_number}/{video_data['frame_count']}...")

    cap.release()
    out.release()
    pose.close()

    print(f"\nAnnotated video saved to: {output_path}")
    print("\nDetected phases:")
    for phase_name, phase_data in phases.items():
        if phase_data and isinstance(phase_data, dict):
            detected = phase_data.get('detected', False)
            if detected:
                timestamp = phase_data.get('timestamp', 0)
                confidence = phase_data.get('confidence', 0)
                print(f"  ✅ {phase_name}: {timestamp:.2f}s (confidence: {confidence:.2f})")
            else:
                reason = phase_data.get('reason', 'Not detected')
                print(f"  ❌ {phase_name}: {reason}")

    # Print engine metrics
    engine_data = analysis_results.to_dict()['engine']
    if engine_data.get('hip_shoulder_separation'):
        print("\nEngine Metrics:")
        print(f"  Hip-Shoulder Separation: {engine_data['hip_shoulder_separation'].get('max_value', 0):.1f}°")
        if engine_data.get('max_shoulder_rotation'):
            print(f"  Max Shoulder Rotation: {engine_data['max_shoulder_rotation'].get('value', 0):.1f}°")
        if engine_data.get('max_hip_rotation'):
            print(f"  Max Hip Rotation: {engine_data['max_hip_rotation'].get('value', 0):.1f}°")

    # Print tempo metrics
    tempo_data = analysis_results.to_dict()['tempo']
    if tempo_data.get('backswing_duration') is not None:
        print("\nTempo Metrics:")
        print(f"  Backswing Duration: {tempo_data['backswing_duration']:.2f}s")
        if tempo_data.get('forward_swing_duration'):
            print(f"  Forward Swing Duration: {tempo_data['forward_swing_duration']:.2f}s")
        if tempo_data.get('swing_rhythm_ratio'):
            print(f"  Swing Rhythm Ratio: {tempo_data['swing_rhythm_ratio']:.2f}")

    return output_path


def _assign_phases_to_frames(phases, total_frames):
    """Assign phase labels with confidence to each frame number

    Args:
        phases: Phase dict from SwingAnalysisResults (new format with unit_turn, backswing, etc.)
        total_frames: Total number of frames in video

    Returns:
        dict: Maps frame_number -> (phase_label, confidence, reason)
    """
    frame_phases = {}

    # Extract phase data with new format that includes detected/confidence/reason
    def get_phase_info(phase_name):
        """Extract frame number, confidence, and reason from phase data"""
        phase_data = phases.get(phase_name, {})
        if not phase_data or not isinstance(phase_data, dict):
            return None, 0.0, "Phase data not available"

        # Check if phase was detected
        if not phase_data.get("detected", False):
            reason = phase_data.get("reason", "Not detected")
            return None, 0.0, reason

        frame = phase_data.get("frame", 0)
        confidence = phase_data.get("confidence", 0.0)
        reason = "Detected"
        return frame, confidence, reason

    # Get frame numbers and confidences for each phase (new names from SwingAnalysisResults)
    unit_turn_frame, unit_turn_conf, unit_turn_reason = get_phase_info("unit_turn")
    backswing_frame, backswing_conf, backswing_reason = get_phase_info("backswing")
    forward_swing_frame, forward_swing_conf, forward_swing_reason = get_phase_info("forward_swing")
    contact_frame, contact_conf, contact_reason = get_phase_info("contact")
    follow_through_frame, follow_through_conf, follow_through_reason = get_phase_info("follow_through")

    # Use 0 for undetected phases
    # Note: We track whether phases were actually detected separately
    unit_turn = unit_turn_frame if unit_turn_frame else 0
    backswing = backswing_frame if backswing_frame else 0
    forward_swing = forward_swing_frame if forward_swing_frame else 0
    contact = contact_frame if contact_frame else 0
    follow_through = follow_through_frame if follow_through_frame else 0

    for frame_num in range(1, total_frames + 1):
        if unit_turn == 0 and backswing == 0:
            # No phases detected at all
            frame_phases[frame_num] = ("Analyzing...", 0.0, "No phases detected")
        elif unit_turn > 0 and frame_num < unit_turn:
            frame_phases[frame_num] = ("Ready Position", 1.0, "Before swing starts")
        elif unit_turn > 0 and backswing > 0 and frame_num >= unit_turn and frame_num < backswing:
            frame_phases[frame_num] = ("UNIT TURN", unit_turn_conf, "Preparing")
        elif backswing > 0 and forward_swing > 0 and frame_num >= backswing and frame_num < forward_swing:
            frame_phases[frame_num] = ("BACKSWING", backswing_conf, "Loading")
        elif forward_swing > 0 and contact > 0 and frame_num >= forward_swing and frame_num < contact:
            frame_phases[frame_num] = ("FORWARD SWING", forward_swing_conf, "Accelerating")
        elif contact > 0 and frame_num == contact:
            frame_phases[frame_num] = ("*** CONTACT ***", contact_conf, contact_reason)
        elif contact > 0 and follow_through > 0 and frame_num > contact and frame_num < follow_through:
            frame_phases[frame_num] = ("FOLLOW THROUGH", contact_conf, "Decelerating")
        elif follow_through > 0 and frame_num >= follow_through:
            frame_phases[frame_num] = ("FINISH", follow_through_conf, "Recovery")
        else:
            # Default based on what was detected
            if contact > 0 and frame_num > contact:
                # After contact but follow through not detected
                frame_phases[frame_num] = ("FOLLOW THROUGH", contact_conf, "After contact")
            elif forward_swing > 0 and frame_num >= forward_swing:
                # Forward swing started, continue as forward swing
                frame_phases[frame_num] = ("FORWARD SWING", forward_swing_conf, "Accelerating")
            elif backswing > 0 and frame_num >= backswing:
                # Past backswing, default to backswing
                frame_phases[frame_num] = ("BACKSWING", backswing_conf, "Loading")
            elif unit_turn > 0 and frame_num >= unit_turn:
                # Past unit turn
                frame_phases[frame_num] = ("UNIT TURN", unit_turn_conf, "Preparing")
            else:
                frame_phases[frame_num] = ("Analyzing...", 0.0, "Unknown phase")

    return frame_phases


def _get_phase_color(phase_name, confidence=1.0):
    """Return color based on phase and confidence level with phase-specific colors.

    Args:
        phase_name: Name of the phase
        confidence: Detection confidence (0.0-1.0)

    Returns:
        tuple: BGR color tuple
    """
    # For "Analyzing..." or undetected phases, use gray
    if phase_name == "Analyzing..." or confidence == 0.0:
        return (128, 128, 128)  # Gray

    # Phase-specific colors (adjusted by confidence)
    # Backswing phases: BLUE
    if "BACKSWING" in phase_name or "UNIT TURN" in phase_name or "Ready Position" in phase_name:
        if confidence > 0.8:
            return (255, 100, 0)  # Bright blue
        elif confidence >= 0.5:
            return (200, 80, 0)  # Medium blue
        else:
            return (150, 60, 0)  # Dim blue

    # Forward swing phase: GREEN
    elif "FORWARD SWING" in phase_name:
        if confidence > 0.8:
            return (0, 255, 0)  # Bright green
        elif confidence >= 0.5:
            return (0, 200, 0)  # Medium green
        else:
            return (0, 150, 0)  # Dim green

    # Contact phase: RED
    elif "CONTACT" in phase_name:
        if confidence > 0.8:
            return (0, 0, 255)  # Bright red
        elif confidence >= 0.5:
            return (0, 0, 200)  # Medium red
        else:
            return (0, 0, 150)  # Dim red

    # Follow through and finish: YELLOW/ORANGE
    elif "FOLLOW THROUGH" in phase_name or "FINISH" in phase_name:
        if confidence > 0.8:
            return (0, 200, 255)  # Bright orange
        elif confidence >= 0.5:
            return (0, 160, 200)  # Medium orange
        else:
            return (0, 120, 150)  # Dim orange

    # Default: confidence-based colors
    if confidence > 0.8:
        return (0, 255, 0)  # Green
    elif confidence >= 0.5:
        return (0, 255, 255)  # Yellow
    else:
        return (0, 0, 255)  # Red


if __name__ == "__main__":
    # ========================================
    # CONFIGURATION - CHANGE THESE SETTINGS
    # ========================================

    # Choose your video and output
    video_path = "uploads/novak_swing.mp4"
    output_path = "results/kinematic_novak_swing.mp4"

    # Toggle detection method:

    # Option 1: KINEMATIC CHAIN MODE (multi-joint biomechanical analysis) 🔥 ENABLED FOR TESTING
    USE_KINEMATIC_CHAIN = True
    USE_ADAPTIVE = True
    VELOCITY_THRESHOLD = 0.5
    ADAPTIVE_PERCENT = 0.15
    CONTACT_ANGLE_MIN = 120
    CONTACT_DETECTION_METHOD = 'kinematic_chain'  # 'velocity_peak', 'kinematic_chain', or 'hybrid'

    # Option 2: Traditional mode with fixed threshold (original)
    # USE_KINEMATIC_CHAIN = False
    # USE_ADAPTIVE = False
    # VELOCITY_THRESHOLD = 0.5
    # ADAPTIVE_PERCENT = 0.15
    # CONTACT_ANGLE_MIN = 150
    # CONTACT_DETECTION_METHOD = 'velocity_peak'

    # Option 3: Traditional mode with adaptive threshold
    # USE_KINEMATIC_CHAIN = False
    # USE_ADAPTIVE = True
    # VELOCITY_THRESHOLD = 0.5  # Ignored when adaptive is True
    # ADAPTIVE_PERCENT = 0.15  # 15% of max velocity
    # CONTACT_ANGLE_MIN = 150
    # CONTACT_DETECTION_METHOD = 'velocity_peak'

    # ========================================

    print(f"\n🎬 Video: {video_path}")
    print(f"📁 Output: {output_path}")
    if USE_KINEMATIC_CHAIN:
        print("⚙️  Mode: KINEMATIC CHAIN (multi-joint biomechanical analysis)")
        print(f"    - Adaptive velocity: {USE_ADAPTIVE}")
        print(f"    - Contact detection: {CONTACT_DETECTION_METHOD}")
    else:
        print(f"⚙️  Mode: {'Adaptive' if USE_ADAPTIVE else 'Fixed'} velocity threshold")
        print(f"    - Contact detection: {CONTACT_DETECTION_METHOD}")
    print()

    visualize_swing_phases(
        video_path,
        output_path,
        use_adaptive=USE_ADAPTIVE,
        velocity_threshold=VELOCITY_THRESHOLD,
        adaptive_percent=ADAPTIVE_PERCENT,
        contact_angle_min=CONTACT_ANGLE_MIN,
        kinematic_chain_mode=USE_KINEMATIC_CHAIN,
        contact_detection_method=CONTACT_DETECTION_METHOD
    )

    print("\n✅ Done! You can now play the annotated video.")
