
from database.db_connection import get_user_collection, get_question_collection, get_assignment_collection, get_db
from bson.objectid import ObjectId
from datetime import datetime
from utils.progress_tracking import ProgressTracker

progress_tracker = ProgressTracker()

def get_assignment_progress(student_id):
    """Fetch assignment progress for the student."""
    try:
        db = get_db()
        assignments_collection = get_assignment_collection()
        topics_collection = db["topics"]
        questions_collection = db["questions"]
        responses_collection = db["responses"]

        print(f"Fetching progress for student_id: {student_id}")
        
        # Get all active assignments for the student
        active_assignments = list(assignments_collection.find(
            {"students": ObjectId(student_id), "status": "active"}
        ))
        print(f"Found active assignments: {len(active_assignments)}")

        progress_data = []

        for assignment in active_assignments:
            print(f"Processing assignment: {assignment['_id']}")
            
            # Get topic data
            topic_data = topics_collection.find_one({"_id": assignment["topic_id"]})
            if not topic_data:
                continue
                
            topic = topic_data.get("name")
            sub_topic = assignment.get("sub_topics", [])[0] if assignment.get("sub_topics") else None

            # Properly handle the deadline
            deadline = assignment.get("deadline")
            if isinstance(deadline, datetime):
                deadline = deadline.strftime("%Y-%m-%d")
            elif deadline is None:
                deadline = "2025-02-22"  # Set a default deadline if none exists
            
            print(f"Deadline for assignment {assignment['_id']}: {deadline}")

            if not topic or not sub_topic:
                continue

            # Get total questions for this topic and subtopic
            total_questions = questions_collection.count_documents({
                "topic": topic,
                "sub_topic": sub_topic
            })

            # Get responses for this specific assignment
            responses = list(responses_collection.find({
                "student_id": ObjectId(student_id),
                "assignment_id": ObjectId(str(assignment["_id"]))
            }))
            
            attempted = len(responses)
            correct = sum(1 for r in responses if r.get("is_correct", False))

            progress_data.append({
                "assignment_id": str(assignment["_id"]),  # <--- add this
                "topic": topic,
                "sub_topic": sub_topic,
                "total_questions": total_questions,
                "attempted": attempted,
                "correct": correct,
                "deadline": deadline  # Now properly formatted
            })
            
        return progress_data
        
    except Exception as e:
        print(f"ERROR in get_assignment_progress: {str(e)}")
        return []
    
    
def resume_assignment(student_id, topic, sub_topic):
    """Resume or create assignment for a specific sub-topic."""
    try:
        assignments = get_assignment_collection()
        topics = get_db()["topics"]
        
        topic_doc = topics.find_one({"name": topic})
        if not topic_doc:
            print(f"Topic not found: {topic}")
            return None

        # Look for an existing assignment
        assignment = assignments.find_one({
            "students": ObjectId(student_id),
            "topic_id": topic_doc["_id"],
            "sub_topics": [sub_topic],
            "status": "active"
        })
        
        if assignment:
            print(f"Found existing assignment for sub-topic: {sub_topic}")
            return str(assignment["_id"])
        else:
            # Create new assignment with deadline
            new_assignment = {
                "students": [ObjectId(student_id)],
                "topic_id": topic_doc["_id"],
                "sub_topics": [sub_topic],
                "status": "active",
                "created_at": datetime.now(),
                "deadline": datetime(2025, 2, 22)  # Set deadline to Feb 22, 2025
            }
            result = assignments.insert_one(new_assignment)
            print(f"Created new assignment with ID: {result.inserted_id}")
            return str(result.inserted_id)
                
    except Exception as e:
        print(f"ERROR in resume_assignment: {str(e)}")
        return None
