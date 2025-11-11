"""
Reading Comprehension Question Form with Image Support
Replace: src/admin_tool/dialogs/question_forms/reading_comp_form.py
Version: 2.0 - Added image support
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from typing import Optional, Dict, Any, Tuple

from shared.models import Subject, Question, ReadingComprehensionQuestion
from shared.validators import QuestionValidator
from admin_tool.dialogs.question_forms.base_form import BaseQuestionForm

# Import image helper
try:
    from utils.image_helper import (
        select_image_file,
        copy_image_to_subject,
        create_image_preview,
        get_image_info,
        format_file_size,
        validate_scale,
        DEFAULT_SCALE
    )
    IMAGE_HELPER_AVAILABLE = True
except ImportError:
    IMAGE_HELPER_AVAILABLE = False
    print("Warning: image_helper not available, image features disabled")


class ReadingComprehensionForm(BaseQuestionForm):
    """Form for Reading Comprehension questions"""
    
    def __init__(self, parent_frame: ttk.Frame, subject: Subject, 
                 lesson_id: Optional[str], mode: str, question: Optional[ReadingComprehensionQuestion] = None):
        super().__init__(parent_frame, subject, lesson_id, mode, question)
        
        # Render and load
        self.render()
        if mode == "edit" and question:
            self.load_data()
    
    def render(self):
        """Render Reading Comprehension form"""
        # Passage
        ttk.Label(self.parent_frame, text="Passage:", font=('', 10, 'bold')).pack(anchor=tk.W, pady=(5, 0))
        self.passage_text = tk.Text(self.parent_frame, height=7, font=('', 10))
        self.passage_text.pack(fill=tk.X, pady=5)
        
        # Question Image Upload
        if IMAGE_HELPER_AVAILABLE:
            self._add_question_image_control()
        
        # Questions
        ttk.Label(self.parent_frame, text="Questions (format: Q | Opt1 | Opt2 | Opt3 | Opt4 | CorrectIdx):",
                 font=('', 10, 'bold')).pack(anchor=tk.W, pady=(10, 0))
        ttk.Label(self.parent_frame, text="Example: What is blue? | Red | Blue | Green | Yellow | 1",
                 foreground='gray', font=('', 9)).pack(anchor=tk.W)
        ttk.Label(self.parent_frame, text="Enter one question per line", 
                 foreground='gray', font=('', 9)).pack(anchor=tk.W)
        ttk.Label(self.parent_frame, text="Correct index is 0-based (0 = first option)", 
                 foreground='gray', font=('', 9)).pack(anchor=tk.W)
        
        self.questions_text = tk.Text(self.parent_frame, height=7, font=('', 10))
        self.questions_text.pack(fill=tk.BOTH, expand=True, pady=5)
    
    def _add_question_image_control(self):
        """Add question image upload control"""
        img_frame = ttk.LabelFrame(self.parent_frame, text="Question Image (Optional)")
        img_frame.pack(fill=tk.X, pady=10)
        
        btn_frame = ttk.Frame(img_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.question_img_path_var = tk.StringVar(value="")
        self.question_img_label = ttk.Label(btn_frame, textvariable=self.question_img_path_var, 
                                            foreground='gray', font=('', 8))
        self.question_img_label.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="📷 Select Image", 
                  command=self._select_question_image).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="✕ Remove", 
                  command=self._remove_question_image).pack(side=tk.LEFT, padx=5)
        
        # Scale control
        scale_frame = ttk.Frame(img_frame)
        scale_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Label(scale_frame, text="Scale:", font=('', 9)).pack(side=tk.LEFT, padx=5)
        self.question_scale_var = tk.IntVar(value=DEFAULT_SCALE)
        ttk.Spinbox(scale_frame, from_=25, to=200, increment=25,
                   textvariable=self.question_scale_var, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Label(scale_frame, text="%").pack(side=tk.LEFT)
        
        # Preview frame
        self.question_preview_frame = ttk.Frame(img_frame)
        self.question_preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.image_controls['question'] = {
            'path_var': self.question_img_path_var,
            'scale_var': self.question_scale_var,
            'preview_frame': self.question_preview_frame,
            'photo_ref': None
        }
    
    def _select_question_image(self):
        """Select question image"""
        filepath = select_image_file(self.parent_frame, "Select Question Image")
        if filepath:
            self.temp_image_paths['question'] = filepath
            self.image_controls['question']['path_var'].set(os.path.basename(filepath))
            self._update_question_image_preview()
    
    def _remove_question_image(self):
        """Remove question image"""
        if 'question' in self.temp_image_paths:
            del self.temp_image_paths['question']
        self.image_controls['question']['path_var'].set("")
        self._update_question_image_preview()
    
    def _update_question_image_preview(self):
        """Update question image preview"""
        preview_frame = self.image_controls['question']['preview_frame']
        
        # Clear preview
        for widget in preview_frame.winfo_children():
            widget.destroy()
        
        if 'question' not in self.temp_image_paths:
            return
        
        filepath = self.temp_image_paths['question']
        if not os.path.exists(filepath):
            ttk.Label(preview_frame, text="⚠ Image file not found", 
                     foreground='orange', font=('', 9)).pack(pady=5)
            return
        
        scale = self.image_controls['question']['scale_var'].get()
        photo, w, h = create_image_preview(filepath, max_width=400, scale_percent=scale)
        
        if photo:
            self.image_controls['question']['photo_ref'] = photo
            label = tk.Label(preview_frame, image=photo)
            label.pack(pady=5)
            
            info = get_image_info(filepath)
            if info:
                info_text = f"{info['width']}x{info['height']} • {format_file_size(info['size'])}"
                ttk.Label(preview_frame, text=info_text, font=('', 8), 
                         foreground='gray').pack()
    
    def load_data(self):
        """Load data from question object (edit mode)"""
        if not self.question:
            return
        
        # Load passage
        self.passage_text.insert('1.0', self.question.passage)
        
        # Load question image
        if IMAGE_HELPER_AVAILABLE and hasattr(self.question, 'questionImage') and self.question.questionImage:
            self.temp_image_paths['question'] = self.question.questionImage
            self.image_controls['question']['path_var'].set(os.path.basename(self.question.questionImage))
            
            if hasattr(self.question, 'questionImageScale'):
                self.image_controls['question']['scale_var'].set(self.question.questionImageScale)
            
            self._update_question_image_preview()
        
        # Load sub-questions
        questions_text = []
        for sq in self.question.questions:
            line = f"{sq.get('question')} | " + " | ".join(sq.get('options', [])) + f" | {sq.get('correct')}"
            questions_text.append(line)
        
        self.questions_text.insert('1.0', '\n'.join(questions_text))
    
    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect data from form"""
        try:
            data = {}
            
            # Passage text
            data['passage'] = self.passage_text.get('1.0', tk.END).strip()
            
            # Question image
            if 'question' in self.temp_image_paths:
                img_path = self.temp_image_paths['question']
                if img_path.startswith('images/'):
                    data['questionImage'] = img_path
                    data['questionImageScale'] = self.image_controls['question']['scale_var'].get()
                else:
                    q_id = self.question.id if self.question else None
                    if q_id:
                        rel_path = copy_image_to_subject(img_path, self.subject.name, q_id, 'main')
                        if rel_path:
                            data['questionImage'] = rel_path
                            data['questionImageScale'] = validate_scale(
                                self.image_controls['question']['scale_var'].get()
                            )
            
            # Parse sub-questions
            lines = [l.strip() for l in self.questions_text.get('1.0', tk.END).split('\n') 
                    if l.strip()]
            
            sub_questions = []
            
            for i, line in enumerate(lines):
                if ' | ' not in line:
                    data['error'] = f"Line {i+1}: Invalid format. Use: Q | Opt1 | Opt2 | Opt3 | Opt4 | CorrectIdx"
                    return data
                
                parts = [p.strip() for p in line.split(' | ')]
                
                if len(parts) < 6:
                    data['error'] = f"Line {i+1}: Need at least 4 options. Format: Q | Opt1 | Opt2 | Opt3 | Opt4 | CorrectIdx"
                    return data
                
                # Extract question, options, and correct index
                question_text = parts[0]
                options = parts[1:-1]
                
                try:
                    correct_idx = int(parts[-1])
                except ValueError:
                    data['error'] = f"Line {i+1}: Correct index must be a number"
                    return data
                
                if correct_idx < 0 or correct_idx >= len(options):
                    data['error'] = f"Line {i+1}: Correct index {correct_idx} is out of range (0-{len(options)-1})"
                    return data
                
                sub_questions.append({
                    "id": f"q{i+1}",
                    "question": question_text,
                    "options": options,
                    "correct": correct_idx
                })
            
            data['sub_questions'] = sub_questions
            
            return data
            
        except Exception as e:
            print(f"Error collecting data: {str(e)}")
            return None
    
    def validate(self) -> Tuple[bool, str]:
        """Validate form data"""
        passage_text = self.passage_text.get('1.0', tk.END).strip()
        
        if not passage_text:
            return False, "Passage text is required"
        
        if len(passage_text) < 20:
            return False, "Passage is too short (minimum 20 characters)"
        
        # Collect and validate sub-questions
        data = self.collect_data()
        
        if not data:
            return False, "Failed to collect form data"
        
        if 'error' in data:
            return False, data['error']
        
        sub_questions = data.get('sub_questions', [])
        
        if len(sub_questions) < 1:
            return False, "At least 1 question is required"
        
        # Additional validation for each sub-question
        for i, sq in enumerate(sub_questions):
            if not sq.get('question'):
                return False, f"Question {i+1} text is empty"
            
            options = sq.get('options', [])
            if len(options) < 2:
                return False, f"Question {i+1} needs at least 2 options"
            
            for j, opt in enumerate(options):
                if not opt:
                    return False, f"Question {i+1}, option {j+1} is empty"
        
        return True, ""
