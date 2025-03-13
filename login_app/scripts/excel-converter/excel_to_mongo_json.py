import pandas as pd
import json
import os
from bson import ObjectId

def clean_value(value):
    """Clean and validate values to ensure MongoDB compatibility"""
    if pd.isna(value):
        return ""
    return str(value).strip()

def map_difficulty(difficulty):
    """Map numeric difficulty to Easy/Medium/Hard"""
    try:
        difficulty_num = int(float(str(difficulty).strip()))
        print(f"Processing difficulty: {difficulty} -> {difficulty_num}")
        
        if difficulty_num <= 2:
            return 'Easy'
        elif difficulty_num == 3:
            return 'Medium'
        elif difficulty_num >= 4:
            return 'Hard'
        else:
            print(f"Unexpected difficulty value: {difficulty_num}")
            return 'Medium'
    except Exception as e:
        print(f"Error processing difficulty value: {difficulty}, Error: {str(e)}")
        return 'Medium'

def get_section_mapping(excel_file):
    """Read sections tab and create section ID to name mapping"""
    try:
        sections_df = pd.read_excel(excel_file, sheet_name='sections')
        section_mapping = {}
        for _, row in sections_df.iterrows():
            section_id = clean_value(row['Section ID'])
            section_name = clean_value(row['Name'])
            combined_name = f"{section_id} - {section_name}"
            section_mapping[section_id] = combined_name
        print("Section mapping loaded:", section_mapping)
        return section_mapping
    except Exception as e:
        print(f"Warning: Could not read sections mapping: {str(e)}")
        return {}

def create_options_with_correct_answer(options_list, correct_answer):
    """Create options array with is_correct flag based on answer"""
    options = []
    answer_mapping = {
        'a': 0,  # option-1
        'b': 1,  # option-2
        'c': 2,  # option-3
        'd': 3   # option-4
    }
    
    correct_index = answer_mapping.get(str(correct_answer).strip().lower(), -1)
    
    for idx, option_text in enumerate(options_list):
        if pd.notna(option_text) and option_text != "":
            option = {
                "option_id": idx,
                "text": clean_value(option_text),
                "is_correct": (idx == correct_index)
            }
            options.append(option)
    return options

# First, create a custom JSON encoder class
class MongoJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return {"$oid": str(obj)}
        return super().default(obj)

def convert_excel_to_mongo_json(excel_file):
    try:
        # Read both sheets
        print(f"Reading Excel file: {excel_file}")
        df = pd.read_excel(excel_file)
        section_mapping = get_section_mapping(excel_file)
        
        # Filter out rows where 'No' column is null
        df = df[pd.notna(df['No'])]
        print(f"Found {len(df)} rows with non-null 'No' values")
        
        # Get the filename without extension for both output and topic
        base_filename = os.path.splitext(os.path.basename(excel_file))[0]
        output_file = f"{base_filename}.json"
        # topic = base_filename.split('_')[0] if '_' in base_filename else base_filename
        topic = base_filename
        # Generate a unique ObjectId for this topic - DO NOT convert to string
        topic_object_id = ObjectId()
        print(f"Generated ObjectId for topic '{topic}': {topic_object_id}")
        
        # Initialize list to store questions
        questions = []
        
        # Convert each row to required format
        for index, row in df.iterrows():
            # Get options with correct answer
            options_list = [
                row.get('option-1'), 
                row.get('option-2'), 
                row.get('option-3'), 
                row.get('option-4')
            ]
            correct_answer = row.get('Answer', '')
            options = create_options_with_correct_answer(options_list, correct_answer)
            
            # Get and map difficulty level
            raw_difficulty = row.get('Difficulty Level', 3)
            mapped_difficulty = map_difficulty(raw_difficulty)
            
            # Get section ID and map to actual name
            section_id = clean_value(row.get('Section', ''))
            section_name = section_mapping.get(section_id, section_id)
            
            # Create question document with cleaned values
            question = {
                "description": clean_value(row['Description']),
                "type": clean_value(row.get('Type', 'SCQ')),
                "options": options,
                "solution": clean_value(row.get('Solution', '')),
                "difficulty": mapped_difficulty,
                "topic": topic,
                "sub_topic": section_name,
                "prerequisites": [],
                "topic_id": topic_object_id  # Use the ObjectId directly (not converted to string)
            }
            
            questions.append(question)
        
        # Save each question as a separate line (MongoDB Compass format) with custom encoder
        with open(output_file, 'w', encoding='utf-8') as f:
            for question in questions:
                f.write(json.dumps(question, ensure_ascii=False, cls=MongoJSONEncoder) + '\n')
        
        print(f"\nSuccessfully converted {len(questions)} questions!")
        print(f"Output saved to: {output_file}")
        print(f"Topic set to: {topic}")
        print(f"Topic_id ObjectId: {topic_object_id}")
        print("\nDifficulty levels mapping:")
        print("1,2 -> Easy")
        print("3   -> Medium")
        print("4,5 -> Hard")
        
        if questions:
            print("\nSample of first converted question:")
            print(json.dumps(questions[0], indent=2, cls=MongoJSONEncoder))
            
        return questions
        
    except FileNotFoundError:
        print(f"Error: Excel file '{excel_file}' not found!")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        raise e

if __name__ == "__main__":
    excel_file = "F:/MathWebApp/Documents/QuestionBank/8/8_CubeAndCubeRoots.xlsx"
    convert_excel_to_mongo_json(excel_file)