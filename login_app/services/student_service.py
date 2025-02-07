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
                print(f"Topic not found for topic_id: {assignment['topic_id']}")
                continue
                
            topic = topic_data.get("name")
            sub_topic = assignment.get("sub_topics", [])[0] if assignment.get("sub_topics") else None
            
            if not topic or not sub_topic:
                print(f"Missing topic ({topic}) or sub_topic ({sub_topic})")
                continue

            print(f"Looking for questions with topic: {topic} and sub_topic: {sub_topic}")
            
            # Get questions specific to this topic and subtopic
            questions = questions_collection.count_documents({
                "topic": topic,
                "sub_topic": sub_topic
            })
            print(f"Found {questions} questions for {topic} - {sub_topic}")

            # Get responses for this specific assignment
            attempted = responses_collection.count_documents({
                "assignment_id": assignment["_id"],
                "student_id": ObjectId(student_id)
            })
            print(f"Found {attempted} attempted questions")

            correct = responses_collection.count_documents({
                "assignment_id": assignment["_id"],
                "student_id": ObjectId(student_id),
                "is_correct": True
            })
            print(f"Found {correct} correct answers")

            progress_data.append({
                "topic": topic,
                "sub_topic": sub_topic,
                "total_questions": questions,
                "attempted": attempted,
                "correct": correct
            })
            
        print(f"Final progress data: {progress_data}")
        return progress_data
        
    except Exception as e:
        print(f"ERROR in get_assignment_progress: {str(e)}")
        print(f"Error details: {str(e.__class__.__name__)}")
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