import os
import re
import json
import fnmatch
import subprocess
import datetime
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

class SecurityAnalyzer:
    def __init__(self, project_path):
        self.project_path = project_path
        self.java_files = []
        self.xml_files = []
        self.security_metrics = {
            "outdated_dependencies": 0,
            "vulnerable_dependencies": 0,
            "critical_vulnerabilities": 0,
            "high_vulnerabilities": 0,
            "medium_vulnerabilities": 0,
            "low_vulnerabilities": 0,
            "static_analysis_findings": 0,
            "overall_security_score": 0
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
    
    def analyze_outdated_dependencies(self):
        """Check for outdated Maven dependencies"""
        outdated_dependencies = []
        pom_files = [f for f in self.xml_files if f.endswith("pom.xml")]
        
        if not pom_files:
            print("No pom.xml files found, skipping dependency analysis")
            return {
                "outdated_count": 0,
                "outdated_dependencies": []
            }
        
        try:
            # Run Maven versions plugin to check for updates
            # Note: This requires Maven to be installed
            main_pom = pom_files[0]  # Use the first pom file found
            
            command = ["mvn", "versions:display-dependency-updates", "-f", main_pom]
            print(f"Running: {' '.join(command)}")
            
            try:
                result = subprocess.run(
                    command, 
                    capture_output=True, 
                    text=True, 
                    check=False,
                    timeout=120  # 2-minute timeout
                )
                output = result.stdout + result.stderr
            except subprocess.TimeoutExpired:
                print("Command timed out, using alternative method")
                output = ""
                
            # Parse the output to find outdated dependencies
            if output:
                version_pattern = re.compile(r'\[INFO\]\s+([^\s]+):([^\s]+)\s+([^\s]+)\s+->\s+([^\s]+)')
                matches = version_pattern.findall(output)
                
                for match in matches:
                    group_id, artifact_id, current_version, latest_version = match
                    outdated_dependencies.append({
                        "group": group_id,
                        "artifact": artifact_id,
                        "current_version": current_version,
                        "latest_version": latest_version
                    })
            
            # If Maven command failed or timed out, fall back to manual parsing
            if not outdated_dependencies:
                print("Using manual parsing for dependencies")
                all_dependencies = self.extract_dependencies_from_pom(main_pom)
                # We'll mark dependencies as potentially outdated if they use old version patterns
                # This is not as accurate as the Maven plugin but provides a fallback
                for dep in all_dependencies:
                    version = dep.get("version", "")
                    # Check for old version patterns or fixed versions (not using properties)
                    if re.match(r'^\d+\.\d+\.\d+$', version) and not version.startswith("999"):
                        parts = version.split('.')
                        if len(parts) >= 3:
                            if int(parts[0]) < 2 and int(parts[1]) < 5:  # Simple heuristic
                                outdated_dependencies.append({
                                    "group": dep.get("group", "unknown"),
                                    "artifact": dep.get("artifact", "unknown"),
                                    "current_version": version,
                                    "latest_version": "unknown (potentially outdated)",
                                    "confidence": "low"
                                })
        
        except Exception as e:
            print(f"Error analyzing dependencies: {str(e)}")
        
        self.security_metrics["outdated_dependencies"] = len(outdated_dependencies)
        
        return {
            "outdated_count": len(outdated_dependencies),
            "outdated_dependencies": outdated_dependencies
        }
    
    def extract_dependencies_from_pom(self, pom_file):
        """Extract dependencies from a pom.xml file"""
        dependencies = []
        try:
            tree = ET.parse(pom_file)
            root_elem = tree.getroot()
            
            # Handle namespaces in Maven POM files
            namespace = {'maven': 'http://maven.apache.org/POM/4.0.0'}
            
            # Find all dependencies
            for dependency in root_elem.findall(".//maven:dependencies/maven:dependency", namespace):
                group_id = dependency.find("maven:groupId", namespace)
                artifact_id = dependency.find("maven:artifactId", namespace)
                version = dependency.find("maven:version", namespace)
                
                if group_id is not None and artifact_id is not None:
                    group_id_text = group_id.text
                    artifact_id_text = artifact_id.text
                    version_text = version.text if version is not None else "unspecified"
                    
                    dependencies.append({
                        "group": group_id_text,
                        "artifact": artifact_id_text,
                        "version": version_text
                    })
        except Exception as e:
            print(f"Error parsing {pom_file}: {str(e)}")
        
        return dependencies
    
    def analyze_owasp_dependency_check(self):
        """Run OWASP Dependency Check or parse existing reports"""
        vulnerabilities = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "total": 0
        }
        vulnerable_dependencies = []
        
        # Check if a Dependency Check report exists
        report_paths = [
            os.path.join(self.project_path, "target/dependency-check-report.xml"),
            os.path.join(self.project_path, "build/reports/dependency-check-report.xml"),
            os.path.join(self.project_path, "dependency-check-report.xml")
        ]
        
        report_file = None
        for path in report_paths:
            if os.path.exists(path):
                report_file = path
                break
        
        if report_file:
            # Parse existing report
            try:
                tree = ET.parse(report_file)
                root = tree.getroot()
                
                # Extract vulnerability counts
                for dependency in root.findall(".//dependency"):
                    has_vulnerabilities = False
                    dep_name = dependency.find("fileName").text if dependency.find("fileName") is not None else "Unknown"
                    
                    vulnerabilities_elem = dependency.find("vulnerabilities")
                    if vulnerabilities_elem is not None:
                        vuln_list = []
                        
                        for vulnerability in vulnerabilities_elem.findall("vulnerability"):
                            has_vulnerabilities = True
                            severity = vulnerability.find("severity")
                            severity_text = severity.text if severity is not None else "unknown"
                            
                            cve = vulnerability.find("name")
                            cve_text = cve.text if cve is not None else "Unknown"
                            
                            if severity_text.lower() == "critical":
                                vulnerabilities["critical"] += 1
                            elif severity_text.lower() == "high":
                                vulnerabilities["high"] += 1
                            elif severity_text.lower() == "medium":
                                vulnerabilities["medium"] += 1
                            elif severity_text.lower() == "low":
                                vulnerabilities["low"] += 1
                            
                            vuln_list.append({
                                "cve": cve_text,
                                "severity": severity_text
                            })
                        
                        if has_vulnerabilities:
                            vulnerable_dependencies.append({
                                "name": dep_name,
                                "vulnerabilities": vuln_list
                            })
            except Exception as e:
                print(f"Error parsing OWASP report: {str(e)}")
        else:
            # No report found, try to run the check (requires OWASP Dependency Check to be installed)
            print("No OWASP Dependency Check report found, checking if we can run the tool...")
            
            try:
                # Check if dependency-check script is available
                check_cmd = ["dependency-check", "--version"]
                try:
                    subprocess.run(check_cmd, capture_output=True, check=False)
                    
                    # Run Dependency Check
                    output_file = os.path.join(self.project_path, "dependency-check-report.xml")
                    dc_cmd = [
                        "dependency-check",
                        "--project", "Security Analysis",
                        "--scan", self.project_path,
                        "--out", output_file,
                        "--format", "XML"
                    ]
                    print(f"Running: {' '.join(dc_cmd)}")
                    
                    try:
                        subprocess.run(dc_cmd, capture_output=True, check=False, timeout=300)  # 5-minute timeout
                        
                        # Now parse the report
                        if os.path.exists(output_file):
                            return self.analyze_owasp_dependency_check()  # Recursive call to parse the new report
                    except subprocess.TimeoutExpired:
                        print("OWASP Dependency Check timed out")
                except subprocess.CalledProcessError:
                    print("OWASP Dependency Check not installed")
                    
                    # Fall back to simple checks based on known vulnerable versions
                    pom_files = [f for f in self.xml_files if f.endswith("pom.xml")]
                    if pom_files:
                        dependencies = self.extract_dependencies_from_pom(pom_files[0])
                        
                        # Check for common known vulnerable libraries and versions
                        # This is a very simplified version and not a replacement for OWASP Dependency Check
                        vulnerable_patterns = [
                            {"group": "log4j", "pattern": r"^1\.", "severity": "high"},
                            {"group": "org.apache.logging.log4j", "pattern": r"^2\.[0-9]\.[0-9]$|^2\.1[0-6]", "severity": "critical"},
                            {"group": "commons-collections", "pattern": r"^3\.[0-2]", "severity": "high"},
                            {"group": "org.springframework", "pattern": r"^4\.[0-2]|^3\.|^2\.", "severity": "medium"},
                            {"group": "com.fasterxml.jackson.core", "pattern": r"^2\.[0-8]", "severity": "medium"}
                        ]
                        
                        for dep in dependencies:
                            for pattern in vulnerable_patterns:
                                if pattern["group"] in dep["group"] and re.match(pattern["pattern"], dep.get("version", "")):
                                    severity = pattern["severity"]
                                    vulnerabilities[severity] += 1
                                    
                                    vulnerable_dependencies.append({
                                        "name": f"{dep['group']}:{dep['artifact']}:{dep['version']}",
                                        "vulnerabilities": [{
                                            "cve": "Potential vulnerability (heuristic match)",
                                            "severity": severity
                                        }]
                                    })
            except Exception as e:
                print(f"Error running OWASP Dependency Check: {str(e)}")
        
        # Calculate total vulnerabilities
        vulnerabilities["total"] = (
            vulnerabilities["critical"] + 
            vulnerabilities["high"] + 
            vulnerabilities["medium"] + 
            vulnerabilities["low"]
        )
        
        # Update security metrics
        self.security_metrics["vulnerable_dependencies"] = len(vulnerable_dependencies)
        self.security_metrics["critical_vulnerabilities"] = vulnerabilities["critical"]
        self.security_metrics["high_vulnerabilities"] = vulnerabilities["high"]
        self.security_metrics["medium_vulnerabilities"] = vulnerabilities["medium"]
        self.security_metrics["low_vulnerabilities"] = vulnerabilities["low"]
        
        return {
            "vulnerabilities": vulnerabilities,
            "vulnerable_dependencies": vulnerable_dependencies,
            "report_file": report_file
        }
    
    def analyze_static_code_security(self):
        """Perform static code analysis for security issues"""
        findings = []
        security_patterns = [
            {
                "name": "Hardcoded credentials",
                "pattern": r'(?i)(password|passwd|pwd|secret|key|token|auth)\s*=\s*["\'][^"\']+["\']',
                "severity": "high"
            },
            {
                "name": "SQL Injection vulnerability",
                "pattern": r'(?i)executeQuery\(\s*"[^"]*\+|executeUpdate\(\s*"[^"]*\+|createStatement\([^)]*\)\.execute\(\s*"[^"]*\+',
                "severity": "high"
            },
            {
                "name": "Potential XSS vulnerability",
                "pattern": r'\.getRawValue\(\)|\.getInputStream\(\)|\.getReader\(\)|request\.getParameter\([^)]+\)',
                "severity": "medium"
            },
            {
                "name": "Insecure random",
                "pattern": r'new Random\(\)|Math\.random\(\)',
                "severity": "medium"
            },
            {
                "name": "Path traversal vulnerability",
                "pattern": r'new File\([^)]*getParameter\([^)]+\)\)',
                "severity": "high"
            },
            {
                "name": "Weak encryption",
                "pattern": r'(?i)(DES|MD5|SHA-1|SHA1|RC4)',
                "severity": "medium"
            },
            {
                "name": "Potential command injection",
                "pattern": r'Runtime\.getRuntime\(\)\.exec\(|ProcessBuilder\(',
                "severity": "high"
            },
            {
                "name": "Potential LDAP injection",
                "pattern": r'ldapTemplate\.search\(|ldapTemplate\.lookup\(',
                "severity": "high"
            },
            {
                "name": "Overly permissive CORS",
                "pattern": r'(?i)Access-Control-Allow-Origin["\'\s:=]+\*',
                "severity": "medium"
            },
            {
                "name": "Insecure SSL/TLS",
                "pattern": r'setHostnameVerifier\(.*ALLOW_ALL.*\)|SSLContext\.getInstance\("SSL"\)',
                "severity": "high"
            }
        ]
        
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }
        
        for java_file in self.java_files:
            with open(java_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            file_rel_path = os.path.relpath(java_file, self.project_path)
            
            for pattern_info in security_patterns:
                matches = re.finditer(pattern_info["pattern"], content)
                
                for match in matches:
                    line_number = content[:match.start()].count('\n') + 1
                    context_start = max(0, content.rfind('\n', 0, match.start()) + 1)
                    context_end = content.find('\n', match.end())
                    if context_end == -1:
                        context_end = len(content)
                    
                    context = content[context_start:context_end].strip()
                    
                    finding = {
                        "type": pattern_info["name"],
                        "severity": pattern_info["severity"],
                        "file": file_rel_path,
                        "line": line_number,
                        "code": context,
                        "description": f"Potential {pattern_info['name']} vulnerability detected"
                    }
                    findings.append(finding)
                    severity_counts[pattern_info["severity"]] += 1
        
        # Check for security configuration issues in Spring and other frameworks
        for xml_file in self.xml_files:
            with open(xml_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            file_rel_path = os.path.relpath(xml_file, self.project_path)
            
            # Check for insecure configurations
            if "web.xml" in xml_file:
                # Check if no security constraints
                if "<security-constraint>" not in content:
                    findings.append({
                        "type": "Missing security constraints",
                        "severity": "medium",
                        "file": file_rel_path,
                        "line": 1,
                        "code": "web.xml",
                        "description": "No security constraints found in web.xml"
                    })
                    severity_counts["medium"] += 1
            
            # Check for cleartext passwords in config files
            password_pattern = re.compile(r'(?i)(password|passwd|pwd|secret|key|token|auth)\s*=\s*["\'][^"\']+["\']')
            matches = password_pattern.finditer(content)
            
            for match in matches:
                line_number = content[:match.start()].count('\n') + 1
                context_start = max(0, content.rfind('\n', 0, match.start()) + 1)
                context_end = content.find('\n', match.end())
                if context_end == -1:
                    context_end = len(content)
                
                context = content[context_start:context_end].strip()
                
                findings.append({
                    "type": "Hardcoded credentials in config",
                    "severity": "high",
                    "file": file_rel_path,
                    "line": line_number,
                    "code": context,
                    "description": "Potential hardcoded credentials in configuration file"
                })
                severity_counts["high"] += 1
        
        total_findings = sum(severity_counts.values())
        self.security_metrics["static_analysis_findings"] = total_findings
        
        return {
            "total_findings": total_findings,
            "findings": findings,
            "severity_counts": severity_counts
        }
    
    def calculate_overall_security_score(self):
        """Calculate overall security score based on found issues"""
        # Start with a perfect score of 100
        score = 100
        
        # Deduct points for vulnerabilities based on severity
        vuln_deductions = {
            "critical_vulnerabilities": 10,  # Deduct 10 points per critical vulnerability
            "high_vulnerabilities": 5,      # Deduct 5 points per high vulnerability
            "medium_vulnerabilities": 2,    # Deduct 2 points per medium vulnerability
            "low_vulnerabilities": 0.5      # Deduct 0.5 points per low vulnerability
        }
        
        for metric, deduction in vuln_deductions.items():
            score -= self.security_metrics[metric] * deduction
        
        # Deduct for outdated dependencies
        score -= self.security_metrics["outdated_dependencies"] * 1  # 1 point per outdated dependency
        
        # Deduct for static analysis findings
        score -= self.security_metrics["static_analysis_findings"] * 2  # 2 points per finding
        
        # Ensure score doesn't go below 0
        score = max(0, score)
        
        self.security_metrics["overall_security_score"] = round(score, 1)
        
        # Determine security grade
        if score >= 90:
            grade = "A"
        elif score >= 80:
            grade = "B"
        elif score >= 70:
            grade = "C"
        elif score >= 60:
            grade = "D"
        else:
            grade = "F"
        
        return {
            "score": self.security_metrics["overall_security_score"],
            "grade": grade
        }
    
    def analyze(self):
        """Run the complete security analysis"""
        print("Starting security analysis...")
        
        print("Finding files...")
        file_stats = self.find_files()
        print(f"Found {file_stats['java_files_count']} Java files and {file_stats['xml_files_count']} XML files")
        
        print("Analyzing outdated dependencies...")
        dependency_results = self.analyze_outdated_dependencies()
        
        print("Running OWASP dependency check analysis...")
        owasp_results = self.analyze_owasp_dependency_check()
        
        print("Performing static code security analysis...")
        static_results = self.analyze_static_code_security()
        
        print("Calculating overall security score...")
        score_results = self.calculate_overall_security_score()
        
        self.results = {
            "metrics": self.security_metrics,
            "file_stats": file_stats,
            "outdated_dependencies": dependency_results,
            "owasp_check": owasp_results,
            "static_analysis": static_results,
            "security_score": score_results,
            "analysis_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        return self.results
    
    def generate_report(self):
        """Generate a formatted report of the security analysis"""
        if not self.results:
            self.analyze()
        
        report = f"""
Security Analysis Report
=======================
Analysis Date: {self.results['analysis_date']}

Overall Security Score: {self.results['security_score']['score']}/100 (Grade: {self.results['security_score']['grade']})

Security Metrics:
----------------
Outdated Dependencies: {self.security_metrics['outdated_dependencies']}
Vulnerable Dependencies: {self.security_metrics['vulnerable_dependencies']}
Security Vulnerabilities:
  - Critical: {self.security_metrics['critical_vulnerabilities']}
  - High: {self.security_metrics['high_vulnerabilities']}
  - Medium: {self.security_metrics['medium_vulnerabilities']}
  - Low: {self.security_metrics['low_vulnerabilities']}
Static Analysis Findings: {self.security_metrics['static_analysis_findings']}

Dependency Vulnerabilities:
-------------------------
"""
        if self.results['owasp_check']['vulnerable_dependencies']:
            for i, dep in enumerate(self.results['owasp_check']['vulnerable_dependencies'][:10], 1):  # Show top 10
                report += f"{i}. {dep['name']}\n"
                for vuln in dep['vulnerabilities'][:3]:  # Show top 3 vulns per dependency
                    report += f"   - {vuln['cve']} (Severity: {vuln['severity']})\n"
        else:
            report += "No vulnerable dependencies detected (or OWASP check not available)\n"
        
        report += "\nOutdated Dependencies:\n"
        report += "---------------------\n"
        if self.results['outdated_dependencies']['outdated_dependencies']:
            for i, dep in enumerate(self.results['outdated_dependencies']['outdated_dependencies'][:10], 1):  # Show top 10
                report += f"{i}. {dep['group']}:{dep['artifact']} - {dep['current_version']} -> {dep['latest_version']}\n"
        else:
            report += "No outdated dependencies detected\n"
        
        report += "\nStatic Analysis Security Findings:\n"
        report += "--------------------------------\n"
        if self.results['static_analysis']['findings']:
            by_severity = defaultdict(list)
            for finding in self.results['static_analysis']['findings']:
                by_severity[finding['severity']].append(finding)
            
            # Show findings ordered by severity
            for severity in ['critical', 'high', 'medium', 'low']:
                findings = by_severity.get(severity, [])
                if findings:
                    report += f"\n{severity.upper()} Severity Issues ({len(findings)}):\n"
                    for i, finding in enumerate(findings[:5], 1):  # Show top 5 per severity
                        report += f"{i}. {finding['type']} in {finding['file']}:{finding['line']}\n"
                        report += f"   Code: {finding['code'][:100]}{'...' if len(finding['code']) > 100 else ''}\n"
        else:
            report += "No security issues found in static analysis\n"
        
        report += f"""
Top Security Concerns:
-------------------
"""
        # Generate top concerns based on scores
        concerns = []
        
        if self.security_metrics['critical_vulnerabilities'] > 0:
            concerns.append(f"- Critical vulnerabilities: {self.security_metrics['critical_vulnerabilities']} found")
        
        if self.security_metrics['high_vulnerabilities'] > 0:
            concerns.append(f"- High vulnerabilities: {self.security_metrics['high_vulnerabilities']} found")
        
        high_severity_findings = sum(1 for f in self.results['static_analysis']['findings'] if f['severity'] == 'high')
        if high_severity_findings > 0:
            concerns.append(f"- High severity code issues: {high_severity_findings} found")
        
        if self.security_metrics['outdated_dependencies'] > 5:
            concerns.append(f"- Significant outdated dependencies: {self.security_metrics['outdated_dependencies']} found")
        
        if not concerns:
            concerns.append("- No major security concerns identified")
        
        for concern in concerns:
            report += concern + "\n"
        
        report += f"""
Recommendations:
--------------
"""
        # Generate recommendations based on findings
        if self.security_metrics['critical_vulnerabilities'] > 0 or self.security_metrics['high_vulnerabilities'] > 0:
            report += "- URGENT: Update dependencies with critical/high vulnerabilities immediately\n"
        
        if self.security_metrics['outdated_dependencies'] > 0:
            report += "- Update all outdated dependencies to latest stable versions\n"
        
        if any(f['type'] == 'Hardcoded credentials' for f in self.results['static_analysis']['findings']):
            report += "- Remove hardcoded credentials and use a secure credential store\n"
        
        if any(f['type'] == 'SQL Injection vulnerability' for f in self.results['static_analysis']['findings']):
            report += "- Fix SQL injection vulnerabilities by using parameterized queries\n"
        
        if any(f['type'] == 'Potential XSS vulnerability' for f in self.results['static_analysis']['findings']):
            report += "- Add input validation and output encoding to prevent XSS attacks\n"
        
        if any(f['type'] == 'Insecure random' for f in self.results['static_analysis']['findings']):
            report += "- Replace Math.random() with SecureRandom for security-sensitive operations\n"
        
        if any(f['type'] == 'Weak encryption' for f in self.results['static_analysis']['findings']):
            report += "- Replace weak crypto algorithms (MD5, SHA-1) with stronger alternatives (SHA-256+)\n"
        
        return report

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze Java project security')
    parser.add_argument('project_path', help='Path to the Java project directory')
    parser.add_argument('--json', action='store_true', help='Output results as JSON')
    parser.add_argument('--output', help='Output file path for the report')
    parser.add_argument('--history', help='Path to historical security data for trend analysis')
    
    args = parser.parse_args()
    
    analyzer = SecurityAnalyzer(args.project_path)
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
                history_entry = {
                    "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "metrics": analyzer.security_metrics
                }
                history_data.append(history_entry)
                
                # Save updated history
                with open(args.history, 'w') as f:
                    json.dump(history_data, f, indent=2)
                
                print(f"\nSecurity history saved to {args.history}")
            except Exception as e:
                print(f"Error saving history data: {str(e)}")

if __name__ == "__main__":
    main()
