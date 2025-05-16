import json
import re
import requests

class OpenAIClient:
    """Client for interacting with the OpenAI API."""
    
    def __init__(self, api_key, model="gpt-4"):
        self.api_key = api_key
        self.model = model
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
    
    def query(self, prompt, system_message=None, max_attempts=3):
        """Query OpenAI API with the given prompt."""
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        
        # Check if prompt is too large and truncate if necessary
        prompt = self._preprocess_prompt(prompt)
        
        # Add increasingly strict instructions on retries
        for attempt in range(max_attempts):
            if attempt > 0:
                print(f"Retry attempt {attempt}: Making instructions more explicit")
                strict_prompt = f"""IMPORTANT: You MUST ONLY output valid Java code and NOTHING ELSE. 
DO NOT include any text like "this cannot be provided" or explanations. 
DO NOT include markdown formatting.
ONLY respond with compilable, valid Java code.

{prompt}"""
                messages = [msg for msg in messages if msg["role"] != "user"]
                messages.append({"role": "user", "content": strict_prompt})
            else:
                messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.2,
            }
            
            response = requests.post("https://api.openai.com/v1/chat/completions", 
                                   headers=self.headers, json=payload)
            
            if response.status_code != 200:
                print(f"Error: {response.status_code}, {response.text}")
                return None
            
            content = response.json()["choices"][0]["message"]["content"]
            result = self._extract_code_if_present(content)
            
            # If we got valid code or we're out of attempts, return the result
            if result is not None or attempt == max_attempts - 1:
                return result
            
            # Otherwise, we'll try again with stricter instructions
            messages.append({"role": "assistant", "content": content})
            messages.append({"role": "user", "content": "The response is not valid Java code. Please provide ONLY Java code with no explanations or text."})
    
    def _preprocess_prompt(self, prompt):
        """Preprocess prompt to handle token limits."""
        max_prompt_tokens = 6000
        if len(prompt) > max_prompt_tokens * 4:
            print("Warning: Prompt is too large. Truncating...")
            
            if "```java" in prompt:
                # Extract the Java code block
                start = prompt.find("```java") + 7
                end = prompt.find("```", start)
                if start > 7 and end > start:
                    code = prompt[start:end].strip()
                    pre_code = prompt[:start-7].strip()
                    
                    # Keep imports, package declarations, and class definitions
                    import_section, package_section, class_section = self._extract_code_sections(code)
                    method_signatures = self._extract_method_signatures(code)
                    
                    # Create a truncated summary
                    truncated_prompt = f"""{pre_code}

```java
// --- Package and imports ---
{package_section}
{import_section}

// --- Class definition ---
{class_section}

// --- Method signatures ---
/* 
{chr(10).join(method_signatures)}
*/

// Note: Code has been truncated due to length constraints
```

Please complete your task based on this truncated code. Focus on the structure and follow the instructions above.
"""
                    return truncated_prompt
            
            # Simple truncation for non-code or malformed code
            return prompt[:max_prompt_tokens * 4] + "...\n[Content truncated due to length]"
        return prompt
    
    def _extract_code_sections(self, code):
        """Extract important sections from Java code."""
        import_section = ""
        package_section = ""
        class_section = ""
        
        lines = code.split('\n')
        in_imports = False
        for line in lines[:500]:
            if line.strip().startswith("package "):
                package_section += line + "\n"
            elif line.strip().startswith("import "):
                import_section += line + "\n"
                in_imports = True
            elif in_imports and not line.strip().startswith("import "):
                in_imports = False
            elif "class " in line or "interface " in line or "enum " in line:
                # Found class declaration - add this and a few more lines for context
                class_index = lines.index(line)
                class_section = "\n".join(lines[class_index:class_index+20])
                break
        
        return import_section, package_section, class_section
    
    def _extract_method_signatures(self, code):
        """Extract method signatures from Java code."""
        method_signatures = []
        lines = code.split('\n')
        for i, line in enumerate(lines):
            if re.search(r'\b(public|private|protected)\b.*\(.*\)', line) and "{" in line:
                method_signatures.append(line.strip())
            if len(method_signatures) >= 15:
                break
        return method_signatures
    
    def _extract_code_if_present(self, content):
        """Extract code from markdown code blocks if present."""
        # First check if the content looks like explanatory text rather than code
        explanation_indicators = [
            "This cannot be provided",
            "I cannot provide",
            "Here is the",
            "The file should",
            "This is a",
            "This code",
            "Without seeing"
        ]
        
        # If content starts with an explanation, request code again with stricter instructions
        for indicator in explanation_indicators:
            if content.strip().startswith(indicator):
                print("WARNING: Received explanatory text instead of code. Re-requesting with stricter instructions.")
                return None
        
        if "```" in content:
            code_blocks = content.split("```")
            for i in range(1, len(code_blocks), 2):
                if i < len(code_blocks):
                    # Remove language identifier if present (e.g., "java\n")
                    if code_blocks[i].strip() and '\n' in code_blocks[i]:
                        lang_identifier = code_blocks[i].split('\n')[0].strip()
                        code = code_blocks[i][code_blocks[i].index('\n')+1:].strip()
                        
                        # Validate Java code - basic checks
                        if lang_identifier.lower() == 'java':
                            # Ensure there's no plaintext commentary in the code
                            code_lines = code.split('\n')
                            filtered_lines = []
                            for line in code_lines:
                                if any(line.strip().startswith(ind) for ind in explanation_indicators):
                                    continue
                                filtered_lines.append(line)
                            
                            code = '\n'.join(filtered_lines)
                            
                            # Basic validation - must contain class or interface declaration
                            if not re.search(r'(public|private|protected)?\s+(class|interface|enum)\s+\w+', code):
                                print("WARNING: Extracted Java code doesn't contain a valid class/interface declaration!")
                                return None
                        
                        return code
        
        # If code looks valid but no markdown, check if it's directly Java code
        if not "```" in content and ("public class" in content or "public interface" in content):
            if re.search(r'(public|private|protected)?\s+(class|interface|enum)\s+\w+', content):
                return content
        
        # If no code block found or extraction failed, return None
        if any(indicator in content for indicator in explanation_indicators):
            print("WARNING: Content contains explanatory text that may not be valid code.")
            return None
        
        return content