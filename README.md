# Ollama Engineer 🚀

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

![image](https://github.com/user-attachments/assets/cc1b3a1b-8a98-49cf-af26-d3c4606d0779)

## Overview

This repository contains a powerful coding assistant application that integrates with Ollama to process user conversations and generate structured JSON responses. Through a simple command-line interface, it can read local file contents, create new files, and apply diff edits to existing files in real time. While making this fork of DeepSeek Engineer our goal was to reduce the dependences and to be able to use any self hosted model while not adding more code then nessary to achive this result.

## Requirements

- Python 3.8 or higher
- Ollama installed and running locally
- Available disk space for the Ollama model (~8GB)

## Key Features

1. Ollama Integration
   - Uses local Ollama instance with the qwen2.5-coder:14b model
   - Streams responses for real-time interaction
   - Structured JSON output for precise code modifications

2. Data Models
   - Leverages Pydantic for type-safe handling of file operations, including:
     • FileToCreate – describes files to be created or updated
     • FileToEdit – describes specific snippet replacements in an existing file
     • AssistantResponse – structures chat responses and potential file operations

3. System Prompt
   - A comprehensive system prompt guides conversation, ensuring all replies strictly adhere to JSON output with optional file creations or edits

4. Helper Functions
   - read_local_file: Reads a target filesystem path and returns its content as a string
   - create_file: Creates or overwrites a file with provided content
   - show_diff_table: Presents proposed file changes in a clear, readable format
   - apply_diff_edit: Applies snippet-level modifications to existing files

5. "/add" Command
   - Users can type "/add path/to/file" to quickly read a file's content and insert it into the conversation as a system message
   - This allows the assistant to reference the file contents for further discussion, code generation, or diff proposals

6. Conversation Flow
   - Maintains a conversation_history list to track messages between user and assistant
   - Streams the assistant's replies via Ollama, parsing them as JSON to preserve both the textual response and the instructions for file modifications

7. Interactive Session
   - Run the script (for example: "python3 main.py") to start an interactive loop at your terminal
   - Enter your requests or code questions. Enter "/add path/to/file" to add file contents to the conversation
   - When the assistant suggests new or edited files, you can confirm changes directly in your local environment
   - Type "exit" or "quit" to end the session

## Prerequisites

1. Install Ollama from https://ollama.ai
2. Pull the qwen2.5-coder model:
   ```bash
   ollama pull qwen2.5-coder:14b
   ```

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/dustinwloring1988/ollama-engineer.git
   cd ollama-engineer
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Start Ollama server (if not already running)

4. Run the application:
   ```bash
   python main.py
   ```

5. Enjoy multi-line streaming responses, file read-ins with "/add path/to/file", and precise file edits when approved.


## Development Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install pre-commit hooks (optional):
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Project Structure

```
ollama-engineer/
├── main.py           # Main application file
├── requirements.txt  # Project dependencies
├── README.md        # Project documentation
└── .gitignore       # Git ignore rules
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Troubleshooting

1. **Ollama Connection Issues**
   - Ensure Ollama is running (`ollama serve`)
   - Check if the default port (11434) is available
   - Verify your firewall settings

2. **Model Issues**
   - Try re-pulling the model: `ollama pull qwen2.5-coder:14b`
   - Check Ollama logs for any errors

3. **Python Environment Issues**
   - Ensure you're using Python 3.8+
   - Try recreating your virtual environment
   - Verify all dependencies are installed

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Original DeepSeek Engineer project for inspiration
- Ollama team for providing local LLM capabilities
- QWen team for the excellent code-focused model

> **Note**: This is a modified version of the original DeepSeek Engineer project, adapted to work with Ollama and the qwen2.5-coder model locally. It provides similar capabilities without requiring API keys or external services.
