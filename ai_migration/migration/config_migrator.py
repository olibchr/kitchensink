import os

class ConfigMigrator:
    """Migrator for Spring Boot configuration."""
    
    def __init__(self, src_dir, target_dir, ai_client, file_utils):
        self.src_dir = src_dir
        self.target_dir = target_dir
        self.ai_client = ai_client
        self.file_utils = file_utils
    
    def setup_spring_boot_project(self):
        """Set up initial Spring Boot project structure."""
        # Create pom.xml
        system_message = "You are a code generation assistant. Output ONLY the complete XML code with no additional text, explanations, or markdown formatting."
        pom_xml = self.ai_client.query(
            """
            Create a pom.xml file for a Spring Boot application that is migrated from a JBoss EAP application.
            The application should include:
            - Spring Boot Starter Web
            - Spring Boot Starter Data JPA
            - Spring Boot Starter Validation
            - Spring Boot Starter Test
            - H2 Database for testing
            - PostgreSQL driver for production
            - Thymeleaf for templates
            The Java version should be 17.
            The group ID should be org.jboss.as.quickstarts and the artifact ID should be kitchensink-spring.
            """,
            system_message=system_message
        )
        self.file_utils.write_file_content(f"{self.target_dir}/pom.xml", pom_xml)
        print("Created pom.xml")
        
        # Create application.properties
        system_message = "You are a configuration file generation assistant. Output ONLY the complete properties file content with no additional text, explanations, or markdown formatting."
        app_properties = self.ai_client.query(
            """
            Create a Spring Boot application.properties file with:
            - Database configuration (H2 for dev/test, prepared for PostgreSQL in production)
            - JPA/Hibernate settings
            - Logging configuration
            - Server port and context path configuration
            """,
            system_message=system_message
        )
        self.file_utils.write_file_content(f"{self.target_dir}/src/main/resources/application.properties", app_properties)
        print("Created application.properties")
        
        # Create main Application class
        system_message = "You are a Java code generation assistant. Output ONLY the complete Java code with no additional text, explanations, or markdown formatting."
        main_class = self.ai_client.query(
            """
            Create a Spring Boot main application class in 
            org.jboss.as.quickstarts.kitchensink package.
            """,
            system_message=system_message
        )
        self.file_utils.write_file_content(
            f"{self.target_dir}/src/main/java/org/jboss/as/quickstarts/kitchensink/KitchensinkApplication.java", 
            main_class
        )
        print("Created main Application class")
    
    def configure_database(self):
        """Configure database settings for Spring Boot."""
        # Database config is already in application.properties
        # Create test configuration if needed
        system_message = "You are a Java code generation assistant. Output ONLY the complete Java code with no additional text, explanations, or markdown formatting."
        test_config = self.ai_client.query(
            """
            Create a Spring Boot test configuration class that sets up an H2 in-memory database
            for testing purposes. The class should be in the org.jboss.as.quickstarts.kitchensink.config package.
            """,
            system_message=system_message
        )
        
        self.file_utils.write_file_content(
            f"{self.target_dir}/src/test/java/org/jboss/as/quickstarts/kitchensink/config/TestDatabaseConfig.java",
            test_config
        )
        print("Created database test configuration")
    
    def implement_transaction_management(self):
        """Implement transaction management."""
        # Create a configuration class for transactions
        system_message = "You are a Java code generation assistant. Output ONLY the complete Java code with no additional text, explanations, or markdown formatting."
        tx_config = self.ai_client.query(
            """
            Create a Spring Boot configuration class for transaction management.
            The class should be in org.jboss.as.quickstarts.kitchensink.config package.
            """,
            system_message=system_message
        )
        
        self.file_utils.write_file_content(
            f"{self.target_dir}/src/main/java/org/jboss/as/quickstarts/kitchensink/config/TransactionConfig.java",
            tx_config
        )
        print("Created transaction configuration") 