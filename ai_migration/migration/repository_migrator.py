import os
import re

class RepositoryMigrator:
    """Migrator for repository interfaces."""
    
    def __init__(self, src_dir, target_dir, ai_client, file_utils):
        self.src_dir = src_dir
        self.target_dir = target_dir
        self.ai_client = ai_client
        self.file_utils = file_utils
    
    def validate_repository_file(self, file_name, content):
        """Validate generated repository Java file content."""
        # First check if the content is explanatory text rather than code
        explanation_indicators = [
            "This cannot be provided",
            "I cannot provide",
            "Here is the",
            "The file should",
            "This is a",
            "This code",
            "Without seeing"
        ]
        
        # If content starts with an explanation, it's not valid Java
        for indicator in explanation_indicators:
            if content.strip().startswith(indicator):
                print(f"ERROR: Generated content for {file_name} is explanatory text, not Java code.")
                return None
        
        # Check for required Java structural elements
        if "package " not in content:
            print(f"WARNING: No package declaration found in {file_name}")
        
        # Check if content contains an interface definition
        interface_pattern = r"public\s+interface\s+(\w+)"
        if not re.search(interface_pattern, content):
            print(f"ERROR: No valid interface declaration found in {file_name}")
            return None
        
        # Check if file name matches public interface name
        file_name_without_ext = file_name.replace(".java", "")
        
        matches = re.findall(interface_pattern, content)
        if matches:
            for interface_name in matches:
                if interface_name != file_name_without_ext:
                    # Fix by renaming the interface to match the file name
                    content = re.sub(
                        f"public\\s+interface\\s+{interface_name}",
                        f"public interface {file_name_without_ext}",
                        content
                    )
                    print(f"WARNING: Renamed interface from {interface_name} to {file_name_without_ext} to match file name")
        
        # Check for method signature clashes with return types
        extend_pattern = r"extends\s+(\w+)"
        extends_match = re.search(extend_pattern, content)
        if extends_match:
            parent_interface = extends_match.group(1)
            # Add comment to check return types
            content = content.replace("public interface",
                                     f"// Make sure all method return types match those in {parent_interface}\npublic interface")
        
        return content

    def migrate_repository(self, repo_file):
        """Migrate a repository to Spring Data JPA."""
        repo_content = self.file_utils.read_file_content(repo_file)
        file_name = repo_file.name
        
        system_message = """You are a Java code generation assistant. Output ONLY the complete Java code with no additional text, explanations, or markdown formatting.
IMPORTANT: 
1. The public interface name MUST match the file name (without .java extension)
2. Include only ONE public interface per file
3. Do not include comments at the beginning or end
4. Ensure all method signatures in child interfaces match parent interfaces (including return types)
5. All Java files must start with a package declaration
6. All required imports must be included
"""
        prompt = f"""
        Migrate this JBoss EAP repository to a Spring Data JPA repository:
        
        ```java
        {repo_content}
        ```
        
        Make these changes:
        1. Create a Spring Data JPA repository interface
        2. Keep the same query methods
        3. Use Spring Data's query derivation or @Query annotations
        4. Follow Spring Boot best practices
        
        The interface name must be {file_name.replace('.java', '')} to match the file name.
        Only respond with the complete migrated Java code, no explanations.
        """
        
        migrated_repo = self.ai_client.query(prompt, system_message=system_message)
        
        # Validate and fix Java code
        migrated_repo = self.validate_repository_file(file_name, migrated_repo)
        
        # If validation failed (returned None), retry with more explicit instructions
        max_retries = 3
        retry_count = 0
        
        while migrated_repo is None and retry_count < max_retries:
            retry_count += 1
            print(f"Retry {retry_count}/{max_retries} for {file_name}...")
            
            strict_prompt = f"""
            IMPORTANT: You MUST output ONLY valid Java code for a Spring Data JPA repository interface. 
            
            Original JBoss repository to migrate:
            ```java
            {repo_content}
            ```
            
            Requirements:
            1. Start with package declaration
            2. Include all necessary imports
            3. The interface MUST be named: {file_name.replace('.java', '')}
            4. Make it extend Spring Data's JpaRepository
            5. Only return valid, compilable Java code
            6. DO NOT include any explanatory text or comments
            
            ONLY respond with the complete Java code.
            """
            
            migrated_repo = self.ai_client.query(strict_prompt, system_message=system_message)
            migrated_repo = self.validate_repository_file(file_name, migrated_repo)
        
        # If we still don't have valid code after retries, create a minimal valid file
        if migrated_repo is None:
            print(f"WARNING: Failed to generate valid Java code for {file_name} after {max_retries} retries. Creating minimal stub.")
            
            # Extract package from original
            package = self.file_utils.extract_package_from_content(repo_content) or "org.jboss.as.quickstarts.kitchensink.data"
            
            # Create minimal valid interface
            interface_name = file_name.replace('.java', '')
            
            # Try to determine the entity class name
            entity_class = "Member"  # Default to common entity
            if "Member" in interface_name:
                entity_class = "Member"
            
            migrated_repo = f"""package {package};

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import org.jboss.as.quickstarts.kitchensink.model.{entity_class};

@Repository
public interface {interface_name} extends JpaRepository<{entity_class}, Long> {{
    // TODO: This is a minimal stub generated due to failures in the migration process
    // Original methods need to be migrated manually
}}
"""
        
        # Use the safe package path extraction
        try:
            # Get package path
            package_path = self.file_utils.get_safe_package_path(
                repo_file, 
                repo_content, 
                "org.jboss.as.quickstarts.kitchensink.repository"
            )
            
            # Create target path
            target_path = f"{self.target_dir}/src/main/java/{package_path.replace('.', '/')}/{file_name}"
            self.file_utils.write_file_content(target_path, migrated_repo)
            print(f"Migrated repository: {file_name}")
        except Exception as e:
            print(f"Error processing repository file {repo_file}: {str(e)}")
            # Create a fallback path in case of errors
            fallback_path = f"{self.target_dir}/src/main/java/org/jboss.as.quickstarts/kitchensink/repository/{file_name}"
            self.file_utils.write_file_content(fallback_path, migrated_repo) 