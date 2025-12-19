"""
Data Manager - Handles JSON file operations
Version: 2.2 - Added backward compatibility for enabled field
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
        # Create questions folder if it doesn't exist
        if not os.path.exists('./questions'):
            os.makedirs('./questions')
        
        subjects = {}
        for filename in os.listdir('./questions'):
            if filename.startswith(QUESTIONS_FILE_PREFIX) and filename.endswith(QUESTIONS_FILE_SUFFIX):
                subject_name = filename.replace(QUESTIONS_FILE_PREFIX, '').replace(QUESTIONS_FILE_SUFFIX, '')
                subjects[subject_name] = os.path.join('./questions', filename)
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
            
            # ===== BACKWARD COMPATIBILITY: Auto-migrate old data =====
            # Add 'enabled' field to lessons if missing
            for lesson in data['lessons']:
                if 'enabled' not in lesson:
                    lesson['enabled'] = True
                    print(f"  Migration: Added 'enabled=True' to lesson '{lesson.get('name', 'Unknown')}'")
            
            # Add 'enabled' field to questions if missing
            enabled_count = 0
            for question in data['questions']:
                if 'enabled' not in question:
                    question['enabled'] = True
                    enabled_count += 1
                
                # Also migrate old questions (add lessonId if missing)
                if 'lessonId' not in question:
                    question['lessonId'] = None
            
            if enabled_count > 0:
                print(f"  Migration: Added 'enabled=True' to {enabled_count} question(s)")
            # ===== END BACKWARD COMPATIBILITY =====
            
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
        # Ensure questions folder exists
        os.makedirs('./questions', exist_ok=True)

        filename = f"{QUESTIONS_FILE_PREFIX}{subject_name}{QUESTIONS_FILE_SUFFIX}"
        full_path = os.path.join('./questions', filename)
    
        # Check if already exists
        if os.path.exists(full_path):
            print(f"Error: Subject '{subject_name}' already exists")
            return None
    
        # Create subject with correct path
        subject = Subject(name=subject_name, filename=full_path)
    
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
            'enabled_questions': sum(1 for q in subject.questions if getattr(q, 'enabled', True)),
            'disabled_questions': sum(1 for q in subject.questions if not getattr(q, 'enabled', True)),
            'enabled_lessons': sum(1 for l in subject.lessons if getattr(l, 'enabled', True)),
            'disabled_lessons': sum(1 for l in subject.lessons if not getattr(l, 'enabled', True)),
            'questions_by_type': {},
            'questions_by_lesson': {},
            'questions_with_images': 0,
            'unassigned_questions': 0
        }
        
        # Count by type (only enabled)
        for q in subject.questions:
            if getattr(q, 'enabled', True):
                qtype = q.type
                stats['questions_by_type'][qtype] = stats['questions_by_type'].get(qtype, 0) + 1
        
        # Count by lesson (only enabled)
        for lesson in subject.lessons:
            if getattr(lesson, 'enabled', True):
                count = subject.get_enabled_questions_count(lesson.id)
                if count > 0:
                    stats['questions_by_lesson'][lesson.name] = count
        
        # Count unassigned (only enabled)
        stats['unassigned_questions'] = sum(
            1 for q in subject.get_questions_by_lesson(None) 
            if getattr(q, 'enabled', True)
        )
        
        # Count with images (only enabled)
        stats['questions_with_images'] = sum(
            1 for q in subject.questions 
            if q.questionImage and getattr(q, 'enabled', True)
        )
        
        return stats
    
    @staticmethod
    def migrate_subject_to_latest(subject: Subject) -> bool:
        """
        Migrate subject data to latest format and save
        This can be called manually if needed
        Returns: True if successful, False otherwise
        """
        try:
            migrated = False
            
            # Ensure all lessons have 'enabled' field
            for lesson in subject.lessons:
                if not hasattr(lesson, 'enabled'):
                    lesson.enabled = True
                    migrated = True
            
            # Ensure all questions have 'enabled' field
            for question in subject.questions:
                if not hasattr(question, 'enabled'):
                    question.enabled = True
                    migrated = True
            
            if migrated:
                print(f"Migrating subject '{subject.name}' to latest format...")
                if DataManager.save_subject(subject):
                    print(f"  ✓ Migration completed successfully")
                    return True
                else:
                    print(f"  ✗ Migration failed during save")
                    return False
            else:
                print(f"Subject '{subject.name}' is already up-to-date")
                return True
        
        except Exception as e:
            print(f"Error during migration: {str(e)}")
            return False