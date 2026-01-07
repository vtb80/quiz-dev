"""
Drop-Down Question Form with Image Support
NEW question type implementation
Version: 1.0
"""

import tkinter as tk
from tkinter import ttk
import os
import re
from typing import Optional, Dict, Any, Tuple

from shared.models import Subject, Question, DropdownQuestion
from shared.validators import QuestionValidator
from shared.constants import (
    MIN_DROPDOWNS, MAX_DROPDOWNS,
    MIN_OPTIONS_PER_DROPDOWN, MAX_OPTIONS_PER_DROPDOWN,
    DROPDOWN_PLACEHOLDER_PREFIX,
    DROPDOWN_PLACEHOLDER_SUFFIX,
    DROPDOWN_PLACEHOLDER_PATTERN
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


class DropdownForm(BaseQuestionForm):
    """Form for Drop-Down Selection questions"""
    
    def __init__(self, parent_frame: ttk.Frame, subject: Subject, 
                 lesson_id: Optional[str], mode: str, question: Optional[DropdownQuestion] = None):
        super().__init__(parent_frame, subject, lesson_id, mode, question)
        
        # Track dropdown widgets
        self.dropdown_frames = {}  # {dd_id: frame_widget}
        self.dropdown_text_widgets = {}  # {dd_id: text_widget for options}
        self.dropdown_correct_vars = {}  # {dd_id: IntVar for correct index}
        
        # Render and load
        self.render()
        if mode == "edit" and question:
            self.load_data()
    
    def render(self):
        """Render Drop-Down form"""
        # Instructions
        ttk.Label(self.parent_frame, text="Question:", font=('', 10, 'bold')).pack(anchor=tk.W, pady=(5, 0))
        
        info_text = f"Use {DROPDOWN_PLACEHOLDER_PREFIX}1{DROPDOWN_PLACEHOLDER_SUFFIX}, {DROPDOWN_PLACEHOLDER_PREFIX}2{DROPDOWN_PLACEHOLDER_SUFFIX}, {DROPDOWN_PLACEHOLDER_PREFIX}3{DROPDOWN_PLACEHOLDER_SUFFIX}, etc. for dropdown locations (max: {MAX_DROPDOWNS})"
        ttk.Label(self.parent_frame, text=info_text, 
                 font=('', 9), foreground='blue').pack(anchor=tk.W)
        
        info_text2 = f"Each dropdown needs {MIN_OPTIONS_PER_DROPDOWN}-{MAX_OPTIONS_PER_DROPDOWN} options"
        ttk.Label(self.parent_frame, text=info_text2, 
                 font=('', 9), foreground='gray').pack(anchor=tk.W)
        
        # Question text area
        self.question_text = tk.Text(self.parent_frame, height=5, font=('', 10), wrap=tk.WORD)
        self.question_text.pack(fill=tk.X, pady=5)
        
        # Bind text change to auto-detect dropdowns
        self.question_text.bind('<KeyRelease>', self._on_question_text_change)
        
        # Question Image Upload
        if IMAGE_HELPER_AVAILABLE:
            self._add_question_image_control()
        
        # Dropdowns section
        dropdowns_label_frame = ttk.Frame(self.parent_frame)
        dropdowns_label_frame.pack(fill=tk.X, pady=(10, 5))
        
        ttk.Label(dropdowns_label_frame, text="Dropdown Options & Correct Answers:", 
                 font=('', 10, 'bold')).pack(side=tk.LEFT)
        
        # Container for dropdown sections
        self.dropdowns_container = ttk.Frame(self.parent_frame)
        self.dropdowns_container.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Initial dropdown (DD1)
        self._add_dropdown_section('DD1')
    
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
        """Auto-detect dropdowns from question text and add/remove sections"""
        question_text = self.question_text.get('1.0', tk.END).strip()
        
        # Find all dropdowns in text
        matches = re.findall(DROPDOWN_PLACEHOLDER_PATTERN, question_text)
        detected_dd_ids = [f'DD{num}' for num in matches]
        
        # Get current dropdown sections
        current_dd_ids = list(self.dropdown_frames.keys())
        
        # Add missing dropdowns
        for dd_id in detected_dd_ids:
            if dd_id not in current_dd_ids:
                self._add_dropdown_section(dd_id)
        
        # Remove dropdowns not in text (but keep DD1 if it's the only one)
        if len(detected_dd_ids) == 0:
            for dd_id in current_dd_ids:
                if dd_id != 'DD1':
                    self._remove_dropdown_section(dd_id)
        else:
            for dd_id in current_dd_ids:
                if dd_id not in detected_dd_ids:
                    self._remove_dropdown_section(dd_id)
    
    def _add_dropdown_section(self, dd_id: str):
        """Add a dropdown section"""
        if dd_id in self.dropdown_frames:
            return
        
        # Create frame
        frame = ttk.LabelFrame(self.dropdowns_container, 
                               text=f"{DROPDOWN_PLACEHOLDER_PREFIX}{dd_id.replace('DD', '')}{DROPDOWN_PLACEHOLDER_SUFFIX}")
        frame.pack(fill=tk.X, pady=5, padx=5)
        
        # Options input
        ttk.Label(frame, text=f"Options ({MIN_OPTIONS_PER_DROPDOWN}-{MAX_OPTIONS_PER_DROPDOWN}, one per line):", 
                 font=('', 9)).pack(anchor=tk.W, padx=5, pady=(5, 0))
        
        text_widget = tk.Text(frame, height=4, font=('', 10))
        text_widget.pack(fill=tk.X, padx=5, pady=5)
        
        # Correct answer selector
        correct_frame = ttk.Frame(frame)
        correct_frame.pack(fill=tk.X, padx=5, pady=(0, 5))
        
        ttk.Label(correct_frame, text="Correct answer index (0-based):", 
                 font=('', 9)).pack(side=tk.LEFT, padx=5)
        
        correct_var = tk.IntVar(value=0)
        ttk.Spinbox(correct_frame, from_=0, to=3, textvariable=correct_var, 
                   width=8).pack(side=tk.LEFT, padx=5)
        
        # Store references
        self.dropdown_frames[dd_id] = frame
        self.dropdown_text_widgets[dd_id] = text_widget
        self.dropdown_correct_vars[dd_id] = correct_var
    
    def _remove_dropdown_section(self, dd_id: str):
        """Remove a dropdown section"""
        if dd_id not in self.dropdown_frames:
            return
        
        self.dropdown_frames[dd_id].destroy()
        del self.dropdown_frames[dd_id]
        del self.dropdown_text_widgets[dd_id]
        del self.dropdown_correct_vars[dd_id]
    
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
        
        # Trigger dropdown detection
        self._on_question_text_change()
        
        # Load dropdown data
        for dd_id, dd_data in self.question.dropdowns.items():
            if dd_id in self.dropdown_text_widgets:
                options = dd_data.get('options', [])
                self.dropdown_text_widgets[dd_id].insert('1.0', '\n'.join(options))
                
                correct = dd_data.get('correct', 0)
                self.dropdown_correct_vars[dd_id].set(correct)
    
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
            
            # Detect dropdowns
            question_text = data['question']
            matches = re.findall(DROPDOWN_PLACEHOLDER_PATTERN, question_text)
            detected_dd_ids = [f'DD{num}' for num in matches]
            
            # Collect dropdown data
            dropdowns_dict = {}
            for dd_id in detected_dd_ids:
                if dd_id in self.dropdown_text_widgets:
                    options_list = [o.strip() for o in 
                                   self.dropdown_text_widgets[dd_id].get('1.0', tk.END).split('\n') 
                                   if o.strip()]
                    correct_idx = self.dropdown_correct_vars[dd_id].get()
                    
                    dropdowns_dict[dd_id] = {
                        'options': options_list,
                        'correct': correct_idx
                    }
            
            data['dropdowns'] = dropdowns_dict
            
            return data
            
        except Exception as e:
            print(f"Error collecting data: {str(e)}")
            return None
    
    def validate(self) -> Tuple[bool, str]:
        """Validate form data"""
        data = self.collect_data()
        if not data:
            return False, "Failed to collect form data"
        
        # Use shared validator
        is_valid, error = QuestionValidator.validate_dropdown(
            data['question'],
            data['dropdowns']
        )
        
        return is_valid, error
