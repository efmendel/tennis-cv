# Tennis Swing Analysis

Analyzes tennis swings using MediaPipe pose detection and automatically identifies swing phases.

## Quick Start

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Put your video in uploads/
# uploads/my_swing.mp4

# 3. Run the analysis
python visualize_swing.py

# 4. Check output
open results/annotated_swing.mp4
```

## Configuration

Edit the top of [visualize_swing.py](visualize_swing.py):

```python
video_path = "uploads/my_swing.mp4"  # Your video
output_path = "results/annotated_swing.mp4"

USE_ADAPTIVE = False        # Keep False for normal videos
VELOCITY_THRESHOLD = 0.5    # Lower = detects slower swings
CONTACT_ANGLE_MIN = 150     # Lower = detects bent-arm swings
```

## What It Detects

1. **Backswing Start** - Wrist goes behind body
2. **Max Backswing** - Furthest back position
3. **Forward Swing** - Wrist accelerates forward
4. **Contact** - Peak velocity with extended arm
5. **Follow Through** - Wrist crosses past body

## Files

**Use these:**
- `visualize_swing.py` - Main script (run this)
- `video_processor.py` - Extracts pose from video (auto-runs)
- `swing_analyzer.py` - Detects swing phases (auto-runs)
- `utils.py` - Helper functions (auto-runs)
- `test_mediapipe.py` - Test if skeleton detection works (optional)

**Ignore these:**
- `swing_analyzer_v2.py` - Old experiment
- `visualize_swing_v2.py` - Old experiment
- `swing_config.py` - Old experiment

## Troubleshooting

**No skeleton showing?**
```bash
python test_mediapipe.py  # Press 'q' to quit
```
Make sure person is fully visible in frame.

**Contact not detected?**
- Lower `CONTACT_ANGLE_MIN` to 130 or 120
- Video might be too long (trim to 2-3 seconds)

**"ModuleNotFoundError"?**
```bash
source venv/bin/activate
```

## How It Works

1. `visualize_swing.py` calls `video_processor.py`
2. MediaPipe extracts pose landmarks from each frame
3. `swing_analyzer.py` calculates velocities and angles
4. Swing phases detected based on wrist position and velocity
5. Annotated video created with skeleton overlay and labels

That's it!
