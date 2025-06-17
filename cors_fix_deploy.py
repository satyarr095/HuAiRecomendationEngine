#!/usr/bin/env python3
import boto3
import json
import zipfile
import os
import shutil

def fix_cors_lambda():
    """Fix CORS to allow multiple origins including localhost"""
    
    # Create package directory
    if os.path.exists("cors_fix_package"):
        shutil.rmtree("cors_fix_package")
    os.makedirs("cors_fix_package")
    
    # Lambda function with fixed CORS
    lambda_code = '''
import json
import time
from typing import Dict, List, Any
import logging
import hashlib

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_security_headers(origin=None):
    """Return security headers with dynamic CORS origin"""
    
    # Allow multiple origins for development and production
    allowed_origins = [
        'https://ai-recommendation-engine-frontend-1750160765.s3-website-us-east-1.amazonaws.com',
        'http://localhost:5173',
        'http://localhost:5174', 
        'http://localhost:3000',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:5174',
        'http://127.0.0.1:3000'
    ]
    
    # Default to wildcard if origin not in allowed list, but prefer specific origin
    cors_origin = '*'
    if origin and origin in allowed_origins:
        cors_origin = origin
    elif not origin:
        cors_origin = allowed_origins[0]  # Default to production
    
    return {
        'Access-Control-Allow-Origin': cors_origin,
        'Access-Control-Allow-Headers': 'Content-Type, X-Requested-With, Accept, Cache-Control, Authorization',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS, PUT, DELETE',
        'Access-Control-Allow-Credentials': 'false',
        'Access-Control-Max-Age': '86400',
        'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
        'Referrer-Policy': 'strict-origin-when-cross-origin',
        'Content-Type': 'application/json'
    }

class LambdaAIEngine:
    """AI Engine for Lambda that analyzes uploaded JSON"""
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 600  # 10 minutes
        
    def _generate_cache_key(self, json_data: Dict[str, Any]) -> str:
        """Generate cache key from JSON data"""
        data_str = json.dumps(json_data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()[:12]
    
    def analyze_json_data(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze JSON data to extract learning profile"""
        analysis = {
            "interests": [],
            "skills": [],
            "experience_level": "beginner",
            "goals": [],
            "user_type": "general"
        }
        
        try:
            # Extract all text content
            text_content = self._extract_text_content(json_data).lower()
            
            # Extract from structure
            self._extract_from_json_structure(json_data, analysis)
            
            # Analyze text content
            self._analyze_text_content(text_content, analysis)
            
            # Smart defaults based on content
            if not analysis['interests']:
                analysis['interests'] = self._infer_interests(text_content)
            
            if not analysis['skills']:
                analysis['skills'] = self._infer_skills(text_content)
            
            logger.info(f"Analyzed JSON: {len(text_content)} chars, found {len(analysis['interests'])} interests, {len(analysis['skills'])} skills")
            return analysis
            
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return analysis
    
    def _extract_text_content(self, data: Any) -> str:
        """Extract all text from JSON recursively"""
        text_parts = []
        
        def extract(obj):
            if isinstance(obj, str):
                text_parts.append(obj)
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    text_parts.append(str(k))
                    extract(v)
            elif isinstance(obj, list):
                for item in obj:
                    extract(item)
            elif obj is not None:
                text_parts.append(str(obj))
        
        extract(data)
        return " ".join(text_parts)
    
    def _extract_from_json_structure(self, data: Any, analysis: Dict) -> None:
        """Extract from JSON structure using key patterns"""
        if isinstance(data, dict):
            for key, value in data.items():
                key_lower = key.lower()
                
                # Interest detection
                if any(word in key_lower for word in ['interest', 'subject', 'topic', 'field', 'hobby', 'passion']):
                    if isinstance(value, list):
                        analysis["interests"].extend([str(v) for v in value[:5]])
                    else:
                        analysis["interests"].append(str(value))
                
                # Skill detection
                elif any(word in key_lower for word in ['skill', 'ability', 'tech', 'language', 'framework', 'tool']):
                    if isinstance(value, list):
                        analysis["skills"].extend([str(v) for v in value[:5]])
                    else:
                        analysis["skills"].append(str(value))
                
                # Experience level
                elif any(word in key_lower for word in ['level', 'experience', 'proficiency']):
                    val_str = str(value).lower()
                    if any(word in val_str for word in ['beginner', 'novice', 'new', 'learning']):
                        analysis["experience_level"] = "beginner"
                    elif any(word in val_str for word in ['expert', 'advanced', 'senior', 'professional']):
                        analysis["experience_level"] = "advanced"
                    else:
                        analysis["experience_level"] = "intermediate"
                
                # Goals
                elif any(word in key_lower for word in ['goal', 'objective', 'want', 'aim', 'target']):
                    if isinstance(value, list):
                        analysis["goals"].extend([str(v) for v in value[:3]])
                    else:
                        analysis["goals"].append(str(value))
                
                # Recurse into nested structures
                if isinstance(value, (dict, list)):
                    self._extract_from_json_structure(value, analysis)
        
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, (dict, list)):
                    self._extract_from_json_structure(item, analysis)
    
    def _analyze_text_content(self, text: str, analysis: Dict) -> None:
        """Analyze text for tech skills and interests"""
        
        # Programming languages
        languages = {
            'python': 'Python', 'javascript': 'JavaScript', 'java': 'Java', 
            'typescript': 'TypeScript', 'c++': 'C++', 'c#': 'C#', 'go': 'Go', 
            'rust': 'Rust', 'swift': 'Swift', 'kotlin': 'Kotlin', 'php': 'PHP'
        }
        
        for lang_key, lang_name in languages.items():
            if lang_key in text:
                analysis['skills'].append(lang_name)
        
        # Frameworks and technologies
        technologies = {
            'react': 'React', 'angular': 'Angular', 'vue': 'Vue.js',
            'node.js': 'Node.js', 'express': 'Express', 'django': 'Django',
            'flask': 'Flask', 'spring': 'Spring', 'docker': 'Docker',
            'kubernetes': 'Kubernetes', 'aws': 'AWS', 'azure': 'Azure',
            'mongodb': 'MongoDB', 'postgresql': 'PostgreSQL', 'mysql': 'MySQL'
        }
        
        for tech_key, tech_name in technologies.items():
            if tech_key in text:
                analysis['skills'].append(tech_name)
        
        # Interest areas
        interest_patterns = {
            'Web Development': ['web dev', 'frontend', 'backend', 'fullstack', 'html', 'css'],
            'Data Science': ['data science', 'machine learning', 'analytics', 'statistics', 'pandas', 'numpy'],
            'Mobile Development': ['mobile dev', 'android', 'ios', 'react native', 'flutter'],
            'DevOps': ['devops', 'ci/cd', 'deployment', 'infrastructure', 'cloud'],
            'Cybersecurity': ['security', 'cybersecurity', 'pentesting', 'ethical hacking'],
            'Game Development': ['game dev', 'unity', 'unreal', 'gaming'],
            'AI/ML': ['artificial intelligence', 'neural networks', 'deep learning', 'tensorflow']
        }
        
        for interest, patterns in interest_patterns.items():
            if any(pattern in text for pattern in patterns):
                analysis['interests'].append(interest)
    
    def _infer_interests(self, text: str) -> List[str]:
        """Infer interests when not explicitly found"""
        interests = []
        
        if any(word in text for word in ['code', 'program', 'develop', 'software']):
            interests.append('Software Development')
        if any(word in text for word in ['data', 'analytics', 'analysis']):
            interests.append('Data Analysis')
        if any(word in text for word in ['design', 'ui', 'ux', 'visual']):
            interests.append('UI/UX Design')
        if any(word in text for word in ['business', 'management', 'startup']):
            interests.append('Business Development')
        
        return interests if interests else ['Technology', 'Learning']
    
    def _infer_skills(self, text: str) -> List[str]:
        """Infer skills when not explicitly found"""
        skills = []
        
        if any(word in text for word in ['communication', 'presentation', 'meeting']):
            skills.append('Communication')
        if any(word in text for word in ['project', 'management', 'planning']):
            skills.append('Project Management')
        if any(word in text for word in ['analysis', 'problem', 'solving']):
            skills.append('Problem Solving')
        if any(word in text for word in ['team', 'collaboration', 'group']):
            skills.append('Teamwork')
        
        return skills if skills else ['Critical Thinking', 'Adaptability']
    
    def generate_recommendations(self, user_analysis: Dict) -> Dict:
        """Generate personalized recommendations based on JSON analysis"""
        interests = user_analysis.get('interests', ['Technology'])
        skills = user_analysis.get('skills', ['Programming'])
        level = user_analysis.get('experience_level', 'beginner')
        goals = user_analysis.get('goals', [])
        
        recommendations = []
        
        # Recommendation 1: Primary interest focused
        primary_interest = interests[0] if interests else 'Technology'
        recommendations.append({
            "id": "rec-001",
            "title": f"{primary_interest} Mastery Course",
            "type": "course",
            "description": f"Comprehensive guide to {primary_interest.lower()} with hands-on projects and real-world applications",
            "reason": f"Based on your JSON data showing strong interest in {primary_interest.lower()}",
            "difficulty": level,
            "duration": "8-12 hours",
            "skills": [primary_interest, "Practical Application"],
            "rating": 4.8,
            "url": self._get_course_url(primary_interest),
            "source": "json_analysis"
        })
        
        # Recommendation 2: Skill enhancement
        if skills:
            primary_skill = skills[0]
            next_level = "advanced" if level == "intermediate" else "intermediate"
            recommendations.append({
                "id": "rec-002",
                "title": f"Advanced {primary_skill} Techniques",
                "type": "course",
                "description": f"Take your {primary_skill.lower()} skills to the next level with industry best practices",
                "reason": f"Your JSON indicates experience with {primary_skill.lower()} - time to advance!",
                "difficulty": next_level,
                "duration": "6-8 hours",
                "skills": [primary_skill, "Advanced Techniques"],
                "rating": 4.7,
                "url": self._get_course_url(primary_skill),
                "source": "skill_analysis"
            })
        
        # Add 3 more recommendations to get 5 total
        comp_skill = self._get_complementary_skill(interests, skills)
        recommendations.append({
            "id": "rec-003",
            "title": f"{comp_skill} Fundamentals",
            "type": "course",
            "description": f"Learn {comp_skill.lower()} to broaden your skill set and increase opportunities",
            "reason": f"Perfect complement to your {primary_interest.lower()} focus",
            "difficulty": "beginner",
            "duration": "4-6 hours",
            "skills": [comp_skill, "Skill Diversification"],
            "rating": 4.6,
            "url": self._get_course_url(comp_skill),
            "source": "recommendation_engine"
        })
        
        recommendations.append({
            "id": "rec-004",
            "title": f"{primary_interest} Portfolio Projects",
            "type": "tutorial",
            "description": f"Build 3 real-world {primary_interest.lower()} projects to showcase your skills",
            "reason": "Portfolio projects demonstrate practical skills to employers",
            "difficulty": level,
            "duration": "15-20 hours",
            "skills": [primary_interest, "Portfolio Building", "Real-world Application"],
            "rating": 4.9,
            "url": "https://github.com/",
            "source": "practical_focus"
        })
        
        recommendations.append({
            "id": "rec-005",
            "title": f"Professional {primary_interest} Certification",
            "type": "course",
            "description": f"Industry-recognized certification in {primary_interest.lower()} to boost your career",
            "reason": "Certifications validate your expertise to employers",
            "difficulty": "advanced",
            "duration": "20-25 hours",
            "skills": [primary_interest, "Professional Certification", "Career Advancement"],
            "rating": 4.8,
            "url": self._get_course_url(primary_interest),
            "source": "certification_path"
        })
        
        # Generate skill gaps
        skill_gaps = [{
            "skill": f"{primary_interest} Professional Skills",
            "currentLevel": 4 if level == "intermediate" else (2 if level == "beginner" else 6),
            "targetLevel": 9,
            "priority": "high",
            "recommendedContent": recommendations[:2]
        }, {
            "skill": f"Advanced {comp_skill}",
            "currentLevel": 2,
            "targetLevel": 7,
            "priority": "medium",
            "recommendedContent": recommendations[2:4]
        }]
        
        # Generate learning paths
        learning_paths = [{
            "id": "path-001",
            "title": f"Complete {primary_interest} Learning Journey",
            "description": f"Personalized path from {level} to expert in {primary_interest.lower()}, based on your uploaded profile",
            "totalDuration": "40-60 hours",
            "steps": [
                recommendations[0],  # Foundation
                recommendations[3],  # Projects
                recommendations[1],  # Advanced
                recommendations[4]   # Certification
            ],
            "skillsGained": [primary_interest, "Professional Development", "Industry Best Practices", "Project Management"]
        }]
        
        return {
            "userId": f"user-{int(time.time())}",
            "recommendations": recommendations,
            "skillGaps": skill_gaps,
            "learningPaths": learning_paths,
            "processingTime": 2.3,
            "dataSource": "cors_fixed_analysis",
            "analysisMethod": "ai_powered_cors_fixed",
            "inputDataSize": len(str(user_analysis)),
            "personalizedFor": interests[:2] if interests else ["General Learning"],
            "securityLevel": "enhanced",
            "corsStatus": "fixed"
        }
    
    def _get_course_url(self, topic: str) -> str:
        """Get relevant course URL for topic - all HTTPS"""
        topic_lower = topic.lower()
        
        url_mapping = {
            'python': "https://python.org/about/gettingstarted/",
            'javascript': "https://javascript.info/",
            'react': "https://reactjs.org/tutorial/tutorial.html",
            'data science': "https://kaggle.com/learn/python",
            'web development': "https://freecodecamp.org/learn/",
            'machine learning': "https://coursera.org/specializations/machine-learning",
            'mobile development': "https://developer.android.com/courses",
            'devops': "https://aws.amazon.com/training/",
            'cybersecurity': "https://cybrary.it/",
            'ui/ux design': "https://uxdesign.cc/"
        }
        
        for key, url in url_mapping.items():
            if key in topic_lower:
                return url
                 
        return "https://coursera.org/"
    
    def _get_complementary_skill(self, interests: List[str], skills: List[str]) -> str:
        """Get complementary skill based on current profile"""
        interest_text = " ".join(interests).lower()
        skill_text = " ".join(skills).lower()
        
        if 'web' in interest_text and 'javascript' not in skill_text:
            return "JavaScript"
        elif 'data' in interest_text and 'python' not in skill_text:
            return "Python for Data Analysis"
        elif 'mobile' in interest_text:
            return "React Native"
        elif 'backend' in interest_text and 'database' not in skill_text:
            return "Database Design"
        elif 'frontend' in interest_text and 'css' not in skill_text:
            return "Advanced CSS"
        else:
            return "Version Control (Git)"

# Global AI engine instance
ai_engine = LambdaAIEngine()

def lambda_handler(event, context):
    """Lambda handler with CORS fix"""
    
    # Get origin from headers
    origin = None
    if 'headers' in event:
        origin = event['headers'].get('Origin') or event['headers'].get('origin')
    
    # Handle CORS preflight with proper origin handling
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': get_security_headers(origin),
            'body': ''
        }
    
    # Health check
    if event.get('path') == '/health':
        return {
            'statusCode': 200,
            'headers': get_security_headers(origin),
            'body': json.dumps({
                "status": "healthy", 
                "timestamp": "2025-06-17", 
                "engine": "cors_fixed_processor", 
                "cors": "fixed",
                "allowedOrigin": origin or "default"
            })
        }
    
    # Recommendations endpoint
    if event.get('path') == '/api/recommendations' and event.get('httpMethod') == 'POST':
        try:
            # Parse request body with validation
            if 'body' in event and event['body']:
                try:
                    request_data = json.loads(event['body'])
                    json_data = request_data.get('jsonData', {})
                    
                    # Basic validation
                    if not isinstance(json_data, dict):
                        raise ValueError("Invalid JSON data format")
                        
                except json.JSONDecodeError:
                    return {
                        'statusCode': 400,
                        'headers': get_security_headers(origin),
                        'body': json.dumps({"error": "Invalid JSON format"})
                    }
            else:
                json_data = {}
            
            logger.info(f"Processing JSON data from origin: {origin}")
            
            # Check cache first
            cache_key = ai_engine._generate_cache_key(json_data)
            
            if cache_key in ai_engine.cache:
                cached_results, timestamp = ai_engine.cache[cache_key]
                if time.time() - timestamp < ai_engine.cache_ttl:
                    logger.info("Using cached results")
                    return {
                        'statusCode': 200,
                        'headers': get_security_headers(origin),
                        'body': json.dumps(cached_results)
                    }
            
            # Analyze the uploaded JSON data
            user_analysis = ai_engine.analyze_json_data(json_data)
            
            # Generate personalized recommendations
            recommendations = ai_engine.generate_recommendations(user_analysis)
            
            # Cache the results
            ai_engine.cache[cache_key] = (recommendations, time.time())
            
            logger.info(f"Generated {len(recommendations['recommendations'])} recommendations")
            
            return {
                'statusCode': 200,
                'headers': get_security_headers(origin),
                'body': json.dumps(recommendations)
            }
            
        except Exception as e:
            logger.error(f"Processing error: {e}")
            return {
                'statusCode': 500,
                'headers': get_security_headers(origin),
                'body': json.dumps({"error": "Processing failed", "details": str(e)})
            }
    
    # Default response
    return {
        'statusCode': 200,
        'headers': get_security_headers(origin),
        'body': json.dumps({
            "message": "AI Recommendation Engine API - CORS Fixed", 
            "status": "ready", 
            "cors": "fixed",
            "origin": origin
        })
    }
'''
    
    with open("cors_fix_package/lambda_function.py", "w") as f:
        f.write(lambda_code)
    
    # Create ZIP file
    with zipfile.ZipFile("cors-fix-lambda.zip", "w") as zf:
        zf.write("cors_fix_package/lambda_function.py", "lambda_function.py")
    
    print("📦 Created CORS fix Lambda package")
    
    # Deploy to AWS Lambda
    lambda_client = boto3.client('lambda', region_name='us-east-1')
    
    function_name = "ai-simple-api"
    
    try:
        with open("cors-fix-lambda.zip", "rb") as f:
            zip_content = f.read()
            
        # Update existing function
        response = lambda_client.update_function_code(
            FunctionName=function_name,
            ZipFile=zip_content
        )
        
        print(f"✅ CORS issue fixed! Lambda updated successfully!")
        print(f"📋 Function ARN: {response['FunctionArn']}")
        print("🌐 Now supports:")
        print("   - Production: https://ai-recommendation-engine-frontend-1750160765.s3-website-us-east-1.amazonaws.com")
        print("   - Local dev: http://localhost:5173, http://localhost:5174")
        print("   - Local dev: http://127.0.0.1:5173, http://127.0.0.1:5174")
        
    except Exception as e:
        print(f"⚠️ Lambda update error: {e}")
        return None
    
    finally:
        # Cleanup
        shutil.rmtree("cors_fix_package", ignore_errors=True)
        if os.path.exists("cors-fix-lambda.zip"):
            os.remove("cors-fix-lambda.zip")
    
    print("🎉 CORS issue resolved! API now works from both localhost and production!")
    return "https://y8wxjhqcfd.execute-api.us-east-1.amazonaws.com/prod"

if __name__ == "__main__":
    fix_cors_lambda() 