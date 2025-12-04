# Test API Flow - Complete Pipeline Testing

This script tests the complete tennis swing analysis pipeline from video input to annotated output.

## What It Tests

1. **Video Processing** - Loads video and extracts pose data with VideoProcessor
2. **Swing Analysis** - Analyzes swing phases with SwingAnalyzer using kinematic chain mode
3. **Results Validation** - Verifies SwingAnalysisResults structure and completeness
4. **Visualization** - Creates annotated video with overlays
5. **JSON Output** - Generates JSON export of all analysis data

## Usage

### Test All Videos
```bash
python test_api_flow.py
```

This will test all three videos in sequence:
- `uploads/test_swing.mp4` (good quality)
- `uploads/novakswing.mp4` (low resolution)
- `uploads/novak_swing.mp4` (motion blur/slow-mo)

### Test Single Video
```bash
python test_api_flow.py path/to/your/video.mp4
```

## Output

The script creates a `test_results/` directory containing:

### For each video:
- **Annotated video**: `annotated_<original_filename>.mp4`
  - Phase labels with color coding
  - Engine metrics during backswing
  - Tempo metrics at finish
  - Tracking quality indicators

- **JSON file**: `analysis_<original_filename>.json`
  - Complete analysis results
  - All detected phases
  - Engine metrics (hip-shoulder separation, rotations)
  - Tempo metrics (durations, rhythm)
  - Kinetic chain data (velocity sequencing)
  - Tracking quality

## What Gets Validated

### Structure Validation
- ✅ All 5 phases present (unit_turn, backswing, forward_swing, contact, follow_through)
- ✅ Each phase has `detected` and `confidence` fields
- ✅ Engine metrics present (hip_shoulder_separation, max_shoulder_rotation, max_hip_rotation)
- ✅ Tempo metrics present (backswing_duration, forward_swing_duration, swing_rhythm_ratio)
- ✅ Kinetic chain metrics present (peak_velocity_sequence, chain_lag, confidence)

### Content Validation
- ⚠️ Warns if phases not detected
- ⚠️ Warns if optional fields missing
- ✅ Verifies confidence values in range [0.0, 1.0]
- ✅ Checks for proper data types

## Example Output

```
======================================================================
STATISTICS FOR: uploads/test_swing.mp4
======================================================================

📊 Overall Quality:
   Phases Detected: 4/5
   Overall Confidence: 85.50%

🎯 Phase Detection:
   ✅ unit_turn       : frame   45, time 1.50s, conf 88.00%
   ✅ backswing       : frame   67, time 2.23s, conf 92.00%
   ✅ forward_swing   : frame   89, time 2.97s, conf 85.00%
   ✅ contact         : frame  102, time 3.40s, conf 95.00%
   ❌ follow_through  : insufficient_wrist_travel

💪 Engine Metrics:
   Hip-Shoulder Separation: 35.2° (frame 67)
   Max Shoulder Rotation: -42.1° (frame 67)
   Max Hip Rotation: -55.3° (frame 65)

⏱️  Tempo Metrics:
   Backswing Duration: 1.200s
   Forward Swing Duration: 0.300s
   Swing Rhythm Ratio: 4.00

⛓️  Kinetic Chain:
   Hip      peak: frame   65, time 2.17s, vel 245.3
   Shoulder peak: frame   67, time 2.23s, vel 312.1
   Elbow    peak: frame   99, time 3.30s, vel 425.7
   Wrist    peak: frame  102, time 3.40s, vel 612.4

   Lag Times:
      Hip → Shoulder: 0.060s
      Shoulder → Elbow: 1.070s
      Elbow → Wrist: 0.100s

   Sequencing Confidence: 92.00%

📹 Tracking Quality:
   Detection Rate: 95.00%
   High Confidence Rate: 87.00%
   Average Confidence: 0.82
```

## Exit Codes

- `0` - All tests passed
- `1` - One or more tests failed

## Configuration

The test uses the following analyzer configuration:
- **Kinematic Chain Mode**: Enabled
- **Contact Detection**: `kinematic_chain` method
- **Adaptive Velocity**: Enabled (15% of max)
- **Contact Angle Min**: 120°
- **Pose Config**: `PRESET_DIFFICULT_VIDEO` (for challenging videos)

## What API Will Return

The JSON output exactly matches what the Flask API will return in the `/api/analyze` endpoint's `analysis` field.

Example API response structure:
```json
{
  "video_id": "550e8400-e29b-41d4-a716-446655440000",
  "video_url": "/api/video/550e8400-e29b-41d4-a716-446655440000",
  "download_url": "/api/download/550e8400-e29b-41d4-a716-446655440000",
  "analysis": {
    "phases": { ... },
    "engine": { ... },
    "tempo": { ... },
    "kinetic_chain": { ... },
    "video_quality": null,
    "tracking_quality": { ... }
  },
  "expires_at": "2025-12-04T12:00:00"
}
```

## Troubleshooting

### "Video not found"
- Ensure the video exists at the specified path
- Default test videos should be in `uploads/` directory

### "Validation failed"
- Check the printed validation report for specific issues
- Most common: structure issues in SwingAnalysisResults

### "Error processing video"
- Check video file is not corrupted
- Ensure video format is supported (mp4, mov, avi, mkv, webm)
- Check MediaPipe is installed: `pip install mediapipe`

### "ImportError"
- Install required dependencies:
  ```bash
  pip install opencv-python mediapipe numpy flask flask-cors
  ```

## Next Steps

After testing locally with this script:

1. **Start the API server**:
   ```bash
   python api.py
   ```

2. **Test the API endpoint**:
   ```bash
   curl -X POST -F "video=@uploads/test_swing.mp4" http://localhost:5000/api/analyze
   ```

3. **Access the annotated video**:
   - Browser: `http://localhost:5000/api/video/<video_id>`
   - Download: `http://localhost:5000/api/download/<video_id>`

## See Also

- [api.py](api.py) - Flask REST API
- [analysis_results.py](analysis_results.py) - SwingAnalysisResults structure
- [visualize_swing.py](visualize_swing.py) - Visualization with overlays
- [swing_analyzer.py](swing_analyzer.py) - Core analysis logic
