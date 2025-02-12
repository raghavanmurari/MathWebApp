import random
import math

class AdaptiveQuiz:
    def __init__(self, questions):
        self.all_questions = questions
        self.current_level = "Medium"  # Starting level
        self.threshold_score = 65  # Passing threshold percentage
        self.question_percentage = 0.75  # 75% of questions to show
        self.current_path = "initial"  # Track which path user is on
        self.reports = []  # Store generated reports
        
    def filter_by_difficulty(self, difficulty):
        """Filter questions by difficulty level"""
        return [q for q in self.all_questions if q['difficulty'] == difficulty]
    
    def get_subset_questions(self, questions, percentage=0.75):
        """Get a subset of questions based on percentage"""
        num_questions = max(1, math.ceil(len(questions) * percentage))
        return random.sample(questions, num_questions)
    
    def calculate_score_percentage(self, score, total_questions):
        """Calculate score percentage"""
        return (score / total_questions) * 100 if total_questions > 0 else 0
    
    def mix_questions(self, medium_questions, easy_questions):
        """Mix medium and easy questions in 25:75 ratio"""
        medium_subset = self.get_subset_questions(medium_questions, 0.25)
        easy_subset = self.get_subset_questions(easy_questions, 0.75)
        mixed = medium_subset + easy_subset
        random.shuffle(mixed)
        return mixed
    
    def get_next_questions(self, current_score=0, total_questions=0):
        """Determine next set of questions based on performance"""
        score_percentage = self.calculate_score_percentage(current_score, total_questions)
        
        if self.current_path == "initial":
            medium_questions = self.filter_by_difficulty("Medium")
            if not medium_questions:  # Add check for empty questions
                self.current_path = "completed"
                return []
            self.current_path = "medium"
            self.current_level = "Medium"
            return self.get_subset_questions(medium_questions)
        
        elif self.current_path == "medium":
            if score_percentage >= self.threshold_score:
                hard_questions = self.filter_by_difficulty("Hard")
                if not hard_questions:  # Add check
                    self.current_path = "completed"
                    return []
                self.current_path = "hard"
                self.current_level = "Hard"
                return self.get_subset_questions(hard_questions)
            else:
                easy_questions = self.filter_by_difficulty("Easy")
                if not easy_questions:  # Add check
                    self.current_path = "completed"
                    return []
                self.current_path = "easy"
                self.current_level = "Easy"
                return self.get_subset_questions(easy_questions)
        
        elif self.current_path == "hard":
            if score_percentage < self.threshold_score:
                medium_questions = self.filter_by_difficulty("Medium")
                easy_questions = self.filter_by_difficulty("Easy")
                if not medium_questions or not easy_questions:  # Add check
                    self.current_path = "completed"
                    return []
                self.current_path = "mixed"
                self.current_level = "Mixed"
                return self.mix_questions(medium_questions, easy_questions)
            self.current_path = "completed"
            return []
        
        self.current_path = "completed"
        return []
    
    def generate_report(self, final_score, total_questions):
        """Generate performance report based on path and score"""
        score_percentage = self.calculate_score_percentage(final_score, total_questions)
        
        if self.current_path == "completed":
            if self.current_level == "Mixed":
                if score_percentage >= self.threshold_score:
                    return {
                        'message': "Good recovery! You're strong at Mixed level (combination of Easy and Medium questions) but need focused practice on Hard level questions before moving to the next topic.",
                        'score': score_percentage,
                        'path': 'Completed - Mixed Level'
                    }
                else:
                    return {
                        'message': "Continue practicing with Mixed level questions (combination of Easy and Medium) to build confidence before attempting Hard level again.",
                        'score': score_percentage,
                        'path': 'Completed - Practice Needed'
                    }
            elif self.current_level == "Hard":
                if score_percentage >= self.threshold_score:
                    return {
                        'message': "Excellent! You've shown strong understanding through Hard level. You're ready for the next topic.",
                        'score': score_percentage,
                        'path': 'Completed Successfully'
                    }
                else:
                    return {
                        'message': "You need more practice with Hard level questions before moving forward.",
                        'score': score_percentage,
                        'path': 'Completed - Practice Needed'
                    }
        elif self.current_path == "mixed":
            if score_percentage >= self.threshold_score:
                return {
                    'message': "Good progress! You're handling Mixed level questions well. Keep practicing Hard level questions to improve further.",
                    'score': score_percentage,
                    'path': 'Mixed Level Success'
                }
            else:
                return {
                    'message': "Continue practicing with Mixed level questions to build confidence before returning to Hard level.",
                    'score': score_percentage,
                    'path': 'Mixed Level - Practice Needed'
                }
        elif self.current_path == "hard":
            if score_percentage >= self.threshold_score:
                return {
                    'message': "Excellent! You've mastered all difficulty levels. Ready for advanced topics.",
                    'score': score_percentage,
                    'path': 'Hard Level Success'
                }
            else:
                return {
                    'message': "Moving you to Mixed level questions for additional practice before attempting full Hard level again.",
                    'score': score_percentage,
                    'path': 'Hard Level - Practice Needed'
                }
        elif self.current_path == "medium":
            if score_percentage >= self.threshold_score:
                return {
                    'message': "Great work! You've shown strong understanding at Medium level. Moving to Hard level questions.",
                    'score': score_percentage,
                    'path': 'Medium Level Success'
                }
            else:
                return {
                    'message': "You need more practice with Medium level questions before moving to harder topics.",
                    'score': score_percentage,
                    'path': 'Medium Level - Practice Needed'
                }
        elif self.current_path == "easy":
            if score_percentage >= self.threshold_score:
                return {
                    'message': "Good progress! You're ready to move up to Medium level questions.",
                    'score': score_percentage,
                    'path': 'Easy Level Success'
                }
            else:
                return {
                    'message': "Keep practicing Easy level questions to build a strong foundation.",
                    'score': score_percentage,
                    'path': 'Easy Level - Practice Needed'
                }
        
        return {
            'message': "Complete the quiz to receive personalized recommendations for your learning path.",
            'score': score_percentage,
            'path': 'Incomplete'
        }
    
    def is_quiz_completed(self):
        """Check if quiz is completed"""
        return self.current_path == "completed"
    
    def get_current_level(self):
        """Get current difficulty level"""
        return self.current_level
    
    def reset_quiz(self):
        """Reset quiz state"""
        self.current_level = "Medium"
        self.current_path = "initial"
        self.reports = []