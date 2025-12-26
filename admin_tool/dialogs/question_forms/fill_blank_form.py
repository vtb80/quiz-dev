"""
Fill in the Blank Question Form
Handles creation and editing of fill in the blank questions
Version: 2.0 - Added multi-blank support
"""

import tkinter as tk
from tkinter import ttk
import os
import re
from typing import Optional, Dict, Any, Tuple

from shared.models import Subject, Question, FillInBlankQuestion
from shared.validators import QuestionValidator
from shared.constants import (
    MAX_BLANKS_FILL,
    BLANK_PLACEHOLDER_PREFIX,
    BLANK_PLACEHOLDER_SUFFIX,
    BLANK_PLACEHOLDER_PATTERN
)
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


class FillInBlankForm(BaseQuestionForm):
    """Form for Fill in the Blank questions (single or multi-blank)"""
    
    def __init__(self, parent_frame: ttk.Frame, subject: Subject, 
                 lesson_id: Optional[str], mode: str, question: Optional[FillInBlankQuestion] = None):
        super().__init__(parent_frame, subject, lesson_id, mode, question)
        
        # Track blank answer widgets
        self.blank_frames = {}  # {blank_id: frame_widget}
        self.blank_text_widgets = {}  # {blank_id: text_widget}
        
        # Render and load
        self.render()
        if mode == "edit" and question:
            self.load_data()
    
    def render(self):
        """Render Fill in the Blank form"""
        # Question text
        ttk.Label(self.parent_frame, text="Question:", font=('', 10, 'bold')).pack(anchor=tk.W, pady=(5, 0))
        
        info_text = f"Use {BLANK_PLACEHOLDER_PREFIX}1{BLANK_PLACEHOLDER_SUFFIX}, {BLANK_PLACEHOLDER_PREFIX}2{BLANK_PLACEHOLDER_SUFFIX}, {BLANK_PLACEHOLDER_PREFIX}3{BLANK_PLACEHOLDER_SUFFIX}, etc. for multiple blanks"
        ttk.Label(self.parent_frame, text=info_text, 
                 font=('', 9), foreground='blue').pack(anchor=tk.W)
        
        self.question_text = tk.Text(self.parent_frame, height=4, font=('', 10))
        self.question_text.pack(fill=tk.X, pady=5)
        
        # Bind text change to auto-detect blanks
        self.question_text.bind('<KeyRelease>', self._on_question_text_change)
        
        # Question Image Upload
        if IMAGE_HELPER_AVAILABLE:
            self._add_question_image_control()
        
        # Blanks section
        blanks_label_frame = ttk.Frame(self.parent_frame)
        blanks_label_frame.pack(fill=tk.X, pady=(10, 5))
        
        ttk.Label(blanks_label_frame, text="Acceptable Answers for Each Blank:", 
                 font=('', 10, 'bold')).pack(side=tk.LEFT)
        
        # Container for blank answer sections
        self.blanks_container = ttk.Frame(self.parent_frame)
        self.blanks_container.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Initial blank (Q1)
        self._add_blank_section('Q1')
    
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
    
    def _on_question_text_change(self, event=None):
        """
        Auto-detect blanks from question text and add/remove sections accordingly
        """
        question_text = self.question_text.get('1.0', tk.END).strip()
        
        # Find all blanks in text
        matches = re.findall(BLANK_PLACEHOLDER_PATTERN, question_text)
        detected_blank_ids = [f'Q{num}' for num in matches]
        
        # Get current blank sections
        current_blank_ids = list(self.blank_frames.keys())
        
        # Add missing blanks
        for blank_id in detected_blank_ids:
            if blank_id not in current_blank_ids:
                self._add_blank_section(blank_id)
        
        # Remove blanks not in text (but keep Q1 if it's the only one)
        if len(detected_blank_ids) == 0:
            # No blanks detected - keep Q1 for single-blank mode
            for blank_id in current_blank_ids:
                if blank_id != 'Q1':
                    self._remove_blank_section(blank_id)
        else:
            for blank_id in current_blank_ids:
                if blank_id not in detected_blank_ids:
                    self._remove_blank_section(blank_id)
    
    def _add_blank_section(self, blank_id: str):
        """
        Add a blank answer section
        Args:
            blank_id: Blank identifier (e.g., 'Q1', 'Q2')
        """
        if blank_id in self.blank_frames:
            return  # Already exists
        
        # Create frame for this blank
        frame = ttk.LabelFrame(self.blanks_container, 
                               text=f"{BLANK_PLACEHOLDER_PREFIX}{blank_id.replace('Q', '')}{BLANK_PLACEHOLDER_SUFFIX}")
        frame.pack(fill=tk.X, pady=5, padx=5)
        
        ttk.Label(frame, text="Acceptable answers (one per line):", 
                 font=('', 9)).pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        text_widget = tk.Text(frame, height=6, font=('', 10))
        text_widget.pack(fill=tk.X, padx=5, pady=5)
        
        # Store references
        self.blank_frames[blank_id] = frame
        self.blank_text_widgets[blank_id] = text_widget
    
    def _remove_blank_section(self, blank_id: str):
        """
        Remove a blank answer section
        Args:
            blank_id: Blank identifier to remove
        """
        if blank_id not in self.blank_frames:
            return
        
        # Destroy frame
        self.blank_frames[blank_id].destroy()
        
        # Remove references
        del self.blank_frames[blank_id]
        del self.blank_text_widgets[blank_id]
    
    def load_data(self):
        """Load data from question object (edit mode)"""
        if not self.question:
            return
        
        # Load question text
        self.question_text.insert('1.0', self.question.question)
        
        # Load question image
        if IMAGE_HELPER_AVAILABLE and hasattr(self.question, 'questionImage') and self.question.questionImage:
            self.temp_image_paths['question'] = self.question.questionImage
            self.image_controls['question']['path_var'].set(os.path.basename(self.question.questionImage))
            
            if hasattr(self.question, 'questionImageScale'):
                self.image_controls['question']['scale_var'].set(self.question.questionImageScale)
            
            self._update_question_image_preview()
        
        # Trigger blank detection from question text
        self._on_question_text_change()
        
        # Load answers into appropriate blanks
        if self.question.is_multi_blank():
            # New format - dict
            for blank_id, answers in self.question.correct.items():
                if blank_id in self.blank_text_widgets:
                    self.blank_text_widgets[blank_id].insert('1.0', '\n'.join(answers))
        else:
            # Old format - list (single blank)
            if 'Q1' in self.blank_text_widgets:
                self.blank_text_widgets['Q1'].insert('1.0', '\n'.join(self.question.correct))
    
    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect data from form"""
        try:
            data = {}
            
            # Question text
            data['question'] = self.question_text.get('1.0', tk.END).strip()
            
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
            
            # Detect blanks in question text
            question_text = data['question']
            matches = re.findall(BLANK_PLACEHOLDER_PATTERN, question_text)
            detected_blank_ids = [f'Q{num}' for num in matches]
            
            # Collect answers
            if len(detected_blank_ids) == 0:
                # Single-blank mode (old format) - no _Q1_ in text
                data['is_multi_blank'] = False
                answers_list = [a.strip() for a in 
                               self.blank_text_widgets['Q1'].get('1.0', tk.END).split('\n') 
                               if a.strip()]
                data['answers'] = answers_list
            else:
                # Multi-blank mode (new format)
                data['is_multi_blank'] = True
                answers_dict = {}
                for blank_id in detected_blank_ids:
                    if blank_id in self.blank_text_widgets:
                        answers_list = [a.strip() for a in 
                                       self.blank_text_widgets[blank_id].get('1.0', tk.END).split('\n') 
                                       if a.strip()]
                        answers_dict[blank_id] = answers_list
                data['answers'] = answers_dict
            
            return data
            
        except Exception as e:
            print(f"Error collecting data: {str(e)}")
            return None
    
    def validate(self) -> Tuple[bool, str]:
        """Validate form data"""
        question_text = self.question_text.get('1.0', tk.END).strip()
        
        if not question_text:
            return False, "Question text is required"
        
        # Collect data to validate
        data = self.collect_data()
        if not data:
            return False, "Failed to collect form data"
        
        # Use shared validator
        is_valid, error = QuestionValidator.validate_fill_in_blank(
            data['question'],
            data['answers']
        )
        
        return is_valid, error