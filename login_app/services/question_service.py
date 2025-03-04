from database.db_connection import get_db
from bson import json_util, ObjectId
import streamlit as st
from datetime import datetime 
import json

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
    Returns the next unanswered question for the student within the current sub-topic.
    Stops showing questions when all questions in the sub-topic are attempted.
    """
    if "current_assignment" not in st.session_state or "student_id" not in st.session_state:
        return None  # No active assignment or student ID missing

    assignment_id = st.session_state["current_assignment"]
    student_id = st.session_state["student_id"]

    db = get_db()
    assignments_collection = db["assignments"]
    questions_collection = db["questions"]
    responses_collection = db["responses"]
    topics_collection = db["topics"]

    # print("\n--- DEBUGGING get_current_question() ---")
    # print(f"Assignment ID: {assignment_id}")
    # print(f"Student ID: {student_id}")

    # Get the assignment details
    assignment = assignments_collection.find_one({"_id": ObjectId(assignment_id)})
    if not assignment:
        # print("❌ ERROR: Assignment not found!")
        st.error("Assignment not found.")
        return None

    # Get the topic details
    topic = topics_collection.find_one({"_id": assignment["topic_id"]})
    if not topic:
        # print("❌ ERROR: Topic not found!")
        st.error("Topic not found.")
        return None

    # Get current sub-topic
    current_sub_topic = assignment.get("sub_topics", [])[0] if assignment.get("sub_topics") else None
    if not current_sub_topic:
        # print("❌ ERROR: No sub-topic found in assignment!")
        st.error("No sub-topic found in assignment.")
        return None

    # print(f"Topic: {topic['name']}, Sub-topic: {current_sub_topic}")

    # Fetch questions for this specific topic and sub-topic
    all_questions = list(questions_collection.find({
        "topic": topic["name"],
        "sub_topic": current_sub_topic
    }))
    total_questions = len(all_questions)

    # print(f"Total Questions in Sub-topic: {total_questions}")

    if total_questions == 0:
        # print("❌ ERROR: No questions found for this sub-topic!")
        st.error("No questions found for this sub-topic.")
        return None

    # Get question IDs for current sub-topic
    current_subtopic_question_ids = [q["_id"] for q in all_questions]

    # Get answered questions ONLY for this sub-topic
    answered_questions = responses_collection.distinct(
        "question_id", 
        {
            "assignment_id": ObjectId(assignment_id), 
            "student_id": ObjectId(student_id),
            "question_id": {"$in": current_subtopic_question_ids}  # Only count questions from current sub-topic
        }
    )
    answered_questions_str = {str(q_id) for q_id in answered_questions}

    # print(f"Answered Questions in current sub-topic: {len(answered_questions_str)}")

    # Filter unanswered questions
    unanswered_questions = [q for q in all_questions if str(q["_id"]) not in answered_questions_str]
    remaining_questions = len(unanswered_questions)

    # print(f"Remaining Unanswered Questions in Sub-topic: {remaining_questions}")

    if remaining_questions == 0:
        # print("🎉 Student has completed all questions in this sub-topic!")
        st.success("🎉 Congratulations! You've completed all questions in this sub-topic!")
        if st.button("Return to Dashboard"):
            del st.session_state["current_assignment"]
            if "current_question_index" in st.session_state:
                del st.session_state["current_question_index"]
            if "progress_data" in st.session_state:
                del st.session_state["progress_data"]
            st.switch_page("pages/student_dashboard.py")
        return None

    # Select the next unanswered question
    next_question = unanswered_questions[0]
    # print(f"Next Question ID: {next_question['_id']} - {next_question['description']}")

    return next_question




def update_student_response(assignment_id, student_id, question_id, selected_answer):
    """Updates the student's response in the database."""
    # print("\n--- DEBUGGING update_student_response() ---")
    # print(f"Student ID: {student_id}")
    # print(f"Assignment ID: {assignment_id}")
    # print(f"Question ID: {question_id}")

    try:
        db = get_db()
        responses_collection = db["responses"]

        # Convert IDs to ObjectId
        student_id_obj = ObjectId(student_id)
        assignment_id_obj = ObjectId(assignment_id)
        question_id_obj = ObjectId(question_id)

        # Prepare response data
        response_data = {
            "student_id": student_id_obj,
            "assignment_id": assignment_id_obj,
            "question_id": question_id_obj,
            "selected_option": selected_answer,
            "is_correct": selected_answer.get("is_correct", False),
            "timestamp": datetime.now()
        }
# 
        print("Saving response data:", response_data)

        # Save response
        result = responses_collection.update_one(
            {
                "student_id": student_id_obj,
                "assignment_id": assignment_id_obj,
                "question_id": question_id_obj
            },
            {"$set": response_data},
            upsert=True
        )

        # print("Response saved successfully")
        # print(f"Matched: {result.matched_count}, Modified: {result.modified_count}")
        if result.upserted_id:
            print(f"New response ID: {result.upserted_id}")
            
        # Verify the response was saved
        saved_response = responses_collection.find_one({
            "student_id": student_id_obj,
            "assignment_id": assignment_id_obj,
            "question_id": question_id_obj
        })
        # print("Verified saved response:", saved_response)

        return True

    except Exception as e:
        # print(f"ERROR in update_student_response: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return False