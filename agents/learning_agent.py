import os
import re
import logging
import json
import datetime
from typing import List, Dict, Any, Optional
from collections import Counter, defaultdict
from agents.base_agent import BaseAgent
from ai_service import ai_service

# Set up logging
logger = logging.getLogger(__name__)

class LearningAgent(BaseAgent):
    """
    The Learning Agent - specialized in improving agent performance through feedback and analysis.
    
    This agent can help with tasks like:
    - Analyzing usage patterns to improve recommendations
    - Learning from user feedback to enhance responses
    - Identifying common pain points and improvement areas
    - Implementing self-diagnostic capabilities
    - Optimizing the agent for specific user workflows
    """
    
    def __init__(self):
        """Initialize the Learning Agent."""
        super().__init__(
            name="LearningAgent",
            description="Specialized in improving agent performance through feedback and analysis."
        )
        self.usage_history = []
        self.feedback_history = []
        self.improvement_suggestions = []
        self.last_analysis_date = None
        self.load_history()
        
    def get_commands(self):
        """Return the commands this agent can handle."""
        return {
            "analyze-usage": {
                "description": "Analyze command usage patterns to improve recommendations",
                "usage": "analyze-usage [days]",
                "examples": [
                    "analyze-usage",
                    "analyze-usage 30"
                ]
            },
            "add-feedback": {
                "description": "Add user feedback about a command or response",
                "usage": "add-feedback <command> <rating> [comment]",
                "examples": [
                    "add-feedback 'security scan-code main.py' 5 'Very helpful output'",
                    "add-feedback 'vscode setup python' 3 'Could include more detail'"
                ]
            },
            "diagnose": {
                "description": "Run self-diagnostic to identify improvement areas",
                "usage": "diagnose [component]",
                "examples": [
                    "diagnose",
                    "diagnose security-agent"
                ]
            },
            "improvement-report": {
                "description": "Generate a report of improvement suggestions",
                "usage": "improvement-report [priority]",
                "examples": [
                    "improvement-report",
                    "improvement-report high"
                ]
            },
            "optimize-workflows": {
                "description": "Suggest workflow optimizations based on usage patterns",
                "usage": "optimize-workflows [workflow_type]",
                "examples": [
                    "optimize-workflows",
                    "optimize-workflows security"
                ]
            }
        }
    
    def execute(self, command, args):
        """Execute a LearningAgent command."""
        try:
            if command == "analyze-usage":
                days = 30  # Default to last 30 days
                if args and args[0].isdigit():
                    days = int(args[0])
                return self._analyze_usage(days)
                
            elif command == "add-feedback":
                if len(args) < 2:
                    return "Error: Missing required arguments. Usage: add-feedback <command> <rating> [comment]"
                
                cmd = args[0]
                try:
                    rating = int(args[1])
                    if rating < 1 or rating > 5:
                        return "Error: Rating must be between 1 and 5"
                except ValueError:
                    return "Error: Rating must be a number between 1 and 5"
                
                comment = " ".join(args[2:]) if len(args) > 2 else ""
                return self._add_feedback(cmd, rating, comment)
                
            elif command == "diagnose":
                component = args[0] if args else None
                return self._diagnose(component)
                
            elif command == "improvement-report":
                priority = args[0] if args else None
                return self._improvement_report(priority)
                
            elif command == "optimize-workflows":
                workflow_type = args[0] if args else None
                return self._optimize_workflows(workflow_type)
                
            else:
                return f"Unknown command: '{command}'"
                
        except Exception as e:
            logger.error(f"Error in LearningAgent: {str(e)}")
            return f"Error executing command: {str(e)}"
    
    def record_usage(self, command, agent, success, execution_time):
        """
        Record command usage for analysis.
        
        Args:
            command: The command executed
            agent: The agent that executed the command
            success: Whether the command was successful
            execution_time: The time taken to execute the command in seconds
        """
        usage_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "command": command,
            "agent": agent,
            "success": success,
            "execution_time": execution_time
        }
        
        self.usage_history.append(usage_entry)
        self.save_history()
        logger.debug(f"Recorded usage: {command} by {agent} (success: {success})")
        
    def load_history(self):
        """Load usage and feedback history from files."""
        try:
            # Usage history
            if os.path.exists("data/usage_history.json"):
                with open("data/usage_history.json", "r") as f:
                    self.usage_history = json.load(f)
                logger.info(f"Loaded {len(self.usage_history)} usage history entries")
            
            # Feedback history
            if os.path.exists("data/feedback_history.json"):
                with open("data/feedback_history.json", "r") as f:
                    self.feedback_history = json.load(f)
                logger.info(f"Loaded {len(self.feedback_history)} feedback history entries")
            
            # Improvement suggestions
            if os.path.exists("data/improvement_suggestions.json"):
                with open("data/improvement_suggestions.json", "r") as f:
                    self.improvement_suggestions = json.load(f)
                logger.info(f"Loaded {len(self.improvement_suggestions)} improvement suggestions")
                
        except Exception as e:
            logger.error(f"Error loading history: {str(e)}")
    
    def save_history(self):
        """Save usage and feedback history to files."""
        try:
            # Ensure data directory exists
            os.makedirs("data", exist_ok=True)
            
            # Usage history
            with open("data/usage_history.json", "w") as f:
                json.dump(self.usage_history, f, indent=2)
            
            # Feedback history
            with open("data/feedback_history.json", "w") as f:
                json.dump(self.feedback_history, f, indent=2)
            
            # Improvement suggestions
            with open("data/improvement_suggestions.json", "w") as f:
                json.dump(self.improvement_suggestions, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving history: {str(e)}")
    
    def _analyze_usage(self, days):
        """
        Analyze command usage patterns.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Analysis report
        """
        try:
            # Calculate cutoff date
            cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
            
            # Filter usage history by date
            recent_usage = [entry for entry in self.usage_history if entry["timestamp"] >= cutoff_date]
            
            if not recent_usage:
                return f"No usage data found for the last {days} days."
            
            # Extract basic statistics
            total_commands = len(recent_usage)
            successful_commands = sum(1 for entry in recent_usage if entry["success"])
            success_rate = (successful_commands / total_commands) * 100 if total_commands > 0 else 0
            
            # Analyze command popularity
            command_counter = Counter()
            agent_counter = Counter()
            command_time = defaultdict(list)
            command_success = defaultdict(list)
            
            for entry in recent_usage:
                cmd = entry["command"].split()[0] if entry["command"].split() else "unknown"
                command_counter[cmd] += 1
                agent_counter[entry["agent"]] += 1
                command_time[cmd].append(entry["execution_time"])
                command_success[cmd].append(1 if entry["success"] else 0)
            
            # Most popular commands
            popular_commands = command_counter.most_common(5)
            
            # Most used agents
            popular_agents = agent_counter.most_common(5)
            
            # Command success rates
            command_success_rates = {}
            for cmd, successes in command_success.items():
                if successes:
                    command_success_rates[cmd] = (sum(successes) / len(successes)) * 100
            
            # Command average execution times
            command_avg_times = {}
            for cmd, times in command_time.items():
                if times:
                    command_avg_times[cmd] = sum(times) / len(times)
            
            # Format results
            result = f"Usage Analysis Report (Last {days} Days)\n\n"
            result += f"Total Commands Executed: {total_commands}\n"
            result += f"Overall Success Rate: {success_rate:.2f}%\n\n"
            
            result += "Most Popular Commands:\n"
            for cmd, count in popular_commands:
                success_rate = command_success_rates.get(cmd, 0)
                avg_time = command_avg_times.get(cmd, 0)
                result += f"- {cmd}: {count} uses (Success Rate: {success_rate:.2f}%, Avg Time: {avg_time:.2f}s)\n"
            
            result += "\nMost Used Agents:\n"
            for agent, count in popular_agents:
                result += f"- {agent}: {count} uses\n"
            
            # Generate optimization suggestions
            result += "\nOptimization Suggestions:\n"
            
            # Find commands with low success rates
            low_success_commands = [cmd for cmd, rate in command_success_rates.items() if rate < 80]
            if low_success_commands:
                result += "- Commands with low success rates that may need improvement:\n"
                for cmd in low_success_commands:
                    result += f"  * {cmd} ({command_success_rates[cmd]:.2f}% success rate)\n"
            
            # Find slow commands
            slow_commands = [cmd for cmd, time in command_avg_times.items() if time > 2.0]
            if slow_commands:
                result += "- Commands with long execution times that may need optimization:\n"
                for cmd in slow_commands:
                    result += f"  * {cmd} ({command_avg_times[cmd]:.2f}s average)\n"
            
            # Check for unused commands/agents
            # (This would require comparing with a list of all available commands)
            
            # Store the analysis date
            self.last_analysis_date = datetime.datetime.now().isoformat()
            
            # Try using AI Service for deeper insights if available
            try:
                if 'claude' in ai_service.models:
                    usage_data = {
                        "total_commands": total_commands,
                        "success_rate": success_rate,
                        "popular_commands": popular_commands,
                        "popular_agents": popular_agents,
                        "command_success_rates": command_success_rates,
                        "command_avg_times": command_avg_times
                    }
                    
                    system_prompt = """
                    You are a usage pattern analyst specializing in AI assistant systems.
                    Analyze the provided usage data and generate actionable insights that could improve the system.
                    Focus on:
                    
                    1. Patterns in command usage
                    2. Potential bottlenecks or pain points
                    3. Opportunities for automation or workflow improvements
                    4. Command success rates and execution times
                    5. User preference patterns
                    
                    Provide 3-5 specific, actionable recommendations based on the data.
                    """
                    
                    logger.debug(f"Using AI Service to analyze usage patterns")
                    response = ai_service.models['claude'].messages.create(
                        model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": f"Please analyze this usage data from our command-line assistant and provide insights:\n{json.dumps(usage_data, indent=2)}"}
                        ],
                        temperature=0.1,
                        max_tokens=1500
                    )
                    ai_insights = response.content[0].text
                    
                    result += "\nAI-Generated Insights:\n" + ai_insights
            except Exception as ai_err:
                logger.warning(f"AI Service usage pattern analysis failed: {str(ai_err)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing usage: {str(e)}")
            return f"Error analyzing usage: {str(e)}"
    
    def _add_feedback(self, command, rating, comment):
        """
        Add user feedback about a command or response.
        
        Args:
            command: The command that was executed
            rating: A rating from 1 to 5
            comment: Optional comment with feedback
            
        Returns:
            Confirmation message
        """
        try:
            feedback_entry = {
                "timestamp": datetime.datetime.now().isoformat(),
                "command": command,
                "rating": rating,
                "comment": comment
            }
            
            self.feedback_history.append(feedback_entry)
            self.save_history()
            
            result = f"Thank you for your feedback! Rating of {rating}/5 recorded for command: {command}"
            
            if rating <= 3 and comment:
                # Generate potential improvement based on feedback
                improvement = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "source": "user_feedback",
                    "command": command,
                    "rating": rating,
                    "feedback": comment,
                    "suggestion": f"Improve output for '{command}' based on user feedback: '{comment}'",
                    "status": "open",
                    "priority": "medium" if rating <= 2 else "low"
                }
                
                self.improvement_suggestions.append(improvement)
                self.save_history()
                
                result += "\n\nYour feedback has been added to our improvement queue."
            
            return result
            
        except Exception as e:
            logger.error(f"Error adding feedback: {str(e)}")
            return f"Error adding feedback: {str(e)}"
    
    def _diagnose(self, component=None):
        """
        Run self-diagnostic to identify improvement areas.
        
        Args:
            component: Optional component to diagnose
            
        Returns:
            Diagnostic report
        """
        try:
            result = "Self-Diagnostic Report\n\n"
            
            # Starting with usage analysis
            # Calculate success rates by agent/component
            component_success = defaultdict(list)
            component_time = defaultdict(list)
            
            # Use recent data (last 30 days)
            cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat()
            recent_usage = [entry for entry in self.usage_history if entry["timestamp"] >= cutoff_date]
            
            for entry in recent_usage:
                component_name = entry["agent"]
                if component and component.lower() != component_name.lower():
                    continue
                
                component_success[component_name].append(1 if entry["success"] else 0)
                component_time[component_name].append(entry["execution_time"])
            
            # Check if we have data for the requested component
            if component and not component_success:
                return f"No diagnostic data available for component: {component}"
            
            # Calculate success rates and performance metrics
            success_rates = {}
            avg_times = {}
            
            for comp, successes in component_success.items():
                if successes:
                    success_rates[comp] = (sum(successes) / len(successes)) * 100
                    
            for comp, times in component_time.items():
                if times:
                    avg_times[comp] = sum(times) / len(times)
            
            # Generate report based on components
            if component:
                # Detailed report for a specific component
                result += f"Component: {component}\n"
                result += f"Success Rate: {success_rates.get(component, 0):.2f}%\n"
                result += f"Average Execution Time: {avg_times.get(component, 0):.2f}s\n\n"
                
                # Check command-specific statistics for this component
                cmd_success = defaultdict(list)
                cmd_time = defaultdict(list)
                
                for entry in recent_usage:
                    if entry["agent"] == component:
                        cmd = entry["command"].split()[0] if entry["command"].split() else "unknown"
                        cmd_success[cmd].append(1 if entry["success"] else 0)
                        cmd_time[cmd].append(entry["execution_time"])
                
                result += "Command Performance:\n"
                for cmd in cmd_success:
                    if cmd_success[cmd]:
                        cmd_success_rate = (sum(cmd_success[cmd]) / len(cmd_success[cmd])) * 100
                        cmd_avg_time = sum(cmd_time[cmd]) / len(cmd_time[cmd]) if cmd_time[cmd] else 0
                        result += f"- {cmd}: {cmd_success_rate:.2f}% success, {cmd_avg_time:.2f}s average time\n"
                
                # User feedback for this component
                comp_feedback = [entry for entry in self.feedback_history if component.lower() in entry["command"].lower()]
                if comp_feedback:
                    total_rating = sum(entry["rating"] for entry in comp_feedback)
                    avg_rating = total_rating / len(comp_feedback)
                    result += f"\nUser Feedback: {avg_rating:.1f}/5 average rating ({len(comp_feedback)} ratings)\n"
                    
                    # Show recent feedback comments
                    recent_comments = [entry for entry in comp_feedback if entry["comment"]][-3:]
                    if recent_comments:
                        result += "Recent feedback comments:\n"
                        for entry in recent_comments:
                            result += f"- \"{entry['comment']}\" (Rating: {entry['rating']}/5)\n"
            else:
                # Overview report for all components
                result += "Component Success Rates:\n"
                for comp, rate in success_rates.items():
                    result += f"- {comp}: {rate:.2f}%\n"
                
                result += "\nComponent Performance:\n"
                for comp, time in avg_times.items():
                    result += f"- {comp}: {time:.2f}s average execution time\n"
                
                # Overall system health
                overall_success = sum(success_rates.values()) / len(success_rates) if success_rates else 0
                result += f"\nOverall System Health: {overall_success:.2f}% success rate\n"
                
                # Check for components that need attention
                attention_needed = [comp for comp, rate in success_rates.items() if rate < 85]
                if attention_needed:
                    result += "\nComponents that may need attention:\n"
                    for comp in attention_needed:
                        result += f"- {comp}: {success_rates[comp]:.2f}% success rate\n"
            
            # Add diagnostic recommendations
            result += "\nDiagnostic Recommendations:\n"
            
            # Calculate threshold values for warnings
            success_threshold = 85.0  # Below this success rate, suggest investigation
            time_threshold = 2.0  # Above this average time, suggest optimization
            
            # Generate component-specific recommendations
            if component:
                comp_success_rate = success_rates.get(component, 0)
                comp_avg_time = avg_times.get(component, 0)
                
                if comp_success_rate < success_threshold:
                    result += f"- Success rate is below target ({comp_success_rate:.2f}% vs {success_threshold:.2f}% target)\n"
                    result += "  * Review error logs to identify common failure patterns\n"
                    result += "  * Consider adding more error handling and validation\n"
                
                if comp_avg_time > time_threshold:
                    result += f"- Execution time is above target ({comp_avg_time:.2f}s vs {time_threshold:.2f}s target)\n"
                    result += "  * Profile the component to identify bottlenecks\n"
                    result += "  * Consider optimizing slow operations or adding caching\n"
                
                # Check for commands with low success rates
                problem_commands = [cmd for cmd, successes in cmd_success.items() 
                                    if successes and (sum(successes) / len(successes)) * 100 < success_threshold]
                if problem_commands:
                    result += "- Commands with low success rates:\n"
                    for cmd in problem_commands:
                        rate = (sum(cmd_success[cmd]) / len(cmd_success[cmd])) * 100
                        result += f"  * {cmd}: {rate:.2f}% success rate\n"
            else:
                # General system recommendations
                if overall_success < success_threshold:
                    result += "- Overall system success rate is below target\n"
                    result += "  * Prioritize fixing components with the lowest success rates\n"
                    result += "  * Consider implementing better error handling across the system\n"
                
                slow_components = [comp for comp, time in avg_times.items() if time > time_threshold]
                if slow_components:
                    result += "- Components with performance issues:\n"
                    for comp in slow_components:
                        result += f"  * {comp}: {avg_times[comp]:.2f}s average execution time\n"
            
            # Try using AI Service for more insightful diagnostic recommendations
            try:
                if 'claude' in ai_service.models:
                    diagnostic_data = {
                        "success_rates": success_rates,
                        "avg_times": avg_times,
                        "component": component,
                        "feedback": [(entry["command"], entry["rating"], entry["comment"]) 
                                    for entry in self.feedback_history if not component or component.lower() in entry["command"].lower()]
                    }
                    
                    system_prompt = """
                    You are a system diagnostics expert specializing in AI assistant systems.
                    Analyze the provided diagnostic data and generate actionable recommendations.
                    Focus on:
                    
                    1. Areas with low success rates or high execution times
                    2. Patterns in user feedback that indicate issues
                    3. Specific improvements that could be made
                    4. Prioritization of fixes based on impact
                    5. Potential root causes of identified issues
                    
                    Provide specific, technical recommendations that would improve the system.
                    """
                    
                    logger.debug(f"Using AI Service to enhance diagnostics")
                    response = ai_service.models['claude'].messages.create(
                        model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": f"Please analyze this diagnostic data from our AI assistant system and provide recommendations:\n{json.dumps(diagnostic_data, indent=2)}"}
                        ],
                        temperature=0.1,
                        max_tokens=1500
                    )
                    ai_recommendations = response.content[0].text
                    
                    result += "\nAI-Generated Diagnostic Recommendations:\n" + ai_recommendations
            except Exception as ai_err:
                logger.warning(f"AI Service diagnostic enhancement failed: {str(ai_err)}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error running diagnostics: {str(e)}")
            return f"Error running diagnostics: {str(e)}"
    
    def _improvement_report(self, priority=None):
        """
        Generate a report of improvement suggestions.
        
        Args:
            priority: Optional priority filter (high, medium, low)
            
        Returns:
            Improvement suggestions report
        """
        try:
            # Filter by priority if specified
            if priority:
                priority = priority.lower()
                if priority not in ["high", "medium", "low"]:
                    return f"Invalid priority: {priority}. Valid values are: high, medium, low"
                
                filtered_suggestions = [s for s in self.improvement_suggestions if s["priority"] == priority]
            else:
                filtered_suggestions = self.improvement_suggestions
            
            if not filtered_suggestions:
                return "No improvement suggestions found with the specified criteria."
            
            # Sort by priority (high > medium > low) and then by timestamp (newest first)
            priority_order = {"high": 0, "medium": 1, "low": 2}
            sorted_suggestions = sorted(
                filtered_suggestions,
                key=lambda s: (priority_order.get(s["priority"], 3), s["timestamp"]),
                reverse=True
            )
            
            result = "Improvement Suggestions Report\n\n"
            
            if priority:
                result += f"Priority: {priority.upper()}\n\n"
            
            # Group by status
            status_groups = defaultdict(list)
            for suggestion in sorted_suggestions:
                status_groups[suggestion["status"]].append(suggestion)
            
            # Open suggestions first
            if "open" in status_groups:
                result += "OPEN ITEMS:\n"
                for i, suggestion in enumerate(status_groups["open"], 1):
                    result += f"{i}. [{suggestion['priority'].upper()}] {suggestion['suggestion']}\n"
                    result += f"   Source: {suggestion['source']}, Date: {suggestion['timestamp'][:10]}\n"
                    if "feedback" in suggestion and suggestion["feedback"]:
                        result += f"   Feedback: \"{suggestion['feedback']}\"\n"
                    result += "\n"
            
            # In progress suggestions
            if "in_progress" in status_groups:
                result += "IN PROGRESS:\n"
                for i, suggestion in enumerate(status_groups["in_progress"], 1):
                    result += f"{i}. [{suggestion['priority'].upper()}] {suggestion['suggestion']}\n"
                    result += f"   Source: {suggestion['source']}, Date: {suggestion['timestamp'][:10]}\n"
                    if "feedback" in suggestion and suggestion["feedback"]:
                        result += f"   Feedback: \"{suggestion['feedback']}\"\n"
                    result += "\n"
            
            # Completed suggestions
            if "completed" in status_groups:
                result += "COMPLETED:\n"
                for i, suggestion in enumerate(status_groups["completed"], 1):
                    result += f"{i}. [{suggestion['priority'].upper()}] {suggestion['suggestion']}\n"
                    result += f"   Source: {suggestion['source']}, Date: {suggestion['timestamp'][:10]}\n"
                    if "completion_date" in suggestion:
                        result += f"   Completed: {suggestion['completion_date'][:10]}\n"
                    result += "\n"
            
            # Generate summary statistics
            total = len(sorted_suggestions)
            open_count = len(status_groups.get("open", []))
            in_progress_count = len(status_groups.get("in_progress", []))
            completed_count = len(status_groups.get("completed", []))
            
            high_priority = sum(1 for s in sorted_suggestions if s["priority"] == "high")
            medium_priority = sum(1 for s in sorted_suggestions if s["priority"] == "medium")
            low_priority = sum(1 for s in sorted_suggestions if s["priority"] == "low")
            
            result += "SUMMARY:\n"
            result += f"Total Suggestions: {total}\n"
            result += f"Status: {open_count} Open, {in_progress_count} In Progress, {completed_count} Completed\n"
            result += f"Priority: {high_priority} High, {medium_priority} Medium, {low_priority} Low\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating improvement report: {str(e)}")
            return f"Error generating improvement report: {str(e)}"
    
    def _optimize_workflows(self, workflow_type=None):
        """
        Suggest workflow optimizations based on usage patterns.
        
        Args:
            workflow_type: Optional workflow type to optimize
            
        Returns:
            Workflow optimization suggestions
        """
        try:
            # Analyze recent usage to identify workflow patterns
            cutoff_date = (datetime.datetime.now() - datetime.timedelta(days=30)).isoformat()
            recent_usage = [entry for entry in self.usage_history if entry["timestamp"] >= cutoff_date]
            
            if not recent_usage:
                return "No recent usage data available for workflow optimization."
            
            # Group usage by user sessions
            # Assume a session gap of 10 minutes (600 seconds)
            session_gap = 600
            session_commands = []
            current_session = []
            last_timestamp = None
            
            for entry in sorted(recent_usage, key=lambda x: x["timestamp"]):
                current_time = datetime.datetime.fromisoformat(entry["timestamp"])
                
                if last_timestamp and (current_time - last_timestamp).total_seconds() > session_gap:
                    # New session
                    if current_session:
                        session_commands.append(current_session)
                    current_session = [entry]
                else:
                    current_session.append(entry)
                
                last_timestamp = current_time
            
            # Add the last session
            if current_session:
                session_commands.append(current_session)
            
            # Filter sessions by workflow type if specified
            if workflow_type:
                workflow_type = workflow_type.lower()
                filtered_sessions = []
                for session in session_commands:
                    session_contains_type = any(workflow_type in entry["command"].lower() for entry in session)
                    if session_contains_type:
                        filtered_sessions.append(session)
                
                session_commands = filtered_sessions
            
            if not session_commands:
                return f"No workflow data found{'for ' + workflow_type if workflow_type else ''}."
            
            # Analyze common command sequences
            command_sequences = []
            for session in session_commands:
                if len(session) > 1:
                    # Extract just the command names (not the full commands with arguments)
                    sequence = [entry["command"].split()[0] if entry["command"].split() else "unknown" for entry in session]
                    command_sequences.append(sequence)
            
            # Find common subsequences (potential workflows)
            common_sequences = self._find_common_subsequences(command_sequences)
            
            # Format results
            result = "Workflow Optimization Suggestions\n\n"
            
            if workflow_type:
                result += f"Workflow Type: {workflow_type}\n\n"
            
            result += f"Analyzed {len(session_commands)} user sessions with {len(recent_usage)} commands\n\n"
            
            if common_sequences:
                result += "Common Command Sequences:\n"
                for seq, count in common_sequences.items():
                    if count > 1:  # Only show sequences that appear multiple times
                        result += f"- Sequence (used {count} times): {' → '.join(seq)}\n"
            else:
                result += "No common command sequences identified.\n"
            
            # Try using AI Service for workflow optimization suggestions
            try:
                if 'claude' in ai_service.models:
                    workflow_data = {
                        "sessions": [[entry["command"] for entry in session] for session in session_commands],
                        "common_sequences": {' → '.join(seq): count for seq, count in common_sequences.items() if count > 1},
                        "workflow_type": workflow_type
                    }
                    
                    system_prompt = """
                    You are a workflow optimization expert specializing in AI assistant systems.
                    Analyze the provided command sessions and suggest ways to optimize user workflows.
                    Focus on:
                    
                    1. Common patterns that could be automated or simplified
                    2. Frequently repeated sequences that could be turned into single commands
                    3. Pain points where users might be struggling (repeated failed commands)
                    4. Natural breakpoints that suggest potential workflow divisions
                    5. Command combinations that could be more efficient
                    
                    Provide specific recommendations for workflow optimization, including:
                    - New command suggestions that would automate common sequences
                    - UI improvements that would streamline workflows
                    - Default parameter suggestions that would reduce typing
                    """
                    
                    logger.debug(f"Using AI Service to optimize workflows")
                    response = ai_service.models['claude'].messages.create(
                        model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": f"Please analyze these command sessions and suggest workflow optimizations:\n{json.dumps(workflow_data, indent=2)}"}
                        ],
                        temperature=0.1,
                        max_tokens=1500
                    )
                    ai_suggestions = response.content[0].text
                    
                    result += "\nAI-Generated Workflow Optimization Suggestions:\n" + ai_suggestions
            except Exception as ai_err:
                logger.warning(f"AI Service workflow optimization failed: {str(ai_err)}")
            
            # Basic workflow suggestions as fallback
            if not 'claude' in ai_service.models:
                result += "\nWorkflow Optimization Suggestions:\n"
                
                if common_sequences:
                    top_sequences = sorted(common_sequences.items(), key=lambda x: len(x[0]) * x[1], reverse=True)[:3]
                    for seq, count in top_sequences:
                        if count > 1 and len(seq) >= 2:
                            result += f"- Consider creating a combined command or shortcut for the sequence: {' → '.join(seq)}\n"
                            result += f"  This sequence appears {count} times in the analyzed sessions.\n"
                
                result += "\nGeneral Optimization Tips:\n"
                result += "- Create aliases for frequently used commands\n"
                result += "- Use tab completion to speed up command entry\n"
                result += "- Document common workflows for reference\n"
                result += "- Use history recall (up arrow) to repeat commands\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error optimizing workflows: {str(e)}")
            return f"Error optimizing workflows: {str(e)}"
    
    def _find_common_subsequences(self, sequences, min_length=2, min_count=2):
        """Find common subsequences in a list of sequences."""
        subsequence_counts = defaultdict(int)
        
        for sequence in sequences:
            # Generate all possible subsequences of minimum length
            for i in range(len(sequence) - min_length + 1):
                for j in range(i + min_length, len(sequence) + 1):
                    subseq = tuple(sequence[i:j])
                    subsequence_counts[subseq] += 1
        
        # Filter by minimum count
        common_subseqs = {seq: count for seq, count in subsequence_counts.items() if count >= min_count}
        
        return common_subseqs
        
    def add_improvement_suggestion(self, suggestion, source, priority="medium", feedback=None):
        """
        Add a new improvement suggestion.
        
        Args:
            suggestion: The improvement suggestion text
            source: Source of the suggestion (e.g., 'user_feedback', 'diagnostics')
            priority: Priority level (high, medium, low)
            feedback: Optional feedback text
            
        Returns:
            True if suggestion was added successfully, False otherwise
        """
        try:
            improvement = {
                "timestamp": datetime.datetime.now().isoformat(),
                "source": source,
                "suggestion": suggestion,
                "status": "open",
                "priority": priority.lower()
            }
            
            if feedback:
                improvement["feedback"] = feedback
            
            self.improvement_suggestions.append(improvement)
            self.save_history()
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding improvement suggestion: {str(e)}")
            return False