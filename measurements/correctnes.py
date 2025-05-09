import os
import re
import json
import fnmatch
import subprocess
import xml.etree.ElementTree as ET
from collections import defaultdict

class CorrectnessAnalyzer:
    def __init__(self, project_path):
        self.project_path = project_path
        self.java_files = []
        self.test_files = []
        self.metrics = {
            "code_coverage": 0,
            "critical_path_coverage": 0,
            "total_tests": 0,
            "passing_tests": 0,
            "failing_tests": 0,
            "data_store_test_coverage": 0,
            "overall_score": 0
        }
        
    def find_files(self):
        """Find Java source and test files"""
        for root, _, filenames in os.walk(self.project_path):
            for filename in fnmatch.filter(filenames, "*.java"):
                path = os.path.join(root, filename)
                if 'test' in path.lower() and not 'main' in path.lower():
                    self.test_files.append(path)
                else:
                    self.java_files.append(path)
        
        return len(self.java_files), len(self.test_files)
    
    def analyze_code_coverage(self):
        """Analyze code coverage from JaCoCo reports"""
        coverage_data = {"overall": 0, "by_package": {}}
        
        # Look for JaCoCo reports in more locations
        jacoco_paths = [
            os.path.join(self.project_path, "target/site/jacoco/jacoco.xml"),
            os.path.join(self.project_path, "build/reports/jacoco/test/jacocoTestReport.xml"),
            os.path.join(self.project_path, "target/coverage-reports/jacoco-ut/jacoco.xml"),
            os.path.join(self.project_path, "target/coverage-reports/jacoco-it/jacoco.xml")
        ]
        
        # Also directly check for the exec file and try to generate a report if needed
        jacoco_exec = os.path.join(self.project_path, "target/coverage-reports/jacoco-ut.exec")
        if os.path.exists(jacoco_exec) and not any(os.path.exists(path) for path in jacoco_paths):
            print(f"Found JaCoCo exec file at {jacoco_exec} but no XML report. Attempting to generate one...")
            try:
                # Create directory for report if it doesn't exist
                report_dir = os.path.join(self.project_path, "target/coverage-reports/jacoco-ut")
                os.makedirs(report_dir, exist_ok=True)
                
                # Try to generate a report from the exec file
                xml_report = os.path.join(report_dir, "jacoco.xml")
                cmd = [
                    "java", "-jar", os.path.expanduser("~/.m2/repository/org/jacoco/org.jacoco.cli/0.8.8/org.jacoco.cli-0.8.8-nodeps.jar"),
                    "report", jacoco_exec,
                    "--classfiles", os.path.join(self.project_path, "target/classes"),
                    "--xml", xml_report
                ]
                
                subprocess.run(cmd, capture_output=True, timeout=30)
                
                if os.path.exists(xml_report):
                    print(f"Successfully generated JaCoCo XML report at {xml_report}")
                    jacoco_paths.append(xml_report)
            except Exception as e:
                print(f"Error generating JaCoCo report: {str(e)}")
        
        # Check if there are any XML files in the jacoco-ut directory
        jacoco_ut_dir = os.path.join(self.project_path, "target/coverage-reports/jacoco-ut")
        if os.path.exists(jacoco_ut_dir):
            for file in os.listdir(jacoco_ut_dir):
                if file.endswith(".xml"):
                    xml_path = os.path.join(jacoco_ut_dir, file)
                    print(f"Found potential JaCoCo XML report: {xml_path}")
                    jacoco_paths.append(xml_path)
        
        for path in jacoco_paths:
            if os.path.exists(path):
                print(f"Analyzing coverage report: {path}")
                try:
                    tree = ET.parse(path)
                    root = tree.getroot()
                    
                    # Get coverage data from the report - try different approaches
                    # First try to get overall INSTRUCTION counter
                    total_covered = 0
                    total_missed = 0
                    
                    # Look for instruction counters at report level
                    for counter in root.findall(".//counter[@type='INSTRUCTION']"):
                        covered = int(counter.get("covered", 0))
                        missed = int(counter.get("missed", 0))
                        total_covered += covered
                        total_missed += missed
                    
                    # Calculate overall coverage from all instructions
                    total_instructions = total_covered + total_missed
                    if total_instructions > 0:
                        overall_coverage = (total_covered / total_instructions) * 100
                        coverage_data["overall"] = round(overall_coverage, 2)
                        print(f"Calculated actual coverage: {coverage_data['overall']}% ({total_covered} covered out of {total_instructions} instructions)")
                    
                    # If no overall coverage found, fall back to original method with LINE counters
                    if coverage_data["overall"] == 0:
                        # Try line coverage
                        for counter in root.findall(".//counter[@type='LINE']"):
                            covered = int(counter.get("covered", 0))
                            missed = int(counter.get("missed", 0))
                            total = covered + missed
                            if total > 0:
                                coverage_data["overall"] = round(covered / total * 100, 2)
                                break
                    
                    # Get coverage by package
                    for package in root.findall(".//package"):
                        pkg_name = package.get("name", "default")
                        package_covered = 0
                        package_missed = 0
                        
                        # Sum up instruction counters for package
                        for counter in package.findall("counter[@type='INSTRUCTION']"):
                            covered = int(counter.get("covered", 0))
                            missed = int(counter.get("missed", 0))
                            package_covered += covered
                            package_missed += missed
                        
                        package_total = package_covered + package_missed
                        if package_total > 0:
                            package_coverage = (package_covered / package_total) * 100
                            coverage_data["by_package"][pkg_name] = round(package_coverage, 2)
                    
                    # Estimate critical path coverage
                    critical_paths = [pkg for pkg in coverage_data["by_package"] 
                                     if any(x in pkg.lower() for x in ['service', 'controller', 'api'])]
                    if critical_paths:
                        critical_coverage = sum(coverage_data["by_package"][pkg] for pkg in critical_paths) / len(critical_paths)
                        coverage_data["critical_paths"] = round(critical_coverage, 2)
                    else:
                        coverage_data["critical_paths"] = coverage_data["overall"]
                    
                    self.metrics["code_coverage"] = coverage_data["overall"]
                    self.metrics["critical_path_coverage"] = coverage_data["critical_paths"]
                    
                    print(f"Found coverage data: {coverage_data['overall']}% overall")
                    
                    # Don't just return 0% coverage - that triggers the estimation logic
                    if self.metrics["code_coverage"] < 1 and total_covered > 0:
                        # If we have any coverage at all, report at least 1%
                        self.metrics["code_coverage"] = 1.0
                        
                    return coverage_data
                except Exception as e:
                    print(f"Error parsing coverage report {path}: {str(e)}")
        
        # If we've reached here, we couldn't find or parse any coverage reports
        
        # Let's check if the exec file exists but we couldn't process it
        if os.path.exists(jacoco_exec):
            print(f"Found JaCoCo exec file at {jacoco_exec} but couldn't process it into usable coverage data.")
            print("You may need to install JaCoCo CLI tools to generate reports.")
            
            # Provide a fallback estimate based on test counts
            if self.metrics["total_tests"] > 0:
                estimated_coverage = min(40, max(10, self.metrics["total_tests"] / max(1, len(self.java_files)) * 30))
                print(f"Estimating coverage at approximately {estimated_coverage}% based on test count.")
                self.metrics["code_coverage"] = estimated_coverage
                self.metrics["critical_path_coverage"] = estimated_coverage
                self.metrics["coverage_estimated"] = True
                
                coverage_data["overall"] = estimated_coverage
                coverage_data["critical_paths"] = estimated_coverage
                coverage_data["estimated"] = True
                
                return coverage_data
        
        print("No coverage data found. Consider adding JaCoCo to your project.")
        return coverage_data
    
    def analyze_tests(self):
        """Analyze test results and types"""
        test_results = {"total": 0, "passed": 0, "failed": 0, "skipped": 0}
        test_types = {"unit": 0, "integration": 0, "data_store": 0, "arquillian": 0}
        
        # Look for test reports in multiple locations
        report_dirs = [
            os.path.join(self.project_path, "target/surefire-reports"),
            os.path.join(self.project_path, "target/failsafe-reports"),
            os.path.join(self.project_path, "build/test-results"),
            os.path.join(self.project_path, "build/reports/tests"),
            os.path.join(self.project_path, "target/arquillian-results")  # Common Arquillian output
        ]
        
        for report_dir in report_dirs:
            if os.path.exists(report_dir):
                print(f"Found test reports in {report_dir}")
                for file in os.listdir(report_dir):
                    if file.endswith(".xml") and (file.startswith("TEST-") or file.startswith("Arquillian")):
                        try:
                            tree = ET.parse(os.path.join(report_dir, file))
                            root = tree.getroot()
                            
                            # Count test results
                            tests = int(root.get("tests", 0))
                            failures = int(root.get("failures", 0))
                            errors = int(root.get("errors", 0))
                            skipped = int(root.get("skipped", 0))
                            
                            test_results["total"] += tests
                            test_results["failed"] += failures + errors
                            test_results["skipped"] += skipped
                            test_results["passed"] += tests - failures - errors - skipped
                        except Exception as e:
                            print(f"Error parsing test report {file}: {str(e)}")
        
        # Add specific detection for Arquillian tests
        arquillian_detected = False
        for test_file in self.test_files:
            try:
                with open(test_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    if 'org.jboss.arquillian' in content or '@RunWith(Arquillian.class)' in content:
                        arquillian_detected = True
                        test_types["arquillian"] += 1
                        # Also categorize by type
                        if any(x in content for x in ['Repository', 'EntityManager', 'jdbc', 'sql']):
                            test_types["data_store"] += 1
                        else:
                            test_types["integration"] += 1
                    else:
                        # Process as before for non-Arquillian tests
                        file_name = os.path.basename(test_file)
                        if 'IT.java' in file_name or 'Integration' in file_name:
                            test_types["integration"] += 1
                        elif any(x in file_name for x in ['Repository', 'DAO', 'Data']):
                            test_types["data_store"] += 1
                        else:
                            test_types["unit"] += 1
                            
                        # Check content for data store tests
                        if test_types["data_store"] == 0 and re.search(r'Repository|EntityManager|DataSource|jdbc|sql', content):
                            test_types["data_store"] += 1
                            if test_types["unit"] > 0:  # Avoid negative values
                                test_types["unit"] -= 1
            except Exception as e:
                print(f"Error analyzing test file {test_file}: {str(e)}")
        
        # If Arquillian detected but no test results, we may need manual testing
        if arquillian_detected and test_results["total"] == 0:
            print("Arquillian tests detected but no test reports found.")
            print("Arquillian tests typically need to be run with a running server.")
            print("Try running: mvn verify -Parq-remote")
        
        # Calculate data store test coverage
        if self.test_files:
            self.metrics["data_store_test_coverage"] = min(100, round(test_types["data_store"] / len(self.test_files) * 100, 2))
        
        self.metrics["total_tests"] = test_results["total"]
        self.metrics["passing_tests"] = test_results["passed"]
        self.metrics["failing_tests"] = test_results["failed"]
        
        return test_results, test_types
    
    def calculate_score(self):
        """Calculate overall correctness score"""
        weights = {
            "code_coverage": 0.35,
            "critical_path_coverage": 0.25,
            "test_pass_rate": 0.25,
            "data_store_coverage": 0.15
        }
        
        # Calculate test pass rate
        pass_rate = 0
        if self.metrics["total_tests"] > 0:
            pass_rate = (self.metrics["passing_tests"] / self.metrics["total_tests"]) * 100
        
        # Round low coverage values to avoid showing "0.0%" when there is actually some coverage
        if 0 < self.metrics["code_coverage"] < 1:
            self.metrics["code_coverage"] = 1.0
        
        if 0 < self.metrics["critical_path_coverage"] < 1:
            self.metrics["critical_path_coverage"] = 1.0
            
        # Adjust if we have tests but no coverage data (common with Arquillian)
        if self.metrics["total_tests"] > 0 and self.metrics["code_coverage"] == 0:
            # Estimate coverage based on test count relative to code size
            estimated_coverage = min(40, max(10, self.metrics["total_tests"] / max(1, len(self.java_files)) * 30))
            print(f"Estimating coverage at approximately {estimated_coverage}% based on test count.")
            self.metrics["code_coverage"] = estimated_coverage
            self.metrics["critical_path_coverage"] = estimated_coverage
            self.metrics["coverage_estimated"] = True
        
        # Calculate weighted score
        score = (
            self.metrics["code_coverage"] * weights["code_coverage"] +
            self.metrics["critical_path_coverage"] * weights["critical_path_coverage"] +
            pass_rate * weights["test_pass_rate"] +
            self.metrics["data_store_test_coverage"] * weights["data_store_coverage"]
        )
        
        self.metrics["overall_score"] = round(score, 2)
        
        # Determine grade
        grade = "F"
        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
            
        return {
            "score": self.metrics["overall_score"],
            "grade": grade
        }
    
    def check_test_framework(self):
        """Check if test frameworks are present"""
        frameworks = {
            "junit": False,
            "mockito": False,
            "jacoco": False,
            "arquillian": False,
            "missing": []
        }
        
        # Check pom.xml
        pom_path = os.path.join(self.project_path, "pom.xml")
        if os.path.exists(pom_path):
            try:
                with open(pom_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    frameworks["junit"] = "junit" in content or "junit-jupiter" in content
                    frameworks["mockito"] = "mockito" in content
                    frameworks["jacoco"] = "jacoco" in content
                    frameworks["arquillian"] = "arquillian" in content
            except Exception:
                pass
        
        # Also check test files directly for imports
        for test_file in self.test_files:
            try:
                with open(test_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    frameworks["junit"] |= "org.junit" in content
                    frameworks["mockito"] |= "org.mockito" in content
                    frameworks["arquillian"] |= "org.jboss.arquillian" in content
            except Exception:
                pass
        
        # Generate list of missing frameworks
        if not (frameworks["junit"] or frameworks["arquillian"]):
            frameworks["missing"].append("JUnit")
        if not frameworks["mockito"]:
            frameworks["missing"].append("Mockito")
        if not frameworks["jacoco"]:
            frameworks["missing"].append("JaCoCo")
        
        return frameworks
    
    def analyze(self):
        """Run the complete analysis"""
        print("Analyzing code correctness...")
        
        src_count, test_count = self.find_files()
        print(f"Found {src_count} source files and {test_count} test files")
        
        coverage_data = self.analyze_code_coverage()
        test_results, test_types = self.analyze_tests()
        frameworks = self.check_test_framework()
        score_data = self.calculate_score()
        
        # Generate report
        report = {
            "metrics": self.metrics,
            "coverage": coverage_data,
            "tests": test_results,
            "test_types": test_types,
            "frameworks": frameworks,
            "score": score_data
        }
        
        return report
    
    def generate_report(self):
        """Generate a human-readable report"""
        report = self.analyze()
        
        output = f"""
Correctness Analysis Report
==========================

Overall Score: {report['score']['score']}/100 (Grade: {report['score']['grade']})

Test Metrics:
------------
"""
        if self.metrics.get("coverage_estimated", False):
            output += f"Code Coverage: {self.metrics['code_coverage']}% (ESTIMATED - actual coverage data not available)\n"
            output += f"Critical Path Coverage: {self.metrics['critical_path_coverage']}% (ESTIMATED)\n"
        else:
            output += f"Code Coverage: {self.metrics['code_coverage']}%\n"
            output += f"Critical Path Coverage: {self.metrics['critical_path_coverage']}%\n"
        
        output += f"""Total Tests: {self.metrics['total_tests']}
Passing Tests: {self.metrics['passing_tests']} ({round(self.metrics['passing_tests']/max(1, self.metrics['total_tests'])*100)}%)
Failing Tests: {self.metrics['failing_tests']}
Data Store Test Coverage: {self.metrics['data_store_test_coverage']}%

Test Framework Status:
--------------------
"""
        if report['frameworks']['missing']:
            output += f"Missing frameworks: {', '.join(report['frameworks']['missing'])}\n"
            output += "\nRecommendations:\n"
            
            if "JUnit" in report['frameworks']['missing']:
                output += "- Add JUnit to your project for unit testing\n"
            if "Mockito" in report['frameworks']['missing']:
                output += "- Add Mockito for mocking dependencies in tests\n"
            if "JaCoCo" in report['frameworks']['missing']:
                output += "- Add JaCoCo for code coverage analysis\n"
        else:
            output += "All key testing frameworks are present\n"
            
        if self.metrics['code_coverage'] < 70:
            output += "\nImprovement Areas:\n"
            output += f"- Increase code coverage (currently {self.metrics['code_coverage']}%, aim for 70%+)\n"
            
        if self.metrics['critical_path_coverage'] < 80:
            output += f"- Focus on testing critical paths (currently {self.metrics['critical_path_coverage']}%, aim for 80%+)\n"
            
        if self.metrics['data_store_test_coverage'] < 50:
            output += f"- Add more data store tests (currently {self.metrics['data_store_test_coverage']}%)\n"
            
        return output

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze Java project correctness')
    parser.add_argument('project_path', help='Path to the Java project directory')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--output', help='Output file path for the report')
    
    args = parser.parse_args()
    
    analyzer = CorrectnessAnalyzer(args.project_path)
    
    if args.json:
        result = json.dumps(analyzer.analyze(), indent=2)
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