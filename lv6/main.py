#!/usr/bin/env python3

import json
import os
import sys
import re
import platform
import shlex
import subprocess
from google import genai
from google.genai import types
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored terminal text
init(autoreset=True)

# ASCII art for the application header
CURSOR_HEADER = r"""
     _   _   _     ___                                
    | | | | (_)   |_ _|     __ _   _ __ ___           
    | |_| | | |    | |     / _` | | '_ ` _ \          
    |  _  | | |    | |    | (_| | | | | | | |         
    |_| |_| |_|   |___|    \__,_| |_| |_| |_|         

     ____            _               _                
    |  _ \    __ _  | |__    _   _  | |               
    | |_) |  / _` | | '_ \  | | | | | |               
    |  _ <  | (_| | | | | | | |_| | | |               
    |_| \_\  \__,_| |_| |_|  \__,_| |_|               

     ____    _                                        
    / ___|  | |__     __ _   _ __   _ __ ___     __ _ 
    \___ \  | '_ \   / _` | | '__| | '_ ` _ \   / _` |
     ___) | | | | | | (_| | | |    | | | | | | | (_| |
    |____/  |_| |_|  \__,_| |_|    |_| |_| |_|  \__,_|  

A stepwise, decision-aware developer assistant
"""

class CursorAI:
    def __init__(self, api_key):
        """Initialize the CursorAI with the provided API key."""
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"
        
        # Detect operating system
        self.os_type = platform.system()
        print(f"Detected operating system: {self.os_type}")
        
        # Load system instructions
        script_dir = os.path.dirname(os.path.abspath(__file__))
        sys_inst_path = os.path.join(script_dir, "sys-inst.txt")
        
        try:
            with open(sys_inst_path, "r") as file:
                self.system_instructions = file.read()
        except FileNotFoundError:
            print(Fore.RED + f"Error: System instruction file not found at {sys_inst_path}")
            sys.exit(1)
            
        # Add OS information to system instructions
        self.system_instructions = f"User's Operating System: {self.os_type}\n\n{self.system_instructions}"
            
        # Configure the model
        self.config = types.GenerateContentConfig(
            response_mime_type="application/json",
            system_instruction=[
                types.Part.from_text(text=self.system_instructions),
            ],
        )
    
    def print_welcome(self):
        """Print welcome message and instructions."""
        print(Fore.CYAN + CURSOR_HEADER)
        print(Fore.GREEN + f"Welcome to Cursor AI! Running on {self.os_type}.")
        print(Fore.YELLOW + "Type 'Q' and press Enter to exit the program.")
        print(Fore.CYAN + "Ask me to help with tasks and I'll execute commands for you.\n")
    
    def print_step_response(self, step, content):
        """Format and print a step response with appropriate colors."""
        step_colors = {
            "UNDERSTAND": Fore.BLUE,
            "PLAN": Fore.GREEN,
            "EXECUTE": Fore.MAGENTA, 
            "CMD_EXECUTE": Fore.RED,
            "CMD_RESULT": Fore.WHITE
        }
        
        color = step_colors.get(step, Fore.WHITE)
        print(f"\n{color}[{step}]{Style.RESET_ALL}")
        print(f"{content}\n")
    
    def extract_command(self, execute_content):
        """Extract command from the EXECUTE step content."""
        command_match = re.search(r"```(?:bash|sh)\s*\n(.*?)\n```", execute_content, re.DOTALL)
        if command_match:
            return command_match.group(1).strip()
        return None

    def run_command(self, command):
        """Run a command and return the success status and output."""
        try:
            # For Windows, we need to use shell=True
            use_shell = self.os_type == "Windows"
            
            # Use shlex.split to correctly handle command arguments on Unix systems
            cmd_parts = shlex.split(command) if not use_shell else command
            
            # Run the command and capture output
            result = subprocess.run(
                cmd_parts,
                shell=use_shell,
                capture_output=True,
                text=True,
                check=False  # Don't raise an exception on non-zero exit
            )
            
            # Combine stdout and stderr if there's an error
            output = result.stdout
            if result.returncode != 0 and result.stderr:
                output += f"\nError: {result.stderr}"
                
            return result.returncode == 0, output
        except Exception as e:
            return False, f"Error executing command: {str(e)}"
    
    def process_step(self, user_query, step_name):
        """Process a single step (UNDERSTAND, PLAN, or EXECUTE) with the AI model."""
        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_query,
                config=self.config
            )
            
            # Parse the JSON response
            try:
                parsed_response = json.loads(response.text)
                step = parsed_response.get('step', 'UNKNOWN')
                content = parsed_response.get('content', 'No content provided')
                
                # Check if we got the expected step
                if step != step_name:
                    print(Fore.RED + f"Warning: Expected '{step_name}' step but got '{step}' instead.")
                
                return step, content
                
            except json.JSONDecodeError:
                print(Fore.RED + "Error: Could not parse response as JSON.")
                return "ERROR", f"Failed to parse response: {response.text}"
                
        except Exception as e:
            print(Fore.RED + f"Error connecting to Gemini API: {str(e)}")
            return "ERROR", f"Failed to get a response: {str(e)}"
    
    def run(self):
        """Run the interactive chat loop."""
        self.print_welcome()
        
        while True:
            # Get user input
            user_input = input(Fore.GREEN + "> " + Style.RESET_ALL)
            
            # Check if user wants to exit
            if user_input.strip().upper() == "Q":
                print(Fore.CYAN + "\nThank you for using Cursor AI. Goodbye!")
                break
            
            # Skip empty inputs
            if not user_input.strip():
                continue
            
            # Step 1: UNDERSTAND
            print(Fore.YELLOW + "Processing..." + Style.RESET_ALL)
            step, content = self.process_step(user_input, "UNDERSTAND")
            self.print_step_response(step, content)
            
            # Step 2: PLAN - automatic transition
            step, content = self.process_step(
                f"User input: {user_input}\nPrevious step: {step} with content: {content}\nNow proceed to PLAN.",
                "PLAN"
            )
            self.print_step_response(step, content)
            
            # Step 3: EXECUTE - automatic transition
            step, content = self.process_step(
                f"User input: {user_input}\nPrevious steps: UNDERSTAND, PLAN\nPLAN content: {content}\nNow proceed to EXECUTE.",
                "EXECUTE"
            )
            self.print_step_response(step, content)
            
            # Extract and execute command if present
            command = self.extract_command(content)
            if command:
                self.print_step_response("CMD_EXECUTE", f"execute: {command}")
                success, result = self.run_command(command)
                self.print_step_response("CMD_RESULT", result)
            else:
                print(Fore.YELLOW + "No executable command found in the EXECUTE step.")


if __name__ == "__main__":
    # API key from environment variable or use the one from existing code
    # For simplicity, using the API key from the provided code examples
    api_key = os.environ.get("GOOGLE_API_KEY", "AIzaSyAwoZd3iMs-_wiiopXr3Ys3Jg0exenAkoU")
    
    # Create and run the assistant
    cursor = CursorAI(api_key)
    cursor.run()
