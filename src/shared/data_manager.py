"""
Data Manager - Handles JSON file operations
Version: 2.1
"""

import json
import os
from typing import Optional, List
from shared.models import Subject, Lesson, Question
from shared.constants import (
    QUESTIONS_FILE_PREFIX,
    QUESTIONS_FILE_SUFFIX,
    IMAGES_FOLDER
)


class DataManager:
    """Manages loading and saving of quiz data"""
    
    @staticmethod
    def discover_subjects() -> dict:
        """
        Discover all available subjects by scanning for JSON files
        Returns: dict {subject_name: filename}
        """
        subjects = {}
        for filename in os.listdir('./questions'):
            if filename.startswith(QUESTIONS_FILE_PREFIX) and filename.endswith(QUESTIONS_FILE_SUFFIX):
                subject_name = filename.replace(QUESTIONS_FILE_PREFIX, '').replace(QUESTIONS_FILE_SUFFIX, '')
                subjects[subject_name] = os.path.join('questions', filename)
        return subjects
    
    @staticmethod
    def load_subject(subject_name: str, filename: str) -> Optional[Subject]:
        """
        Load a subject from JSON file
        Returns: Subject object or None if failed
        """
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Ensure required structure
            if 'lessons' not in data:
                data['lessons'] = []
            if 'questions' not in data:
                data['questions'] = []
            
            # Migrate old questions (add lessonId if missing)
            for q in data['questions']:
                if 'lessonId' not in q:
                    q['lessonId'] = None
            
            subject = Subject.from_dict(subject_name, filename, data)
            return subject
        
        except FileNotFoundError:
            print(f"Error: File not found: {filename}")
            return None
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON in {filename}: {str(e)}")
            return None
        except Exception as e:
            print(f"Error loading subject: {str(e)}")
            return None
    
    @staticmethod
    def save_subject(subject: Subject) -> bool:
        """
        Save a subject to JSON file
        Returns: True if successful, False otherwise
        """
        try:
            data = subject.to_dict()
            
            with open(subject.filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
        
        except Exception as e:
            print(f"Error saving subject: {str(e)}")
            return False
    
    @staticmethod
    def create_subject(subject_name: str) -> Optional[Subject]:
        """
        Create a new subject with empty data
        Returns: Subject object or None if failed
        """
        filename = f"{QUESTIONS_FILE_PREFIX}{subject_name}{QUESTIONS_FILE_SUFFIX}"
        
        # Check if already exists
        if os.path.exists(filename):
            print(f"Error: Subject '{subject_name}' already exists")
            return None
        
        # Create subject
        subject = Subject(name=subject_name, filename=filename)
        
        # Save to file
        if DataManager.save_subject(subject):
            # Create images folder
            img_folder = os.path.join(IMAGES_FOLDER, subject_name)
            os.makedirs(img_folder, exist_ok=True)
            
            return subject
        
        return None
    
    @staticmethod
    def delete_subject(subject: Subject, delete_images: bool = True) -> bool:
        """
        Delete a subject and optionally its images
        Returns: True if successful, False otherwise
        """
        try:
            # Delete JSON file
            if os.path.exists(subject.filename):
                os.remove(subject.filename)
            
            # Delete images folder
            if delete_images:
                img_folder = os.path.join(IMAGES_FOLDER, subject.name)
                if os.path.exists(img_folder):
                    import shutil
                    shutil.rmtree(img_folder)
            
            return True
        
        except Exception as e:
            print(f"Error deleting subject: {str(e)}")
            return False
    
    @staticmethod
    def backup_subject(subject: Subject) -> Optional[str]:
        """
        Create a backup copy of subject file
        Returns: Backup filename or None if failed
        """
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{subject.filename}.backup_{timestamp}"
            
            import shutil
            shutil.copy2(subject.filename, backup_filename)
            
            return backup_filename
        
        except Exception as e:
            print(f"Error creating backup: {str(e)}")
            return None
    
    @staticmethod
    def validate_json_file(filename: str) -> tuple:
        """
        Validate a JSON file
        Returns: (is_valid, error_message)
        """
        if not os.path.exists(filename):
            return False, "File does not exist"
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check required structure
            if not isinstance(data, dict):
                return False, "Root must be an object"
            
            if 'questions' not in data:
                return False, "Missing 'questions' array"
            
            if not isinstance(data['questions'], list):
                return False, "'questions' must be an array"
            
            # Optional: validate lessons if present
            if 'lessons' in data and not isinstance(data['lessons'], list):
                return False, "'lessons' must be an array"
            
            return True, None
        
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    @staticmethod
    def export_subject(subject: Subject, export_path: str) -> bool:
        """
        Export subject to a different location
        Returns: True if successful, False otherwise
        """
        try:
            import shutil
            
            # Copy JSON file
            shutil.copy2(subject.filename, export_path)
            
            # Optionally copy images folder
            img_folder = os.path.join(IMAGES_FOLDER, subject.name)
            if os.path.exists(img_folder):
                export_img_folder = os.path.join(
                    os.path.dirname(export_path),
                    IMAGES_FOLDER,
                    subject.name
                )
                os.makedirs(os.path.dirname(export_img_folder), exist_ok=True)
                if os.path.exists(export_img_folder):
                    shutil.rmtree(export_img_folder)
                shutil.copytree(img_folder, export_img_folder)
            
            return True
        
        except Exception as e:
            print(f"Error exporting subject: {str(e)}")
            return False
    
    @staticmethod
    def get_subject_statistics(subject: Subject) -> dict:
        """
        Get statistics for a subject
        Returns: dict with various stats
        """
        stats = {
            'total_questions': len(subject.questions),
            'total_lessons': len(subject.lessons),
            'questions_by_type': {},
            'questions_by_lesson': {},
            'questions_with_images': 0,
            'unassigned_questions': 0
        }
        
        # Count by type
        for q in subject.questions:
            qtype = q.type
            stats['questions_by_type'][qtype] = stats['questions_by_type'].get(qtype, 0) + 1
        
        # Count by lesson
        for lesson in subject.lessons:
            count = len(subject.get_questions_by_lesson(lesson.id))
            stats['questions_by_lesson'][lesson.name] = count
        
        # Count unassigned
        stats['unassigned_questions'] = len(subject.get_questions_by_lesson(None))
        
        # Count with images
        stats['questions_with_images'] = sum(1 for q in subject.questions if q.questionImage)
        
        return stats