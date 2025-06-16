import json
import asyncio
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import logging

# Free internet access libraries
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

class FlexibleAIRecommendationEngine:
    """
    AI Recommendation Engine that can handle ANY JSON format and provides
    intelligent learning recommendations using free resources only.
    """
    
    def __init__(self):
        self.ollama_model = "mistral:7b"  # Default model
        self.max_search_results = 2  # Reduced to minimize rate limiting
        self.ddgs = None  # Initialize only when needed
        
        # Check if Ollama is available
        self.ollama_available = False
        if ollama:
            try:
                # Test if model is available
                available_models = ollama.list()
                # Handle the correct response structure: models attribute contains a list of Model objects
                if hasattr(available_models, 'models'):
                    models_data = available_models.models
                else:
                    models_data = available_models.get('models', [])
                
                model_names = []
                
                for model in models_data:
                    # Handle Model objects (newer Ollama versions)
                    if hasattr(model, 'model'):
                        model_names.append(model.model)
                    # Handle dict format (older versions)
                    elif isinstance(model, dict) and 'name' in model:
                        model_names.append(model['name'])
                    elif isinstance(model, dict) and 'model' in model:
                        model_names.append(model['model'])
                
                logger.info(f"Available models: {model_names}")
                
                if self.ollama_model not in model_names:
                    # Try alternative models
                    for alt_model in ["llama2:7b", "llama2", "mistral", "tinyllama"]:
                        if alt_model in model_names:
                            self.ollama_model = alt_model
                            break
                    else:
                        logger.warning("No suitable Ollama model found. Using first available model.")
                        if model_names:
                            self.ollama_model = model_names[0]
                        
                logger.info(f"Using Ollama model: {self.ollama_model}")
                self.ollama_available = True
            except Exception as e:
                logger.error(f"Ollama connection error: {e}")
                self.ollama_available = False

    async def analyze_json_data(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dynamically analyze any JSON structure to extract meaningful information
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
            # Flatten the JSON to work with nested structures
            flattened = flatten(json_data)
            
            # Convert all values to strings for text analysis
            all_text = " ".join([str(v) for v in flattened.values() if v is not None])
            
            # Use Ollama to understand the data if available
            if self.ollama_available:
                analysis_prompt = f"""
                Analyze this user data and extract:
                1. Learning interests and subjects
                2. Current skills and experience level
                3. Learning goals and objectives
                4. Any educational background
                5. Preferred learning styles or formats
                
                User Data: {json.dumps(json_data, indent=2)}
                
                Respond in JSON format with extracted information.
                """
                
                try:
                    ollama_response = ollama.generate(
                        model=self.ollama_model,
                        prompt=analysis_prompt,
                        options={"temperature": 0.3}
                    )
                    
                    # Try to parse Ollama's response as JSON
                    response_text = ollama_response['response']
                    
                    # Extract JSON from response if wrapped in text
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        try:
                            ollama_analysis = json.loads(json_match.group())
                            analysis.update(ollama_analysis)
                        except json.JSONDecodeError:
                            pass
                            
                except Exception as e:
                    logger.error(f"Ollama analysis error: {e}")
            
            # Fallback: Rule-based extraction from JSON
            self._extract_from_json_structure(json_data, analysis)
            
            # Extract keywords from all text
            analysis["extracted_keywords"] = self._extract_keywords(all_text)
            
            return analysis
            
        except Exception as e:
            logger.error(f"JSON analysis error: {e}")
            return analysis

    def _extract_from_json_structure(self, data: Any, analysis: Dict, prefix: str = "") -> None:
        """
        Recursively extract information from JSON structure using pattern matching
        """
        if isinstance(data, dict):
            for key, value in data.items():
                key_lower = key.lower()
                
                # Extract user information
                if any(keyword in key_lower for keyword in ['name', 'user', 'profile']):
                    analysis["user_info"][key] = value
                
                # Extract interests
                elif any(keyword in key_lower for keyword in ['interest', 'subject', 'topic', 'field']):
                    if isinstance(value, list):
                        analysis["interests"].extend(value)
                    else:
                        analysis["interests"].append(str(value))
                
                # Extract skills
                elif any(keyword in key_lower for keyword in ['skill', 'ability', 'knowledge', 'expertise']):
                    if isinstance(value, list):
                        analysis["skills"].extend(value)
                    else:
                        analysis["skills"].append(str(value))
                
                # Extract experience level
                elif any(keyword in key_lower for keyword in ['level', 'experience', 'expertise']):
                    analysis["experience_level"] = str(value).lower()
                
                # Extract goals
                elif any(keyword in key_lower for keyword in ['goal', 'objective', 'aim', 'target']):
                    if isinstance(value, list):
                        analysis["goals"].extend(value)
                    else:
                        analysis["goals"].append(str(value))
                
                # Extract learning history
                elif any(keyword in key_lower for keyword in ['course', 'education', 'learning', 'training', 'study']):
                    if isinstance(value, list):
                        analysis["learning_history"].extend(value)
                    else:
                        analysis["learning_history"].append(str(value))
                
                # Recurse into nested structures
                if isinstance(value, (dict, list)):
                    self._extract_from_json_structure(value, analysis, f"{prefix}{key}.")
                    
        elif isinstance(data, list):
            for i, item in enumerate(data):
                self._extract_from_json_structure(item, analysis, f"{prefix}[{i}].")

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract relevant keywords from text
        """
        # Common learning-related keywords
        learning_keywords = [
            'programming', 'python', 'javascript', 'web development', 'data science',
            'machine learning', 'ai', 'artificial intelligence', 'react', 'node.js',
            'sql', 'database', 'cloud', 'aws', 'azure', 'docker', 'kubernetes',
            'cybersecurity', 'design', 'ui/ux', 'marketing', 'business', 'finance',
            'project management', 'agile', 'scrum', 'analytics', 'excel', 'powerbi'
        ]
        
        text_lower = text.lower()
        found_keywords = [keyword for keyword in learning_keywords if keyword in text_lower]
        
        return list(set(found_keywords))

    async def search_learning_content(self, interests: List[str], skills: List[str]) -> List[Dict]:
        """
        Search for learning content using minimal external resources to avoid rate limiting
        """
        search_results = []
        
        # Try minimal search with proper rate limiting
        try:
            # Only search for the most important interest to avoid rate limiting
            if interests:
                # Initialize DuckDuckGo only when needed
                if self.ddgs is None:
                    self.ddgs = DDGS()
                
                main_interest = interests[0]
                query = f"free online courses {main_interest}"
                
                # Add delay to avoid rate limiting
                await asyncio.sleep(2)  # Increased delay
                
                ddg_results = self.ddgs.text(query, max_results=1)  # Further reduced
                
                for result in ddg_results:
                    search_results.append({
                        "title": result.get('title', ''),
                        "url": result.get('href', ''),
                        "description": result.get('body', ''),
                        "source": "web_search",
                        "query": query
                    })
                    
        except Exception as e:
            logger.warning(f"Search temporarily unavailable due to rate limiting: {e}")
            # Don't fail, just continue with generated content
        
        # Generate comprehensive content using AI knowledge without external searches
        synthetic_content = self._generate_synthetic_learning_content(interests, skills)
        search_results.extend(synthetic_content)
        
        return search_results[:10]  # Return limited results

    def _generate_synthetic_learning_content(self, interests: List[str], skills: List[str]) -> List[Dict]:
        """
        Generate learning content suggestions based on AI knowledge without external searches
        """
        content_database = {
            "programming": [
                {"title": "FreeCodeCamp - Full Stack Development", "url": "https://freecodecamp.org", "description": "Comprehensive free coding bootcamp"},
                {"title": "Codecademy - Programming Fundamentals", "url": "https://codecademy.com", "description": "Interactive programming courses"},
                {"title": "Khan Academy - Computer Programming", "url": "https://khanacademy.org", "description": "Free programming tutorials and exercises"}
            ],
            "python": [
                {"title": "Python.org Official Tutorial", "url": "https://docs.python.org/3/tutorial/", "description": "Official Python documentation and tutorial"},
                {"title": "Real Python - Python Tutorials", "url": "https://realpython.com", "description": "Comprehensive Python learning resources"},
                {"title": "Automate the Boring Stuff with Python", "url": "https://automatetheboringstuff.com", "description": "Free online Python book for beginners"}
            ],
            "javascript": [
                {"title": "MDN Web Docs - JavaScript", "url": "https://developer.mozilla.org/en-US/docs/Web/JavaScript", "description": "Comprehensive JavaScript documentation"},
                {"title": "JavaScript.info - Modern JavaScript Tutorial", "url": "https://javascript.info", "description": "In-depth JavaScript tutorial"},
                {"title": "FreeCodeCamp - JavaScript Algorithms", "url": "https://freecodecamp.org/learn/javascript-algorithms-and-data-structures/", "description": "Free JavaScript course with projects"}
            ],
            "web development": [
                {"title": "The Odin Project", "url": "https://theodinproject.com", "description": "Free full-stack web development curriculum"},
                {"title": "MDN Web Docs", "url": "https://developer.mozilla.org", "description": "Comprehensive web development documentation"},
                {"title": "freeCodeCamp Web Development", "url": "https://freecodecamp.org", "description": "Free web development certification"}
            ],
            "data science": [
                {"title": "Kaggle Learn", "url": "https://kaggle.com/learn", "description": "Free data science micro-courses"},
                {"title": "Coursera - Data Science Specialization", "url": "https://coursera.org", "description": "University-level data science courses"},
                {"title": "edX - MIT Introduction to Data Science", "url": "https://edx.org", "description": "Free data science course from MIT"}
            ],
            "machine learning": [
                {"title": "Andrew Ng's Machine Learning Course", "url": "https://coursera.org/learn/machine-learning", "description": "Famous ML course by Stanford professor"},
                {"title": "Fast.ai - Practical Deep Learning", "url": "https://fast.ai", "description": "Free practical deep learning course"},
                {"title": "Google AI Education", "url": "https://ai.google/education", "description": "Free AI and ML courses from Google"}
            ],
            "react": [
                {"title": "React Official Documentation", "url": "https://react.dev", "description": "Official React documentation and tutorial"},
                {"title": "FreeCodeCamp - React Course", "url": "https://freecodecamp.org/learn/front-end-development-libraries/", "description": "Free React certification course"},
                {"title": "React Tutorial - Build a Game", "url": "https://react.dev/learn/tutorial-tic-tac-toe", "description": "Official interactive React tutorial"}
            ]
        }
        
        results = []
        
        # Match interests to content database
        for interest in interests[:3]:
            interest_lower = interest.lower()
            for key, content_list in content_database.items():
                if key in interest_lower or interest_lower in key:
                    for content in content_list:
                        results.append({
                            "title": content["title"],
                            "url": content["url"],
                            "description": content["description"],
                            "source": "curated_database",
                            "category": key
                        })
        
        # Add general learning platforms if no specific matches
        if not results:
            general_content = [
                {"title": "Khan Academy", "url": "https://khanacademy.org", "description": "Free world-class education for anyone, anywhere"},
                {"title": "Coursera", "url": "https://coursera.org", "description": "Online courses from top universities and companies"},
                {"title": "edX", "url": "https://edx.org", "description": "Free online courses from Harvard, MIT, and other top institutions"},
                {"title": "Udacity", "url": "https://udacity.com", "description": "Tech-focused online learning with nanodegree programs"},
                {"title": "FreeCodeCamp", "url": "https://freecodecamp.org", "description": "Learn to code for free with hands-on projects"}
            ]
            
            for content in general_content:
                results.append({
                    "title": content["title"],
                    "url": content["url"],
                    "description": content["description"],
                    "source": "general_education",
                    "category": "general"
                })
        
        return results[:8]  # Return up to 8 curated results

    async def generate_recommendations(self, user_analysis: Dict, search_results: List[Dict]) -> Dict:
        """
        Generate personalized recommendations using primarily Ollama AI with minimal external dependency
        """
        if not self.ollama_available:
            return self._generate_fallback_recommendations(user_analysis, search_results)
        
        try:
            # Create a comprehensive prompt for Ollama that relies on its knowledge
            recommendation_prompt = f"""
            You are an expert learning advisor. Based on the user profile below, create 5 specific learning recommendations.

            USER PROFILE:
            - Interests: {user_analysis.get('interests', ['general learning'])}
            - Current Skills: {user_analysis.get('skills', [])}
            - Experience Level: {user_analysis.get('experience_level', 'beginner')}
            - Learning Goals: {user_analysis.get('goals', [])}
            - Previous Learning: {user_analysis.get('learning_history', [])}

            For each recommendation, provide:
            - title: specific course/resource name
            - type: "course", "video", "article", or "quiz"
            - description: 2-3 sentence description
            - reason: why this is recommended for this user
            - difficulty: "beginner", "intermediate", or "advanced"
            - duration: estimated time like "3 hours", "2 weeks", etc.
            - skills: list of 2-3 skills learned
            - rating: number between 4.0-5.0

            Focus on FREE resources like:
            - Khan Academy, Coursera, edX free courses
            - FreeCodeCamp, Codecademy free tracks
            - Official documentation and tutorials
            - YouTube educational channels
            - Open source books and guides

            Format as plain text, not JSON. List each recommendation clearly numbered 1-5.
            """
            
            ollama_response = ollama.generate(
                model=self.ollama_model,
                prompt=recommendation_prompt,
                options={"temperature": 0.5, "num_predict": 1000}
            )
            
            response_text = ollama_response['response']
            
            # Parse the text response into structured data
            return self._parse_ollama_text_response(response_text, user_analysis, search_results)
            
        except Exception as e:
            logger.error(f"Recommendation generation error: {e}")
            return self._generate_fallback_recommendations(user_analysis, search_results)

    def _parse_ollama_text_response(self, response_text: str, user_analysis: Dict, search_results: List[Dict]) -> Dict:
        """
        Parse Ollama's text response into structured recommendations
        """
        recommendations = []
        interests = user_analysis.get('interests', ['learning'])
        
        # Extract numbered recommendations from text
        lines = response_text.split('\n')
        current_rec = {}
        rec_counter = 0
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for numbered recommendations
            if any(line.startswith(f"{i}.") for i in range(1, 6)):
                # Save previous recommendation
                if current_rec and rec_counter < 5:
                    current_rec["id"] = f"rec-{rec_counter+1:03d}"
                    recommendations.append(current_rec)
                    rec_counter += 1
                
                # Start new recommendation
                current_rec = {
                    "title": line.split('.', 1)[1].strip() if '.' in line else f"Learning Resource {rec_counter+1}",
                    "type": "course",
                    "description": "AI-recommended learning resource",
                    "reason": f"Recommended based on your interests in {interests[0] if interests else 'learning'}",
                    "difficulty": "intermediate",
                    "duration": "2-4 hours",
                    "skills": interests[:2] if interests else ["General Knowledge"],
                    "rating": 4.5
                }
            
            # Extract details from subsequent lines
            elif current_rec:
                line_lower = line.lower()
                if 'type:' in line_lower or line_lower.startswith('type'):
                    type_match = re.search(r'(course|video|article|quiz)', line_lower)
                    if type_match:
                        current_rec["type"] = type_match.group(1)
                elif 'description:' in line_lower:
                    desc = line.split(':', 1)[1].strip() if ':' in line else line
                    current_rec["description"] = desc[:200] if desc else current_rec["description"]
                elif 'difficulty:' in line_lower:
                    diff_match = re.search(r'(beginner|intermediate|advanced)', line_lower)
                    if diff_match:
                        current_rec["difficulty"] = diff_match.group(1)
                elif 'duration:' in line_lower:
                    duration = line.split(':', 1)[1].strip() if ':' in line else "2-4 hours"
                    current_rec["duration"] = duration[:50] if duration else "2-4 hours"
        
        # Add the last recommendation
        if current_rec and rec_counter < 5:
            current_rec["id"] = f"rec-{rec_counter+1:03d}"
            recommendations.append(current_rec)
        
        # Ensure we have 5 recommendations
        while len(recommendations) < 5:
            rec_id = len(recommendations) + 1
            recommendations.append({
                "id": f"rec-{rec_id:03d}",
                "title": f"{interests[0] if interests else 'General'} Learning Resource {rec_id}",
                "type": "course",
                "description": f"Comprehensive learning resource for {interests[0] if interests else 'general knowledge'}",
                "reason": f"Recommended based on your learning profile",
                "difficulty": "intermediate",
                "duration": "3-5 hours",
                "skills": interests[:2] if interests else ["General Knowledge"],
                "rating": 4.4
            })
        
        # Generate skill gaps and learning paths
        skill_gaps = [
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
        
        learning_paths = [{
            "id": "path-001",
            "title": f"{interests[0] if interests else 'Comprehensive'} Learning Journey",
            "description": "Structured learning path based on AI analysis of your profile",
            "totalDuration": "15-20 hours",
            "steps": recommendations[:4],
            "skillsGained": interests[:3] if interests else ["Core Knowledge", "Problem Solving", "Critical Thinking"]
        }]
        
        return {
            "userId": f"user-{int(datetime.now().timestamp())}",
            "recommendations": recommendations,
            "skillGaps": skill_gaps,
            "learningPaths": learning_paths,
            "processingTime": 3.2,
            "dataSource": "ai_analysis",
            "analysisMethod": "ollama_enhanced"
        }

    def _generate_fallback_recommendations(self, user_analysis: Dict, search_results: List[Dict]) -> Dict:
        """
        Generate recommendations without Ollama (fallback method)
        """
        recommendations = []
        interests = user_analysis.get('interests', ['general learning'])
        skills = user_analysis.get('skills', [])
        
        # Use search results to create recommendations
        for i, result in enumerate(search_results[:5]):
            recommendation = {
                "id": f"rec-{i+1:03d}",
                "title": result.get('title', f'Learning Resource {i+1}'),
                "type": self._determine_content_type(result.get('title', ''), result.get('description', '')),
                "description": result.get('description', 'Comprehensive learning resource'),
                "reason": f"Matches your interest in {interests[0] if interests else 'learning'}",
                "difficulty": "intermediate",
                "duration": "2-4 hours",
                "skills": interests[:3],
                "rating": 4.5,
                "url": result.get('url', ''),
                "source": result.get('source', 'web')
            }
            recommendations.append(recommendation)
        
        # Generate skill gaps
        skill_gaps = [
            {
                "skill": f"{interests[0] if interests else 'General'} Fundamentals",
                "currentLevel": 3,
                "targetLevel": 8,
                "priority": "high",
                "recommendedContent": recommendations[:1]
            }
        ]
        
        # Generate learning path
        learning_paths = [{
            "id": "path-001",
            "title": f"{interests[0] if interests else 'General'} Learning Path",
            "description": "Structured learning journey based on your profile",
            "totalDuration": "10-15 hours",
            "steps": recommendations[:3],
            "skillsGained": interests[:3] if interests else ["General Knowledge"]
        }]
        
        return {
            "userId": f"user-{int(datetime.now().timestamp())}",
            "recommendations": recommendations,
            "skillGaps": skill_gaps,
            "learningPaths": learning_paths,
            "processingTime": 2.5,
            "dataSource": "ai_analysis",
            "analysisMethod": "fallback" if not self.ollama_available else "ollama"
        }

    def _determine_content_type(self, title: str, description: str) -> str:
        """
        Determine content type based on title and description
        """
        text = (title + " " + description).lower()
        
        if any(keyword in text for keyword in ['course', 'class', 'program']):
            return 'course'
        elif any(keyword in text for keyword in ['video', 'watch', 'tutorial']):
            return 'video'
        elif any(keyword in text for keyword in ['article', 'blog', 'guide', 'post']):
            return 'article'
        elif any(keyword in text for keyword in ['quiz', 'test', 'exam', 'assessment']):
            return 'quiz'
        else:
            return 'course'

    def _format_recommendations(self, recommendations_data: Dict, search_results: List[Dict]) -> Dict:
        """
        Format and validate recommendations from Ollama
        """
        # This method would format the Ollama response into the expected structure
        # Implementation depends on the specific format Ollama returns
        return recommendations_data

    def _generate_structured_recommendations(self, user_analysis: Dict, search_results: List[Dict], ollama_text: str) -> Dict:
        """
        Generate structured recommendations when Ollama doesn't return JSON
        """
        # Parse the text response and create structured data
        return self._generate_fallback_recommendations(user_analysis, search_results)

# Global instance
ai_engine = FlexibleAIRecommendationEngine()

async def process_any_json(json_data: Dict[str, Any]) -> Dict:
    """
    Main function to process any JSON and return AI recommendations
    """
    try:
        # Step 1: Analyze the JSON data
        user_analysis = await ai_engine.analyze_json_data(json_data)
        
        # Step 2: Search for relevant learning content
        search_results = await ai_engine.search_learning_content(
            user_analysis.get('interests', []),
            user_analysis.get('skills', [])
        )
        
        # Step 3: Generate AI-powered recommendations
        recommendations = await ai_engine.generate_recommendations(user_analysis, search_results)
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Processing error: {e}")
        # Return basic recommendations even if processing fails
        return {
            "userId": f"user-{int(datetime.now().timestamp())}",
            "recommendations": [],
            "skillGaps": [],
            "learningPaths": [],
            "processingTime": 0.5,
            "error": str(e),
            "status": "partial_success"
        } 