import os
import re
import json
import fnmatch
from collections import Counter, defaultdict

class DocumentationAnalyzer:
    def __init__(self, project_path):
        self.project_path = project_path
        self.java_files = []
        self.doc_metrics = {
            "class_doc_coverage": 0,
            "method_doc_coverage": 0,
            "readme_completeness": 0,
            "code_comment_ratio": 0,
            "api_documentation": 0,
            "example_coverage": 0,
            "architecture_doc": 0,
            "overall_score": 0
        }
        self.results = {}
        
    def find_java_files(self):
        """Find all Java files in the project"""
        for root, dirnames, filenames in os.walk(self.project_path):
            for filename in fnmatch.filter(filenames, "*.java"):
                self.java_files.append(os.path.join(root, filename))
        return len(self.java_files)
    
    def analyze_javadoc_coverage(self):
        """Analyze Javadoc coverage for classes and methods"""
        total_classes = 0
        documented_classes = 0
        total_methods = 0
        documented_methods = 0
        
        for java_file in self.java_files:
            with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Count classes and their documentation
            class_pattern = re.compile(r'(?:/\*\*[\s\S]*?\*/\s+)?(public\s+class|public\s+interface|public\s+enum)\s+(\w+)')
            classes = class_pattern.findall(content)
            total_classes += len(classes)
            
            for match in classes:
                # Check if class has JavaDoc
                class_name = match[1]
                class_pos = content.find(f"{match[0]} {class_name}")
                if class_pos > 0:
                    preceding_text = content[:class_pos].strip()
                    if preceding_text.endswith("*/"):
                        documented_classes += 1
            
            # Count methods and their documentation
            method_pattern = re.compile(r'(?:/\*\*[\s\S]*?\*/\s+)?(public|protected)\s+(?:static\s+)?(?:[\w<>?,\s]+)\s+(\w+)\s*\([^)]*\)')
            methods = method_pattern.findall(content)
            total_methods += len(methods)
            
            for match in methods:
                # Check if method has JavaDoc
                method_name = match[1]
                method_pos = content.find(f"{match[0]} ")
                if method_pos > 0:
                    preceding_text = content[:method_pos].strip()
                    if preceding_text.endswith("*/"):
                        documented_methods += 1
        
        class_coverage = documented_classes / total_classes if total_classes > 0 else 0
        method_coverage = documented_methods / total_methods if total_methods > 0 else 0
        
        self.doc_metrics["class_doc_coverage"] = round(class_coverage * 100, 2)
        self.doc_metrics["method_doc_coverage"] = round(method_coverage * 100, 2)
        
        return {
            "total_classes": total_classes,
            "documented_classes": documented_classes,
            "class_coverage_percentage": self.doc_metrics["class_doc_coverage"],
            "total_methods": total_methods,
            "documented_methods": documented_methods,
            "method_coverage_percentage": self.doc_metrics["method_doc_coverage"]
        }
    
    def analyze_code_comment_ratio(self):
        """Calculate the ratio of comments to code"""
        total_lines = 0
        comment_lines = 0
        code_lines = 0
        
        for java_file in self.java_files:
            in_multiline_comment = False
            
            with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    stripped_line = line.strip()
                    total_lines += 1
                    
                    # Skip empty lines
                    if not stripped_line:
                        continue
                    
                    # Check for multiline comments
                    if in_multiline_comment:
                        comment_lines += 1
                        if "*/" in stripped_line:
                            in_multiline_comment = False
                        continue
                    
                    # Check for the start of a multiline comment
                    if stripped_line.startswith("/*") or stripped_line.startswith("/**"):
                        comment_lines += 1
                        if not stripped_line.endswith("*/"):
                            in_multiline_comment = True
                        continue
                    
                    # Check for single line comments
                    if stripped_line.startswith("//"):
                        comment_lines += 1
                        continue
                    
                    # This is a code line
                    code_lines += 1
        
        comment_ratio = comment_lines / code_lines if code_lines > 0 else 0
        self.doc_metrics["code_comment_ratio"] = round(comment_ratio * 100, 2)
        
        return {
            "total_lines": total_lines,
            "comment_lines": comment_lines,
            "code_lines": code_lines,
            "comment_to_code_ratio": self.doc_metrics["code_comment_ratio"]
        }
    
    def analyze_readme_quality(self):
        """Analyze the quality of README files"""
        readme_files = []
        for root, _, filenames in os.walk(self.project_path):
            for filename in filenames:
                if filename.lower().startswith('readme.'):
                    readme_files.append(os.path.join(root, filename))
        
        if not readme_files:
            self.doc_metrics["readme_completeness"] = 0
            return {"readme_found": False}
        
        readme_score = 0
        readme_contents = ""
        
        for readme in readme_files:
            with open(readme, 'r', encoding='utf-8', errors='ignore') as f:
                readme_contents += f.read()
        
        # Check for key sections in README
        key_sections = [
            r'(installation|setup|getting started)',
            r'(usage|how to use)',
            r'(api|endpoints)',
            r'(configuration|settings)',
            r'(examples?|demos?)',
            r'(architecture|design)',
            r'(contribute|contributing)',
            r'(license|licensing)'
        ]
        
        section_scores = {}
        for section in key_sections:
            found = bool(re.search(section, readme_contents, re.IGNORECASE))
            section_scores[section] = 1 if found else 0
            readme_score += section_scores[section]
        
        readme_score = (readme_score / len(key_sections)) * 100
        self.doc_metrics["readme_completeness"] = round(readme_score, 2)
        
        return {
            "readme_found": True,
            "readme_files": readme_files,
            "section_coverage": section_scores,
            "readme_score": self.doc_metrics["readme_completeness"]
        }
    
    def analyze_api_documentation(self):
        """Analyze API documentation quality"""
        api_files = []
        for java_file in self.java_files:
            with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                if '@Path' in content or '@RestController' in content or '@WebServlet' in content:
                    api_files.append(java_file)
        
        if not api_files:
            self.doc_metrics["api_documentation"] = 0
            return {"api_files_found": False}
        
        api_score = 0
        total_endpoints = 0
        documented_endpoints = 0
        
        for api_file in api_files:
            with open(api_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Find REST endpoints
            endpoint_patterns = [
                r'@(GET|POST|PUT|DELETE|PATCH)[\s\n]*(?:/\*\*[\s\S]*?\*/\s+)?public\s+[\w<>?[\],\s]+\s+(\w+)\s*\(',
                r'@RequestMapping[\s\n]*(?:/\*\*[\s\S]*?\*/\s+)?public\s+[\w<>?[\],\s]+\s+(\w+)\s*\('
            ]
            
            for pattern in endpoint_patterns:
                endpoints = re.findall(pattern, content)
                total_endpoints += len(endpoints)
                
                for endpoint in endpoints:
                    method_name = endpoint[1] if isinstance(endpoint, tuple) and len(endpoint) > 1 else endpoint
                    method_pos = content.find(f"public") # Simplified - real implementation would be more precise
                    
                    # Check if method has documentation
                    if method_pos > 0:
                        preceding_text = content[:method_pos].strip()
                        if preceding_text.endswith("*/"):
                            documented_endpoints += 1
        
        api_score = documented_endpoints / total_endpoints if total_endpoints > 0 else 0
        self.doc_metrics["api_documentation"] = round(api_score * 100, 2)
        
        return {
            "api_files_found": True,
            "api_files_count": len(api_files),
            "total_endpoints": total_endpoints,
            "documented_endpoints": documented_endpoints,
            "api_doc_score": self.doc_metrics["api_documentation"]
        }
    
    def analyze_examples(self):
        """Analyze the presence of examples in documentation"""
        example_count = 0
        files_with_examples = 0
        
        for java_file in self.java_files:
            has_example = False
            with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Look for @example tags in JavaDoc
            examples = re.findall(r'@example', content, re.IGNORECASE)
            example_count += len(examples)
            
            # Look for code blocks in JavaDoc that might be examples
            code_examples = re.findall(r'<pre>[\s\S]*?</pre>|```[\s\S]*?```', content)
            example_count += len(code_examples)
            
            if examples or code_examples:
                has_example = True
                files_with_examples += 1
        
        # Check README for examples
        readme_files = []
        for root, _, filenames in os.walk(self.project_path):
            for filename in filenames:
                if filename.lower().startswith('readme.'):
                    readme_files.append(os.path.join(root, filename))
        
        readme_examples = 0
        for readme in readme_files:
            with open(readme, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            code_blocks = re.findall(r'```[\s\S]*?```|~~~[\s\S]*?~~~|<pre>[\s\S]*?</pre>', content)
            readme_examples += len(code_blocks)
        
        example_count += readme_examples
        example_score = min(100, (example_count / max(1, len(self.java_files))) * 100)
        self.doc_metrics["example_coverage"] = round(example_score, 2)
        
        return {
            "total_examples": example_count,
            "readme_examples": readme_examples,
            "files_with_examples": files_with_examples,
            "example_score": self.doc_metrics["example_coverage"]
        }
    
    def analyze_architecture_docs(self):
        """Analyze architecture documentation"""
        architecture_docs = []
        for root, _, filenames in os.walk(self.project_path):
            for filename in filenames:
                if any(term in filename.lower() for term in ['architecture', 'design', 'structure']):
                    if filename.endswith(('.md', '.txt', '.adoc', '.html', '.pdf')):
                        architecture_docs.append(os.path.join(root, filename))
        
        # Check README for architecture sections
        readme_files = []
        has_architecture_section = False
        for root, _, filenames in os.walk(self.project_path):
            for filename in filenames:
                if filename.lower().startswith('readme.'):
                    readme_files.append(os.path.join(root, filename))
        
        for readme in readme_files:
            with open(readme, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            if re.search(r'#+ *(architecture|design|structure)', content, re.IGNORECASE):
                has_architecture_section = True
        
        # Check for diagrams
        diagrams = []
        for root, _, filenames in os.walk(self.project_path):
            for filename in filenames:
                if filename.endswith(('.png', '.jpg', '.svg', '.drawio')):
                    if any(term in filename.lower() for term in ['diagram', 'arch', 'structure', 'flow']):
                        diagrams.append(os.path.join(root, filename))
        
        score = 0
        if architecture_docs:
            score += 50
        if has_architecture_section:
            score += 30
        if diagrams:
            score += 20
        
        self.doc_metrics["architecture_doc"] = score
        
        return {
            "architecture_docs": architecture_docs,
            "has_architecture_in_readme": has_architecture_section,
            "diagrams": diagrams,
            "architecture_score": self.doc_metrics["architecture_doc"]
        }
    
    def calculate_overall_score(self):
        """Calculate overall documentation score with weighted metrics"""
        weights = {
            "class_doc_coverage": 0.15,
            "method_doc_coverage": 0.20,
            "readme_completeness": 0.20,
            "code_comment_ratio": 0.10,
            "api_documentation": 0.15,
            "example_coverage": 0.10,
            "architecture_doc": 0.10
        }
        
        overall_score = sum(self.doc_metrics[metric] * weights[metric] for metric in weights)
        self.doc_metrics["overall_score"] = round(overall_score, 2)
        
        return self.doc_metrics["overall_score"]
    
    def analyze(self):
        """Run the full analysis"""
        print("Starting documentation analysis...")
        
        print("Finding Java files...")
        java_count = self.find_java_files()
        print(f"Found {java_count} Java files")
        
        print("Analyzing Javadoc coverage...")
        javadoc_results = self.analyze_javadoc_coverage()
        
        print("Analyzing code comment ratio...")
        comment_results = self.analyze_code_comment_ratio()
        
        print("Analyzing README quality...")
        readme_results = self.analyze_readme_quality()
        
        print("Analyzing API documentation...")
        api_results = self.analyze_api_documentation()
        
        print("Analyzing examples...")
        example_results = self.analyze_examples()
        
        print("Analyzing architecture documentation...")
        architecture_results = self.analyze_architecture_docs()
        
        print("Calculating overall score...")
        overall_score = self.calculate_overall_score()
        
        self.results = {
            "metrics": self.doc_metrics,
            "java_files": java_count,
            "javadoc_details": javadoc_results,
            "comments_details": comment_results,
            "readme_details": readme_results,
            "api_details": api_results,
            "example_details": example_results,
            "architecture_details": architecture_results
        }
        
        return self.results
    
    def generate_report(self):
        """Generate a formatted report of the analysis"""
        if not self.results:
            self.analyze()
        
        report = f"""
Documentation Analysis Report
============================

Overall Documentation Score: {self.doc_metrics['overall_score']}/100

Metrics Breakdown:
-----------------
Class Documentation Coverage: {self.doc_metrics['class_doc_coverage']}%
Method Documentation Coverage: {self.doc_metrics['method_doc_coverage']}%
README Completeness: {self.doc_metrics['readme_completeness']}%
Code Comment Ratio: {self.doc_metrics['code_comment_ratio']}%
API Documentation: {self.doc_metrics['api_documentation']}%
Example Coverage: {self.doc_metrics['example_coverage']}%
Architecture Documentation: {self.doc_metrics['architecture_doc']}%

Summary:
--------
- Found {self.results['java_files']} Java files
- {self.results['javadoc_details']['documented_classes']} out of {self.results['javadoc_details']['total_classes']} classes have documentation
- {self.results['javadoc_details']['documented_methods']} out of {self.results['javadoc_details']['total_methods']} methods have documentation
- README completeness score: {self.doc_metrics['readme_completeness']}/100
- API endpoints with documentation: {self.results['api_details'].get('documented_endpoints', 0)} out of {self.results['api_details'].get('total_endpoints', 0)}
- Total examples found: {self.results['example_details']['total_examples']}

Recommendations:
--------------
"""
        # Generate recommendations based on scores
        if self.doc_metrics['class_doc_coverage'] < 70:
            report += "- Improve class-level documentation\n"
        if self.doc_metrics['method_doc_coverage'] < 70:
            report += "- Add more method-level documentation\n"
        if self.doc_metrics['readme_completeness'] < 70:
            report += "- Enhance README with more sections (usage, examples, etc.)\n"
        if self.doc_metrics['api_documentation'] < 70:
            report += "- Improve API endpoint documentation\n"
        if self.doc_metrics['example_coverage'] < 50:
            report += "- Add more code examples in documentation\n"
        if self.doc_metrics['architecture_doc'] < 50:
            report += "- Add architecture documentation or diagrams\n"
        
        return report

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze Java project documentation quality')
    parser.add_argument('project_path', help='Path to the Java project directory')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--output', help='Output file path for the report')
    
    args = parser.parse_args()
    
    analyzer = DocumentationAnalyzer(args.project_path)
    analyzer.analyze()
    
    if args.json:
        result = json.dumps(analyzer.results, indent=2)
        if args.output:
            with open(args.output, 'w') as f:
                f.write(result)
        else:
            print(result)
    else:
        report = analyzer.generate_report()
        if args.output:
            with open(args.output, 'w') as f:
                f.write(report)
        else:
            print(report)

if __name__ == "__main__":
    main()
