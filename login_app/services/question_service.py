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
    Returns the next unanswered question for the student.
    """
    if "current_assignment" not in st.session_state or "student_id" not in st.session_state:
        return None  # No active assignment or student ID missing

    assignment_id = st.session_state["current_assignment"]
    student_id = st.session_state["student_id"]

    db = get_db()
    assignments_collection = db["assignments"]
    questions_collection = db["questions"]
    responses_collection = db["responses"]

    print("\n--- DEBUGGING get_current_question() ---")
    print(f"Assignment ID: {assignment_id}")
    print(f"Student ID: {student_id}")

    # Get the topic_id from the assignment
    assignment = assignments_collection.find_one({"_id": ObjectId(assignment_id)})
    if not assignment:
        print("❌ ERROR: Assignment not found!")
        st.error("Assignment not found.")
        return None

    topic_id = assignment.get("topic_id")
    if not topic_id:
        print("❌ ERROR: Assignment has no topic_id!")
        st.error("Assignment has no topic linked.")
        return None

    # Fetch questions using topic_id
    all_questions = list(questions_collection.find({"topic_id": ObjectId(topic_id)}))

    print(f"Total Questions Found: {len(all_questions)}")

    if not all_questions:
        print("❌ ERROR: No questions found in DB for this topic!")
        st.error("No questions found for this topic.")
        return None

    # Get all answered questions and convert ObjectId to string for comparison
    answered_questions = responses_collection.distinct(
        "question_id", {"assignment_id": ObjectId(assignment_id), "student_id": ObjectId(student_id)}
    )
    answered_questions_str = {str(q_id) for q_id in answered_questions}  # Convert ObjectId list to string set

    print(f"Answered Questions: {answered_questions_str}")

    # Filter unanswered questions
    unanswered_questions = [q for q in all_questions if str(q["_id"]) not in answered_questions_str]

    print(f"Remaining Unanswered Questions: {len(unanswered_questions)}")

    if not unanswered_questions:
        print("🎉 Student has completed all questions!")
        st.success("🎉 You've completed all questions in this assignment!")
        return None

    # Select the next unanswered question
    next_question = unanswered_questions[0]
    print(f"Next Question ID: {next_question['_id']} - {next_question['description']}")

    return next_question








def update_student_response(assignment_id, student_id, question_id, selected_answer):
    """
    Updates the student's response in the database.
    Parameters:
    - assignment_id: ID of the current assignment
    - student_id: ID of the current student
    - question_id: ID of the current question
    - selected_answer: The complete option object that was selected
    """

    print("\n--- DEBUGGING update_student_response() ---")
    print(f"Student ID: {student_id}")
    print(f"Assignment ID: {assignment_id}")
    print(f"Question ID: {question_id}")
    print(f"Selected Answer: {json.dumps(selected_answer, default=json_util.default)}")

    db = get_db()
    questions_collection = db["questions"]
    responses_collection = db["responses"]

    # Verify the question exists
    question = questions_collection.find_one({"_id": ObjectId(question_id)})
    if not question:
        print(f"❌ ERROR: Question with ID {question_id} not found in MongoDB!")
        st.error("Question not found!")
        return

    # Determine if the selected answer is correct
    is_correct = selected_answer.get("is_correct", False)

    # Prepare response data
    response_data = {
        "student_id": ObjectId(student_id),
        "assignment_id": ObjectId(assignment_id),
        "question_id": ObjectId(question_id),
        "selected_option": {
            "option_id": selected_answer.get("option_id", ""),
            "text": selected_answer.get("text", "")
        },
        "is_correct": is_correct,
        "timestamp": datetime.now()
    }

    print("\nUpdating MongoDB with data:")
    print(json.dumps(response_data, default=json_util.default))

    # Perform the database update
    try:
        result = responses_collection.update_one(
            {
                "student_id": ObjectId(student_id),
                "assignment_id": ObjectId(assignment_id),
                "question_id": ObjectId(question_id)
            },
            {"$set": response_data},
            upsert=True  # Insert if not exists, update if exists
        )

        # Log MongoDB update results
        print(f"✅ MongoDB Update Result: Matched {result.matched_count}, Modified {result.modified_count}")
        if result.matched_count == 0 and result.upserted_id:
            print(f"🆕 New response inserted with ID: {result.upserted_id}")
        elif result.modified_count == 0:
            print(f"⚠️ Warning: No changes were made. Maybe data was already the same?")

    except Exception as e:
        print(f"❌ ERROR updating MongoDB: {str(e)}")
        st.error("Failed to save response. Please try again.")