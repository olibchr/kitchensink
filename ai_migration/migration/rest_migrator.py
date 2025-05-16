import os

class RestMigrator:
    """Migrator for REST endpoints."""
    
    def __init__(self, src_dir, target_dir, ai_client, file_utils):
        self.src_dir = src_dir
        self.target_dir = target_dir
        self.ai_client = ai_client
        self.file_utils = file_utils
    
    def migrate_rest_endpoint(self, rest_file):
        """Migrate JAX-RS endpoints to Spring @RestController."""
        rest_content = self.file_utils.read_file_content(rest_file)
        file_name = rest_file.name
        
        system_message = "You are a Java code generation assistant. Output ONLY the complete Java code with no additional text, explanations, or markdown formatting."
        prompt = f"""
        Migrate this JAX-RS endpoint to a Spring Boot RestController:
        
        ```java
        {rest_content}
        ```
        
        Make these changes:
        1. Replace JAX-RS annotations with Spring MVC annotations
        2. Keep the same API paths and functionality
        3. Update dependency injection to use Spring's approach
        4. Maintain the same validation and error handling logic
        
        Only respond with the complete migrated Java code, no explanations.
        """
        
        migrated_rest = self.ai_client.query(prompt, system_message=system_message)
        
        # Extract package and save file
        try:
            # Get package path
            package_path = self.file_utils.get_safe_package_path(
                rest_file, 
                rest_content, 
                "org.jboss.as.quickstarts.kitchensink.rest"
            )
            
            # Create target path
            target_path = f"{self.target_dir}/src/main/java/{package_path.replace('.', '/')}/{file_name}"
            self.file_utils.write_file_content(target_path, migrated_rest)
            print(f"Migrated REST endpoint: {file_name}")
        except Exception as e:
            print(f"Error processing REST file {rest_file}: {str(e)}")
            # Create a fallback path in case of errors
            fallback_path = f"{self.target_dir}/src/main/java/org/jboss.as.quickstarts/kitchensink/rest/{file_name}"
            self.file_utils.write_file_content(fallback_path, migrated_rest) 