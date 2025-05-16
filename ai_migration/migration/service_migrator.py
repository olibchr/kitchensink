import os

class ServiceMigrator:
    """Migrator for EJB services."""
    
    def __init__(self, src_dir, target_dir, ai_client, file_utils):
        self.src_dir = src_dir
        self.target_dir = target_dir
        self.ai_client = ai_client
        self.file_utils = file_utils
    
    def migrate_service(self, service_file):
        """Migrate an EJB service to Spring service."""
        service_content = self.file_utils.read_file_content(service_file)
        file_name = service_file.name
        
        system_message = "You are a Java code generation assistant. Output ONLY the complete Java code with no additional text, explanations, or markdown formatting."
        prompt = f"""
        Migrate this JBoss EJB service to a Spring Boot service:
        
        ```java
        {service_content}
        ```
        
        Make these changes:
        1. Replace EJB annotations with Spring annotations (@Service, @Transactional, etc.)
        2. Update dependency injection to use Spring's approach
        3. Keep the same business logic
        4. Update any JBoss-specific APIs to Spring equivalents
        
        Only respond with the complete migrated Java code, no explanations.
        """
        
        migrated_service = self.ai_client.query(prompt, system_message=system_message)
        
        # Extract package and save file
        try:
            # Get package path
            package_path = self.file_utils.get_safe_package_path(
                service_file, 
                service_content, 
                "org.jboss.as.quickstarts.kitchensink.service"
            )
            
            # Create target path
            target_path = f"{self.target_dir}/src/main/java/{package_path.replace('.', '/')}/{file_name}"
            self.file_utils.write_file_content(target_path, migrated_service)
            print(f"Migrated service: {file_name}")
        except Exception as e:
            print(f"Error processing service file {service_file}: {str(e)}")
            # Create a fallback path in case of errors
            fallback_path = f"{self.target_dir}/src/main/java/org/jboss.as.quickstarts/kitchensink/service/{file_name}"
            self.file_utils.write_file_content(fallback_path, migrated_service) 