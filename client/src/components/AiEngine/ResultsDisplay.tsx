import React from 'react';
import { motion } from 'framer-motion';
import { 
  BookOpen, 
  Play, 
  FileText, 
  HelpCircle, 
  Star, 
  Clock, 
  TrendingUp, 
  Target,
  ArrowRight,
  CheckCircle
} from 'lucide-react';
import type { AIResponse, RecommendationItem, SkillGap, LearningPath } from '../../services/aiService';

interface ResultsDisplayProps {
  results: AIResponse;
  onBackToUpload: () => void;
}

const getTypeIcon = (type: string) => {
  switch (type) {
    case 'course': return BookOpen;
    case 'video': return Play;
    case 'article': return FileText;
    case 'quiz': return HelpCircle;
    default: return BookOpen;
  }
};

const getDifficultyColor = (difficulty: string) => {
  switch (difficulty) {
    case 'beginner': return 'difficulty-beginner';
    case 'intermediate': return 'difficulty-intermediate';
    case 'advanced': return 'difficulty-advanced';
    default: return 'difficulty-beginner';
  }
};

const getPriorityColor = (priority: string) => {
  switch (priority) {
    case 'high': return 'priority-high';
    case 'medium': return 'priority-medium';
    case 'low': return 'priority-low';
    default: return 'priority-medium';
  }
};

const RecommendationCard: React.FC<{ item: RecommendationItem; index: number }> = ({ item, index }) => {
  const TypeIcon = getTypeIcon(item.type);
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className="recommendation-card"
    >
      <div className="card-header">
        <div className="type-indicator">
          <TypeIcon className="type-icon" />
          <span className="type-text">{item.type}</span>
        </div>
        <div className="rating">
          <Star className="star-icon" />
          <span>{item.rating}</span>
        </div>
      </div>
      
      <div className="card-content">
        <h3 className="card-title">{item.title}</h3>
        <p className="card-description">{item.description}</p>
        
        <div className="reason-box">
          <TrendingUp className="reason-icon" />
          <span className="reason-text">{item.reason}</span>
        </div>
        
        <div className="card-meta">
          <div className="meta-item">
            <Clock className="meta-icon" />
            <span>{item.duration}</span>
          </div>
          <div className={`difficulty-badge ${getDifficultyColor(item.difficulty)}`}>
            {item.difficulty}
          </div>
        </div>
        
        <div className="skills-tags">
          {item.skills.map((skill, idx) => (
            <span key={idx} className="skill-tag">{skill}</span>
          ))}
        </div>
      </div>
      
      <div className="card-footer">
        <button className="btn btn-primary btn-small">
          Start Learning
          <ArrowRight className="btn-icon" />
        </button>
      </div>
    </motion.div>
  );
};

const SkillGapCard: React.FC<{ gap: SkillGap; index: number }> = ({ gap, index }) => {
  const progressPercentage = (gap.currentLevel / gap.targetLevel) * 100;
  
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
      className="skill-gap-card"
    >
      <div className="skill-header">
        <div className="skill-info">
          <h3 className="skill-name">{gap.skill}</h3>
          <span className={`priority-badge ${getPriorityColor(gap.priority)}`}>
            {gap.priority} priority
          </span>
        </div>
        <div className="skill-levels">
          <span className="current-level">Current: {gap.currentLevel}/10</span>
          <span className="target-level">Target: {gap.targetLevel}/10</span>
        </div>
      </div>
      
      <div className="progress-container">
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
        <span className="progress-text">{Math.round(progressPercentage)}% complete</span>
      </div>
      
      {gap.recommendedContent.length > 0 && (
        <div className="recommended-content">
          <h4 className="content-title">Recommended to bridge this gap:</h4>
          {gap.recommendedContent.map((content, idx) => (
            <div key={idx} className="mini-recommendation">
              <div className="mini-rec-header">
                <span className="mini-rec-title">{content.title}</span>
                <span className="mini-rec-duration">{content.duration}</span>
              </div>
              <p className="mini-rec-reason">{content.reason}</p>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
};

const LearningPathCard: React.FC<{ path: LearningPath; index: number }> = ({ path, index }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: index * 0.2 }}
      className="learning-path-card"
    >
      <div className="path-header">
        <h3 className="path-title">{path.title}</h3>
        <div className="path-meta">
          <span className="path-duration">
            <Clock className="meta-icon" />
            {path.totalDuration}
          </span>
        </div>
      </div>
      
      <p className="path-description">{path.description}</p>
      
      <div className="skills-gained">
        <h4 className="skills-title">Skills you'll gain:</h4>
        <div className="skills-list">
          {path.skillsGained.map((skill, idx) => (
            <span key={idx} className="skill-tag skill-gained">{skill}</span>
          ))}
        </div>
      </div>
      
      <div className="learning-steps">
        <h4 className="steps-title">Learning Steps:</h4>
        {path.steps.map((step, idx) => (
          <div key={idx} className="learning-step">
            <div className="step-number">{idx + 1}</div>
            <div className="step-content">
              <h5 className="step-title">{step.title}</h5>
              <p className="step-description">{step.description}</p>
              <div className="step-meta">
                <span className="step-duration">{step.duration}</span>
                <span className={`difficulty-badge ${getDifficultyColor(step.difficulty)}`}>
                  {step.difficulty}
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      <div className="path-footer">
        <button className="btn btn-primary">
          Start Learning Path
          <ArrowRight className="btn-icon" />
        </button>
      </div>
    </motion.div>
  );
};

const ResultsDisplay: React.FC<ResultsDisplayProps> = ({ results, onBackToUpload }) => {
  return (
    <div className="results-container">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="results-header"
      >
        <div className="header-content">
          <div className="success-indicator">
            <CheckCircle className="success-icon" />
            <div className="success-text">
              <h2>Analysis Complete!</h2>
              <p>Processed in {results.processingTime}s • Generated {results.recommendations.length} personalized recommendations</p>
            </div>
          </div>
          <button onClick={onBackToUpload} className="btn btn-secondary">
            Upload New Data
          </button>
        </div>
      </motion.div>

      {/* Personalized Recommendations Section */}
      <section className="recommendations-section">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="section-header"
        >
          <h2 className="section-title">
            <Target className="section-icon" />
            Recommended for You
          </h2>
          <p className="section-subtitle">
            Personalized learning content based on your profile and goals
          </p>
        </motion.div>
        
        <div className="recommendations-grid">
          {results.recommendations.map((item, index) => (
            <RecommendationCard key={item.id} item={item} index={index} />
          ))}
        </div>
      </section>

      {/* Skill Gap Analysis Section */}
      <section className="skill-gaps-section">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="section-header"
        >
          <h2 className="section-title">
            <TrendingUp className="section-icon" />
            Skill Gap Analysis
          </h2>
          <p className="section-subtitle">
            Identify areas for improvement and bridge your skill gaps
          </p>
        </motion.div>
        
        <div className="skill-gaps-grid">
          {results.skillGaps.map((gap, index) => (
            <SkillGapCard key={gap.skill} gap={gap} index={index} />
          ))}
        </div>
      </section>

      {/* Learning Paths Section */}
      <section className="learning-paths-section">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.6 }}
          className="section-header"
        >
          <h2 className="section-title">
            <BookOpen className="section-icon" />
            Suggested Learning Paths
          </h2>
          <p className="section-subtitle">
            Structured learning journeys to achieve your goals
          </p>
        </motion.div>
        
        <div className="learning-paths-grid">
          {results.learningPaths.map((path, index) => (
            <LearningPathCard key={path.id} path={path} index={index} />
          ))}
        </div>
      </section>
    </div>
  );
};

export default ResultsDisplay; 