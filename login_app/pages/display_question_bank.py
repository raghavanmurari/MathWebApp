# display_question_bank.py
import streamlit as st
import pandas as pd
from database.db_connection import get_db

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