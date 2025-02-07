from database.db_connection import get_db
from bson.objectid import ObjectId
from collections import defaultdict

class ProgressTracker:
    def __init__(self):
        self.db = get_db()
        self.responses_collection = self.db["responses"]
        self.questions_collection = self.db["questions"]
        self.assignments_collection = self.db["assignments"]
        self.topics_collection = self.db["topics"]

    def get_assignment_progress(self, assignment_id, student_id):
        """Calculate student's progress in an assignment"""
        attempted_questions = self.responses_collection.count_documents({
            "assignment_id": ObjectId(assignment_id),
            "student_id": ObjectId(student_id)
        })
        
        assignment = self.assignments_collection.find_one({"_id": ObjectId(assignment_id)})
        total_questions = len(assignment.get("sub_topics", [])) if assignment else 1
        total_questions = max(total_questions, 1)  # Ensure non-zero denominator
        
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
        assignments = self.assignments_collection.find({
            "students": ObjectId(student_id),
            "status": "active"
        })
        
        total_progress = []
        for assignment in assignments:
            progress = self.get_assignment_progress(assignment["_id"], student_id)
            total_progress.append(progress)
            
        if not total_progress:
            return None
            
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

    def get_subtopic_progress(self, student_id):
        """Fetch student performance by sub-topic and difficulty level (Easy, Medium, Hard)."""
        responses = list(self.responses_collection.find({"student_id": ObjectId(student_id)}))

        progress_data = {}
        for response in responses:
            question = self.questions_collection.find_one({"_id": response["question_id"]})
            if question:
                sub_topic = question["sub_topic"]
                topic_id = question["topic_id"]
                
                total_questions_count = self.questions_collection.count_documents({"sub_topic": sub_topic})
                topic_doc = self.topics_collection.find_one({"_id": topic_id})
                topic_name = topic_doc["name"] if topic_doc else "Unknown Topic"

                if sub_topic not in progress_data:
                    progress_data[sub_topic] = {
                        "topic_name": topic_name,
                        "total_questions": total_questions_count,
                        "Easy": {"attempted": 0, "correct": 0},
                        "Medium": {"attempted": 0, "correct": 0},
                        "Hard": {"attempted": 0, "correct": 0}
                    }

                difficulty = question["difficulty"]
                progress_data[sub_topic][difficulty]["attempted"] += 1

                if response["is_correct"]:
                    progress_data[sub_topic][difficulty]["correct"] += 1

        student_progress = []
        for sub_topic, levels in progress_data.items():
            student_progress.append({
                "topic_name": levels["topic_name"],
                "sub_topic": sub_topic,
                "total_questions": levels["total_questions"],
                "Easy": {
                    "attempted": levels["Easy"]["attempted"],
                    "correct": levels["Easy"]["correct"],
                    "accuracy": (levels["Easy"]["correct"] / levels["Easy"]["attempted"] * 100) if levels["Easy"]["attempted"] > 0 else 0
                },
                "Medium": {
                    "attempted": levels["Medium"]["attempted"],
                    "correct": levels["Medium"]["correct"],
                    "accuracy": (levels["Medium"]["correct"] / levels["Medium"]["attempted"] * 100) if levels["Medium"]["attempted"] > 0 else 0
                },
                "Hard": {
                    "attempted": levels["Hard"]["attempted"],
                    "correct": levels["Hard"]["correct"],
                    "accuracy": (levels["Hard"]["correct"] / levels["Hard"]["attempted"] * 100) if levels["Hard"]["attempted"] > 0 else 0
                }
            })

        return student_progress

    def get_assignment_status(self, assignment_id, student_id):
        """Fetch assignment status for a student."""
        assignment = self.assignments_collection.find_one({"_id": ObjectId(assignment_id)})
        if not assignment:
            return {"status": "Assignment not found"}

        progress = self.get_assignment_progress(assignment_id, student_id)

        if progress["percent"] == 100:
            return {"status": "Completed"}
        elif progress["percent"] > 0:
            return {"status": "In Progress"}
        else:
            return {"status": "Not Started"}
