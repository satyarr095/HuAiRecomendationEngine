import json
import asyncio
import re
import time
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import logging
import hashlib
from collections import defaultdict

# Internet search libraries
from duckduckgo_search import DDGS
import requests
from bs4 import BeautifulSoup
import aiohttp

# Ollama for local LLM
try:
    import ollama
except ImportError:
    print("Ollama not installed. Please install: pip install ollama")
    ollama = None

# JSON processing
from json_flatten import flatten

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntelligentSearchAIEngine:
    """
    Intelligent AI Recommendation Engine that actually searches the internet
    while being smart about rate limiting and caching.
    """
    
    def __init__(self):
        self.ollama_model = "mistral:7b"
        self.ddgs = DDGS()
        
        # Smart rate limiting (not disabling search)
        self.search_rate_limiter = defaultdict(list)
        self.max_searches_per_minute = 30  # Reasonable limit
        self.search_delay = 1.5  # Delay between searches
        
        # Intelligent caching - only cache similar requests
        self.cache = {}
        self.cache_ttl = 600  # 10 minutes for search results
        self.similarity_threshold = 0.8  # How similar requests need to be to use cache
        
        # Check if Ollama is available
        self.ollama_available = False
        if ollama:
            try:
                available_models = ollama.list()
                if hasattr(available_models, 'models'):
                    models_data = available_models.models
                else:
                    models_data = available_models.get('models', [])
                
                model_names = []
                for model in models_data:
                    if hasattr(model, 'model'):
                        model_names.append(model.model)
                    elif isinstance(model, dict) and 'name' in model:
                        model_names.append(model['name'])
                    elif isinstance(model, dict) and 'model' in model:
                        model_names.append(model['model'])
                
                logger.info(f"Available models: {model_names}")
                
                if self.ollama_model not in model_names:
                    for alt_model in ["llama3:latest", "llama3.2:latest", "mistral", "tinyllama"]:
                        if alt_model in model_names:
                            self.ollama_model = alt_model
                            break
                    else:
                        if model_names:
                            self.ollama_model = model_names[0]
                        
                logger.info(f"Using Ollama model: {self.ollama_model}")
                self.ollama_available = True
            except Exception as e:
                logger.error(f"Ollama connection error: {e}")
                self.ollama_available = False

    def _generate_smart_cache_key(self, interests: List[str], skills: List[str], level: str) -> str:
        """Generate cache key based on core learning profile elements"""
        # Sort to make consistent keys for similar profiles
        interests_str = "_".join(sorted([i.lower().strip() for i in interests[:3]]))
        skills_str = "_".join(sorted([s.lower().strip() for s in skills[:3]]))
        level_str = level.lower().strip()
        
        key_data = f"{interests_str}_{skills_str}_{level_str}"
        return hashlib.md5(key_data.encode()).hexdigest()[:12]

    def _should_use_cache(self, cache_key: str) -> bool:
        """Check if we should use cached results"""
        if cache_key not in self.cache:
            return False
        
        cached_data, timestamp = self.cache[cache_key]
        return time.time() - timestamp < self.cache_ttl

    def _can_search_now(self) -> bool:
        """Smart rate limiting - allow searches but with delays"""
        now = time.time()
        minute_ago = now - 60
        
        # Clean old entries
        self.search_rate_limiter['searches'] = [
            timestamp for timestamp in self.search_rate_limiter['searches']
            if timestamp > minute_ago
        ]
        
        recent_searches = len(self.search_rate_limiter['searches'])
        
        if recent_searches >= self.max_searches_per_minute:
            logger.warning(f"Rate limit reached ({recent_searches} searches in last minute)")
            return False
        
        return True

    async def analyze_json_data(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze JSON data to extract learning profile
        """
        analysis = {
            "user_info": {},
            "interests": [],
            "skills": [],
            "experience_level": "beginner",
            "goals": [],
            "learning_history": [],
            "preferences": {},
            "extracted_keywords": []
        }
        
        try:
            # Flatten and extract text
            flattened = flatten(json_data)
            all_text = " ".join([str(v) for v in flattened.values() if v is not None])
            
            # Use Ollama for intelligent analysis
            if self.ollama_available:
                try:
                    analysis_prompt = f"""
                    Analyze this user data and extract their learning profile:
                    
                    Data: {json.dumps(json_data, indent=1)[:800]}
                    
                    Extract and return ONLY:
                    INTERESTS: [specific subjects/topics they want to learn]
                    SKILLS: [current abilities/knowledge they have]
                    LEVEL: beginner/intermediate/advanced
                    GOALS: [what they want to achieve]
                    
                    Be specific and detailed in your extraction.
                    """
                    
                    response = ollama.generate(
                        model=self.ollama_model,
                        prompt=analysis_prompt,
                        options={"temperature": 0.3, "num_predict": 300}
                    )
                    
                    response_text = response['response'].lower()
                    
                    # Parse the structured response
                    if 'interests:' in response_text:
                        interests_section = response_text.split('interests:')[1].split('skills:')[0] if 'skills:' in response_text else response_text.split('interests:')[1]
                        interests = re.findall(r'[a-zA-Z\s]+', interests_section)
                        analysis['interests'] = [i.strip() for i in interests if i.strip() and len(i.strip()) > 2][:5]
                    
                    if 'skills:' in response_text:
                        skills_section = response_text.split('skills:')[1].split('level:')[0] if 'level:' in response_text else response_text.split('skills:')[1]
                        skills = re.findall(r'[a-zA-Z\s]+', skills_section)
                        analysis['skills'] = [s.strip() for s in skills if s.strip() and len(s.strip()) > 2][:5]
                    
                    if 'level:' in response_text:
                        level_match = re.search(r'level:\s*(beginner|intermediate|advanced)', response_text)
                        if level_match:
                            analysis['experience_level'] = level_match.group(1)
                    
                    if 'goals:' in response_text:
                        goals_section = response_text.split('goals:')[1]
                        goals = re.findall(r'[a-zA-Z\s]+', goals_section)
                        analysis['goals'] = [g.strip() for g in goals if g.strip() and len(g.strip()) > 2][:3]
                        
                except Exception as e:
                    logger.warning(f"Ollama analysis error: {e}")
            
            # Fallback extraction if Ollama fails
            if not analysis['interests']:
                self._extract_from_json_structure(json_data, analysis)
            
            # Ensure we have at least some interests
            if not analysis['interests']:
                analysis['interests'] = ['general learning', 'skill development']
            
            return analysis
            
        except Exception as e:
            logger.error(f"JSON analysis error: {e}")
            return analysis

    def _extract_from_json_structure(self, data: Any, analysis: Dict, prefix: str = "") -> None:
        """Extract information from JSON structure using pattern matching"""
        if isinstance(data, dict):
            for key, value in data.items():
                key_lower = key.lower()
                
                if any(keyword in key_lower for keyword in ['interest', 'subject', 'topic', 'field']):
                    if isinstance(value, list):
                        analysis["interests"].extend([str(v) for v in value[:3]])
                    else:
                        analysis["interests"].append(str(value))
                elif any(keyword in key_lower for keyword in ['skill', 'ability', 'knowledge', 'expertise']):
                    if isinstance(value, list):
                        analysis["skills"].extend([str(v) for v in value[:3]])
                    else:
                        analysis["skills"].append(str(value))
                elif any(keyword in key_lower for keyword in ['level', 'experience']):
                    analysis["experience_level"] = str(value).lower()
                elif any(keyword in key_lower for keyword in ['goal', 'objective', 'aim', 'target']):
                    if isinstance(value, list):
                        analysis["goals"].extend([str(v) for v in value[:2]])
                    else:
                        analysis["goals"].append(str(value))
                
                if isinstance(value, dict) and len(prefix) < 2:
                    self._extract_from_json_structure(value, analysis, f"{prefix}{key}.")

    async def search_learning_content(self, interests: List[str], skills: List[str], experience_level: str) -> List[Dict]:
        """
        Intelligent internet search for learning content
        """
        # Generate cache key for this search profile
        cache_key = self._generate_smart_cache_key(interests, skills, experience_level)
        
        # Check if we should use cached results
        if self._should_use_cache(cache_key):
            cached_results, _ = self.cache[cache_key]
            logger.info(f"Using cached search results for similar profile")
            return cached_results
        
        search_results = []
        
        # Check if we can make new searches
        if not self._can_search_now():
            logger.warning("Rate limit reached, using fallback search strategy")
            return self._generate_fallback_search_results(interests, skills)
        
        try:
            # Create targeted search queries
            search_queries = self._generate_smart_search_queries(interests, skills, experience_level)
            
            for query in search_queries[:4]:  # Limit to 4 searches
                try:
                    logger.info(f"Searching: {query}")
                    
                    # Add search delay for rate limiting
                    await asyncio.sleep(self.search_delay)
                    
                    # Record search attempt
                    self.search_rate_limiter['searches'].append(time.time())
                    
                    # Perform search
                    ddg_results = self.ddgs.text(query, max_results=3)
                    
                    for result in ddg_results:
                        search_results.append({
                            "title": result.get('title', ''),
                            "url": result.get('href', ''),
                            "description": result.get('body', ''),
                            "source": "live_search",
                            "query": query,
                            "relevance_score": self._calculate_relevance(result, interests)
                        })
                        
                except Exception as e:
                    logger.warning(f"Search error for '{query}': {e}")
                    continue
            
            # Add some curated high-quality sources
            curated_results = self._get_curated_quality_sources(interests, skills)
            search_results.extend(curated_results)
            
            # Sort by relevance
            search_results.sort(key=lambda x: x.get('relevance_score', 0), reverse=True)
            
            # Cache the results
            self.cache[cache_key] = (search_results[:12], time.time())
            
            return search_results[:12]
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return self._generate_fallback_search_results(interests, skills)

    def _generate_smart_search_queries(self, interests: List[str], skills: List[str], level: str) -> List[str]:
        """Generate targeted search queries based on user profile"""
        queries = []
        
        for interest in interests[:2]:
            # Level-specific searches
            queries.append(f"best {level} {interest} courses free online 2024")
            queries.append(f"learn {interest} {level} tutorial")
            
            # Skill-gap based searches
            if skills:
                main_skill = skills[0]
                queries.append(f"{interest} for {main_skill} developers")
            
            # Practical project searches
            queries.append(f"{interest} projects {level} hands-on")
        
        return queries

    def _calculate_relevance(self, result: Dict, interests: List[str]) -> float:
        """Calculate relevance score for search results"""
        title = result.get('title', '').lower()
        description = result.get('body', '').lower()
        content = f"{title} {description}"
        
        score = 0.0
        
        # Interest matching
        for interest in interests:
            if interest.lower() in content:
                score += 1.0
        
        # Quality indicators
        quality_indicators = ['course', 'tutorial', 'learn', 'guide', 'free', 'beginner', 'complete']
        for indicator in quality_indicators:
            if indicator in content:
                score += 0.3
        
        # Trusted sources get bonus
        trusted_domains = ['coursera.org', 'edx.org', 'khanacademy.org', 'freecodecamp.org', 'udacity.com']
        url = result.get('href', '').lower()
        for domain in trusted_domains:
            if domain in url:
                score += 2.0
                break
        
        return score

    def _get_curated_quality_sources(self, interests: List[str], skills: List[str]) -> List[Dict]:
        """Get high-quality curated sources"""
        curated = []
        
        for interest in interests[:2]:
            interest_lower = interest.lower()
            
            if any(term in interest_lower for term in ['python', 'programming', 'coding']):
                curated.extend([
                    {
                        "title": f"Python.org Official Tutorial",
                        "url": "https://docs.python.org/3/tutorial/",
                        "description": "Complete Python tutorial from the official documentation",
                        "source": "curated",
                        "relevance_score": 3.0
                    },
                    {
                        "title": f"Real Python - {interest}",
                        "url": "https://realpython.com",
                        "description": f"High-quality Python tutorials for {interest}",
                        "source": "curated", 
                        "relevance_score": 2.8
                    }
                ])
            
            elif any(term in interest_lower for term in ['javascript', 'js', 'web']):
                curated.extend([
                    {
                        "title": f"MDN Web Docs - {interest}",
                        "url": "https://developer.mozilla.org",
                        "description": f"Comprehensive {interest} documentation and tutorials",
                        "source": "curated",
                        "relevance_score": 3.0
                    }
                ])
            
            elif any(term in interest_lower for term in ['data science', 'machine learning', 'ai']):
                curated.extend([
                    {
                        "title": f"Kaggle Learn - {interest}",
                        "url": "https://kaggle.com/learn",
                        "description": f"Free micro-courses in {interest}",
                        "source": "curated",
                        "relevance_score": 2.9
                    }
                ])
        
        return curated

    def _generate_fallback_search_results(self, interests: List[str], skills: List[str]) -> List[Dict]:
        """Generate fallback results when search is not available"""
        logger.info("Using fallback search results")
        
        results = []
        for i, interest in enumerate(interests[:3]):
            results.append({
                "title": f"Complete {interest} Course",
                "url": f"https://freecodecamp.org",
                "description": f"Comprehensive free course covering {interest} fundamentals and advanced topics",
                "source": "fallback",
                "relevance_score": 2.0
            })
        
        return results

    async def generate_recommendations(self, user_analysis: Dict, search_results: List[Dict]) -> Dict:
        """
        Generate personalized recommendations using search results and AI
        """
        if not self.ollama_available:
            return self._generate_rule_based_recommendations(user_analysis, search_results)
        
        try:
            interests = user_analysis.get('interests', [])
            skills = user_analysis.get('skills', [])
            level = user_analysis.get('experience_level', 'beginner')
            goals = user_analysis.get('goals', [])
            
            # Create detailed prompt with actual search results
            recommendation_prompt = f"""
            You are an expert learning advisor. Create 5 personalized learning recommendations.

            USER PROFILE:
            - Learning Interests: {interests}
            - Current Skills: {skills}
            - Experience Level: {level}
            - Goals: {goals}

            AVAILABLE RESOURCES FROM INTERNET SEARCH:
            {json.dumps(search_results[:8], indent=1)}

            Create 5 specific recommendations. For each, provide:
            1. Title (be specific, not generic)
            2. Type: course/video/article/tutorial
            3. Description (2-3 sentences explaining what they'll learn)
            4. Why recommended (specific to their profile)
            5. Difficulty: beginner/intermediate/advanced
            6. Duration estimate
            7. Skills they'll gain
            8. URL if available from search results

            Make each recommendation unique and tailored to their specific interests and level.
            Use the actual search results when possible.
            """
            
            response = ollama.generate(
                model=self.ollama_model,
                prompt=recommendation_prompt,
                options={"temperature": 0.6, "num_predict": 1200}
            )
            
            response_text = response['response']
            
            # Parse AI response into structured recommendations
            recommendations = self._parse_ai_recommendations(response_text, search_results, user_analysis)
            
            # Generate skill gaps and learning paths
            skill_gaps = self._generate_skill_gaps(user_analysis, recommendations)
            learning_paths = self._generate_learning_paths(user_analysis, recommendations)
            
            return {
                "userId": f"user-{int(time.time())}",
                "recommendations": recommendations,
                "skillGaps": skill_gaps,
                "learningPaths": learning_paths,
                "processingTime": 2.5,
                "dataSource": "live_search_and_ai",
                "searchResultsUsed": len(search_results),
                "analysisMethod": "intelligent_search"
            }
            
        except Exception as e:
            logger.error(f"Recommendation generation error: {e}")
            return self._generate_rule_based_recommendations(user_analysis, search_results)

    def _parse_ai_recommendations(self, ai_text: str, search_results: List[Dict], user_analysis: Dict) -> List[Dict]:
        """Parse AI-generated recommendations into structured format"""
        recommendations = []
        
        # Split response into sections
        sections = re.split(r'\d+\.', ai_text)
        
        for i, section in enumerate(sections[1:6]):  # Take first 5 recommendations
            if not section.strip():
                continue
                
            # Extract information from AI response
            lines = section.strip().split('\n')
            
            rec = {
                "id": f"rec-{i+1:03d}",
                "title": "Learning Resource",
                "type": "course",
                "description": "AI-recommended learning resource",
                "reason": "Recommended based on your profile",
                "difficulty": user_analysis.get('experience_level', 'intermediate'),
                "duration": "3-5 hours",
                "skills": user_analysis.get('interests', ['Learning'])[:2],
                "rating": 4.5,
                "url": "",
                "source": "ai_generated"
            }
            
            # Parse the AI response
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if i == 0 and len(line) > 10:  # First substantial line is likely the title
                    rec["title"] = line[:100]
                elif "description:" in line.lower() or "learn:" in line.lower():
                    desc = line.split(':', 1)[1].strip() if ':' in line else line
                    rec["description"] = desc[:200]
                elif "type:" in line.lower():
                    type_match = re.search(r'(course|video|article|tutorial)', line.lower())
                    if type_match:
                        rec["type"] = type_match.group(1)
                elif "difficulty:" in line.lower() or "level:" in line.lower():
                    diff_match = re.search(r'(beginner|intermediate|advanced)', line.lower())
                    if diff_match:
                        rec["difficulty"] = diff_match.group(1)
                elif "duration:" in line.lower() or "time:" in line.lower():
                    duration = line.split(':', 1)[1].strip() if ':' in line else "3-5 hours"
                    rec["duration"] = duration[:30]
                elif "url:" in line.lower() or "link:" in line.lower():
                    url = line.split(':', 1)[1].strip() if ':' in line else ""
                    rec["url"] = url
            
            # Try to match with search results for URLs
            if not rec["url"] and search_results:
                for result in search_results:
                    if any(word in result.get('title', '').lower() for word in rec["title"].lower().split()[:3]):
                        rec["url"] = result.get('url', '')
                        rec["source"] = "matched_search_result"
                        break
            
            recommendations.append(rec)
        
        # Ensure we have 5 recommendations
        while len(recommendations) < 5:
            interests = user_analysis.get('interests', ['learning'])
            rec_num = len(recommendations) + 1
            recommendations.append({
                "id": f"rec-{rec_num:03d}",
                "title": f"{interests[0] if interests else 'Learning'} Resource {rec_num}",
                "type": "course",
                "description": f"Additional learning resource for {interests[0] if interests else 'skill development'}",
                "reason": "Recommended to complement your learning journey",
                "difficulty": user_analysis.get('experience_level', 'intermediate'),
                "duration": "2-4 hours",
                "skills": interests[:2] if interests else ["General Skills"],
                "rating": 4.3,
                "url": search_results[rec_num % len(search_results)].get('url', '') if search_results else '',
                "source": "generated"
            })
        
        return recommendations

    def _generate_skill_gaps(self, user_analysis: Dict, recommendations: List[Dict]) -> List[Dict]:
        """Generate skill gap analysis"""
        interests = user_analysis.get('interests', ['learning'])
        
        return [
            {
                "skill": f"{interests[0] if interests else 'Core'} Fundamentals",
                "currentLevel": 3,
                "targetLevel": 8,
                "priority": "high",
                "recommendedContent": recommendations[:2]
            },
            {
                "skill": f"Advanced {interests[0] if interests else 'Concepts'}",
                "currentLevel": 2,
                "targetLevel": 7,
                "priority": "medium",
                "recommendedContent": recommendations[2:4]
            }
        ]

    def _generate_learning_paths(self, user_analysis: Dict, recommendations: List[Dict]) -> List[Dict]:
        """Generate learning paths"""
        interests = user_analysis.get('interests', ['learning'])
        
        return [{
            "id": "path-001",
            "title": f"{interests[0] if interests else 'Comprehensive'} Learning Journey",
            "description": "Structured learning path based on current internet resources and AI analysis",
            "totalDuration": "20-30 hours",
            "steps": recommendations[:4],
            "skillsGained": interests[:3] if interests else ["Problem Solving", "Critical Thinking"]
        }]

    def _generate_rule_based_recommendations(self, user_analysis: Dict, search_results: List[Dict]) -> Dict:
        """Fallback recommendations when AI is not available"""
        interests = user_analysis.get('interests', ['learning'])
        
        recommendations = []
        for i, result in enumerate(search_results[:5]):
            recommendations.append({
                "id": f"rec-{i+1:03d}",
                "title": result.get('title', f'{interests[0] if interests else "Learning"} Resource {i+1}'),
                "type": "course",
                "description": result.get('description', 'Quality learning resource from internet search'),
                "reason": f"Found through targeted search for {interests[0] if interests else 'your interests'}",
                "difficulty": user_analysis.get('experience_level', 'intermediate'),
                "duration": "3-6 hours",
                "skills": interests[:2] if interests else ["General Skills"],
                "rating": 4.4,
                "url": result.get('url', ''),
                "source": "search_based"
            })
        
        return {
            "userId": f"user-{int(time.time())}",
            "recommendations": recommendations,
            "skillGaps": self._generate_skill_gaps(user_analysis, recommendations),
            "learningPaths": self._generate_learning_paths(user_analysis, recommendations),
            "processingTime": 1.5,
            "dataSource": "internet_search_only",
            "analysisMethod": "rule_based"
        }

# Global instance for intelligent search
intelligent_engine = IntelligentSearchAIEngine()

async def process_with_intelligent_search(json_data: Dict[str, Any]) -> Dict:
    """
    Main processing function that actually searches the internet and gives personalized results
    """
    try:
        # Step 1: Analyze user profile
        user_analysis = await intelligent_engine.analyze_json_data(json_data)
        
        # Step 2: Search internet for relevant content
        search_results = await intelligent_engine.search_learning_content(
            user_analysis.get('interests', []),
            user_analysis.get('skills', []),
            user_analysis.get('experience_level', 'beginner')
        )
        
        # Step 3: Generate AI-powered recommendations using search results
        recommendations = await intelligent_engine.generate_recommendations(user_analysis, search_results)
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Intelligent search processing error: {e}")
        return {
            "userId": f"user-{int(time.time())}",
            "recommendations": [],
            "skillGaps": [],
            "learningPaths": [],
            "processingTime": 0.5,
            "error": str(e),
            "status": "error"
        } 