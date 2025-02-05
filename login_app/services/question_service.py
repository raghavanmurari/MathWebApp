from database.db_connection import get_db
from bson.objectid import ObjectId
import streamlit as st

# Connect to database
db = get_db()
questions_collection = db["questions"]
responses_collection = db["responses"]
assignments_collection = db["assignments"]
topics_collection = db["topics"]

def get_questions_for_assignment(assignment_id):
    """
    Fetch all questions for a given assignment based on its topic and sub-topics.
    Returns a list of questions in a fixed order.
    """
    # First get the assignment details
    assignment = assignments_collection.find_one({"_id": ObjectId(assignment_id)})
    if not assignment:
        return []

    # Get the topic name from topics collection
    topic = topics_collection.find_one({"_id": ObjectId(assignment["topic_id"])})
    if not topic:
        return []

    # Query questions based on topic name and sub-topics
    query = {
        "topic": topic["name"],
        "sub_topic": {"$in": assignment["sub_topics"]}
    }
    
    return list(questions_collection.find(query))


def get_current_question():
    """
    Returns the current question based on session state.
    """
    if "current_assignment" not in st.session_state:
        return None  # No active assignment

    assignment_id = st.session_state["current_assignment"]
    
    # Get all questions for this assignment
    questions = get_questions_for_assignment(assignment_id)
    
    if not questions:
        st.error("No questions found for this assignment.")
        return None

    # Initialize question index if not exists
    if "current_question_index" not in st.session_state:
        st.session_state["current_question_index"] = 0

    # Get current index
    index = st.session_state["current_question_index"]
    
    # Check if we've reached the end
    if index >= len(questions):
        st.success("You've completed all questions!")
        return None

    return questions[index]

def update_student_response(assignment_id, student_id, question_id, selected_answer):
    """
    Updates the student's response in the database.
    """
    # Get the question to check the correct answer
    question = questions_collection.find_one({"_id": ObjectId(question_id)})
    if not question:
        st.error("Question not found!")
        return

    # Check if the answer is correct
    is_correct = selected_answer == question.get("solution")

    response_data = {
        "student_id": ObjectId(student_id),
        "assignment_id": ObjectId(assignment_id),
        "question_id": ObjectId(question_id),
        "selected_answer": selected_answer,
        "is_correct": is_correct,
        "timestamp": datetime.now()
    }

    # Update or insert the response
    responses_collection.update_one(
        {
            "student_id": ObjectId(student_id),
            "assignment_id": ObjectId(assignment_id),
            "question_id": ObjectId(question_id)
        },
        {"$set": response_data},
        upsert=True
    )

    # Move to the next question
    st.session_state["current_question_index"] = st.session_state.get("current_question_index", 0) + 1

    if is_correct:
        st.success("Correct answer!")
    else:
        st.error(f"Incorrect. The correct answer was: {question.get('solution')}")