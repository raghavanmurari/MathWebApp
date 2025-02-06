from database.db_connection import get_user_collection, get_question_collection, get_assignment_collection, get_db
from bson.objectid import ObjectId


def get_all_students():
    """Fetch all students from the database."""
    try:
        users = get_user_collection()
        students = users.find(
            {"role": "student"}, 
            {"name": 1, "email": 1, "parent_email": 1, "role": 1, "active": 1, "_id": 0}
        )
        return list(students)
    except Exception as e:
        print(f"ERROR in get_all_students: {str(e)}")
        return []

def get_student_question_stats(student_id):
    """Fetch question statistics (assigned, attempted, correct) per sub-topic for a student."""
    try:
        questions = get_question_collection()
        
        pipeline = [
            {"$match": {"student_id": student_id}},  # Filter by student
            {"$group": {
                "_id": "$sub_topic",
                "total_questions": {"$sum": 1},
                "attempted": {"$sum": {"$cond": [{"$ifNull": ["$attempted", False]}, 1, 0]}}},
                "correct": {"$sum": {"$cond": [{"$eq": ["$is_correct", True]}, 1, 0]}}}
            ]
        
        result = list(questions.aggregate(pipeline))
        return result

    except Exception as e:
        print(f"ERROR in get_student_question_stats: {str(e)}")
        return []

def get_assignment_progress(student_id):
    """Fetch assignment progress for the student."""
    try:
        db = get_db()
        assignments_collection = get_assignment_collection()
        topics_collection = db["topics"]
        questions_collection = db["questions"]
        responses_collection = db["responses"]  # Add this line here

        active_assignments = list(assignments_collection.find(
            {"students": ObjectId(student_id), "status": "active"}
        ))

        progress_data = []
        for assignment in active_assignments:
            # ✅ Fetch topic name from topics collection
            topic_data = topics_collection.find_one({"_id": assignment["topic_id"]})
            topic = topic_data.get("name", "Unknown Topic") if topic_data else "Unknown Topic"

            # ✅ Extract first sub-topic from array
            sub_topic = assignment.get("sub_topics", ["Unknown Sub-topic"])[0]

            # ✅ Fetch total questions using topic name and sub-topic
            total_questions = questions_collection.count_documents({
                "topic": topic,  # ✅ Match questions based on topic name
                "sub_topic": sub_topic  # ✅ Match based on sub-topic
            })

            attempted = responses_collection.count_documents({
                "assignment_id": assignment["_id"],
                "student_id": ObjectId(student_id)
            })

            correct = responses_collection.count_documents({
                "assignment_id": assignment["_id"],
                "student_id": ObjectId(student_id),
                "is_correct": True
            })

            progress_data.append({
                "topic": topic,  # ✅ Correct topic name
                "sub_topic": sub_topic,  # ✅ Correct sub-topic name
                "total_questions": total_questions,  # ✅ Should now show correct values
                "attempted": attempted,
                "correct": correct
            })

        return progress_data
    except Exception as e:
        print(f"ERROR in get_assignment_progress: {str(e)}")
        return []

def resume_assignment(student_id, topic, sub_topic):
    try:
        assignments = get_assignment_collection()
        topics = get_db()["topics"]
        
        topic_doc = topics.find_one({"name": topic})
        if topic_doc:
            print("Searching for assignment with:")
            print(f"student_id: {ObjectId(student_id)}")
            print(f"topic_id: {topic_doc['_id']}")
            
            assignment = assignments.find_one({
                "students": ObjectId(student_id),  # Changed from student_id to students
                "topic_id": topic_doc["_id"],
                "status": "active"
            })
            print(f"Found assignment: {assignment}")
            return str(assignment["_id"]) if assignment else None
    except Exception as e:
            print(f"ERROR in resume_assignment: {str(e)}")
            return None