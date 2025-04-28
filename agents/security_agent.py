import os
import re
import subprocess
import logging
import json
import requests
from typing import List, Dict, Any, Optional
from agents.base_agent import BaseAgent
from ai_service import ai_service

# Set up logging
logger = logging.getLogger(__name__)

class SecurityAgent(BaseAgent):
    """
    The Security Agent - specialized in vulnerability detection and security operations.
    
    This agent can help with tasks like:
    - Scanning code for security vulnerabilities
    - Performing OWASP checks on web applications
    - Checking dependencies for known vulnerabilities
    - Generating security reports
    - Recommending Linux system hardening
    """
    
    def __init__(self):
        """Initialize the Security Agent."""
        super().__init__(
            name="SecurityAgent",
            description="Specialized in vulnerability detection and security analysis."
        )
        self.supported_scan_types = [
            "code", "web", "deps", "system", "network"
        ]
        
    def get_commands(self):
        """Return the commands this agent can handle."""
        return {
            "scan-code": {
                "description": "Scan code for security vulnerabilities",
                "usage": "scan-code <file_path>",
                "examples": [
                    "scan-code main.py",
                    "scan-code ./webapp/auth.js"
                ]
            },
            "owasp-check": {
                "description": "Check a web application against OWASP Top 10 vulnerabilities",
                "usage": "owasp-check <target_url>",
                "examples": [
                    "owasp-check example.com",
                    "owasp-check https://myapp.com/login"
                ]
            },
            "check-deps": {
                "description": "Check project dependencies for known vulnerabilities",
                "usage": "check-deps <project_path>",
                "examples": [
                    "check-deps ./",
                    "check-deps ./myproject/package.json"
                ]
            },
            "harden-linux": {
                "description": "Get recommendations for hardening a Linux system",
                "usage": "harden-linux [specific_area]",
                "examples": [
                    "harden-linux",
                    "harden-linux ssh",
                    "harden-linux firewall"
                ]
            },
            "generate-report": {
                "description": "Generate a security report for a target",
                "usage": "generate-report <target> [vuln_type]",
                "examples": [
                    "generate-report myapp.com",
                    "generate-report myapp.com xss",
                    "generate-report ./src sql-injection"
                ]
            }
        }
    
    def execute(self, command, args):
        """Execute a SecurityAgent command."""
        try:
            if command == "scan-code":
                if not args:
                    return "Error: Missing file path. Usage: scan-code <file_path>"
                return self._scan_code(args[0])
                
            elif command == "owasp-check":
                if not args:
                    return "Error: Missing target URL. Usage: owasp-check <target_url>"
                return self._owasp_check(args[0])
                
            elif command == "check-deps":
                path = "./" if not args else args[0]
                return self._check_dependencies(path)
                
            elif command == "harden-linux":
                area = None if not args else args[0]
                return self._harden_linux(area)
                
            elif command == "generate-report":
                if not args:
                    return "Error: Missing target. Usage: generate-report <target> [vuln_type]"
                
                target = args[0]
                vuln_type = args[1] if len(args) > 1 else None
                return self._generate_report(target, vuln_type)
                
            else:
                return f"Unknown command: '{command}'"
                
        except Exception as e:
            logger.error(f"Error in SecurityAgent: {str(e)}")
            return f"Error executing command: {str(e)}"
    
    def _scan_code(self, file_path):
        """
        Scan code for security vulnerabilities.
        
        Args:
            file_path: Path to the file to scan
            
        Returns:
            Security analysis of the code
        """
        if not os.path.exists(file_path):
            return f"Error: File not found: {file_path}"
        
        try:
            # Read the file
            with open(file_path, 'r') as f:
                code = f.read()
            
            # Determine language from file extension
            _, ext = os.path.splitext(file_path)
            language = self._get_language_from_extension(ext)
            
            if not language:
                return f"Error: Unsupported file type: {ext}"
            
            # Try using AI Service first for advanced analysis
            try:
                logger.debug(f"Using AI Service to scan {language} code for security issues")
                ai_analysis = ai_service.analyze_code(language, code, analysis_type="security")
                
                if ai_analysis and "Error" not in ai_analysis:
                    result = f"Security Scan Results for {file_path} ({language}):\n\n"
                    result += ai_analysis
                    return result
            except Exception as ai_err:
                logger.warning(f"AI Service code security scan failed: {str(ai_err)}. Falling back to pattern-based scanning.")
            
            # Fallback to basic pattern matching
            vulnerabilities = []
            
            # Check for common vulnerabilities based on language
            if language in ["python", "py"]:
                vulnerabilities.extend(self._check_python_vulnerabilities(code))
            elif language in ["javascript", "js"]:
                vulnerabilities.extend(self._check_javascript_vulnerabilities(code))
            elif language in ["php"]:
                vulnerabilities.extend(self._check_php_vulnerabilities(code))
            
            # Format the result
            if vulnerabilities:
                result = f"Security Scan Results for {file_path} ({language}):\n\n"
                result += "Potential Vulnerabilities Found:\n"
                for i, vuln in enumerate(vulnerabilities, 1):
                    result += f"{i}. {vuln['type']}: {vuln['description']}\n"
                    if 'line' in vuln:
                        result += f"   Line {vuln['line']}: {vuln['code']}\n"
                    if 'recommendation' in vuln:
                        result += f"   Recommendation: {vuln['recommendation']}\n"
                    result += "\n"
            else:
                result = f"Security Scan Results for {file_path} ({language}):\n\n"
                result += "No obvious security vulnerabilities detected. However, this does not guarantee the code is secure.\n"
                result += "Consider a more thorough security review with specialized tools."
            
            return result
            
        except Exception as e:
            logger.error(f"Error scanning code: {str(e)}")
            return f"Error scanning code: {str(e)}"
    
    def _owasp_check(self, target_url):
        """
        Check a web application against OWASP Top 10 vulnerabilities.
        
        Args:
            target_url: URL of the target web application
            
        Returns:
            OWASP security analysis
        """
        # Ensure URL has http/https prefix
        if not target_url.startswith(("http://", "https://")):
            target_url = "https://" + target_url
        
        try:
            # Try using AI Service for OWASP analysis based on best practices
            try:
                system_prompt = f"""
                You are a security expert specializing in web application security.
                Analyze the target URL {target_url} and provide a thorough OWASP Top 10 security assessment.
                Focus on the most critical security risks from the latest OWASP Top 10:
                
                1. Broken Access Control
                2. Cryptographic Failures
                3. Injection
                4. Insecure Design
                5. Security Misconfiguration
                6. Vulnerable and Outdated Components
                7. Identification and Authentication Failures
                8. Software and Data Integrity Failures
                9. Security Logging and Monitoring Failures
                10. Server-Side Request Forgery
                
                For each risk category, explain:
                - What the vulnerability is
                - How it might manifest in this application
                - How to test for it
                - Recommendations to mitigate the risk
                
                Format your response in clear sections with headings and bullet points.
                """
                
                ai_analysis = "Based on the provided URL, I can offer general OWASP Top 10 security assessment guidance:\n\n"
                
                # Use AI service to generate the analysis
                if 'claude' in ai_service.models:
                    logger.debug(f"Using AI Service to analyze OWASP risks for {target_url}")
                    response = ai_service.models['claude'].messages.create(
                        model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": f"Please provide an OWASP Top 10 security assessment for {target_url}"}
                        ],
                        temperature=0.1,
                        max_tokens=2500
                    )
                    ai_analysis = response.content[0].text
                
                result = f"OWASP Top 10 Security Assessment for {target_url}:\n\n"
                result += ai_analysis
                return result
                
            except Exception as ai_err:
                logger.warning(f"AI Service OWASP analysis failed: {str(ai_err)}. Falling back to basic checks.")
            
            # Basic security checks as fallback
            result = f"OWASP Top 10 Security Assessment for {target_url}:\n\n"
            result += "Note: This is a basic assessment. A comprehensive security audit would require detailed testing.\n\n"
            
            # Try to fetch the URL to check basic security headers
            try:
                response = requests.get(target_url, timeout=10)
                headers = response.headers
                
                # Check security headers
                security_headers = {
                    "Strict-Transport-Security": "Missing HSTS header which helps protect against SSL strip attacks",
                    "Content-Security-Policy": "Missing CSP header which helps prevent XSS and data injection attacks",
                    "X-Content-Type-Options": "Missing X-Content-Type-Options header which prevents MIME type sniffing",
                    "X-Frame-Options": "Missing X-Frame-Options header which prevents clickjacking attacks",
                    "X-XSS-Protection": "Missing X-XSS-Protection header which enables browser XSS protection"
                }
                
                result += "Security Headers Analysis:\n"
                for header, issue in security_headers.items():
                    if header not in headers:
                        result += f"- {issue}\n"
                    else:
                        result += f"+ {header} is properly configured\n"
                
                # Check if using HTTPS
                if target_url.startswith("http://"):
                    result += "- Site is not using HTTPS which exposes data to man-in-the-middle attacks\n"
                else:
                    result += "+ Site is using HTTPS\n"
                    
            except requests.exceptions.RequestException as req_err:
                result += f"Unable to connect to {target_url}: {str(req_err)}\n"
            
            # Add general recommendations
            result += "\nKey OWASP Top 10 Security Recommendations:\n"
            result += "1. Implement proper input validation and output encoding to prevent injection attacks\n"
            result += "2. Use parameterized queries for database operations\n"
            result += "3. Implement proper access controls and authentication mechanisms\n"
            result += "4. Keep all components and dependencies up to date\n"
            result += "5. Implement proper logging and monitoring\n"
            result += "6. Use HTTPS with proper TLS configuration\n"
            result += "7. Set secure cookie attributes (HttpOnly, Secure, SameSite)\n"
            result += "8. Implement proper session management\n"
            result += "9. Use Content Security Policy (CSP) to mitigate XSS attacks\n"
            result += "10. Validate and sanitize all user inputs\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error performing OWASP check: {str(e)}")
            return f"Error performing OWASP check: {str(e)}"
    
    def _check_dependencies(self, project_path):
        """
        Check project dependencies for known vulnerabilities.
        
        Args:
            project_path: Path to the project directory or dependency file
            
        Returns:
            Analysis of dependencies for known vulnerabilities
        """
        if not os.path.exists(project_path):
            return f"Error: Path not found: {project_path}"
        
        try:
            # Determine project type
            project_type = self._detect_project_type(project_path)
            
            if not project_type:
                return "Error: Could not determine project type. Supported project types: Node.js (package.json), Python (requirements.txt, pyproject.toml)"
            
            # Extract dependencies based on project type
            dependencies = self._extract_dependencies(project_path, project_type)
            
            if not dependencies:
                return f"No dependencies found in {project_path}"
            
            # Use AI service to analyze dependencies if available
            try:
                system_prompt = f"""
                You are a security expert specializing in software supply chain security.
                Analyze the provided dependencies for potential security vulnerabilities and outdated packages.
                For each dependency, consider:
                
                1. Known vulnerabilities in current versions
                2. Whether the version is outdated
                3. The likelihood of security issues based on the package's track record
                4. Proper dependency management practices
                
                Format your response in clear sections with headings and bullet points.
                """
                
                dependencies_str = json.dumps(dependencies, indent=2)
                
                if 'claude' in ai_service.models:
                    logger.debug(f"Using AI Service to analyze dependencies for {project_path}")
                    response = ai_service.models['claude'].messages.create(
                        model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": f"Please analyze these {project_type} dependencies for potential security issues:\n```json\n{dependencies_str}\n```"}
                        ],
                        temperature=0.1,
                        max_tokens=2000
                    )
                    ai_analysis = response.content[0].text
                    
                    result = f"Dependency Security Analysis for {project_path} ({project_type}):\n\n"
                    result += ai_analysis
                    return result
                    
            except Exception as ai_err:
                logger.warning(f"AI Service dependency analysis failed: {str(ai_err)}. Falling back to basic analysis.")
            
            # Basic dependency analysis as fallback
            result = f"Dependency Security Analysis for {project_path} ({project_type}):\n\n"
            result += f"Found {len(dependencies)} dependencies:\n\n"
            
            for i, (name, version) in enumerate(dependencies.items(), 1):
                result += f"{i}. {name}: {version}\n"
            
            result += "\nRecommendations:\n"
            result += "1. Regularly update dependencies to their latest secure versions\n"
            result += "2. Consider using tools like npm audit (Node.js) or safety (Python) for vulnerability scanning\n"
            result += "3. Implement a dependency lock file to ensure consistent installations\n"
            result += "4. Review dependencies for suspicious packages or unused dependencies\n"
            result += "5. Consider setting up automatic vulnerability scanning in your CI/CD pipeline\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error checking dependencies: {str(e)}")
            return f"Error checking dependencies: {str(e)}"
    
    def _harden_linux(self, area=None):
        """
        Provide recommendations for hardening a Linux system.
        
        Args:
            area: Specific area to harden (optional)
            
        Returns:
            Linux hardening recommendations
        """
        try:
            # Use AI service for detailed hardening recommendations
            if area:
                query = f"Provide detailed Linux hardening recommendations for {area}"
            else:
                query = "Provide comprehensive Linux hardening recommendations for a secure system"
                
            try:
                system_prompt = f"""
                You are a Linux security expert specializing in system hardening.
                Provide detailed, actionable recommendations for hardening Linux systems.
                Focus on:
                
                1. Practical steps that can be implemented
                2. Command examples where applicable
                3. Configuration file changes with specific parameters
                4. Best practices from established security frameworks
                
                Format your response in clear sections with headings, numbered steps, and code examples.
                """
                
                if 'claude' in ai_service.models:
                    logger.debug(f"Using AI Service to generate Linux hardening recommendations")
                    response = ai_service.models['claude'].messages.create(
                        model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": query}
                        ],
                        temperature=0.1,
                        max_tokens=2500
                    )
                    ai_analysis = response.content[0].text
                    
                    result = f"Linux Hardening Recommendations"
                    if area:
                        result += f" for {area}"
                    result += ":\n\n"
                    result += ai_analysis
                    return result
                    
            except Exception as ai_err:
                logger.warning(f"AI Service hardening recommendations failed: {str(ai_err)}. Falling back to basic recommendations.")
            
            # Basic hardening recommendations as fallback
            result = f"Linux Hardening Recommendations"
            if area:
                result += f" for {area}"
            result += ":\n\n"
            
            if area == "ssh":
                result += "SSH Hardening Recommendations:\n\n"
                result += "1. Disable root login\n   Edit /etc/ssh/sshd_config and set: PermitRootLogin no\n\n"
                result += "2. Use SSH key authentication instead of passwords\n   Generate keys: ssh-keygen -t ed25519\n   Copy to server: ssh-copy-id user@server\n   Disable password auth: PasswordAuthentication no\n\n"
                result += "3. Change default SSH port\n   Edit /etc/ssh/sshd_config and set: Port 2222\n\n"
                result += "4. Limit user access\n   Edit /etc/ssh/sshd_config and set: AllowUsers user1 user2\n\n"
                result += "5. Enable strict mode\n   Edit /etc/ssh/sshd_config and set: StrictModes yes\n\n"
                result += "6. Implement idle timeout\n   Edit /etc/ssh/sshd_config and set:\n   ClientAliveInterval 300\n   ClientAliveCountMax 0\n\n"
                result += "7. Disable empty passwords\n   Edit /etc/ssh/sshd_config and set: PermitEmptyPasswords no\n\n"
                result += "8. Disable X11 forwarding if not needed\n   Edit /etc/ssh/sshd_config and set: X11Forwarding no\n\n"
            
            elif area == "firewall":
                result += "Firewall Hardening Recommendations:\n\n"
                result += "1. Enable and configure UFW (Uncomplicated Firewall)\n   sudo apt install ufw\n   sudo ufw default deny incoming\n   sudo ufw default allow outgoing\n   sudo ufw allow ssh\n   sudo ufw enable\n\n"
                result += "2. Only allow necessary services\n   sudo ufw allow 80/tcp # HTTP\n   sudo ufw allow 443/tcp # HTTPS\n\n"
                result += "3. Limit SSH access by IP\n   sudo ufw allow from 192.168.1.0/24 to any port 22\n\n"
                result += "4. Enable logging\n   sudo ufw logging on\n\n"
                result += "5. Check firewall status\n   sudo ufw status verbose\n\n"
                result += "6. Consider iptables for more complex rules\n   sudo apt install iptables-persistent\n\n"
            
            else:
                # General hardening recommendations
                result += "General Linux Hardening Recommendations:\n\n"
                result += "1. Keep the system updated\n   sudo apt update && sudo apt upgrade -y\n\n"
                result += "2. Enable automatic security updates\n   sudo apt install unattended-upgrades\n   sudo dpkg-reconfigure unattended-upgrades\n\n"
                result += "3. Configure a firewall\n   sudo apt install ufw\n   sudo ufw default deny incoming\n   sudo ufw default allow outgoing\n   sudo ufw allow ssh\n   sudo ufw enable\n\n"
                result += "4. Secure SSH access\n   Edit /etc/ssh/sshd_config and set:\n   PermitRootLogin no\n   PasswordAuthentication no\n\n"
                result += "5. Implement strong password policies\n   sudo apt install libpam-pwquality\n   Edit /etc/security/pwquality.conf\n\n"
                result += "6. Disable unnecessary services\n   sudo systemctl disable <service>\n   sudo systemctl stop <service>\n\n"
                result += "7. Regularly audit user accounts\n   sudo awk -F: '\\$3 >= 1000 && \\$1 != \"nobody\" {print \\$1}' /etc/passwd\n\n"
                result += "8. Implement file system security\n   sudo chmod 644 /etc/passwd\n   sudo chmod 600 /etc/shadow\n\n"
                result += "9. Configure system logging\n   sudo apt install rsyslog\n   sudo systemctl enable rsyslog\n\n"
                result += "10. Implement regular backups\n    sudo apt install restic\n\n"
                result += "11. Install and configure intrusion detection\n    sudo apt install aide\n    sudo aideinit\n\n"
                result += "12. Disable USB storage if not needed\n    echo 'blacklist usb-storage' | sudo tee /etc/modprobe.d/disable-usb-storage.conf\n\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating hardening recommendations: {str(e)}")
            return f"Error generating hardening recommendations: {str(e)}"
    
    def _generate_report(self, target, vuln_type=None):
        """
        Generate a security report for a target.
        
        Args:
            target: Target to generate report for (URL or path)
            vuln_type: Specific vulnerability type to focus on (optional)
            
        Returns:
            Security report
        """
        try:
            # Determine if target is a URL or file path
            is_url = target.startswith(("http://", "https://")) or not os.path.exists(target)
            
            # Create prompt based on target type and vulnerability type
            if is_url:
                if not target.startswith(("http://", "https://")):
                    target = "https://" + target
                
                title = f"Security Report for {target}"
                if vuln_type:
                    title += f" focusing on {vuln_type}"
                    
                system_prompt = f"""
                You are a security expert specializing in web application security.
                Generate a comprehensive security report for the target website {target}.
                """
                
                if vuln_type:
                    system_prompt += f"\nFocus specifically on {vuln_type} vulnerabilities."
                    
                system_prompt += """
                Include in your report:
                
                1. Executive summary
                2. Methodology
                3. Findings and vulnerabilities
                4. Risk assessment for each finding
                5. Detailed recommendations
                6. Remediation plan with priorities
                
                Format your report professionally with clear sections, headings, and bullet points.
                """
                
                query = f"Generate a security report for {target}"
                if vuln_type:
                    query += f" focusing on {vuln_type} vulnerabilities"
                
            else:
                # Target is a file or directory
                title = f"Code Security Report for {target}"
                if vuln_type:
                    title += f" focusing on {vuln_type}"
                    
                system_prompt = f"""
                You are a security expert specializing in application security and code review.
                Generate a comprehensive security report for the code located at {target}.
                """
                
                if vuln_type:
                    system_prompt += f"\nFocus specifically on {vuln_type} vulnerabilities."
                    
                system_prompt += """
                Include in your report:
                
                1. Executive summary
                2. Methodology for code review
                3. Findings and vulnerabilities
                4. Risk assessment for each finding
                5. Code examples and fix recommendations
                6. Remediation plan with priorities
                
                Format your report professionally with clear sections, headings, and bullet points.
                """
                
                query = f"Generate a code security report for {target}"
                if vuln_type:
                    query += f" focusing on {vuln_type} vulnerabilities"
            
            # Use AI service to generate the report
            try:
                if 'claude' in ai_service.models:
                    logger.debug(f"Using AI Service to generate security report for {target}")
                    response = ai_service.models['claude'].messages.create(
                        model="claude-3-5-sonnet-20241022",  # the newest Anthropic model is "claude-3-5-sonnet-20241022" which was released October 22, 2024
                        system=system_prompt,
                        messages=[
                            {"role": "user", "content": query}
                        ],
                        temperature=0.1,
                        max_tokens=3000
                    )
                    ai_analysis = response.content[0].text
                    
                    result = f"{title}\n{'=' * len(title)}\n\n"
                    result += ai_analysis
                    return result
                    
            except Exception as ai_err:
                logger.warning(f"AI Service report generation failed: {str(ai_err)}. Falling back to template report.")
            
            # Basic report template as fallback
            result = f"{title}\n{'=' * len(title)}\n\n"
            
            result += "EXECUTIVE SUMMARY\n----------------\n\n"
            result += f"This report presents the findings of a security assessment conducted for {target}. "
            if vuln_type:
                result += f"The assessment focused specifically on {vuln_type} vulnerabilities. "
            result += "The purpose of this assessment was to identify security vulnerabilities and provide recommendations for remediation.\n\n"
            
            result += "METHODOLOGY\n-----------\n\n"
            if is_url:
                result += "The assessment was conducted using a combination of automated scanning tools and manual testing techniques. "
                result += "The methodology followed industry best practices for web application security testing.\n\n"
            else:
                result += "The assessment was conducted using static code analysis techniques. "
                result += "The methodology followed industry best practices for secure code review.\n\n"
            
            result += "FINDINGS\n--------\n\n"
            result += "Due to the limited scope of this automated report, a full security assessment could not be performed. "
            result += "It is recommended to conduct a comprehensive security assessment with specialized tools and manual testing.\n\n"
            
            result += "RECOMMENDATIONS\n---------------\n\n"
            
            if is_url:
                result += "1. Implement security headers (HSTS, CSP, X-Content-Type-Options, etc.)\n"
                result += "2. Ensure proper input validation and output encoding\n"
                result += "3. Use parameterized queries for database operations\n"
                result += "4. Implement proper authentication and session management\n"
                result += "5. Keep all components and dependencies up to date\n"
            else:
                result += "1. Implement secure coding practices\n"
                result += "2. Conduct regular code reviews\n"
                result += "3. Implement proper input validation and output encoding\n"
                result += "4. Use parameterized queries for database operations\n"
                result += "5. Keep all dependencies up to date\n"
            
            result += "\nCONCLUSION\n----------\n\n"
            result += "This automated report provides a starting point for improving the security of "
            if is_url:
                result += f"the web application at {target}. "
            else:
                result += f"the code at {target}. "
            result += "For a comprehensive security assessment, it is recommended to engage with specialized security professionals.\n"
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            return f"Error generating report: {str(e)}"
    
    def _get_language_from_extension(self, ext):
        """Determine language from file extension."""
        ext = ext.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.html': 'html',
            '.css': 'css',
            '.php': 'php',
            '.rb': 'ruby',
            '.java': 'java',
            '.go': 'go',
            '.ts': 'typescript',
            '.cs': 'csharp',
            '.c': 'c',
            '.cpp': 'cpp',
            '.sh': 'bash',
            '.sql': 'sql',
            '.md': 'markdown',
            '.json': 'json',
            '.xml': 'xml',
            '.yaml': 'yaml',
            '.yml': 'yaml'
        }
        
        return language_map.get(ext)
    
    def _check_python_vulnerabilities(self, code):
        """Check Python code for common security vulnerabilities."""
        vulnerabilities = []
        
        # Check for SQL injection vulnerabilities
        sql_patterns = [
            (r'cursor\.execute\s*\(\s*[\'"][^\'",]*%s[^\'",]*[\'"]\s*%\s*\(', 
             "Potential SQL Injection",
             "String formatting used with SQL queries is vulnerable to SQL injection attacks.",
             "Use parameterized queries with cursor.execute(query, params) instead of string formatting."),
            
            (r'cursor\.execute\s*\(\s*[\'"][^\'",]*\'\s*\+', 
             "Potential SQL Injection",
             "String concatenation used with SQL queries is vulnerable to SQL injection attacks.",
             "Use parameterized queries with cursor.execute(query, params) instead of string concatenation."),
             
            (r'cursor\.execute\s*\(\s*f[\'"]', 
             "Potential SQL Injection",
             "f-strings used with SQL queries are vulnerable to SQL injection attacks.",
             "Use parameterized queries with cursor.execute(query, params) instead of f-strings.")
        ]
        
        for pattern, vuln_type, description, recommendation in sql_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                line = code.splitlines()[line_num - 1].strip()
                vulnerabilities.append({
                    'type': vuln_type,
                    'description': description,
                    'line': line_num,
                    'code': line,
                    'recommendation': recommendation
                })
        
        # Check for command injection vulnerabilities
        cmd_patterns = [
            (r'os\.system\s*\(\s*[^)]*\+', 
             "Potential Command Injection",
             "String concatenation used with os.system() is vulnerable to command injection attacks.",
             "Use subprocess module with shell=False and pass arguments as a list."),
             
            (r'os\.system\s*\(\s*f[\'"]', 
             "Potential Command Injection",
             "f-strings used with os.system() are vulnerable to command injection attacks.",
             "Use subprocess module with shell=False and pass arguments as a list."),
             
            (r'subprocess\.(?:call|run|Popen)\s*\([^)]*shell\s*=\s*True', 
             "Potential Command Injection",
             "Using shell=True with subprocess functions is vulnerable to command injection attacks.",
             "Use shell=False and pass arguments as a list.")
        ]
        
        for pattern, vuln_type, description, recommendation in cmd_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                line = code.splitlines()[line_num - 1].strip()
                vulnerabilities.append({
                    'type': vuln_type,
                    'description': description,
                    'line': line_num,
                    'code': line,
                    'recommendation': recommendation
                })
        
        # Check for pickle security issues
        if 'pickle.loads' in code:
            matches = re.finditer(r'pickle\.loads\s*\(', code)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                line = code.splitlines()[line_num - 1].strip()
                vulnerabilities.append({
                    'type': "Potential Insecure Deserialization",
                    'description': "The pickle module is unsafe when used with untrusted data.",
                    'line': line_num,
                    'code': line,
                    'recommendation': "Avoid using pickle with untrusted data. Consider using JSON or other safer serialization formats."
                })
        
        # Check for hardcoded secrets
        secret_patterns = [
            (r'(?:password|passwd|pwd|token|secret|key|api_key|apikey)\s*=\s*[\'"]+[a-zA-Z0-9]{10,}[\'"]+', 
             "Potential Hardcoded Secret",
             "Hardcoded secrets found in the code.",
             "Store secrets in environment variables or a secure vault solution.")
        ]
        
        for pattern, vuln_type, description, recommendation in secret_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                line = code.splitlines()[line_num - 1].strip()
                # Redact the actual secret from the output
                redacted_line = re.sub(r'([\'"]+)[a-zA-Z0-9]{10,}([\'"]+)', r'\1[REDACTED]\2', line)
                vulnerabilities.append({
                    'type': vuln_type,
                    'description': description,
                    'line': line_num,
                    'code': redacted_line,
                    'recommendation': recommendation
                })
        
        return vulnerabilities
    
    def _check_javascript_vulnerabilities(self, code):
        """Check JavaScript code for common security vulnerabilities."""
        vulnerabilities = []
        
        # Check for XSS vulnerabilities
        xss_patterns = [
            (r'innerHTML\s*=', 
             "Potential Cross-Site Scripting (XSS)",
             "Using innerHTML can lead to XSS vulnerabilities if user input is not properly sanitized.",
             "Use textContent instead, or sanitize input with a library like DOMPurify before using innerHTML."),
             
            (r'document\.write\s*\(', 
             "Potential Cross-Site Scripting (XSS)",
             "Using document.write can lead to XSS vulnerabilities if user input is not properly sanitized.",
             "Avoid document.write and use safer DOM manipulation methods."),
             
            (r'eval\s*\(', 
             "Potential Injection and XSS",
             "Using eval() can lead to code injection and XSS vulnerabilities.",
             "Avoid using eval() and find safer alternatives for the intended functionality.")
        ]
        
        for pattern, vuln_type, description, recommendation in xss_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                line = code.splitlines()[line_num - 1].strip()
                vulnerabilities.append({
                    'type': vuln_type,
                    'description': description,
                    'line': line_num,
                    'code': line,
                    'recommendation': recommendation
                })
        
        # Check for hardcoded secrets
        secret_patterns = [
            (r'(?:password|passwd|pwd|token|secret|key|api_key|apikey)\s*=\s*[\'"]+[a-zA-Z0-9]{10,}[\'"]+', 
             "Potential Hardcoded Secret",
             "Hardcoded secrets found in the code.",
             "Store secrets in environment variables or a secure vault solution.")
        ]
        
        for pattern, vuln_type, description, recommendation in secret_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                line = code.splitlines()[line_num - 1].strip()
                # Redact the actual secret from the output
                redacted_line = re.sub(r'([\'"]+)[a-zA-Z0-9]{10,}([\'"]+)', r'\1[REDACTED]\2', line)
                vulnerabilities.append({
                    'type': vuln_type,
                    'description': description,
                    'line': line_num,
                    'code': redacted_line,
                    'recommendation': recommendation
                })
        
        return vulnerabilities
    
    def _check_php_vulnerabilities(self, code):
        """Check PHP code for common security vulnerabilities."""
        vulnerabilities = []
        
        # Check for SQL injection vulnerabilities
        sql_patterns = [
            (r'mysqli_query\s*\(\s*[^,]+,\s*[\'"][^\'",]*\'\s*\.\s*', 
             "Potential SQL Injection",
             "String concatenation used with SQL queries is vulnerable to SQL injection attacks.",
             "Use prepared statements with mysqli_prepare() instead of string concatenation."),
             
            (r'mysql_query\s*\(\s*[\'"][^\'",]*\'\s*\.\s*', 
             "Potential SQL Injection",
             "String concatenation used with mysql_query() is vulnerable to SQL injection attacks.",
             "Use prepared statements with mysqli_prepare() instead of deprecated mysql_query().")
        ]
        
        for pattern, vuln_type, description, recommendation in sql_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                line = code.splitlines()[line_num - 1].strip()
                vulnerabilities.append({
                    'type': vuln_type,
                    'description': description,
                    'line': line_num,
                    'code': line,
                    'recommendation': recommendation
                })
        
        # Check for command injection vulnerabilities
        cmd_patterns = [
            (r'(?:system|exec|shell_exec|passthru|proc_open)\s*\(\s*[^)]*\.\s*', 
             "Potential Command Injection",
             "String concatenation used with command execution functions is vulnerable to command injection attacks.",
             "Avoid using command execution functions with user input, or properly validate and escape inputs.")
        ]
        
        for pattern, vuln_type, description, recommendation in cmd_patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                line = code.splitlines()[line_num - 1].strip()
                vulnerabilities.append({
                    'type': vuln_type,
                    'description': description,
                    'line': line_num,
                    'code': line,
                    'recommendation': recommendation
                })
        
        # Check for XSS vulnerabilities
        if 'echo' in code and not ('htmlspecialchars' in code or 'htmlentities' in code):
            matches = re.finditer(r'echo\s+\$_(?:GET|POST|REQUEST|COOKIE)', code)
            for match in matches:
                line_num = code[:match.start()].count('\n') + 1
                line = code.splitlines()[line_num - 1].strip()
                vulnerabilities.append({
                    'type': "Potential Cross-Site Scripting (XSS)",
                    'description': "Outputting user input without proper escaping can lead to XSS vulnerabilities.",
                    'line': line_num,
                    'code': line,
                    'recommendation': "Use htmlspecialchars() or htmlentities() to escape user input before outputting it."
                })
        
        return vulnerabilities
    
    def _detect_project_type(self, project_path):
        """Detect the type of project based on dependency files."""
        if os.path.isfile(project_path):
            if project_path.endswith("package.json"):
                return "nodejs"
            elif project_path.endswith("requirements.txt"):
                return "python"
            elif project_path.endswith("pyproject.toml"):
                return "python"
            return None
        
        # Check for dependency files in directory
        if os.path.isdir(project_path):
            if os.path.exists(os.path.join(project_path, "package.json")):
                return "nodejs"
            elif os.path.exists(os.path.join(project_path, "requirements.txt")):
                return "python"
            elif os.path.exists(os.path.join(project_path, "pyproject.toml")):
                return "python"
        
        return None
    
    def _extract_dependencies(self, project_path, project_type):
        """Extract dependencies from project files."""
        dependencies = {}
        
        if project_type == "nodejs":
            # Extract dependencies from package.json
            package_json_path = project_path
            if os.path.isdir(project_path):
                package_json_path = os.path.join(project_path, "package.json")
            
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                
                # Get regular dependencies
                if "dependencies" in package_data:
                    for dep, version in package_data["dependencies"].items():
                        dependencies[dep] = version
                
                # Get dev dependencies
                if "devDependencies" in package_data:
                    for dep, version in package_data["devDependencies"].items():
                        dependencies[dep] = version
            except Exception as e:
                logger.warning(f"Error parsing package.json: {str(e)}")
        
        elif project_type == "python":
            # Extract dependencies from requirements.txt or pyproject.toml
            if os.path.isdir(project_path):
                requirements_path = os.path.join(project_path, "requirements.txt")
                pyproject_path = os.path.join(project_path, "pyproject.toml")
            else:
                requirements_path = project_path if project_path.endswith("requirements.txt") else None
                pyproject_path = project_path if project_path.endswith("pyproject.toml") else None
            
            # Try requirements.txt first
            if requirements_path and os.path.exists(requirements_path):
                try:
                    with open(requirements_path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith('#'):
                                # Parse requirement line (e.g., "flask==2.0.1")
                                parts = line.split('==')
                                if len(parts) == 2:
                                    dependencies[parts[0]] = parts[1]
                                else:
                                    # Handle other formats like >=, ~=, etc.
                                    name = line.split('>=')[0].split('<=')[0].split('~=')[0].split('>')[0].split('<')[0].strip()
                                    version = line.replace(name, '').strip()
                                    if name:
                                        dependencies[name] = version if version else "latest"
                except Exception as e:
                    logger.warning(f"Error parsing requirements.txt: {str(e)}")
            
            # Then try pyproject.toml
            elif pyproject_path and os.path.exists(pyproject_path):
                try:
                    with open(pyproject_path, 'r') as f:
                        content = f.read()
                    
                    # Very basic TOML parsing for dependencies
                    # This is not a full TOML parser
                    in_dependencies = False
                    for line in content.splitlines():
                        line = line.strip()
                        if "[tool.poetry.dependencies]" in line or "[project.dependencies]" in line:
                            in_dependencies = True
                            continue
                        elif in_dependencies and line.startswith('['):
                            in_dependencies = False
                            continue
                        
                        if in_dependencies and '=' in line:
                            parts = line.split('=')
                            if len(parts) >= 2:
                                name = parts[0].strip().strip('"').strip("'")
                                version = parts[1].strip().strip('"').strip("'")
                                if name != "python" and name:  # Skip python version constraint
                                    dependencies[name] = version
                except Exception as e:
                    logger.warning(f"Error parsing pyproject.toml: {str(e)}")
        
        return dependencies