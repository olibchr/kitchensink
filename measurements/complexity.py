import os
import re
import json
import fnmatch
import ast
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

class ComplexityAnalyzer:
    def __init__(self, project_path):
        self.project_path = project_path
        self.java_files = []
        self.xml_files = []
        self.complexity_metrics = {
            "avg_method_length": 0,
            "avg_cyclomatic_complexity": 0,
            "dependency_count": 0,
            "total_loc": 0,
            "config_complexity": 0,
            "overall_complexity_score": 0
        }
        self.results = {}
        
    def find_files(self):
        """Find all Java and XML configuration files in the project"""
        for root, dirnames, filenames in os.walk(self.project_path):
            for filename in fnmatch.filter(filenames, "*.java"):
                self.java_files.append(os.path.join(root, filename))
            for filename in fnmatch.filter(filenames, "*.xml"):
                self.xml_files.append(os.path.join(root, filename))
        
        # Also find build files
        build_files = []
        for root, _, filenames in os.walk(self.project_path):
            for filename in filenames:
                if filename in ["pom.xml", "build.gradle", "build.gradle.kts"]:
                    build_files.append(os.path.join(root, filename))
        
        return {
            "java_files_count": len(self.java_files),
            "xml_files_count": len(self.xml_files),
            "build_files": build_files
        }
    
    def analyze_method_complexity(self):
        """Analyze method length and cyclomatic complexity"""
        method_lengths = []
        cyclomatic_complexities = []
        long_methods = []
        complex_methods = []
        
        for java_file in self.java_files:
            with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Find all method definitions
            method_pattern = re.compile(r'(public|private|protected)(?:\s+static)?\s+[\w<>\[\],\s]+\s+(\w+)\s*\([^)]*\)\s*(?:throws\s+[\w,\s]+)?\s*\{([\s\S]*?)(?=\n\s*\})')
            methods = method_pattern.findall(content)
            
            file_rel_path = os.path.relpath(java_file, self.project_path)
            
            for method in methods:
                method_name = method[1]
                method_body = method[2]
                
                # Calculate method length (LOC)
                method_lines = len(method_body.strip().split("\n"))
                method_lengths.append(method_lines)
                
                if method_lines > 30:  # Threshold for long methods
                    long_methods.append({
                        "file": file_rel_path,
                        "method": method_name,
                        "length": method_lines
                    })
                
                # Calculate cyclomatic complexity
                complexity = 1  # Base complexity
                
                # Count decision points
                complexity += method_body.count("if ")
                complexity += method_body.count("else ")
                complexity += method_body.count("case ")
                complexity += method_body.count("default:")
                complexity += method_body.count("for ")
                complexity += method_body.count("while ")
                complexity += method_body.count("do ")
                complexity += method_body.count("catch ")
                complexity += method_body.count(" && ")
                complexity += method_body.count(" || ")
                complexity += method_body.count(" ? ")
                
                cyclomatic_complexities.append(complexity)
                
                if complexity > 10:  # Threshold for complex methods
                    complex_methods.append({
                        "file": file_rel_path,
                        "method": method_name,
                        "complexity": complexity
                    })
        
        avg_method_length = sum(method_lengths) / len(method_lengths) if method_lengths else 0
        avg_complexity = sum(cyclomatic_complexities) / len(cyclomatic_complexities) if cyclomatic_complexities else 0
        
        self.complexity_metrics["avg_method_length"] = round(avg_method_length, 2)
        self.complexity_metrics["avg_cyclomatic_complexity"] = round(avg_complexity, 2)
        
        return {
            "total_methods": len(method_lengths),
            "avg_method_length": self.complexity_metrics["avg_method_length"],
            "avg_cyclomatic_complexity": self.complexity_metrics["avg_cyclomatic_complexity"],
            "long_methods": long_methods[:10],  # Limit to top 10
            "complex_methods": complex_methods[:10],  # Limit to top 10
            "method_length_distribution": {
                "1-10": sum(1 for x in method_lengths if 1 <= x <= 10),
                "11-20": sum(1 for x in method_lengths if 11 <= x <= 20),
                "21-30": sum(1 for x in method_lengths if 21 <= x <= 30),
                "31-50": sum(1 for x in method_lengths if 31 <= x <= 50),
                "50+": sum(1 for x in method_lengths if x > 50)
            },
            "complexity_distribution": {
                "1-5": sum(1 for x in cyclomatic_complexities if 1 <= x <= 5),
                "6-10": sum(1 for x in cyclomatic_complexities if 6 <= x <= 10),
                "11-15": sum(1 for x in cyclomatic_complexities if 11 <= x <= 15),
                "16-20": sum(1 for x in cyclomatic_complexities if 16 <= x <= 20),
                "20+": sum(1 for x in cyclomatic_complexities if x > 20)
            }
        }
    
    def analyze_dependencies(self):
        """Analyze dependency count and types"""
        import_counts = Counter()
        external_dependencies = defaultdict(int)
        internal_dependencies = defaultdict(int)
        dependency_list = []
        
        # Extract Maven/Gradle dependencies
        build_dependencies = []
        pom_files = [f for f in self.xml_files if f.endswith("pom.xml")]
        for pom_file in pom_files:
            try:
                tree = ET.parse(pom_file)
                root = tree.getroot()
                
                # Handle namespaces in Maven POM files
                namespace = {'maven': 'http://maven.apache.org/POM/4.0.0'}
                
                # Find all dependencies
                for dependency in root.findall(".//maven:dependencies/maven:dependency", namespace):
                    group_id = dependency.find("maven:groupId", namespace)
                    artifact_id = dependency.find("maven:artifactId", namespace)
                    version = dependency.find("maven:version", namespace)
                    
                    if group_id is not None and artifact_id is not None:
                        group_id_text = group_id.text
                        artifact_id_text = artifact_id.text
                        version_text = version.text if version is not None else "unspecified"
                        
                        dep_key = f"{group_id_text}:{artifact_id_text}"
                        build_dependencies.append({
                            "group": group_id_text,
                            "artifact": artifact_id_text,
                            "version": version_text
                        })
                        
                        # Count external dependencies by group
                        if not (group_id_text.startswith("com.internal") or group_id_text.startswith("org.internal")):
                            external_dependencies[group_id_text] += 1
            except Exception as e:
                print(f"Error parsing {pom_file}: {str(e)}")
        
        # Analyze imports in Java files
        for java_file in self.java_files:
            with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Find all imports
            import_pattern = re.compile(r'^import\s+([\w.]+);', re.MULTILINE)
            imports = import_pattern.findall(content)
            
            for imp in imports:
                import_counts[imp] += 1
                
                # Classify as internal or external
                top_level_package = imp.split('.')[0]
                if top_level_package in ['java', 'javax', 'jakarta']:
                    # Standard Java imports
                    continue
                elif top_level_package in ['com', 'org', 'io', 'net']:
                    # External dependencies (simplified - in reality would need better heuristics)
                    external_dependencies[imp.split('.')[0] + '.' + imp.split('.')[1]] += 1
                else:
                    # Assume internal project dependencies
                    internal_dependencies[top_level_package] += 1
                
                dependency_list.append(imp)
        
        # Calculate unique dependencies to avoid counting duplicate imports
        unique_imports = len(import_counts)
        self.complexity_metrics["dependency_count"] = unique_imports
        
        return {
            "total_imports": sum(import_counts.values()),
            "unique_imports": unique_imports,
            "build_dependencies": build_dependencies,
            "top_external_dependencies": dict(sorted(external_dependencies.items(), key=lambda x: x[1], reverse=True)[:10]),
            "internal_dependencies": dict(internal_dependencies),
            "external_dependency_count": sum(external_dependencies.values()),
            "internal_dependency_count": sum(internal_dependencies.values()),
            "dependency_ratio": round(sum(external_dependencies.values()) / max(1, sum(internal_dependencies.values())), 2),
            "most_common_imports": dict(import_counts.most_common(10))
        }
    
    def analyze_loc(self):
        """Calculate total lines of code"""
        total_loc = 0
        code_loc = 0
        comment_loc = 0
        blank_loc = 0
        file_loc = {}
        
        for java_file in self.java_files:
            file_lines = 0
            file_code_lines = 0
            file_comment_lines = 0
            file_blank_lines = 0
            in_comment = False
            
            with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    total_loc += 1
                    file_lines += 1
                    
                    if in_comment:
                        # Inside a multi-line comment
                        comment_loc += 1
                        file_comment_lines += 1
                        if "*/" in line:
                            in_comment = False
                    elif line.startswith("/*") or line.startswith("/**"):
                        # Start of a multi-line comment
                        comment_loc += 1
                        file_comment_lines += 1
                        if not line.endswith("*/"):
                            in_comment = True
                    elif line.startswith("//"):
                        # Single-line comment
                        comment_loc += 1
                        file_comment_lines += 1
                    elif line == "":
                        # Blank line
                        blank_loc += 1
                        file_blank_lines += 1
                    else:
                        # Code line
                        code_loc += 1
                        file_code_lines += 1
            
            file_loc[os.path.relpath(java_file, self.project_path)] = {
                "total": file_lines,
                "code": file_code_lines,
                "comments": file_comment_lines,
                "blank": file_blank_lines
            }
        
        self.complexity_metrics["total_loc"] = total_loc
        
        return {
            "total_loc": total_loc,
            "code_loc": code_loc,
            "comment_loc": comment_loc,
            "blank_loc": blank_loc,
            "code_to_comment_ratio": round(code_loc / max(1, comment_loc), 2),
            "largest_files": sorted(file_loc.items(), key=lambda x: x[1]["code"], reverse=True)[:10]
        }
    
    def analyze_config_complexity(self):
        """Analyze configuration complexity"""
        config_file_count = 0
        total_config_lines = 0
        config_complexity_score = 0
        config_files_by_type = defaultdict(int)
        largest_config_files = []
        
        # Look for configuration files
        config_extensions = ['.xml', '.properties', '.yml', '.yaml', '.json', '.conf', '.config', '.ini']
        
        for root, _, filenames in os.walk(self.project_path):
            for filename in filenames:
                file_path = os.path.join(root, filename)
                file_ext = os.path.splitext(filename)[1].lower()
                
                if file_ext in config_extensions:
                    config_file_count += 1
                    config_files_by_type[file_ext] += 1
                    
                    # Count lines in config file
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            line_count = len(lines)
                            total_config_lines += line_count
                            
                            largest_config_files.append({
                                "file": os.path.relpath(file_path, self.project_path),
                                "lines": line_count
                            })
                            
                            # Add complexity based on config file size
                            if line_count > 500:
                                config_complexity_score += 5
                            elif line_count > 200:
                                config_complexity_score += 3
                            elif line_count > 100:
                                config_complexity_score += 2
                            else:
                                config_complexity_score += 1
                    except Exception as e:
                        print(f"Error reading {file_path}: {str(e)}")
                
                # Special handling for specific config files
                if filename == "pom.xml":
                    try:
                        tree = ET.parse(file_path)
                        root_elem = tree.getroot()  # Changed variable name from 'root' to 'root_elem'
                        
                        # Count plugins as a complexity factor
                        namespace = {'maven': 'http://maven.apache.org/POM/4.0.0'}
                        plugins = root_elem.findall(".//maven:plugins/maven:plugin", namespace)
                        config_complexity_score += len(plugins)
                        
                        # Count profiles as a complexity factor
                        profiles = root_elem.findall(".//maven:profiles/maven:profile", namespace)
                        config_complexity_score += len(profiles) * 2
                    except Exception as e:
                        print(f"Error parsing {file_path}: {str(e)}")
        
        # Normalize configuration complexity score
        normalized_config_complexity = min(100, config_complexity_score)
        self.complexity_metrics["config_complexity"] = normalized_config_complexity
        
        return {
            "config_file_count": config_file_count,
            "config_files_by_type": dict(config_files_by_type),
            "total_config_lines": total_config_lines,
            "config_complexity_score": normalized_config_complexity,
            "largest_config_files": sorted(largest_config_files, key=lambda x: x["lines"], reverse=True)[:10]
        }
    
    def calculate_overall_complexity(self):
        """Calculate overall complexity score with weighted metrics"""
        
        # Define weights for each metric
        weights = {
            "avg_method_length": 0.2,  # Higher is worse
            "avg_cyclomatic_complexity": 0.3,  # Higher is worse
            "dependency_count": 0.2,  # Higher is worse
            "total_loc": 0.15,  # Higher is worse
            "config_complexity": 0.15  # Higher is worse
        }
        
        # Normalize metrics to 0-100 scale (higher = more complex = worse)
        normalized_metrics = {
            "avg_method_length": min(100, (self.complexity_metrics["avg_method_length"] / 20) * 100),
            "avg_cyclomatic_complexity": min(100, (self.complexity_metrics["avg_cyclomatic_complexity"] / 10) * 100),
            "dependency_count": min(100, (self.complexity_metrics["dependency_count"] / 100) * 100),
            "total_loc": min(100, (self.complexity_metrics["total_loc"] / 10000) * 100),
            "config_complexity": self.complexity_metrics["config_complexity"]  # Already normalized
        }
        
        # Calculate weighted score (0-100, where lower is better)
        overall_score = sum(normalized_metrics[metric] * weights[metric] for metric in weights)
        self.complexity_metrics["overall_complexity_score"] = round(overall_score, 2)
        
        return {
            "normalized_metrics": normalized_metrics,
            "overall_complexity_score": self.complexity_metrics["overall_complexity_score"]
        }
    
    def analyze(self):
        """Run the full complexity analysis"""
        print("Starting complexity analysis...")
        
        print("Finding files...")
        file_stats = self.find_files()
        print(f"Found {file_stats['java_files_count']} Java files and {file_stats['xml_files_count']} XML files")
        
        print("Analyzing method complexity...")
        method_results = self.analyze_method_complexity()
        
        print("Analyzing dependencies...")
        dependency_results = self.analyze_dependencies()
        
        print("Analyzing lines of code...")
        loc_results = self.analyze_loc()
        
        print("Analyzing configuration complexity...")
        config_results = self.analyze_config_complexity()
        
        print("Calculating overall complexity score...")
        overall_results = self.calculate_overall_complexity()
        
        self.results = {
            "metrics": self.complexity_metrics,
            "file_stats": file_stats,
            "method_complexity": method_results,
            "dependencies": dependency_results,
            "lines_of_code": loc_results,
            "config_complexity": config_results,
            "overall_complexity": overall_results
        }
        
        return self.results
    
    def generate_report(self):
        """Generate a formatted report of the complexity analysis"""
        if not self.results:
            self.analyze()
        
        complexity_level = "Low"
        if self.complexity_metrics["overall_complexity_score"] > 70:
            complexity_level = "High"
        elif self.complexity_metrics["overall_complexity_score"] > 40:
            complexity_level = "Medium"
        
        report = f"""
Code Complexity Analysis Report
==============================

Overall Complexity Score: {self.complexity_metrics['overall_complexity_score']}/100 ({complexity_level} Complexity)

Metrics Breakdown:
-----------------
Average Method Length: {self.complexity_metrics['avg_method_length']} lines
Average Cyclomatic Complexity: {self.complexity_metrics['avg_cyclomatic_complexity']}
Dependency Count: {self.complexity_metrics['dependency_count']} unique imports
Total Lines of Code: {self.complexity_metrics['total_loc']}
Configuration Complexity: {self.complexity_metrics['config_complexity']}/100

Method Complexity:
-----------------
- Total Methods Analyzed: {self.results['method_complexity']['total_methods']}
- Methods > 30 lines: {len(self.results['method_complexity']['long_methods'])}
- Methods with complexity > 10: {len(self.results['method_complexity']['complex_methods'])}

Dependencies:
------------
- External Dependencies: {self.results['dependencies']['external_dependency_count']}
- Internal Dependencies: {self.results['dependencies']['internal_dependency_count']}
- Dependency Ratio (External/Internal): {self.results['dependencies']['dependency_ratio']}

Code Size:
---------
- Code Lines: {self.results['lines_of_code']['code_loc']}
- Comment Lines: {self.results['lines_of_code']['comment_loc']}
- Blank Lines: {self.results['lines_of_code']['blank_loc']}
- Code to Comment Ratio: {self.results['lines_of_code']['code_to_comment_ratio']}

Configuration:
-------------
- Config Files: {self.results['config_complexity']['config_file_count']}
- Total Config Lines: {self.results['config_complexity']['total_config_lines']}

Top Issues:
----------
"""
        # Generate top issues based on scores
        if self.complexity_metrics['avg_method_length'] > 20:
            report += "- Methods are too long (avg > 20 lines)\n"
            report += f"  Top offenders:\n"
            for method in self.results['method_complexity']['long_methods'][:3]:
                report += f"  * {method['file']} - {method['method']}: {method['length']} lines\n"
        
        if self.complexity_metrics['avg_cyclomatic_complexity'] > 5:
            report += "- High cyclomatic complexity (avg > 5)\n"
            report += f"  Top offenders:\n"
            for method in self.results['method_complexity']['complex_methods'][:3]:
                report += f"  * {method['file']} - {method['method']}: complexity {method['complexity']}\n"
        
        if self.complexity_metrics['dependency_count'] > 50:
            report += "- Too many dependencies (> 50 unique imports)\n"
            report += f"  Most common external dependencies:\n"
            for dep, count in list(self.results['dependencies']['top_external_dependencies'].items())[:3]:
                report += f"  * {dep}: {count} usages\n"
        
        if self.complexity_metrics['config_complexity'] > 50:
            report += "- High configuration complexity\n"
            report += f"  Largest config files:\n"
            for config in self.results['config_complexity']['largest_config_files'][:3]:
                report += f"  * {config['file']}: {config['lines']} lines\n"
        
        report += f"""
Recommendations:
--------------
"""
        # Generate recommendations based on scores
        if self.complexity_metrics['avg_method_length'] > 20:
            report += "- Refactor long methods into smaller, more focused methods\n"
        if self.complexity_metrics['avg_cyclomatic_complexity'] > 5:
            report += "- Reduce complexity by simplifying conditional logic and extracting methods\n"
        if self.complexity_metrics['dependency_count'] > 50:
            report += "- Review and reduce external dependencies; consolidate similar libraries\n"
        if self.results['dependencies']['dependency_ratio'] > 2:
            report += "- Heavy reliance on external code; consider internalizing critical functionality\n"
        if self.complexity_metrics['config_complexity'] > 50:
            report += "- Simplify configuration files; consider breaking into smaller, focused configs\n"
        
        return report

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze Java project code complexity')
    parser.add_argument('project_path', help='Path to the Java project directory')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--output', help='Output file path for the report')
    parser.add_argument('--history', help='Path to historical complexity data for trend analysis')
    
    args = parser.parse_args()
    
    analyzer = ComplexityAnalyzer(args.project_path)
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
        
        # Save history data for future trend analysis
        if args.history:
            try:
                # Load existing history
                history_data = []
                if os.path.exists(args.history):
                    with open(args.history, 'r') as f:
                        history_data = json.load(f)
                
                # Add current results with timestamp
                from datetime import datetime
                history_entry = {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "metrics": analyzer.complexity_metrics
                }
                history_data.append(history_entry)
                
                # Save updated history
                with open(args.history, 'w') as f:
                    json.dump(history_data, f, indent=2)
                
                print(f"\nComplexity history saved to {args.history}")
            except Exception as e:
                print(f"Error saving history data: {str(e)}")

if __name__ == "__main__":
    main()
