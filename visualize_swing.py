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

        # Get current phase
        current_phase = frame_phases.get(frame_number, "Analyzing...")
        timestamp = frame_number / fps

        # Draw semi-transparent background for text
        overlay = frame.copy()
        cv2.rectangle(overlay, (10, 10), (600, 120), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)

        # Draw phase text
        phase_color = _get_phase_color(current_phase)
        cv2.putText(
            frame,
            f"Phase: {current_phase}",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.2,
            phase_color,
            3,
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

        # Draw key phase markers
        key_frames = [
            p.get("frame") for p in phases.values() if p and isinstance(p, dict)
        ]
        if frame_number in key_frames:
            cv2.circle(frame, (width - 50, 50), 20, (0, 255, 255), -1)
            cv2.putText(
                frame,
                "KEY",
                (width - 80, 100),
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
    """Assign phase labels to each frame number"""
    frame_phases = {}

    # Safely get frame numbers for each phase, default to 0 or total_frames if None
    backswing_start = (
        phases.get("backswing_start", {}).get("frame", 0)
        if phases.get("backswing_start")
        else 0
    )
    max_backswing = (
        phases.get("max_backswing", {}).get("frame", 0)
        if phases.get("max_backswing")
        else 0
    )
    forward_start = (
        phases.get("forward_swing_start", {}).get("frame", 0)
        if phases.get("forward_swing_start")
        else 0
    )
    contact = phases.get("contact", {}).get("frame", 0) if phases.get("contact") else 0
    follow_through = (
        phases.get("follow_through", {}).get("frame", total_frames)
        if phases.get("follow_through")
        else total_frames
    )

    for frame_num in range(1, total_frames + 1):
        if backswing_start == 0:
            frame_phases[frame_num] = "Analyzing..."
        elif frame_num < backswing_start:
            frame_phases[frame_num] = "Ready Position"
        elif frame_num < max_backswing:
            frame_phases[frame_num] = "BACKSWING"
        elif frame_num < forward_start:
            frame_phases[frame_num] = "LOADING"
        elif frame_num < contact:
            frame_phases[frame_num] = "FORWARD SWING"
        elif frame_num == contact:
            frame_phases[frame_num] = "*** CONTACT ***"
        elif frame_num < follow_through:
            frame_phases[frame_num] = "FOLLOW THROUGH"
        else:
            frame_phases[frame_num] = "FINISH"

    return frame_phases


def _get_phase_color(phase_name):
    """Return color based on phase"""
    colors = {
        "Ready Position": (200, 200, 200),
        "BACKSWING": (255, 200, 0),
        "LOADING": (255, 150, 0),
        "FORWARD SWING": (0, 255, 0),
        "*** CONTACT ***": (0, 0, 255),
        "FOLLOW THROUGH": (255, 0, 255),
        "FINISH": (100, 100, 255),
    }
    return colors.get(phase_name, (255, 255, 255))


if __name__ == "__main__":
    # ========================================
    # CONFIGURATION - CHANGE THESE SETTINGS
    # ========================================

    # Choose your video and output
    video_path = "uploads/test_swing.mp4"  # Change to "uploads/novak_swing.mp4"
    output_path = "results/annotated_swing.mp4"

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
