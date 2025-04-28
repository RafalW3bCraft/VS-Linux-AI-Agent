"""
Advanced AI Service for the Commander Agent System.

This module provides integration with multiple state-of-the-art AI models including 
Anthropic Claude and OpenAI for sophisticated natural language understanding,
multimodal processing, and advanced knowledge management.
"""

import os
import logging
import sys
import json
import base64
import requests
from typing import Dict, List, Any, Optional, Union
import anthropic
from anthropic import Anthropic

# Optional OpenAI import
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    
# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AIService:
    """
    Service for interacting with advanced AI models.
    
    This class provides methods for:
    - Advanced natural language understanding
    - Context-aware command parsing
    - Multi-turn conversation handling
    - Code generation and analysis
    """
    
    def __init__(self):
        """Initialize the AI Service with available AI models."""
        self.models = {}
        self.conversation_history = {}
        self.embedding_cache = {}
        self.knowledge_store = {}
        self.setup_anthropic()
        self.setup_openai()
    
    def setup_anthropic(self):
        """Set up the Anthropic Claude integration."""
        try:
            anthropic_key = os.environ.get('ANTHROPIC_API_KEY')
            if not anthropic_key:
                logger.warning("ANTHROPIC_API_KEY not found in environment variables.")
                return
            
            self.models['claude'] = Anthropic(api_key=anthropic_key)
            logger.info("Anthropic Claude API initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing Anthropic Claude API: {str(e)}")
    
    def setup_openai(self):
        """Set up the OpenAI integration."""
        try:
            if not OPENAI_AVAILABLE:
                logger.warning("OpenAI package not installed. Skipping OpenAI setup.")
                return
                
            openai_key = os.environ.get('OPENAI_API_KEY')
            if not openai_key:
                logger.warning("OPENAI_API_KEY not found in environment variables.")
                return
                
            self.models['openai'] = OpenAI(api_key=openai_key)
            logger.info("OpenAI API initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing OpenAI API: {str(e)}")
    
    def understand_command(self, command_text, user_id="default", context=None):
        """
        Understand and parse a natural language command into structured format.
        
        Args:
            command_text: The text-based command to understand
            user_id: Identifier for the user (for conversation history)
            context: Additional context information
            
        Returns:
            Structured command information
        """
        if 'claude' not in self.models:
            return {"error": "Claude API not available"}
        
        # Get conversation history for the user
        history = self.get_conversation_history(user_id)
        
        # Create system prompt for command understanding
        system_prompt = """
        You are an assistant that helps parse natural language commands into structured formats.
        Your task is to understand user commands related to VS Code configurations, 
        Linux terminal operations, and security operations.
        
        Convert natural language commands to our system's command format.
        
        Command format:
        {
            "command": "<main_command>",
            "subcommand": "<sub_command>",
            "args": [<list_of_arguments>],
            "options": {<dictionary_of_options>},
            "original_text": "<original_command_text>"
        }
        
        Available main commands:
        - help: Get help information
        - file: File operations
        - terminal: Execute terminal commands
        - api: Make API requests
        - about: Show information about the system
        - coder: Code generation and debugging
        - researcher: Web scraping and analysis
        - sysadmin: System administration
        - memory: Persistent memory storage
        - vscode: VS Code operations
        - security: Security scanning
        
        Format all outputs as JSON.
        """
        
        # Create user message with context if provided
        user_message = command_text
        if context:
            user_message = f"Context: {json.dumps(context)}\n\nCommand: {command_text}"
        
        try:
            response = self.models['claude'].messages.create(
                model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ],
                temperature=0.0,
                max_tokens=1000
            )
            
            # Extract and parse the JSON from the response
            result = {}
            try:
                content = response.content[0].text
                # Extract JSON from the content (it might be wrapped in ```json or other formatting)
                if "```json" in content:
                    json_start = content.find("```json") + 7
                    json_end = content.find("```", json_start)
                    json_str = content[json_start:json_end].strip()
                    result = json.loads(json_str)
                else:
                    result = json.loads(content)
                
                # Add to conversation history
                self.add_to_history(user_id, {"role": "user", "content": user_message})
                self.add_to_history(user_id, {"role": "assistant", "content": content})
                
                return result
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON from Claude response: {content}")
                return {
                    "command": command_text.split()[0] if command_text.split() else "",
                    "original_text": command_text,
                    "parsed_by": "fallback"
                }
                
        except Exception as e:
            logger.error(f"Error calling Claude API: {str(e)}")
            return {
                "command": command_text.split()[0] if command_text.split() else "",
                "original_text": command_text,
                "parsed_by": "fallback",
                "error": str(e)
            }
    
    def generate_code(self, language, description, context=None):
        """
        Generate code based on a description.
        
        Args:
            language: The programming language to use
            description: Description of what the code should do
            context: Additional context (file snippets, etc.)
            
        Returns:
            Generated code with explanation
        """
        if 'claude' not in self.models:
            return "Claude API not available. Cannot generate code."
        
        system_prompt = f"""
        You are an expert programmer specializing in {language}.
        Generate high-quality, efficient, and well-documented code based on the user's description.
        Include helpful comments and explanations where appropriate.
        Optimize for readability and maintainability.
        """
        
        user_message = f"Create {language} code that does the following:\n{description}"
        if context:
            user_message += f"\n\nAdditional context:\n{context}"
        
        try:
            response = self.models['claude'].messages.create(
                model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_message}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error generating code with Claude API: {str(e)}")
            return f"Error generating code: {str(e)}"
    
    def analyze_code(self, language, code, analysis_type="security"):
        """
        Analyze code for various purposes (security, optimization, etc.).
        
        Args:
            language: The programming language of the code
            code: The code to analyze
            analysis_type: Type of analysis to perform
            
        Returns:
            Analysis results
        """
        if 'claude' not in self.models:
            return "Claude API not available. Cannot analyze code."
        
        system_prompt = f"""
        You are an expert code analyzer specializing in {language}.
        Perform a detailed {analysis_type} analysis of the provided code.
        For security analysis, look for:
        - Injection vulnerabilities
        - Authentication issues
        - Authorization flaws
        - Data exposure risks
        - Security misconfigurations
        - Cryptographic failures
        - Business logic vulnerabilities
        
        Provide specific explanations and code examples for remediation.
        Format your response in clear sections with bullet points.
        """
        
        try:
            response = self.models['claude'].messages.create(
                model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                system=system_prompt,
                messages=[
                    {"role": "user", "content": code}
                ],
                temperature=0.1,
                max_tokens=2500
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error analyzing code with Claude API: {str(e)}")
            return f"Error analyzing code: {str(e)}"
    
    def suggest_improvements(self, language, code):
        """
        Suggest improvements for the provided code.
        
        Args:
            language: The programming language of the code
            code: The code to improve
            
        Returns:
            Suggested improvements
        """
        if 'claude' not in self.models:
            return "Claude API not available. Cannot suggest improvements."
        
        system_prompt = f"""
        You are an expert programmer specializing in {language}.
        Analyze the provided code and suggest improvements for:
        - Performance optimization
        - Code readability
        - Error handling
        - Maintainability
        - Following best practices
        
        For each suggestion, provide:
        1. The issue or opportunity for improvement
        2. Why it matters
        3. A code example showing the improved version
        
        Focus on practical, impactful improvements.
        """
        
        try:
            response = self.models['claude'].messages.create(
                model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                system=system_prompt,
                messages=[
                    {"role": "user", "content": code}
                ],
                temperature=0.1,
                max_tokens=2500
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error suggesting improvements with Claude API: {str(e)}")
            return f"Error suggesting improvements: {str(e)}"
    
    def explain_code(self, language, code):
        """
        Provide an explanation for a code snippet.
        
        Args:
            language: The programming language of the code
            code: The code to explain
            
        Returns:
            Explanation of the code
        """
        if 'claude' not in self.models:
            return "Claude API not available. Cannot explain code."
        
        system_prompt = f"""
        You are an expert programmer and teacher specializing in {language}.
        Explain the provided code in a clear, educational manner.
        Break down:
        - What the code does overall
        - How it works step by step
        - Any important patterns, algorithms, or techniques used
        - Potential edge cases or limitations
        
        Format your explanation to be educational for a programmer who is
        familiar with programming but may not be an expert in {language}.
        """
        
        try:
            response = self.models['claude'].messages.create(
                model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                system=system_prompt,
                messages=[
                    {"role": "user", "content": code}
                ],
                temperature=0.1,
                max_tokens=2000
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error explaining code with Claude API: {str(e)}")
            return f"Error explaining code: {str(e)}"
    
    def generate_test(self, language, code):
        """
        Generate tests for the provided code.
        
        Args:
            language: The programming language of the code
            code: The code to test
            
        Returns:
            Generated tests for the code
        """
        if 'claude' not in self.models:
            return "Claude API not available. Cannot generate tests."
        
        system_prompt = f"""
        You are an expert in test-driven development for {language}.
        Generate comprehensive tests for the provided code that:
        - Cover all main functionality
        - Test edge cases and error conditions
        - Follow testing best practices for {language}
        - Are well-documented and maintainable
        
        Include explanation of the testing approach and any test frameworks or
        libraries that should be used.
        """
        
        try:
            response = self.models['claude'].messages.create(
                model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                system=system_prompt,
                messages=[
                    {"role": "user", "content": code}
                ],
                temperature=0.2,
                max_tokens=2000
            )
            
            return response.content[0].text
            
        except Exception as e:
            logger.error(f"Error generating tests with Claude API: {str(e)}")
            return f"Error generating tests: {str(e)}"
    
    def get_conversation_history(self, user_id):
        """Get conversation history for a user."""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        return self.conversation_history[user_id]
    
    def add_to_history(self, user_id, message):
        """Add a message to a user's conversation history."""
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        self.conversation_history[user_id].append(message)
        # Limit history size to avoid memory issues
        if len(self.conversation_history[user_id]) > 20:
            self.conversation_history[user_id] = self.conversation_history[user_id][-20:]
    
    def clear_history(self, user_id):
        """Clear conversation history for a user."""
        if user_id in self.conversation_history:
            self.conversation_history[user_id] = []
            return f"Conversation history cleared for {user_id}"
        return f"No conversation history found for {user_id}"
        
    # Multimodal capabilities
    
    def analyze_image(self, image_data, query=None):
        """
        Analyze an image and provide a description or answer questions about it.
        
        Args:
            image_data: The base64-encoded image data
            query: Optional question about the image
            
        Returns:
            Analysis of the image or answer to the question
        """
        if 'openai' not in self.models:
            return "OpenAI API not available. Cannot analyze image."
            
        try:
            prompt = "Describe this image in detail."
            if query:
                prompt = query
                
            response = self.models['openai'].chat.completions.create(
                model="gpt-4o", # the newest OpenAI model is "gpt-4o" which was released May 13, 2024
                messages=[
                    {
                        "role": "user", 
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
                            }
                        ]
                    }
                ],
                max_tokens=1000
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error analyzing image with OpenAI API: {str(e)}")
            return f"Error analyzing image: {str(e)}"
    
    def generate_image(self, prompt):
        """
        Generate an image based on a text prompt.
        
        Args:
            prompt: Text description of the image to generate
            
        Returns:
            URL of the generated image
        """
        if 'openai' not in self.models:
            return "OpenAI API not available. Cannot generate image."
            
        try:
            response = self.models['openai'].images.generate(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            
            return {"url": response.data[0].url}
            
        except Exception as e:
            logger.error(f"Error generating image with OpenAI API: {str(e)}")
            return f"Error generating image: {str(e)}"
    
    def answer_with_sources(self, query, context_sources):
        """
        Answer a question with proper citations to the provided sources.
        
        Args:
            query: The question to answer
            context_sources: List of documents/sources with their content
            
        Returns:
            Answer with citations to the sources
        """
        if 'claude' not in self.models and 'openai' not in self.models:
            return "AI APIs not available. Cannot generate answer with sources."
            
        # Prefer Claude for this task if available
        model_key = 'claude' if 'claude' in self.models else 'openai'
        model_name = "claude-3-5-sonnet-20241022" if model_key == 'claude' else "gpt-4o"
        
        try:
            # Format context sources
            formatted_context = "\n\n".join([
                f"SOURCE {i+1}: {source['title']}\n{source['content']}"
                for i, source in enumerate(context_sources)
            ])
            
            system_prompt = """
            You are a research assistant that provides accurate, factual information with proper citations.
            When answering the user's question:
            1. Use ONLY the information provided in the sources
            2. Cite your sources using [SOURCE X] notation
            3. If the sources contradict each other, note the discrepancy
            4. If the answer cannot be determined from the sources, say so clearly
            5. Do not make up or infer information not contained in the sources
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"SOURCES:\n\n{formatted_context}\n\nQUESTION: {query}"}
            ]
            
            if model_key == 'claude':
                response = self.models[model_key].messages.create(
                    model=model_name,
                    system=system_prompt,
                    messages=[{"role": "user", "content": f"SOURCES:\n\n{formatted_context}\n\nQUESTION: {query}"}],
                    temperature=0.1,
                    max_tokens=2000
                )
                return response.content[0].text
            else:
                response = self.models[model_key].chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=0.1,
                    max_tokens=2000
                )
                return response.choices[0].message.content
                
        except Exception as e:
            logger.error(f"Error generating answer with sources: {str(e)}")
            return f"Error generating answer with sources: {str(e)}"
    
    def store_knowledge(self, key, content, metadata=None):
        """
        Store knowledge in the knowledge base with metadata.
        
        Args:
            key: Unique identifier for the knowledge
            content: The content to store
            metadata: Additional information about the content
            
        Returns:
            Success message
        """
        if not metadata:
            metadata = {}
        
        self.knowledge_store[key] = {
            "content": content,
            "metadata": metadata,
            "created_at": self._get_timestamp(),
            "last_accessed": self._get_timestamp()
        }
        
        return f"Knowledge stored with key: {key}"
    
    def retrieve_knowledge(self, key):
        """
        Retrieve knowledge from the knowledge base.
        
        Args:
            key: Unique identifier for the knowledge
            
        Returns:
            The stored content or error message
        """
        if key in self.knowledge_store:
            self.knowledge_store[key]["last_accessed"] = self._get_timestamp()
            return self.knowledge_store[key]["content"]
        return f"No knowledge found with key: {key}"
    
    def search_knowledge(self, query, limit=5):
        """
        Search the knowledge base for relevant information.
        
        Args:
            query: Search query
            limit: Maximum number of results to return
            
        Returns:
            List of relevant knowledge items
        """
        # Simple keyword-based search for now
        results = []
        for key, data in self.knowledge_store.items():
            content = data["content"]
            if query.lower() in content.lower():
                results.append({
                    "key": key,
                    "content": content,
                    "metadata": data["metadata"],
                    "relevance": content.lower().count(query.lower())
                })
        
        # Sort by relevance
        results.sort(key=lambda x: x["relevance"], reverse=True)
        return results[:limit]
    
    def _get_timestamp(self):
        """Get a formatted timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()

# Initialize the global AI service
ai_service = AIService()