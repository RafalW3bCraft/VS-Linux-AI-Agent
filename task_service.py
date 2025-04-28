"""
Task Service for The Commander AI Agent System.

This module provides task-oriented suggestions and workflows for common security and
development tasks, integrating multiple AI models for comprehensive solutions.
"""

import json
import logging
import os
from typing import Dict, List, Any, Optional, Union
import random

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TaskService:
    """
    Service for providing task-oriented suggestions and workflows.
    
    This class provides methods for:
    - Suggesting task workflows for common security tasks
    - Integrating multiple AI models for comprehensive solutions
    - Providing step-by-step guidance for complex tasks
    """
    
    def __init__(self):
        """Initialize the Task Service with available templates."""
        self.templates_file = os.path.join("templates", "task_templates.json")
        self.templates = self._load_templates()
        self.available_ai = self._get_available_ai()
        
    def _load_templates(self) -> Dict[str, Any]:
        """Load task templates from the JSON file."""
        try:
            with open(self.templates_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading task templates: {str(e)}")
            return {}
            
    def _get_available_ai(self) -> Dict[str, bool]:
        """Check which AI services are available."""
        available = {
            "openai": os.environ.get("OPENAI_API_KEY") is not None,
            "claude": os.environ.get("ANTHROPIC_API_KEY") is not None,
            "perplexity": os.environ.get("PERPLEXITY_API_KEY") is not None,
            "deepseek": False  # Not currently supported but included for future
        }
        return available
    
    def get_task_templates(self) -> List[Dict[str, Any]]:
        """
        Get a list of available task templates.
        
        Returns:
            List of template metadata (name, description)
        """
        result = []
        for key, template in self.templates.items():
            result.append({
                "id": key,
                "name": template.get("name", key),
                "description": template.get("description", "")
            })
        return result
    
    def get_task_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific task template by ID.
        
        Args:
            template_id: The ID of the template to retrieve
            
        Returns:
            The template or None if not found
        """
        return self.templates.get(template_id)
    
    def get_task_suggestions(self, query: str) -> List[Dict[str, Any]]:
        """
        Get task suggestions based on a query.
        
        Args:
            query: The user's query or task description
            
        Returns:
            List of suggested tasks with relevance scores
        """
        # Simple keyword matching for now
        keywords = {
            "bug_bounty": ["bug bounty", "vulnerability", "security", "exploit", "bounty", "hack"],
            "code_review": ["code review", "secure code", "analyze code", "review code", "code security"],
            "penetration_testing": ["pentest", "penetration test", "pen test", "hacking", "red team"],
            "secure_development": ["secure development", "sdlc", "secure coding", "security development"]
        }
        
        query = query.lower()
        scores = {}
        
        # Score each template based on keyword matches
        for template_id, words in keywords.items():
            score = 0
            for word in words:
                if word in query:
                    score += 1
            if score > 0:
                scores[template_id] = score
        
        # Sort by score and convert to list
        result = []
        for template_id, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            template = self.templates.get(template_id, {})
            result.append({
                "id": template_id,
                "name": template.get("name", template_id),
                "description": template.get("description", ""),
                "relevance": min(score / 3, 1.0)  # Normalize score between 0-1
            })
            
        # If no matches, suggest general templates
        if not result:
            for template_id in random.sample(list(self.templates.keys()), min(2, len(self.templates))):
                template = self.templates.get(template_id, {})
                result.append({
                    "id": template_id,
                    "name": template.get("name", template_id),
                    "description": template.get("description", ""),
                    "relevance": 0.5  # Middle relevance
                })
                
        return result
    
    def get_ai_suggestions(self, template_id: str) -> Dict[str, str]:
        """
        Get AI-specific suggestions for a template.
        
        Args:
            template_id: The template ID
            
        Returns:
            Dictionary mapping AI names to suggestions
        """
        template = self.templates.get(template_id, {})
        ai_suggestions = template.get("ai_suggestions", {})
        
        # Filter to only available AIs
        available_suggestions = {}
        for ai, suggestion in ai_suggestions.items():
            if self.available_ai.get(ai, False):
                available_suggestions[ai] = suggestion
                
        return available_suggestions
    
    def get_task_steps(self, template_id: str) -> List[Dict[str, Any]]:
        """
        Get the detailed steps for a task.
        
        Args:
            template_id: The template ID
            
        Returns:
            List of steps with commands and descriptions
        """
        template = self.templates.get(template_id, {})
        return template.get("steps", [])
    
    def get_missing_ai_services(self) -> List[Dict[str, str]]:
        """
        Get a list of AI services that could be enabled.
        
        Returns:
            List of missing AI services with descriptions
        """
        missing = []
        
        descriptions = {
            "openai": "OpenAI GPT-4o for state-of-the-art visual and textual analysis",
            "claude": "Anthropic Claude for nuanced understanding and detailed explanations",
            "perplexity": "Perplexity for real-time research and up-to-date information",
            "deepseek": "DeepSeek for specialized code understanding and generation"
        }
        
        for ai, available in self.available_ai.items():
            if not available:
                missing.append({
                    "name": ai,
                    "description": descriptions.get(ai, f"Enable {ai.capitalize()} integration")
                })
                
        return missing

# Initialize the task service
task_service = TaskService()