class LatexConverter:
    """
    A comprehensive LaTeX converter that handles all mathematical notation cases
    including mixed content, solutions, and special environments.
    """

    def __init__(self):
        # Mathematical operators and symbols
        self.math_operators = {
            '+', '-', '*', '/', '=', '<', '>', '≤', '≥', '±', '∓', '×', '÷',
            '\\times', '\\div', '\\pm', '\\mp', '\\cdot', '\\leq', '\\geq'
        }
        
        # Math environments that need special handling
        self.math_environments = {
            'align', 'equation', 'gather', 'matrix', 'cases',
            'split', 'aligned', 'gathered'
        }
        
        # Mathematical functions and commands
        self.math_commands = {
            '\\sqrt', '\\frac', '\\sum', '\\int', '\\prod',
            '\\alpha', '\\beta', '\\gamma', '\\theta',
            '\\infty', '\\pi', '\\Delta'
        }

    def clean_delimiters(self, text):
        """Clean and standardize LaTeX delimiters"""
        if not text:
            return text

        # Convert \( \) to $ $
        text = text.replace('\\(', '$')
        text = text.replace('\\)', '$')
        
        # Convert \[ \] to $$ $$
        text = text.replace('\\[', '$$')
        text = text.replace('\\]', '$$')
        
        # Normalize multiple consecutive delimiters
        text = text.replace('$$$$', '$$')
        text = text.replace('$$', '$')
        
        return text

    def is_math_expression(self, text):
        """Determine if text contains mathematical content"""
        if not text:
            return False
            
        # Check for numbers with operators
        if any(op in text for op in self.math_operators):
            return True
            
        # Check for LaTeX commands
        if any(cmd in text for cmd in self.math_commands):
            return True
            
        # Check for common math patterns
        import re
        math_patterns = [
            r'\d+\s*[+\-*/]\s*\d+',  # Basic operations
            r'\d*\.\d+',              # Decimal numbers
            r'[xyz]\d*',              # Variables with optional numbers
            r'[ab]\s*=',              # Assignment
            r'\\[a-zA-Z]+',           # LaTeX commands
            r'\^',                    # Exponents
            r'_',                     # Subscripts
        ]
        
        return any(re.search(pattern, text) for pattern in math_patterns)

    def handle_mixed_content(self, text):
        """Handle text that contains both math and regular content"""
        if not text:
            return text
            
        parts = []
        current_part = []
        in_math = False
        
        for char in text:
            if char == '$':
                # Toggle math mode
                if current_part:
                    parts.append(''.join(current_part))
                    current_part = []
                parts.append('$')
                in_math = not in_math
            else:
                current_part.append(char)
                
        if current_part:
            parts.append(''.join(current_part))
            
        # Process each part
        processed_parts = []
        for i, part in enumerate(parts):
            if part == '$':
                processed_parts.append(part)
            else:
                # If not in math mode and contains math, wrap in delimiters
                if i % 2 == 0 and self.is_math_expression(part):
                    processed_parts.append(f'${part}$')
                else:
                    processed_parts.append(part)
                    
        return ''.join(processed_parts)

    def convert_question(self, text):
        """Convert question text with proper math handling"""
        if not text:
            return text
            
        # Clean existing delimiters
        text = self.clean_delimiters(text)
        
        # Handle mixed content
        text = self.handle_mixed_content(text)
        
        # Ensure proper spacing around math delimiters
        import re
        text = re.sub(r'(\$)([^\s])', r'\1 \2', text)  # Space after $
        text = re.sub(r'([^\s])(\$)', r'\1 \2', text)  # Space before $
        
        return text

    def convert_option(self, text):
        """Convert option text with proper math handling"""
        if not text:
            return text
            
        # Clean delimiters
        text = self.clean_delimiters(text)
        
        # If it's a pure math expression, ensure it's wrapped
        if self.is_math_expression(text):
            if not (text.startswith('$') and text.endswith('$')):
                text = f'${text}$'
        
        return text.strip()

    def convert_solution(self, text):
        """Convert solution text with full math support"""
        if not text:
            return text
            
        # Clean delimiters
        text = self.clean_delimiters(text)
        
        # Split into lines to handle each separately
        lines = text.split('\n')
        processed_lines = []
        
        for line in lines:
            # Handle mixed content in each line
            line = self.handle_mixed_content(line)
            processed_lines.append(line)
            
        return '\n'.join(processed_lines)

    def convert_complete_question(self, question_dict):
        """Process an entire question dictionary"""
        if not question_dict:
            return question_dict
            
        # Copy to avoid modifying original
        processed = dict(question_dict)
        
        # Convert main question text
        if 'description' in processed:
            processed['description'] = self.convert_question(processed['description'])
            
        # Convert options
        if 'options' in processed and isinstance(processed['options'], list):
            for option in processed['options']:
                if isinstance(option, dict) and 'text' in option:
                    option['text'] = self.convert_option(option['text'])
                    
        # Convert solution if present
        if 'solution' in processed:
            processed['solution'] = self.convert_solution(processed['solution'])
            
        # Convert explanation if present
        if 'explanation' in processed:
            processed['explanation'] = self.convert_solution(processed['explanation'])
            
        return processed

    @staticmethod
    def convert(text, mode='inline'):
        """
        Main conversion function with mode selection
        modes: 'inline', 'display', 'solution'
        """
        converter = LatexConverter()
        
        try:
            if mode == 'solution':
                return converter.convert_solution(text)
            elif mode == 'display':
                return converter.convert_question(text)
            else:
                return converter.convert_option(text)
        except Exception as e:
            print(f"Error in LaTeX conversion: {str(e)}")
            return text  # Return original text if conversion fails