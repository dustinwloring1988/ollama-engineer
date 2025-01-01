#!/usr/bin/env python3

import os
import sys
import json
from pathlib import Path
from textwrap import dedent
from typing import List, Dict, Any, Optional
import requests
from pydantic import BaseModel
import random

# --------------------------------------------------------------------------------
# 1. Configure Ollama client settings
# --------------------------------------------------------------------------------
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "qwen2.5-coder:14b"

# Word lists for random folder names
ADJECTIVES = ['swift', 'bright', 'calm', 'wise', 'bold', 'kind', 'pure', 'warm', 'cool', 'soft']
NOUNS = ['river', 'mountain', 'forest', 'cloud', 'star', 'ocean', 'valley', 'meadow', 'wind', 'sun']
COLORS = ['azure', 'coral', 'jade', 'amber', 'ruby', 'pearl', 'gold', 'silver', 'bronze', 'crystal']

def generate_random_folder_name() -> str:
    """Generate a random 3-word folder name"""
    return f"{random.choice(ADJECTIVES)}_{random.choice(COLORS)}_{random.choice(NOUNS)}"

# Color codes for terminal output
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_color(text: str, color: str = '', end='\n'):
    """Print colored text to terminal"""
    print(f"{color}{text}{Colors.END}", end=end)

# --------------------------------------------------------------------------------
# 2. Define our schema using Pydantic for type safety
# --------------------------------------------------------------------------------
class FileToCreate(BaseModel):
    path: str
    content: str

# NEW: Diff editing structure
class FileToEdit(BaseModel):
    path: str
    original_snippet: str
    new_snippet: str

class AssistantResponse(BaseModel):
    assistant_reply: str
    files_to_create: Optional[List[FileToCreate]] = None
    # NEW: optionally hold diff edits
    files_to_edit: Optional[List[FileToEdit]] = None

# --------------------------------------------------------------------------------
# 3. system prompt
# --------------------------------------------------------------------------------
system_PROMPT = dedent("""\
    You are an elite software engineer called Ollama Engineer with decades of experience across all programming domains.
    Your expertise spans system design, algorithms, testing, and best practices.
    You provide thoughtful, well-structured solutions while explaining your reasoning.

    Core capabilities:
    1. Code Analysis & Discussion
       - Analyze code with expert-level insight
       - Explain complex concepts clearly
       - Suggest optimizations and best practices
       - Debug issues with precision

    2. File Operations:
       a) Read existing files
          - Access user-provided file contents for context
          - Analyze multiple files to understand project structure
       
       b) Create new files
          - Generate complete new files with proper structure
          - Create complementary files (tests, configs, etc.)
       
       c) Edit existing files
          - Make precise changes using diff-based editing
          - Modify specific sections while preserving context
          - Suggest refactoring improvements

    Output Format:
    You must provide responses in this JSON structure:
    {
      "assistant_reply": "Your main explanation or response",
      "files_to_create": [
        {
          "path": "path/to/new/file",
          "content": "complete file content"
        }
      ],
      "files_to_edit": [
        {
          "path": "path/to/existing/file",
          "original_snippet": "exact code to be replaced",
          "new_snippet": "new code to insert"
        }
      ]
    }

    Guidelines:
    1. For normal responses, use 'assistant_reply'
    2. When creating files, include full content in 'files_to_create'
    3. For editing files:
       - Use 'files_to_edit' for precise changes
       - Include enough context in original_snippet to locate the change
       - Ensure new_snippet maintains proper indentation
       - Prefer targeted edits over full file replacements
    4. Always explain your changes and reasoning
    5. Consider edge cases and potential impacts
    6. Follow language-specific best practices
    7. Suggest tests or validation steps when appropriate

    Remember: You're a senior engineer - be thorough, precise, and thoughtful in your solutions.
""")

# --------------------------------------------------------------------------------
# 4. Helper functions 
# --------------------------------------------------------------------------------

def read_local_file(file_path: str) -> str:
    """Return the text content of a local file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def create_file(path: str, content: str):
    """Create (or overwrite) a file at 'path' with the given 'content'."""
    file_path = Path(path)
    
    # If this is a new file (not editing an existing one), place it in the session folder
    if not file_path.exists():
        file_path = Path(session_folder) / file_path.name
    
    file_path.parent.mkdir(parents=True, exist_ok=True)  # ensures any dirs exist
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    print_color(f"[green]✓[/green] Created/updated file at '[cyan]{file_path}[/cyan]'", Colors.GREEN)
    
    # Record the action
    conversation_history.append({
        "role": "assistant",
        "content": f"✓ Created/updated file at '{file_path}'"
    })
    
    # NEW: Add the actual content to conversation context
    normalized_path = normalize_path(str(file_path))
    conversation_history.append({
        "role": "system",
        "content": f"Content of file '{normalized_path}':\n\n{content}"
    })

# NEW: Show the user a table of proposed edits and confirm
def show_diff_table(files_to_edit: List[FileToEdit]) -> None:
    """Display a simple ASCII table showing the proposed edits."""
    if not files_to_edit:
        return
    
    print_color("\nProposed Edits:", Colors.BOLD + Colors.BLUE)
    print("-" * 80)
    
    for edit in files_to_edit:
        print_color(f"File: {edit.path}", Colors.CYAN)
        print_color("Original:", Colors.RED)
        print(edit.original_snippet)
        print_color("New:", Colors.GREEN)
        print(edit.new_snippet)
        print("-" * 80)

# NEW: Apply diff edits
def apply_diff_edit(path: str, original_snippet: str, new_snippet: str):
    """Reads the file at 'path', replaces the first occurrence of 'original_snippet' with 'new_snippet', then overwrites."""
    try:
        content = read_local_file(path)
        if original_snippet in content:
            updated_content = content.replace(original_snippet, new_snippet, 1)
            create_file(path, updated_content)  # This will now also update conversation context
            print_color(f"✓ Applied diff edit to '{path}'", Colors.GREEN)
            conversation_history.append({
                "role": "assistant",
                "content": f"✓ Applied diff edit to '{path}'"
            })
        else:
            # Show mismatch info
            print_color(f"⚠ Original snippet not found in '{path}'. No changes made.", Colors.YELLOW)
            print_color("\nExpected snippet:", Colors.YELLOW)
            print(original_snippet)
            print_color("\nActual file content:", Colors.YELLOW)
            print(content)
    except FileNotFoundError:
        print_color(f"✗ File not found for diff editing: '{path}'", Colors.RED)

def try_handle_add_command(user_input: str) -> bool:
    """
    If user_input starts with '/add ', read that file and insert its content
    into conversation as a system message. Returns True if handled; else False.
    """
    prefix = "/add "
    if user_input.strip().lower().startswith(prefix):
        file_path = user_input[len(prefix):].strip()
        try:
            content = read_local_file(file_path)
            conversation_history.append({
                "role": "system",
                "content": f"Content of file '{file_path}':\n\n{content}"
            })
            print_color(f"[green]✓[/green] Added file '[cyan]{file_path}[/cyan]' to conversation.\n", Colors.GREEN)
        except OSError as e:
            print_color(f"[red]✗[/red] Could not add file '[cyan]{file_path}[/cyan]': {e}\n", Colors.RED)
        return True
    return False

def ensure_file_in_context(file_path: str) -> bool:
    """
    Ensures the file content is in the conversation context.
    Returns True if successful, False if file not found.
    """
    try:
        normalized_path = normalize_path(file_path)
        content = read_local_file(normalized_path)
        file_marker = f"Content of file '{normalized_path}'"
        if not any(file_marker in msg["content"] for msg in conversation_history):
            conversation_history.append({
                "role": "system",
                "content": f"{file_marker}:\n\n{content}"
            })
        return True
    except OSError:
        print_color(f"[red]✗[/red] Could not read file '[cyan]{file_path}[/cyan]' for editing context", Colors.RED)
        return False

def normalize_path(path_str: str) -> str:
    """Return a canonical, absolute version of the path."""
    return str(Path(path_str).resolve())

# --------------------------------------------------------------------------------
# 5. Conversation state
# --------------------------------------------------------------------------------
conversation_history = [
    {"role": "system", "content": system_PROMPT}
]

# Session folder for file organization
session_folder = generate_random_folder_name()
print_color(f"\nSession files will be saved in: {session_folder}/", Colors.CYAN)

# --------------------------------------------------------------------------------
# 6. OpenAI API interaction with streaming
# --------------------------------------------------------------------------------

def guess_files_in_message(user_message: str) -> List[str]:
    """
    Attempt to guess which files the user might be referencing.
    Returns normalized absolute paths.
    """
    recognized_extensions = [".css", ".html", ".js", ".py", ".json", ".md"]
    potential_paths = []
    for word in user_message.split():
        if any(ext in word for ext in recognized_extensions) or "/" in word:
            path = word.strip("',\"")
            try:
                normalized_path = normalize_path(path)
                potential_paths.append(normalized_path)
            except (OSError, ValueError):
                continue
    return potential_paths

def stream_openai_response(user_message: str):
    """
    Streams the Ollama chat completion response and handles structured output.
    Returns the final AssistantResponse.
    """
    # Attempt to guess which file(s) user references
    potential_paths = guess_files_in_message(user_message)
    
    valid_files = {}

    # Try to read all potential files before the API call
    for path in potential_paths:
        try:
            content = read_local_file(path)
            valid_files[path] = content  # path is already normalized
            file_marker = f"Content of file '{path}'"
            # Add to conversation if we haven't already
            if not any(file_marker in msg["content"] for msg in conversation_history):
                conversation_history.append({
                    "role": "system",
                    "content": f"{file_marker}:\n\n{content}"
                })
        except OSError:
            error_msg = f"Cannot proceed: File '{path}' does not exist or is not accessible"
            print_color(f"[red]✗[/red] {error_msg}", Colors.RED)
            continue

    # Now proceed with the API call
    conversation_history.append({"role": "user", "content": user_message})

    try:
        # Prepare the request payload for Ollama
        payload = {
            "model": MODEL_NAME,
            "messages": conversation_history,
            "stream": True,
            "format": "json"  # Request JSON output
        }

        # Make streaming request to Ollama
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            json=payload,
            stream=True
        )
        response.raise_for_status()

        print_color("\nAssistant> ", Colors.BOLD + Colors.BLUE, end="")
        full_content = ""

        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                if "message" in chunk and "content" in chunk["message"]:
                    content_chunk = chunk["message"]["content"]
                    full_content += content_chunk
                    print_color(content_chunk, end="")

        print_color("\n")

        try:
            # Try to parse the full response as JSON
            parsed_response = json.loads(full_content)
            
            # [NEW] Ensure assistant_reply is present
            if "assistant_reply" not in parsed_response:
                parsed_response["assistant_reply"] = ""

            # If assistant tries to edit files not in valid_files, remove them
            if "files_to_edit" in parsed_response and parsed_response["files_to_edit"]:
                new_files_to_edit = []
                for edit in parsed_response["files_to_edit"]:
                    try:
                        edit_abs_path = normalize_path(edit["path"])
                        # If we have the file in context or can read it now
                        if edit_abs_path in valid_files or ensure_file_in_context(edit_abs_path):
                            edit["path"] = edit_abs_path  # Use normalized path
                            new_files_to_edit.append(edit)
                    except (OSError, ValueError):
                        print_color(f"[yellow]⚠[/yellow] Skipping invalid path: '{edit['path']}'", Colors.YELLOW)
                        continue
                parsed_response["files_to_edit"] = new_files_to_edit

            response_obj = AssistantResponse(**parsed_response)

            # Save the assistant's textual reply to conversation
            conversation_history.append({
                "role": "assistant",
                "content": response_obj.assistant_reply
            })

            return response_obj

        except json.JSONDecodeError:
            error_msg = "Failed to parse JSON response from assistant"
            print_color(f"[red]✗[/red] {error_msg}", Colors.RED)
            return AssistantResponse(
                assistant_reply=error_msg,
                files_to_create=[]
            )

    except Exception as e:
        error_msg = f"Ollama API error: {str(e)}"
        print_color(f"\n[red]✗[/red] {error_msg}", Colors.RED)
        return AssistantResponse(
            assistant_reply=error_msg,
            files_to_create=[]
        )

# --------------------------------------------------------------------------------
# 7. Main interactive loop
# --------------------------------------------------------------------------------

def main():
    print_color("\n🤖 Welcome to Ollama Engineer! 🚀", Colors.BOLD + Colors.BLUE)
    print_color("Your AI Pair Programming Assistant", Colors.CYAN)
    print_color("=" * 60)
    print_color("\n📝 Quick Guide:", Colors.BOLD + Colors.GREEN)
    print_color("• Ask me anything about coding, debugging, or software design", Colors.GREEN)
    print_color("• Use '/add path/to/file' to share code files with me", Colors.GREEN)
    print_color("• I can create new files and suggest code improvements", Colors.GREEN)
    print_color("• All new files will be organized in random-named folders", Colors.GREEN)
    print_color("\n⌨️  Commands:", Colors.BOLD + Colors.YELLOW)
    print_color("• /add path/to/file - Add a file to our conversation", Colors.YELLOW)
    print_color("• exit or quit - End the session", Colors.YELLOW)
    print_color("\nReady to help with your coding tasks! 💻\n", Colors.BOLD + Colors.BLUE)

    while True:
        try:
            print_color("You> ", Colors.BOLD + Colors.GREEN, end="")
            user_input = input().strip()
        except (EOFError, KeyboardInterrupt):
            print_color("\nExiting.", Colors.YELLOW)
            break

        if not user_input:
            continue

        if user_input.lower() in ["exit", "quit"]:
            print_color("Goodbye!", Colors.YELLOW)
            break

        # If user is reading a file
        if try_handle_add_command(user_input):
            continue

        # Get streaming response from Ollama
        response_data = stream_openai_response(user_input)

        # Create any files if requested
        if response_data.files_to_create:
            for file_info in response_data.files_to_create:
                create_file(file_info.path, file_info.content)

        # Show and confirm diff edits if requested
        if response_data.files_to_edit:
            show_diff_table(response_data.files_to_edit)
            print_color("\nDo you want to apply these changes? (y/n): ", Colors.BOLD, end="")
            confirm = input().strip().lower()
            if confirm == 'y':
                for edit_info in response_data.files_to_edit:
                    apply_diff_edit(edit_info.path, edit_info.original_snippet, edit_info.new_snippet)
            else:
                print_color("ℹ Skipped applying diff edits.", Colors.YELLOW)

    print_color("Session finished.", Colors.BLUE)

if __name__ == "__main__":
    main()
