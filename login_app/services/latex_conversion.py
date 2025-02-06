# utils/latex_conversion.py

class LatexConverter:
    """
    A comprehensive LaTeX converter that handles all mathematical notation cases
    found in the question bank.
    """

    def __init__(self):
        self.math_commands = {
            "\\frac", "\\sqrt", "\\sum", "\\int", "\\prod",
            "\\times", "\\div", "\\pm", "\\approx", "\\neq",
            "\\leq", "\\geq", "\\rightarrow", "\\leftarrow",
            "\\alpha", "\\beta", "\\pi"
        }

    def clean_delimiters(self, text):
        """Clean up LaTeX delimiters"""
        if not text:
            return text

        # Handle escaped delimiters
        text = text.replace('\\(', '$').replace('\\)', '$')
        text = text.strip()

        # Ensure proper spacing around math mode
        text = text.replace('$$', '$')
        return text

    def format_math_mode(self, text):
        """Ensure proper math mode wrapping"""
        if not text:
            return text

        # Don't double wrap
        if text.startswith('$') and text.endswith('$'):
            return text

        # Check if text needs math mode
        needs_math = any(cmd in text for cmd in self.math_commands)

        if needs_math and not (text.startswith('$') and text.endswith('$')):
            text = f'${text}$'

        return text

    def handle_mixed_numbers(self, text):
        """Handle mixed numbers like 2 \frac{3}{4}"""
        if not text or '\\frac' not in text:
            return text

        parts = []
        current_part = ""
        i = 0
        in_number = False

        while i < len(text):
            if text[i:i+5] == '\\frac':  # Start of fraction
                if in_number:
                    parts.append('$')
                    in_number = False

                # Find end of fraction
                start = i
                brace_count = 0
                while i < len(text):
                    if text[i] == '{':
                        brace_count += 1
                    elif text[i] == '}':
                        brace_count -= 1
                        if brace_count == 0 and (i + 1 >= len(text) or text[i + 1] != '\\'):
                            break
                    i += 1
                i += 1

                parts.append(f"$\\frac{text[start+5:i]}$")  # Extract fraction properly
            else:
                if text[i].isdigit():
                    if not in_number:
                        parts.append('$')
                        in_number = True
                elif in_number and not text[i].isspace():
                    parts.append('$')
                    in_number = False

                parts.append(text[i])
                i += 1

        if in_number:
            parts.append('$')

        return ''.join(parts)

    def convert_inline(self, text):
        """Convert inline math expressions"""
        if not text:
            return text

        text = self.clean_delimiters(text)
        text = self.handle_mixed_numbers(text)

        # Handle any remaining math commands
        parts = []
        i = 0
        while i < len(text):
            if any(text[i:].startswith(cmd) for cmd in self.math_commands):
                if i > 0 and parts and not parts[-1].endswith('$'):
                    parts.append('$')

                # Find end of math expression
                start = i
                brace_count = 0
                while i < len(text):
                    if text[i] == '{':
                        brace_count += 1
                    elif text[i] == '}':
                        brace_count -= 1
                        if brace_count == 0 and (i + 1 >= len(text) or text[i + 1] != '\\'):
                            break
                    i += 1
                i += 1

                parts.append(f"${text[start:i]}$")
            else:
                parts.append(text[i])
                i += 1

        text = ''.join(parts)

        # Clean up any double spaces or multiple $$ signs
        text = ' '.join(text.split()).replace('$$', '$')
        return text

    def convert_display(self, text):
        """Convert display math equations"""
        if not text:
            return text

        # If it's a single math expression, use display math
        text = text.strip()
        if (text.startswith('\\(') and text.endswith('\\)')) or \
           all(c in self.math_commands or c in '{}_^0123456789' for c in text if not c.isspace()):
            return f'$${text.strip("\\()")}$$'

        return self.convert_inline(text)

    def convert_option(self, text):
        """Convert multiple choice options"""
        if not text:
            return text

        text = text.strip()
        text = self.clean_delimiters(text)

        # If it's just a fraction or math expression, wrap in inline math
        if '\\frac' in text or any(cmd in text for cmd in self.math_commands):
            return self.format_math_mode(text)

        return text

    def convert(self, text, mode='inline'):
        """
        Main conversion function
        mode: 'inline' or 'display'
        """
        if not text:
            return text

        try:
            if mode == 'display':
                return self.convert_display(text)
            else:
                return self.convert_inline(text)
        except Exception as e:
            print(f"Error in conversion: {e}")
            return text
