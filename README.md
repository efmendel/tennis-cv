# Tennis Swing Analysis API

AI-powered tennis swing analysis using computer vision and biomechanical analysis. Upload a video of your tennis swing and get detailed insights into your technique, including phase detection, engine metrics, tempo analysis, and kinetic chain sequencing.

This Python model is a part of the ShotVision application, which has these 2 parts

1.  **Next.js Application** (Frontend & Backend API): Contained in [ShotVision](https://github.com/bxlyy/shotvision).
2.  **Python Model API**: Contained in this repository.

For the full application pipeline to work, both of these repositories need to be hosted. They can be hosted locally.

This GitHub has 2 branches:

- **`main`**: Use this branch if you are testing on a **macOS** machine.
- **`locally-working-commit`**: Use this branch if you are testing on a **Windows** machine.

Each branch contains a slightly different version of the model optimized for the specific operating system, as they do not work interchangeably on different operating systems. Please use the branch corresponding with your OS.

### Steps

1. **Create virtual environment** (if not already created)

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Create required directories**

   ```bash
   mkdir -p uploads results test_results
   ```

4. **Create `.env`**

   Next, you must have a necessary `.env` file. Create a `.env` file in the root directory. Add the variables contained in this document: [.env variables](https://docs.google.com/document/d/1EEhCrxg5U8kV-6IXnu2_qylEWbUcVoZ1nh65zVFH-VE/edit?usp=sharing).

## Quick Start

### Run the API Server

```bash
python api.py
```

The API will start on `http://localhost:5001`

### Test with Sample Video

```bash
# Upload and analyze a video
curl -X POST http://localhost:5001/api/analyze \
  -F "video=@uploads/test_swing.mp4"

# Response will include video_id for downloading results
```

### Test Complete Pipeline

```bash
# Test all functionality with local test script
python test_api_flow.py

# Or test single video
python test_api_flow.py uploads/your_video.mp4
```

## API Documentation

Base URL: `http://localhost:5001`

### POST /api/analyze

Upload and analyze a tennis swing video.

**Request:**

```bash
curl -X POST http://localhost:5001/api/analyze \
  -F "video=@my_swing.mp4" \
  -F "kinematic_chain_mode=true" \
  -F "contact_detection_method=kinematic_chain"
```

**Parameters:**

- `video` (file, required): Video file (mp4, mov, avi, mkv, webm)
- `kinematic_chain_mode` (bool): Use kinematic chain analysis (default: true)
- `contact_detection_method` (string): 'velocity_peak', 'kinematic_chain', or 'hybrid' (default: 'kinematic_chain')
- `use_adaptive` (bool): Use adaptive velocity threshold (default: true)
- `adaptive_percent` (float): Percentage of max velocity (default: 0.15)
- `contact_angle_min` (int): Minimum elbow angle at contact (default: 120)

**Response (200 OK):**

```json
{
  "video_id": "550e8400-e29b-41d4-a716-446655440000",
  "video_url": "/api/video/550e8400-e29b-41d4-a716-446655440000",
  "download_url": "/api/download/550e8400-e29b-41d4-a716-446655440000",
  "expires_at": "2025-12-04T12:00:00",
  "analysis": {
    "phases": {
      "unit_turn": {...},
      "backswing": {...},
      "forward_swing": {...},
      "contact": {...},
      "follow_through": {...}
    },
    "engine": {
      "hip_shoulder_separation": {...},
      "max_shoulder_rotation": {...},
      "max_hip_rotation": {...}
    },
    "tempo": {
      "backswing_duration": 1.2,
      "forward_swing_duration": 0.3,
      "swing_rhythm_ratio": 4.0
    },
    "kinetic_chain": {
      "peak_velocity_sequence": {...},
      "chain_lag": {...},
      "confidence": 0.92
    },
    "tracking_quality": {...}
  }
}
```

### GET /api/video/{video_id}

Stream the annotated video for browser playback.

**Request:**

```bash
curl http://localhost:5001/api/video/550e8400-e29b-41d4-a716-446655440000
```

### GET /api/download/{video_id}

Download the annotated video file.

**Request:**

```bash
curl -O http://localhost:5001/api/download/550e8400-e29b-41d4-a716-446655440000
```

### GET /api/health

Health check endpoint.

**Request:**

```bash
curl http://localhost:5001/api/health
```

**Response:**

```json
{
  "status": "healthy",
  "cached_videos": 3,
  "config": {
    "upload_folder": "uploads",
    "results_folder": "results",
    "video_expiry_hours": 1,
    "max_video_size_mb": 100,
    "allowed_formats": ["mp4", "mov", "avi", "mkv", "webm"]
  }
}
```

See [full API documentation below](#full-api-reference) for all endpoints.

## Configuration

Environment variables for customization:

```bash
# Upload directory (default: uploads)
export UPLOAD_FOLDER=uploads

# Results directory (default: results)
export RESULTS_FOLDER=results

# Video expiry time in hours (default: 1)
export VIDEO_EXPIRY_HOURS=1

# Max video size in MB (default: 100)
export MAX_VIDEO_SIZE_MB=100
```

## Analysis Metrics Explained

### Phases

- **Unit Turn**: Initial shoulder rotation to prepare for backswing
- **Backswing**: Maximum loading position with shoulder coil
- **Forward Swing**: Start of acceleration toward ball
- **Contact**: Ball strike point (peak wrist velocity + arm extension)
- **Follow Through**: Deceleration and finish position

### Engine Metrics

- **Hip-Shoulder Separation**: Angle difference between hips and shoulders (power generation)
- **Max Shoulder Rotation**: Peak shoulder turn during backswing
- **Max Hip Rotation**: Peak hip rotation during loading phase

### Tempo Metrics

- **Backswing Duration**: Time from unit turn to forward swing start
- **Forward Swing Duration**: Time from forward swing start to contact
- **Swing Rhythm Ratio**: Ratio of backswing to forward swing duration

### Kinetic Chain

- **Peak Velocity Sequence**: Timing of peak velocities (should be hip → shoulder → elbow → wrist)
- **Chain Lag**: Time delays between segment peak velocities
- **Confidence**: How well the kinetic chain follows proper sequencing

## Testing

### Run Unit Tests

```bash
# Test swing analyzer
python tests/test_swing_analyzer.py

# Test integration
python tests/test_integration.py
```

### Run Full Pipeline Test

```bash
# Tests all videos with complete validation
python test_api_flow.py
```

See [TEST_API_FLOW_README.md](TEST_API_FLOW_README.md) for detailed testing documentation.

## Troubleshooting

### "No pose detected"

- Ensure player is fully visible in frame
- Check video quality and lighting
- Try using `PRESET_DIFFICULT_VIDEO` configuration

### "Contact not detected"

- Adjust `contact_angle_min` parameter (lower for bent arm shots)
- Try `contact_detection_method=hybrid` for better detection
- Ensure swing has clear acceleration and contact point

### "File too large"

- Default max size is 100MB
- Increase with `MAX_VIDEO_SIZE_MB` environment variable
- Or compress video before uploading

### API not responding

- Check if server is running: `curl http://localhost:5001/api/health`
- Verify port 5001 is not in use
- Check logs for errors

## Full API Reference

Complete documentation of all API endpoints with detailed request/response examples.

### Endpoints

1. **POST /api/analyze** - Upload and analyze video
2. **GET /api/video/{video_id}** - Stream annotated video
3. **GET /api/download/{video_id}** - Download annotated video
4. **GET /api/status/{video_id}** - Get processing status
5. **GET /api/analysis/{video_id}** - Get analysis results only
6. **GET /api/health** - Health check

For complete endpoint documentation with all parameters and response schemas, see the API Documentation section above.

## License

[Specify your license here]

---

**Version**: 1.0.0
**Last Updated**: December 2025
