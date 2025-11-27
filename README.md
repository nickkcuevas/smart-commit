# Smart Commit Tool

A Python CLI tool that automatically generates descriptive commit messages by analyzing staged git changes using OpenAI's API.

## Features

- 🔍 Analyzes staged git changes (files, additions, deletions)
- 🤖 Uses OpenAI to generate conventional commit messages
- 📝 Multi-line commit messages with title and body
- 🎨 Beautiful terminal UI with rich formatting
- ✏️ Interactive preview and editing
- ⚙️ Configurable via environment variables or config file

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up your OpenAI API key:
```bash
export OPENAI_API_KEY='your-api-key-here'
```

Or create a config file at `~/.smart_commit_config` or `.smart_commit_config`:
```json
{
  "api_key": "your-api-key-here",
  "model": "gpt-4"
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
python smart_commit.py
```

3. Review the generated message and choose to:
   - `c` - Commit with the generated message
   - `e` - Edit the message
   - `r` - Regenerate the message
   - `q` - Quit without committing

### Command Line Options

```bash
python smart_commit.py [OPTIONS]

Options:
  --model TEXT        OpenAI model to use (default: gpt-4)
  --auto-commit       Automatically commit without confirmation
  --no-preview        Skip preview and commit directly
  --help              Show this message and exit
```

### Examples

```bash
# Use a different model
python smart_commit.py --model gpt-3.5-turbo

# Auto-commit without confirmation
python smart_commit.py --auto-commit

# Skip preview
python smart_commit.py --no-preview
```

## Configuration

### Environment Variable (Recommended)

```bash
export OPENAI_API_KEY='sk-...'
```

### Config File

Create `~/.smart_commit_config` (user-level) or `.smart_commit_config` (project-level):

```json
{
  "api_key": "sk-...",
  "model": "gpt-4"
}
```

**Note:** Project-level config takes precedence over user-level config. Environment variables take precedence over config files.

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

