import os
import logging
import glob
from typing import Dict, Any, List

logger = logging.getLogger("code-scan-action")

class CodeScanAction:
    """Action for scanning code repositories."""
    
    def __init__(self, agent, event):
        """Initialize the code scan action.
        
        Args:
            agent: The GitHub agent
            event: The GitHub event data
        """
        self.agent = agent
        self.event = event
        self.include_patterns = self._parse_patterns(os.environ.get("INCLUDE_PATTERNS", ""))
        self.exclude_patterns = self._parse_patterns(os.environ.get("EXCLUDE_PATTERNS", ""))
        self.max_files = int(os.environ.get("MAX_FILES", 10))
    
    def _parse_patterns(self, patterns_str: str) -> List[str]:
        """Parse comma-separated glob patterns."""
        if not patterns_str:
            return []
        return [p.strip() for p in patterns_str.split(",")]
    
    def _get_files_to_scan(self, repo_name: str) -> List[str]:
        """Get files to scan based on patterns."""
        # Get repository structure
        repo_info = self.agent.execute_tool("get_repository", {
            "repo": repo_name
        })
        
        # Use file search API or default patterns if none provided
        if not self.include_patterns:
            self.include_patterns = [
                "*.py", "*.js", "*.ts", "*.jsx", "*.tsx", 
                "*.java", "*.cpp", "*.c", "*.h", "*.go",
                "*.rb", "*.php", "*.sh"
            ]
        
        # TODO: This is a simplified version, real implementation would involve
        # GitHub API calls to list files in repository with appropriate filtering
        # For now, we'll return a placeholder set of files
        
        files_to_scan = []
        
        # This would be replaced with actual API calls
        for pattern in self.include_patterns:
            # Simulated matching
            if "*.py" in pattern:
                files_to_scan.extend(["src/main.py", "src/utils.py", "tests/test_main.py"])
            elif "*.js" in pattern:
                files_to_scan.extend(["src/index.js", "src/components/app.js"])
            elif "*.go" in pattern:
                files_to_scan.append("main.go")
        
        # Filter based on exclude patterns
        if self.exclude_patterns:
            files_to_scan = [f for f in files_to_scan if not any(
                glob.fnmatch.fnmatch(f, pattern) for pattern in self.exclude_patterns
            )]
        
        return files_to_scan[:self.max_files]
    
    def run(self) -> Dict[str, Any]:
        """Run the code scan action."""
        try:
            # Extract repository information from event
            repo_name = self.event.get("repository", {}).get("full_name")
            
            if not repo_name:
                logger.error("Missing required repository information in GitHub event")
                return {
                    "summary": "Error: Could not extract repository information from GitHub event",
                    "details": "Make sure this action is triggered on repository events",
                    "suggestions": ""
                }
            
            # Get repository information
            repo_info = self.agent.execute_tool("get_repository", {
                "repo": repo_name
            })
            
            # Get repository stats
            repo_stats = self.agent.execute_tool("get_repository_stats", {
                "repo": repo_name
            })
            
            # Get files to scan
            files_to_scan = self._get_files_to_scan(repo_name)
            
            # Read file contents
            file_contents = {}
            for file_path in files_to_scan:
                try:
                    content = self.agent.execute_tool("get_repository_file_content", {
                        "repo": repo_name,
                        "path": file_path
                    })
                    file_contents[file_path] = content
                except Exception as e:
                    logger.warning(f"Error reading file {file_path}: {str(e)}")
                    file_contents[file_path] = f"Error: {str(e)}"
            
            # Construct message for the agent
            file_content_str = ""
            for file_path, content in file_contents.items():
                file_content_str += f"\n\n--- {file_path} ---\n{content[:2000]}"
                if len(content) > 2000:
                    file_content_str += "...[truncated]"
            
            message = (
                f"Please perform a security and best practices scan on this repository:\n\n"
                f"Repository: {repo_name}\n"
                f"Description: {repo_info.get('description', 'No description')}\n\n"
                f"I'll provide the content of key files for you to analyze. "
                f"Please scan for security vulnerabilities, code quality issues, and best practices.\n"
                f"{file_content_str}\n\n"
                f"Please provide:\n"
                f"1. A summary of the repository structure and purpose\n"
                f"2. Security vulnerabilities found (if any)\n"
                f"3. Code quality issues\n"
                f"4. Best practices recommendations\n"
                f"5. Overall assessment of the codebase"
            )
            
            # Process message with agent
            context = f"Code scan for {repo_name}"
            response = self.agent.process_message(message, context)
            
            # Create or update a file in the repository with the results
            # Note: This would require write permissions and should be optional
            
            # Extract structured data from the response
            lines = response["content"].split("\n")
            summary = ""
            details = ""
            suggestions = ""
            
            current_section = None
            for line in lines:
                if "summary" in line.lower() or "structure" in line.lower():
                    current_section = "summary"
                    continue
                elif "vulnerabilit" in line.lower() or "issue" in line.lower() or "quality" in line.lower():
                    current_section = "details"
                    continue
                elif "recommend" in line.lower() or "best practice" in line.lower() or "suggest" in line.lower():
                    current_section = "suggestions"
                    continue
                
                if current_section == "summary":
                    summary += line + "\n"
                elif current_section == "details":
                    details += line + "\n"
                elif current_section == "suggestions":
                    suggestions += line + "\n"
            
            # Return results
            return {
                "summary": summary.strip(),
                "details": details.strip(),
                "suggestions": suggestions.strip()
            }
            
        except Exception as e:
            logger.error(f"Error running code scan action: {str(e)}")
            return {
                "summary": f"Error: {str(e)}",
                "details": "",
                "suggestions": ""
            }