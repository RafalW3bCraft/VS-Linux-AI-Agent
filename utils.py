import re
import shlex
import logging
import json
from typing import Tuple, List, Dict, Any, Optional, Union

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def parse_command(command_text: str) -> Tuple[str, List[str]]:
    """
    Parse a command string into command name and arguments.
    
    Args:
        command_text: The command string to parse
        
    Returns:
        Tuple of (command_name, args_list)
    """
    try:
        # Use shlex to handle quoted arguments properly
        args = shlex.split(command_text)
        
        if not args:
            return ("help", [])
        
        command = args[0].lower()
        arguments = args[1:]
        
        logger.debug(f"Parsed command: {command}, args: {arguments}")
        return (command, arguments)
    except Exception as e:
        logger.error(f"Error parsing command: {str(e)}")
        return ("error", [f"Could not parse command: {str(e)}"])

def advanced_parse_command(command_text: str) -> Dict[str, Any]:
    """
    Advanced parsing of a command string into structured format with command, 
    subcommand, arguments, and options.
    
    This function handles:
    - Basic commands (help, file, terminal, api, about)
    - Agent commands (vscode, security, etc.)
    - Options in format --key=value or --flag
    - Quoted arguments
    - Named parameters
    
    Args:
        command_text: The command string to parse
        
    Returns:
        Dictionary with command structure
    """
    try:
        # Use shlex to handle quoted arguments properly
        tokens = shlex.split(command_text)
        
        if not tokens:
            return {
                "command": "help",
                "subcommand": None,
                "args": [],
                "options": {},
                "original_text": command_text
            }
        
        # Start with the command structure
        result = {
            "command": tokens[0].lower(),
            "subcommand": None,
            "args": [],
            "options": {},
            "original_text": command_text
        }
        
        # Known agent commands
        agent_commands = [
            "coder", "researcher", "sysadmin", "memory", "vscode", 
            "security", "database", "devops", "learning"
        ]
        
        # Process remaining tokens
        remaining_tokens = tokens[1:]
        
        # If the main command is an agent command and we have at least one token left,
        # the next token is the subcommand
        if result["command"] in agent_commands and remaining_tokens:
            result["subcommand"] = remaining_tokens[0].lower()
            remaining_tokens = remaining_tokens[1:]
        
        # Special handling for 'file' and 'terminal' commands
        if result["command"] == "file" and remaining_tokens:
            result["subcommand"] = remaining_tokens[0].lower()
            remaining_tokens = remaining_tokens[1:]
        
        # Process all remaining tokens
        i = 0
        while i < len(remaining_tokens):
            token = remaining_tokens[i]
            
            # Check for options (--key=value or --flag)
            if token.startswith("--"):
                option_parts = token[2:].split("=", 1)
                if len(option_parts) == 2:
                    key, value = option_parts
                    # Try to parse the value as a number or boolean if possible
                    try:
                        if value.lower() == "true":
                            value = True
                        elif value.lower() == "false":
                            value = False
                        elif value.isdigit():
                            value = int(value)
                        elif re.match(r"^\d+\.\d+$", value):
                            value = float(value)
                    except:
                        pass
                    result["options"][key] = value
                else:
                    # It's a flag without a value
                    result["options"][option_parts[0]] = True
            # Check for named parameters (key:value or key=value)
            elif ":" in token and not token.startswith(("http:", "https:")):
                key, value = token.split(":", 1)
                result["options"][key] = value
            elif "=" in token and not token.startswith(("http:", "https:")):
                key, value = token.split("=", 1)
                result["options"][key] = value
            else:
                # It's a regular argument
                result["args"].append(token)
            
            i += 1
        
        logger.debug(f"Advanced parsed command: {result}")
        return result
    except Exception as e:
        logger.error(f"Error in advanced parsing: {str(e)}")
        return {
            "command": "error",
            "subcommand": None,
            "args": [f"Could not parse command: {str(e)}"],
            "options": {},
            "original_text": command_text
        }

def parse_natural_language_command(command_text: str, ai_service=None, available_commands=None) -> Dict[str, Any]:
    """
    Parse a natural language command using AI services if available.
    Falls back to advanced_parse_command if AI services are not available.
    
    Args:
        command_text: The natural language command text
        ai_service: An initialized AIService instance
        available_commands: Dictionary of available commands for context
        
    Returns:
        Dictionary with structured command information
    """
    # If the text already appears to be a formatted command, use advanced parsing
    if re.match(r"^[a-zA-Z]+((\s+[a-zA-Z0-9_\-\.]+)+|\s*$)", command_text):
        return advanced_parse_command(command_text)
        
    # If AI service is available, use it for natural language understanding
    if ai_service and hasattr(ai_service, 'understand_command'):
        try:
            context = {"available_commands": available_commands} if available_commands else None
            result = ai_service.understand_command(command_text, context=context)
            
            # Return the result if it's valid, otherwise fall back to advanced parsing
            if isinstance(result, dict) and "command" in result and not "error" in result:
                # Add the original text
                result["original_text"] = command_text
                return result
        except Exception as e:
            logger.warning(f"Error using AI service for command parsing: {str(e)}")
    
    # Fall back to advanced parsing
    return advanced_parse_command(command_text)

def format_response(response):
    """
    Format a response for better readability.
    
    Args:
        response: The response to format
        
    Returns:
        Formatted response string
    """
    if isinstance(response, dict) or isinstance(response, list):
        try:
            return json.dumps(response, indent=2)
        except:
            return str(response)
    
    return str(response)

def sanitize_input(input_text):
    """
    Sanitize user input to prevent injection.
    
    Args:
        input_text: The input to sanitize
        
    Returns:
        Sanitized input string
    """
    # Remove any potentially dangerous characters or patterns
    sanitized = re.sub(r'[;&|><$\n\r]', '', input_text)
    return sanitized

def find_similar_commands(command: str, available_commands: Dict[str, Any]) -> List[str]:
    """
    Find similar commands when a command is not recognized.
    
    Args:
        command: The unrecognized command
        available_commands: Dictionary of available commands
        
    Returns:
        List of similar command suggestions
    """
    if not command or not available_commands:
        return []
    
    # Simple similarity check - commands that start with the same letters
    prefix_matches = [cmd for cmd in available_commands.keys() 
                     if cmd.startswith(command[:1]) and cmd != command]
    
    # Levenshtein distance for more advanced similarity (with a max distance of 3)
    lev_matches = []
    for cmd in available_commands.keys():
        if cmd != command and levenshtein_distance(command, cmd) <= 3:
            lev_matches.append(cmd)
    
    # Combine and remove duplicates
    all_matches = list(set(prefix_matches + lev_matches))
    
    # Sort by similarity (closer matches first)
    all_matches.sort(key=lambda x: levenshtein_distance(command, x))
    
    return all_matches[:5]  # Return up to 5 suggestions

def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Calculate the Levenshtein distance between two strings.
    
    Args:
        s1: First string
        s2: Second string
        
    Returns:
        Edit distance between the strings
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]
