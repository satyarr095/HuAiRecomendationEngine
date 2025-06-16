# AI Recommendation Engine Backend

This is the FastAPI backend for the AI Recommendation Engine that provides personalized learning recommendations.

## Setup

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the FastAPI server:**
   ```bash
   python app.py
   ```
   
   Or alternatively:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```

3. **Access the API:**
   - API Base URL: `http://localhost:8000`
   - Interactive API Docs: `http://localhost:8000/docs`
   - Alternative API Docs: `http://localhost:8000/redoc`

## API Endpoints

### POST `/api/recommendations`
Analyze uploaded JSON data and return personalized learning recommendations.

**Request Body:**
```json
{
  "jsonData": { /* your uploaded JSON data */ },
  "userId": "optional-user-id"
}
```

**Response:**
```json
{
  "userId": "user-123",
  "recommendations": [/* array of recommendation items */],
  "skillGaps": [/* array of skill gap analyses */],
  "learningPaths": [/* array of learning paths */],
  "processingTime": 2.5
}
```

### POST `/api/skill-gap-analysis/{user_id}`
Get detailed skill gap analysis for a specific user.

**Response:**
```json
[
  {
    "skill": "Data Structures & Algorithms",
    "currentLevel": 3,
    "targetLevel": 8,
    "priority": "high",
    "recommendedContent": [/* array of recommendations */]
  }
]
```

### GET `/health`
Health check endpoint.

## Development

- The backend currently serves static dummy data
- CORS is configured for React development servers (ports 3000, 5173)
- Processing time is simulated with a 2.5-second delay

## Future Enhancements

- Replace dummy data with actual AI/ML processing
- Add authentication and user management
- Implement real skill analysis algorithms
- Add database persistence 