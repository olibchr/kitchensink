import subprocess
import json
import os
import re

class TestRunner:
    """Manager for running tests and handling failures."""
    
    def __init__(self, target_dir, ai_client):
        self.target_dir = target_dir
        self.ai_client = ai_client
    
    def run_tests(self):
        """Run tests for the target project."""
        result = subprocess.run(["mvn", "test"], cwd=self.target_dir, capture_output=True)
        return result.returncode == 0, result.stdout.decode(), result.stderr.decode()
    
    def debug_and_fix_errors(self, test_output, error_message):
        """Use an agentic approach to debug and fix test failures."""
        # Truncate long outputs
        test_output = self._truncate_text(test_output, 10000)
        error_message = self._truncate_text(error_message, 10000)
        
        system_message = """You are an expert Java developer assistant specializing in Spring Boot migration.
You will analyze test failures, identify root causes, and provide solutions.
Follow this problem-solving process:
1. Analyze the error logs to identify the specific problem
2. Determine which files need to be modified
3. Provide the exact code changes needed
4. Explain your reasoning briefly

IMPORTANT JAVA REQUIREMENTS:
- Each public class MUST be in a file with the same name (e.g., Member.java must contain public class Member)
- Avoid duplicate class declarations
- Method signatures in child interfaces must match parent interface signatures (including return types)
- Do not include any explanatory text in the Java files, only valid code

Your response should be structured as JSON with the following format:
{
  "analysis": "Brief analysis of the error",
  "files_to_modify": [
    {
      "file_path": "Relative path to the file from project root",
      "code": "Complete content of the fixed file"
    },
    ...
  ],
  "explanation": "Brief explanation of your fix",
  "additional_files": [
    {
      "file_path": "Path to any new file needed",
      "code": "Complete content of the new file"
    },
    ...
  ]
}"""

        prompt = f"""
        I'm migrating a JBoss application to Spring Boot and encountered test failures.
        
        Here's the test output:
        {test_output}
        
        Here's the error message:
        {error_message}
        
        Please analyze what's wrong and provide a fix in the required JSON format.
        """
        
        response = self.ai_client.query(prompt, system_message=system_message)
        return self._process_solution(response)
    
    def run_tests_until_success(self, max_attempts=5):
        """Run tests until they succeed, using an agentic approach to fix failures."""
        from pathlib import Path
        from .file_utils import FileUtils
        
        # Initial validation of file structure
        self._validate_file_structure()
        
        for attempt in range(max_attempts):
            print(f"Test attempt {attempt+1}/{max_attempts}...")
            success, stdout, stderr = self.run_tests()
            
            if success:
                print("Tests passed successfully!")
                return True
            
            print(f"Test failures detected on attempt {attempt+1}. Applying agentic problem-solving...")
            
            if not self.debug_and_fix_errors(stdout, stderr):
                print("Failed to fix issues automatically.")
                
                # Try comprehensive analysis on later attempts
                if attempt >= 2:
                    print("Attempting a more comprehensive analysis...")
                    if not self._try_comprehensive_fix(stdout, stderr):
                        if attempt == max_attempts - 1:
                            # Last attempt, ask user if they want to manually fix
                            user_input = input("Tests still failing. Would you like to manually fix and continue? (y/n): ")
                            if user_input.lower() != 'y':
                                return False
        
        # Final test attempt
        success, _, _ = self.run_tests()
        return success
    
    def _try_comprehensive_fix(self, stdout, stderr):
        """Try a more comprehensive fix with file context."""
        from pathlib import Path
        from .file_utils import FileUtils
        
        # Get list of Java files
        all_files = list(Path(self.target_dir).rglob("*.java"))
        file_contents = {}
        
        # Read and truncate file contents
        for file_path in all_files[:10]:
            relative_path = file_path.relative_to(self.target_dir)
            content = FileUtils.read_file_content(file_path)
            file_contents[str(relative_path)] = self._truncate_java_file(content)
        
        # Create prompt with file context
        comprehensive_prompt = f"""
        I'm debugging Spring Boot test failures and need a comprehensive solution.
        
        Test output (truncated):
        {self._truncate_text(stdout, 5000)}
        
        Error message (truncated):
        {self._truncate_text(stderr, 5000)}
        
        Here are the key project files (some truncated for brevity):
        
        {json.dumps(file_contents, indent=2)}
        
        Please analyze what's wrong and provide fixes for ALL relevant files in the required JSON format.
        """
        
        return self.debug_and_fix_errors(comprehensive_prompt, "")
    
    def _process_solution(self, response):
        """Process and apply the AI solution."""
        from .file_utils import FileUtils
        
        try:
            # Find JSON content if embedded
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_content = response[json_start:json_end]
                solution = json.loads(json_content)
                
                # Apply fixes to existing files
                if "files_to_modify" in solution:
                    for file_info in solution["files_to_modify"]:
                        file_path = f"{self.target_dir}/{file_info['file_path']}"
                        file_code = file_info['code']
                        
                        # Additional validation for Java files
                        if file_path.endswith(".java"):
                            # Check if this is just explanatory text
                            explanation_indicators = [
                                "This cannot be provided",
                                "I cannot provide",
                                "The file should",
                                "This is a"
                            ]
                            
                            if any(file_code.strip().startswith(indicator) for indicator in explanation_indicators):
                                print(f"WARNING: Received explanatory text instead of code for {file_path}. Skipping this file.")
                                continue
                        
                            # Get filename and check if class name matches
                            filename = file_path.split("/")[-1].replace(".java", "")
                            class_match = re.search(r'public\s+(class|interface|enum)\s+(\w+)', file_code)
                            
                            if class_match:
                                class_name = class_match.group(2)
                                if class_name != filename:
                                    # Fix class name to match filename
                                    file_code = re.sub(
                                        f"public\\s+(class|interface|enum)\\s+{class_name}",
                                        f"public \\1 {filename}",
                                        file_code
                                    )
                                    print(f"Fixed class name in {file_path} from {class_name} to {filename}")
                        
                            # Ensure package declaration matches file path
                            package_match = re.search(r'package\s+([^;]+);', file_code)
                            if package_match:
                                package = package_match.group(1)
                                
                                # Figure out the expected package based on file path
                                path_parts = file_path.split("/")
                                if "/main/java/" in file_path:
                                    java_index = path_parts.index("java")
                                    expected_package = ".".join(path_parts[java_index+1:-1])
                                elif "/test/java/" in file_path:
                                    java_index = path_parts.index("java")
                                    expected_package = ".".join(path_parts[java_index+1:-1])
                                else:
                                    expected_package = "org.jboss.as.quickstarts.kitchensink"
                                    if "model" in file_path:
                                        expected_package += ".model"
                                    elif "data" in file_path:
                                        expected_package += ".data"
                                
                                if package != expected_package:
                                    print(f"WARNING: Package declaration in {file_path} doesn't match path. Fixing...")
                                    file_code = re.sub(
                                        f"package\\s+{re.escape(package)};",
                                        f"package {expected_package};",
                                        file_code
                                    )
                        
                            # Check if test file is in the right directory
                            is_test_file = "Test" in filename or filename.startswith("test") or filename.endswith("test")
                            if is_test_file and "/main/java/" in file_path:
                                # Convert main to test path
                                correct_path = file_path.replace("/main/java/", "/test/java/")
                                print(f"WARNING: Test file {file_path} is in main source, moving to {correct_path}")
                                os.makedirs(os.path.dirname(correct_path), exist_ok=True)
                                FileUtils.write_file_content(correct_path, file_code)
                                # Skip writing to main path
                                continue
                        
                        FileUtils.write_file_content(file_path, file_code)
                        print(f"Modified file: {file_info['file_path']}")
                
                # Create any new files
                if "additional_files" in solution:
                    for file_info in solution["additional_files"]:
                        file_path = f"{self.target_dir}/{file_info['file_path']}"
                        FileUtils.write_file_content(file_path, file_info['code'])
                        print(f"Created new file: {file_info['file_path']}")
                
                print(f"Analysis: {solution.get('analysis', 'No analysis provided')}")
                print(f"Explanation: {solution.get('explanation', 'No explanation provided')}")
                
                return True
            else:
                print("Could not find valid JSON in the response.")
                return False
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON solution: {str(e)}")
            print(f"Raw response: {response}")
            return False
        except Exception as e:
            print(f"Error applying solution: {str(e)}")
            return False
    
    def _truncate_text(self, text, max_length=10000):
        """Truncate text if too long."""
        if len(text) > max_length:
            return text[:max_length] + "...\n[Output truncated due to length]"
        return text
    
    def _truncate_java_file(self, content, max_length=3000):
        """Truncate Java file content while preserving structure."""
        if len(content) <= max_length:
            return content
            
        lines = content.split('\n')
        
        # Extract important parts
        imports_and_package = []
        for line in lines[:200]:
            if line.strip().startswith('package ') or line.strip().startswith('import '):
                imports_and_package.append(line)
        
        # Find class declaration
        class_decl_index = -1
        for i, line in enumerate(lines):
            if 'class ' in line or 'interface ' in line or 'enum ' in line:
                class_decl_index = i
                break
        
        if class_decl_index >= 0:
            # Get lines around class declaration
            start_idx = max(0, class_decl_index - 5)
            end_idx = min(len(lines), class_decl_index + 20)
            class_declaration = lines[start_idx:end_idx]
            
            # Combine parts
            truncated_content = '\n'.join(imports_and_package) + '\n\n' + '\n'.join(class_declaration) + '\n\n// ... file truncated ...'
            return truncated_content
            
        # If no class found, do simple truncation
        return content[:max_length] + "...\n[Content truncated]"

    def _validate_file_structure(self):
        """Validate and fix file structure issues before running tests."""
        from pathlib import Path
        import os
        import re
        from .file_utils import FileUtils
        
        print("Validating file structure...")
        
        # Check for files in wrong directories
        all_java_files = list(Path(self.target_dir).rglob("*.java"))
        for file_path in all_java_files:
            file_name = file_path.name
            is_test = "Test" in file_name or file_name.startswith("test") or file_name.endswith("Test")
            in_test_dir = "/test/java/" in str(file_path)
            in_main_dir = "/main/java/" in str(file_path)
            
            # Move test files from main to test
            if is_test and in_main_dir:
                target_path = str(file_path).replace("/main/java/", "/test/java/")
                print(f"Moving test file from main to test: {file_path} → {target_path}")
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                content = FileUtils.read_file_content(file_path)
                FileUtils.write_file_content(target_path, content)
                # Optionally delete the original file
                os.remove(file_path)
            
            # Check for correct package declaration
            content = FileUtils.read_file_content(file_path)
            package_match = re.search(r'package\s+([^;]+);', content)
            if package_match:
                package = package_match.group(1)
                
                # Determine expected package
                path_parts = str(file_path).split("/")
                if in_main_dir or in_test_dir:
                    java_index = path_parts.index("java")
                    expected_package = ".".join(path_parts[java_index+1:-1])
                    
                    if package != expected_package:
                        print(f"Fixing package declaration in {file_path}: {package} → {expected_package}")
                        content = re.sub(
                            f"package\\s+{re.escape(package)};",
                            f"package {expected_package};",
                            content
                        )
                        FileUtils.write_file_content(file_path, content)
        
        # Ensure test directories exist
        test_dir = f"{self.target_dir}/src/test/java/org/jboss/as/quickstarts/kitchensink/model"
        os.makedirs(test_dir, exist_ok=True)
        
        print("File structure validation complete")