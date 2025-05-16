import os
import re

class EntityMigrator:
    """Migrator for JPA entities."""
    
    def __init__(self, src_dir, target_dir, ai_client, file_utils):
        self.src_dir = src_dir
        self.target_dir = target_dir
        self.ai_client = ai_client
        self.file_utils = file_utils
    
    def validate_java_file(self, file_name, content):
        """Validate generated Java file content."""
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
        
        # Check if content contains a class definition
        class_pattern = r"(public\s+class|public\s+interface|public\s+enum)\s+(\w+)"
        if not re.search(class_pattern, content):
            print(f"ERROR: No valid class/interface/enum declaration found in {file_name}")
            return None
        
        # Check if file name matches public class name
        file_name_without_ext = file_name.replace(".java", "")
        
        matches = re.findall(class_pattern, content)
        if matches:
            for _, class_name in matches:
                if class_name != file_name_without_ext:
                    # Fix by renaming the class to match the file name
                    content = re.sub(
                        f"(public\\s+class|public\\s+interface|public\\s+enum)\\s+{class_name}",
                        f"\\1 {file_name_without_ext}",
                        content
                    )
                    print(f"WARNING: Renamed class from {class_name} to {file_name_without_ext} to match file name")
        
        # Check for duplicate class declarations
        classes = re.findall(class_pattern, content)
        if len(classes) > 1:
            print(f"WARNING: Found multiple class declarations in {file_name}. Keeping only the first one.")
            # Keep everything before the second class declaration
            second_class_match = re.search(class_pattern, content[content.find(classes[0][0]) + len(classes[0][0]):])
            if second_class_match:
                second_class_pos = content.find(classes[0][0]) + len(classes[0][0]) + second_class_match.start()
                content = content[:second_class_pos] + "// Additional code removed due to duplicate class declaration"
        
        return content
    
    def migrate_entity(self, entity_file):
        """Migrate a JPA entity to Spring Boot."""
        entity_content = self.file_utils.read_file_content(entity_file)
        file_name = entity_file.name
        
        # Check if this is a test file and handle it differently
        is_test_file = "Test" in file_name or "test" in str(entity_file)
        target_dir_type = "test" if is_test_file else "main"
        
        system_message = """You are a Java code generation assistant. Output ONLY the complete Java code with no additional text, explanations, or markdown formatting.
IMPORTANT: 
1. The public class name MUST match the file name (without .java extension)
2. Include only ONE public class per file
3. Do not include comments at the beginning or end
4. All Java files must start with a package declaration
5. All required imports must be included
6. Test files MUST include appropriate JUnit 5 imports and assertions
7. Files containing 'Test' in their name should be placed in the test source folder
"""
        
        # Customize prompt based on whether this is a test file
        if is_test_file:
            prompt = f"""
            Migrate this JBoss EAP JPA entity test to a Spring Boot entity test:
            
            ```java
            {entity_content}
            ```
            
            Make these changes:
            1. Update imports to JUnit 5 and Spring Boot testing equivalents
            2. Use org.junit.jupiter.api.Assertions for assertions
            3. The class name must be {file_name.replace('.java', '')} to match the file name
            4. Follow Spring Boot testing best practices
            5. Ensure test methods use appropriate assertions
            6. This test should go in the TEST source directory, not the main source directory
            
            Only respond with the complete migrated Java code, no explanations.
            """
        else:
            prompt = f"""
            Migrate this JBoss EAP JPA entity to a Spring Boot entity:
            
            ```java
            {entity_content}
            ```
            
            Make these changes:
            1. Update imports to Spring Boot equivalents
            2. Keep all validation annotations
            3. Use appropriate Spring Data JPA annotations
            4. Follow Spring Boot best practices
            5. Keep the same logic and functionality
            
            The class name must be {file_name.replace('.java', '')} to match the file name.
            Only respond with the complete migrated Java code, no explanations.
            """
        
        migrated_entity = self.ai_client.query(prompt, system_message=system_message)
        
        # Validate and fix Java code
        migrated_entity = self.validate_java_file(file_name, migrated_entity)
        
        # If validation failed (returned None), retry with more explicit instructions
        max_retries = 3
        retry_count = 0
        
        while migrated_entity is None and retry_count < max_retries:
            retry_count += 1
            print(f"Retry {retry_count}/{max_retries} for {file_name}...")
            
            strict_prompt = f"""
            IMPORTANT: You MUST output ONLY valid Java code for a Spring Boot entity. 
            
            Original JBoss entity to migrate:
            ```java
            {entity_content}
            ```
            
            Requirements:
            1. Start with package declaration
            2. Include all necessary imports
            3. The class MUST be named: {file_name.replace('.java', '')}
            4. Use Spring Data JPA annotations (@Entity, etc.)
            5. Only return valid, compilable Java code
            6. DO NOT include any explanatory text or comments
            
            ONLY respond with the complete Java code.
            """
            
            migrated_entity = self.ai_client.query(strict_prompt, system_message=system_message)
            migrated_entity = self.validate_java_file(file_name, migrated_entity)
        
        # If we still don't have valid code after retries, create a minimal valid file
        if migrated_entity is None:
            print(f"WARNING: Failed to generate valid Java code for {file_name} after {max_retries} retries. Creating minimal stub.")
            
            # Extract package from original
            package = self.file_utils.extract_package_from_content(entity_content) or "org.jboss.as.quickstarts.kitchensink.model"
            
            # Create minimal valid class
            class_name = file_name.replace('.java', '')
            migrated_entity = f"""package {package};

import javax.persistence.Entity;
import javax.persistence.Id;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import org.springframework.data.jpa.domain.support.AuditingEntityListener;
import javax.persistence.EntityListeners;

@Entity
@EntityListeners(AuditingEntityListener.class)
public class {class_name} {{
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    // TODO: This is a minimal stub generated due to failures in the migration process
    // Original fields and methods need to be migrated manually
    
    public Long getId() {{
        return id;
    }}
    
    public void setId(Long id) {{
        this.id = id;
    }}
}}
"""
        
        # Extract package and save file, adjusting for test files
        try:
            package_path = self.file_utils.get_safe_package_path(
                entity_file, 
                entity_content, 
                "org.jboss.as.quickstarts.kitchensink.model"
            )
            
            # Create target path, placing test files in test directory
            if is_test_file:
                target_path = f"{self.target_dir}/src/test/java/{package_path.replace('.', '/')}/{file_name}"
                # Create directories if they don't exist
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
            else:
                target_path = f"{self.target_dir}/src/main/java/{package_path.replace('.', '/')}/{file_name}"
            
            self.file_utils.write_file_content(target_path, migrated_entity)
            print(f"Migrated {'test ' if is_test_file else ''}entity: {file_name}")
        except Exception as e:
            print(f"Error processing entity file {entity_file}: {str(e)}")
            # Create a fallback path in case of errors
            if is_test_file:
                fallback_path = f"{self.target_dir}/src/test/java/org/jboss/as/quickstarts/kitchensink/model/{file_name}"
            else:
                fallback_path = f"{self.target_dir}/src/main/java/org/jboss/as/quickstarts/kitchensink/model/{file_name}"
            self.file_utils.write_file_content(fallback_path, migrated_entity)
    
    def add_validation_to_entity(self, entity_file):
        """Ensure proper validation is in entity classes."""
        file_name = entity_file.name
        
        try:
            # Get package path
            entity_content = self.file_utils.read_file_content(entity_file)
            package_path = self.file_utils.get_safe_package_path(
                entity_file, 
                entity_content, 
                "org.jboss.as.quickstarts.kitchensink.model"
            )
            
            # Find migrated file
            target_path = f"{self.target_dir}/src/main/java/{package_path.replace('.', '/')}/{file_name}"
            if not os.path.exists(target_path):
                # Try with default path
                target_path = f"{self.target_dir}/src/main/java/org/jboss/as/quickstarts/kitchensink/model/{file_name}"
                if not os.path.exists(target_path):
                    print(f"Warning: Could not find migrated entity file {file_name}. Skipping validation enhancements.")
                    return
            
            # Read migrated file and enhance validation
            entity_content = self.file_utils.read_file_content(target_path)
            
            system_message = "You are a Java code generation assistant. Output ONLY the complete Java code with no additional text, explanations, or markdown formatting."
            prompt = f"""
            Check and enhance validation annotations in this Spring Boot entity:
            
            ```java
            {entity_content}
            ```
            
            Make these changes:
            1. Ensure all fields have appropriate validation annotations
            2. Add custom validation messages if missing
            3. Keep all existing functionality
            
            Only respond with the complete updated Java code, no explanations.
            """
            
            updated_entity = self.ai_client.query(prompt, system_message=system_message)
            
            # Write back to the target path
            self.file_utils.write_file_content(target_path, updated_entity)
            print(f"Enhanced validation for entity: {file_name}")
            
        except Exception as e:
            print(f"Error enhancing validation for entity file {entity_file}: {str(e)}")