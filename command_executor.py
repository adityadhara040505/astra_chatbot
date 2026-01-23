"""
Intelligent Command Executor - Uses LLM + Ubuntu Linux Toolbox to execute commands with retry logic
"""
import os
import subprocess
import json
import httpx
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from pdf_knowledge_base import PDFKnowledgeBase

OLLAMA_API = os.environ.get("OLLAMA_API", "http://localhost:11434")
DEFAULT_MODEL = os.environ.get("ASTRA_CHATBOT_MODEL", "qwen2.5:0.5b")

class CommandExecutor:
    def __init__(self, pdf_path: str):
        self.pdf_kb = PDFKnowledgeBase(pdf_path)
        self.max_attempts = 5
        self.execution_history = []
    
    def ask_llm(self, prompt: str, context: str = "") -> str:
        """Ask LLM for help"""
        try:
            full_prompt = f"{context}\n\n{prompt}" if context else prompt
            
            with httpx.Client(timeout=60.0) as client:  # Increased from 30 to 60
                response = client.post(
                    f"{OLLAMA_API}/api/generate",
                    json={
                        "model": DEFAULT_MODEL,
                        "prompt": full_prompt,
                        "stream": False,
                        "options": {
                            "temperature": 0.1,  # Reduced from 0.3 for more deterministic
                            "num_predict": 200   # Reduced from 500 for faster response
                        }
                    }
                )
                response.raise_for_status()
                return response.json().get("response", "").strip()
        
        except Exception as e:
            return f"LLM Error: {str(e)}"
    
    def extract_commands(self, text: str) -> List[str]:
        """Extract shell commands from LLM response"""
        commands = []
        lines = text.split('\n')
        in_code_block = False
        
        # Common command prefixes - expanded to include system info commands
        command_prefixes = [
            # Package management
            'sudo', 'apt', 'apt-get', 'dpkg', 'snap', 'systemctl', 
            'flatpak', 'add-apt-repository', 'update-alternatives',
            # Network tools
            'wget', 'curl', 'ping', 'netstat', 'ss', 'ip', 'ifconfig',
            # Development
            'git', 'pip', 'python', 'python3', 'node', 'npm', 'bash', 'sh',
            # File operations
            'chmod', 'chown', 'mkdir', 'rm', 'cp', 'mv', 'ln', 'touch',
            'cat', 'less', 'more', 'head', 'tail', 'nano', 'vi', 'vim',
            # Search and text processing
            'grep', 'find', 'sed', 'awk', 'sort', 'uniq', 'wc',
            # Compression
            'tar', 'gzip', 'gunzip', 'zip', 'unzip', 'bzip2',
            # System information (IMPORTANT - these were missing!)
            'df', 'du', 'free', 'top', 'htop', 'ps', 'lsblk', 'lsof',
            'uname', 'uptime', 'who', 'whoami', 'id', 'hostname',
            # Process management
            'kill', 'killall', 'pkill', 'service', 'jobs', 'bg', 'fg',
            # Other common commands
            'echo', 'date', 'cal', 'which', 'whereis', 'man',
            'install', 'gpg', 'ssh', 'scp', 'rsync', 'mount', 'umount'
        ]
        
        for line in lines:
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Handle code blocks
            if line.startswith('```'):
                in_code_block = not in_code_block
                continue
            
            # Extract commands from code blocks
            if in_code_block:
                # Remove common prefixes like '$ ' or '# '
                if line.startswith('$ '):
                    commands.append(line[2:].strip())
                elif line.startswith('# ') and not line.startswith('##'):
                    # Skip comments unless they look like commands
                    continue
                else:
                    # Check if it looks like a command
                    first_word = line.split()[0] if line.split() else ''
                    if first_word in command_prefixes:
                        commands.append(line)
                continue
            
            # Outside code blocks
            # Remove $ prefix if present
            if line.startswith('$ '):
                commands.append(line[2:].strip())
            elif line.startswith('$'):
                commands.append(line[1:].strip())
            # Check for command prefixes
            elif any(line.startswith(prefix + ' ') or line == prefix for prefix in command_prefixes):
                commands.append(line)
            # Check for numbered lists (e.g., "1. sudo apt install...")
            elif line[0].isdigit() and '. ' in line:
                cmd_part = line.split('. ', 1)[1].strip()
                if any(cmd_part.startswith(prefix + ' ') for prefix in command_prefixes):
                    commands.append(cmd_part)
        
        return commands
    
    def execute_command(self, command: str) -> Tuple[bool, str, str]:
        """
        Execute a shell command
        Returns: (success, stdout, stderr)
        """
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            success = result.returncode == 0
            return success, result.stdout, result.stderr
        
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out after 60 seconds"
        except Exception as e:
            return False, "", str(e)
    
    def analyze_error(self, command: str, error: str, attempt: int) -> str:
        """Use LLM to analyze error and suggest fix"""
        # Get relevant context from PDF
        pdf_context = self.pdf_kb.get_context(f"{command} error fix")
        
        prompt = f"""You are a Linux system expert. A command failed and you need to fix it.

Command that failed: {command}
Error message: {error}
Attempt number: {attempt} of {self.max_attempts}

Based on the Ubuntu Linux Toolbox reference and your knowledge, provide:
1. A brief explanation of what went wrong
2. The EXACT command(s) to fix this issue (one per line, starting with $)

Be concise and provide working commands only."""
        
        return self.ask_llm(prompt, pdf_context)
    
    def execute_with_retry(self, user_request: str) -> Dict:
        """
        Main execution method with retry logic
        Returns execution report
        """
        report = {
            "request": user_request,
            "attempts": [],
            "final_status": "failed",
            "summary": ""
        }
        
        # Step 1: Get initial command from LLM + PDF
        print(f"\n🤖 Understanding request: {user_request}")
        pdf_context = self.pdf_kb.get_context(user_request)
        
        initial_prompt = f"""Task: {user_request}

Provide ONLY the Linux command(s) needed. One per line. No explanations.

Examples:
Task: check disk space
df -h

Task: install docker
sudo apt update
sudo apt install -y docker.io

Your commands:"""
        
        llm_response = self.ask_llm(initial_prompt, pdf_context)
        print(f"\n📝 LLM Response:\n{llm_response[:500]}\n")
        
        commands = self.extract_commands(llm_response)
        
        if not commands:
            print(f"⚠️  No commands extracted. Full LLM response:")
            print(llm_response)
            report["summary"] = f"❌ Could not determine commands from LLM response. Response was: {llm_response[:200]}"
            report["attempts"].append({
                "attempt": 0,
                "command": "N/A",
                "success": False,
                "stdout": "",
                "stderr": f"LLM response: {llm_response}"
            })
            return report
        
        print(f"📋 Identified {len(commands)} command(s) to execute:")
        for i, cmd in enumerate(commands, 1):
            print(f"  {i}. {cmd}")
        
        # Step 2: Execute commands with retry logic
        for cmd_idx, command in enumerate(commands, 1):
            print(f"\n{'='*60}")
            print(f"Command {cmd_idx}/{len(commands)}: {command}")
            print(f"{'='*60}")
            
            for attempt in range(1, self.max_attempts + 1):
                print(f"\n🔄 Attempt {attempt}/{self.max_attempts}")
                
                success, stdout, stderr = self.execute_command(command)
                
                attempt_data = {
                    "attempt": attempt,
                    "command": command,
                    "success": success,
                    "stdout": stdout[:3000],  # Increased from 500 to 3000
                    "stderr": stderr[:1000]   # Increased from 500 to 1000
                }
                report["attempts"].append(attempt_data)
                
                if success:
                    print(f"✅ Command succeeded!")
                    if stdout:
                        print(f"Output: {stdout[:200]}")
                    break
                else:
                    print(f"❌ Command failed: {stderr[:200]}")
                    
                    if attempt < self.max_attempts:
                        # Analyze error and get fix
                        print(f"\n🔍 Analyzing error...")
                        fix_response = self.analyze_error(command, stderr, attempt)
                        print(f"💡 LLM suggests:\n{fix_response[:300]}")
                        
                        # Extract new command from fix
                        new_commands = self.extract_commands(fix_response)
                        if new_commands:
                            command = new_commands[0]  # Try first suggested fix
                            print(f"\n🔧 Trying alternative: {command}")
                        else:
                            print(f"⚠️  No alternative command found, retrying same command...")
                    else:
                        print(f"\n❌ Max attempts reached for this command")
                        report["final_status"] = "failed"
                        report["summary"] = f"Failed after {self.max_attempts} attempts. Last error: {stderr[:200]}"
                        return report
        
        # All commands succeeded
        report["final_status"] = "success"
        report["summary"] = f"✅ Successfully executed all commands"
        return report
    
    def get_summary(self, report: Dict) -> str:
        """Generate human-readable summary with command outputs"""
        if report["final_status"] == "success":
            summary = f"✅ **Success!** Completed: {report['request']}\n\n"
            
            # Group attempts by command (in case of retries)
            commands_executed = {}
            for attempt in report['attempts']:
                cmd = attempt['command']
                if cmd not in commands_executed or attempt['success']:
                    commands_executed[cmd] = attempt
            
            # Show each command and its output
            for i, (cmd, attempt) in enumerate(commands_executed.items(), 1):
                summary += f"**Command {i}:** `{cmd}`\n\n"
                
                if attempt['stdout']:
                    # Format output in code block
                    output = attempt['stdout'].strip()
                    # Limit output length but show meaningful data
                    if len(output) > 2000:
                        output = output[:2000] + "\n... (output truncated)"
                    summary += f"```\n{output}\n```\n\n"
                else:
                    summary += "*Command executed successfully (no output)*\n\n"
            
            return summary
        else:
            summary = f"❌ **Failed:** {report['request']}\n\n"
            summary += f"**Summary:** {report['summary']}\n\n"
            summary += f"**Attempts made:** {len(report['attempts'])}\n\n"
            
            if report['attempts']:
                last_attempt = report['attempts'][-1]
                summary += f"**Last error:**\n```\n{last_attempt['stderr'][:300]}\n```\n\n"
                summary += "**Suggestion:** The system tried multiple approaches but couldn't complete the task. "
                summary += "You may need to check system permissions or package availability."
            
            return summary
