import re
import logging
import os
from tools import FileSystemTool, TerminalTool, ApiTool
from utils import parse_command, format_response
from agents.coder_agent import CoderAgent
from agents.researcher_agent import ResearcherAgent
from agents.sysadmin_agent import SysAdminAgent
from agents.memorykeeper_agent import MemoryKeeperAgent
from agents.vscode_agent import VSCodeAgent
from agents.security_agent import SecurityAgent
from agents.database_agent import DatabaseAgent
from agents.devops_agent import DevOpsAgent
from agents.learning_agent import LearningAgent

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Commander:
    """
    The Commander AI Agent for Replit
    
    This agent can execute various commands through a text-based interface, 
    utilizing tools like filesystem operations, terminal commands, and API calls.
    It also manages specialized sub-agents (soldiers) for specific tasks.
    """
    
    def __init__(self):
        """Initialize the Commander agent with its tools and sub-agents."""
        logger.debug("Initializing Commander agent")
        self.name = "The Commander"
        self.version = "1.0.0"
        
        # Initialize core tools
        self.file_tool = FileSystemTool()
        self.terminal_tool = TerminalTool()
        self.api_tool = ApiTool()
        
        # Initialize specialized sub-agents
        self.coder_agent = CoderAgent()
        self.researcher_agent = ResearcherAgent()
        self.sysadmin_agent = SysAdminAgent()
        # Initialize MemoryKeeper with database URL if available
        self.memorykeeper_agent = MemoryKeeperAgent(db_url=os.environ.get("DATABASE_URL"))
        # Initialize VSCode agent for VS Code and Linux integration
        self.vscode_agent = VSCodeAgent()
        # Initialize Security agent for vulnerability detection
        self.security_agent = SecurityAgent()
        # Initialize Database agent for database operations
        self.database_agent = DatabaseAgent()
        # Initialize DevOps agent for automation and deployment
        self.devops_agent = DevOpsAgent()
        # Initialize Learning agent for pattern analysis and improvement
        self.learning_agent = LearningAgent()
        
        # Track all available sub-agents
        self.agents = {
            "coder": self.coder_agent,
            "researcher": self.researcher_agent,
            "sysadmin": self.sysadmin_agent,
            "memory": self.memorykeeper_agent,
            "vscode": self.vscode_agent,
            "security": self.security_agent,
            "database": self.database_agent,
            "devops": self.devops_agent,
            "learning": self.learning_agent
        }
        
        # Command registry with help text
        self.commands = {
            "help": {
                "description": "Display available commands and their usage",
                "usage": "help [command]",
                "examples": ["help", "help file", "help coder"]
            },
            "file": {
                "description": "Perform file operations",
                "usage": "file <operation> <args>",
                "operations": {
                    "read": "Read a file's contents",
                    "write": "Write content to a file",
                    "list": "List files in a directory",
                    "delete": "Delete a file",
                    "create": "Create a new file"
                },
                "examples": [
                    "file read main.py",
                    "file list ./",
                    "file write example.txt 'Hello, world!'",
                    "file create test.py",
                    "file delete temp.txt"
                ]
            },
            "terminal": {
                "description": "Execute terminal commands",
                "usage": "terminal <command>",
                "examples": [
                    "terminal ls -la",
                    "terminal python -V",
                    "terminal echo 'Hello from The Commander'"
                ]
            },
            "api": {
                "description": "Make API requests",
                "usage": "api <method> <url> [params] [headers]",
                "examples": [
                    "api get https://api.example.com/data",
                    "api post https://api.example.com/submit {\"name\": \"Commander\"}"
                ]
            },
            "about": {
                "description": "Display information about The Commander",
                "usage": "about",
                "examples": ["about"]
            },
            # Sub-agent commands
            "coder": {
                "description": "Code generation and debugging operations",
                "usage": "coder <command> <args>",
                "examples": [
                    "coder write python 'A function to calculate fibonacci numbers'",
                    "coder explain python 'def factorial(n): return 1 if n <= 1 else n * factorial(n-1)'",
                    "coder debug python 'def divide(a, b): return a/b'",
                    "coder languages"
                ]
            },
            "researcher": {
                "description": "Web scraping and document analysis operations",
                "usage": "researcher <command> <args>",
                "examples": [
                    "researcher scrape https://news.ycombinator.com",
                    "researcher summarize 'Long text that needs to be summarized...'",
                    "researcher extract-links https://example.com",
                    "researcher analyze 'Text to analyze for readability and statistics'"
                ]
            },
            "sysadmin": {
                "description": "System administration operations",
                "usage": "sysadmin <command> <args>",
                "examples": [
                    "sysadmin exec ls -la",
                    "sysadmin sysinfo",
                    "sysadmin processes python",
                    "sysadmin diskspace ."
                ]
            },
            "memory": {
                "description": "Persistent memory storage operations",
                "usage": "memory <command> <args>",
                "examples": [
                    "memory remember server_ip 192.168.1.100 infrastructure",
                    "memory recall server_ip",
                    "memory list",
                    "memory search ip"
                ]
            },
            "vscode": {
                "description": "VS Code and Linux integration operations",
                "usage": "vscode <command> <args>",
                "examples": [
                    "vscode recommend-extensions python",
                    "vscode create-task build 'make all'",
                    "vscode linux-terminal bash /bin/bash",
                    "vscode create-launch 'Python Debug' python app.py"
                ]
            },
            "security": {
                "description": "Security and vulnerability detection operations",
                "usage": "security <command> <args>",
                "examples": [
                    "security scan-code main.py",
                    "security owasp-check example.com",
                    "security check-deps ./",
                    "security harden-linux",
                    "security generate-report myapp.com xss"
                ]
            },
            "database": {
                "description": "Database operations and SQL management",
                "usage": "database <command> <args>",
                "examples": [
                    "database generate-schema postgresql 'A blog with users, posts, and comments'",
                    "database optimize-query postgresql 'SELECT * FROM users JOIN posts ON users.id = posts.user_id'",
                    "database security-audit mysql 'CREATE USER app'",
                    "database generate-migration postgresql 'Add email column to users'",
                    "database document-schema postgresql 'CREATE TABLE users...'"
                ]
            },
            "devops": {
                "description": "DevOps, automation, and deployment operations",
                "usage": "devops <command> <args>",
                "examples": [
                    "devops docker-setup flask",
                    "devops ci-pipeline github-actions python",
                    "devops infrastructure terraform aws-ec2",
                    "devops monitor-setup prometheus",
                    "devops deployment kubernetes python-app"
                ]
            },
            "learning": {
                "description": "Learning and improvement system for agents",
                "usage": "learning <command> <args>",
                "examples": [
                    "learning analyze-usage 30",
                    "learning add-feedback 'security scan-code main.py' 5 'Very helpful output'",
                    "learning diagnose security-agent",
                    "learning improvement-report",
                    "learning optimize-workflows security"
                ]
            }
        }
    
    def get_available_commands(self):
        """Return the available commands dictionary."""
        return self.commands
    
    def execute_command(self, command_text, use_advanced_parsing=True, use_ai=True, ai_service=None):
        """
        Parse and execute a command using advanced parsing and AI understanding.
        
        Args:
            command_text: The text-based command to execute
            use_advanced_parsing: Whether to use advanced parsing (default: True)
            use_ai: Whether to use AI for natural language understanding (default: True)
            ai_service: An initialized AIService instance
            
        Returns:
            The result of the command execution
        """
        try:
            logger.debug(f"Executing command: {command_text}")
            
            # First try to parse the command using advanced parsing if enabled
            if use_advanced_parsing:
                from utils import parse_natural_language_command, advanced_parse_command, find_similar_commands
                
                # Use AI-based natural language understanding if available
                if use_ai and ai_service:
                    parsed_command = parse_natural_language_command(
                        command_text, 
                        ai_service=ai_service,
                        available_commands=self.commands
                    )
                else:
                    parsed_command = advanced_parse_command(command_text)
                
                # Extract command and handle it
                command = parsed_command.get("command", "").lower()
                subcommand = parsed_command.get("subcommand")
                args = parsed_command.get("args", [])
                options = parsed_command.get("options", {})
                
                # Special error handling
                if command == "error":
                    logger.error(f"Parse error: {args[0] if args else 'Unknown error'}")
                    return f"Error parsing command: {args[0] if args else 'Unknown error'}"
                
                # Execute the appropriate command
                if command == "help":
                    return self._help_command(args)
                elif command == "file":
                    return self._file_command_advanced(subcommand, args, options)
                elif command == "terminal":
                    # Reconstruct the terminal command
                    terminal_command = " ".join(args)
                    return self._terminal_command([terminal_command])
                elif command == "api":
                    return self._api_command_advanced(args, options)
                elif command == "about":
                    return self._about_command()
                # Handle sub-agent commands using advanced structure
                elif command in self.agents:
                    if subcommand:
                        args.insert(0, subcommand)
                    return self._agent_command(command, args)
                else:
                    # Try to find similar commands as suggestions
                    similar_commands = find_similar_commands(command, self.commands)
                    
                    if similar_commands:
                        suggestion_text = "Did you mean:\n"
                        for i, cmd in enumerate(similar_commands):
                            suggestion_text += f"{i+1}. {cmd}\n"
                        return f"Unknown command: '{command}'.\n\n{suggestion_text}\nType 'help' for available commands."
                    else:
                        return f"Unknown command: '{command}'. Type 'help' for available commands."
            
            # Fall back to legacy parsing if advanced parsing is disabled
            else:
                command, args = parse_command(command_text)
                
                if command == "help":
                    return self._help_command(args)
                elif command == "file":
                    return self._file_command(args)
                elif command == "terminal":
                    return self._terminal_command(args)
                elif command == "api":
                    return self._api_command(args)
                elif command == "about":
                    return self._about_command()
                # Handle sub-agent commands
                elif command in self.agents:
                    return self._agent_command(command, args)
                else:
                    return f"Unknown command: '{command}'. Type 'help' for available commands."
        
        except Exception as e:
            logger.error(f"Error executing command: {str(e)}")
            return f"Error executing command: {str(e)}"
            
    def _agent_command(self, agent_name, args):
        """Execute commands through specialized sub-agents."""
        if not args:
            # Display agent help if no subcommand is provided
            agent = self.agents[agent_name]
            result = f"Agent: {agent.name}\n"
            result += f"Description: {agent.description}\n\n"
            result += "Available Commands:\n"
            
            commands = agent.get_commands()
            for cmd, info in commands.items():
                result += f"- {cmd}: {info['description']}\n"
            
            result += f"\nUse '{agent_name} <command> [args]' to execute a command."
            return result
        
        # Extract the sub-agent command and its arguments
        agent_command = args[0]
        agent_args = args[1:] if len(args) > 1 else []
        
        # Execute the command through the appropriate agent
        try:
            agent = self.agents[agent_name]
            return agent.execute(agent_command, agent_args)
        except Exception as e:
            logger.error(f"Error executing {agent_name} command: {str(e)}")
            return f"Error executing {agent_name} command: {str(e)}"
    
    def _help_command(self, args):
        """Display help information for commands."""
        if not args:
            # General help
            result = "Available commands:\n\n"
            for cmd, info in self.commands.items():
                result += f"- {cmd}: {info['description']}\n"
            result += "\nType 'help <command>' for more information on a specific command."
            return result
        
        # Help for a specific command
        cmd = args[0]
        if cmd in self.commands:
            info = self.commands[cmd]
            result = f"Command: {cmd}\n"
            result += f"Description: {info['description']}\n"
            result += f"Usage: {info['usage']}\n\n"
            
            if "operations" in info:
                result += "Operations:\n"
                for op, desc in info["operations"].items():
                    result += f"- {op}: {desc}\n"
                result += "\n"
            
            result += "Examples:\n"
            for example in info["examples"]:
                result += f"- {example}\n"
            
            return result
        else:
            return f"Unknown command: '{cmd}'. Type 'help' for available commands."
    
    def _file_command(self, args):
        """Execute file system operations."""
        if not args:
            return "Missing file operation. Try 'help file' for more information."
        
        operation = args[0]
        operation_args = args[1:]
        
        if operation == "read":
            if not operation_args:
                return "Missing filename. Usage: file read <filename>"
            return self.file_tool.read_file(operation_args[0])
        
        elif operation == "write":
            if len(operation_args) < 2:
                return "Missing filename or content. Usage: file write <filename> <content>"
            filename = operation_args[0]
            content = " ".join(operation_args[1:])
            return self.file_tool.write_file(filename, content)
        
        elif operation == "list":
            path = "." if not operation_args else operation_args[0]
            return self.file_tool.list_files(path)
        
        elif operation == "delete":
            if not operation_args:
                return "Missing filename. Usage: file delete <filename>"
            return self.file_tool.delete_file(operation_args[0])
        
        elif operation == "create":
            if not operation_args:
                return "Missing filename. Usage: file create <filename>"
            return self.file_tool.create_file(operation_args[0])
        
        else:
            return f"Unknown file operation: '{operation}'. Try 'help file' for more information."
            
    def _file_command_advanced(self, subcommand, args, options):
        """Execute file system operations with advanced parsing."""
        if not subcommand:
            return "Missing file operation. Try 'help file' for more information."
        
        # Extract common options
        path = options.get("path", "")
        filename = options.get("filename", "")
        content = options.get("content", "")
        
        # If args are provided, use them to override options
        if args and not filename:
            filename = args[0]
        
        if len(args) > 1 and not content:
            content = " ".join(args[1:])
        
        if subcommand == "read":
            if not filename:
                return "Missing filename. Usage: file read <filename>"
            return self.file_tool.read_file(filename)
        
        elif subcommand == "write":
            if not filename:
                return "Missing filename. Usage: file write <filename> <content>"
            if not content:
                return "Missing content. Usage: file write <filename> <content>"
            return self.file_tool.write_file(filename, content)
        
        elif subcommand == "list":
            directory = path or filename or "."
            return self.file_tool.list_files(directory)
        
        elif subcommand == "delete":
            if not filename:
                return "Missing filename. Usage: file delete <filename>"
            return self.file_tool.delete_file(filename)
        
        elif subcommand == "create":
            if not filename:
                return "Missing filename. Usage: file create <filename>"
            return self.file_tool.create_file(filename, content)
        
        else:
            return f"Unknown file operation: '{subcommand}'. Try 'help file' for more information."
    
    def _terminal_command(self, args):
        """Execute terminal commands."""
        if not args:
            return "Missing terminal command. Usage: terminal <command>"
        
        command = " ".join(args)
        return self.terminal_tool.execute(command)
    
    def _api_command(self, args):
        """Execute API requests."""
        if not args or len(args) < 2:
            return "Missing API method or URL. Usage: api <method> <url> [data] [headers]"
        
        method = args[0].upper()
        url = args[1]
        data = None
        headers = None
        
        if len(args) >= 3:
            try:
                # Try to parse as data (JSON)
                data = " ".join(args[2:])
            except:
                data = args[2]
                
        if len(args) >= 4:
            try:
                # Try to parse as headers (JSON)
                headers = args[3]
            except:
                headers = None
        
        return self.api_tool.make_request(method, url, data, headers)
        
    def _api_command_advanced(self, args, options):
        """Execute API requests with advanced parsing."""
        # Extract method and URL from options or args
        method = options.get("method", "").upper()
        url = options.get("url", "")
        
        # Extract data and headers from options
        data = options.get("data", None)
        headers = options.get("headers", None)
        
        # If args are provided, use them to override options
        if args and not method:
            method = args[0].upper()
            
        if len(args) > 1 and not url:
            url = args[1]
            
        if len(args) > 2 and not data:
            try:
                # Try to parse as JSON
                import json
                data_str = " ".join(args[2:])
                data = json.loads(data_str)
            except:
                # Fallback to string
                data = " ".join(args[2:])
        
        # Validate required parameters
        if not method:
            return "Missing API method. Usage: api <method> <url> [data] [headers]"
            
        if not url:
            return "Missing API URL. Usage: api <method> <url> [data] [headers]"
            
        # Convert method to uppercase
        method = method.upper()
        
        # Parse additional options
        timeout = options.get("timeout", None)
        verify_ssl = options.get("verify", True)
        
        # Process authentication options
        auth = None
        if "auth_username" in options and "auth_password" in options:
            from requests.auth import HTTPBasicAuth
            auth = HTTPBasicAuth(options["auth_username"], options["auth_password"])
        
        # Add additional options to request
        request_options = {}
        if timeout is not None:
            request_options["timeout"] = float(timeout)
        if verify_ssl is not None:
            request_options["verify"] = verify_ssl
        if auth is not None:
            request_options["auth"] = auth
            
        logger.debug(f"Making API request: {method} {url}")
        return self.api_tool.make_request(method, url, data, headers, **request_options)
    
    def _about_command(self):
        """Display information about the Commander agent."""
        return f"""
        {self.name} - v{self.version}
        
        An AI agent specializing in VS Code integration with Linux environments
        and advanced security capabilities.
        
        Core Tools:
        - File System Operations
        - Terminal Command Execution
        - API Request Handling
        
        Specialized Sub-Agents:
        - Coder: Code generation and debugging using advanced AI
        - Researcher: Web scraping and document summarization
        - SysAdmin: System administration and monitoring
        - Memory: Persistent memory storage
        - VSCode: VS Code integration for Linux development
        - Security: Vulnerability detection and security operations
        - Database: Database operations and SQL management
        - DevOps: Automation, deployment, and infrastructure
        - Learning: Pattern analysis and system improvement
        
        Type 'help' to see available commands.
        """
