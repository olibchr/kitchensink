import os
from pathlib import Path

class FileUtils:
    """Utilities for file operations."""
    
    @staticmethod
    def read_file_content(file_path):
        """Read content of a file."""
        with open(file_path, 'r') as file:
            return file.read()
    
    @staticmethod
    def write_file_content(file_path, content):
        """Write content to a file."""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as file:
            file.write(content)
    
    @staticmethod
    def extract_package_from_content(content):
        """Extract package name from Java file content."""
        for line in content.splitlines():
            if line.strip().startswith("package "):
                return line.strip().replace("package ", "").replace(";", "")
        return None
    
    @staticmethod
    def extract_package_from_path(file_path):
        """Extract package name from file path."""
        path_parts = str(file_path).split("/")
        java_index = -1
        for i, part in enumerate(path_parts):
            if part == "java":
                java_index = i
                break
        
        if java_index >= 0 and java_index + 1 < len(path_parts):
            # Extract package path from directory structure after 'java' folder
            package_parts = path_parts[java_index+1:-1]  # Exclude filename
            return ".".join(package_parts)
        return None
    
    @staticmethod
    def get_safe_package_path(file_path, content, default_package):
        """Get package path safely from file content or path."""
        # Try to extract from content
        package = FileUtils.extract_package_from_content(content)
        if package:
            return package
        
        # Try to extract from path
        package = FileUtils.extract_package_from_path(file_path)
        if package:
            return package
        
        # Return default package as last resort
        return default_package