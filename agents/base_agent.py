import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class BaseAgent:
    """
    Base class for all specialized agents (soldiers).
    
    This class defines the common structure and methods that all
    specialized agents will inherit and implement.
    """
    
    def __init__(self, name, description):
        """
        Initialize the base agent.
        
        Args:
            name: The name of the agent
            description: A short description of what the agent does
        """
        self.name = name
        self.description = description
        logger.debug(f"Initializing {self.name}")
        
    def get_info(self):
        """Return basic information about the agent."""
        return {
            "name": self.name,
            "description": self.description,
            "commands": self.get_commands()
        }
    
    def get_commands(self):
        """
        Return the commands this agent can handle.
        
        To be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement get_commands()")
    
    def execute(self, command, args):
        """
        Execute a command with the given arguments.
        
        Args:
            command: The command to execute
            args: Arguments for the command
            
        Returns:
            The result of the command execution
        """
        raise NotImplementedError("Subclasses must implement execute()")