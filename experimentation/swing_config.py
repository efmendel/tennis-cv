"""
Configuration presets for different video types
"""

class SwingConfig:
    """Base configuration for swing analysis"""
    def __init__(self):
        # Velocity threshold (as percentage of max velocity)
        self.velocity_threshold_percent = 0.15

        # Minimum elbow angle at contact (degrees)
        self.contact_angle_min = 120

        # Follow-through detection threshold (distance past body center)
        self.follow_through_threshold = 0.10

        # Contact point frame adjustment (multiplied by fps/30)
        self.contact_frame_adjustment = 3

        # Search window size after forward swing (frames at 30fps)
        self.contact_search_window = 60

        # Name for display
        self.name = "Default"


class NormalSpeedConfig(SwingConfig):
    """Optimized for regular speed videos (30-60 FPS)"""
    def __init__(self):
        super().__init__()
        self.velocity_threshold_percent = 0.20  # Higher threshold for normal speed
        self.contact_angle_min = 130  # Stricter arm extension
        self.follow_through_threshold = 0.15  # Further past body
        self.contact_frame_adjustment = 3
        self.contact_search_window = 45  # Shorter window
        self.name = "Normal Speed"


class SlowMotionConfig(SwingConfig):
    """Optimized for slow-motion videos (120-240 FPS)"""
    def __init__(self):
        super().__init__()
        self.velocity_threshold_percent = 0.12  # Lower threshold for slow-mo
        self.contact_angle_min = 115  # More relaxed arm extension
        self.follow_through_threshold = 0.08  # Closer to body center
        self.contact_frame_adjustment = 4
        self.contact_search_window = 80  # Longer window
        self.name = "Slow Motion"


class UltraSlowMotionConfig(SwingConfig):
    """Optimized for ultra slow-motion videos (480+ FPS)"""
    def __init__(self):
        super().__init__()
        self.velocity_threshold_percent = 0.08  # Very low threshold
        self.contact_angle_min = 110  # Very relaxed
        self.follow_through_threshold = 0.06
        self.contact_frame_adjustment = 5
        self.contact_search_window = 120  # Much longer window
        self.name = "Ultra Slow Motion"


class AggressiveSwingConfig(SwingConfig):
    """For fast, aggressive swings (Djokovic, Nadal style)"""
    def __init__(self):
        super().__init__()
        self.velocity_threshold_percent = 0.18
        self.contact_angle_min = 125
        self.follow_through_threshold = 0.12
        self.contact_frame_adjustment = 3
        self.contact_search_window = 50
        self.name = "Aggressive Swing"


class SliceSwingConfig(SwingConfig):
    """For slice shots (less velocity, different arm angle)"""
    def __init__(self):
        super().__init__()
        self.velocity_threshold_percent = 0.10  # Lower velocity
        self.contact_angle_min = 100  # Less extension
        self.follow_through_threshold = 0.08
        self.contact_frame_adjustment = 2
        self.contact_search_window = 70
        self.name = "Slice Shot"


# Preset dictionary for easy access
PRESETS = {
    'normal': NormalSpeedConfig(),
    'slomo': SlowMotionConfig(),
    'ultra_slomo': UltraSlowMotionConfig(),
    'aggressive': AggressiveSwingConfig(),
    'slice': SliceSwingConfig(),
    'default': SwingConfig()
}


def get_config(preset_name='default'):
    """
    Get configuration by preset name

    Args:
        preset_name: One of 'normal', 'slomo', 'ultra_slomo', 'aggressive', 'slice', 'default'

    Returns:
        SwingConfig object
    """
    config = PRESETS.get(preset_name.lower())
    if config is None:
        print(f"⚠️  Unknown preset '{preset_name}'. Using default config.")
        config = PRESETS['default']
    else:
        print(f"✓ Using preset: {config.name}")
    return config


def print_all_presets():
    """Print all available presets and their settings"""
    print("\n" + "="*70)
    print("AVAILABLE PRESETS")
    print("="*70)

    for key, config in PRESETS.items():
        print(f"\n'{key}' - {config.name}:")
        print(f"  Velocity threshold: {config.velocity_threshold_percent*100:.0f}% of max")
        print(f"  Min elbow angle: {config.contact_angle_min}°")
        print(f"  Follow-through threshold: {config.follow_through_threshold}")
        print(f"  Contact adjustment: {config.contact_frame_adjustment} frames")
        print(f"  Search window: {config.contact_search_window} frames")

    print("\n" + "="*70)


if __name__ == "__main__":
    print_all_presets()
