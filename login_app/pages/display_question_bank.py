# display_question_bank.py
import streamlit as st
import pandas as pd
from database.db_connection import get_db
# from pages.question_page import convert_latex


def convert_latex(text):
    """Convert Excel LaTeX format to Streamlit-compatible format."""
    if text and isinstance(text, str):
        return text.replace('\\(', '$').replace('\\)', '$')
    return text

def display_question_bank():
    st.header("Question Bank Overview")
    
    db = get_db()
    questions = db["questions"]
    
  
    pipeline = [
        {
            "$group": {
                "_id": {
                    "topic": "$topic",
                    "sub_topic": "$sub_topic"
                },
                "total_questions": {"$sum": 1},
                "difficulty_counts": {
                    "$push": {
                        "difficulty": "$difficulty",
                        "count": 1
                    }
                }
            }
        },
        {
            "$project": {
                "topic": "$_id.topic",
                "sub_topic": "$_id.sub_topic",
                "total_questions": 1,
                "easy": {
                    "$size": {
                        "$filter": {
                            "input": "$difficulty_counts",
                            "cond": {"$eq": ["$$this.difficulty", "Easy"]}
                        }
                    }
                },
                "medium": {
                    "$size": {
                        "$filter": {
                            "input": "$difficulty_counts",
                            "cond": {"$eq": ["$$this.difficulty", "Medium"]}
                        }
                    }
                },
                "hard": {
                    "$size": {
                        "$filter": {
                            "input": "$difficulty_counts",
                            "cond": {"$eq": ["$$this.difficulty", "Hard"]}
                        }
                    }
                }
            }
        }
    ]
    
    results = list(questions.aggregate(pipeline))
    
    if results:
        df = pd.DataFrame(results)
        df = df.fillna(0)  # Replace NaN with 0
        
        # Reorder columns
        df = df[[
            'topic', 'sub_topic', 'total_questions',
            'easy', 'medium', 'hard'
        ]]
        
        # Rename columns
        df.columns = [
            'Topic', 'Sub-Topic', 'Total Questions',
            'Easy', 'Medium', 'Hard'
        ]
        
        st.dataframe(
            df,
            column_config={
                "Topic": st.column_config.TextColumn("Topic", width=200),
                "Sub-Topic": st.column_config.TextColumn("Sub-Topic", width=200),
                "Total Questions": st.column_config.NumberColumn("Total Questions", format="%d"),
                "Easy": st.column_config.NumberColumn("Easy", format="%d"),
                "Medium": st.column_config.NumberColumn("Medium", format="%d"),
                "Hard": st.column_config.NumberColumn("Hard", format="%d")
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No questions found in the database.")


def view_questions():
    st.header("View Questions")
    db = get_db()
    questions_col = db["questions"]

    # Dropdown for Topics
    topics = questions_col.distinct("topic")
    selected_topic = st.selectbox("Select Topic", options=topics)

    # Dropdown for Sub-Topics
    subtopics = questions_col.distinct("sub_topic", {"topic": selected_topic})
    selected_subtopic = st.selectbox("Select Sub-Topic", options=subtopics)

    # Query the filtered questions
    query = {"topic": selected_topic, "sub_topic": selected_subtopic}
    results = list(questions_col.find(query))

    if results:
        # Initialize a question counter
        question_number = 1
        
        for q in results:
            # Convert LaTeX if needed
            question_text = convert_latex(q.get('description', 'No description'))
            solution_text = convert_latex(q.get('solution', 'No solution'))

            # Combine question number, question text, and difficulty
            st.markdown(
                f"**Question {question_number}:** {question_text} &emsp;&emsp;"
                f"**Difficulty:** {q.get('difficulty', 'N/A')}"
            )
            st.markdown(f"**Solution:** {solution_text}")
            st.markdown("---")

            question_number += 1
    else:
        st.info("No questions found for the selected criteria.")
