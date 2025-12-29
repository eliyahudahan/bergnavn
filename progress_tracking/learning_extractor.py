"""
Learning extraction module
Extracts learnings and insights from your_plan.md
"""

import re
from datetime import datetime

class LearningExtractor:
    """Extracts learnings from project documentation"""
    
    def __init__(self, config):
        self.config = config
    
    def extract_todays_learnings(self):
        """
        Extract learnings from your_plan.md file
        
        Returns:
            list: List of learning items
        """
        if not self.config.PLAN_FILE.exists():
            print(f"Warning: Plan file not found: {self.config.PLAN_FILE}")
            return []
        
        try:
            with open(self.config.PLAN_FILE, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract learnings from specific sections first
            learnings = self._extract_learning_section(content)
            
            # Then look for learning statements in the text (excluding code blocks)
            all_learnings = self._find_learning_keywords(content)
            
            # Combine and deduplicate
            combined = list(set(learnings + all_learnings))
            
            # Save learnings to file
            if combined:
                self._save_learnings(combined)
            
            return combined
            
        except Exception as e:
            print(f"Error extracting learnings: {e}")
            return []
    
    def _extract_learning_section(self, content):
        """Extract learnings from specific sections in the plan"""
        learnings = []
        
        # Pattern for learning sections
        patterns = [
            r'### (?:Today\'s|Today’s) Learnings.*?\n(.*?)(?=\n###|\n##|\n---|$)',
            r'## Learning Insights.*?\n(.*?)(?=\n##|\n---|$)',
            r'## 📚 (?:Learning Insights|Key Takeaways).*?\n(.*?)(?=\n##|\n---|$)',
            r'### 🧠 Today\'s Learnings.*?\n(.*?)(?=\n###|\n##|\n---|$)',
            r'Key Takeaways.*?\n(.*?)(?=\n##|\n---|$)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                section_content = match.group(1)
                # Extract list items (bullet points and numbered lists)
                items = re.findall(r'^[\s]*[•\-\*]\s*(.+)$', section_content, re.MULTILINE)
                items += re.findall(r'^[\s]*\d+\.\s*(.+)$', section_content, re.MULTILINE)
                
                # Also look for plain sentences in the learning section
                sentences = re.split(r'[.!?]+', section_content)
                for sentence in sentences:
                    sentence = sentence.strip()
                    if (len(sentence.split()) >= 3 and 
                        any(keyword in sentence.lower() for keyword in ['learn', 'note', 'important', 'realized'])):
                        items.append(sentence)
                
                learnings.extend(items)
        
        # Clean and filter the learnings
        cleaned_learnings = []
        for item in learnings:
            item = item.strip()
            if item and len(item.split()) >= 3:  # At least 3 words
                # Remove any markdown formatting that might have been included
                item = re.sub(r'[*_`#]', '', item)
                item = re.sub(r'\s+', ' ', item).strip()
                cleaned_learnings.append(item)
        
        return cleaned_learnings
    
    def _find_learning_keywords(self, content):
        """Find learning statements using keywords (excluding code blocks)"""
        learnings = []
        
        # First remove all code blocks to avoid analyzing code as text
        content_without_code = self._remove_code_blocks(content)
        
        # Split into sentences
        sentences = re.split(r'[.!?]+', content_without_code)
        
        for sentence in sentences:
            sentence = sentence.strip()
            
            # Skip very short sentences or sentences that look like code/commands
            if (len(sentence.split()) < 3 or 
                sentence.startswith('```') or 
                sentence.startswith('$ ') or
                'def ' in sentence or 
                'class ' in sentence or
                'import ' in sentence or
                'from ' in sentence):
                continue
            
            # Check if sentence contains learning keywords
            if any(keyword in sentence.lower() for keyword in self.config.LEARNING_KEYWORDS):
                # Clean up the sentence
                clean_sentence = self._clean_learning_sentence(sentence)
                if clean_sentence and len(clean_sentence.split()) >= 3:
                    # Check if this looks like a real learning, not code
                    if not self._looks_like_code(clean_sentence):
                        learnings.append(clean_sentence)
        
        return learnings
    
    def _remove_code_blocks(self, content):
        """Remove all code blocks from content"""
        # Remove ```code blocks```
        content = re.sub(r'```.*?```', '', content, flags=re.DOTALL)
        # Remove inline `code`
        content = re.sub(r'`.*?`', '', content)
        # Remove Python function definitions
        content = re.sub(r'def \w+\(.*?\):', '', content, flags=re.DOTALL)
        # Remove class definitions
        content = re.sub(r'class \w+.*?:', '', content, flags=re.DOTALL)
        # Remove import statements
        content = re.sub(r'^(import|from) .*$', '', content, flags=re.MULTILINE)
        
        return content
    
    def _looks_like_code(self, text):
        """Check if text looks like code rather than natural language"""
        code_patterns = [
            r'\w+\(.*?\)',  # Function calls
            r'\w+\.\w+\(',  # Method calls
            r'\[.*?\]',     # List/dict access
            r'\{.*?\}',     # Dict/set
            r'=\s*[{\[]',   # Assignment to collection
            r'\.py',        # File extensions
            r'\.append\(',  # Common methods
            r'\.split\(',   # Common methods
            r'\+\=',        # Augmented assignment
            r'if .*?:',     # If statements
            r'for .*?:',    # For loops
            r'return ',     # Return statements
        ]
        
        for pattern in code_patterns:
            if re.search(pattern, text):
                return True
        
        # Check for excessive punctuation or symbols
        symbol_count = sum(1 for char in text if char in '{}[]()<>;:=+*/')
        word_count = len(text.split())
        
        if symbol_count > word_count * 0.3:  # More than 30% symbols
            return True
        
        return False
    
    def _clean_learning_sentence(self, sentence):
        """Clean and format learning sentence"""
        # Remove remaining markdown formatting
        clean = re.sub(r'[*_`#]', '', sentence)
        # Remove HTML entities
        clean = re.sub(r'&[a-z]+;', '', clean)
        # Remove URLs
        clean = re.sub(r'https?://\S+', '', clean)
        # Remove extra whitespace
        clean = re.sub(r'\s+', ' ', clean).strip()
        # Remove leading/trailing punctuation
        clean = clean.strip('.,;:- ')
        
        # Capitalize first letter if not already
        if clean and clean[0].islower():
            clean = clean[0].upper() + clean[1:]
        
        # Ensure sentence ends with period
        if clean and not clean.endswith('.'):
            clean = clean + '.'
        
        return clean
    
    def _save_learnings(self, learnings):
        """Save learnings to a markdown file"""
        if not learnings:
            return
        
        # Filter out any remaining code-like entries
        filtered_learnings = []
        for learning in learnings:
            if (not self._looks_like_code(learning) and 
                len(learning.split()) >= 3 and
                len(learning) > 10):
                filtered_learnings.append(learning)
        
        if not filtered_learnings:
            return
        
        # Create filename with date
        filename = self.config.LEARNINGS_DIR / f"learnings_{self.config.today_str}.md"
        
        content = f"""# Learnings - {self.config.today_str}
*Extracted from your_plan.md*

## Summary
Found {len(filtered_learnings)} meaningful learning item(s) today.

## Learning Items

"""
        
        for i, learning in enumerate(filtered_learnings, 1):
            # Truncate very long learnings
            if len(learning) > 200:
                learning = learning[:197] + "..."
            content += f"{i}. {learning}\n"
        
        content += f"""

---
*Auto-generated by BergNavn Progress Tracker*
*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"Warning: Could not save learnings: {e}")