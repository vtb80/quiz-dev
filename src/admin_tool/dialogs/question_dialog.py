"""
Question Dialog - Create/Edit questions
Version: 3.0 - Fully Modularized All Question Types
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys

# Add path for imports if needed
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared.models import *
from shared.constants import QUESTION_TYPES, QUESTION_TYPE_NAMES, OTHERS_CATEGORY

# Import all modular forms
from admin_tool.dialogs.question_forms import (
    MultipleChoiceForm,
    TrueFalseForm,
    FillInBlankForm,
    MatchingForm,
    ReorderingForm,
    ReadingComprehensionForm
)

# Import image helper for save operations
try:
    from utils.image_helper import copy_image_to_subject, validate_scale, DEFAULT_SCALE
    IMAGE_HELPER_AVAILABLE = True
except ImportError:
    IMAGE_HELPER_AVAILABLE = False


class QuestionDialog:
    """Dialog for creating and editing questions"""
    
    def __init__(self, parent, subject, lesson_id, mode, question=None, callback=None, parent_app=None):
        if parent_app and parent_app.dialog_open:
            return
        
        if parent_app:
            parent_app.dialog_open = True
        
        self.parent = parent
        self.subject = subject
        self.lesson_id = lesson_id
        self.mode = mode
        self.question = question
        self.callback = callback
        self.parent_app = parent_app
        
        self.original_type = question.type if question else None
        self.original_data = {}
        
        # Current form instance
        self.current_form = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"{mode.capitalize()} Question")
        screen_width = self.dialog.winfo_screenwidth()
        screen_height = self.dialog.winfo_screenheight()
        dialog_width = int(screen_width * 0.7)
        dialog_height = int(screen_height * 0.7)
        self.dialog.geometry(f"{dialog_width}x{dialog_height}")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        self.type_var = tk.StringVar(value=question.type if question else "multiple_choice")
        
        self.setup_ui()
        
        if mode == "edit" and question:
            # Data loading is handled by individual forms
            pass
        
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def on_close(self):
        if self.parent_app:
            self.parent_app.dialog_open = False
        self.dialog.destroy()
    
    def setup_ui(self):
        """Setup dialog UI"""
        # Lesson selector
        lesson_frame = ttk.Frame(self.dialog)
        lesson_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Label(lesson_frame, text="Assign to Lesson:", 
                 font=('', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        # Build lesson options
        lesson_names = [OTHERS_CATEGORY] + [l.name for l in self.subject.lessons]
        lesson_ids = [None] + [l.id for l in self.subject.lessons]
        self.lesson_mapping = dict(zip(lesson_names, lesson_ids))
        
        self.lesson_var = tk.StringVar()
        self.lesson_combo = ttk.Combobox(lesson_frame, textvariable=self.lesson_var,
                                         values=lesson_names, state="readonly", 
                                         width=25, font=('', 10))
        self.lesson_combo.pack(side=tk.LEFT, padx=5)
        
        # Pre-select lesson if provided
        if self.lesson_id:
            lesson = self.subject.get_lesson_by_id(self.lesson_id)
            if lesson:
                self.lesson_combo.set(lesson.name)
            else:
                self.lesson_combo.set(OTHERS_CATEGORY)
        else:
            self.lesson_combo.set(OTHERS_CATEGORY)
        
        # Type selector
        type_frame = ttk.Frame(self.dialog)
        type_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        
        ttk.Label(type_frame, text="Question Type:", font=('', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        type_combo = ttk.Combobox(type_frame, textvariable=self.type_var,
                                  values=QUESTION_TYPES, state="readonly", width=25, font=('', 10))
        type_combo.pack(side=tk.LEFT, padx=5)
        type_combo.bind('<<ComboboxSelected>>', self.on_type_change)
        
        # Scrollable content frame
        canvas_frame = ttk.Frame(self.dialog)
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        canvas = tk.Canvas(canvas_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        self.content_frame = ttk.Frame(canvas)
        
        canvas.create_window((0, 0), window=self.content_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Update scroll region when content changes
        self.content_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        
        self.update_form()
        
        # Buttons
        btn_frame = ttk.Frame(self.dialog)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Save", command=self.save, width=15).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancel", command=self.on_close, width=15).pack(side=tk.LEFT, padx=5)
    
    def on_type_change(self, event=None):
        """Handle question type change"""
        if self.original_type:
            self.save_current_form_data()
        
        self.update_form()
        
        # Note: Type conversion data restoration not implemented for modular forms yet
        # Would require implementing a data injection method in each form
    
    def save_current_form_data(self):
        """Save current form data before type change"""
        if self.current_form:
            data = self.current_form.collect_data()
            if data:
                self.original_data = data
    
    def update_form(self):
        """Update form based on question type"""
        # Clear previous form
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Clean up previous form instance
        if self.current_form:
            self.current_form.cleanup()
            self.current_form = None
        
        qtype = self.type_var.get()
        
        # Create appropriate form based on type
        if qtype == "multiple_choice":
            self.current_form = MultipleChoiceForm(
                self.content_frame, self.subject, self.lesson_id, self.mode,
                self.question if self.mode == "edit" and isinstance(self.question, MultipleChoiceQuestion) else None
            )
        
        elif qtype == "true_false":
            self.current_form = TrueFalseForm(
                self.content_frame, self.subject, self.lesson_id, self.mode,
                self.question if self.mode == "edit" and isinstance(self.question, TrueFalseQuestion) else None
            )
        
        elif qtype == "fill_in_blank":
            self.current_form = FillInBlankForm(
                self.content_frame, self.subject, self.lesson_id, self.mode,
                self.question if self.mode == "edit" and isinstance(self.question, FillInBlankQuestion) else None
            )
        
        elif qtype == "matching":
            self.current_form = MatchingForm(
                self.content_frame, self.subject, self.lesson_id, self.mode,
                self.question if self.mode == "edit" and isinstance(self.question, MatchingQuestion) else None
            )
        
        elif qtype == "reordering":
            self.current_form = ReorderingForm(
                self.content_frame, self.subject, self.lesson_id, self.mode,
                self.question if self.mode == "edit" and isinstance(self.question, ReorderingQuestion) else None
            )
        
        elif qtype == "reading_comprehension":
            self.current_form = ReadingComprehensionForm(
                self.content_frame, self.subject, self.lesson_id, self.mode,
                self.question if self.mode == "edit" and isinstance(self.question, ReadingComprehensionQuestion) else None
            )
    
    def get_selected_lesson_id(self):
        """Get the lesson ID selected in the lesson dropdown"""
        selected_name = self.lesson_var.get()
        return self.lesson_mapping.get(selected_name)
    
    def save(self):
        """Save question"""
        try:
            qtype = self.type_var.get()
            question_id = self.question.id if self.mode == "edit" else self.subject.get_next_question_id()
            selected_lesson_id = self.get_selected_lesson_id()
            
            # Validate
            is_valid, error = self.current_form.validate()
            if not is_valid:
                messagebox.showerror("Validation Error", error)
                return
            
            # Collect data
            data = self.current_form.collect_data()
            if not data:
                messagebox.showerror("Error", "Failed to collect form data")
                return
            
            # Check for errors in collected data (from matching/reading comp)
            if 'error' in data:
                messagebox.showerror("Validation Error", data['error'])
                return
            
            # Create question based on type
            if qtype == "multiple_choice":
                new_question = self.create_multiple_choice(question_id, selected_lesson_id, data)
            elif qtype == "true_false":
                new_question = self.create_true_false(question_id, selected_lesson_id, data)
            elif qtype == "fill_in_blank":
                new_question = self.create_fill_blank(question_id, selected_lesson_id, data)
            elif qtype == "matching":
                new_question = self.create_matching(question_id, selected_lesson_id, data)
            elif qtype == "reordering":
                new_question = self.create_reordering(question_id, selected_lesson_id, data)
            elif qtype == "reading_comprehension":
                new_question = self.create_reading_comp(question_id, selected_lesson_id, data)
            else:
                messagebox.showerror("Error", f"Unknown question type: {qtype}")
                return
            
            # Save to subject
            if self.mode == "add":
                self.subject.add_question(new_question)
            else:
                self.subject.update_question(question_id, new_question)
            
            # Save subject to file
            from shared.data_manager import DataManager
            if DataManager.save_subject(self.subject):
                if self.parent_app:
                    self.parent_app.dialog_open = False
                
                self.dialog.destroy()
                
                if self.callback:
                    self.callback(self.mode, question_id)
                
                messagebox.showinfo("Success", f"Question {self.mode}ed successfully!")
            else:
                messagebox.showerror("Error", "Failed to save question")
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", f"Save failed: {str(e)}")
    
    def create_multiple_choice(self, question_id, lesson_id, data):
        """Create Multiple Choice question from data"""
        new_question = MultipleChoiceQuestion(
            id=question_id,
            type='multiple_choice',
            lessonId=lesson_id,
            question=data['question'],
            options=data['options'],
            correct=data['correct']
        )
        
        # Handle question image
        if 'questionImage' in data:
            new_question.questionImage = data['questionImage']
            new_question.questionImageScale = data.get('questionImageScale', DEFAULT_SCALE)
        
        # Handle option images
        if data.get('use_option_images'):
            option_images = {}
            for i, img_path in data.get('option_images_temp', {}).items():
                if img_path.startswith('images/'):
                    option_images[str(i)] = img_path
                else:
                    rel_path = copy_image_to_subject(img_path, self.subject.name, question_id, f'option_{i}')
                    if rel_path:
                        option_images[str(i)] = rel_path
            
            new_question.optionImages = option_images
            new_question.optionImageScale = data.get('option_scale', DEFAULT_SCALE)
        
        return new_question
    
    def create_true_false(self, question_id, lesson_id, data):
        """Create True/False question from data"""
        return TrueFalseQuestion(
            id=question_id,
            type='true_false',
            lessonId=lesson_id,
            question=data['question'],
            correct=data['correct']
        )
    
    def create_fill_blank(self, question_id, lesson_id, data):
        """Create Fill in Blank question from data"""
        new_question = FillInBlankQuestion(
            id=question_id,
            type='fill_in_blank',
            lessonId=lesson_id,
            question=data['question'],
            correct=data['answers']
        )
        
        # Handle question image
        if 'questionImage' in data:
            new_question.questionImage = data['questionImage']
            new_question.questionImageScale = data.get('questionImageScale', DEFAULT_SCALE)
        
        return new_question
    
    def create_matching(self, question_id, lesson_id, data):
        """Create Matching question from data"""
        return MatchingQuestion(
            id=question_id,
            type='matching',
            lessonId=lesson_id,
            question=data['question'],
            pairs=data['pairs'],
            correct=data['correct']
        )
    
    def create_reordering(self, question_id, lesson_id, data):
        """Create Reordering question from data"""
        return ReorderingQuestion(
            id=question_id,
            type='reordering',
            lessonId=lesson_id,
            question=data['question'],
            items=data['items']
        )
    
    def create_reading_comp(self, question_id, lesson_id, data):
        """Create Reading Comprehension question from data"""
        return ReadingComprehensionQuestion(
            id=question_id,
            type='reading_comprehension',
            lessonId=lesson_id,
            passage=data['passage'],
            passageId=f"passage_{question_id}",
            questions=data['sub_questions']
        )
