import os
import re
import logging
import subprocess
import json
import psycopg2
from typing import List, Dict, Any, Optional
from agents.base_agent import BaseAgent
from ai_service import ai_service

# Set up logging
logger = logging.getLogger(__name__)

class DatabaseAgent(BaseAgent):
    """
    The Database Agent - specialized in database operations and security.
    
    This agent can help with tasks like:
    - Creating and optimizing database schemas
    - Generating and validating SQL queries
    - Performing database security audits
    - Managing database connections
    - Generating database documentation
    """
    
    def __init__(self):
        """Initialize the Database Agent."""
        super().__init__(
            name="DatabaseAgent",
            description="Specialized in database operations, SQL, and database security."
        )
        self.supported_db_types = [
            "postgresql", "mysql", "sqlite", "mongodb"
        ]
        
    def get_commands(self):
        """Return the commands this agent can handle."""
        return {
            "generate-schema": {
                "description": "Generate a database schema from description",
                "usage": "generate-schema <db_type> <description>",
                "examples": [
                    "generate-schema postgresql 'A blog with users, posts, and comments'",
                    "generate-schema sqlite 'A simple inventory tracking system'"
                ]
            },
            "optimize-query": {
                "description": "Optimize a SQL query for performance",
                "usage": "optimize-query <db_type> <query>",
                "examples": [
                    "optimize-query postgresql 'SELECT * FROM users JOIN posts ON users.id = posts.user_id'",
                    "optimize-query mysql 'SELECT * FROM products WHERE price > 100'"
                ]
            },
            "security-audit": {
                "description": "Perform a security audit on database setup or query",
                "usage": "security-audit <db_type> <query_or_schema>",
                "examples": [
                    "security-audit postgresql 'SELECT * FROM users WHERE username = \\'$input\\''",
                    "security-audit mysql 'CREATE USER \\'app\\'@\\'%\\' IDENTIFIED BY \\'password\\''"
                ]
            },
            "generate-migration": {
                "description": "Generate a database migration script",
                "usage": "generate-migration <db_type> <description>",
                "examples": [
                    "generate-migration postgresql 'Add email_verified column to users table'",
                    "generate-migration mysql 'Create new order_history table with foreign key to orders'"
                ]
            },
            "document-schema": {
                "description": "Generate documentation for a database schema",
                "usage": "document-schema <db_type> <schema>",
                "examples": [
                    "document-schema postgresql 'CREATE TABLE users (id SERIAL PRIMARY KEY, username VARCHAR(50), email VARCHAR(100) UNIQUE)'"
                ]
            }
        }
    
    def execute(self, command, args):
        """Execute a DatabaseAgent command."""
        try:
            if command == "generate-schema":
                if len(args) < 2:
                    return "Error: Missing database type or description. Usage: generate-schema <db_type> <description>"
                db_type = args[0].lower()
                description = " ".join(args[1:])
                return self._generate_schema(db_type, description)
            
            elif command == "optimize-query":
                if len(args) < 2:
                    return "Error: Missing database type or query. Usage: optimize-query <db_type> <query>"
                db_type = args[0].lower()
                query = " ".join(args[1:])
                return self._optimize_query(db_type, query)
                
            elif command == "security-audit":
                if len(args) < 2:
                    return "Error: Missing database type or query/schema. Usage: security-audit <db_type> <query_or_schema>"
                db_type = args[0].lower()
                query_or_schema = " ".join(args[1:])
                return self._security_audit(db_type, query_or_schema)
                
            elif command == "generate-migration":
                if len(args) < 2:
                    return "Error: Missing database type or description. Usage: generate-migration <db_type> <description>"
                db_type = args[0].lower()
                description = " ".join(args[1:])
                return self._generate_migration(db_type, description)
                
            elif command == "document-schema":
                if len(args) < 2:
                    return "Error: Missing database type or schema. Usage: document-schema <db_type> <schema>"
                db_type = args[0].lower()
                schema = " ".join(args[1:])
                return self._document_schema(db_type, schema)
                
            else:
                return f"Unknown command: '{command}'"
                
        except Exception as e:
            logger.error(f"Error in DatabaseAgent: {str(e)}")
            return f"Error executing command: {str(e)}"

    def _generate_schema(self, db_type, description):
        """
        Generate a database schema from a description.
        
        Args:
            db_type: Type of database (postgresql, mysql, etc.)
            description: Description of the database needs
            
        Returns:
            Generated schema
        """
        if db_type not in self.supported_db_types:
            return f"Error: Unsupported database type: {db_type}. Supported types: {', '.join(self.supported_db_types)}"
        
        try:
            # Try using AI Service for schema generation
            try:
                system_prompt = f"""
                You are an expert database architect specializing in {db_type}.
                Generate a complete database schema based on the user's description.
                Include:
                
                1. All necessary tables with appropriate fields
                2. Primary and foreign keys
                3. Appropriate indexes for performance
                4. Data types suitable for {db_type}
                5. Constraints for data integrity
                
                Format your response with clear CREATE TABLE statements and comments explaining design decisions.
                Follow best practices for {db_type} database design.
                """
                
                if 'claude' in ai_service.models:
                    logger.debug(f"Using AI Service to generate {db_type} schema for: {description}")
                    response = ai_service.models['claude'].messages.create(
                        model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": f"Please design a {db_type} database schema for: {description}"}
                        ],
                        temperature=0.1,
                        max_tokens=2000
                    )
                    ai_output = response.content[0].text
                    
                    result = f"{db_type.upper()} Schema for: {description}\n\n"
                    result += ai_output
                    return result
                    
            except Exception as ai_err:
                logger.warning(f"AI Service schema generation failed: {str(ai_err)}. Falling back to template schemas.")
            
            # Fallback to template schemas
            if db_type == "postgresql":
                if "blog" in description.lower():
                    schema = """-- Users table to store user information
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    bio TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Posts table to store blog posts
CREATE TABLE posts (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Comments table to store post comments
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tags table for categorizing posts
CREATE TABLE tags (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
);

-- Junction table for many-to-many relationship between posts and tags
CREATE TABLE post_tags (
    post_id INTEGER NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (post_id, tag_id)
);

-- Create indexes for performance
CREATE INDEX idx_posts_user_id ON posts(user_id);
CREATE INDEX idx_comments_post_id ON comments(post_id);
CREATE INDEX idx_comments_user_id ON comments(user_id);
CREATE INDEX idx_post_tags_tag_id ON post_tags(tag_id);

-- Trigger function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_posts_updated_at BEFORE UPDATE ON posts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_comments_updated_at BEFORE UPDATE ON comments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
"""
                elif "inventory" in description.lower() or "product" in description.lower():
                    schema = """-- Categories table for product classification
CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT
);

-- Products table for inventory items
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    sku VARCHAR(50) UNIQUE,
    price DECIMAL(10, 2) NOT NULL,
    cost DECIMAL(10, 2),
    quantity INTEGER NOT NULL DEFAULT 0,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Suppliers table
CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    contact_name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    address TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Product suppliers junction table
CREATE TABLE product_suppliers (
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    supplier_id INTEGER NOT NULL REFERENCES suppliers(id) ON DELETE CASCADE,
    supply_price DECIMAL(10, 2),
    lead_time_days INTEGER,
    PRIMARY KEY (product_id, supplier_id)
);

-- Inventory transactions for tracking changes
CREATE TABLE inventory_transactions (
    id SERIAL PRIMARY KEY,
    product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL,
    transaction_type VARCHAR(20) NOT NULL, -- e.g., 'purchase', 'sale', 'adjustment'
    reference_id VARCHAR(100), -- e.g., order ID or purchase ID
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_products_category_id ON products(category_id);
CREATE INDEX idx_product_suppliers_supplier_id ON product_suppliers(supplier_id);
CREATE INDEX idx_inventory_transactions_product_id ON inventory_transactions(product_id);
CREATE INDEX idx_products_price ON products(price);
CREATE INDEX idx_products_quantity ON products(quantity);

-- Trigger function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for tables
CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_suppliers_updated_at BEFORE UPDATE ON suppliers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update product quantity after transactions
CREATE OR REPLACE FUNCTION update_product_quantity()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE products
    SET quantity = quantity + NEW.quantity
    WHERE id = NEW.product_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER after_inventory_transaction_insert AFTER INSERT ON inventory_transactions
    FOR EACH ROW EXECUTE FUNCTION update_product_quantity();
"""
                else:
                    schema = """-- This is a generic schema. For a more tailored schema, please provide specific details.

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Items table (customize based on your needs)
CREATE TABLE items (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX idx_items_user_id ON items(user_id);

-- Trigger function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_items_updated_at BEFORE UPDATE ON items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
"""
            elif db_type == "mysql":
                # Similar structures for MySQL with appropriate syntax
                if "blog" in description.lower():
                    schema = """-- Users table to store user information
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    bio TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Posts table to store blog posts
CREATE TABLE posts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    user_id INT NOT NULL,
    published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Comments table to store post comments
CREATE TABLE comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    content TEXT NOT NULL,
    user_id INT NOT NULL,
    post_id INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Tags table for categorizing posts
CREATE TABLE tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    description TEXT
) ENGINE=InnoDB;

-- Junction table for many-to-many relationship between posts and tags
CREATE TABLE post_tags (
    post_id INT NOT NULL,
    tag_id INT NOT NULL,
    PRIMARY KEY (post_id, tag_id),
    FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
    FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Create indexes for performance
CREATE INDEX idx_posts_user_id ON posts(user_id);
CREATE INDEX idx_comments_post_id ON comments(post_id);
CREATE INDEX idx_comments_user_id ON comments(user_id);
CREATE INDEX idx_post_tags_tag_id ON post_tags(tag_id);
"""
                else:
                    schema = """-- This is a generic MySQL schema
-- Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- Items table (customize based on your needs)
CREATE TABLE items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    user_id INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
) ENGINE=InnoDB;

-- Create indexes
CREATE INDEX idx_items_user_id ON items(user_id);
"""
            else:
                # Simplified generic schema for other databases
                schema = f"""-- This is a generic {db_type} schema template.
-- Please modify according to {db_type}'s specific syntax.

-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Items table
CREATE TABLE items (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    user_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Create index on items.user_id
CREATE INDEX idx_items_user_id ON items(user_id);
"""
            
            result = f"{db_type.upper()} Schema for: {description}\n\n```sql\n{schema}\n```"
            return result
            
        except Exception as e:
            logger.error(f"Error generating schema: {str(e)}")
            return f"Error generating schema: {str(e)}"
            
    def _optimize_query(self, db_type, query):
        """
        Optimize a SQL query for performance.
        
        Args:
            db_type: Type of database (postgresql, mysql, etc.)
            query: SQL query to optimize
            
        Returns:
            Optimized query with explanation
        """
        if db_type not in self.supported_db_types:
            return f"Error: Unsupported database type: {db_type}. Supported types: {', '.join(self.supported_db_types)}"
        
        try:
            # Try using AI Service for query optimization
            try:
                system_prompt = f"""
                You are a database performance expert specializing in {db_type}.
                Analyze and optimize the provided SQL query.
                Consider:
                
                1. Proper indexing suggestions
                2. Query structure and joins
                3. Selection of columns (avoid SELECT *)
                4. Limiting result sets appropriately
                5. Proper use of WHERE clauses
                6. Usage of appropriate built-in functions
                
                Provide the optimized query and explain each optimization step.
                Include performance implications and reasoning.
                """
                
                if 'claude' in ai_service.models:
                    logger.debug(f"Using AI Service to optimize {db_type} query: {query}")
                    response = ai_service.models['claude'].messages.create(
                        model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": f"Please optimize this {db_type} query: {query}"}
                        ],
                        temperature=0.1,
                        max_tokens=2000
                    )
                    ai_output = response.content[0].text
                    
                    result = f"Query Optimization for {db_type}:\n\n"
                    result += f"Original query:\n```sql\n{query}\n```\n\n"
                    result += ai_output
                    return result
                    
            except Exception as ai_err:
                logger.warning(f"AI Service query optimization failed: {str(ai_err)}. Falling back to basic optimization rules.")
            
            # Basic query optimization suggestions as fallback
            result = f"Query Optimization for {db_type}:\n\n"
            result += f"Original query:\n```sql\n{query}\n```\n\n"
            
            # Pattern-based optimization suggestions
            suggestions = []
            
            # Check for SELECT *
            if "SELECT *" in query.upper():
                suggestions.append("Avoid using SELECT * - specify only the columns you need to reduce data transfer and improve performance.")
            
            # Check for missing WHERE clause
            if "WHERE" not in query.upper() and "SELECT" in query.upper() and "FROM" in query.upper():
                suggestions.append("Consider adding a WHERE clause to limit results if appropriate.")
            
            # Check for JOIN without criteria
            if "JOIN" in query.upper() and "ON" not in query.upper():
                suggestions.append("Ensure all JOINs have proper ON conditions to avoid cartesian products.")
            
            # Check for GROUP BY without index
            if "GROUP BY" in query.upper():
                suggestions.append("Ensure columns in GROUP BY have appropriate indexes.")
            
            # Check for ORDER BY on non-indexed columns
            if "ORDER BY" in query.upper():
                suggestions.append("Ensure columns in ORDER BY have appropriate indexes, especially for large result sets.")
            
            # Database-specific suggestions
            if db_type == "postgresql":
                if "LIKE" in query.upper():
                    suggestions.append("For pattern matching in PostgreSQL, consider using trigram indexes (pg_trgm) for LIKE queries.")
                
                if "DISTINCT" in query.upper():
                    suggestions.append("DISTINCT operations can be expensive. Consider if you can restructure your query to avoid needing DISTINCT.")
                
                if "JOIN" in query.upper() and "INNER JOIN" not in query.upper() and "LEFT JOIN" not in query.upper() and "RIGHT JOIN" not in query.upper():
                    suggestions.append("Specify the type of JOIN explicitly (INNER JOIN, LEFT JOIN, etc.) for better readability and optimization.")
            
            elif db_type == "mysql":
                if "TEXT" in query.upper() and "LIKE" in query.upper():
                    suggestions.append("In MySQL, LIKE operations on TEXT columns can be slow. Consider using FULLTEXT indexes for text searches.")
                
                if "ORDER BY RAND()" in query.upper():
                    suggestions.append("ORDER BY RAND() is extremely inefficient for large tables. Consider alternative methods for randomization.")
            
            # Optimized version (simplified)
            optimized_query = query.replace("SELECT *", "SELECT id, name, created_at") if "SELECT *" in query else query
            
            if suggestions:
                result += "Optimization Suggestions:\n"
                for i, suggestion in enumerate(suggestions, 1):
                    result += f"{i}. {suggestion}\n"
                result += "\n"
            else:
                result += "No obvious optimization issues detected. For a more thorough analysis, consider using EXPLAIN or EXPLAIN ANALYZE with your query.\n\n"
            
            result += f"Simplified optimized query (basic improvements only):\n```sql\n{optimized_query}\n```\n\n"
            result += "Note: This is a basic optimization. For complex queries, consider database-specific performance tuning and proper indexing strategy."
            
            return result
            
        except Exception as e:
            logger.error(f"Error optimizing query: {str(e)}")
            return f"Error optimizing query: {str(e)}"
            
    def _security_audit(self, db_type, query_or_schema):
        """
        Perform a security audit on a database query or schema.
        
        Args:
            db_type: Type of database (postgresql, mysql, etc.)
            query_or_schema: SQL query or schema to audit
            
        Returns:
            Security analysis and recommendations
        """
        if db_type not in self.supported_db_types:
            return f"Error: Unsupported database type: {db_type}. Supported types: {', '.join(self.supported_db_types)}"
        
        try:
            # Try using AI Service for security audit
            try:
                system_prompt = f"""
                You are a database security expert specializing in {db_type}.
                Perform a comprehensive security audit on the provided SQL query or schema.
                Look for:
                
                1. SQL injection vulnerabilities
                2. Excessive permissions or privilege issues
                3. Sensitive data exposure risks
                4. Missing input validation
                5. Insecure configurations
                6. Weak authentication mechanisms
                7. Improper error handling
                
                Provide specific recommendations to mitigate each identified issue.
                Include code examples where appropriate.
                Format your response with clear sections for each vulnerability category.
                """
                
                if 'claude' in ai_service.models:
                    logger.debug(f"Using AI Service for {db_type} security audit")
                    response = ai_service.models['claude'].messages.create(
                        model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": f"Please perform a security audit on this {db_type} query or schema: {query_or_schema}"}
                        ],
                        temperature=0.1,
                        max_tokens=2000
                    )
                    ai_output = response.content[0].text
                    
                    result = f"Database Security Audit ({db_type}):\n\n"
                    result += f"Analyzed SQL:\n```sql\n{query_or_schema}\n```\n\n"
                    result += ai_output
                    return result
                    
            except Exception as ai_err:
                logger.warning(f"AI Service security audit failed: {str(ai_err)}. Falling back to basic security checks.")
            
            # Basic security checks as fallback
            result = f"Database Security Audit ({db_type}):\n\n"
            result += f"Analyzed SQL:\n```sql\n{query_or_schema}\n```\n\n"
            
            # Check for common security issues
            issues = []
            
            # Check for SQL injection vulnerabilities
            if "'" in query_or_schema and ("WHERE" in query_or_schema.upper() or "VALUES" in query_or_schema.upper()):
                issues.append({
                    "category": "SQL Injection Risk",
                    "description": "String concatenation or direct inclusion of user input can lead to SQL injection attacks.",
                    "recommendation": "Use parameterized queries or prepared statements instead of building SQL strings with user input."
                })
            
            # Check for excessive permissions
            if "GRANT" in query_or_schema.upper() and "ALL" in query_or_schema.upper():
                issues.append({
                    "category": "Excessive Permissions",
                    "description": "Granting ALL privileges is usually too permissive and violates the principle of least privilege.",
                    "recommendation": "Grant only the specific permissions needed (SELECT, INSERT, etc.) rather than ALL privileges."
                })
            
            # Check for weak passwords
            if "PASSWORD" in query_or_schema.upper() or "IDENTIFIED BY" in query_or_schema.upper():
                if re.search(r"'[^']{1,8}'", query_or_schema):  # Simple check for short passwords
                    issues.append({
                        "category": "Weak Authentication",
                        "description": "Short or simple passwords detected in database setup.",
                        "recommendation": "Use strong, complex passwords and consider implementing password policies."
                    })
            
            # Check for public access
            if "'%'" in query_or_schema and "USER" in query_or_schema.upper():
                issues.append({
                    "category": "Unrestricted Access",
                    "description": "Allowing connections from any host ('%') exposes the database to broader network access.",
                    "recommendation": "Restrict access to specific IP addresses or networks instead of using '%'."
                })
            
            # Check for sensitive data in table definitions
            sensitive_terms = ["password", "ssn", "credit", "card", "social", "security", "secret", "token", "key"]
            for term in sensitive_terms:
                if term in query_or_schema.lower() and "ENCRYPT" not in query_or_schema.upper() and "HASH" not in query_or_schema.upper():
                    issues.append({
                        "category": "Sensitive Data Exposure",
                        "description": f"Potential storage of sensitive data ('{term}') without encryption.",
                        "recommendation": "Ensure sensitive data is encrypted at rest and in transit. Use appropriate data types and encryption methods."
                    })
                    break
            
            # Format results
            if issues:
                result += "Security Issues Detected:\n\n"
                for i, issue in enumerate(issues, 1):
                    result += f"{i}. {issue['category']}\n"
                    result += f"   Description: {issue['description']}\n"
                    result += f"   Recommendation: {issue['recommendation']}\n\n"
            else:
                result += "No obvious security issues detected. However, this is a basic scan and not a comprehensive security audit.\n\n"
            
            # General security best practices
            result += "General Database Security Best Practices:\n\n"
            result += "1. Use parameterized queries to prevent SQL injection\n"
            result += "2. Implement the principle of least privilege for database users\n"
            result += "3. Encrypt sensitive data at rest and in transit\n"
            result += "4. Regularly backup your database and test restore procedures\n"
            result += "5. Keep your database software up to date\n"
            result += "6. Implement proper error handling to avoid information leakage\n"
            result += "7. Audit and log database access and changes\n"
            result += "8. Use strong authentication and consider multi-factor authentication for database access\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error performing security audit: {str(e)}")
            return f"Error performing security audit: {str(e)}"
            
    def _generate_migration(self, db_type, description):
        """
        Generate a database migration script.
        
        Args:
            db_type: Type of database (postgresql, mysql, etc.)
            description: Description of the migration changes
            
        Returns:
            Migration script
        """
        if db_type not in self.supported_db_types:
            return f"Error: Unsupported database type: {db_type}. Supported types: {', '.join(self.supported_db_types)}"
        
        try:
            # Try using AI Service for migration generation
            try:
                system_prompt = f"""
                You are a database migration expert specializing in {db_type}.
                Generate a migration script based on the user's description.
                Include:
                
                1. Both forward (up) and rollback (down) migrations
                2. Proper syntax for {db_type}
                3. Safe migration practices to avoid data loss
                4. Proper indexing for new columns or tables
                5. Explicit comments explaining each step
                
                Use best practices for database migrations in {db_type}.
                """
                
                if 'claude' in ai_service.models:
                    logger.debug(f"Using AI Service to generate {db_type} migration for: {description}")
                    response = ai_service.models['claude'].messages.create(
                        model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": f"Please generate a {db_type} migration script for: {description}"}
                        ],
                        temperature=0.1,
                        max_tokens=2000
                    )
                    ai_output = response.content[0].text
                    
                    result = f"Database Migration for: {description} ({db_type})\n\n"
                    result += ai_output
                    return result
                    
            except Exception as ai_err:
                logger.warning(f"AI Service migration generation failed: {str(ai_err)}. Falling back to template migrations.")
            
            # Basic migration templates as fallback
            if db_type == "postgresql":
                if "add" in description.lower() and "column" in description.lower():
                    table_name = "users"  # Default table, would be better if extracted from description
                    column_matches = re.search(r'add ([\w_]+) column', description.lower())
                    column_name = column_matches.group(1) if column_matches else "new_column"
                    
                    data_type = "VARCHAR(255)"
                    if "email" in column_name:
                        data_type = "VARCHAR(100)"
                    elif "date" in column_name or "time" in column_name:
                        data_type = "TIMESTAMP"
                    elif "price" in column_name or "amount" in column_name:
                        data_type = "DECIMAL(10, 2)"
                    elif "is_" in column_name or "has_" in column_name:
                        data_type = "BOOLEAN DEFAULT FALSE"
                    
                    migration = f"""-- Migration: Add {column_name} column to {table_name}

-- Up Migration
ALTER TABLE {table_name}
ADD COLUMN {column_name} {data_type};

-- Add an index if this column will be frequently queried
CREATE INDEX idx_{table_name}_{column_name} ON {table_name}({column_name});

-- Down Migration (rollback)
-- ALTER TABLE {table_name} DROP COLUMN {column_name};
"""
                elif "create" in description.lower() and "table" in description.lower():
                    table_matches = re.search(r'create ([\w_]+) table', description.lower())
                    table_name = table_matches.group(1) if table_matches else "new_table"
                    
                    migration = f"""-- Migration: Create {table_name} table

-- Up Migration
CREATE TABLE {table_name} (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create an index on the name column
CREATE INDEX idx_{table_name}_name ON {table_name}(name);

-- Down Migration (rollback)
-- DROP TABLE {table_name};
"""
                else:
                    migration = f"""-- Migration: {description}

-- Up Migration
-- Replace with actual migration code based on {description}
-- For example:
-- ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;

-- Down Migration (rollback)
-- Replace with rollback code
-- For example:
-- ALTER TABLE users DROP COLUMN email_verified;
"""
            elif db_type == "mysql":
                if "add" in description.lower() and "column" in description.lower():
                    table_name = "users"  # Default table
                    column_matches = re.search(r'add ([\w_]+) column', description.lower())
                    column_name = column_matches.group(1) if column_matches else "new_column"
                    
                    data_type = "VARCHAR(255)"
                    if "email" in column_name:
                        data_type = "VARCHAR(100)"
                    elif "date" in column_name or "time" in column_name:
                        data_type = "TIMESTAMP"
                    elif "price" in column_name or "amount" in column_name:
                        data_type = "DECIMAL(10, 2)"
                    elif "is_" in column_name or "has_" in column_name:
                        data_type = "BOOLEAN DEFAULT FALSE"
                    
                    migration = f"""-- Migration: Add {column_name} column to {table_name}

-- Up Migration
ALTER TABLE {table_name}
ADD COLUMN {column_name} {data_type};

-- Add an index if this column will be frequently queried
CREATE INDEX idx_{table_name}_{column_name} ON {table_name}({column_name});

-- Down Migration (rollback)
-- ALTER TABLE {table_name} DROP COLUMN {column_name};
"""
                else:
                    migration = f"""-- Migration: {description}

-- Up Migration
-- Replace with actual migration code based on {description}
-- For example:
-- ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT FALSE;

-- Down Migration (rollback)
-- Replace with rollback code
-- For example:
-- ALTER TABLE users DROP COLUMN email_verified;
"""
            else:
                migration = f"""-- Migration for {db_type}: {description}

-- This is a template. Please adjust syntax for {db_type}.

-- Up Migration
-- Replace with actual migration code based on {description}

-- Down Migration (rollback)
-- Replace with rollback code
"""
                
            result = f"Database Migration for: {description} ({db_type})\n\n```sql\n{migration}\n```\n\n"
            result += "Note: This is a template migration. You should review and adjust it to your specific database schema."
            return result
            
        except Exception as e:
            logger.error(f"Error generating migration: {str(e)}")
            return f"Error generating migration: {str(e)}"
            
    def _document_schema(self, db_type, schema):
        """
        Generate documentation for a database schema.
        
        Args:
            db_type: Type of database (postgresql, mysql, etc.)
            schema: Database schema to document
            
        Returns:
            Schema documentation
        """
        if db_type not in self.supported_db_types:
            return f"Error: Unsupported database type: {db_type}. Supported types: {', '.join(self.supported_db_types)}"
        
        try:
            # Try using AI Service for schema documentation
            try:
                system_prompt = f"""
                You are a database documentation expert specializing in {db_type}.
                Generate comprehensive documentation for the provided database schema.
                Include:
                
                1. Overview of the database design
                2. Entity-relationship descriptions
                3. Table purposes and descriptions
                4. Column details (data types, constraints, purposes)
                5. Index explanations and performance considerations
                6. Constraints and integrity rules
                7. Relationships between tables
                
                Format your response in clear sections with markdown formatting.
                Make the documentation accessible to both technical and non-technical stakeholders.
                """
                
                if 'claude' in ai_service.models:
                    logger.debug(f"Using AI Service to document {db_type} schema")
                    response = ai_service.models['claude'].messages.create(
                        model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": f"Please document this {db_type} schema:\n\n{schema}"}
                        ],
                        temperature=0.1,
                        max_tokens=2500
                    )
                    ai_output = response.content[0].text
                    
                    result = f"Database Schema Documentation ({db_type}):\n\n"
                    result += ai_output
                    return result
                    
            except Exception as ai_err:
                logger.warning(f"AI Service schema documentation failed: {str(ai_err)}. Falling back to basic documentation.")
            
            # Basic schema documentation as fallback
            result = f"Database Schema Documentation ({db_type}):\n\n"
            result += f"Original Schema:\n```sql\n{schema}\n```\n\n"
            
            # Extract table information (very basic parsing)
            tables = []
            current_table = None
            
            for line in schema.split('\n'):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('--') or line.startswith('/*'):
                    continue
                
                # Find CREATE TABLE statements
                if "CREATE TABLE" in line.upper():
                    table_match = re.search(r'CREATE TABLE [\"`]?(\w+)[\"`]?', line, re.IGNORECASE)
                    if table_match:
                        current_table = {
                            "name": table_match.group(1),
                            "columns": [],
                            "constraints": []
                        }
                        tables.append(current_table)
                
                # End of table definition
                elif current_table and line.startswith(');'):
                    current_table = None
                
                # Column definitions
                elif current_table and "," in line:
                    # This is a very simplified parser and won't catch all valid SQL
                    col_match = re.search(r'[\"`]?(\w+)[\"`]?\s+([^,]+)', line)
                    if col_match and not line.upper().startswith('PRIMARY KEY') and not line.upper().startswith('FOREIGN KEY'):
                        col_name = col_match.group(1)
                        col_type = col_match.group(2).strip()
                        current_table["columns"].append({
                            "name": col_name,
                            "type": col_type
                        })
                
                # Constraints
                elif current_table and ("PRIMARY KEY" in line.upper() or "FOREIGN KEY" in line.upper() or "CONSTRAINT" in line.upper()):
                    current_table["constraints"].append(line.rstrip(','))
            
            # Format documentation
            result += "# Database Documentation\n\n"
            
            if tables:
                result += "## Tables Overview\n\n"
                for table in tables:
                    result += f"- **{table['name']}**: Contains {len(table['columns'])} columns\n"
                
                result += "\n## Table Details\n\n"
                for table in tables:
                    result += f"### {table['name']}\n\n"
                    
                    # Columns
                    result += "#### Columns\n\n"
                    result += "| Column Name | Data Type | Description |\n"
                    result += "|-------------|-----------|-------------|\n"
                    for column in table["columns"]:
                        # Attempt to generate a basic description based on the column name and type
                        description = ""
                        if column["name"].lower() == "id":
                            description = "Primary identifier for the record"
                        elif "name" in column["name"].lower():
                            description = "Name or title"
                        elif "description" in column["name"].lower():
                            description = "Detailed description or information"
                        elif "created" in column["name"].lower() and "at" in column["name"].lower():
                            description = "Timestamp when the record was created"
                        elif "updated" in column["name"].lower() and "at" in column["name"].lower():
                            description = "Timestamp when the record was last updated"
                        elif "user" in column["name"].lower() and "id" in column["name"].lower():
                            description = "Reference to a user record"
                        elif "email" in column["name"].lower():
                            description = "Email address"
                        elif "password" in column["name"].lower():
                            description = "Hashed password (never store plaintext passwords)"
                        
                        result += f"| {column['name']} | {column['type']} | {description} |\n"
                    
                    # Constraints
                    if table["constraints"]:
                        result += "\n#### Constraints\n\n"
                        for constraint in table["constraints"]:
                            result += f"- `{constraint}`\n"
                    
                    result += "\n"
            else:
                result += "No table definitions found in the provided schema.\n"
            
            result += "\n## Relationships\n\n"
            result += "Relationships between tables should be defined by foreign key constraints. Please review the schema for specific relationships.\n\n"
            
            result += "## Performance Considerations\n\n"
            result += "- Ensure proper indexes are created for columns used in WHERE, JOIN, and ORDER BY clauses\n"
            result += "- Consider adding indexes for foreign key columns\n"
            result += "- Monitor query performance and adjust indexes as needed\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error documenting schema: {str(e)}")
            return f"Error documenting schema: {str(e)}"