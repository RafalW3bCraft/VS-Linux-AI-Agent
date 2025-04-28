import os
import json
import logging
import datetime
from pathlib import Path
from agents.base_agent import BaseAgent
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.declarative import declarative_base

# Set up logging
logger = logging.getLogger(__name__)

# Database models
Base = declarative_base()

class Memory(Base):
    """Database model for storing memories."""
    __tablename__ = 'memories'
    
    id = sa.Column(sa.Integer, primary_key=True)
    key = sa.Column(sa.String(128), index=True, nullable=False)
    value = sa.Column(sa.Text, nullable=False)
    category = sa.Column(sa.String(64), index=True, nullable=True)
    created_at = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
    updated_at = sa.Column(sa.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f"<Memory {self.key}: {self.value[:30]}...>"


class MemoryKeeperAgent(BaseAgent):
    """
    The MemoryKeeper Agent - specialized in persistent memory storage.
    
    This agent can help with tasks like:
    - Storing information for future retrieval
    - Retrieving previously stored information
    - Updating stored information
    - Managing categories of information
    """
    
    def __init__(self, db_url=None):
        """Initialize the MemoryKeeper Agent."""
        super().__init__(
            name="MemoryKeeperAgent",
            description="Specialized in persistent memory storage."
        )
        
        # Set up the memory storage
        self.memory_file = "memory_store.json"
        self.memories = {}
        
        # Load existing memories from file
        self._load_memories()
        
        # Database configuration
        self.db_url = db_url or os.environ.get("DATABASE_URL")
        self.db_initialized = False
        
        # Initialize database if URL is provided
        if self.db_url:
            try:
                self._init_db()
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
    
    def get_commands(self):
        """Return the commands this agent can handle."""
        return {
            "remember": {
                "description": "Store a piece of information for future retrieval",
                "usage": "remember <key> <value> [category]",
                "examples": [
                    "remember server_ip 192.168.1.100 infrastructure",
                    "remember project_deadline '2023-12-31' schedule"
                ]
            },
            "recall": {
                "description": "Retrieve a previously stored piece of information",
                "usage": "recall <key>",
                "examples": [
                    "recall server_ip",
                    "recall project_deadline"
                ]
            },
            "forget": {
                "description": "Delete a stored piece of information",
                "usage": "forget <key>",
                "examples": [
                    "forget server_ip",
                    "forget project_deadline"
                ]
            },
            "list": {
                "description": "List all stored memories, optionally filtered by category",
                "usage": "list [category]",
                "examples": [
                    "list",
                    "list infrastructure",
                    "list schedule"
                ]
            },
            "search": {
                "description": "Search for memories containing a specific term",
                "usage": "search <term>",
                "examples": [
                    "search ip",
                    "search 2023"
                ]
            },
            "categories": {
                "description": "List all available memory categories",
                "usage": "categories",
                "examples": ["categories"]
            }
        }
    
    def execute(self, command, args):
        """Execute a MemoryKeeperAgent command."""
        try:
            if command == "remember":
                if len(args) < 2:
                    return "Error: Missing key or value. Usage: remember <key> <value> [category]"
                key = args[0]
                # Join all remaining args except the last one (which might be a category)
                value = " ".join(args[1:-1]) if len(args) > 2 else args[1]
                category = args[-1] if len(args) > 2 else None
                
                # If the value is exactly the same as the key, or the last arg is part of the value
                if value == key or (len(args) > 2 and category in value):
                    value = " ".join(args[1:])
                    category = None
                
                return self._remember(key, value, category)
                
            elif command == "recall":
                if not args:
                    return "Error: Missing key. Usage: recall <key>"
                key = args[0]
                return self._recall(key)
                
            elif command == "forget":
                if not args:
                    return "Error: Missing key. Usage: forget <key>"
                key = args[0]
                return self._forget(key)
                
            elif command == "list":
                category = args[0] if args else None
                return self._list_memories(category)
                
            elif command == "search":
                if not args:
                    return "Error: Missing search term. Usage: search <term>"
                term = args[0]
                return self._search_memories(term)
                
            elif command == "categories":
                return self._list_categories()
                
            else:
                return f"Unknown command: '{command}'"
                
        except Exception as e:
            logger.error(f"Error in MemoryKeeperAgent: {str(e)}")
            return f"Error executing command: {str(e)}"
    
    def _init_db(self):
        """Initialize the database connection and create tables if needed."""
        try:
            if not self.db_url:
                logger.warning("No database URL provided, will use file-based storage")
                return
            
            engine = sa.create_engine(self.db_url)
            Base.metadata.create_all(engine)
            self.engine = engine
            self.db_initialized = True
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def _db_session(self):
        """Create a new database session."""
        if not self.db_initialized:
            return None
        
        Session = sa.orm.sessionmaker(bind=self.engine)
        return Session()
    
    def _load_memories(self):
        """Load memories from JSON file if it exists."""
        try:
            if os.path.exists(self.memory_file):
                with open(self.memory_file, 'r') as f:
                    self.memories = json.load(f)
                logger.debug(f"Loaded {len(self.memories)} memories from file")
            else:
                self.memories = {}
                logger.debug("No memory file found, starting with empty memory")
        except Exception as e:
            logger.error(f"Error loading memories from file: {str(e)}")
            self.memories = {}
    
    def _save_memories(self):
        """Save memories to JSON file."""
        try:
            with open(self.memory_file, 'w') as f:
                json.dump(self.memories, f, indent=2)
            logger.debug(f"Saved {len(self.memories)} memories to file")
        except Exception as e:
            logger.error(f"Error saving memories to file: {str(e)}")
    
    def _remember(self, key, value, category=None):
        """
        Store a piece of information.
        
        Args:
            key: The key to store the information under
            value: The information to store
            category: Optional category for organizing memories
            
        Returns:
            Confirmation message
        """
        try:
            logger.debug(f"Storing memory: {key} = {value} (category: {category})")
            
            # Try to store in database first if available
            if self.db_initialized:
                try:
                    session = self._db_session()
                    if session:
                        # Check if memory already exists
                        existing = session.query(Memory).filter_by(key=key).first()
                        
                        if existing:
                            existing.value = value
                            if category:
                                existing.category = category
                            existing.updated_at = datetime.datetime.utcnow()
                        else:
                            new_memory = Memory(
                                key=key,
                                value=value,
                                category=category
                            )
                            session.add(new_memory)
                        
                        session.commit()
                        session.close()
                        return f"Remembered: {key} = {value}" + (f" (category: {category})" if category else "")
                except Exception as db_e:
                    logger.error(f"Database storage failed, falling back to file storage: {db_e}")
            
            # Fall back to file-based storage
            memory_data = {
                "value": value,
                "timestamp": datetime.datetime.now().isoformat()
            }
            
            if category:
                memory_data["category"] = category
            
            self.memories[key] = memory_data
            self._save_memories()
            
            return f"Remembered: {key} = {value}" + (f" (category: {category})" if category else "")
            
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            return f"Error storing memory: {str(e)}"
    
    def _recall(self, key):
        """
        Retrieve a piece of information.
        
        Args:
            key: The key to retrieve
            
        Returns:
            The stored information or error message
        """
        try:
            logger.debug(f"Retrieving memory: {key}")
            
            # Try to retrieve from database first if available
            if self.db_initialized:
                try:
                    session = self._db_session()
                    if session:
                        memory = session.query(Memory).filter_by(key=key).first()
                        session.close()
                        
                        if memory:
                            category_info = f" (category: {memory.category})" if memory.category else ""
                            return f"{key} = {memory.value}{category_info}"
                except Exception as db_e:
                    logger.error(f"Database retrieval failed, falling back to file storage: {db_e}")
            
            # Fall back to file-based storage
            if key in self.memories:
                memory_data = self.memories[key]
                value = memory_data["value"]
                category_info = f" (category: {memory_data['category']})" if "category" in memory_data else ""
                return f"{key} = {value}{category_info}"
            else:
                return f"No memory found for key: {key}"
            
        except Exception as e:
            logger.error(f"Error retrieving memory: {str(e)}")
            return f"Error retrieving memory: {str(e)}"
    
    def _forget(self, key):
        """
        Delete a piece of information.
        
        Args:
            key: The key to delete
            
        Returns:
            Confirmation message
        """
        try:
            logger.debug(f"Deleting memory: {key}")
            
            # Try to delete from database first if available
            if self.db_initialized:
                try:
                    session = self._db_session()
                    if session:
                        memory = session.query(Memory).filter_by(key=key).first()
                        
                        if memory:
                            session.delete(memory)
                            session.commit()
                            session.close()
                            return f"Forgotten: {key}"
                except Exception as db_e:
                    logger.error(f"Database deletion failed, falling back to file storage: {db_e}")
            
            # Fall back to file-based storage
            if key in self.memories:
                del self.memories[key]
                self._save_memories()
                return f"Forgotten: {key}"
            else:
                return f"No memory found for key: {key}"
            
        except Exception as e:
            logger.error(f"Error deleting memory: {str(e)}")
            return f"Error deleting memory: {str(e)}"
    
    def _list_memories(self, category=None):
        """
        List all stored memories, optionally filtered by category.
        
        Args:
            category: Optional category to filter by
            
        Returns:
            List of memories
        """
        try:
            logger.debug(f"Listing memories" + (f" for category: {category}" if category else ""))
            
            # Try to list from database first if available
            if self.db_initialized:
                try:
                    session = self._db_session()
                    if session:
                        query = session.query(Memory)
                        
                        if category:
                            query = query.filter_by(category=category)
                        
                        memories = query.order_by(Memory.key).all()
                        session.close()
                        
                        if memories:
                            result = f"Stored Memories" + (f" (category: {category})" if category else "") + ":\n\n"
                            for memory in memories:
                                category_info = f" (category: {memory.category})" if memory.category else ""
                                result += f"- {memory.key} = {memory.value}{category_info}\n"
                            return result
                        else:
                            return f"No memories found" + (f" for category: {category}" if category else "")
                except Exception as db_e:
                    logger.error(f"Database listing failed, falling back to file storage: {db_e}")
            
            # Fall back to file-based storage
            if not self.memories:
                return "No memories stored yet."
            
            # Filter by category if specified
            filtered_memories = {}
            
            if category:
                for key, data in self.memories.items():
                    if "category" in data and data["category"] == category:
                        filtered_memories[key] = data
            else:
                filtered_memories = self.memories
            
            if not filtered_memories:
                return f"No memories found" + (f" for category: {category}" if category else "")
            
            result = f"Stored Memories" + (f" (category: {category})" if category else "") + ":\n\n"
            
            # Sort by key for consistent output
            for key in sorted(filtered_memories.keys()):
                data = filtered_memories[key]
                value = data["value"]
                category_info = f" (category: {data['category']})" if "category" in data else ""
                result += f"- {key} = {value}{category_info}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing memories: {str(e)}")
            return f"Error listing memories: {str(e)}"
    
    def _search_memories(self, term):
        """
        Search for memories containing a specific term.
        
        Args:
            term: The term to search for
            
        Returns:
            List of matching memories
        """
        try:
            logger.debug(f"Searching memories for term: {term}")
            term = term.lower()
            
            # Try to search in database first if available
            if self.db_initialized:
                try:
                    session = self._db_session()
                    if session:
                        # Search in both key and value
                        memories = session.query(Memory).filter(
                            sa.or_(
                                Memory.key.ilike(f"%{term}%"),
                                Memory.value.ilike(f"%{term}%")
                            )
                        ).order_by(Memory.key).all()
                        
                        session.close()
                        
                        if memories:
                            result = f"Search Results for '{term}':\n\n"
                            for memory in memories:
                                category_info = f" (category: {memory.category})" if memory.category else ""
                                result += f"- {memory.key} = {memory.value}{category_info}\n"
                            return result
                        else:
                            return f"No memories found containing '{term}'"
                except Exception as db_e:
                    logger.error(f"Database search failed, falling back to file storage: {db_e}")
            
            # Fall back to file-based storage
            if not self.memories:
                return "No memories stored yet."
            
            # Search in keys and values
            matches = {}
            
            for key, data in self.memories.items():
                value = data["value"]
                
                if term in key.lower() or term in value.lower():
                    matches[key] = data
            
            if not matches:
                return f"No memories found containing '{term}'"
            
            result = f"Search Results for '{term}':\n\n"
            
            # Sort by key for consistent output
            for key in sorted(matches.keys()):
                data = matches[key]
                value = data["value"]
                category_info = f" (category: {data['category']})" if "category" in data else ""
                result += f"- {key} = {value}{category_info}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error searching memories: {str(e)}")
            return f"Error searching memories: {str(e)}"
    
    def _list_categories(self):
        """
        List all available memory categories.
        
        Returns:
            List of categories
        """
        try:
            logger.debug("Listing memory categories")
            
            # Try to list categories from database first if available
            if self.db_initialized:
                try:
                    session = self._db_session()
                    if session:
                        # Get distinct categories
                        categories = session.query(Memory.category).distinct().filter(Memory.category != None).all()
                        session.close()
                        
                        if categories:
                            result = "Available Memory Categories:\n\n"
                            for i, (category,) in enumerate(sorted(categories), 1):
                                result += f"{i}. {category}\n"
                            return result
                        else:
                            return "No categories defined yet."
                except Exception as db_e:
                    logger.error(f"Database category listing failed, falling back to file storage: {db_e}")
            
            # Fall back to file-based storage
            categories = set()
            
            for _, data in self.memories.items():
                if "category" in data and data["category"]:
                    categories.add(data["category"])
            
            if not categories:
                return "No categories defined yet."
            
            result = "Available Memory Categories:\n\n"
            for i, category in enumerate(sorted(categories), 1):
                result += f"{i}. {category}\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error listing categories: {str(e)}")
            return f"Error listing categories: {str(e)}"