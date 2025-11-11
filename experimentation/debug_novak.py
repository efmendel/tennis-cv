"""Debug script to see what's happening with Novak video"""
from video_processor import VideoProcessor
from swing_analyzer import SwingAnalyzer
from utils import calculate_angle, calculate_velocity, is_wrist_behind_body, get_body_center_x

processor = VideoProcessor()
video_data = processor.process_video("uploads/novak_swing.mp4")

frames = video_data['frames']
fps = video_data['fps']
valid_frames = [f for f in frames if f['pose_detected']]

print(f"Total frames: {len(valid_frames)}")
print(f"FPS: {fps}")

# Calculate metrics manually
frame_metrics = []
for i, frame in enumerate(valid_frames):
    landmarks = frame['landmarks']

    elbow_angle = calculate_angle(
        landmarks['right_shoulder'],
        landmarks['right_elbow'],
        landmarks['right_wrist']
    )

    wrist_velocity = 0
    if i > 0:
        prev_wrist = valid_frames[i-1]['landmarks']['right_wrist']
        curr_wrist = landmarks['right_wrist']
        time_delta = 1 / fps
        wrist_velocity = calculate_velocity(curr_wrist, prev_wrist, time_delta)

    wrist_behind = is_wrist_behind_body(
        landmarks['right_wrist'],
        landmarks['left_shoulder'],
        landmarks['right_shoulder']
    )

    frame_metrics.append({
        'frame_number': frame['frame_number'],
        'timestamp': frame['timestamp'],
        'elbow_angle': elbow_angle,
        'wrist_velocity': wrist_velocity,
        'wrist_behind_body': wrist_behind,
    })

# Find max backswing
backswing_frames = [m for m in frame_metrics if m['wrist_behind_body']]
max_back = min(backswing_frames, key=lambda x: frame_metrics[frame_metrics.index(x)]['frame_number'])
max_back_idx = next(i for i, m in enumerate(frame_metrics) if m['frame_number'] == max_back['frame_number'])

print(f"\nMax backswing at frame {max_back['frame_number']} ({max_back['timestamp']:.2f}s)")

# Find forward swing start
velocities = [m['wrist_velocity'] for m in frame_metrics]
max_velocity = max(velocities)
adaptive_threshold = max_velocity * 0.15

print(f"Max velocity: {max_velocity:.4f}")
print(f"Adaptive threshold (15%): {adaptive_threshold:.4f}")

forward_idx = None
for i in range(max_back_idx, len(frame_metrics)):
    if frame_metrics[i]['wrist_velocity'] > adaptive_threshold:
        forward_idx = i
        print(f"Forward swing at frame {frame_metrics[i]['frame_number']} ({frame_metrics[i]['timestamp']:.2f}s)")
        break

# Look at contact detection window
if forward_idx:
    search_window_end = min(forward_idx + 40, len(frame_metrics))
    print(f"\n🔍 Contact search window: frames {forward_idx} to {search_window_end}")
    print(f"   (Frame numbers {frame_metrics[forward_idx]['frame_number']} to {frame_metrics[min(search_window_end-1, len(frame_metrics)-1)]['frame_number']})")

    print("\n📊 Frames in search window:")
    print(f"{'Frame':<8} {'Time':<8} {'Velocity':<12} {'Angle':<10} {'Behind Body':<12} {'Passes Checks'}")
    print("-" * 80)

    for i in range(forward_idx, search_window_end):
        m = frame_metrics[i]

        # Check all conditions
        angle_ok = m['elbow_angle'] > 120
        velocity_ok = m['wrist_velocity'] > adaptive_threshold
        position_ok = not m['wrist_behind_body']
        all_ok = angle_ok and velocity_ok and position_ok

        marker = "✓" if all_ok else " "

        print(f"{m['frame_number']:<8} {m['timestamp']:<8.2f} {m['wrist_velocity']:<12.4f} {m['elbow_angle']:<10.1f} {str(m['wrist_behind_body']):<12} {marker}")

    # Find candidates
    contact_candidates = []
    for i in range(forward_idx, search_window_end):
        m = frame_metrics[i]
        if (m['elbow_angle'] > 120 and
            m['wrist_velocity'] > adaptive_threshold and
            not m['wrist_behind_body']):
            contact_candidates.append(m)

    print(f"\n✅ Found {len(contact_candidates)} contact candidates")

    if contact_candidates:
        best = max(contact_candidates, key=lambda x: x['wrist_velocity'])
        print(f"   Best candidate: Frame {best['frame_number']} at {best['timestamp']:.2f}s")
        print(f"   Velocity: {best['wrist_velocity']:.4f}")
        print(f"   Angle: {best['elbow_angle']:.1f}°")
else:
    print("\n❌ No forward swing detected!")
