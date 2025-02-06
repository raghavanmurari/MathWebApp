from database.db_connection import get_db
from bson.objectid import ObjectId
from utils.latex_conversion import LatexConverter

class QuestionHandler:
    def __init__(self):
        self.db = get_db()
        self.responses_collection = self.db["responses"]
        self.latex_converter = LatexConverter()
        
    def get_current_question(self, assignment_id, current_index):
        """Get the current question based on assignment and index"""
        assignment = self.db["assignments"].find_one({"_id": ObjectId(assignment_id)})
        if not assignment or "sub_topics" not in assignment:
            return None
            
        questions = assignment.get("sub_topics", [])
        if current_index < len(questions):
            return questions[current_index]
        return None
        
    def format_question_text(self, question_text):
        """Format question text with LaTeX conversion"""
        if not question_text:  # Add null check
            return ""
            
        # Convert to string if not already
        question_text = str(question_text)
        
        if "\n" in question_text or question_text.strip().startswith("\\["):
            return self.latex_converter.convert(question_text, mode='display')
        return self.latex_converter.convert(question_text, mode='inline')
        
    def format_options(self, options):
        """Format question options with LaTeX conversion"""
        display_values = []
        option_mapping = {}
        
        for option in options:
            display_text = option.get('text', '')
            formatted_text = self.latex_converter.convert_option(display_text)
            display_values.append(formatted_text)
            option_mapping[formatted_text] = option
            
        return display_values, option_mapping
        
    def update_student_response(self, assignment_id, student_id, question_id, selected_answer):
        """Record student's answer to a question"""
        response_data = {
            "assignment_id": ObjectId(assignment_id),
            "student_id": ObjectId(student_id),
            "question_id": question_id,
            "selected_answer": selected_answer,
            "timestamp": datetime.now()
        }
        
        # Update if exists, insert if new
        self.responses_collection.update_one(
            {
                "assignment_id": ObjectId(assignment_id),
                "student_id": ObjectId(student_id),
                "question_id": question_id
            },
            {"$set": response_data},
            upsert=True
        )
        
    def get_student_response(self, assignment_id, student_id, question_id):
        """Get student's previous response to a question"""
        return self.responses_collection.find_one({
            "assignment_id": ObjectId(assignment_id),
            "student_id": ObjectId(student_id),
            "question_id": question_id
        })