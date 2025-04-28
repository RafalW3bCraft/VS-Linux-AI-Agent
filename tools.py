import os
import subprocess
import logging
import requests
import json
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class FileSystemTool:
    """Tool for interacting with the file system."""
    
    def read_file(self, filename):
        """
        Read content from a file.
        
        Args:
            filename: Path to the file to read
            
        Returns:
            The content of the file
        """
        try:
            logger.debug(f"Reading file: {filename}")
            path = Path(filename)
            
            if not path.exists():
                return f"Error: File '{filename}' not found."
            
            if not path.is_file():
                return f"Error: '{filename}' is not a file."
            
            with open(filename, 'r') as file:
                content = file.read()
            
            return content
        except Exception as e:
            logger.error(f"Error reading file {filename}: {str(e)}")
            return f"Error reading file: {str(e)}"
    
    def write_file(self, filename, content):
        """
        Write content to a file.
        
        Args:
            filename: Path to the file to write
            content: Content to write to the file
            
        Returns:
            Success message
        """
        try:
            logger.debug(f"Writing to file: {filename}")
            with open(filename, 'w') as file:
                file.write(content)
            
            return f"Successfully wrote to '{filename}'."
        except Exception as e:
            logger.error(f"Error writing to file {filename}: {str(e)}")
            return f"Error writing to file: {str(e)}"
    
    def list_files(self, directory="."):
        """
        List files in a directory.
        
        Args:
            directory: Directory to list files from (default: current directory)
            
        Returns:
            List of files in the directory
        """
        try:
            logger.debug(f"Listing files in directory: {directory}")
            path = Path(directory)
            
            if not path.exists():
                return f"Error: Directory '{directory}' not found."
            
            if not path.is_dir():
                return f"Error: '{directory}' is not a directory."
            
            files = list(path.iterdir())
            
            result = f"Files in '{directory}':\n"
            for file in files:
                result += f"- {'📁 ' if file.is_dir() else '📄 '}{file.name}\n"
            
            return result
        except Exception as e:
            logger.error(f"Error listing files in {directory}: {str(e)}")
            return f"Error listing files: {str(e)}"
    
    def delete_file(self, filename):
        """
        Delete a file.
        
        Args:
            filename: Path to the file to delete
            
        Returns:
            Success message
        """
        try:
            logger.debug(f"Deleting file: {filename}")
            path = Path(filename)
            
            if not path.exists():
                return f"Error: File '{filename}' not found."
            
            if path.is_dir():
                return f"Error: '{filename}' is a directory. Use a different command to delete directories."
            
            os.remove(filename)
            
            return f"Successfully deleted '{filename}'."
        except Exception as e:
            logger.error(f"Error deleting file {filename}: {str(e)}")
            return f"Error deleting file: {str(e)}"
    
    def create_file(self, filename, content=""):
        """
        Create a new file.
        
        Args:
            filename: Path to the file to create
            content: Initial content (default: empty)
            
        Returns:
            Success message
        """
        try:
            logger.debug(f"Creating file: {filename}")
            path = Path(filename)
            
            if path.exists():
                return f"Error: File '{filename}' already exists."
            
            with open(filename, 'w') as file:
                file.write(content)
            
            return f"Successfully created '{filename}'."
        except Exception as e:
            logger.error(f"Error creating file {filename}: {str(e)}")
            return f"Error creating file: {str(e)}"


class TerminalTool:
    """Tool for executing terminal commands."""
    
    def __init__(self):
        """Initialize the Terminal Tool."""
        self.forbidden_commands = [
            "rm -rf", "sudo", "chmod", "chown", 
            "> /dev/", "format", "mkfs", "dd"
        ]
    
    def is_safe_command(self, command):
        """
        Check if a command is safe to execute.
        
        Args:
            command: The command to check
            
        Returns:
            Boolean indicating safety
        """
        for forbidden in self.forbidden_commands:
            if forbidden in command:
                return False
        return True
    
    def execute(self, command):
        """
        Execute a terminal command.
        
        Args:
            command: The command to execute
            
        Returns:
            Command output
        """
        try:
            logger.debug(f"Executing terminal command: {command}")
            
            if not self.is_safe_command(command):
                return f"Error: The command '{command}' contains potentially harmful operations and is not allowed."
            
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True,
                timeout=15  # Set a timeout to prevent long-running commands
            )
            
            output = result.stdout
            error = result.stderr
            
            if result.returncode != 0:
                return f"Command executed with errors (return code {result.returncode}):\n{error}"
            
            if not output and not error:
                return "Command executed successfully (no output)."
            
            return output if output else error
        except subprocess.TimeoutExpired:
            return "Error: Command execution timed out (15 seconds limit)."
        except Exception as e:
            logger.error(f"Error executing terminal command {command}: {str(e)}")
            return f"Error executing command: {str(e)}"


class ApiTool:
    """Tool for making API requests."""
    
    def make_request(self, method, url, data=None, headers=None, **kwargs):
        """
        Make an API request.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            url: URL to make the request to
            data: Data to send with the request (optional)
            headers: Headers to include in the request (optional)
            **kwargs: Additional options to pass to requests.request (optional)
                - timeout: Request timeout in seconds (default: 10)
                - verify: Verify SSL certificates (default: True)
                - auth: Authentication object
                - params: Query parameters for GET requests
                - cookies: Cookies to send with the request
                - stream: Whether to stream the response
                - cert: SSL client certificate
            
        Returns:
            API response
        """
        try:
            logger.debug(f"Making API {method} request to: {url}")
            
            # Extract common options from kwargs
            timeout = kwargs.get('timeout', 10)
            verify = kwargs.get('verify', True)
            auth = kwargs.get('auth', None)
            params = kwargs.get('params', None)
            cookies = kwargs.get('cookies', None)
            
            # Parse data if it's a string
            if data and isinstance(data, str):
                try:
                    # If it's valid JSON, parse it
                    data = json.loads(data)
                except json.JSONDecodeError:
                    # If not valid JSON, keep as is
                    pass
            
            # Parse headers if it's a string
            if headers and isinstance(headers, str):
                try:
                    headers = json.loads(headers)
                except json.JSONDecodeError:
                    # If not valid JSON, create a simple header from string
                    headers = {"Content-Type": "application/json"}
            
            # Format debug output with redacted auth info
            debug_info = {
                "method": method,
                "url": url,
                "has_data": data is not None,
                "has_headers": headers is not None,
                "timeout": timeout,
                "verify_ssl": verify,
                "has_auth": auth is not None
            }
            logger.debug(f"API request details: {debug_info}")
            
            # Make the request
            response = requests.request(
                method=method,
                url=url,
                json=data if data and isinstance(data, dict) else None,
                data=data if data and not isinstance(data, dict) else None,
                headers=headers,
                timeout=timeout,
                verify=verify,
                auth=auth,
                params=params,
                cookies=cookies,
                **{k: v for k, v in kwargs.items() if k not in ['timeout', 'verify', 'auth', 'params', 'cookies']}
            )
            
            # Process the response
            response_info = {
                "status_code": response.status_code,
                "reason": response.reason,
                "content_type": response.headers.get('Content-Type', ''),
                "elapsed_time": f"{response.elapsed.total_seconds():.2f}s"
            }
            
            # Format output based on response type
            output = {}
            output["request"] = {
                "method": method,
                "url": url,
                "headers": headers,
                "data_size": len(str(data)) if data else 0
            }
            output["response"] = response_info
            
            # Try to format content as JSON if possible
            try:
                output["data"] = response.json()
            except json.JSONDecodeError:
                # Add text preview if not JSON
                content = response.text
                preview = (content[:500] + '...') if len(content) > 500 else content
                output["text_preview"] = preview
                
                # Check if it's HTML
                if response.headers.get('Content-Type', '').startswith('text/html'):
                    output["html"] = True
                
            # Return the formatted output
            return json.dumps(output, indent=2)
            
        except requests.RequestException as e:
            logger.error(f"Error making API request to {url}: {str(e)}")
            return json.dumps({
                "error": True,
                "type": "request_error",
                "message": str(e),
                "request": {
                    "method": method,
                    "url": url
                }
            }, indent=2)
        except Exception as e:
            logger.error(f"Error in API tool: {str(e)}")
            return json.dumps({
                "error": True,
                "type": "general_error",
                "message": str(e)
            }, indent=2)
