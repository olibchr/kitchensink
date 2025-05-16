#!/usr/bin/env python3
import os
import json
import argparse
from pathlib import Path

# Import components
from components.openai_client import OpenAIClient
from components.file_utils import FileUtils
from components.git_manager import GitManager
from components.test_runner import TestRunner

# Import migrators
from migration.entity_migrator import EntityMigrator
from migration.repository_migrator import RepositoryMigrator
from migration.service_migrator import ServiceMigrator
from migration.rest_migrator import RestMigrator
from migration.ui_migrator import UIMigrator
from migration.config_migrator import ConfigMigrator

# Configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("Please set the OPENAI_API_KEY environment variable")

class JBossToSpringMigrator:
    def __init__(self, src_dir, target_dir, model="gpt-4"):
        self.src_dir = Path(src_dir).resolve()
        self.target_dir = Path(target_dir).resolve()
        
        # Initialize components
        self.ai_client = OpenAIClient(OPENAI_API_KEY, model)
        self.file_utils = FileUtils()
        self.git_manager = GitManager(self.target_dir)
        self.test_runner = TestRunner(self.target_dir, self.ai_client)
        
        # Initialize migrators
        self.entity_migrator = EntityMigrator(self.src_dir, self.target_dir, self.ai_client, self.file_utils)
        self.repository_migrator = RepositoryMigrator(self.src_dir, self.target_dir, self.ai_client, self.file_utils)
        self.service_migrator = ServiceMigrator(self.src_dir, self.target_dir, self.ai_client, self.file_utils)
        self.rest_migrator = RestMigrator(self.src_dir, self.target_dir, self.ai_client, self.file_utils)
        self.ui_migrator = UIMigrator(self.src_dir, self.target_dir, self.ai_client, self.file_utils)
        self.config_migrator = ConfigMigrator(self.src_dir, self.target_dir, self.ai_client, self.file_utils)
        
        # Ensure target directory exists
        self.target_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize git repository
        self.git_manager.init_repo()
    
    def gather_code_files(self, pattern):
        """Gather code files from source directory matching pattern."""
        return list(self.src_dir.glob(pattern))
    
    def migrate_data_layer(self):
        """Phase 1: Data Layer Migration"""
        print("Phase 1: Migrating Data Layer...")
        self.git_manager.create_branch("phase1-data-layer")
        
        # 1. Set up initial Spring Boot project structure
        self.config_migrator.setup_spring_boot_project()
        
        # 2. Migrate JPA entities
        entity_files = self.gather_code_files("**/model/*.java")
        for entity_file in entity_files:
            self.entity_migrator.migrate_entity(entity_file)
        
        # 3. Create repository interfaces
        repository_files = self.gather_code_files("**/data/*Repository.java")
        for repo_file in repository_files:
            self.repository_migrator.migrate_repository(repo_file)
        
        # 4. Configure database connection
        self.config_migrator.configure_database()
        
        # 5. Run tests and ensure they pass before continuing
        if not self.test_runner.run_tests_until_success():
            print("Failed to fix data layer tests. Migration halted at Phase 1.")
            return False
        
        self.git_manager.commit_changes("Phase 1: Data Layer Migration completed")
        print("Phase 1 completed successfully!")
        return True
    
    def migrate_service_layer(self):
        """Phase 2: Service Layer Migration"""
        print("Phase 2: Migrating Service Layer...")
        self.git_manager.create_branch("phase2-service-layer")
        
        # 1. Migrate EJB components to Spring Services
        service_files = self.gather_code_files("**/service/*.java")
        for service_file in service_files:
            self.service_migrator.migrate_service(service_file)
        
        # 2. Implement transaction management
        self.config_migrator.implement_transaction_management()
        
        # 3. Run tests and ensure they pass before continuing
        if not self.test_runner.run_tests_until_success():
            print("Failed to fix service layer tests. Migration halted at Phase 2.")
            return False
        
        self.git_manager.commit_changes("Phase 2: Service Layer Migration completed")
        print("Phase 2 completed successfully!")
        return True
    
    def migrate_rest_api(self):
        """Phase 3: REST API Migration"""
        print("Phase 3: Migrating REST API...")
        self.git_manager.create_branch("phase3-rest-api")
        
        # 1. Migrate JAX-RS endpoints
        rest_files = self.gather_code_files("**/rest/*.java")
        for rest_file in rest_files:
            self.rest_migrator.migrate_rest_endpoint(rest_file)
        
        # 2. Run tests and ensure they pass before continuing
        if not self.test_runner.run_tests_until_success():
            print("Failed to fix REST API tests. Migration halted at Phase 3.")
            return False
        
        self.git_manager.commit_changes("Phase 3: REST API Migration completed")
        print("Phase 3 completed successfully!")
        return True
    
    def migrate_ui_layer(self):
        """Phase 4: UI Layer Migration"""
        print("Phase 4: Migrating UI Layer...")
        self.git_manager.create_branch("phase4-ui-layer")
        
        # 1. Replace JSF with a modern web approach
        jsf_files = self.gather_code_files("**/webapp/*.xhtml")
        for jsf_file in jsf_files:
            self.ui_migrator.migrate_jsf_to_thymeleaf(jsf_file)
        
        # 2. Migrate controller classes
        controller_files = self.gather_code_files("**/controller/*.java")
        for controller_file in controller_files:
            self.ui_migrator.migrate_controller(controller_file)
        
        # 3. Run tests and ensure they pass before continuing
        if not self.test_runner.run_tests_until_success():
            print("Failed to fix UI layer tests. Migration halted at Phase 4.")
            return False
        
        self.git_manager.commit_changes("Phase 4: UI Layer Migration completed")
        print("Phase 4 completed successfully!")
        return True
    
    def implement_validation(self):
        """Phase 5: Validation Implementation"""
        print("Phase 5: Implementing Validation...")
        self.git_manager.create_branch("phase5-validation")
        
        # 1. Ensure validation annotations in entity classes
        entity_files = self.gather_code_files("**/model/*.java")
        for entity_file in entity_files:
            self.entity_migrator.add_validation_to_entity(entity_file)
        
        # 2. Implement validation in controllers
        controller_files = self.gather_code_files("**/controller/*.java")
        for controller_file in controller_files:
            self.ui_migrator.add_validation_to_controller(controller_file)
        
        # 3. Run tests and ensure they pass before continuing
        if not self.test_runner.run_tests_until_success():
            print("Failed to fix validation tests. Migration halted at Phase 5.")
            return False
        
        self.git_manager.commit_changes("Phase 5: Validation Implementation completed")
        print("Phase 5 completed successfully!")
        return True
    
    def migrate(self):
        """Run the full migration process."""
        print("Starting JBoss to Spring Boot migration...")
        
        # Execute all phases in order, stopping if any phase fails
        if not self.migrate_data_layer():
            return
        
        if not self.migrate_service_layer():
            return
        
        if not self.migrate_rest_api():
            return
        
        if not self.migrate_ui_layer():
            return
        
        if not self.implement_validation():
            return
        
        print("Migration completed successfully!")

def main():
    parser = argparse.ArgumentParser(description='Migrate JBoss application to Spring Boot')
    parser.add_argument('--src', required=True, help='Source JBoss application directory')
    parser.add_argument('--target', required=True, help='Target directory for Spring Boot application')
    parser.add_argument('--model', default='gpt-4', help='OpenAI model to use')
    
    args = parser.parse_args()
    
    migrator = JBossToSpringMigrator(args.src, args.target, args.model)
    migrator.migrate()

if __name__ == "__main__":
    main()