import subprocess

class GitManager:
    """Manager for Git operations."""
    
    def __init__(self, target_dir):
        self.target_dir = target_dir
    
    def init_repo(self):
        """Initialize target as a git repository if it doesn't exist."""
        if not (self.target_dir / ".git").exists():
            subprocess.run(["git", "init"], cwd=self.target_dir)
    
    def create_branch(self, branch_name):
        """Create a new git branch."""
        subprocess.run(["git", "checkout", "-b", branch_name], cwd=self.target_dir)
    
    def commit_changes(self, message):
        """Commit changes to git."""
        subprocess.run(["git", "add", "."], cwd=self.target_dir)
        subprocess.run(["git", "commit", "-m", message], cwd=self.target_dir)