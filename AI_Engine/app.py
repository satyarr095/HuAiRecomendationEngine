# source ai_env/bin/activate && uvicorn app:app --host 0.0.0.0 --port 8000 --reload
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import time
import asyncio

# Import our AI recommendation engines
from ai_recommendation_engine import process_any_json
from performance_optimized_engine import process_high_volume_requests

# Choose engine based on load (you can switch this for production)
USE_HIGH_VOLUME_ENGINE = True  # Set to True for production/high-volume usage

app = FastAPI(title="AI Recommendation Engine",
              description="AI-powered learning recommendations API")

# Add CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000",
                   "http://127.0.0.1:5173"],  # React dev server ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response


class RecommendationItem(BaseModel):
    id: str
    title: str
    type: str  # 'course' | 'video' | 'article' | 'quiz'
    description: str
    reason: str
    difficulty: str  # 'beginner' | 'intermediate' | 'advanced'
    duration: str
    skills: List[str]
    rating: float
    thumbnail: Optional[str] = None


class SkillGap(BaseModel):
    skill: str
    currentLevel: int
    targetLevel: int
    priority: str  # 'high' | 'medium' | 'low'
    recommendedContent: List[RecommendationItem]


class LearningPath(BaseModel):
    id: str
    title: str
    description: str
    totalDuration: str
    steps: List[RecommendationItem]
    skillsGained: List[str]


class AIResponse(BaseModel):
    userId: str
    recommendations: List[RecommendationItem]
    skillGaps: List[SkillGap]
    learningPaths: List[LearningPath]
    processingTime: float


class AnalysisRequest(BaseModel):
    jsonData: Dict[str, Any]
    userId: Optional[str] = None

# Static dummy data - same as frontend but now in backend


def generate_dummy_recommendations() -> List[RecommendationItem]:
    return [
        RecommendationItem(
            id="rec-001",
            title="Advanced JavaScript Concepts",
            type="course",
            description="Master closures, prototypes, async/await, and modern ES6+ features",
            reason="Recommended based on low performance in JavaScript fundamentals",
            difficulty="intermediate",
            duration="4 hours",
            skills=["JavaScript", "ES6+", "Async Programming"],
            rating=4.8,
            thumbnail="/api/placeholder/300/200"
        ),
        RecommendationItem(
            id="rec-002",
            title="React Hooks Deep Dive",
            type="video",
            description="Complete guide to React Hooks including custom hooks and best practices",
            reason="Based on your interest in React development",
            difficulty="intermediate",
            duration="2.5 hours",
            skills=["React", "Hooks", "Frontend Development"],
            rating=4.9,
            thumbnail="/api/placeholder/300/200"
        ),
        RecommendationItem(
            id="rec-003",
            title="Database Design Principles",
            type="article",
            description="Learn normalization, indexing, and optimization techniques",
            reason="Skill gap identified in database management",
            difficulty="beginner",
            duration="45 minutes",
            skills=["Database Design", "SQL", "Data Modeling"],
            rating=4.6,
            thumbnail="/api/placeholder/300/200"
        ),
        RecommendationItem(
            id="rec-004",
            title="API Security Best Practices Quiz",
            type="quiz",
            description="Test your knowledge of REST API security and authentication",
            reason="Popular among peers with similar learning paths",
            difficulty="intermediate",
            duration="30 minutes",
            skills=["API Security", "Authentication", "Web Security"],
            rating=4.7,
            thumbnail="/api/placeholder/300/200"
        ),
        RecommendationItem(
            id="rec-005",
            title="TypeScript for JavaScript Developers",
            type="course",
            description="Transition from JavaScript to TypeScript with practical examples",
            reason="Next logical step in your learning progression",
            difficulty="intermediate",
            duration="3 hours",
            skills=["TypeScript", "Type Safety", "JavaScript"],
            rating=4.8,
            thumbnail="/api/placeholder/300/200"
        )
    ]


def generate_dummy_skill_gaps() -> List[SkillGap]:
    return [
        SkillGap(
            skill="Data Structures & Algorithms",
            currentLevel=3,
            targetLevel=8,
            priority="high",
            recommendedContent=[
                RecommendationItem(
                    id="sg-001",
                    title="Data Structures Masterclass",
                    type="course",
                    description="Complete guide to arrays, linked lists, trees, and graphs",
                    reason="Essential for closing your skill gap in algorithms",
                    difficulty="intermediate",
                    duration="6 hours",
                    skills=["Data Structures",
                            "Algorithms", "Problem Solving"],
                    rating=4.9
                )
            ]
        ),
        SkillGap(
            skill="System Design",
            currentLevel=2,
            targetLevel=7,
            priority="high",
            recommendedContent=[
                RecommendationItem(
                    id="sg-002",
                    title="System Design Interview Prep",
                    type="course",
                    description="Learn to design scalable systems and architectures",
                    reason="Critical skill gap for senior developer roles",
                    difficulty="advanced",
                    duration="8 hours",
                    skills=["System Design", "Architecture", "Scalability"],
                    rating=4.8
                )
            ]
        ),
        SkillGap(
            skill="DevOps & CI/CD",
            currentLevel=4,
            targetLevel=7,
            priority="medium",
            recommendedContent=[
                RecommendationItem(
                    id="sg-003",
                    title="Docker & Kubernetes Fundamentals",
                    type="course",
                    description="Containerization and orchestration for modern applications",
                    reason="Enhance your deployment and infrastructure skills",
                    difficulty="intermediate",
                    duration="5 hours",
                    skills=["Docker", "Kubernetes", "DevOps"],
                    rating=4.7
                )
            ]
        )
    ]


def generate_dummy_learning_paths() -> List[LearningPath]:
    return [
        LearningPath(
            id="path-001",
            title="Full-Stack Developer Mastery",
            description="Complete learning path to become a proficient full-stack developer",
            totalDuration="15 hours",
            skillsGained=["React", "Node.js",
                          "Database Design", "API Development"],
            steps=[
                RecommendationItem(
                    id="step-001",
                    title="React Fundamentals",
                    type="course",
                    description="Build modern user interfaces with React",
                    reason="Foundation for frontend development",
                    difficulty="beginner",
                    duration="4 hours",
                    skills=["React", "JavaScript", "Frontend"],
                    rating=4.8
                ),
                RecommendationItem(
                    id="step-002",
                    title="Node.js Backend Development",
                    type="course",
                    description="Create robust server-side applications",
                    reason="Essential for full-stack development",
                    difficulty="intermediate",
                    duration="5 hours",
                    skills=["Node.js", "Express", "Backend"],
                    rating=4.7
                ),
                RecommendationItem(
                    id="step-003",
                    title="Database Integration",
                    type="course",
                    description="Connect your applications to databases",
                    reason="Complete your full-stack knowledge",
                    difficulty="intermediate",
                    duration="3 hours",
                    skills=["Database", "SQL", "Integration"],
                    rating=4.6
                )
            ]
        )
    ]

# API Routes


@app.get("/")
async def root():
    return {"message": "AI Recommendation Engine API", "status": "running"}


@app.post("/api/recommendations")
async def get_recommendations(request: AnalysisRequest):
    """
    Analyze uploaded JSON data and return personalized learning recommendations using AI
    High-volume optimized version with caching and minimal external dependencies
    """
    try:
        start_time = time.time()
        
        # Choose engine based on configuration
        if USE_HIGH_VOLUME_ENGINE:
            ai_response = await process_high_volume_requests(request.jsonData)
        else:
            ai_response = await process_any_json(request.jsonData)
        
        processing_time = time.time() - start_time
        ai_response["processingTime"] = round(processing_time, 2)
        
        # Add user ID if provided
        if request.userId:
            ai_response["userId"] = request.userId
        
        return ai_response

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing recommendations: {str(e)}")


@app.post("/api/skill-gap-analysis/{user_id}", response_model=List[SkillGap])
async def get_skill_gap_analysis(user_id: str):
    """
    Get detailed skill gap analysis for a specific user
    """
    try:
        # Simulate processing time
        time.sleep(1.5)

        return generate_dummy_skill_gaps()

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing skill gap analysis: {str(e)}")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
