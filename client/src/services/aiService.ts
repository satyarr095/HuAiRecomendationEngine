// AI Service for handling recommendation API calls

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

// Simulate API delay
const simulateApiDelay = (ms: number = 2000) => 
  new Promise(resolve => setTimeout(resolve, ms));

// Dummy data generator
const generateDummyRecommendations = (): RecommendationItem[] => [
  {
    id: "rec-001",
    title: "Advanced JavaScript Concepts",
    type: "course",
    description: "Master closures, prototypes, async/await, and modern ES6+ features",
    reason: "Recommended based on low performance in JavaScript fundamentals",
    difficulty: "intermediate",
    duration: "4 hours",
    skills: ["JavaScript", "ES6+", "Async Programming"],
    rating: 4.8,
    thumbnail: "/api/placeholder/300/200"
  },
  {
    id: "rec-002",
    title: "React Hooks Deep Dive",
    type: "video",
    description: "Complete guide to React Hooks including custom hooks and best practices",
    reason: "Based on your interest in React development",
    difficulty: "intermediate",
    duration: "2.5 hours",
    skills: ["React", "Hooks", "Frontend Development"],
    rating: 4.9,
    thumbnail: "/api/placeholder/300/200"
  },
  {
    id: "rec-003",
    title: "Database Design Principles",
    type: "article",
    description: "Learn normalization, indexing, and optimization techniques",
    reason: "Skill gap identified in database management",
    difficulty: "beginner",
    duration: "45 minutes",
    skills: ["Database Design", "SQL", "Data Modeling"],
    rating: 4.6,
    thumbnail: "/api/placeholder/300/200"
  },
  {
    id: "rec-004",
    title: "API Security Best Practices Quiz",
    type: "quiz",
    description: "Test your knowledge of REST API security and authentication",
    reason: "Popular among peers with similar learning paths",
    difficulty: "intermediate",
    duration: "30 minutes",
    skills: ["API Security", "Authentication", "Web Security"],
    rating: 4.7,
    thumbnail: "/api/placeholder/300/200"
  },
  {
    id: "rec-005",
    title: "TypeScript for JavaScript Developers",
    type: "course",
    description: "Transition from JavaScript to TypeScript with practical examples",
    reason: "Next logical step in your learning progression",
    difficulty: "intermediate",
    duration: "3 hours",
    skills: ["TypeScript", "Type Safety", "JavaScript"],
    rating: 4.8,
    thumbnail: "/api/placeholder/300/200"
  }
];

const generateDummySkillGaps = (): SkillGap[] => [
  {
    skill: "Data Structures & Algorithms",
    currentLevel: 3,
    targetLevel: 8,
    priority: "high",
    recommendedContent: [
      {
        id: "sg-001",
        title: "Data Structures Masterclass",
        type: "course",
        description: "Complete guide to arrays, linked lists, trees, and graphs",
        reason: "Essential for closing your skill gap in algorithms",
        difficulty: "intermediate",
        duration: "6 hours",
        skills: ["Data Structures", "Algorithms", "Problem Solving"],
        rating: 4.9
      }
    ]
  },
  {
    skill: "System Design",
    currentLevel: 2,
    targetLevel: 7,
    priority: "high",
    recommendedContent: [
      {
        id: "sg-002",
        title: "System Design Interview Prep",
        type: "course",
        description: "Learn to design scalable systems and architectures",
        reason: "Critical skill gap for senior developer roles",
        difficulty: "advanced",
        duration: "8 hours",
        skills: ["System Design", "Architecture", "Scalability"],
        rating: 4.8
      }
    ]
  },
  {
    skill: "DevOps & CI/CD",
    currentLevel: 4,
    targetLevel: 7,
    priority: "medium",
    recommendedContent: [
      {
        id: "sg-003",
        title: "Docker & Kubernetes Fundamentals",
        type: "course",
        description: "Containerization and orchestration for modern applications",
        reason: "Enhance your deployment and infrastructure skills",
        difficulty: "intermediate",
        duration: "5 hours",
        skills: ["Docker", "Kubernetes", "DevOps"],
        rating: 4.7
      }
    ]
  }
];

const generateDummyLearningPaths = (): LearningPath[] => [
  {
    id: "path-001",
    title: "Full-Stack Developer Mastery",
    description: "Complete learning path to become a proficient full-stack developer",
    totalDuration: "15 hours",
    skillsGained: ["React", "Node.js", "Database Design", "API Development"],
    steps: [
      {
        id: "step-001",
        title: "React Fundamentals",
        type: "course",
        description: "Build modern user interfaces with React",
        reason: "Foundation for frontend development",
        difficulty: "beginner",
        duration: "4 hours",
        skills: ["React", "JavaScript", "Frontend"],
        rating: 4.8
      },
      {
        id: "step-002",
        title: "Node.js Backend Development",
        type: "course",
        description: "Create robust server-side applications",
        reason: "Essential for full-stack development",
        difficulty: "intermediate",
        duration: "5 hours",
        skills: ["Node.js", "Express", "Backend"],
        rating: 4.7
      },
      {
        id: "step-003",
        title: "Database Integration",
        type: "course",
        description: "Connect your applications to databases",
        reason: "Complete your full-stack knowledge",
        difficulty: "intermediate",
        duration: "3 hours",
        skills: ["Database", "SQL", "Integration"],
        rating: 4.6
      }
    ]
  }
];

export const aiService = {
  async getRecommendations(jsonData: Record<string, unknown>): Promise<AIResponse> {
    // Simulate API processing time
    await simulateApiDelay(2500);
    
    // In a real implementation, this would send jsonData to the AI backend
    // For now, we return dummy data
    return {
      userId: "user-123",
      recommendations: generateDummyRecommendations(),
      skillGaps: generateDummySkillGaps(),
      learningPaths: generateDummyLearningPaths(),
      processingTime: 2.5
    };
  },

  async getSkillGapAnalysis(userId: string): Promise<SkillGap[]> {
    await simulateApiDelay(1500);
    return generateDummySkillGaps();
  }
}; 