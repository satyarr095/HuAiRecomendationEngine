const API_BASE_URL = 'http://localhost:8000';

export interface RecommendationItem {
  id: string;
  title: string;
  type: 'course' | 'video' | 'article' | 'quiz';
  description: string;
  reason: string;
  difficulty: 'beginner' | 'intermediate' | 'advanced';
  duration: string;
  skills: string[];
  rating: number;
  thumbnail?: string;
}

export interface SkillGap {
  skill: string;
  currentLevel: number;
  targetLevel: number;
  priority: 'high' | 'medium' | 'low';
  recommendedContent: RecommendationItem[];
}

export interface LearningPath {
  id: string;
  title: string;
  description: string;
  totalDuration: string;
  steps: RecommendationItem[];
  skillsGained: string[];
}

export interface AIResponse {
  userId: string;
  recommendations: RecommendationItem[];
  skillGaps: SkillGap[];
  learningPaths: LearningPath[];
  processingTime: number;
}

// API request helper with error handling
async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const errorData = await response.text();
      throw new Error(`API Error ${response.status}: ${errorData}`);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof Error) {
      throw new Error(`Failed to connect to AI backend: ${error.message}`);
    }
    throw new Error('Unknown error occurred while contacting AI backend');
  }
}

export const aiService = {
  async getRecommendations(jsonData: Record<string, unknown>): Promise<AIResponse> {
    // Send the JSON data to the FastAPI backend for analysis
    return await apiRequest<AIResponse>('/api/recommendations', {
      method: 'POST',
      body: JSON.stringify({
        jsonData,
        userId: `user-${Date.now()}` // Generate a simple user ID
      }),
    });
  },

  async getSkillGapAnalysis(userId: string): Promise<SkillGap[]> {
    // Get skill gap analysis from the FastAPI backend
    return await apiRequest<SkillGap[]>(`/api/skill-gap-analysis/${userId}`, {
      method: 'POST',
    });
  }
}; 