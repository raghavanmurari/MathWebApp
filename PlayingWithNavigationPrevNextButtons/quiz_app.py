import streamlit as st
import pandas as pd
import openpyxl
import re

# Initialize session state variables if they don't exist
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'submitted_answers' not in st.session_state:
    st.session_state.submitted_answers = [None] * 5
if 'show_solutions' not in st.session_state:
    st.session_state.show_solutions = [False] * 5

def convert_latex_math(latex_str):
    """Convert LaTeX math expressions to readable text format"""
    # Remove LaTeX delimiters
    latex_str = str(latex_str).replace('\\(', '').replace('\\)', '').strip()
    
    # Dictionary of LaTeX math symbols and their text representations
    math_symbols = {
        '\\times': '×',
        '\\div': '÷',
        '\\pm': '±',
        '\\leq': '≤',
        '\\geq': '≥',
        '\\neq': '≠',
        '\\approx': '≈',
        '\\cdot': '·',
        '\\sqrt': '√',
        '\\pi': 'π',
        '\\infty': '∞',
        '\\sum': 'Σ',
        '\\prod': 'Π',
        '\\alpha': 'α',
        '\\beta': 'β',
        '\\gamma': 'γ',
        '\\delta': 'δ',
        '\\theta': 'θ',
        '\\lambda': 'λ',
        '\\mu': 'μ',
        '\\sigma': 'σ',
        '\\omega': 'ω'
    }
    
    # Replace LaTeX symbols with their text equivalents
    for symbol, replacement in math_symbols.items():
        latex_str = latex_str.replace(symbol, replacement)
    
    # Handle fractions \frac{num}{den}
    latex_str = re.sub(r'\\frac{([^{}]+)}{([^{}]+)}', r'\1/\2', latex_str)
    
    # Handle superscripts - replace x^{2} with x²
    superscript_map = {'0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴', 
                      '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'}
    latex_str = re.sub(r'\^{(\d)}', lambda m: superscript_map.get(m.group(1), m.group(1)), latex_str)
    latex_str = re.sub(r'\^(\d)', lambda m: superscript_map.get(m.group(1), m.group(1)), latex_str)
    
    # Handle subscripts - replace x_{2} with x₂
    subscript_map = {'0': '₀', '1': '₁', '2': '₂', '3': '₃', '4': '₄', 
                    '5': '₅', '6': '₆', '7': '₇', '8': '₈', '9': '₉'}
    latex_str = re.sub(r'_{(\d)}', lambda m: subscript_map.get(m.group(1), m.group(1)), latex_str)
    latex_str = re.sub(r'_(\d)', lambda m: subscript_map.get(m.group(1), m.group(1)), latex_str)
    
    # Handle square roots
    latex_str = re.sub(r'\\sqrt{([^{}]+)}', r'√(\1)', latex_str)
    
    # Handle basic algebraic operations
    latex_str = re.sub(r'\\left\(', '(', latex_str)
    latex_str = re.sub(r'\\right\)', ')', latex_str)
    latex_str = re.sub(r'\\left\[', '[', latex_str)
    latex_str = re.sub(r'\\right\]', ']', latex_str)
    
    # Clean up any remaining LaTeX commands and extra spaces
    latex_str = re.sub(r'\\[a-zA-Z]+', '', latex_str)
    latex_str = re.sub(r'\s+', ' ', latex_str)
    
    return latex_str.strip()

# Read questions from Excel
def load_questions():
    df = pd.read_excel('FractionsSample.xlsx', sheet_name='Sheet1')
    questions = []
    
    for index, row in df.iterrows():
        # Convert LaTeX expressions in options
        options = [
            convert_latex_math(str(row.iloc[2])),  # Column C
            convert_latex_math(str(row.iloc[3])),  # Column D
            convert_latex_math(str(row.iloc[4])),  # Column E
            convert_latex_math(str(row.iloc[5]))   # Column F
        ]
        
        # Map the correct answer letter to the correct option
        correct_letter = str(row.iloc[6]).lower()  # Column G
        correct_option = None
        if correct_letter == 'a':
            correct_option = options[0]
        elif correct_letter == 'b':
            correct_option = options[1]
        elif correct_letter == 'c':
            correct_option = options[2]
        elif correct_letter == 'd':
            correct_option = options[3]
        
        # Convert LaTeX expressions in solution text
        solution_text = str(row.iloc[7])
        # Find all LaTeX math expressions in solution text
        math_expressions = re.finditer(r'\\(\(.*?\)|\[.*?\]|{.*?})', solution_text)
        for match in math_expressions:
            latex_expr = match.group(0)
            simple_expr = convert_latex_math(latex_expr)
            solution_text = solution_text.replace(latex_expr, simple_expr)
            
        question = {
            'question_number': row.iloc[0],  # Column A
            'question': row.iloc[1],         # Column B
            'options': options,
            'correct_answer': correct_option,
            'solution': solution_text
        }
        questions.append(question)
    return questions



# Navigation functions
def next_question():
    if st.session_state.current_question < len(questions) - 1:
        st.session_state.current_question += 1

def prev_question():
    if st.session_state.current_question > 0:
        st.session_state.current_question -= 1

try:
    # Load questions
    questions = load_questions()

    # App title
    st.title('Fractions Quiz')

    # Current question number display
    st.subheader(f'Question {st.session_state.current_question + 1} of {len(questions)}')

    # Display current question
    current_q = questions[st.session_state.current_question]
    st.write(f"Question {current_q['question_number']}: {current_q['question']}")

    # Radio buttons for options
    selected_option = st.radio('Choose your answer:', 
                             current_q['options'],
                             index=None if st.session_state.submitted_answers[st.session_state.current_question] is None 
                             else current_q['options'].index(st.session_state.submitted_answers[st.session_state.current_question]),
                             key=f"radio_{st.session_state.current_question}")

    # Submit button (only show if not already submitted)
    if not st.session_state.show_solutions[st.session_state.current_question]:
        if st.button('Submit'):
            st.session_state.submitted_answers[st.session_state.current_question] = selected_option
            st.session_state.show_solutions[st.session_state.current_question] = True

    # Display result and solution if submitted
    if st.session_state.show_solutions[st.session_state.current_question]:
        submitted_answer = st.session_state.submitted_answers[st.session_state.current_question]
        if submitted_answer == current_q['correct_answer']:
            st.success('Correct! 🎉')
        else:
            st.error(f'Incorrect! The correct answer is: {current_q["correct_answer"]}')
        
        st.write('Solution:', current_q['solution'])

    # Navigation buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button('Previous', disabled=st.session_state.current_question == 0):
            prev_question()
    with col2:
        if st.button('Next', disabled=st.session_state.current_question == len(questions) - 1):
            next_question()

except Exception as e:
    st.error(f"Error loading questions: {str(e)}")
    st.write("Please make sure the Excel file is in the correct format and location.")