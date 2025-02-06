from database.db_connection import get_db
from bson.objectid import ObjectId

class ProgressTracker:
    def __init__(self):
        self.db = get_db()
        self.responses_collection = self.db["responses"]
        
    def get_assignment_progress(self, assignment_id, student_id):
        """Calculate student's progress in an assignment"""
        # Get total attempted questions
        attempted_questions = self.responses_collection.count_documents({
            "assignment_id": ObjectId(assignment_id),
            "student_id": ObjectId(student_id)
        })
        
        # Get total questions in assignment
        assignment = self.db["assignments"].find_one({"_id": ObjectId(assignment_id)})
        total_questions = len(assignment.get("sub_topics", [])) if assignment else 1
        total_questions = max(total_questions, 1)  # Ensure non-zero denominator
        
        # Calculate progress
        progress_decimal = min(attempted_questions / total_questions, 1.0)
        progress_percent = progress_decimal * 100
        
        return {
            "attempted": attempted_questions,
            "total": total_questions,
            "decimal": progress_decimal,
            "percent": progress_percent
        }
        
    def get_overall_student_progress(self, student_id):
        """Get overall progress across all assignments"""
        # Get all active assignments for student
        assignments = self.db["assignments"].find({
            "students": ObjectId(student_id),
            "status": "active"
        })
        
        total_progress = []
        for assignment in assignments:
            progress = self.get_assignment_progress(assignment["_id"], student_id)
            total_progress.append(progress)
            
        if not total_progress:
            return None
            
        # Calculate averages
        avg_progress = sum(p["decimal"] for p in total_progress) / len(total_progress)
        return {
            "average_progress": avg_progress,
            "average_percent": avg_progress * 100,
            "completed_assignments": sum(1 for p in total_progress if p["decimal"] >= 1.0),
            "total_assignments": len(total_progress)
        }
        
    def get_question_status(self, assignment_id, student_id, question_id):
        """Check if a specific question has been attempted"""
        response = self.responses_collection.find_one({
            "assignment_id": ObjectId(assignment_id),
            "student_id": ObjectId(student_id),
            "question_id": question_id
        })
        return response is not None