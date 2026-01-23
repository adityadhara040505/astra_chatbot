#!/usr/bin/env python3
"""
Quick test of command extraction
"""
from command_executor import CommandExecutor

# Test the extract_commands function
test_responses = [
    # Format 1: With $ prefix
    """$ sudo apt update
$ sudo apt install -y code""",
    
    # Format 2: Without prefix
    """sudo apt update
sudo apt install -y code""",
    
    # Format 3: In code block
    """```bash
sudo apt update
sudo apt install -y code
```""",
    
    # Format 4: Numbered list
    """1. sudo apt update
2. sudo apt install -y code""",
    
    # Format 5: Mixed with explanation
    """To install VS Code, run these commands:

sudo apt update
sudo apt install -y code

This will install Visual Studio Code."""
]

print("Testing command extraction...\n")

# Create a mock executor (without PDF for testing)
class MockExecutor:
    def extract_commands(self, text):
        # Copy the extract_commands logic
        commands = []
        lines = text.split('\n')
        in_code_block = False
        
        command_prefixes = [
            'sudo', 'apt', 'apt-get', 'dpkg', 'snap', 'systemctl', 
            'wget', 'curl', 'git', 'pip', 'python', 'bash', 'sh',
            'chmod', 'chown', 'mkdir', 'rm', 'cp', 'mv', 'ln',
            'echo', 'cat', 'grep', 'find', 'sed', 'awk',
            'tar', 'gzip', 'unzip', 'service', 'update-alternatives',
            'add-apt-repository', 'gpg', 'install', 'flatpak'
        ]
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            if line.startswith('```'):
                in_code_block = not in_code_block
                continue
            
            if in_code_block:
                if line.startswith('$ '):
                    commands.append(line[2:].strip())
                elif line.startswith('# ') and not line.startswith('##'):
                    continue
                else:
                    first_word = line.split()[0] if line.split() else ''
                    if first_word in command_prefixes:
                        commands.append(line)
                continue
            
            if line.startswith('$ '):
                commands.append(line[2:].strip())
            elif line.startswith('$'):
                commands.append(line[1:].strip())
            elif any(line.startswith(prefix + ' ') or line == prefix for prefix in command_prefixes):
                commands.append(line)
            elif line[0].isdigit() and '. ' in line:
                cmd_part = line.split('. ', 1)[1].strip()
                if any(cmd_part.startswith(prefix + ' ') for prefix in command_prefixes):
                    commands.append(cmd_part)
        
        return commands

executor = MockExecutor()

for i, response in enumerate(test_responses, 1):
    print(f"Test {i}:")
    print(f"Input:\n{response}\n")
    commands = executor.extract_commands(response)
    print(f"Extracted {len(commands)} commands:")
    for cmd in commands:
        print(f"  - {cmd}")
    print("\n" + "="*60 + "\n")

print("✅ All tests completed!")
