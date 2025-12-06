# Tennis Swing Analysis Worker

AI-powered tennis swing analysis microservice using computer vision and biomechanical analysis. This Flask worker service processes tennis swing videos and returns detailed technical insights including phase detection, engine metrics, tempo analysis, and kinetic chain sequencing.

## Architecture

This is a **microservice worker** designed to be called by the Next.js frontend (ShotVision). It is **not a standalone API**.

**Flow:**
1. User uploads video via Next.js frontend (localhost:3000)
2. Next.js saves video to Backblaze B2 and metadata to MongoDB
3. Next.js calls this Flask worker's `/process` endpoint with signed URL
4. Worker downloads video, processes it, uploads annotated result to B2
5. Worker sends webhook callback to Next.js with analysis results
6. Next.js updates MongoDB with completed analysis

## Features

- **Swing Phase Detection**: Automatically identifies 5 key phases (unit turn, backswing, forward swing, contact, follow through)
- **Engine Metrics**: Measures hip-shoulder separation and rotation angles
- **Tempo Analysis**: Calculates swing timing and rhythm ratios
- **Kinetic Chain Analysis**: Tracks velocity sequencing from hip → shoulder → elbow → wrist
- **Annotated Video Output**: Creates video with overlays showing phases, metrics, and tracking quality
- **Asynchronous Processing**: Uses threading for non-blocking video processing
- **Webhook Callbacks**: Notifies Next.js when processing completes or fails

## Technology Stack

- **Computer Vision**: MediaPipe Pose for body landmark detection
- **Analysis**: Custom biomechanical algorithms for swing analysis
- **API**: Flask REST API with threading for async processing
- **Video Processing**: OpenCV with FFmpeg for H.264 encoding
- **Cloud Storage**: Backblaze B2 via boto3
- **Deployment**: Docker container on Render

## Installation

### Prerequisites

- Python 3.10 or higher
- Docker (for deployment)
- FFmpeg (for video encoding)
- Backblaze B2 account credentials
- Next.js frontend configured with webhook endpoint

### Local Development Setup

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   Create a `.env` file:
   ```bash
   B2_BUCKET_NAME=your-bucket-name
   B2_ENDPOINT=https://s3.us-west-004.backblazeb2.com
   B2_KEY_ID=your-key-id
   B2_APP_KEY=your-app-key
   NEXT_WEBHOOK_URL=http://localhost:3000/api/ai-completion
   AI_SERVICE_SECRET=your-shared-secret
   PORT=5001
   ```

4. **Run the worker**
   ```bash
   python api.py
   ```

The worker will start on `http://localhost:5001`

## API Endpoints

The worker exposes only 3 endpoints:

### GET /health

Health check endpoint for monitoring.

**Request:**
```bash
curl http://localhost:5001/health
```

**Response:**
```json
{
  "status": "healthy",
  "service": "Tennis Swing AI Worker",
  "version": "1.0",
  "b2_configured": true
}
```

### GET /

Simple status check.

**Request:**
```bash
curl http://localhost:5001/
```

**Response:**
```json
{
  "status": "AI Worker Running"
}
```

### POST /process

Main processing endpoint called by Next.js. Starts asynchronous video processing.

**Request:**
```bash
curl -X POST http://localhost:5001/process \
  -H "Content-Type: application/json" \
  -H "x-secret: your_secret_here" \
  -d '{
    "videoId": "test-123",
    "userId": "user-456",
    "videoUrl": "https://signed-url.backblazeb2.com/video.mp4",
    "rawKey": "videos/user-456/test.mp4"
  }'
```

**Parameters:**
- `videoId` (string, required): Unique video identifier from MongoDB
- `userId` (string, required): User ID for organizing uploads
- `videoUrl` (string, required): Signed B2 URL to download video
- `rawKey` (string, required): B2 object key for the raw video

**Headers:**
- `x-secret`: Shared secret for authentication (must match `AI_SERVICE_SECRET`)
- `Content-Type`: application/json

**Response (202 Accepted):**
```json
{
  "success": true,
  "message": "Processing started"
}
```

**Processing Flow:**
1. Returns 202 immediately (non-blocking)
2. Downloads video from B2 to `/tmp/uploads/{videoId}.mp4`
3. Analyzes swing using MediaPipe and biomechanical algorithms
4. Renders annotated video to `/tmp/results/{videoId}_annotated.mp4`
5. Uploads result to B2 at `videos/{userId}/{videoId}_annotated.mp4`
6. Sends webhook POST to `NEXT_WEBHOOK_URL` with analysis results
7. Cleans up local temporary files

**Webhook Payload (Success):**
```json
{
  "videoId": "test-123",
  "annotatedKey": "videos/user-456/test-123_annotated.mp4",
  "status": "completed",
  "rawKey": "videos/user-456/test.mp4",
  "analysis": {
    "phases": { ... },
    "engine": { ... },
    "tempo": { ... },
    "kinetic_chain": { ... },
    "tracking_quality": { ... }
  }
}
```

**Webhook Payload (Failure):**
```json
{
  "videoId": "test-123",
  "status": "failed",
  "error": "Error message here"
}
```

## Environment Variables

Required for production deployment:

```bash
# Backblaze B2 Configuration
B2_BUCKET_NAME=your-bucket-name
B2_ENDPOINT=https://s3.us-west-004.backblazeb2.com
B2_KEY_ID=your-key-id
B2_APP_KEY=your-app-key

# Next.js Integration
NEXT_WEBHOOK_URL=https://your-app.vercel.app/api/ai-completion
AI_SERVICE_SECRET=your-shared-secret

# Server Configuration
PORT=5001  # Or $PORT for Render
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

## Deployment

### Docker Build

The worker uses Docker for consistent FFmpeg and codec support:

```bash
docker build -t tennis-swing-worker .
docker run -p 5001:5001 --env-file .env tennis-swing-worker
```

### Render Deployment

The `render.yaml` configures automatic deployment:

```yaml
services:
  - type: web
    name: tennis-swing-ai-worker
    env: docker
    region: oregon
    healthCheckPath: /health
```

Set environment variables in Render dashboard.

## Testing

### Test Local Worker

```bash
# Check health
curl http://localhost:5001/health

# Test processing (requires B2 signed URL)
curl -X POST http://localhost:5001/process \
  -H "Content-Type: application/json" \
  -H "x-secret: your_secret" \
  -d '{"videoId": "test", "userId": "user", "videoUrl": "https://...", "rawKey": "..."}'
```

### Run Unit Tests

```bash
# Test swing analyzer (runs without video files, but needs uploads/test_swing.mp4 for full coverage)
python tests/test_swing_analyzer.py

# Test integration (requires uploads/ folder with test videos for full coverage)
python tests/test_integration.py
```

**Note:** Both test files will gracefully skip tests if video files are missing. For full test coverage, create an `uploads/` folder with test videos:
- `uploads/test_swing.mp4` (required for full `test_swing_analyzer.py` coverage)
- `uploads/novakswing.mp4` (optional, for `test_integration.py`)
- `uploads/novak_swing.mp4` (optional, for `test_integration.py`)

### Full Pipeline Test

```bash
# Test complete processing pipeline (requires uploads/ folder with test videos)
python test_api_flow.py

# Or test single video (provide any video path)
python test_api_flow.py uploads/your_video.mp4
```

**Note:** When run without arguments, expects the same test videos as `test_integration.py`:
- `uploads/test_swing.mp4`
- `uploads/novakswing.mp4`
- `uploads/novak_swing.mp4`

Tests will skip missing videos gracefully. When testing a single video, you can provide any path.

See [TEST_API_FLOW_README.md](TEST_API_FLOW_README.md) for detailed testing documentation.

## Troubleshooting

### "No pose detected"
- Ensure player is fully visible in frame
- Check video quality and lighting
- Algorithm uses `PRESET_DIFFICULT_VIDEO` configuration for robustness

### "Contact not detected"
- Check that swing has clear acceleration and deceleration
- Ensure elbow extension is visible at contact point
- Kinematic chain mode provides better detection than velocity-only

### "Output video is too small" / Encoding errors
- FFmpeg and codecs are required (included in Docker image)
- For local dev, ensure FFmpeg is installed: `brew install ffmpeg` (macOS)
- Video encoding uses H.264 (avc1) codec

### Worker not responding
- Check if server is running: `curl http://localhost:5001/health`
- Verify port 5001 is not in use: `lsof -i :5001`
- Check logs for errors
- Verify B2 credentials are correct

### Webhook not received by Next.js
- Confirm `NEXT_WEBHOOK_URL` is correct
- Verify `AI_SERVICE_SECRET` matches between services
- Check Next.js logs for incoming webhook requests
- Ensure Next.js is running on localhost:3000 (local) or accessible URL (production)

## Project Structure

```
tennis-cv/
├── api.py                    # Flask worker with /process endpoint
├── swing_analyzer.py         # Biomechanical analysis algorithms
├── video_processor.py        # MediaPipe pose detection
├── visualize_swing.py        # Video annotation and rendering
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker config with FFmpeg
├── render.yaml              # Render deployment config
├── tests/                   # Unit and integration tests
└── /tmp/
    ├── uploads/             # Temporary video downloads
    └── results/             # Temporary annotated outputs
```

## License

[Specify your license here]

---

**Version**: 1.0.0
**Last Updated**: December 2025
**Microservice for**: [ShotVision](https://github.com/integratebpd-org/shotvision)
