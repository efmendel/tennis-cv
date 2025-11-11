from utils import (
    calculate_angle,
    calculate_velocity,
    is_wrist_behind_body,
    get_body_center_x
)
import matplotlib.pyplot as plt
import numpy as np
from swing_config import get_config, SwingConfig

class SwingAnalyzerV2:
    def __init__(self, debug_mode=False, config=None):
        """
        Initialize swing analyzer with optional configuration

        Args:
            debug_mode: If True, generates debug plots
            config: SwingConfig object or preset name ('normal', 'slomo', etc.)
                   If None, uses default adaptive config
        """
        self.debug_mode = debug_mode

        # Handle config parameter
        if config is None:
            self.config = get_config('default')
        elif isinstance(config, str):
            self.config = get_config(config)
        elif isinstance(config, SwingConfig):
            self.config = config
        else:
            print(f"⚠️  Invalid config type. Using default.")
            self.config = get_config('default')

        print(f"🎯 Config: {self.config.name}")

    def analyze_swing(self, video_data):
        """
        Improved swing analysis with adaptive thresholds
        """
        frames = video_data['frames']
        fps = video_data['fps']

        # Filter to only frames with pose detected
        valid_frames = [f for f in frames if f['pose_detected']]

        if len(valid_frames) < 10:
            return {
                'error': 'Not enough frames with pose detected',
                'frames_detected': len(valid_frames)
            }

        print(f"Analyzing {len(valid_frames)} valid frames at {fps} FPS...")

        # Calculate metrics for each frame
        frame_metrics = self._calculate_frame_metrics(valid_frames, fps)

        # Adaptive thresholds based on actual data
        velocities = [m['wrist_velocity'] for m in frame_metrics]
        max_velocity = max(velocities)
        avg_velocity = np.mean(velocities)

        # Set adaptive threshold using config percentage
        adaptive_velocity_threshold = max_velocity * self.config.velocity_threshold_percent

        print(f"\n📊 Velocity Analysis:")
        print(f"   Max velocity: {max_velocity:.4f}")
        print(f"   Avg velocity: {avg_velocity:.4f}")
        print(f"   Adaptive threshold: {adaptive_velocity_threshold:.4f} ({self.config.velocity_threshold_percent*100:.0f}% of max)")

        # Detect swing phases with adaptive thresholds
        phases = self._detect_phases_adaptive(frame_metrics, valid_frames, fps, adaptive_velocity_threshold)

        # Debug visualization if enabled
        if self.debug_mode:
            self._plot_metrics(frame_metrics, phases)

        return phases

    def _calculate_frame_metrics(self, frames, fps):
        """Calculate angles and velocities for each frame"""
        metrics = []

        for i, frame in enumerate(frames):
            landmarks = frame['landmarks']

            # Calculate elbow angle (shoulder-elbow-wrist)
            elbow_angle = calculate_angle(
                landmarks['right_shoulder'],
                landmarks['right_elbow'],
                landmarks['right_wrist']
            )

            # Calculate wrist velocity
            wrist_velocity = 0
            if i > 0:
                prev_wrist = frames[i-1]['landmarks']['right_wrist']
                curr_wrist = landmarks['right_wrist']
                time_delta = 1 / fps
                wrist_velocity = calculate_velocity(curr_wrist, prev_wrist, time_delta)

            # Check if wrist is behind body
            wrist_behind = is_wrist_behind_body(
                landmarks['right_wrist'],
                landmarks['left_shoulder'],
                landmarks['right_shoulder']
            )

            # Get body center
            body_center = get_body_center_x(
                landmarks['left_shoulder'],
                landmarks['right_shoulder']
            )

            metrics.append({
                'frame_number': frame['frame_number'],
                'timestamp': frame['timestamp'],
                'elbow_angle': elbow_angle,
                'wrist_velocity': wrist_velocity,
                'wrist_x': landmarks['right_wrist']['x'],
                'wrist_y': landmarks['right_wrist']['y'],
                'wrist_behind_body': wrist_behind,
                'body_center_x': body_center
            })

        return metrics

    def _detect_phases_adaptive(self, metrics, frames, fps, velocity_threshold):
        """
        Improved phase detection using adaptive thresholds and relative metrics
        """
        phases = {
            'backswing_start': None,
            'max_backswing': None,
            'forward_swing_start': None,
            'contact': None,
            'follow_through': None
        }

        # 1. BACKSWING START - wrist goes behind body
        for i, m in enumerate(metrics):
            if m['wrist_behind_body']:
                phases['backswing_start'] = {
                    'frame': m['frame_number'],
                    'timestamp': m['timestamp']
                }
                print(f"✓ Backswing start detected at {m['timestamp']:.2f}s")
                break

        # 2. MAX BACKSWING - furthest back position
        if phases['backswing_start']:
            backswing_frames = [m for m in metrics if m['wrist_behind_body']]
            if backswing_frames:
                max_back = min(backswing_frames, key=lambda x: x['wrist_x'])
                phases['max_backswing'] = {
                    'frame': max_back['frame_number'],
                    'timestamp': max_back['timestamp'],
                    'wrist_x': max_back['wrist_x']
                }
                print(f"✓ Max backswing detected at {max_back['timestamp']:.2f}s")

        # 3. FORWARD SWING START - velocity starts increasing after max backswing
        if phases['max_backswing']:
            max_back_idx = next(i for i, m in enumerate(metrics)
                              if m['frame_number'] == phases['max_backswing']['frame'])

            # Look for velocity exceeding adaptive threshold
            for i in range(max_back_idx, len(metrics)):
                if metrics[i]['wrist_velocity'] > velocity_threshold:
                    phases['forward_swing_start'] = {
                        'frame': metrics[i]['frame_number'],
                        'timestamp': metrics[i]['timestamp'],
                        'velocity': metrics[i]['wrist_velocity']
                    }
                    print(f"✓ Forward swing start detected at {metrics[i]['timestamp']:.2f}s (vel: {metrics[i]['wrist_velocity']:.4f})")
                    break

        # 4. CONTACT POINT - IMPROVED DETECTION
        if phases['forward_swing_start']:
            forward_idx = next(i for i, m in enumerate(metrics)
                             if m['frame_number'] == phases['forward_swing_start']['frame'])

            # Search window - use config setting, scaled with FPS
            window_size = int(self.config.contact_search_window * (fps / 30))
            search_window_end = min(forward_idx + window_size, len(metrics))

            print(f"\n🔍 Searching for contact in window: {window_size} frames")

            # Method 1: Find PEAK VELOCITY with reasonable arm extension
            contact_candidates = []
            for i in range(forward_idx, search_window_end):
                m = metrics[i]
                # Use config angle threshold
                if (m['elbow_angle'] > self.config.contact_angle_min and
                    m['wrist_velocity'] > velocity_threshold and
                    not m['wrist_behind_body']):
                    contact_candidates.append((i, m))

            if contact_candidates:
                # Find frame with maximum velocity
                peak_idx, _ = max(contact_candidates, key=lambda x: x[1]['wrist_velocity'])

                # Adjust forward based on config and FPS
                frames_adjustment = int(self.config.contact_frame_adjustment * (fps / 30))
                adjusted_idx = min(len(metrics) - 1, peak_idx + frames_adjustment)
                adjusted_contact = metrics[adjusted_idx]

                phases['contact'] = {
                    'frame': adjusted_contact['frame_number'],
                    'timestamp': adjusted_contact['timestamp'],
                    'velocity': adjusted_contact['wrist_velocity'],
                    'elbow_angle': adjusted_contact['elbow_angle']
                }
                print(f"✓ Contact detected at {adjusted_contact['timestamp']:.2f}s (vel: {adjusted_contact['wrist_velocity']:.4f}, angle: {adjusted_contact['elbow_angle']:.1f}°)")
            else:
                print("⚠ No contact point found - trying fallback method...")

                # FALLBACK: Just use absolute peak velocity in the window
                search_metrics = metrics[forward_idx:search_window_end]
                if search_metrics:
                    peak = max(enumerate(search_metrics), key=lambda x: x[1]['wrist_velocity'])
                    peak_idx_in_window, _ = peak
                    actual_idx = forward_idx + peak_idx_in_window

                    frames_adjustment = int(self.config.contact_frame_adjustment * (fps / 30))
                    adjusted_idx = min(len(metrics) - 1, actual_idx + frames_adjustment)
                    adjusted_contact = metrics[adjusted_idx]

                    phases['contact'] = {
                        'frame': adjusted_contact['frame_number'],
                        'timestamp': adjusted_contact['timestamp'],
                        'velocity': adjusted_contact['wrist_velocity'],
                        'elbow_angle': adjusted_contact['elbow_angle']
                    }
                    print(f"✓ Contact detected (fallback) at {adjusted_contact['timestamp']:.2f}s")

        # 5. FOLLOW THROUGH - wrist crosses far past body center
        if phases['contact']:
            contact_idx = next(i for i, m in enumerate(metrics)
                             if m['frame_number'] == phases['contact']['frame'])

            for i in range(contact_idx, len(metrics)):
                m = metrics[i]
                # Wrist significantly past body center (use config threshold)
                if m['wrist_x'] > m['body_center_x'] + self.config.follow_through_threshold:
                    phases['follow_through'] = {
                        'frame': m['frame_number'],
                        'timestamp': m['timestamp'],
                        'wrist_x': m['wrist_x']
                    }
                    print(f"✓ Follow through detected at {m['timestamp']:.2f}s")
                    break

        return phases

    def _plot_metrics(self, metrics, phases):
        """
        Create debug visualization showing all metrics over time
        """
        timestamps = [m['timestamp'] for m in metrics]
        velocities = [m['wrist_velocity'] for m in metrics]
        angles = [m['elbow_angle'] for m in metrics]
        wrist_x = [m['wrist_x'] for m in metrics]

        _fig, axes = plt.subplots(3, 1, figsize=(14, 10))

        # Plot 1: Wrist Velocity
        axes[0].plot(timestamps, velocities, 'b-', linewidth=2, label='Wrist Velocity')
        axes[0].set_ylabel('Velocity', fontsize=12)
        axes[0].set_title('Swing Analysis - Wrist Velocity Over Time', fontsize=14, fontweight='bold')
        axes[0].grid(True, alpha=0.3)
        axes[0].legend()

        # Plot 2: Elbow Angle
        axes[1].plot(timestamps, angles, 'g-', linewidth=2, label='Elbow Angle')
        axes[1].axhline(y=150, color='r', linestyle='--', alpha=0.5, label='Old Threshold (150°)')
        axes[1].axhline(y=120, color='orange', linestyle='--', alpha=0.5, label='New Threshold (120°)')
        axes[1].set_ylabel('Angle (degrees)', fontsize=12)
        axes[1].set_title('Elbow Extension', fontsize=14, fontweight='bold')
        axes[1].grid(True, alpha=0.3)
        axes[1].legend()

        # Plot 3: Wrist X Position
        axes[2].plot(timestamps, wrist_x, 'purple', linewidth=2, label='Wrist X Position')
        body_centers = [m['body_center_x'] for m in metrics]
        axes[2].plot(timestamps, body_centers, 'r--', alpha=0.5, label='Body Center')
        axes[2].set_ylabel('X Position', fontsize=12)
        axes[2].set_xlabel('Time (seconds)', fontsize=12)
        axes[2].set_title('Wrist Horizontal Position', fontsize=14, fontweight='bold')
        axes[2].grid(True, alpha=0.3)
        axes[2].legend()

        # Mark phases on all plots
        colors = {
            'backswing_start': 'cyan',
            'max_backswing': 'blue',
            'forward_swing_start': 'green',
            'contact': 'red',
            'follow_through': 'orange'
        }

        for phase_name, phase_data in phases.items():
            if phase_data and isinstance(phase_data, dict):
                timestamp = phase_data['timestamp']
                color = colors.get(phase_name, 'gray')

                for ax in axes:
                    ax.axvline(x=timestamp, color=color, linestyle=':', linewidth=2, alpha=0.7)

                # Add label to top plot
                axes[0].text(timestamp, max(velocities) * 0.9,
                           phase_name.replace('_', '\n'),
                           rotation=0, ha='center', fontsize=8,
                           bbox=dict(boxstyle='round', facecolor=color, alpha=0.3))

        plt.tight_layout()
        plt.savefig('/Users/eddiemendel/Documents/Random-Coding-Projects/tennis-cv/results/debug_analysis.png', dpi=150)
        print("\n📊 Debug plot saved to: results/debug_analysis.png")
        plt.show()


# Test the improved analyzer
if __name__ == "__main__":
    from video_processor import VideoProcessor

    print("Processing video...")
    processor = VideoProcessor()
    video_data = processor.process_video("uploads/test_swing.mp4")

    print("\n" + "="*60)
    print("ANALYZING SWING PHASES (V2 - Configurable)")
    print("="*60)

    # Toggle between presets here:
    # 'normal' - Regular speed videos (30-60 FPS)
    # 'slomo' - Slow motion (120-240 FPS)
    # 'ultra_slomo' - Ultra slow motion (480+ FPS)
    # 'aggressive' - Fast aggressive swings
    # 'slice' - Slice shots
    # 'default' - Balanced settings

    PRESET = 'slomo'  # <-- CHANGE THIS TO SWITCH PRESETS

    analyzer = SwingAnalyzerV2(debug_mode=True, config=PRESET)
    phases = analyzer.analyze_swing(video_data)

    print("\n" + "="*60)
    print("SWING ANALYSIS RESULTS")
    print("="*60)
    for phase_name, phase_data in phases.items():
        if phase_data and isinstance(phase_data, dict):
            print(f"\n{phase_name.upper().replace('_', ' ')}:")
            for key, value in phase_data.items():
                if key == 'timestamp':
                    print(f"  {key}: {value:.3f}s")
                elif isinstance(value, float):
                    print(f"  {key}: {value:.3f}")
                else:
                    print(f"  {key}: {value}")
        else:
            print(f"\n{phase_name.upper().replace('_', ' ')}: Not detected")
