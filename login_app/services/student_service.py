from database.db_connection import get_user_collection, get_question_collection, get_assignment_collection, get_db
from bson.objectid import ObjectId
from datetime import datetime
from utils.progress_tracking import ProgressTracker  # ✅ Import ProgressTracker

progress_tracker = ProgressTracker()  # ✅ Initialize ProgressTracker

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

        # Track processed sub-topics to avoid duplicates
        processed_sub_topics = set()
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

            # Skip if we've already processed this sub-topic
            if sub_topic in processed_sub_topics:
                print(f"Skipping duplicate sub-topic: {sub_topic}")
                continue

            processed_sub_topics.add(sub_topic)
            print(f"Looking for questions with topic: {topic} and sub-topic: {sub_topic}")
            
            # Get questions specific to this topic and subtopic
            questions = questions_collection.count_documents({
                "topic": topic,
                "sub_topic": sub_topic
            })
            print(f"Found {questions} questions for {topic} - {sub_topic}")

            # Get unique questions attempted by the student for this sub-topic
            subtopic_questions = list(questions_collection.find({
                "topic": topic,
                "sub_topic": sub_topic
            }))
            subtopic_question_ids = [q["_id"] for q in subtopic_questions]

            # Get attempts only for questions in this sub-topic
            attempted_questions = responses_collection.distinct(
                "question_id",
                {
                    "assignment_id": assignment["_id"],
                    "student_id": ObjectId(student_id),
                    "question_id": {"$in": subtopic_question_ids}
                }
            )

            # Count only unique question attempts
            attempted = len(attempted_questions)
            print(f"Found {attempted} attempted questions")

            # Count correct answers only for this sub-topic
            correct = responses_collection.count_documents({
                "assignment_id": assignment["_id"],
                "student_id": ObjectId(student_id),
                "question_id": {"$in": subtopic_question_ids},
                "is_correct": True
            })
            print(f"Found {correct} correct answers")

            # ✅ Fetch assignment status
            status = progress_tracker.get_assignment_status(assignment["_id"], student_id)

            progress_data.append({
                "topic": topic,
                "sub_topic": sub_topic,
                "total_questions": questions,
                "attempted": attempted,
                "correct": correct,
                "status": status  # ✅ Include assignment status
            })
            
        print(f"Final progress data: {progress_data}")
        return progress_data
        
    except Exception as e:
        print(f"ERROR in get_assignment_progress: {str(e)}")
        print(f"Error details: {str(e.__class__.__name__)}")
        return []

def resume_assignment(student_id, topic, sub_topic):
    """
    Resume or create assignment for a specific sub-topic.
    Each sub-topic gets its own assignment to track progress independently.
    """
    try:
        assignments = get_assignment_collection()
        topics = get_db()["topics"]
        
        topic_doc = topics.find_one({"name": topic})
        if not topic_doc:
            print(f"Topic not found: {topic}")
            return None

        print("Searching for assignment with:")
        print(f"student_id: {ObjectId(student_id)}")
        print(f"topic_id: {topic_doc['_id']}")
        print(f"sub_topic: {sub_topic}")
        
        # Look for an existing assignment for this specific sub-topic
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
            # Create new assignment specifically for this sub-topic
            print(f"Creating new assignment for sub-topic: {sub_topic}")
            new_assignment = {
                "students": [ObjectId(student_id)],
                "topic_id": topic_doc["_id"],
                "sub_topics": [sub_topic],
                "status": "active",
                "created_at": datetime.now()
            }
            result = assignments.insert_one(new_assignment)
            print(f"Created new assignment with ID: {result.inserted_id}")
            return str(result.inserted_id)
                
    except Exception as e:
        print(f"ERROR in resume_assignment: {str(e)}")
        print(f"Error details: {str(e.__class__.__name__)}")
        return None
