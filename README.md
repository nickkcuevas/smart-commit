# Smart Commit Tool

A Python CLI tool that automatically generates descriptive commit messages by analyzing staged git changes using OpenAI's API.

## Features

- 🔍 Analyzes staged git changes (files, additions, deletions)
- 🤖 Uses OpenAI or Groq (free!) to generate conventional commit messages
- 📝 Multi-line commit messages with title and body
- 🎨 Beautiful terminal UI with rich formatting
- ✏️ Interactive preview and editing
- ⚙️ Configurable via environment variables or config file
- 💰 Supports free Groq API (no credit card required!)

## Installation

### Option 1: Install as a command (Recommended)

Install the tool so you can run it from anywhere:

```bash
# From the project directory
pip install -e .

# Now you can use it from anywhere (Groq is the default):
smart-commit
# or explicitly: smart-commit --provider groq
```

### Option 2: Simple executable (No installation)

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make the script executable (if not already):
```bash
chmod +x smart_commit.py
```

3. Run it directly (Groq is now the default):
```bash
./smart_commit.py
# or explicitly: ./smart_commit.py --provider groq
```

### Option 3: Create an alias (Quick access)

Add to your `~/.zshrc` or `~/.bashrc`:

```bash
# For zsh
alias smart-commit='/path/to/hackaton/smart_commit.py'

# Or if using virtual environment:
alias smart-commit='source /path/to/hackaton/venv/bin/activate && /path/to/hackaton/smart_commit.py'
```

Then reload your shell:
```bash
source ~/.zshrc  # or source ~/.bashrc
```

Now you can use:
```bash
smart-commit --provider groq
```

### Set up your API key (choose one):

**Option A: Groq (FREE, default provider)**
```bash
# Get free API key at: https://console.groq.com/keys
export GROQ_API_KEY='your-groq-key-here'
```

**Option B: OpenAI (paid, use --provider openai)**
```bash
export OPENAI_API_KEY='your-openai-key-here'
# Then use: smart-commit --provider openai
```

Or create a config file at `~/.smart_commit_config` or `.smart_commit_config`:
```json
{
  "provider": "groq",
  "groq_api_key": "your-groq-key-here",
  "model": "llama-3.1-8b-instant"
}
```

## Usage

### Basic Usage

1. Stage your changes:
```bash
git add .
```

2. Run smart-commit:
```bash
# If installed as command:
smart-commit

# Or if using directly:
python smart_commit.py
# or
./smart_commit.py
```

3. Review the generated message and choose to:
   - `c` - Commit with the generated message
   - `e` - Edit the message
   - `r` - Regenerate the message
   - `q` - Quit without committing

### Command Line Options

```bash
smart-commit [OPTIONS]
# or
python smart_commit.py [OPTIONS]

Options:
  --model TEXT        Model to use (default depends on provider)
  --provider TEXT     API provider: openai or groq (default: groq)
  --auto-commit       Automatically commit without confirmation
  --no-preview        Skip preview and commit directly
  --help              Show this message and exit
```

### Examples

```bash
# Use Groq (default, FREE!)
smart-commit
# or explicitly: smart-commit --provider groq

# Use a specific Groq model
smart-commit --model llama-3.1-70b-versatile

# Use OpenAI instead
smart-commit --provider openai --model gpt-3.5-turbo

# Auto-commit without confirmation
smart-commit --auto-commit

# Skip preview
smart-commit --no-preview
```

## Configuration

### Environment Variable (Recommended)

**For Groq (FREE):**
```bash
export GROQ_API_KEY='gsk_...'
```

**For OpenAI:**
```bash
export OPENAI_API_KEY='sk-...'
```

### Config File

Create `~/.smart_commit_config` (user-level) or `.smart_commit_config` (project-level):

**For Groq:**
```json
{
  "provider": "groq",
  "groq_api_key": "gsk_...",
  "model": "llama-3.1-8b-instant"
}

**For OpenAI (if you want to use OpenAI instead of Groq):**
```json
{
  "provider": "openai",
  "api_key": "sk-...",
  "model": "gpt-4"
}
```

**Note:** Project-level config takes precedence over user-level config. Environment variables take precedence over config files.

### Free Groq Models

Groq offers free API access with these models:
- `llama-3.1-8b-instant` - Fast, good for commits (default)
- `llama-3.1-70b-versatile` - More capable, slightly slower
- `llama-3.3-70b-versatile` - Latest, most capable
- `mixtral-8x7b-32768` - Good balance
- `gemma-7b-it` - Alternative option

**Note:** Older model names like `llama3-8b-8192` have been decommissioned. The tool will automatically map them to current models.

Get your free API key at: https://console.groq.com/keys

## Requirements

- Python 3.7+
- Git repository
- OpenAI API key

## Dependencies

- `openai` - OpenAI API client
- `click` - CLI framework
- `rich` - Terminal formatting
- `GitPython` - Git operations

## How It Works

1. Analyzes staged git changes using `git diff --staged`
2. Extracts file paths, change statistics, and file types
3. Builds a context-rich prompt with diff snippets
4. Sends prompt to OpenAI API
5. Generates a conventional commit message
6. Shows preview and allows editing/regeneration
7. Creates the commit with the final message

## Commit Message Format

The tool generates commit messages following the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>: <description>

[optional body]

[optional footer]
```

Types include: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`, `perf`

## Troubleshooting

### "OPENAI_API_KEY not set"
Set the API key via environment variable or config file (see Configuration section).

### "Not a git repository"
Run the command from within a git repository directory.

### "No staged changes found"
Stage some files first with `git add`.

### Rate limit errors
OpenAI API has rate limits. Wait a moment and try again, or use a different API key.

## License

MIT

