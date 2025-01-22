# AI Terminal

A Python-based terminal emulator with AI command interpretation capabilities. This terminal allows you to use natural language to execute terminal commands.

## Features

- Modern dark theme GUI interface
- Natural language command interpretation using OpenAI's GPT-3.5
- Toggle between AI and regular command mode
- Support for all standard terminal commands
- Color-coded output for better readability
- Scrollable command history

## Setup

1. Install the required packages:
```bash
pip install -r requirements.txt
```

2. Configure your OpenAI API key:
- Open `config.py`
- Replace `your_api_key_here` with your actual OpenAI API key

## Usage

Run the terminal:
```bash
python main.py
```

### Example Commands

With AI mode enabled (default), you can use natural language:
- "list the files in this directory" → `ls`
- "show me where I am" → `pwd`
- "go to parent directory" → `cd ..`
- "what's the current date" → `date`

You can also use regular terminal commands directly:
- `ls`
- `pwd`
- `cd`
- `clear`

### Controls

- Toggle AI mode using the checkbox in the bottom-left corner
- Press Enter to execute commands
- Type 'exit' or close the window to quit

## Requirements

- Python 3.x
- tkinter
- OpenAI API key
