import os

class UIMigrator:
    """Migrator for UI components."""
    
    def __init__(self, src_dir, target_dir, ai_client, file_utils):
        self.src_dir = src_dir
        self.target_dir = target_dir
        self.ai_client = ai_client
        self.file_utils = file_utils
    
    def migrate_jsf_to_thymeleaf(self, jsf_file):
        """Migrate JSF to Thymeleaf templates."""
        jsf_content = self.file_utils.read_file_content(jsf_file)
        file_name = jsf_file.name.replace(".xhtml", ".html")
        
        system_message = "You are an HTML template generation assistant. Output ONLY the complete HTML code with no additional text, explanations, or markdown formatting."
        prompt = f"""
        Convert this JSF page to a Thymeleaf template:
        
        ```xml
        {jsf_content}
        ```
        
        Make these changes:
        1. Replace JSF tags with Thymeleaf attributes
        2. Keep the same page structure and functionality
        3. Use Thymeleaf's syntax for forms, iterations, conditionals, etc.
        
        Only respond with the complete HTML Thymeleaf template, no explanations.
        """
        
        thymeleaf_template = self.ai_client.query(prompt, system_message=system_message)
        
        # Create target path
        target_path = f"{self.target_dir}/src/main/resources/templates/{file_name}"
        self.file_utils.write_file_content(target_path, thymeleaf_template)
        print(f"Migrated JSF to Thymeleaf: {file_name}")
    
    def migrate_controller(self, controller_file):
        """Migrate controller classes."""
        if not controller_file.exists():
            print(f"Warning: Controller file {controller_file} does not exist. Skipping.")
            return
            
        controller_content = self.file_utils.read_file_content(controller_file)
        file_name = controller_file.name
        
        system_message = "You are a Java code generation assistant. Output ONLY the complete Java code with no additional text, explanations, or markdown formatting."
        prompt = f"""
        Migrate this JSF-based controller to a Spring MVC controller:
        
        ```java
        {controller_content}
        ```
        
        Make these changes:
        1. Replace JSF-specific code with Spring MVC approach
        2. Keep the same functionality
        3. Use Spring's approach for forms and redirects
        
        Only respond with the complete migrated Java code, no explanations.
        """
        
        migrated_controller = self.ai_client.query(prompt, system_message=system_message)
        
        # Extract package and save file
        try:
            # Get package path
            package_path = self.file_utils.get_safe_package_path(
                controller_file, 
                controller_content, 
                "org.jboss.as.quickstarts.kitchensink.controller"
            )
            
            # Create target path
            target_path = f"{self.target_dir}/src/main/java/{package_path.replace('.', '/')}/{file_name}"
            self.file_utils.write_file_content(target_path, migrated_controller)
            print(f"Migrated controller: {file_name}")
        except Exception as e:
            print(f"Error processing controller file {controller_file}: {str(e)}")
            # Create a fallback path in case of errors
            fallback_path = f"{self.target_dir}/src/main/java/org/jboss.as.quickstarts/kitchensink/controller/{file_name}"
            self.file_utils.write_file_content(fallback_path, migrated_controller)
    
    def add_validation_to_controller(self, controller_file):
        """Add validation to controller classes."""
        if not controller_file.exists():
            print(f"Warning: Controller file {controller_file} does not exist. Skipping.")
            return
        
        file_name = controller_file.name
        
        try:
            # Get package path
            controller_content = self.file_utils.read_file_content(controller_file)
            package_path = self.file_utils.get_safe_package_path(
                controller_file, 
                controller_content, 
                "org.jboss.as.quickstarts.kitchensink.controller"
            )
            
            # Find migrated file
            target_path = f"{self.target_dir}/src/main/java/{package_path.replace('.', '/')}/{file_name}"
            if not os.path.exists(target_path):
                # Try with default path
                target_path = f"{self.target_dir}/src/main/java/org/jboss.as.quickstarts/kitchensink/controller/{file_name}"
                if not os.path.exists(target_path):
                    print(f"Warning: Could not find migrated controller file {file_name}. Skipping validation enhancements.")
                    return
            
            # Read migrated file and enhance validation
            controller_content = self.file_utils.read_file_content(target_path)
            
            system_message = "You are a Java code generation assistant. Output ONLY the complete Java code with no additional text, explanations, or markdown formatting."
            prompt = f"""
            Enhance validation in this Spring MVC controller:
            
            ```java
            {controller_content}
            ```
            
            Make these changes:
            1. Add @Valid annotations to appropriate method parameters
            2. Add BindingResult parameter for validation errors
            3. Implement proper validation error handling
            4. Keep all existing functionality
            
            Only respond with the complete updated Java code, no explanations.
            """
            
            updated_controller = self.ai_client.query(prompt, system_message=system_message)
            
            # Write back to the target path
            self.file_utils.write_file_content(target_path, updated_controller)
            print(f"Enhanced validation for controller: {file_name}")
            
        except Exception as e:
            print(f"Error enhancing validation for controller file {controller_file}: {str(e)}") 