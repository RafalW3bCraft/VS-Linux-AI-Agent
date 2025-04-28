"""
Advanced Command and Control Center for The Commander AI Agent System.

This module provides orchestration and coordination between specialized agents,
enabling complex AI workflows, multimodal processing, and knowledge management.
It acts as the central hub for all agent activities in the system.
"""

import logging
import json
import os
from typing import Dict, List, Any, Optional, Union
from agent import Commander

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class CommandCenter:
    """
    Command and Control Center for coordinating agent activities.
    
    This class manages communication between agents, orchestrates complex tasks,
    and maintains the overall system state.
    """
    
    def __init__(self):
        """Initialize the Command Center with its agents and tools."""
        logger.debug("Initializing Command Center")
        
        # Initialize the main Commander agent
        self.commander = Commander()
        
        # Direct references to specialized agents for easy access
        self.coder = self.commander.coder_agent
        self.researcher = self.commander.researcher_agent
        self.sysadmin = self.commander.sysadmin_agent
        self.memory = self.commander.memorykeeper_agent
        self.vscode = self.commander.vscode_agent
        self.security = self.commander.security_agent
        self.database = self.commander.database_agent
        self.devops = self.commander.devops_agent
        self.learning = self.commander.learning_agent
        
        # Task history for tracking and auditing
        self.task_history = []
    
    def execute_command(self, command_text: str, use_advanced_parsing: bool = True, use_ai: bool = True) -> str:
        """
        Execute a command through the Commander agent with enhanced parsing capabilities.
        
        Args:
            command_text: The text-based command to execute
            use_advanced_parsing: Whether to use advanced parsing (default: True)
            use_ai: Whether to use AI for natural language understanding (default: True)
            
        Returns:
            The result of the command execution
        """
        logger.debug(f"Command Center executing: {command_text}")
        
        # Record this command in history
        self.task_history.append({
            "command": command_text,
            "timestamp": self._get_timestamp()
        })
        
        try:
            # Import here to avoid circular imports
            from ai_service import ai_service
            
            # Execute the command with advanced parsing and AI understanding if enabled
            result = self.commander.execute_command(
                command_text,
                use_advanced_parsing=use_advanced_parsing,
                use_ai=use_ai,
                ai_service=ai_service
            )
        except ImportError:
            # Fallback if ai_service is not available
            logger.warning("AI service not available, falling back to basic parsing")
            result = self.commander.execute_command(command_text, use_advanced_parsing=True, use_ai=False)
        except Exception as e:
            logger.error(f"Error executing command with advanced parsing: {str(e)}")
            # Fallback to basic parsing if advanced parsing fails
            result = self.commander.execute_command(command_text, use_advanced_parsing=False, use_ai=False)
        
        # Update the task history with the result
        self.task_history[-1]["result"] = result[:100] + "..." if len(result) > 100 else result
        
        return result
    
    def agent_to_agent(self, source_agent: str, target_agent: str, 
                        action: str, data: Any) -> Dict[str, Any]:
        """
        Facilitate communication between agents.
        
        Args:
            source_agent: Name of the agent initiating the communication
            target_agent: Name of the agent receiving the communication
            action: The action to perform
            data: Data to pass between agents
            
        Returns:
            Dictionary with the results and any relevant metadata
        """
        logger.debug(f"Agent-to-agent call: {source_agent} -> {target_agent} [{action}]")
        
        try:
            # Validate agent names
            agents = {
                "commander": self.commander,
                "coder": self.coder,
                "researcher": self.researcher,
                "sysadmin": self.sysadmin,
                "memory": self.memory,
                "vscode": self.vscode,
                "security": self.security,
                "database": self.database,
                "devops": self.devops,
                "learning": self.learning
            }
            
            if source_agent not in agents:
                return {"error": f"Unknown source agent: {source_agent}"}
            
            if target_agent not in agents:
                return {"error": f"Unknown target agent: {target_agent}"}
            
            # Handle special multi-agent workflows
            if action == "research_and_code":
                return self._workflow_research_and_code(data)
            
            elif action == "research_and_remember":
                return self._workflow_research_and_remember(data)
            
            elif action == "code_and_execute":
                return self._workflow_code_and_execute(data)
                
            elif action == "vscode_project_setup":
                return self._workflow_vscode_project_setup(data)
                
            elif action == "secure_database_setup":
                return self._workflow_secure_database_setup(data)
                
            elif action == "analyze_and_improve":
                return self._workflow_analyze_and_improve(data)
                
            elif action == "analyze_image":
                return self._workflow_analyze_image(data)
                
            elif action == "generate_image":
                return self._workflow_generate_image(data)
                
            elif action == "visual_code_review":
                return self._workflow_visual_code_review(data)
                
            elif action == "research_with_sources":
                return self._workflow_research_with_sources(data)
                
            elif action == "knowledge_store":
                return self._workflow_knowledge_store(data)
            
            # Direct agent-to-agent calls
            elif target_agent == "coder":
                if action in self.coder.get_commands():
                    args = data.get("args", [])
                    result = self.coder.execute(action, args)
                    return {"result": result}
                else:
                    return {"error": f"Unknown coder action: {action}"}
            
            elif target_agent == "researcher":
                if action in self.researcher.get_commands():
                    args = data.get("args", [])
                    result = self.researcher.execute(action, args)
                    return {"result": result}
                else:
                    return {"error": f"Unknown researcher action: {action}"}
            
            elif target_agent == "sysadmin":
                if action in self.sysadmin.get_commands():
                    args = data.get("args", [])
                    result = self.sysadmin.execute(action, args)
                    return {"result": result}
                else:
                    return {"error": f"Unknown sysadmin action: {action}"}
            
            elif target_agent == "memory":
                if action in self.memory.get_commands():
                    args = data.get("args", [])
                    result = self.memory.execute(action, args)
                    return {"result": result}
                else:
                    return {"error": f"Unknown memory action: {action}"}
            
            elif target_agent == "vscode":
                if action in self.vscode.get_commands():
                    args = data.get("args", [])
                    result = self.vscode.execute(action, args)
                    return {"result": result}
                else:
                    return {"error": f"Unknown vscode action: {action}"}
                    
            elif target_agent == "security":
                if action in self.security.get_commands():
                    args = data.get("args", [])
                    result = self.security.execute(action, args)
                    return {"result": result}
                else:
                    return {"error": f"Unknown security action: {action}"}
                    
            elif target_agent == "database":
                if action in self.database.get_commands():
                    args = data.get("args", [])
                    result = self.database.execute(action, args)
                    return {"result": result}
                else:
                    return {"error": f"Unknown database action: {action}"}
                    
            elif target_agent == "devops":
                if action in self.devops.get_commands():
                    args = data.get("args", [])
                    result = self.devops.execute(action, args)
                    return {"result": result}
                else:
                    return {"error": f"Unknown devops action: {action}"}
                    
            elif target_agent == "learning":
                if action in self.learning.get_commands():
                    args = data.get("args", [])
                    result = self.learning.execute(action, args)
                    return {"result": result}
                else:
                    return {"error": f"Unknown learning action: {action}"}
            
            else:
                return {"error": f"Unsupported action: {action}"}
                
        except Exception as e:
            logger.error(f"Error in agent-to-agent communication: {str(e)}")
            return {"error": f"Error in agent-to-agent communication: {str(e)}"}
    
    def _workflow_research_and_code(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow that involves researching a topic and generating code.
        
        Args:
            data: Dictionary containing query, language, and other parameters
            
        Returns:
            Dictionary with research findings and generated code
        """
        try:
            query = data.get("query")
            language = data.get("language", "python")
            
            if not query:
                return {"error": "Missing query parameter"}
            
            # Step 1: Research the topic
            logger.debug(f"Researching: {query}")
            research_result = self.researcher.execute("summarize", [query])
            
            # Step 2: Use research findings to generate code
            logger.debug(f"Generating code based on research in {language}")
            code_request = f"Code to implement: {query} based on: {research_result[:500]}"
            code_result = self.coder.execute("write", [language, code_request])
            
            # Step 3: Store the results in memory for future reference
            memory_key = f"research_code_{self._generate_key(query)}"
            self.memory.execute("remember", [memory_key, json.dumps({
                "query": query,
                "research": research_result[:1000],
                "code": code_result,
                "language": language
            }), "research_code"])
            
            return {
                "research": research_result,
                "code": code_result,
                "memory_key": memory_key
            }
            
        except Exception as e:
            logger.error(f"Error in research_and_code workflow: {str(e)}")
            return {"error": f"Error in research_and_code workflow: {str(e)}"}
    
    def _workflow_research_and_remember(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow that involves researching a topic and storing the findings.
        
        Args:
            data: Dictionary containing query and category parameters
            
        Returns:
            Dictionary with research findings and memory details
        """
        try:
            query = data.get("query")
            category = data.get("category", "research")
            
            if not query:
                return {"error": "Missing query parameter"}
            
            # Step 1: Research the topic
            logger.debug(f"Researching for memory: {query}")
            if self._is_url(query):
                research_result = self.researcher.execute("scrape", [query])
            else:
                research_result = self.researcher.execute("summarize", [query])
            
            # Step 2: Analyze the content
            analysis_result = self.researcher.execute("analyze", [research_result[:2000]])
            
            # Step 3: Store the results in memory
            memory_key = f"research_{self._generate_key(query)}"
            memory_value = json.dumps({
                "query": query,
                "content": research_result[:2000],
                "analysis": analysis_result
            })
            
            self.memory.execute("remember", [memory_key, memory_value, category])
            
            return {
                "research": research_result[:500] + "...",
                "analysis": analysis_result,
                "memory_key": memory_key,
                "category": category
            }
            
        except Exception as e:
            logger.error(f"Error in research_and_remember workflow: {str(e)}")
            return {"error": f"Error in research_and_remember workflow: {str(e)}"}
    
    def _workflow_code_and_execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow that involves generating code and running it.
        
        Args:
            data: Dictionary containing description and language parameters
            
        Returns:
            Dictionary with generated code and execution results
        """
        try:
            description = data.get("description")
            language = data.get("language", "python")
            
            if not description:
                return {"error": "Missing description parameter"}
            
            # Step 1: Generate code
            logger.debug(f"Generating {language} code for: {description}")
            code_result = self.coder.execute("write", [language, description])
            
            # Extract just the code part (between triple backticks)
            import re
            code_match = re.search(r'```(?:\w+)?\n(.*?)```', code_result, re.DOTALL)
            if code_match:
                code = code_match.group(1)
            else:
                code = code_result
            
            # Step 2: Execute the code (only for Python)
            if language.lower() == "python":
                logger.debug("Executing generated Python code")
                execution_result = self.coder.execute("run", [language, code])
            else:
                execution_result = f"Code execution is only supported for Python. Generated {language} code but did not execute it."
            
            # Step 3: Store in memory
            memory_key = f"code_{language}_{self._generate_key(description)}"
            self.memory.execute("remember", [memory_key, json.dumps({
                "description": description,
                "code": code,
                "execution_result": execution_result,
                "language": language
            }), "code_executions"])
            
            return {
                "code": code_result,
                "execution": execution_result,
                "memory_key": memory_key
            }
            
        except Exception as e:
            logger.error(f"Error in code_and_execute workflow: {str(e)}")
            return {"error": f"Error in code_and_execute workflow: {str(e)}"}
    
    def get_task_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get the recent task history.
        
        Args:
            limit: Maximum number of history items to return
            
        Returns:
            List of recent tasks with their results
        """
        return self.task_history[-limit:] if limit > 0 else self.task_history
    
    def _is_url(self, text: str) -> bool:
        """Check if the given text is a URL."""
        return text.startswith(("http://", "https://"))
    
    def _generate_key(self, text: str) -> str:
        """Generate a simplified key from text."""
        import re
        key = re.sub(r'[^\w]', '_', text.lower())
        key = re.sub(r'_+', '_', key)
        return key[:50]  # Limit length
    
    def _workflow_vscode_project_setup(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow that sets up a VS Code project environment with Linux integrations.
        
        Args:
            data: Dictionary containing project_type, project_name, and other parameters
            
        Returns:
            Dictionary with VS Code setup results and configurations
        """
        try:
            project_type = data.get("project_type", "python")
            project_name = data.get("project_name", "my_project")
            
            if not project_type:
                return {"error": "Missing project_type parameter"}
            
            # Step 1: Get recommended extensions for the project type
            logger.debug(f"Getting recommended extensions for {project_type}")
            extensions_result = self.vscode.execute("recommend-extensions", [project_type])
            
            # Step 2: Create launch configuration based on project type
            logger.debug(f"Creating launch configuration for {project_type}")
            launch_config_name = f"Debug {project_type.capitalize()}"
            
            if project_type.lower() == "python":
                program_path = "app.py"
                launch_result = self.vscode.execute("create-launch", [launch_config_name, "python", program_path])
            elif project_type.lower() in ["node", "javascript", "typescript"]:
                program_path = "index.js"
                launch_result = self.vscode.execute("create-launch", [launch_config_name, "node", program_path])
            else:
                launch_result = f"No predefined launch configuration for {project_type}. Created generic configuration."
                
            # Step 3: Create common project tasks
            logger.debug(f"Creating common tasks for {project_type}")
            if project_type.lower() == "python":
                build_task = self.vscode.execute("create-task", ["test", "python -m pytest"])
                run_task = self.vscode.execute("create-task", ["run", "python app.py"])
            elif project_type.lower() in ["node", "javascript", "typescript"]:
                build_task = self.vscode.execute("create-task", ["build", "npm run build"])
                run_task = self.vscode.execute("create-task", ["start", "npm start"])
            else:
                build_task = self.vscode.execute("create-task", ["build", f"echo 'Building {project_name}...'"])
                run_task = self.vscode.execute("create-task", ["run", f"echo 'Running {project_name}...'"])
                
            # Step 4: Set up Linux terminal integration
            terminal_result = self.vscode.execute("linux-terminal", ["bash", "/bin/bash"])
            
            # Step 5: Store the project setup in memory
            memory_key = f"vscode_project_{self._generate_key(project_name)}"
            self.memory.execute("remember", [memory_key, json.dumps({
                "project_type": project_type,
                "project_name": project_name,
                "extensions": extensions_result,
                "launch_config": launch_result,
                "tasks": {
                    "build": build_task,
                    "run": run_task
                },
                "terminal": terminal_result
            }), "vscode_projects"])
            
            return {
                "project_name": project_name,
                "project_type": project_type,
                "extensions": extensions_result,
                "launch_config": launch_result,
                "tasks": {
                    "build": build_task, 
                    "run": run_task
                },
                "terminal": terminal_result,
                "memory_key": memory_key
            }
            
        except Exception as e:
            logger.error(f"Error in vscode_project_setup workflow: {str(e)}")
            return {"error": f"Error in vscode_project_setup workflow: {str(e)}"}
    
    def _workflow_secure_database_setup(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow that sets up a secure database with security audit.
        
        Args:
            data: Dictionary containing db_type, description, and other parameters
            
        Returns:
            Dictionary with database schema, security audit, and deployment configuration
        """
        try:
            db_type = data.get("db_type", "postgresql")
            description = data.get("description")
            
            if not description:
                return {"error": "Missing database description parameter"}
            
            # Step 1: Generate the database schema
            logger.debug(f"Generating {db_type} schema for: {description}")
            schema_result = self.database.execute("generate-schema", [db_type, description])
            
            # Step 2: Perform a security audit on the generated schema
            logger.debug("Performing security audit on the schema")
            security_audit = self.security.execute("security-audit", [db_type, schema_result])
            
            # Step 3: Create deployment configuration
            logger.debug(f"Generating deployment configuration for {db_type}")
            deployment_config = self.devops.execute("deployment", ["kubernetes", f"{db_type}-database"])
            
            # Step 4: Store results in memory
            memory_key = f"db_setup_{self._generate_key(description)}"
            self.memory.execute("remember", [memory_key, json.dumps({
                "db_type": db_type,
                "description": description,
                "schema": schema_result,
                "security_audit": security_audit,
                "deployment_config": deployment_config
            }), "database_setups"])
            
            return {
                "schema": schema_result,
                "security_audit": security_audit,
                "deployment_config": deployment_config,
                "memory_key": memory_key
            }
            
        except Exception as e:
            logger.error(f"Error in secure_database_setup workflow: {str(e)}")
            return {"error": f"Error in secure_database_setup workflow: {str(e)}"}
    
    def _workflow_analyze_and_improve(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow that analyzes usage patterns and suggests improvements.
        
        Args:
            data: Dictionary containing component and days parameters
            
        Returns:
            Dictionary with analysis results and improvement suggestions
        """
        try:
            component = data.get("component")
            days = data.get("days", 30)
            
            # Step 1: Analyze usage patterns
            logger.debug(f"Analyzing usage patterns for the last {days} days")
            usage_analysis = self.learning.execute("analyze-usage", [str(days)])
            
            # Step 2: Run diagnostics on the specified component (if any)
            if component:
                logger.debug(f"Running diagnostics on component: {component}")
                diagnostic_result = self.learning.execute("diagnose", [component])
            else:
                logger.debug("Running system-wide diagnostics")
                diagnostic_result = self.learning.execute("diagnose", [])
            
            # Step 3: Generate workflow optimization suggestions
            logger.debug("Generating workflow optimization suggestions")
            if component:
                workflow_suggestions = self.learning.execute("optimize-workflows", [component])
            else:
                workflow_suggestions = self.learning.execute("optimize-workflows", [])
            
            # Step 4: Generate an improvement report
            logger.debug("Generating improvement report")
            improvement_report = self.learning.execute("improvement-report", [])
            
            # Step 5: Store analysis in memory
            memory_key = f"system_analysis_{self._get_timestamp()}"
            self.memory.execute("remember", [memory_key, json.dumps({
                "component": component,
                "days_analyzed": days,
                "usage_analysis": usage_analysis,
                "diagnostic_result": diagnostic_result,
                "workflow_suggestions": workflow_suggestions,
                "improvement_report": improvement_report
            }), "system_analysis"])
            
            return {
                "usage_analysis": usage_analysis,
                "diagnostic_result": diagnostic_result,
                "workflow_suggestions": workflow_suggestions,
                "improvement_report": improvement_report,
                "memory_key": memory_key
            }
            
        except Exception as e:
            logger.error(f"Error in analyze_and_improve workflow: {str(e)}")
            return {"error": f"Error in analyze_and_improve workflow: {str(e)}"}
    
    def _get_timestamp(self) -> str:
        """Get a formatted timestamp."""
        from datetime import datetime
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
    def _workflow_analyze_image(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow for image analysis using multimodal AI.
        
        Args:
            data: Dictionary containing image_data (base64) and optional query
            
        Returns:
            Dictionary with analysis results and optional memory reference
        """
        try:
            from ai_service import ai_service
            
            image_data = data.get("image_data")
            query = data.get("query")
            store_in_memory = data.get("store_in_memory", False)
            
            if not image_data:
                return {"error": "Missing image_data parameter"}
                
            # Step 1: Analyze the image
            logger.debug("Analyzing image with multimodal AI")
            analysis_result = ai_service.analyze_image(image_data, query)
            
            result = {
                "analysis": analysis_result
            }
            
            # Step 2: Store in memory if requested
            if store_in_memory:
                memory_key = f"image_analysis_{self._get_timestamp()}"
                memory_data = {
                    "query": query,
                    "analysis": analysis_result,
                    "timestamp": self._get_timestamp()
                }
                
                self.memory.execute("remember", [memory_key, json.dumps(memory_data), "image_analysis"])
                result["memory_key"] = memory_key
                
            return result
            
        except Exception as e:
            logger.error(f"Error in analyze_image workflow: {str(e)}")
            return {"error": f"Error in analyze_image workflow: {str(e)}"}
            
    def _workflow_generate_image(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow for AI image generation.
        
        Args:
            data: Dictionary containing prompt for image generation
            
        Returns:
            Dictionary with generated image URL and optional memory reference
        """
        try:
            from ai_service import ai_service
            
            prompt = data.get("prompt")
            store_in_memory = data.get("store_in_memory", False)
            
            if not prompt:
                return {"error": "Missing prompt parameter"}
                
            # Step 1: Generate the image
            logger.debug(f"Generating image for prompt: {prompt}")
            generation_result = ai_service.generate_image(prompt)
            
            result = {
                "image_url": generation_result.get("url"),
                "prompt": prompt
            }
            
            # Step 2: Store in memory if requested
            if store_in_memory:
                memory_key = f"generated_image_{self._generate_key(prompt)}"
                memory_data = {
                    "prompt": prompt,
                    "image_url": result.get("image_url"),
                    "timestamp": self._get_timestamp()
                }
                
                self.memory.execute("remember", [memory_key, json.dumps(memory_data), "generated_images"])
                result["memory_key"] = memory_key
                
            return result
            
        except Exception as e:
            logger.error(f"Error in generate_image workflow: {str(e)}")
            return {"error": f"Error in generate_image workflow: {str(e)}"}
            
    def _workflow_visual_code_review(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow that uses multimodal AI to review code with visual context.
        
        Args:
            data: Dictionary containing code, language, and optional screenshot
            
        Returns:
            Dictionary with code review results and improvement suggestions
        """
        try:
            from ai_service import ai_service
            
            code = data.get("code")
            language = data.get("language", "python")
            screenshot_data = data.get("screenshot")
            security_focus = data.get("security_focus", False)
            
            if not code:
                return {"error": "Missing code parameter"}
                
            # Step 1: Perform static code analysis
            logger.debug(f"Analyzing {language} code")
            analysis_type = "security" if security_focus else "general"
            code_analysis = ai_service.analyze_code(language, code, analysis_type)
            
            # Step 2: Generate improvement suggestions
            logger.debug("Generating code improvement suggestions")
            suggestions = ai_service.suggest_improvements(language, code)
            
            result = {
                "code_analysis": code_analysis,
                "improvement_suggestions": suggestions
            }
            
            # Step 3: If screenshot provided, do visual analysis
            if screenshot_data:
                logger.debug("Performing visual code analysis with screenshot")
                visual_query = f"Analyze this screenshot showing {language} code. The code is:\n\n{code[:500]}...\n\nIdentify any visual issues or improvements that aren't visible in the text alone."
                visual_analysis = ai_service.analyze_image(screenshot_data, visual_query)
                result["visual_analysis"] = visual_analysis
            
            return result
            
        except Exception as e:
            logger.error(f"Error in visual_code_review workflow: {str(e)}")
            return {"error": f"Error in visual_code_review workflow: {str(e)}"}
            
    def _workflow_research_with_sources(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow that researches a topic and provides answers with citations.
        
        Args:
            data: Dictionary containing query and optional context_urls
            
        Returns:
            Dictionary with research results and citations
        """
        try:
            from ai_service import ai_service
            
            query = data.get("query")
            context_urls = data.get("context_urls", [])
            store_in_memory = data.get("store_in_memory", False)
            
            if not query:
                return {"error": "Missing query parameter"}
                
            # Step 1: Collect sources from URLs if provided
            context_sources = []
            
            if context_urls:
                logger.debug(f"Collecting {len(context_urls)} sources for research")
                for i, url in enumerate(context_urls):
                    if self._is_url(url):
                        content = self.researcher.execute("scrape", [url])
                        context_sources.append({
                            "title": f"Source from {url}",
                            "content": content[:4000],  # Limit size
                            "url": url
                        })
            
            # Step 2: If not enough sources from URLs, use research agent to find more
            if len(context_sources) < 3:
                logger.debug("Finding additional sources through research")
                research_results = self.researcher.execute("search", [query])
                
                # Parse research results and add as sources
                try:
                    research_data = json.loads(research_results)
                    for result in research_data.get("results", [])[:3]:
                        if "title" in result and "content" in result:
                            context_sources.append({
                                "title": result["title"],
                                "content": result["content"][:4000],
                                "url": result.get("url", "")
                            })
                except:
                    # Fallback if parsing fails
                    context_sources.append({
                        "title": "General Research Results",
                        "content": research_results[:4000],
                        "url": ""
                    })
            
            # Step 3: Generate answer with sources
            logger.debug(f"Generating answer with {len(context_sources)} sources")
            answer = ai_service.answer_with_sources(query, context_sources)
            
            result = {
                "answer": answer,
                "sources_count": len(context_sources)
            }
            
            # Step 4: Store in memory if requested
            if store_in_memory:
                memory_key = f"research_sources_{self._generate_key(query)}"
                memory_data = {
                    "query": query,
                    "answer": answer,
                    "sources": [{"title": s["title"], "url": s["url"]} for s in context_sources],
                    "timestamp": self._get_timestamp()
                }
                
                self.memory.execute("remember", [memory_key, json.dumps(memory_data), "research_with_sources"])
                result["memory_key"] = memory_key
                
            return result
            
        except Exception as e:
            logger.error(f"Error in research_with_sources workflow: {str(e)}")
            return {"error": f"Error in research_with_sources workflow: {str(e)}"}
            
    def _workflow_knowledge_store(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow that manages the knowledge store.
        
        Args:
            data: Dictionary containing action (store/retrieve/search) and related parameters
            
        Returns:
            Dictionary with operation results
        """
        try:
            from ai_service import ai_service
            
            action = data.get("action")
            
            if not action:
                return {"error": "Missing action parameter"}
                
            if action == "store":
                key = data.get("key")
                content = data.get("content")
                metadata = data.get("metadata", {})
                
                if not key or not content:
                    return {"error": "Missing key or content parameters for store action"}
                
                store_result = ai_service.store_knowledge(key, content, metadata)
                return {"result": store_result, "action": "store", "key": key}
                
            elif action == "retrieve":
                key = data.get("key")
                
                if not key:
                    return {"error": "Missing key parameter for retrieve action"}
                
                content = ai_service.retrieve_knowledge(key)
                return {"result": content, "action": "retrieve", "key": key}
                
            elif action == "search":
                query = data.get("query")
                limit = data.get("limit", 5)
                
                if not query:
                    return {"error": "Missing query parameter for search action"}
                
                search_results = ai_service.search_knowledge(query, limit)
                return {
                    "results": search_results, 
                    "action": "search", 
                    "query": query,
                    "count": len(search_results)
                }
                
            else:
                return {"error": f"Unsupported knowledge store action: {action}"}
                
        except Exception as e:
            logger.error(f"Error in knowledge_store workflow: {str(e)}")
            return {"error": f"Error in knowledge_store workflow: {str(e)}"}

# Initialize the command center
command_center = CommandCenter()