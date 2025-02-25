import streamlit as st
from database.db_connection import get_db
from bson.objectid import ObjectId

# LaTeX conversion function
def convert_latex(text):
    """Convert Excel LaTeX format to Streamlit-compatible format"""
    if text and isinstance(text, str):
        return text.replace('\\(', '$').replace('\\)', '$')
    return text

# Page title
st.title("Review Page")

# Navigation Buttons: Place them side by side using st.columns
col_nav1, col_nav2 = st.columns(2)
with col_nav1:
    if st.button("Back to Dashboard"):
        st.switch_page("pages/student_dashboard.py")
with col_nav2:
    if st.button("Go To Question Page"):
        st.switch_page("pages/question_page.py")

if "current_assignment" not in st.session_state or "student_id" not in st.session_state:
    st.error("Missing assignment or student ID. Please return to the dashboard.")
    st.stop()

current_assignment = st.session_state["current_assignment"]
student_id = st.session_state["student_id"]

# Connect to the database
db = get_db()

# Step 3: Retrieve responses for the current assignment and student
responses_collection = db["responses"]
responses_cursor = responses_collection.find({
    "assignment_id": ObjectId(current_assignment),
    "student_id": ObjectId(student_id)
})
responses = list(responses_cursor)

if not responses:
    st.info("No responses found for this assignment.")
else:
    st.write(f"Found {len(responses)} responses.")
    
    # Get the questions collection
    questions_collection = db["questions"]

    # Step 4: Loop through each response to fetch question details and display review info
    for i, response in enumerate(responses, start=1):
        # Fetch the corresponding question using the question_id from the response
        question = questions_collection.find_one({"_id": ObjectId(response["question_id"])})
        if not question:
            st.write("Question details not found.")
            continue

        # Display the question description with LaTeX conversion
        st.markdown(f"### Question {i}")
        st.markdown(convert_latex(question.get("description", "No description available.")))

        # Display the student's selected answer and correctness indicator with LaTeX conversion if needed
        selected_option = response.get("selected_option", {})
        selected_text = selected_option.get("text", "No answer selected")
        is_correct = response.get("is_correct", False)
        if is_correct:
            st.markdown(f"**Your Answer:** {convert_latex(selected_text)} ✅")
        else:
            st.markdown(f"**Your Answer:** {convert_latex(selected_text)} ❌")

        # Display solution or explanation if available, using LaTeX conversion
        if question.get("solution"):
            st.markdown("**Solution:**")
            st.markdown(convert_latex(question["solution"]))
        elif question.get("explanation"):
            st.markdown("**Explanation:**")
            st.markdown(convert_latex(question["explanation"]))

        st.markdown("---")  # Divider between questions
