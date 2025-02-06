from database.db_connection import get_assignment_collection, get_db
from bson.objectid import ObjectId

class AssignmentManager:
    def __init__(self):
        self.assignments_collection = get_assignment_collection()
        self.db = get_db()
        self.topics_collection = self.db["topics"]
        
    def get_active_assignments(self, student_id):
        """Fetch all active assignments for a student"""
        return list(self.assignments_collection.find(
            {"students": ObjectId(student_id), "status": "active"}
        ))
        
    def get_assignment_topic(self, topic_id):
        """Get topic information for an assignment"""
        topic = self.topics_collection.find_one({"_id": ObjectId(topic_id)})
        return topic.get("name", "Untitled Assignment") if topic else "Untitled Assignment"
        
    def get_assignment_details(self, assignment_id):
        """Get detailed information about a specific assignment"""
        return self.assignments_collection.find_one({"_id": ObjectId(assignment_id)})
        
    def count_total_questions(self, assignment):
        """Get total number of questions in an assignment"""
        return max(len(assignment.get("sub_topics", [])), 1)
        
    def update_assignment_status(self, assignment_id, new_status):
        """Update the status of an assignment"""
        self.assignments_collection.update_one(
            {"_id": ObjectId(assignment_id)},
            {"$set": {"status": new_status}}
        )
        
    def get_assignment_subtopics(self, assignment_id):
        """Get all subtopics for an assignment"""
        assignment = self.get_assignment_details(assignment_id)
        return assignment.get("sub_topics", []) if assignment else []
        
    def verify_student_access(self, assignment_id, student_id):
        """Verify if a student has access to an assignment"""
        assignment = self.assignments_collection.find_one({
            "_id": ObjectId(assignment_id),
            "students": ObjectId(student_id)
        })
        return assignment is not None