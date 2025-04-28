import os
import re
import logging
import subprocess
import json
import platform
import psutil
from typing import List, Dict, Any, Optional
from agents.base_agent import BaseAgent
from ai_service import ai_service

# Set up logging
logger = logging.getLogger(__name__)

class DevOpsAgent(BaseAgent):
    """
    The DevOps Agent - specialized in automation, deployment, and monitoring.
    
    This agent can help with tasks like:
    - Setting up CI/CD pipelines
    - Managing containerization with Docker
    - Configuring cloud infrastructure
    - Monitoring system performance
    - Automating deployment processes
    - Implementing infrastructure as code
    """
    
    def __init__(self):
        """Initialize the DevOps Agent."""
        super().__init__(
            name="DevOpsAgent",
            description="Specialized in automation, deployment, and infrastructure management."
        )
        self.supported_platforms = [
            "docker", "kubernetes", "aws", "azure", "gcp", "github-actions", "jenkins", "gitlab-ci", "terraform", "ansible"
        ]
        
    def get_commands(self):
        """Return the commands this agent can handle."""
        return {
            "docker-setup": {
                "description": "Generate Docker configuration files",
                "usage": "docker-setup <app_type> [options]",
                "examples": [
                    "docker-setup flask",
                    "docker-setup nodejs --with-database"
                ]
            },
            "ci-pipeline": {
                "description": "Create CI/CD pipeline configuration",
                "usage": "ci-pipeline <platform> <app_type>",
                "examples": [
                    "ci-pipeline github-actions python",
                    "ci-pipeline gitlab-ci nodejs"
                ]
            },
            "infrastructure": {
                "description": "Generate infrastructure as code templates",
                "usage": "infrastructure <platform> <resource_type>",
                "examples": [
                    "infrastructure terraform aws-ec2",
                    "infrastructure ansible web-server"
                ]
            },
            "monitor-setup": {
                "description": "Setup monitoring configuration",
                "usage": "monitor-setup <platform> [options]",
                "examples": [
                    "monitor-setup prometheus",
                    "monitor-setup cloudwatch --with-alarms"
                ]
            },
            "deployment": {
                "description": "Generate deployment scripts or configurations",
                "usage": "deployment <platform> <app_type>",
                "examples": [
                    "deployment kubernetes python-app",
                    "deployment heroku nodejs-app"
                ]
            }
        }
    
    def execute(self, command, args):
        """Execute a DevOpsAgent command."""
        try:
            if command == "docker-setup":
                if not args:
                    return "Error: Missing application type. Usage: docker-setup <app_type> [options]"
                app_type = args[0].lower()
                options = args[1:] if len(args) > 1 else []
                return self._docker_setup(app_type, options)
                
            elif command == "ci-pipeline":
                if len(args) < 2:
                    return "Error: Missing platform or application type. Usage: ci-pipeline <platform> <app_type>"
                platform = args[0].lower()
                app_type = args[1].lower()
                return self._ci_pipeline(platform, app_type)
                
            elif command == "infrastructure":
                if len(args) < 2:
                    return "Error: Missing platform or resource type. Usage: infrastructure <platform> <resource_type>"
                platform = args[0].lower()
                resource_type = args[1].lower()
                return self._infrastructure(platform, resource_type)
                
            elif command == "monitor-setup":
                if not args:
                    return "Error: Missing platform. Usage: monitor-setup <platform> [options]"
                platform = args[0].lower()
                options = args[1:] if len(args) > 1 else []
                return self._monitor_setup(platform, options)
                
            elif command == "deployment":
                if len(args) < 2:
                    return "Error: Missing platform or application type. Usage: deployment <platform> <app_type>"
                platform = args[0].lower()
                app_type = args[1].lower()
                return self._deployment(platform, app_type)
                
            else:
                return f"Unknown command: '{command}'"
                
        except Exception as e:
            logger.error(f"Error in DevOpsAgent: {str(e)}")
            return f"Error executing command: {str(e)}"

    def _docker_setup(self, app_type, options):
        """
        Generate Docker configuration files.
        
        Args:
            app_type: Type of application (flask, nodejs, etc.)
            options: Additional options
            
        Returns:
            Docker configuration files
        """
        try:
            with_database = "--with-database" in options
            multi_stage = "--multi-stage" in options
            
            # Try using AI Service for Dockerfile generation
            try:
                system_prompt = f"""
                You are a DevOps expert specializing in Docker containerization.
                Generate Docker configuration files for a {app_type} application.
                
                Include:
                1. A well-structured Dockerfile with best practices
                2. Docker Compose configuration if appropriate
                3. Clear comments explaining each section
                4. Proper security considerations
                5. Optimized image size and build process
                
                {"Include database configuration in docker-compose.yml" if with_database else ""}
                {"Use multi-stage builds for optimized images" if multi_stage else ""}
                
                Format your response with clear file headers and code blocks.
                """
                
                if 'claude' in ai_service.models:
                    logger.debug(f"Using AI Service to generate Docker configuration for {app_type}")
                    response = ai_service.models['claude'].messages.create(
                        model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": f"Please generate Docker configuration files for a {app_type} application. {' Include database setup.' if with_database else ''} {' Use multi-stage build.' if multi_stage else ''}"}
                        ],
                        temperature=0.1,
                        max_tokens=2500
                    )
                    ai_output = response.content[0].text
                    
                    result = f"Docker Configuration for {app_type}:\n\n"
                    result += ai_output
                    return result
                    
            except Exception as ai_err:
                logger.warning(f"AI Service Docker configuration generation failed: {str(ai_err)}. Falling back to templates.")
            
            # Basic Dockerfile templates as fallback
            dockerfile = ""
            docker_compose = ""
            
            if app_type == "flask" or app_type == "python":
                if multi_stage:
                    dockerfile = """# Dockerfile for Flask/Python application with multi-stage build

# ---- Build Stage ----
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends gcc

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# ---- Final Stage ----
FROM python:3.11-slim

WORKDIR /app

# Create a non-root user to run the application
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy wheels from builder stage
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application code
COPY . .

# Set proper permissions
RUN chown -R appuser:appuser /app
USER appuser

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PORT=5000

# Expose the port the app runs on
EXPOSE ${PORT}

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
"""
                else:
                    dockerfile = """# Dockerfile for Flask/Python application

FROM python:3.11-slim

WORKDIR /app

# Create a non-root user to run the application
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set proper permissions
RUN chown -R appuser:appuser /app
USER appuser

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \\
    PYTHONUNBUFFERED=1 \\
    PORT=5000

# Expose the port the app runs on
EXPOSE ${PORT}

# Command to run the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
"""
                
                if with_database:
                    docker_compose = """version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/postgres
    depends_on:
      - db
    restart: always
    volumes:
      - ./:/app
    networks:
      - app-network

  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_DB=postgres
    ports:
      - "5432:5432"
    restart: always
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  postgres_data:
"""
                else:
                    docker_compose = """version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    restart: always
    volumes:
      - ./:/app
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
"""
                    
            elif app_type == "nodejs" or app_type == "express":
                if multi_stage:
                    dockerfile = """# Dockerfile for Node.js application with multi-stage build

# ---- Build Stage ----
FROM node:18-slim AS builder

WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# If you have a build step (e.g., for TypeScript)
# RUN npm run build

# ---- Final Stage ----
FROM node:18-slim

WORKDIR /app

# Create a non-root user to run the application
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy from builder stage
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app ./

# Set proper permissions
RUN chown -R appuser:appuser /app
USER appuser

# Set environment variables
ENV NODE_ENV=production \\
    PORT=3000

# Expose the port the app runs on
EXPOSE ${PORT}

# Command to run the application
CMD ["node", "app.js"]
"""
                else:
                    dockerfile = """# Dockerfile for Node.js application

FROM node:18-slim

WORKDIR /app

# Create a non-root user to run the application
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Set proper permissions
RUN chown -R appuser:appuser /app
USER appuser

# Set environment variables
ENV NODE_ENV=production \\
    PORT=3000

# Expose the port the app runs on
EXPOSE ${PORT}

# Command to run the application
CMD ["node", "app.js"]
"""
                
                if with_database:
                    docker_compose = """version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/postgres
    depends_on:
      - db
    restart: always
    volumes:
      - ./:/app
      - /app/node_modules
    networks:
      - app-network

  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_DB=postgres
    ports:
      - "5432:5432"
    restart: always
    networks:
      - app-network

networks:
  app-network:
    driver: bridge

volumes:
  postgres_data:
"""
                else:
                    docker_compose = """version: '3.8'

services:
  app:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
    restart: always
    volumes:
      - ./:/app
      - /app/node_modules
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
"""
            else:
                # Generic template
                dockerfile = f"""# Dockerfile for {app_type} application

# Replace with the appropriate base image for {app_type}
FROM base-image:latest

WORKDIR /app

# Install dependencies
# COPY dependencies-file .
# RUN install-dependencies-command

# Copy application code
COPY . .

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application
CMD ["start-application-command"]
"""
                
                docker_compose = """version: '3.8'

services:
  app:
    build: .
    ports:
      - "8080:8080"
    restart: always
    volumes:
      - ./:/app
    networks:
      - app-network

networks:
  app-network:
    driver: bridge
"""
                if with_database:
                    docker_compose += """
  db:
    image: postgres:14
    volumes:
      - postgres_data:/var/lib/postgresql/data/
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_DB=postgres
    ports:
      - "5432:5432"
    restart: always
    networks:
      - app-network

volumes:
  postgres_data:
"""
            
            result = f"Docker Configuration for {app_type}:\n\n"
            result += "## Dockerfile\n\n```dockerfile\n" + dockerfile + "\n```\n\n"
            
            if docker_compose:
                result += "## docker-compose.yml\n\n```yaml\n" + docker_compose + "\n```\n\n"
                
            result += "## Usage Instructions\n\n"
            result += "1. Save the Dockerfile in your project root directory\n"
            if docker_compose:
                result += "2. Save the docker-compose.yml file in your project root directory\n"
                result += "3. Build and run your application with: `docker-compose up --build`\n"
            else:
                result += "2. Build the Docker image: `docker build -t your-app-name .`\n"
                result += "3. Run the container: `docker run -p 5000:5000 your-app-name`\n"
                
            return result
            
        except Exception as e:
            logger.error(f"Error generating Docker configuration: {str(e)}")
            return f"Error generating Docker configuration: {str(e)}"
            
    def _ci_pipeline(self, platform, app_type):
        """
        Create CI/CD pipeline configuration.
        
        Args:
            platform: CI/CD platform (github-actions, gitlab-ci, etc.)
            app_type: Type of application (python, nodejs, etc.)
            
        Returns:
            CI/CD pipeline configuration
        """
        try:
            # Try using AI Service for CI/CD configuration
            try:
                system_prompt = f"""
                You are a DevOps expert specializing in CI/CD pipelines.
                Generate a {platform} CI/CD pipeline configuration for a {app_type} application.
                
                Include:
                1. Build and test stages
                2. Proper caching for dependencies
                3. Linting and code quality checks
                4. Security scanning
                5. Deployment configuration
                6. Clear comments explaining each section
                
                Format your response with clear file headers and code blocks.
                Use current best practices for {platform} and {app_type}.
                """
                
                if 'claude' in ai_service.models:
                    logger.debug(f"Using AI Service to generate {platform} pipeline for {app_type}")
                    response = ai_service.models['claude'].messages.create(
                        model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": f"Please generate a {platform} CI/CD pipeline configuration for a {app_type} application."}
                        ],
                        temperature=0.1,
                        max_tokens=2500
                    )
                    ai_output = response.content[0].text
                    
                    result = f"CI/CD Pipeline Configuration ({platform} for {app_type}):\n\n"
                    result += ai_output
                    return result
                    
            except Exception as ai_err:
                logger.warning(f"AI Service CI/CD configuration generation failed: {str(ai_err)}. Falling back to templates.")
            
            # Basic CI/CD templates as fallback
            ci_config = ""
            filename = ""
            
            if platform == "github-actions":
                filename = ".github/workflows/ci-cd.yml"
                
                if app_type == "python" or app_type == "flask":
                    ci_config = """name: Python CI/CD Pipeline

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        python-version: [3.9, 3.11]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Cache dependencies
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install flake8 pytest pytest-cov
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
    
    - name: Lint with flake8
      run: |
        # stop the build if there are Python syntax errors or undefined names
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        # exit-zero treats all errors as warnings
        flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    
    - name: Test with pytest
      run: |
        pytest --cov=. --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: false

  deploy:
    needs: test
    if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master')
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
    
    # Uncomment and customize deployment steps based on your target platform
    # - name: Deploy to Production
    #   run: |
    #     # Add your deployment commands here
    #     echo "Deploying to production"
"""
                
                elif app_type == "nodejs" or app_type == "express":
                    ci_config = """name: Node.js CI/CD Pipeline

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    strategy:
      matrix:
        node-version: [16.x, 18.x]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Use Node.js ${{ matrix.node-version }}
      uses: actions/setup-node@v3
      with:
        node-version: ${{ matrix.node-version }}
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Lint
      run: npm run lint
      if: ${{ always() }}
    
    - name: Test
      run: npm test
    
    - name: Build
      run: npm run build --if-present

  deploy:
    needs: test
    if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master')
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Use Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18.x'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Build
      run: npm run build --if-present
    
    # Uncomment and customize deployment steps based on your target platform
    # - name: Deploy to Production
    #   run: |
    #     # Add your deployment commands here
    #     echo "Deploying to production"
"""
                
                else:
                    # Generic GitHub Actions template
                    ci_config = f"""name: CI/CD Pipeline

on:
  push:
    branches: [ main, master ]
  pull_request:
    branches: [ main, master ]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup environment
      run: |
        echo "Setting up environment for {app_type}"
    
    - name: Install dependencies
      run: |
        echo "Installing dependencies for {app_type}"
    
    - name: Lint
      run: |
        echo "Running linting for {app_type}"
    
    - name: Test
      run: |
        echo "Running tests for {app_type}"
    
    - name: Build
      run: |
        echo "Building {app_type} application"

  deploy:
    needs: build
    if: github.event_name == 'push' && (github.ref == 'refs/heads/main' || github.ref == 'refs/heads/master')
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup environment
      run: |
        echo "Setting up environment for deployment"
    
    - name: Deploy
      run: |
        echo "Deploying {app_type} application"
"""
                
            elif platform == "gitlab-ci":
                filename = ".gitlab-ci.yml"
                
                if app_type == "python" or app_type == "flask":
                    ci_config = """stages:
  - lint
  - test
  - build
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.pip-cache"

cache:
  paths:
    - .pip-cache/

lint:
  stage: lint
  image: python:3.11
  script:
    - pip install flake8
    - flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
    - flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

test:
  stage: test
  image: python:3.11
  script:
    - pip install pytest pytest-cov
    - pip install -r requirements.txt
    - pytest --cov=. --cov-report=xml
  artifacts:
    paths:
      - coverage.xml
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

build:
  stage: build
  image: python:3.11
  script:
    - pip install build
    - python -m build
  artifacts:
    paths:
      - dist/
  only:
    - main
    - master

deploy:
  stage: deploy
  image: python:3.11
  script:
    - echo "Deploying application..."
    # Add your deployment commands here
  environment:
    name: production
  only:
    - main
    - master
"""
                
                elif app_type == "nodejs" or app_type == "express":
                    ci_config = """stages:
  - lint
  - test
  - build
  - deploy

variables:
  NPM_CACHE_DIR: "$CI_PROJECT_DIR/.npm-cache"

cache:
  paths:
    - .npm-cache/
    - node_modules/

lint:
  stage: lint
  image: node:18
  script:
    - npm ci
    - npm run lint

test:
  stage: test
  image: node:18
  script:
    - npm ci
    - npm test
  artifacts:
    paths:
      - coverage/
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage/cobertura-coverage.xml

build:
  stage: build
  image: node:18
  script:
    - npm ci
    - npm run build
  artifacts:
    paths:
      - dist/
      - build/
  only:
    - main
    - master

deploy:
  stage: deploy
  image: node:18
  script:
    - echo "Deploying application..."
    # Add your deployment commands here
  environment:
    name: production
  only:
    - main
    - master
"""
                
                else:
                    # Generic GitLab CI template
                    ci_config = f"""stages:
  - lint
  - test
  - build
  - deploy

lint:
  stage: lint
  script:
    - echo "Linting {app_type} code"

test:
  stage: test
  script:
    - echo "Testing {app_type} application"

build:
  stage: build
  script:
    - echo "Building {app_type} application"
  artifacts:
    paths:
      - dist/
  only:
    - main
    - master

deploy:
  stage: deploy
  script:
    - echo "Deploying {app_type} application"
  environment:
    name: production
  only:
    - main
    - master
"""
                
            elif platform == "jenkins":
                filename = "Jenkinsfile"
                
                if app_type == "python" or app_type == "flask":
                    ci_config = """pipeline {
    agent {
        docker {
            image 'python:3.11'
        }
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'python -m pip install --upgrade pip'
                sh 'pip install -r requirements.txt'
                sh 'pip install flake8 pytest pytest-cov'
            }
        }
        
        stage('Lint') {
            steps {
                sh 'flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics'
                sh 'flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics'
            }
        }
        
        stage('Test') {
            steps {
                sh 'pytest --cov=. --cov-report=xml'
            }
            post {
                always {
                    junit 'test-reports/*.xml'
                    cobertura coberturaReportFile: 'coverage.xml'
                }
            }
        }
        
        stage('Build') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                sh 'python -m build'
            }
        }
        
        stage('Deploy') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                echo 'Deploying application...'
                // Add your deployment commands here
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
    }
}
"""
                
                elif app_type == "nodejs" or app_type == "express":
                    ci_config = """pipeline {
    agent {
        docker {
            image 'node:18'
        }
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'npm ci'
            }
        }
        
        stage('Lint') {
            steps {
                sh 'npm run lint'
            }
        }
        
        stage('Test') {
            steps {
                sh 'npm test'
            }
            post {
                always {
                    junit 'test-reports/*.xml'
                }
            }
        }
        
        stage('Build') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                sh 'npm run build'
            }
        }
        
        stage('Deploy') {
            when {
                anyOf {
                    branch 'main'
                    branch 'master'
                }
            }
            steps {
                echo 'Deploying application...'
                // Add your deployment commands here
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
    }
}
"""
                
                else:
                    # Generic Jenkinsfile template
                    ci_config = f"""pipeline {{
    agent any
    
    stages {{
        stage('Setup') {{
            steps {{
                echo 'Setting up environment for {app_type}'
            }}
        }}
        
        stage('Lint') {{
            steps {{
                echo 'Linting {app_type} code'
            }}
        }}
        
        stage('Test') {{
            steps {{
                echo 'Testing {app_type} application'
            }}
        }}
        
        stage('Build') {{
            when {{
                anyOf {{
                    branch 'main'
                    branch 'master'
                }}
            }}
            steps {{
                echo 'Building {app_type} application'
            }}
        }}
        
        stage('Deploy') {{
            when {{
                anyOf {{
                    branch 'main'
                    branch 'master'
                }}
            }}
            steps {{
                echo 'Deploying {app_type} application'
            }}
        }}
    }}
    
    post {{
        always {{
            cleanWs()
        }}
    }}
}}
"""
                
            else:
                # Generic CI template
                filename = f"{platform}-config.yml"
                ci_config = f"""# {platform} CI/CD configuration for {app_type}

# Define stages/jobs for your pipeline
# - Setup
# - Lint
# - Test
# - Build
# - Deploy

# Example configuration:
"""
            
            result = f"CI/CD Pipeline Configuration ({platform} for {app_type}):\n\n"
            result += f"## {filename}\n\n```yaml\n{ci_config}\n```\n\n"
            
            result += "## Setup Instructions\n\n"
            result += f"1. Create the file `{filename}` in your project repository\n"
            result += "2. Copy the configuration above into the file\n"
            result += "3. Customize the configuration to match your project's specific needs\n"
            
            if platform == "github-actions":
                result += "4. Ensure your repository has GitHub Actions enabled in the Settings tab\n"
            elif platform == "gitlab-ci":
                result += "4. Ensure your GitLab repository has CI/CD enabled in the Settings\n"
            elif platform == "jenkins":
                result += "4. Set up a Jenkins pipeline that uses this Jenkinsfile\n"
            
            result += "\nNote: This is a basic template. You'll need to adjust it based on your specific project requirements and deployment targets."
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating CI/CD configuration: {str(e)}")
            return f"Error generating CI/CD configuration: {str(e)}"
            
    def _infrastructure(self, platform, resource_type):
        """
        Generate infrastructure as code templates.
        
        Args:
            platform: Platform (terraform, ansible, etc.)
            resource_type: Type of resource to configure
            
        Returns:
            Infrastructure as code template
        """
        try:
            # Try using AI Service for infrastructure code generation
            try:
                system_prompt = f"""
                You are a DevOps expert specializing in infrastructure as code.
                Generate {platform} configuration for {resource_type}.
                
                Include:
                1. Complete and working configuration files
                2. Clear comments explaining each section
                3. Best practices for security and performance
                4. Variables for customization
                5. Resource naming conventions
                
                Format your response with clear file headers and code blocks.
                """
                
                if 'claude' in ai_service.models:
                    logger.debug(f"Using AI Service to generate {platform} configuration for {resource_type}")
                    response = ai_service.models['claude'].messages.create(
                        model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": f"Please generate {platform} infrastructure as code for {resource_type}."}
                        ],
                        temperature=0.1,
                        max_tokens=2500
                    )
                    ai_output = response.content[0].text
                    
                    result = f"Infrastructure as Code ({platform} for {resource_type}):\n\n"
                    result += ai_output
                    return result
                    
            except Exception as ai_err:
                logger.warning(f"AI Service infrastructure code generation failed: {str(ai_err)}. Falling back to templates.")
            
            # Basic infrastructure code templates as fallback
            if platform == "terraform":
                if "aws" in resource_type.lower():
                    if "ec2" in resource_type.lower():
                        code = """# main.tf - AWS EC2 Instance Configuration

# Configure the AWS Provider
provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-west-2"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "ami_id" {
  description = "AMI ID for the EC2 instance"
  type        = string
  default     = "ami-0c55b159cbfafe1f0" # Amazon Linux 2 AMI (replace with current AMI ID)
}

variable "key_name" {
  description = "SSH key name for EC2 instance"
  type        = string
}

variable "project_name" {
  description = "Name of the project for resource tagging"
  type        = string
  default     = "my-app"
}

# Security Group
resource "aws_security_group" "app_sg" {
  name        = "${var.project_name}-sg"
  description = "Security group for ${var.project_name} application"

  # HTTP access from anywhere
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTP"
  }

  # HTTPS access from anywhere
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "HTTPS"
  }

  # SSH access from specific IPs (replace with your IP)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
    description = "SSH"
  }

  # Outbound internet access
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = {
    Name    = "${var.project_name}-sg"
    Project = var.project_name
  }
}

# EC2 Instance
resource "aws_instance" "app_server" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  key_name               = var.key_name
  vpc_security_group_ids = [aws_security_group.app_sg.id]

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
    encrypted   = true
  }

  tags = {
    Name    = "${var.project_name}-server"
    Project = var.project_name
  }

  # User data for initialization (customize as needed)
  user_data = <<-EOF
              #!/bin/bash
              echo "Installing dependencies..."
              yum update -y
              yum install -y docker
              systemctl start docker
              systemctl enable docker
              echo "Setup complete!"
              EOF
}

# Output the public IP address
output "instance_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.app_server.public_ip
}

# Output the instance ID
output "instance_id" {
  description = "ID of the EC2 instance"
  value       = aws_instance.app_server.id
}
"""
                    elif "rds" in resource_type.lower():
                        code = """# main.tf - AWS RDS Database Configuration

# Configure the AWS Provider
provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-west-2"
}

variable "db_name" {
  description = "Name of the database"
  type        = string
  default     = "appdb"
}

variable "db_username" {
  description = "Username for the database"
  type        = string
  sensitive   = true
}

variable "db_password" {
  description = "Password for the database"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "Database instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "project_name" {
  description = "Name of the project for resource tagging"
  type        = string
  default     = "my-app"
}

# Security Group for RDS
resource "aws_security_group" "db_sg" {
  name        = "${var.project_name}-db-sg"
  description = "Security group for ${var.project_name} database"

  # PostgreSQL access from specified CIDR blocks (customize based on your VPC)
  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = ["10.0.0.0/8"]
    description = "PostgreSQL"
  }

  # Outbound internet access
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "All outbound traffic"
  }

  tags = {
    Name    = "${var.project_name}-db-sg"
    Project = var.project_name
  }
}

# Subnet group for RDS
resource "aws_db_subnet_group" "db_subnet_group" {
  name        = "${var.project_name}-db-subnet-group"
  description = "Subnet group for ${var.project_name} RDS database"
  subnet_ids  = ["subnet-12345678", "subnet-87654321"] # Replace with your subnet IDs

  tags = {
    Name    = "${var.project_name}-db-subnet-group"
    Project = var.project_name
  }
}

# RDS Instance
resource "aws_db_instance" "database" {
  allocated_storage      = 20
  storage_type           = "gp2"
  engine                 = "postgres"
  engine_version         = "14"
  instance_class         = var.db_instance_class
  identifier             = "${var.project_name}-db"
  db_name                = var.db_name
  username               = var.db_username
  password               = var.db_password
  parameter_group_name   = "default.postgres14"
  db_subnet_group_name   = aws_db_subnet_group.db_subnet_group.name
  vpc_security_group_ids = [aws_security_group.db_sg.id]
  multi_az               = false
  publicly_accessible    = false
  skip_final_snapshot    = true
  backup_retention_period = 7
  storage_encrypted       = true

  tags = {
    Name    = "${var.project_name}-db"
    Project = var.project_name
  }
}

# Output the database endpoint
output "db_endpoint" {
  description = "The endpoint of the database"
  value       = aws_db_instance.database.endpoint
}

# Output the database port
output "db_port" {
  description = "The port of the database"
  value       = aws_db_instance.database.port
}
"""
                    else:
                        code = """# main.tf - AWS Generic Infrastructure

# Configure the AWS Provider
provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-west-2"
}

variable "project_name" {
  description = "Name of the project for resource tagging"
  type        = string
  default     = "my-app"
}

# Configure other resources based on your specific needs
# For example:
# - VPC and networking
# - EC2 instances
# - RDS databases
# - S3 buckets
# - IAM roles and policies
# - CloudWatch alarms and logs

# Example resource
resource "aws_s3_bucket" "app_bucket" {
  bucket = "${var.project_name}-bucket"

  tags = {
    Name    = "${var.project_name}-bucket"
    Project = var.project_name
  }
}

# Example output
output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.app_bucket.bucket
}
"""
                
                elif "kubernetes" in resource_type.lower():
                    code = """# Terraform configuration for Kubernetes resources

# Configure the Kubernetes Provider
provider "kubernetes" {
  config_path = "~/.kube/config"
}

# Variables
variable "namespace" {
  description = "Kubernetes namespace for the application"
  type        = string
  default     = "my-app"
}

variable "app_name" {
  description = "Name of the application"
  type        = string
  default     = "my-app"
}

variable "app_image" {
  description = "Docker image for the application"
  type        = string
  default     = "nginx:latest"
}

variable "app_replicas" {
  description = "Number of replicas for the application"
  type        = number
  default     = 2
}

# Create a namespace
resource "kubernetes_namespace" "app_namespace" {
  metadata {
    name = var.namespace
  }
}

# Create a deployment
resource "kubernetes_deployment" "app_deployment" {
  metadata {
    name      = var.app_name
    namespace = kubernetes_namespace.app_namespace.metadata[0].name
    labels = {
      app = var.app_name
    }
  }

  spec {
    replicas = var.app_replicas

    selector {
      match_labels = {
        app = var.app_name
      }
    }

    template {
      metadata {
        labels = {
          app = var.app_name
        }
      }

      spec {
        container {
          image = var.app_image
          name  = var.app_name

          port {
            container_port = 80
          }

          resources {
            limits = {
              cpu    = "0.5"
              memory = "512Mi"
            }
            requests = {
              cpu    = "0.25"
              memory = "256Mi"
            }
          }

          liveness_probe {
            http_get {
              path = "/"
              port = 80
            }
            initial_delay_seconds = 30
            period_seconds        = 10
          }
        }
      }
    }
  }
}

# Create a service
resource "kubernetes_service" "app_service" {
  metadata {
    name      = var.app_name
    namespace = kubernetes_namespace.app_namespace.metadata[0].name
  }

  spec {
    selector = {
      app = kubernetes_deployment.app_deployment.metadata[0].labels.app
    }

    port {
      port        = 80
      target_port = 80
    }

    type = "ClusterIP"
  }
}

# Output the service name
output "service_name" {
  description = "Name of the Kubernetes service"
  value       = kubernetes_service.app_service.metadata[0].name
}

# Output the service namespace
output "service_namespace" {
  description = "Namespace of the Kubernetes service"
  value       = kubernetes_service.app_service.metadata[0].namespace
}
"""
                else:
                    code = """# Terraform configuration template

# Configure provider(s) based on your specific needs
provider "aws" {
  region = var.aws_region
}

# Variables
variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "us-west-2"
}

variable "project_name" {
  description = "Name of the project for resource tagging"
  type        = string
  default     = "my-app"
}

# Example resource
resource "aws_s3_bucket" "example" {
  bucket = "${var.project_name}-bucket"

  tags = {
    Name    = "${var.project_name}-bucket"
    Project = var.project_name
  }
}

# Example output
output "bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.example.bucket
}
"""
            
            elif platform == "ansible":
                if "web-server" in resource_type.lower():
                    code = """---
# playbook.yml - Configure a web server

- name: Configure Web Server
  hosts: web_servers
  become: yes
  vars:
    app_name: my-app
    app_user: app
    app_group: app
    app_directory: /var/www/my-app
    nginx_config_path: /etc/nginx/sites-available
    app_domain: example.com

  tasks:
    - name: Update apt cache
      apt:
        update_cache: yes
        cache_valid_time: 3600
      when: ansible_os_family == 'Debian'

    - name: Install required packages
      package:
        name:
          - nginx
          - certbot
          - python3-certbot-nginx
          - git
          - ufw
        state: present

    - name: Create app user
      user:
        name: "{{ app_user }}"
        group: "{{ app_group }}"
        state: present
        system: yes

    - name: Create app directory
      file:
        path: "{{ app_directory }}"
        state: directory
        owner: "{{ app_user }}"
        group: "{{ app_group }}"
        mode: '0755'

    - name: Configure Nginx
      template:
        src: templates/nginx.conf.j2
        dest: "{{ nginx_config_path }}/{{ app_name }}"
        owner: root
        group: root
        mode: '0644'
      notify: Reload Nginx

    - name: Enable Nginx configuration
      file:
        src: "{{ nginx_config_path }}/{{ app_name }}"
        dest: /etc/nginx/sites-enabled/{{ app_name }}
        state: link
      notify: Reload Nginx

    - name: Configure UFW
      ufw:
        rule: allow
        name: "{{ item }}"
        state: enabled
      with_items:
        - Nginx Full
        - OpenSSH

    - name: Enable UFW
      ufw:
        state: enabled
        policy: deny

    - name: Set up SSL with Certbot
      command: >
        certbot --nginx -d {{ app_domain }} -d www.{{ app_domain }}
        --non-interactive --agree-tos --email webmaster@{{ app_domain }}
      args:
        creates: /etc/letsencrypt/live/{{ app_domain }}/fullchain.pem

  handlers:
    - name: Reload Nginx
      service:
        name: nginx
        state: reloaded

    - name: Restart Nginx
      service:
        name: nginx
        state: restarted

# This playbook requires a template file at templates/nginx.conf.j2 with content like:
#
# server {
#     listen 80;
#     server_name {{ app_domain }} www.{{ app_domain }};
#     root {{ app_directory }};
#     
#     location / {
#         try_files $uri $uri/ /index.html;
#     }
# }
"""
                elif "database" in resource_type.lower():
                    code = """---
# playbook.yml - Configure a database server

- name: Configure Database Server
  hosts: db_servers
  become: yes
  vars:
    db_type: postgresql
    db_version: 14
    db_user: appuser
    db_password: "{{ vault_db_password }}" # This should be stored in an Ansible Vault
    db_name: appdb
    backup_dir: /var/backups/postgresql
    postgresql_config_path: /etc/postgresql/14/main

  tasks:
    - name: Update apt cache
      apt:
        update_cache: yes
        cache_valid_time: 3600
      when: ansible_os_family == 'Debian'

    - name: Install PostgreSQL
      package:
        name:
          - postgresql-{{ db_version }}
          - postgresql-contrib
          - python3-psycopg2
          - ufw
        state: present
      when: db_type == 'postgresql'

    - name: Ensure PostgreSQL is running
      service:
        name: postgresql
        state: started
        enabled: yes
      when: db_type == 'postgresql'

    - name: Configure PostgreSQL to listen on all interfaces
      lineinfile:
        path: "{{ postgresql_config_path }}/postgresql.conf"
        regexp: "^#?listen_addresses\\s*="
        line: "listen_addresses = '*'"
      notify: Restart PostgreSQL
      when: db_type == 'postgresql'

    - name: Configure PostgreSQL client authentication
      template:
        src: templates/pg_hba.conf.j2
        dest: "{{ postgresql_config_path }}/pg_hba.conf"
        owner: postgres
        group: postgres
        mode: '0640'
      notify: Restart PostgreSQL
      when: db_type == 'postgresql'

    - name: Create PostgreSQL user
      become_user: postgres
      postgresql_user:
        name: "{{ db_user }}"
        password: "{{ db_password }}"
        state: present
        role_attr_flags: CREATEDB,LOGIN
      when: db_type == 'postgresql'

    - name: Create PostgreSQL database
      become_user: postgres
      postgresql_db:
        name: "{{ db_name }}"
        owner: "{{ db_user }}"
        encoding: UTF-8
        lc_collate: en_US.UTF-8
        lc_ctype: en_US.UTF-8
        template: template0
        state: present
      when: db_type == 'postgresql'

    - name: Create backup directory
      file:
        path: "{{ backup_dir }}"
        state: directory
        owner: postgres
        group: postgres
        mode: '0750'
      when: db_type == 'postgresql'

    - name: Set up daily backups
      cron:
        name: "Backup PostgreSQL database"
        user: postgres
        hour: "3"
        minute: "0"
        job: "pg_dump {{ db_name }} | gzip > {{ backup_dir }}/{{ db_name }}_$(date +\\%Y\\%m\\%d).sql.gz"
      when: db_type == 'postgresql'

    - name: Configure UFW
      ufw:
        rule: allow
        port: "{{ item }}"
        proto: tcp
        state: enabled
      with_items:
        - 22    # SSH
        - 5432  # PostgreSQL
      when: db_type == 'postgresql'

    - name: Enable UFW
      ufw:
        state: enabled
        policy: deny

  handlers:
    - name: Restart PostgreSQL
      service:
        name: postgresql
        state: restarted
      when: db_type == 'postgresql'

# This playbook requires a template file at templates/pg_hba.conf.j2 with content like:
#
# # TYPE  DATABASE        USER            ADDRESS                 METHOD
# local   all             postgres                                peer
# local   all             all                                     peer
# host    all             all             127.0.0.1/32            md5
# host    all             all             ::1/128                 md5
# host    appdb           appuser         10.0.0.0/8              md5
"""
                else:
                    code = """---
# playbook.yml - Generic Ansible Playbook

- name: Configure Servers
  hosts: all
  become: yes
  vars:
    app_name: my-app

  tasks:
    - name: Update package cache
      package:
        update_cache: yes
      when: ansible_os_family == 'Debian' or ansible_os_family == 'RedHat'

    - name: Install common packages
      package:
        name:
          - vim
          - curl
          - wget
          - htop
          - git
          - ufw
        state: present

    - name: Configure hostname
      hostname:
        name: "{{ inventory_hostname }}"

    - name: Configure timezone
      timezone:
        name: UTC

    - name: Configure UFW
      ufw:
        rule: allow
        port: "{{ item }}"
        proto: tcp
        state: enabled
      with_items:
        - 22    # SSH
      notify: Enable UFW

    - name: Create app directory
      file:
        path: "/opt/{{ app_name }}"
        state: directory
        mode: '0755'

  handlers:
    - name: Enable UFW
      ufw:
        state: enabled
        policy: deny
        logging: on
"""
            else:
                code = f"""# Generic Infrastructure as Code template for {platform}

# This is a placeholder template for {platform}.
# Replace with appropriate syntax and resources for {platform}.

# Example resource definition:
# resource "example_resource" "name" {{
#   property = "value"
# }}

# Example variables:
# - project_name: Name of the project
# - environment: Environment (dev, test, prod)
# - region: Deployment region

# For more specific templates, please specify a more detailed resource type.
"""
                
            result = f"Infrastructure as Code ({platform} for {resource_type}):\n\n"
            result += f"```\n{code}\n```\n\n"
            
            result += "## Usage Instructions\n\n"
            
            if platform == "terraform":
                result += "1. Save the above code to `main.tf`\n"
                result += "2. Initialize the Terraform workspace: `terraform init`\n"
                result += "3. Review the planned changes: `terraform plan`\n"
                result += "4. Apply the configuration: `terraform apply`\n"
                result += "\nAdditional files you might need:\n"
                result += "- `variables.tf` - For variable definitions\n"
                result += "- `outputs.tf` - For output definitions\n"
                result += "- `terraform.tfvars` - For variable values\n"
            
            elif platform == "ansible":
                result += "1. Save the above code to `playbook.yml`\n"
                result += "2. Create an inventory file with your target hosts\n"
                result += "3. Run the playbook: `ansible-playbook -i inventory playbook.yml`\n"
                result += "\nAdditional files you might need:\n"
                result += "- `inventory` - List of target hosts\n"
                result += "- `ansible.cfg` - Ansible configuration\n"
                result += "- `templates/` - Directory for Jinja2 templates\n"
                result += "- `vars/` - Directory for variable files\n"
            
            else:
                result += f"1. Save the configuration file in the appropriate location for {platform}\n"
                result += f"2. Follow the {platform}-specific instructions for deployment\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating infrastructure code: {str(e)}")
            return f"Error generating infrastructure code: {str(e)}"
            
    def _monitor_setup(self, platform, options):
        """
        Setup monitoring configuration.
        
        Args:
            platform: Monitoring platform (prometheus, cloudwatch, etc.)
            options: Additional options
            
        Returns:
            Monitoring configuration
        """
        try:
            with_alarms = "--with-alarms" in options
            with_dashboards = "--with-dashboards" in options
            
            # Try using AI Service for monitoring configuration
            try:
                system_prompt = f"""
                You are a DevOps expert specializing in monitoring and observability.
                Generate monitoring configuration for the {platform} platform.
                
                Include:
                1. Complete configuration files
                2. Clear comments explaining each section
                3. Best practices for alert thresholds
                4. Key metrics to monitor
                5. Dashboard configuration if applicable
                
                {"Include alarm/alert configuration" if with_alarms else ""}
                {"Include dashboard configuration" if with_dashboards else ""}
                
                Format your response with clear file headers and code blocks.
                """
                
                if 'claude' in ai_service.models:
                    logger.debug(f"Using AI Service to generate {platform} monitoring configuration")
                    response = ai_service.models['claude'].messages.create(
                        model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": f"Please generate monitoring configuration for {platform}."}
                        ],
                        temperature=0.1,
                        max_tokens=2500
                    )
                    ai_output = response.content[0].text
                    
                    result = f"Monitoring Configuration ({platform}):\n\n"
                    result += ai_output
                    return result
                    
            except Exception as ai_err:
                logger.warning(f"AI Service monitoring configuration generation failed: {str(ai_err)}. Falling back to templates.")
            
            # Basic monitoring configuration templates as fallback
            result = f"Monitoring Configuration ({platform}):\n\n"
            
            if platform == "prometheus":
                prometheus_config = """# prometheus.yml - Prometheus Server Configuration

global:
  scrape_interval: 15s  # Set the scrape interval to every 15 seconds
  evaluation_interval: 15s  # Evaluate rules every 15 seconds

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

# Load rules once and periodically evaluate them
rule_files:
  - "alert_rules.yml"

# A scrape configuration containing endpoints to scrape
scrape_configs:
  # The job name is added as a label `job=<job_name>` to any timeseries scraped from this config
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  # Example job for Node Exporter
  - job_name: "node"
    static_configs:
      - targets: ["node-exporter:9100"]

  # Example job for Cadvisor
  - job_name: "cadvisor"
    static_configs:
      - targets: ["cadvisor:8080"]

  # Example job for application metrics
  - job_name: "app"
    metrics_path: /metrics
    static_configs:
      - targets: ["app:8000"]
"""
                
                alert_rules = """# alert_rules.yml - Prometheus Alert Rules

groups:
  - name: example
    rules:
      - alert: HighCPULoad
        expr: 100 - (avg by(instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU load (instance {{ $labels.instance }})"
          description: "CPU load is > 80%\\n  VALUE = {{ $value }}\\n  LABELS: {{ $labels }}"

      - alert: HighMemoryLoad
        expr: (node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory load (instance {{ $labels.instance }})"
          description: "Memory load is > 80%\\n  VALUE = {{ $value }}\\n  LABELS: {{ $labels }}"

      - alert: HighDiskUsage
        expr: (node_filesystem_size_bytes - node_filesystem_free_bytes) / node_filesystem_size_bytes * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High disk usage (instance {{ $labels.instance }})"
          description: "Disk usage is > 85%\\n  VALUE = {{ $value }}\\n  LABELS: {{ $labels }}"

      - alert: InstanceDown
        expr: up == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Instance down (instance {{ $labels.instance }})"
          description: "Instance has been down for more than 5 minutes"
"""
                
                docker_compose = """version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alert_rules.yml:/etc/prometheus/alert_rules.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    ports:
      - "9090:9090"
    restart: unless-stopped
    networks:
      - monitoring

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
      - alertmanager_data:/alertmanager
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    ports:
      - "9093:9093"
    restart: unless-stopped
    networks:
      - monitoring

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.ignored-mount-points=^/(sys|proc|dev|host|etc)($$|/)'
    ports:
      - "9100:9100"
    restart: unless-stopped
    networks:
      - monitoring

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:latest
    container_name: cadvisor
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    ports:
      - "8080:8080"
    restart: unless-stopped
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3000:3000"
    restart: unless-stopped
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge

volumes:
  prometheus_data:
  alertmanager_data:
  grafana_data:
"""
                
                alertmanager_config = """# alertmanager.yml - Alertmanager Configuration

global:
  resolve_timeout: 5m
  # smtp_from: 'alertmanager@example.org'
  # smtp_smarthost: 'smtp.example.org:587'
  # smtp_auth_username: 'alertmanager'
  # smtp_auth_password: 'password'

route:
  group_by: ['alertname', 'job']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'slack'

receivers:
- name: 'slack'
  slack_configs:
  - api_url: 'https://hooks.slack.com/services/T00000000/B00000000/XXXXXXXXXX'
    channel: '#monitoring'
    send_resolved: true
    icon_emoji: ':robot:'
    title: "{{ .GroupLabels.alertname }}"
    text: "{{ range .Alerts }}{{ .Annotations.description }}\n{{ end }}"

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'dev', 'instance']
"""
                
                result += "## prometheus.yml\n\n```yaml\n" + prometheus_config + "\n```\n\n"
                
                if with_alarms:
                    result += "## alert_rules.yml\n\n```yaml\n" + alert_rules + "\n```\n\n"
                    result += "## alertmanager.yml\n\n```yaml\n" + alertmanager_config + "\n```\n\n"
                
                result += "## docker-compose.yml\n\n```yaml\n" + docker_compose + "\n```\n\n"
                
                if with_dashboards:
                    result += "## Grafana Dashboard Example\n\n"
                    result += "Grafana dashboards are typically defined as JSON files, which can be quite lengthy. Here's how to set up a basic dashboard:\n\n"
                    result += "1. Access Grafana at http://localhost:3000 (default credentials: admin/admin)\n"
                    result += "2. Go to 'Create' > 'Dashboard'\n"
                    result += "3. Add panels for key metrics:\n"
                    result += "   - CPU Usage: `100 - (avg by(instance) (irate(node_cpu_seconds_total{mode='idle'}[5m])) * 100)`\n"
                    result += "   - Memory Usage: `(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100`\n"
                    result += "   - Disk Usage: `(node_filesystem_size_bytes{mountpoint='/'} - node_filesystem_free_bytes{mountpoint='/'}) / node_filesystem_size_bytes{mountpoint='/'} * 100`\n"
                    result += "   - Network Traffic: `rate(node_network_receive_bytes_total[5m])` and `rate(node_network_transmit_bytes_total[5m])`\n"
                    result += "4. Save the dashboard and export it as JSON for version control\n"
                
            elif platform == "cloudwatch":
                cloudformation_template = """AWSTemplateFormatVersion: '2010-09-09'
Description: 'CloudWatch Monitoring Setup'

Resources:
  # CPU Utilization Alarm
  HighCPUAlarm:
    Type: 'AWS::CloudWatch::Alarm'
    Properties:
      AlarmName: HighCPUUtilization
      AlarmDescription: 'Alarm if CPU exceeds 70% for 5 minutes'
      MetricName: CPUUtilization
      Namespace: AWS/EC2
      Statistic: Average
      Period: 300
      EvaluationPeriods: 1
      Threshold: 70
      ComparisonOperator: GreaterThanThreshold
      Dimensions:
        - Name: InstanceId
          Value: !Ref InstanceId
      # Uncomment to add SNS notification
      # AlarmActions:
      #   - !Ref AlarmNotificationTopic

  # Memory Utilization Alarm (requires CloudWatch agent)
  HighMemoryAlarm:
    Type: 'AWS::CloudWatch::Alarm'
    Properties:
      AlarmName: HighMemoryUtilization
      AlarmDescription: 'Alarm if memory usage exceeds 80% for 5 minutes'
      MetricName: mem_used_percent
      Namespace: CWAgent
      Statistic: Average
      Period: 300
      EvaluationPeriods: 1
      Threshold: 80
      ComparisonOperator: GreaterThanThreshold
      Dimensions:
        - Name: InstanceId
          Value: !Ref InstanceId
      # Uncomment to add SNS notification
      # AlarmActions:
      #   - !Ref AlarmNotificationTopic

  # Disk Utilization Alarm (requires CloudWatch agent)
  HighDiskUsageAlarm:
    Type: 'AWS::CloudWatch::Alarm'
    Properties:
      AlarmName: HighDiskUtilization
      AlarmDescription: 'Alarm if disk usage exceeds 85% for 5 minutes'
      MetricName: disk_used_percent
      Namespace: CWAgent
      Statistic: Average
      Period: 300
      EvaluationPeriods: 1
      Threshold: 85
      ComparisonOperator: GreaterThanThreshold
      Dimensions:
        - Name: path
          Value: /
        - Name: InstanceId
          Value: !Ref InstanceId
      # Uncomment to add SNS notification
      # AlarmActions:
      #   - !Ref AlarmNotificationTopic

  # Optional: SNS Topic for alarm notifications
  # AlarmNotificationTopic:
  #   Type: 'AWS::SNS::Topic'
  #   Properties:
  #     DisplayName: 'CloudWatch Alarm Notifications'
  #     Subscription:
  #       - Endpoint: 'email@example.com'
  #         Protocol: 'email'

Parameters:
  InstanceId:
    Type: String
    Description: 'ID of the EC2 instance to monitor'

Outputs:
  CPUAlarmName:
    Description: 'Name of the CPU utilization alarm'
    Value: !Ref HighCPUAlarm

  MemoryAlarmName:
    Description: 'Name of the memory utilization alarm'
    Value: !Ref HighMemoryAlarm

  DiskAlarmName:
    Description: 'Name of the disk utilization alarm'
    Value: !Ref HighDiskUsageAlarm
"""
                
                cloudwatch_agent_config = """{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "cwagent"
  },
  "metrics": {
    "namespace": "CWAgent",
    "append_dimensions": {
      "InstanceId": "${aws:InstanceId}"
    },
    "metrics_collected": {
      "cpu": {
        "resources": [
          "*"
        ],
        "measurement": [
          "usage_idle",
          "usage_iowait",
          "usage_user",
          "usage_system"
        ],
        "totalcpu": true
      },
      "mem": {
        "measurement": [
          "used",
          "available",
          "total",
          "used_percent",
          "available_percent"
        ]
      },
      "disk": {
        "resources": [
          "/"
        ],
        "measurement": [
          "used",
          "available",
          "total",
          "used_percent",
          "available_percent"
        ]
      },
      "diskio": {
        "resources": [
          "*"
        ],
        "measurement": [
          "reads",
          "writes",
          "read_bytes",
          "write_bytes",
          "read_time",
          "write_time"
        ]
      },
      "swap": {
        "measurement": [
          "used",
          "free",
          "used_percent"
        ]
      },
      "netstat": {
        "measurement": [
          "tcp_established",
          "tcp_time_wait"
        ]
      },
      "processes": {
        "measurement": [
          "running",
          "sleeping",
          "dead"
        ]
      }
    }
  },
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/syslog",
            "log_group_name": "/var/log/syslog",
            "log_stream_name": "{instance_id}"
          },
          {
            "file_path": "/var/log/auth.log",
            "log_group_name": "/var/log/auth.log",
            "log_stream_name": "{instance_id}"
          },
          {
            "file_path": "/var/log/application.log",
            "log_group_name": "/var/log/application.log",
            "log_stream_name": "{instance_id}"
          }
        ]
      }
    }
  }
}
"""
                
                result += "## CloudFormation Template (cloudwatch-alarms.yml)\n\n```yaml\n" + cloudformation_template + "\n```\n\n"
                result += "## CloudWatch Agent Configuration (amazon-cloudwatch-agent.json)\n\n```json\n" + cloudwatch_agent_config + "\n```\n\n"
                
                if with_dashboards:
                    result += "## CloudWatch Dashboard (cloudwatch-dashboard.json)\n\n"
                    result += "CloudWatch dashboards can be defined using JSON. Here's a basic example that you'd typically create through the AWS console or API:\n\n"
                    result += "```json\n"
                    result += """{
  "widgets": [
    {
      "type": "metric",
      "x": 0,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "AWS/EC2", "CPUUtilization", "InstanceId", "${InstanceId}" ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "${AWS::Region}",
        "title": "CPU Utilization",
        "period": 300,
        "stat": "Average"
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 0,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "CWAgent", "mem_used_percent", "InstanceId", "${InstanceId}" ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "${AWS::Region}",
        "title": "Memory Utilization",
        "period": 300,
        "stat": "Average"
      }
    },
    {
      "type": "metric",
      "x": 0,
      "y": 6,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "CWAgent", "disk_used_percent", "path", "/", "InstanceId", "${InstanceId}" ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "${AWS::Region}",
        "title": "Disk Utilization",
        "period": 300,
        "stat": "Average"
      }
    },
    {
      "type": "metric",
      "x": 12,
      "y": 6,
      "width": 12,
      "height": 6,
      "properties": {
        "metrics": [
          [ "CWAgent", "netstat_tcp_established", "InstanceId", "${InstanceId}" ],
          [ "CWAgent", "netstat_tcp_time_wait", "InstanceId", "${InstanceId}" ]
        ],
        "view": "timeSeries",
        "stacked": false,
        "region": "${AWS::Region}",
        "title": "Network Connections",
        "period": 300,
        "stat": "Average"
      }
    }
  ]
}
"""
                    result += "\n```\n\n"
                
                result += "## Installation and Setup\n\n"
                result += "1. **Install CloudWatch Agent**:\n"
                result += "   - On Amazon Linux: `sudo yum install amazon-cloudwatch-agent`\n"
                result += "   - On Ubuntu: `wget https://s3.amazonaws.com/amazoncloudwatch-agent/ubuntu/amd64/latest/amazon-cloudwatch-agent.deb && sudo dpkg -i amazon-cloudwatch-agent.deb`\n\n"
                result += "2. **Configure CloudWatch Agent**:\n"
                result += "   - Save the agent configuration to `/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json`\n"
                result += "   - Start the agent: `sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl -a fetch-config -m ec2 -s -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json`\n\n"
                result += "3. **Deploy CloudFormation Template**:\n"
                result += "   - Save the template to `cloudwatch-alarms.yml`\n"
                result += "   - Deploy: `aws cloudformation create-stack --stack-name monitoring-alarms --template-body file://cloudwatch-alarms.yml --parameters ParameterKey=InstanceId,ParameterValue=i-1234567890abcdef0`\n"
                
            elif platform == "grafana":
                grafana_config = """[paths]
data = /var/lib/grafana
logs = /var/log/grafana
plugins = /var/lib/grafana/plugins
provisioning = /etc/grafana/provisioning

[server]
protocol = http
http_port = 3000
domain = localhost
root_url = %(protocol)s://%(domain)s:%(http_port)s/
router_logging = false

[security]
# Change this for production use
admin_user = admin
admin_password = admin
secret_key = SW2YcwTIb9zpOOhoPsMm

[dashboards]
versions_to_keep = 20

[users]
allow_sign_up = false
auto_assign_org = true
auto_assign_org_role = Viewer

[auth.anonymous]
enabled = false

[analytics]
reporting_enabled = false
check_for_updates = true

[smtp]
enabled = false
# Configure for email alerts
# host = smtp.example.com:587
# user = grafana@example.com
# password = password
# from_address = grafana@example.com
"""
                
                prometheus_datasource = """apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
"""
                
                dashboard_config = """apiVersion: 1

providers:
  - name: 'Default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    editable: true
    options:
      path: /etc/grafana/provisioning/dashboards
"""
                
                docker_compose = """version: '3.8'

services:
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    volumes:
      - ./grafana.ini:/etc/grafana/grafana.ini
      - ./provisioning:/etc/grafana/provisioning
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3000:3000"
    restart: unless-stopped
    networks:
      - monitoring

  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    ports:
      - "9090:9090"
    restart: unless-stopped
    networks:
      - monitoring

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.ignored-mount-points=^/(sys|proc|dev|host|etc)($$|/)'
    ports:
      - "9100:9100"
    restart: unless-stopped
    networks:
      - monitoring

  loki:
    image: grafana/loki:latest
    container_name: loki
    ports:
      - "3100:3100"
    volumes:
      - loki_data:/loki
    command: -config.file=/etc/loki/local-config.yaml
    restart: unless-stopped
    networks:
      - monitoring

  promtail:
    image: grafana/promtail:latest
    container_name: promtail
    volumes:
      - /var/log:/var/log
      - ./promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml
    restart: unless-stopped
    networks:
      - monitoring

networks:
  monitoring:
    driver: bridge

volumes:
  grafana_data:
  prometheus_data:
  loki_data:
"""
                
                result += "## grafana.ini\n\n```ini\n" + grafana_config + "\n```\n\n"
                result += "## provisioning/datasources/prometheus.yml\n\n```yaml\n" + prometheus_datasource + "\n```\n\n"
                result += "## provisioning/dashboards/dashboard.yml\n\n```yaml\n" + dashboard_config + "\n```\n\n"
                result += "## docker-compose.yml\n\n```yaml\n" + docker_compose + "\n```\n\n"
                
                if with_dashboards:
                    result += "## Sample Dashboard JSON\n\n"
                    result += "Grafana dashboards are defined as JSON files. Here's a minimal example for a system monitoring dashboard:\n\n"
                    result += "```json\n"
                    result += """{
  "annotations": {
    "list": [
      {
        "builtIn": 1,
        "datasource": "-- Grafana --",
        "enable": true,
        "hide": true,
        "iconColor": "rgba(0, 211, 255, 1)",
        "name": "Annotations & Alerts",
        "type": "dashboard"
      }
    ]
  },
  "editable": true,
  "gnetId": null,
  "graphTooltip": 0,
  "id": 1,
  "links": [],
  "panels": [
    {
      "aliasColors": {},
      "bars": false,
      "dashLength": 10,
      "dashes": false,
      "datasource": "Prometheus",
      "fill": 1,
      "fillGradient": 0,
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 0,
        "y": 0
      },
      "hiddenSeries": false,
      "id": 2,
      "legend": {
        "avg": false,
        "current": false,
        "max": false,
        "min": false,
        "show": true,
        "total": false,
        "values": false
      },
      "lines": true,
      "linewidth": 1,
      "nullPointMode": "null",
      "options": {
        "dataLinks": []
      },
      "percentage": false,
      "pointradius": 2,
      "points": false,
      "renderer": "flot",
      "seriesOverrides": [],
      "spaceLength": 10,
      "stack": false,
      "steppedLine": false,
      "targets": [
        {
          "expr": "100 - (avg by(instance) (irate(node_cpu_seconds_total{mode=\\"idle\\"}[5m])) * 100)",
          "legendFormat": "CPU Usage",
          "refId": "A"
        }
      ],
      "thresholds": [],
      "timeFrom": null,
      "timeRegions": [],
      "timeShift": null,
      "title": "CPU Usage",
      "tooltip": {
        "shared": true,
        "sort": 0,
        "value_type": "individual"
      },
      "type": "graph",
      "xaxis": {
        "buckets": null,
        "mode": "time",
        "name": null,
        "show": true,
        "values": []
      },
      "yaxes": [
        {
          "format": "percent",
          "label": null,
          "logBase": 1,
          "max": "100",
          "min": "0",
          "show": true
        },
        {
          "format": "short",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        }
      ],
      "yaxis": {
        "align": false,
        "alignLevel": null
      }
    },
    {
      "aliasColors": {},
      "bars": false,
      "dashLength": 10,
      "dashes": false,
      "datasource": "Prometheus",
      "fill": 1,
      "fillGradient": 0,
      "gridPos": {
        "h": 8,
        "w": 12,
        "x": 12,
        "y": 0
      },
      "hiddenSeries": false,
      "id": 3,
      "legend": {
        "avg": false,
        "current": false,
        "max": false,
        "min": false,
        "show": true,
        "total": false,
        "values": false
      },
      "lines": true,
      "linewidth": 1,
      "nullPointMode": "null",
      "options": {
        "dataLinks": []
      },
      "percentage": false,
      "pointradius": 2,
      "points": false,
      "renderer": "flot",
      "seriesOverrides": [],
      "spaceLength": 10,
      "stack": false,
      "steppedLine": false,
      "targets": [
        {
          "expr": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100",
          "legendFormat": "Memory Usage",
          "refId": "A"
        }
      ],
      "thresholds": [],
      "timeFrom": null,
      "timeRegions": [],
      "timeShift": null,
      "title": "Memory Usage",
      "tooltip": {
        "shared": true,
        "sort": 0,
        "value_type": "individual"
      },
      "type": "graph",
      "xaxis": {
        "buckets": null,
        "mode": "time",
        "name": null,
        "show": true,
        "values": []
      },
      "yaxes": [
        {
          "format": "percent",
          "label": null,
          "logBase": 1,
          "max": "100",
          "min": "0",
          "show": true
        },
        {
          "format": "short",
          "label": null,
          "logBase": 1,
          "max": null,
          "min": null,
          "show": true
        }
      ],
      "yaxis": {
        "align": false,
        "alignLevel": null
      }
    }
  ],
  "refresh": "5s",
  "schemaVersion": 22,
  "style": "dark",
  "tags": [],
  "templating": {
    "list": []
  },
  "time": {
    "from": "now-6h",
    "to": "now"
  },
  "timepicker": {
    "refresh_intervals": [
      "5s",
      "10s",
      "30s",
      "1m",
      "5m",
      "15m",
      "30m",
      "1h",
      "2h",
      "1d"
    ]
  },
  "timezone": "",
  "title": "System Monitoring",
  "uid": "system-monitoring",
  "version": 1
}
"""
                    result += "\n```\n\n"
                
                result += "## Setup Instructions\n\n"
                result += "1. Create the following directory structure:\n"
                result += "```\n"
                result += "monitoring/\n"
                result += "├── docker-compose.yml\n"
                result += "├── grafana.ini\n"
                result += "├── prometheus/\n"
                result += "│   └── prometheus.yml\n"
                result += "├── provisioning/\n"
                result += "│   ├── dashboards/\n"
                result += "│   │   ├── dashboard.yml\n"
                result += "│   │   └── system-monitoring.json\n"
                result += "│   └── datasources/\n"
                result += "│       └── prometheus.yml\n"
                result += "└── promtail-config.yml\n"
                result += "```\n\n"
                result += "2. Create a `prometheus.yml` file with your scrape configuration\n"
                result += "3. Create a `promtail-config.yml` file for log collection\n"
                result += "4. Start the stack: `docker-compose up -d`\n"
                result += "5. Access Grafana at http://localhost:3000 (default credentials: admin/admin)\n"
                
            else:
                # Generic monitoring configuration
                result += f"## Basic monitoring setup for {platform}\n\n"
                result += "This is a generic template that you should customize based on your specific monitoring requirements.\n\n"
                result += "Key components to consider for your monitoring system:\n\n"
                result += "1. **Metrics Collection**\n"
                result += "   - System metrics (CPU, memory, disk, network)\n"
                result += "   - Application metrics\n"
                result += "   - Database metrics\n\n"
                result += "2. **Alerting**\n"
                result += "   - Thresholds for critical metrics\n"
                result += "   - Alert delivery channels (email, Slack, PagerDuty, etc.)\n"
                result += "   - Escalation policies\n\n"
                result += "3. **Dashboards**\n"
                result += "   - System overview\n"
                result += "   - Application performance\n"
                result += "   - Business metrics\n\n"
                result += "4. **Log Management**\n"
                result += "   - Log collection\n"
                result += "   - Log parsing and indexing\n"
                result += "   - Log querying and visualization\n\n"
                result += f"For specific {platform} configuration, please provide more details about your monitoring requirements."
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating monitoring configuration: {str(e)}")
            return f"Error generating monitoring configuration: {str(e)}"
            
    def _deployment(self, platform, app_type):
        """
        Generate deployment scripts or configurations.
        
        Args:
            platform: Deployment platform (kubernetes, heroku, etc.)
            app_type: Type of application (python-app, nodejs-app, etc.)
            
        Returns:
            Deployment scripts or configurations
        """
        try:
            # Try using AI Service for deployment configuration
            try:
                system_prompt = f"""
                You are a DevOps expert specializing in application deployment.
                Generate deployment configuration for {app_type} on {platform}.
                
                Include:
                1. Complete configuration files
                2. Clear comments explaining each section
                3. Best practices for secure deployment
                4. Environment variable handling
                5. Scaling configuration
                
                Format your response with clear file headers and code blocks.
                """
                
                if 'claude' in ai_service.models:
                    logger.debug(f"Using AI Service to generate {platform} deployment configuration for {app_type}")
                    response = ai_service.models['claude'].messages.create(
                        model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": f"Please generate deployment configuration for {app_type} on {platform}."}
                        ],
                        temperature=0.1,
                        max_tokens=2500
                    )
                    ai_output = response.content[0].text
                    
                    result = f"Deployment Configuration ({platform} for {app_type}):\n\n"
                    result += ai_output
                    return result
                    
            except Exception as ai_err:
                logger.warning(f"AI Service deployment configuration generation failed: {str(ai_err)}. Falling back to templates.")
            
            # Basic deployment configuration templates as fallback
            result = f"Deployment Configuration ({platform} for {app_type}):\n\n"
            
            if platform == "kubernetes":
                if "python" in app_type.lower() or "flask" in app_type.lower():
                    deployment_yaml = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: python-app
  labels:
    app: python-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: python-app
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  template:
    metadata:
      labels:
        app: python-app
    spec:
      containers:
      - name: python-app
        image: ${DOCKER_REGISTRY}/python-app:${APP_VERSION}
        ports:
        - containerPort: 5000
        resources:
          limits:
            cpu: "500m"
            memory: "512Mi"
          requests:
            cpu: "200m"
            memory: "256Mi"
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        - name: FLASK_ENV
          value: "production"
        - name: PORT
          value: "5000"
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 15
          periodSeconds: 20
      imagePullSecrets:
      - name: registry-credentials
---
apiVersion: v1
kind: Service
metadata:
  name: python-app
spec:
  selector:
    app: python-app
  ports:
  - port: 80
    targetPort: 5000
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: python-app-ingress
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - app.example.com
    secretName: python-app-tls
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: python-app
            port:
              number: 80
---
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  # Base64 encoded secrets
  database-url: cG9zdGdyZXNxbDovL3VzZXJuYW1lOnBhc3N3b3JkQGhvc3Q6NTQzMi9kYg==  # Replace with your encoded secret
"""
                
                elif "node" in app_type.lower() or "express" in app_type.lower():
                    deployment_yaml = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: nodejs-app
  labels:
    app: nodejs-app
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nodejs-app
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  template:
    metadata:
      labels:
        app: nodejs-app
    spec:
      containers:
      - name: nodejs-app
        image: ${DOCKER_REGISTRY}/nodejs-app:${APP_VERSION}
        ports:
        - containerPort: 3000
        resources:
          limits:
            cpu: "500m"
            memory: "512Mi"
          requests:
            cpu: "200m"
            memory: "256Mi"
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        - name: NODE_ENV
          value: "production"
        - name: PORT
          value: "3000"
        readinessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 3000
          initialDelaySeconds: 15
          periodSeconds: 20
      imagePullSecrets:
      - name: registry-credentials
---
apiVersion: v1
kind: Service
metadata:
  name: nodejs-app
spec:
  selector:
    app: nodejs-app
  ports:
  - port: 80
    targetPort: 3000
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nodejs-app-ingress
  annotations:
    kubernetes.io/ingress.class: "nginx"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
spec:
  tls:
  - hosts:
    - app.example.com
    secretName: nodejs-app-tls
  rules:
  - host: app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: nodejs-app
            port:
              number: 80
---
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
type: Opaque
data:
  # Base64 encoded secrets
  database-url: bW9uZ29kYjovL3VzZXJuYW1lOnBhc3N3b3JkQGhvc3Q6MjcwMTcvZGI=  # Replace with your encoded secret
"""
                
                else:
                    deployment_yaml = f"""apiVersion: apps/v1
kind: Deployment
metadata:
  name: {app_type}
  labels:
    app: {app_type}
spec:
  replicas: 2
  selector:
    matchLabels:
      app: {app_type}
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 1
  template:
    metadata:
      labels:
        app: {app_type}
    spec:
      containers:
      - name: {app_type}
        image: ${{DOCKER_REGISTRY}}/{app_type}:${{APP_VERSION}}
        ports:
        - containerPort: 8080
        resources:
          limits:
            cpu: "500m"
            memory: "512Mi"
          requests:
            cpu: "200m"
            memory: "256Mi"
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: app-secrets
              key: database-url
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
      imagePullSecrets:
      - name: registry-credentials
---
apiVersion: v1
kind: Service
metadata:
  name: {app_type}
spec:
  selector:
    app: {app_type}
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
"""
                
                # Kubernetes deployment files
                result += "## kubernetes/deployment.yaml\n\n```yaml\n" + deployment_yaml + "\n```\n\n"
                
                # Deployment script
                deploy_script = """#!/bin/bash
# deploy.sh - Deploy to Kubernetes

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null; then
    echo "kubectl is not installed. Please install it first."
    exit 1
fi

# Set variables
APP_VERSION=${1:-latest}
DOCKER_REGISTRY=${DOCKER_REGISTRY:-"example.registry.com"}
NAMESPACE=${NAMESPACE:-"default"}

# Replace variables in YAML files
envsubst < kubernetes/deployment.yaml > kubernetes/deployment-processed.yaml

# Apply configurations
echo "Deploying application version $APP_VERSION to namespace $NAMESPACE..."
kubectl apply -f kubernetes/deployment-processed.yaml -n $NAMESPACE

# Check deployment status
echo "Checking deployment status..."
kubectl rollout status deployment/python-app -n $NAMESPACE

echo "Deployment complete!"
"""
                
                result += "## deploy.sh\n\n```bash\n" + deploy_script + "\n```\n\n"
                
                # Usage instructions
                result += "## Usage Instructions\n\n"
                result += "1. Create the Kubernetes YAML files in a `kubernetes/` directory\n"
                result += "2. Create the deployment script and make it executable: `chmod +x deploy.sh`\n"
                result += "3. Set up your environment variables (or use a .env file):\n"
                result += "   ```bash\n"
                result += "   export DOCKER_REGISTRY=your-registry.com\n"
                result += "   export NAMESPACE=your-namespace\n"
                result += "   ```\n"
                result += "4. Run the deployment script: `./deploy.sh 1.0.0`\n\n"
                result += "For initial setup, you may also need to create the namespace and secrets:\n"
                result += "```bash\n"
                result += "kubectl create namespace your-namespace\n"
                result += "kubectl create secret docker-registry registry-credentials \\\n"
                result += "    --docker-server=your-registry.com \\\n"
                result += "    --docker-username=username \\\n"
                result += "    --docker-password=password \\\n"
                result += "    --docker-email=email@example.com \\\n"
                result += "    -n your-namespace\n"
                result += "```\n"
                
            elif platform == "heroku":
                if "python" in app_type.lower() or "flask" in app_type.lower():
                    procfile = """web: gunicorn --bind 0.0.0.0:$PORT main:app
"""
                    
                    runtime = """python-3.11.7
"""
                    
                    app_json = """{
  "name": "python-app",
  "description": "A Python web application",
  "repository": "https://github.com/username/python-app",
  "keywords": ["python", "flask"],
  "env": {
    "SECRET_KEY": {
      "description": "A secret key for encryption",
      "generator": "secret"
    },
    "DATABASE_URL": {
      "description": "URL for the PostgreSQL database",
      "value": ""
    }
  },
  "addons": [
    "heroku-postgresql:hobby-dev"
  ],
  "buildpacks": [
    {
      "url": "heroku/python"
    }
  ],
  "formation": {
    "web": {
      "quantity": 1,
      "size": "eco"
    }
  }
}
"""
                
                elif "node" in app_type.lower() or "express" in app_type.lower():
                    procfile = """web: node app.js
"""
                    
                    app_json = """{
  "name": "nodejs-app",
  "description": "A Node.js web application",
  "repository": "https://github.com/username/nodejs-app",
  "keywords": ["node", "express"],
  "env": {
    "NODE_ENV": {
      "description": "Environment for Node.js application",
      "value": "production"
    },
    "DATABASE_URL": {
      "description": "URL for the PostgreSQL database",
      "value": ""
    }
  },
  "addons": [
    "heroku-postgresql:hobby-dev"
  ],
  "buildpacks": [
    {
      "url": "heroku/nodejs"
    }
  ],
  "formation": {
    "web": {
      "quantity": 1,
      "size": "eco"
    }
  }
}
"""
                
                else:
                    procfile = f"""web: ./start_command $PORT
"""
                    
                    app_json = f"""{{
  "name": "{app_type}",
  "description": "A web application",
  "repository": "https://github.com/username/{app_type}",
  "env": {{
    "SECRET_KEY": {{
      "description": "A secret key for encryption",
      "generator": "secret"
    }}
  }},
  "formation": {{
    "web": {{
      "quantity": 1,
      "size": "eco"
    }}
  }}
}}
"""
                
                # Heroku deployment files
                result += "## Procfile\n\n```\n" + procfile + "\n```\n\n"
                
                if "python" in app_type.lower():
                    result += "## runtime.txt\n\n```\n" + runtime + "\n```\n\n"
                
                result += "## app.json\n\n```json\n" + app_json + "\n```\n\n"
                
                # Deployment script
                deploy_script = """#!/bin/bash
# deploy.sh - Deploy to Heroku

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "Heroku CLI is not installed. Please install it first."
    exit 1
fi

# Set variables
APP_NAME=${1:-"my-app"}
BRANCH=${2:-"main"}

# Login to Heroku (if not already logged in)
heroku auth:whoami &> /dev/null || heroku login

# Check if app exists, create if it doesn't
if ! heroku apps:info --app $APP_NAME &> /dev/null; then
    echo "Creating Heroku app $APP_NAME..."
    heroku apps:create $APP_NAME
else
    echo "Using existing Heroku app $APP_NAME..."
fi

# Set up remote if it doesn't exist
if ! git remote | grep heroku &> /dev/null; then
    git remote add heroku git@heroku.com:$APP_NAME.git
fi

# Push to Heroku
echo "Deploying application to Heroku..."
git push heroku $BRANCH:main

# Run database migrations (if needed)
# heroku run python manage.py db upgrade --app $APP_NAME

echo "Deployment complete! Your app is available at: https://$APP_NAME.herokuapp.com"
"""
                
                result += "## deploy.sh\n\n```bash\n" + deploy_script + "\n```\n\n"
                
                # Usage instructions
                result += "## Usage Instructions\n\n"
                result += "1. Create the Heroku configuration files in your project root directory\n"
                result += "2. Create the deployment script and make it executable: `chmod +x deploy.sh`\n"
                result += "3. Ensure your application code is committed to Git\n"
                result += "4. Run the deployment script: `./deploy.sh your-app-name main`\n\n"
                result += "You can also deploy directly using Git:\n"
                result += "```bash\n"
                result += "heroku create your-app-name\n"
                result += "git push heroku main\n"
                result += "```\n\n"
                result += "To set environment variables:\n"
                result += "```bash\n"
                result += "heroku config:set KEY=VALUE\n"
                result += "```\n"
                
            else:
                # Generic deployment configuration
                result += f"## Generic deployment configuration for {app_type} on {platform}\n\n"
                result += "This is a basic template that you should customize based on your specific deployment requirements.\n\n"
                
                result += "### Key components for deployment:\n\n"
                result += "1. **Application Packaging**\n"
                result += "   - Build artifacts (compiled code, static assets)\n"
                result += "   - Dependencies\n"
                result += "   - Configuration files\n\n"
                result += "2. **Environment Configuration**\n"
                result += "   - Environment variables\n"
                result += "   - Secrets management\n"
                result += "   - Service connections\n\n"
                result += "3. **Deployment Process**\n"
                result += "   - Build steps\n"
                result += "   - Deployment steps\n"
                result += "   - Health checks\n"
                result += "   - Rollback procedures\n\n"
                result += "4. **Scaling Configuration**\n"
                result += "   - Horizontal scaling\n"
                result += "   - Vertical scaling\n"
                result += "   - Auto-scaling rules\n\n"
                
                result += f"For specific {platform} deployment configuration, please provide more details about your deployment requirements."
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating deployment configuration: {str(e)}")
            return f"Error generating deployment configuration: {str(e)}"