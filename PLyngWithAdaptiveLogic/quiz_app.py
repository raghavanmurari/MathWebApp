import streamlit as st
import pandas as pd
from adaptive_logic import AdaptiveQuiz

def load_questions():
    try:
        df = pd.read_excel('AlgebraicExpressions.xlsx', sheet_name='Questions')
        questions = []
        
        for _, row in df.iterrows():
            if pd.isna(row['No']) or pd.isna(row['Description']):
                continue
            
            if isinstance(row['No'], (int, float)):
                question = {
                    'number': int(row['No']),
                    'question': row['Description'],
                    'options': [
                        row['option-1'],
                        row['option-2'],
                        row['option-3'],
                        row['option-4']
                    ],
                    'correct_answer': row['Answer'].lower() if pd.notna(row['Answer']) else None,
                    'difficulty': row['Difficulty Level'] if pd.notna(row['Difficulty Level']) else 'Medium'
                }
                questions.append(question)
        return questions
    except Exception as e:
        st.error(f"Error loading questions: {str(e)}")
        return []

def initialize_session_state():
    # Initialize adaptive_quiz first
    if 'adaptive_quiz' not in st.session_state:
        all_questions = load_questions()
        st.session_state.adaptive_quiz = AdaptiveQuiz(all_questions)

    if 'questions' not in st.session_state:
        st.session_state.questions = st.session_state.adaptive_quiz.get_next_questions()
        
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
        
    if 'score' not in st.session_state:
        st.session_state.score = 0
        
    if 'answered' not in st.session_state:
        st.session_state.answered = False
        
    if 'total_attempted' not in st.session_state:
        st.session_state.total_attempted = 0
        
    if 'current_set_completed' not in st.session_state:
        st.session_state.current_set_completed = False

def main():
    st.set_page_config(page_title="Adaptive Algebraic Expressions Quiz", layout="centered")
    
    st.markdown("""
        <style>
        .stRadio [role=radiogroup]{
            padding: 10px;
            background-color: #f0f2f6;
            border-radius: 10px;
        }
        .stButton button {
            width: 100%;
        }
        .math-question {
            font-size: 18px;
            padding: 15px;
            background-color: #f8f9fa;
            border-radius: 5px;
            margin: 10px 0;
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("Adaptive Algebraic Expressions Quiz")
    
    initialize_session_state()
    
    if not st.session_state.questions:
        if st.session_state.adaptive_quiz.is_quiz_completed():
            report = st.session_state.adaptive_quiz.generate_report(
                st.session_state.score, 
                st.session_state.total_attempted
            )
            
            st.success("Quiz Completed! 🎉")
            
            # Display detailed report
            st.markdown("### Final Report")
            st.markdown(f"**Learning Path:** {report['path']}")
            st.markdown(f"**Score:** {report['score']:.1f}%")
            
            # Display recommendation with appropriate styling
            st.markdown("### Recommendation")
            if 'Success' in report['path']:
                st.success(report['message'])
            elif 'Needs' in report['path']:
                st.warning(report['message'])
            else:
                st.info(report['message'])
            
            # Display progress metrics
            st.markdown("### Progress Metrics")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Questions Attempted", st.session_state.total_attempted)
            with col2:
                st.metric("Correct Answers", st.session_state.score)
            
            if st.button("Restart Quiz", key="restart_final"):
                st.session_state.clear()
                st.rerun()
            return
        else:
            st.error("No questions loaded. Please check your Excel file.")
            return
    
    total_questions = len(st.session_state.questions)
    current_q_num = st.session_state.current_question + 1
    progress = st.progress(current_q_num / total_questions)
    
    # Display current level and progress
    current_level = st.session_state.adaptive_quiz.get_current_level()
    st.markdown(f"**Current Level:** {current_level}")
    st.write(f"Question {current_q_num} of {total_questions}")
    
    current_q = st.session_state.questions[st.session_state.current_question]
    
    st.markdown(f'<div class="math-question">{current_q["question"]}</div>', unsafe_allow_html=True)
    
    if current_q.get('difficulty'):
        difficulty_color = {
            'Easy': 'green',
            'Medium': 'orange',
            'Hard': 'red'
        }.get(current_q['difficulty'], 'blue')
        st.markdown(f"**Difficulty:** <span style='color: {difficulty_color}'>{current_q['difficulty']}</span>", 
                    unsafe_allow_html=True)
    
    valid_options = [(f"Option {i+1}", opt) for i, opt in enumerate(current_q['options']) 
                    if pd.notna(opt)]
    
    selected_option = st.radio(
        "Choose your answer:",
        valid_options,
        format_func=lambda x: f"{x[1]}",
        key=f"q_{st.session_state.current_question}",
        index=None
    )
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Submit", disabled=st.session_state.answered):
            if selected_option is not None:
                st.session_state.answered = True
                selected_index = valid_options.index(selected_option)
                correct_answer_index = ord(current_q['correct_answer'].lower()) - ord('a')
                
                if selected_index == correct_answer_index:
                    st.success("Correct! 🎉")
                    st.session_state.score += 1
                else:
                    correct_option = valid_options[correct_answer_index][1]
                    st.error(f"Incorrect. The correct answer was: {correct_option}")
                
                st.session_state.total_attempted += 1
                st.info(f"Current Score: {st.session_state.score}/{st.session_state.total_attempted}")
    
    with col2:
        if st.button("Next", disabled=not st.session_state.answered):
            if st.session_state.current_question < len(st.session_state.questions) - 1:
                st.session_state.current_question += 1
                st.session_state.answered = False
                st.rerun()
            else:
                # Current set completed, get next set based on performance
                current_score = st.session_state.score
                total_questions = st.session_state.total_attempted
                next_questions = st.session_state.adaptive_quiz.get_next_questions(
                    current_score, 
                    total_questions
                )
                
                if next_questions:
                    st.session_state.questions = next_questions
                    st.session_state.current_question = 0
                    st.session_state.answered = False
                    st.rerun()
                else:
                    st.session_state.questions = []
                    st.rerun()

if __name__ == "__main__":
    main()