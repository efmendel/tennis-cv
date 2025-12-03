import json

import cv2  # pylint: disable=no-member
import mediapipe as mp

from swing_analyzer import SwingAnalyzer
from video_processor import VideoProcessor


def visualize_swing_phases(video_path, output_path="output_annotated.mp4",
                          use_adaptive=False, velocity_threshold=0.5,
                          adaptive_percent=0.15, contact_angle_min=150):
    """
    Process video and create annotated version with swing phases overlaid

    Args:
        video_path: Path to input video
        output_path: Path for output video
        use_adaptive: If True, uses adaptive velocity threshold
        velocity_threshold: Fixed velocity threshold (if not using adaptive)
        adaptive_percent: Percentage of max velocity for threshold (if using adaptive)
        contact_angle_min: Minimum elbow angle at contact in degrees
    """
    print("Processing video...")
    processor = VideoProcessor()
    video_data = processor.process_video(video_path)

    print("Analyzing swing phases...")
    analyzer = SwingAnalyzer(
        velocity_threshold=velocity_threshold,
        contact_angle_min=contact_angle_min,
        use_adaptive_velocity=use_adaptive,
        adaptive_velocity_percent=adaptive_percent
    )
    phases = analyzer.analyze_swing(video_data)

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

        # Get current phase and confidence
        phase_info = frame_phases.get(frame_number, ("Analyzing...", 0.0))
        current_phase, phase_confidence = phase_info
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

            # Draw analysis quality if available
            if '_analysis_quality' in phases:
                aq = phases['_analysis_quality']
                overall_score = aq.get('overall_score', 0.0)

                analysis_color = (0, 255, 0) if overall_score > 0.7 else (0, 255, 255) if overall_score > 0.5 else (0, 0, 255)
                cv2.putText(
                    frame,
                    f"Analysis: {overall_score*100:.1f}%",
                    (width - 340, 75),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    analysis_color,
                    2,
                )

                # Show phases detected count
                cv2.putText(
                    frame,
                    f"Phases: {aq.get('phases_detected', 0)}/{aq.get('total_phases', 5)}",
                    (width - 340, 110),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
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
            print(f"  {phase_name}: {phase_data.get('timestamp', 'N/A'):.2f}s")


def _assign_phases_to_frames(phases, total_frames):
    """Assign phase labels with confidence to each frame number

    Returns:
        dict: Maps frame_number -> (phase_label, confidence)
    """
    frame_phases = {}

    # Extract phase data with new format that includes detected/confidence/reason
    def get_phase_info(phase_name):
        """Extract frame number and confidence from phase data"""
        phase_data = phases.get(phase_name, {})
        if not phase_data or not isinstance(phase_data, dict):
            return None, 0.0

        # Check if phase was detected
        if not phase_data.get("detected", False):
            return None, 0.0

        frame = phase_data.get("frame", 0)
        confidence = phase_data.get("confidence", 0.0)
        return frame, confidence

    # Get frame numbers and confidences for each phase
    backswing_start_frame, backswing_start_conf = get_phase_info("backswing_start")
    max_backswing_frame, max_backswing_conf = get_phase_info("max_backswing")
    forward_start_frame, forward_start_conf = get_phase_info("forward_swing_start")
    contact_frame, contact_conf = get_phase_info("contact")
    follow_through_frame, follow_through_conf = get_phase_info("follow_through")

    # Use 0 for undetected phases
    # Note: We track whether phases were actually detected separately
    backswing_start = backswing_start_frame if backswing_start_frame else 0
    max_backswing = max_backswing_frame if max_backswing_frame else 0
    forward_start = forward_start_frame if forward_start_frame else 0
    contact = contact_frame if contact_frame else 0
    follow_through = follow_through_frame if follow_through_frame else 0

    for frame_num in range(1, total_frames + 1):
        if backswing_start == 0:
            # No phases detected
            frame_phases[frame_num] = ("Analyzing...", 0.0)
        elif frame_num < backswing_start:
            frame_phases[frame_num] = ("Ready Position", 1.0)  # Always confident
        elif max_backswing > 0 and frame_num < max_backswing:
            frame_phases[frame_num] = ("BACKSWING", backswing_start_conf)
        elif forward_start > 0 and frame_num < forward_start:
            frame_phases[frame_num] = ("LOADING", max_backswing_conf)
        elif contact > 0 and frame_num < contact:
            frame_phases[frame_num] = ("FORWARD SWING", forward_start_conf)
        elif contact > 0 and frame_num == contact:
            frame_phases[frame_num] = ("*** CONTACT ***", contact_conf)
        elif contact > 0 and follow_through > 0 and frame_num < follow_through:
            frame_phases[frame_num] = ("FOLLOW THROUGH", contact_conf)
        elif follow_through > 0 and frame_num >= follow_through:
            frame_phases[frame_num] = ("FINISH", follow_through_conf)
        else:
            # Default based on what was detected
            if contact > 0:
                # Contact was detected, so everything after is follow through
                frame_phases[frame_num] = ("FOLLOW THROUGH", contact_conf)
            elif forward_start > 0:
                # Forward swing started, continue as forward swing
                frame_phases[frame_num] = ("FORWARD SWING", forward_start_conf)
            elif max_backswing > 0 and frame_num >= max_backswing:
                # Past max backswing, default to loading
                frame_phases[frame_num] = ("LOADING", max_backswing_conf)
            else:
                frame_phases[frame_num] = ("Analyzing...", 0.0)

    return frame_phases


def _get_phase_color(phase_name, confidence=1.0):
    """Return color based on phase and confidence level

    Args:
        phase_name: Name of the phase
        confidence: Detection confidence (0.0-1.0)

    Returns:
        tuple: BGR color tuple
    """
    # For "Analyzing..." or undetected phases, use gray
    if phase_name == "Analyzing..." or confidence == 0.0:
        return (128, 128, 128)  # Gray

    # Color based on confidence level
    if confidence > 0.8:
        # High confidence - Green
        base_color = (0, 255, 0)
    elif confidence >= 0.5:
        # Medium confidence - Yellow
        base_color = (0, 255, 255)
    else:
        # Low confidence - Red
        base_color = (0, 0, 255)

    # For special phases, blend with their characteristic color
    if phase_name == "*** CONTACT ***":
        # Contact is red, so keep it red but adjust intensity based on confidence
        return (0, 0, int(255 * min(1.0, confidence + 0.3)))

    return base_color


if __name__ == "__main__":
    # ========================================
    # CONFIGURATION - CHANGE THESE SETTINGS
    # ========================================

    # Choose your video and output
    video_path = "uploads/novakswing.mp4"
    output_path = "results/annotated_novakswing.mp4"

    # Toggle detection method:

    # Option 1: Fixed threshold (original - works well for test_swing.mp4)
    USE_ADAPTIVE = False
    VELOCITY_THRESHOLD = 0.5
    ADAPTIVE_PERCENT = 0.15

    # Option 2: Adaptive threshold (better for different videos)
    # USE_ADAPTIVE = True
    # VELOCITY_THRESHOLD = 0.5  # Ignored when adaptive is True
    # ADAPTIVE_PERCENT = 0.15  # 15% of max velocity

    # Other settings
    CONTACT_ANGLE_MIN = 150  # Try 130 for more relaxed detection

    # ========================================

    print(f"\n🎬 Video: {video_path}")
    print(f"📁 Output: {output_path}")
    print(f"⚙️  Mode: {'Adaptive' if USE_ADAPTIVE else 'Fixed'} velocity threshold\n")

    visualize_swing_phases(
        video_path,
        output_path,
        use_adaptive=USE_ADAPTIVE,
        velocity_threshold=VELOCITY_THRESHOLD,
        adaptive_percent=ADAPTIVE_PERCENT,
        contact_angle_min=CONTACT_ANGLE_MIN
    )

    print("\n✅ Done! You can now play the annotated video.")
