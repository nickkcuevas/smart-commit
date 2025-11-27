#!/usr/bin/env python3
"""
Smart Commit Tool - Auto-generates descriptive commit messages using OpenAI
"""
import os
import sys
import subprocess
import json
from typing import Dict, List, Optional, Tuple
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.text import Text
import git
from openai import OpenAI

console = Console()

CONFIG_FILE = Path.home() / ".smart_commit_config"
PROJECT_CONFIG_FILE = Path(".smart_commit_config")


class GitAnalyzer:
    """Analyzes staged git changes"""
    
    def __init__(self, repo_path: Optional[str] = None):
        try:
            self.repo = git.Repo(repo_path or ".")
        except git.InvalidGitRepositoryError:
            console.print("[red]Error: Not a git repository. Run this command from a git repository directory.[/red]")
            sys.exit(1)
        except git.exc.GitCommandError as e:
            console.print(f"[red]Error accessing git repository: {e}[/red]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]Unexpected error initializing git repository: {e}[/red]")
            sys.exit(1)
    
    def get_staged_changes(self) -> Dict:
        """Get all staged changes with statistics"""
        staged_files = []
        total_additions = 0
        total_deletions = 0
        processed_paths = set()
        
        # Use git diff --cached to get all staged files (more reliable)
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', '--name-status'],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            staged_changes = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        except Exception:
            staged_changes = []
        
        # Check if this is a fresh repository with no commits
        try:
            head_commit = self.repo.head.commit
            has_commits = True
        except (ValueError, git.BadName):
            # No commits yet, all files in index are new
            has_commits = False
            head_commit = None
        
        # Process staged changes from git diff --cached
        for change_line in staged_changes:
            if not change_line:
                continue
            
            # Parse git diff --cached output: status\tfile_path
            parts = change_line.split('\t', 1)
            if len(parts) != 2:
                continue
            
            status = parts[0]
            file_path = parts[1]
            
            if file_path in processed_paths:
                continue
            processed_paths.add(file_path)
            
            # Determine change type from status
            if status.startswith('A'):
                change_type = "added"
            elif status.startswith('D'):
                change_type = "deleted"
            elif status.startswith('R') or status.startswith('C'):
                change_type = "renamed"
            else:
                change_type = "modified"
            
            # Get diff stats using git diff --cached
            try:
                stats_result = subprocess.run(
                    ['git', 'diff', '--cached', '--numstat', file_path],
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=10
                )
                # Format: additions\tdeletions\tfile
                stats_line = stats_result.stdout.strip()
                if stats_line:
                    stats_parts = stats_line.split('\t')
                    if len(stats_parts) >= 2:
                        try:
                            additions = int(stats_parts[0]) if stats_parts[0] != '-' else 0
                            deletions = int(stats_parts[1]) if stats_parts[1] != '-' else 0
                        except ValueError:
                            additions, deletions = self._count_changes_from_diff(file_path)
                    else:
                        additions, deletions = self._count_changes_from_diff(file_path)
                else:
                    additions, deletions = self._count_changes_from_diff(file_path)
            except Exception:
                additions, deletions = self._count_changes_from_diff(file_path)
            
            total_additions += additions
            total_deletions += deletions
            
            # Get file type
            file_type = self._categorize_file(file_path)
            
            # Get diff content (truncated)
            diff_content = self._get_diff_content(file_path)
            
            staged_files.append({
                "path": file_path,
                "type": change_type,
                "file_type": file_type,
                "additions": additions,
                "deletions": deletions,
                "diff": diff_content
            })
        
        # Fallback: if no changes found via git diff --cached, try GitPython
        if not staged_files and has_commits:
            try:
                for item in self.repo.index.diff("HEAD"):
                    file_path = item.a_path if item.a_path else item.b_path
                    if file_path in processed_paths:
                        continue
                    processed_paths.add(file_path)
                    
                    change_type = self._get_change_type(item)
                    
                    # Get diff stats
                    diff_index = self.repo.index.diff("HEAD", paths=[file_path])
                    additions, deletions = self._count_changes(diff_index)
                    total_additions += additions
                    total_deletions += deletions
                    
                    # Get file type
                    file_type = self._categorize_file(file_path)
                    
                    # Get diff content (truncated)
                    diff_content = self._get_diff_content(file_path)
                    
                    staged_files.append({
                        "path": file_path,
                        "type": change_type,
                        "file_type": file_type,
                        "additions": additions,
                        "deletions": deletions,
                        "diff": diff_content
                    })
            except Exception:
                pass
        
        # Check for new files in staging area
        # For fresh repos, all files in index are new
        # For existing repos, compare index to HEAD
        if not has_commits:
            # Fresh repository - all files in index are new
            # Use git command to get staged files
            try:
                result = subprocess.run(
                    ['git', 'diff', '--cached', '--name-only'],
                    capture_output=True,
                    text=True,
                    check=True
                )
                staged_file_paths = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            except:
                # Fallback: try to get from index entries
                try:
                    staged_file_paths = list(self.repo.index.entries.keys())
                except:
                    staged_file_paths = []
            
            for file_path in staged_file_paths:
                # Ensure file_path is a string
                if isinstance(file_path, tuple):
                    file_path = file_path[0] if file_path else ""
                if not file_path or file_path in processed_paths:
                    continue
                processed_paths.add(file_path)
                
                # Count lines in new file
                try:
                    blob = self.repo.index[file_path]
                    # Get actual content
                    try:
                        content = blob.data_stream.read().decode('utf-8', errors='ignore')
                        additions = len([l for l in content.split('\n') if l.strip()])
                    except:
                        # Fallback estimate
                        additions = blob.size // 80 if blob.size > 0 else 0
                except:
                    # Fallback: read from filesystem
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            additions = len(f.readlines())
                    except:
                        additions = 0
                
                total_additions += additions
                file_type = self._categorize_file(file_path)
                
                staged_files.append({
                    "path": file_path,
                    "type": "added",
                    "file_type": file_type,
                    "additions": additions,
                    "deletions": 0,
                    "diff": self._get_new_file_diff(file_path)
                })
        else:
            # Existing repository - check for new files by comparing index to HEAD
            try:
                for item in self.repo.index.diff(head_commit):
                    if hasattr(item, 'new_file') and item.new_file:
                        file_path = item.a_path
                        if file_path in processed_paths:
                            continue
                        processed_paths.add(file_path)
                        
                        # Count lines in new file
                        try:
                            blob = self.repo.index[file_path]
                            # Get actual content
                            try:
                                content = blob.data_stream.read().decode('utf-8', errors='ignore')
                                additions = len([l for l in content.split('\n') if l.strip()])
                            except:
                                # Fallback estimate
                                additions = blob.size // 80 if blob.size > 0 else 0
                        except:
                            # Fallback: read from filesystem
                            try:
                                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                    additions = len(f.readlines())
                            except:
                                additions = 0
                        
                        total_additions += additions
                        file_type = self._categorize_file(file_path)
                        
                        staged_files.append({
                            "path": file_path,
                            "type": "added",
                            "file_type": file_type,
                            "additions": additions,
                            "deletions": 0,
                            "diff": self._get_new_file_diff(file_path)
                        })
            except Exception:
                pass
        
        return {
            "files": staged_files,
            "total_additions": total_additions,
            "total_deletions": total_deletions,
            "file_count": len(staged_files)
        }
    
    def _get_change_type(self, item) -> str:
        """Determine change type from git diff item"""
        if item.new_file:
            return "added"
        elif item.deleted_file:
            return "deleted"
        elif item.renamed_file:
            return "renamed"
        else:
            return "modified"
    
    def _count_changes(self, diff_index) -> Tuple[int, int]:
        """Count additions and deletions from diff"""
        additions = 0
        deletions = 0
        
        for diff in diff_index:
            diff_text = diff.diff.decode('utf-8', errors='ignore')
            for line in diff_text.split('\n'):
                if line.startswith('+') and not line.startswith('+++'):
                    additions += 1
                elif line.startswith('-') and not line.startswith('---'):
                    deletions += 1
        
        return additions, deletions
    
    def _count_changes_from_diff(self, file_path: str) -> Tuple[int, int]:
        """Count additions and deletions from git diff --cached for a file"""
        try:
            result = subprocess.run(
                ['git', 'diff', '--cached', file_path],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            additions = 0
            deletions = 0
            for line in result.stdout.split('\n'):
                if line.startswith('+') and not line.startswith('+++'):
                    additions += 1
                elif line.startswith('-') and not line.startswith('---'):
                    deletions += 1
            return additions, deletions
        except Exception:
            return 0, 0
    
    def _categorize_file(self, file_path: str) -> str:
        """Categorize file by type"""
        path_lower = file_path.lower()
        
        if path_lower.endswith('.py'):
            if 'migration' in path_lower or 'migrations' in path_lower:
                return "migration"
            elif 'test' in path_lower or 'tests' in path_lower:
                return "test"
            elif 'model' in path_lower or 'models' in path_lower:
                return "model"
            elif 'api' in path_lower:
                return "api"
            elif 'config' in path_lower or 'settings' in path_lower:
                return "config"
            else:
                return "python"
        elif path_lower.endswith(('.js', '.jsx', '.ts', '.tsx')):
            return "javascript"
        elif path_lower.endswith(('.json', '.yaml', '.yml')):
            return "config"
        elif path_lower.endswith(('.md', '.txt', '.rst')):
            return "documentation"
        elif 'dockerfile' in path_lower or 'docker-compose' in path_lower:
            return "docker"
        elif 'requirements' in path_lower or 'setup.py' in path_lower or 'pyproject.toml' in path_lower:
            return "dependencies"
        else:
            return "other"
    
    def _get_diff_content(self, file_path: str, max_lines: int = 100) -> str:
        """Get diff content for a file, truncated if too large"""
        try:
            result = subprocess.run(
                ['git', 'diff', '--staged', file_path],
                capture_output=True,
                text=True,
                check=True,
                timeout=10
            )
            if not result.stdout:
                return ""
            diff_lines = result.stdout.split('\n')
            if len(diff_lines) > max_lines:
                return '\n'.join(diff_lines[:max_lines]) + f"\n... (truncated, showing first {max_lines} lines)"
            return result.stdout
        except subprocess.TimeoutExpired:
            return f"# Timeout reading diff for {file_path}"
        except subprocess.CalledProcessError:
            return ""
        except Exception:
            return ""
    
    def _get_new_file_diff(self, file_path: str, max_lines: int = 100) -> str:
        """Get diff content for a new file"""
        try:
            # Try to read from git index first
            try:
                blob = self.repo.index[file_path]
                content = blob.data_stream.read().decode('utf-8', errors='ignore')
            except (KeyError, AttributeError):
                # Fallback to filesystem
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            
            lines = content.split('\n')
            if len(lines) > max_lines:
                content = '\n'.join(lines[:max_lines]) + f"\n... (truncated, showing first {max_lines} lines)"
            return f"+++ {file_path}\n{content}"
        except FileNotFoundError:
            return f"+++ {file_path}\n# File not found"
        except PermissionError:
            return f"+++ {file_path}\n# Permission denied"
        except Exception:
            return f"+++ {file_path}\n# Error reading file"
    
    def has_staged_changes(self) -> bool:
        """Check if there are any staged changes"""
        try:
            # Check if there are any files in the index
            if len(self.repo.index.entries) == 0:
                return False
            
            # Check if this is a fresh repository with no commits
            try:
                head_commit = self.repo.head.commit
                has_commits = True
            except (ValueError, git.BadName):
                # No commits yet, if index has files, they're staged
                return len(self.repo.index.entries) > 0
            
            # For repos with commits, check for differences
            try:
                # Check for staged changes against HEAD
                if len(self.repo.index.diff("HEAD")) > 0:
                    return True
                
                # Check for new files by comparing index to HEAD
                for item in self.repo.index.diff(head_commit):
                    if hasattr(item, 'new_file') and item.new_file:
                        return True
            except Exception:
                # If diff fails, check if index has entries
                return len(self.repo.index.entries) > 0
            
            return False
        except Exception:
            return False


def load_config() -> Dict:
    """Load configuration from file or return empty dict"""
    config = {}
    
    # Try project-level config first, then user-level
    for config_path in [PROJECT_CONFIG_FILE, CONFIG_FILE]:
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                break
            except json.JSONDecodeError:
                console.print(f"[yellow]Warning: Invalid JSON in {config_path}[/yellow]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not read config file {config_path}: {e}[/yellow]")
    
    return config


class CommitMessageGenerator:
    """Generates commit messages using OpenAI or Groq"""
    
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, provider: str = "openai"):
        config = load_config()
        
        self.provider = provider or config.get("provider", "openai")
        
        # Priority: explicit parameter > env var > config file
        if self.provider == "groq":
            api_key = api_key or os.getenv("GROQ_API_KEY") or config.get("groq_api_key")
            # Use newer model names - these are currently available
            default_model = "llama-3.1-8b-instant"  # Current default
            # Groq models - current available models (as of 2024)
            groq_models = ["llama-3.1-8b-instant", "llama-3.1-70b-versatile", "llama-3.3-70b-versatile",
                          "mixtral-8x7b-32768", "gemma-7b-it", "llama-3.2-3b-instruct"]
            # Map old/deprecated names to current ones
            model_mapping = {
                "llama3-8b-8192": "llama-3.1-8b-instant",
                "llama3-70b-8192": "llama-3.1-70b-versatile",
                "llama3-8b": "llama-3.1-8b-instant",
                "llama3-70b": "llama-3.1-70b-versatile"
            }
            # If user specified a mapped model name, use the current one
            if model and model in model_mapping:
                console.print(f"[yellow]Note: '{model}' is deprecated. Using '{model_mapping[model]}' instead.[/yellow]")
                model = model_mapping[model]
            # If user specified an OpenAI model or unknown model, use default Groq model
            elif model and model not in groq_models and not any(model.startswith(prefix) for prefix in ["llama", "mixtral", "gemma"]):
                console.print(f"[yellow]Warning: '{model}' is not a Groq model. Using default Groq model instead.[/yellow]")
                model = default_model
            # If no model specified, use default or from config (but only if it's a Groq model)
            if not model:
                config_model = config.get("model")
                if config_model and config_model in groq_models:
                    model = config_model
                else:
                    model = default_model
        else:
            api_key = api_key or os.getenv("OPENAI_API_KEY") or config.get("api_key")
            default_model = "gpt-4"
            model = model or config.get("model", default_model)
        
        if not api_key:
            if self.provider == "groq":
                console.print("[red]Error: Groq API key not found[/red]")
                console.print("[yellow]Get a free API key at: https://console.groq.com/keys[/yellow]")
                console.print("[yellow]Then set: export GROQ_API_KEY='your-key-here'[/yellow]")
            else:
                console.print("[red]Error: OpenAI API key not found[/red]")
                console.print("[yellow]Set it via one of:[/yellow]")
                console.print("[yellow]  1. Environment variable: export OPENAI_API_KEY='your-key-here'[/yellow]")
                console.print("[yellow]  2. Config file: ~/.smart_commit_config or .smart_commit_config[/yellow]")
                console.print("[yellow]     Format: {\"api_key\": \"your-key-here\", \"model\": \"gpt-4\"}[/yellow]")
            sys.exit(1)
        
        if not api_key.strip():
            console.print(f"[red]Error: {self.provider.upper()} API key is empty[/red]")
            sys.exit(1)
        
        try:
            if self.provider == "groq":
                # Groq uses OpenAI-compatible API
                from openai import OpenAI
                self.client = OpenAI(api_key=api_key, base_url="https://api.groq.com/openai/v1")
            else:
                self.client = OpenAI(api_key=api_key)
            self.model = model
        except Exception as e:
            console.print(f"[red]Error initializing {self.provider.upper()} client: {e}[/red]")
            sys.exit(1)
    
    def generate_message(self, changes: Dict) -> str:
        """Generate commit message from changes"""
        if not changes.get("files"):
            raise ValueError("No changes to analyze")
        
        prompt = self._build_prompt(changes)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing code changes and writing clear, professional git commit messages. You follow conventional commit format strictly. Your messages are concise, specific, and help developers understand what changed and why. Always format as: title line (50-72 chars) followed by optional body paragraph(s) separated by blank lines."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=500,
                timeout=30
            )
            
            if not response.choices or not response.choices[0].message.content:
                raise ValueError("Empty response from OpenAI API")
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            error_str = str(e).lower()
            error_msg = str(e)
            
            if "rate limit" in error_str:
                console.print("[red]Error: API rate limit exceeded. Please try again later.[/red]")
            elif "quota" in error_str or "insufficient_quota" in error_str or "billing" in error_str:
                if self.provider == "groq":
                    console.print("[red]Error: Groq API quota exceeded.[/red]")
                    console.print("[yellow]Check your Groq account at: https://console.groq.com[/yellow]")
                else:
                    console.print("[red]Error: OpenAI API quota exceeded or insufficient credits.[/red]")
                    console.print("[yellow]Please check your OpenAI account billing and add credits at:[/yellow]")
                    console.print("[yellow]https://platform.openai.com/account/billing[/yellow]")
            elif "authentication" in error_str or "api key" in error_str or "invalid api key" in error_str:
                if self.provider == "groq":
                    console.print("[red]Error: Invalid Groq API key. Check your GROQ_API_KEY environment variable.[/red]")
                else:
                    console.print("[red]Error: Invalid OpenAI API key. Check your OPENAI_API_KEY environment variable.[/red]")
            elif "model" in error_str or "not found" in error_str or "does not exist" in error_str or "decommissioned" in error_str:
                console.print(f"[red]Error: Model '{self.model}' not available or has been decommissioned.[/red]")
                if self.provider == "groq":
                    if "decommissioned" in error_str:
                        console.print("[yellow]This model has been decommissioned. Using current models:[/yellow]")
                    else:
                        console.print("[yellow]Available Groq models:[/yellow]")
                    console.print("[yellow]  - llama-3.1-8b-instant (fast, recommended)[/yellow]")
                    console.print("[yellow]  - llama-3.1-70b-versatile (more capable)[/yellow]")
                    console.print("[yellow]  - llama-3.3-70b-versatile (latest)[/yellow]")
                    console.print("[yellow]  - mixtral-8x7b-32768 (good balance)[/yellow]")
                    console.print("[yellow]  - gemma-7b-it (alternative)[/yellow]")
                    console.print("[yellow]Try: --provider groq --model llama-3.1-8b-instant[/yellow]")
                    console.print("[yellow]Check deprecations: https://console.groq.com/docs/deprecations[/yellow]")
                    console.print(f"[dim]Full error: {error_msg}[/dim]")
                else:
                    console.print("[yellow]Try using: --model gpt-3.5-turbo[/yellow]")
            else:
                console.print(f"[red]Error calling {self.provider.upper()} API: {e}[/red]")
                # Show full error for debugging
                if self.provider == "groq":
                    console.print(f"[dim]Full error details: {error_msg}[/dim]")
            sys.exit(1)
    
    def _build_prompt(self, changes: Dict) -> str:
        """Build prompt for OpenAI from changes"""
        files = changes["files"]
        
        prompt_parts = [
            "Analyze the following git changes and generate a descriptive commit message following conventional commit format.",
            "",
            "=== CHANGE SUMMARY ===",
            f"Files changed: {changes['file_count']}",
            f"Lines added: {changes['total_additions']}",
            f"Lines deleted: {changes['total_deletions']}",
            f"Net change: {changes['total_additions'] - changes['total_deletions']:+d}",
            "",
            "=== CHANGED FILES ==="
        ]
        
        # Group files by type for better organization
        files_by_type = {}
        for file_info in files:
            file_type = file_info["file_type"]
            if file_type not in files_by_type:
                files_by_type[file_type] = []
            files_by_type[file_type].append(file_info)
        
        # List files grouped by type
        for file_type, type_files in sorted(files_by_type.items()):
            prompt_parts.append(f"\n{file_type.upper()} ({len(type_files)} file(s)):")
            for file_info in type_files:
                status_icon = {
                    "added": "[NEW]",
                    "modified": "[MOD]",
                    "deleted": "[DEL]",
                    "renamed": "[REN]"
                }.get(file_info["type"], "[?]")
                prompt_parts.append(
                    f"  {status_icon} {file_info['path']} "
                    f"(+{file_info['additions']}/-{file_info['deletions']})"
                )
        
        # Add relevant diff snippets (prioritize important files)
        important_files = [f for f in files if f["file_type"] in ["api", "model", "migration", "config"]]
        other_files = [f for f in files if f["file_type"] not in ["api", "model", "migration", "config"]]
        files_to_show = (important_files + other_files)[:5]  # Show up to 5 files
        
        if files_to_show:
            prompt_parts.append("\n\n=== CODE CHANGES (snippets) ===")
            for file_info in files_to_show:
                if file_info["diff"]:
                    prompt_parts.append(f"\n--- {file_info['path']} ({file_info['type']}) ---")
                    # Truncate diff to avoid token limits (keep first 40 lines)
                    diff_lines = file_info["diff"].split('\n')[:40]
                    prompt_parts.append('\n'.join(diff_lines))
                    if len(file_info["diff"].split('\n')) > 40:
                        prompt_parts.append("... (truncated)")
        
        prompt_parts.extend([
            "\n\n=== INSTRUCTIONS ===",
            "Generate a commit message with:",
            "1. Title line (50-72 chars): Use format '[type]: brief description'",
            "2. Optional body: Provide context, explain 'what' and 'why' if needed",
            "",
            "Conventional commit types:",
            "- feat: New feature",
            "- fix: Bug fix",
            "- docs: Documentation changes",
            "- style: Code style changes (formatting, no logic change)",
            "- refactor: Code refactoring",
            "- test: Adding or updating tests",
            "- chore: Maintenance tasks, dependencies, config",
            "- perf: Performance improvements",
            "",
            "Be specific and descriptive. Focus on what changed and why it matters."
        ])
        
        return '\n'.join(prompt_parts)


@click.command()
@click.option('--model', default=None, help='Model to use (default depends on provider)')
@click.option('--provider', type=click.Choice(['openai', 'groq'], case_sensitive=False), default='openai', help='API provider: openai or groq (default: openai)')
@click.option('--auto-commit', is_flag=True, help='Automatically commit without confirmation')
@click.option('--no-preview', is_flag=True, help='Skip preview and commit directly')
def main(model: Optional[str], provider: str, auto_commit: bool, no_preview: bool):
    """Smart Commit - Auto-generate commit messages from staged changes"""
    
    # Check for staged changes
    analyzer = GitAnalyzer()
    if not analyzer.has_staged_changes():
        console.print("[yellow]No staged changes found. Stage some files first with 'git add'[/yellow]")
        sys.exit(1)
    
    # Analyze changes
    console.print("[cyan]Analyzing staged changes...[/cyan]")
    changes = analyzer.get_staged_changes()
    
    # Display summary
    net_change = changes['total_additions'] - changes['total_deletions']
    net_color = "green" if net_change >= 0 else "red"
    
    summary_text = Text()
    summary_text.append("Files: ", style="bold")
    summary_text.append(f"{changes['file_count']}\n", style="cyan")
    summary_text.append("Additions: ", style="bold")
    summary_text.append(f"+{changes['total_additions']}\n", style="green")
    summary_text.append("Deletions: ", style="bold")
    summary_text.append(f"-{changes['total_deletions']}\n", style="red")
    summary_text.append("Net: ", style="bold")
    summary_text.append(f"{net_change:+d}", style=net_color)
    
    console.print("\n[bold]Changes Summary:[/bold]")
    console.print(Panel(summary_text, border_style="blue"))
    
    # Show file list
    if changes['file_count'] <= 10:
        console.print("\n[dim]Changed files:[/dim]")
        for file_info in changes['files']:
            status_colors = {
                "added": "green",
                "modified": "yellow",
                "deleted": "red",
                "renamed": "cyan"
            }
            status_icons = {
                "added": "+",
                "modified": "~",
                "deleted": "-",
                "renamed": "→"
            }
            color = status_colors.get(file_info['type'], 'white')
            icon = status_icons.get(file_info['type'], '?')
            console.print(f"  [{color}]{icon}[/{color}] {file_info['path']} "
                         f"([green]+{file_info['additions']}[/green]/[red]-{file_info['deletions']}[/red])")
    
    # Generate commit message
    provider_name = provider.upper() if provider else "OpenAI"
    model_display = model or ("default" if provider == "groq" else "gpt-4")
    console.print(f"\n[cyan]Generating commit message with {provider_name} ({model_display})...[/cyan]")
    try:
        generator = CommitMessageGenerator(model=model, provider=provider)
        commit_message = generator.generate_message(changes)
    except KeyboardInterrupt:
        console.print("\n[yellow]Cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Error generating commit message: {e}[/red]")
        sys.exit(1)
    
    # Display preview
    if not no_preview:
        console.print("\n[bold]Generated Commit Message:[/bold]")
        # Split message into title and body for better display
        lines = commit_message.split('\n')
        title = lines[0] if lines else commit_message
        body = '\n'.join(lines[1:]) if len(lines) > 1 else None
        
        title_panel = Panel(title, border_style="green", title="Title")
        console.print(title_panel)
        if body:
            body_panel = Panel(body, border_style="dim", title="Body")
            console.print(body_panel)
    
    # Interactive confirmation
    if auto_commit:
        action = "commit"
    elif no_preview:
        action = "commit"
    else:
        console.print("\n[bold]What would you like to do?[/bold]")
        console.print("  [green]c[/green] - Commit with this message")
        console.print("  [yellow]e[/yellow] - Edit the message")
        console.print("  [cyan]r[/cyan] - Regenerate message")
        console.print("  [red]q[/red] - Quit without committing")
        
        choice = Prompt.ask("\nChoice", default="c").lower()
        
        if choice == "q":
            console.print("[yellow]Cancelled[/yellow]")
            sys.exit(0)
        elif choice == "e":
            # Open editor
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(commit_message)
                temp_path = f.name
            
            editor = os.getenv('EDITOR', 'nano')
            try:
                subprocess.run([editor, temp_path], check=True)
            except subprocess.CalledProcessError:
                console.print("[red]Error opening editor[/red]")
                sys.exit(1)
            except FileNotFoundError:
                console.print(f"[red]Editor '{editor}' not found. Set EDITOR environment variable.[/red]")
                sys.exit(1)
            
            with open(temp_path, 'r') as f:
                edited_message = f.read().strip()
            
            os.unlink(temp_path)
            
            if not edited_message:
                console.print("[yellow]Empty message, cancelling[/yellow]")
                sys.exit(0)
            
            commit_message = edited_message
            console.print("\n[green]Using edited message:[/green]")
            console.print(Panel(commit_message, border_style="green"))
            action = "commit"
        elif choice == "r":
            # Regenerate
            console.print("[cyan]Regenerating commit message...[/cyan]")
            try:
                commit_message = generator.generate_message(changes)
                lines = commit_message.split('\n')
                title = lines[0] if lines else commit_message
                body = '\n'.join(lines[1:]) if len(lines) > 1 else None
                
                title_panel = Panel(title, border_style="green", title="Title")
                console.print(title_panel)
                if body:
                    body_panel = Panel(body, border_style="dim", title="Body")
                    console.print(body_panel)
                
                if Confirm.ask("\nCommit with this message?"):
                    action = "commit"
                else:
                    sys.exit(0)
            except Exception as e:
                console.print(f"[red]Error regenerating: {e}[/red]")
                sys.exit(1)
        else:
            action = "commit"
    
    # Create commit
    if action == "commit":
        if not commit_message or not commit_message.strip():
            console.print("[red]Error: Commit message is empty[/red]")
            sys.exit(1)
        
        try:
            analyzer.repo.index.commit(commit_message)
            title_line = commit_message.split('\n')[0]
            console.print(f"\n[green]✓[/green] [bold]Commit created successfully![/bold]")
            console.print(f"[dim]{title_line}[/dim]")
            
            # Show commit hash
            commit_hash = analyzer.repo.head.commit.hexsha[:7]
            console.print(f"[dim]Commit: {commit_hash}[/dim]")
        except git.exc.GitCommandError as e:
            console.print(f"[red]Error creating commit: {e}[/red]")
            sys.exit(1)
        except Exception as e:
            console.print(f"[red]Unexpected error: {e}[/red]")
            sys.exit(1)


if __name__ == "__main__":
    main()

