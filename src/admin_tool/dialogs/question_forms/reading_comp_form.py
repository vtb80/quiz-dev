"""
Reading Comprehension Question Form
Handles creation and editing of reading comprehension questions
Version: 1.0
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any, Tuple

from shared.models import Subject, Question, ReadingComprehensionQuestion
from shared.validators import QuestionValidator
from admin_tool.dialogs.question_forms.base_form import BaseQuestionForm


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
    
    def load_data(self):
        """Load data from question object (edit mode)"""
        if not self.question:
            return
        
        # Load passage
        self.passage_text.insert('1.0', self.question.passage)
        
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
