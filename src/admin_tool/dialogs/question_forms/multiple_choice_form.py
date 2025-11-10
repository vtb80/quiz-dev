"""
Multiple Choice Question Form
Handles creation and editing of multiple choice questions
Version: 1.0
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
from typing import Optional, Dict, Any, Tuple

from shared.models import Subject, Question, MultipleChoiceQuestion
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


class MultipleChoiceForm(BaseQuestionForm):
    """Form for Multiple Choice questions"""
    
    def __init__(self, parent_frame: ttk.Frame, subject: Subject, 
                 lesson_id: Optional[str], mode: str, question: Optional[MultipleChoiceQuestion] = None):
        super().__init__(parent_frame, subject, lesson_id, mode, question)
        
        # MC-specific attributes
        self.use_option_images_var = tk.BooleanVar(value=False)
        self.saved_text_options = []
        self.saved_image_options = {}
        
        # Render and load
        self.render()
        if mode == "edit" and question:
            self.load_data()
    
    def render(self):
        """Render Multiple Choice form"""
        # Question text
        ttk.Label(self.parent_frame, text="Question:", font=('', 10, 'bold')).pack(anchor=tk.W, pady=(5, 0))
        self.question_text = tk.Text(self.parent_frame, height=4, font=('', 10))
        self.question_text.pack(fill=tk.X, pady=5)
        
        # Question Image Upload
        if IMAGE_HELPER_AVAILABLE:
            self._add_question_image_control()
        
        # Options Section
        options_label_frame = ttk.Frame(self.parent_frame)
        options_label_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(options_label_frame, text="Options:", font=('', 10, 'bold')).pack(side=tk.LEFT)
        
        # Checkbox for image options
        if IMAGE_HELPER_AVAILABLE:
            self.use_option_images_checkbox = ttk.Checkbutton(
                options_label_frame,
                text="Use images for options",
                variable=self.use_option_images_var,
                command=self.toggle_option_images
            )
            self.use_option_images_checkbox.pack(side=tk.LEFT, padx=(20, 0))
        
        # Text Options Frame
        self.text_options_frame = ttk.Frame(self.parent_frame)
        self.text_options_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(self.text_options_frame, text="Enter options (one per line):", 
                 font=('', 9), foreground='gray').pack(anchor=tk.W)
        self.options_text = tk.Text(self.text_options_frame, height=8, font=('', 10))
        self.options_text.pack(fill=tk.X, pady=5)
        
        # Image Options Frame (hidden by default)
        if IMAGE_HELPER_AVAILABLE:
            self.image_options_frame = ttk.LabelFrame(self.parent_frame, text="Option Images (All 4 required)")
            
            for i in range(4):
                self._add_option_image_control(i)
            
            # Scale control for all option images
            scale_frame = ttk.Frame(self.image_options_frame)
            scale_frame.pack(fill=tk.X, padx=5, pady=5)
            ttk.Label(scale_frame, text="Options Image Scale:", font=('', 9, 'bold')).pack(side=tk.LEFT, padx=5)
            self.option_scale_var = tk.IntVar(value=DEFAULT_SCALE)
            ttk.Spinbox(scale_frame, from_=25, to=200, increment=25, 
                       textvariable=self.option_scale_var, width=8).pack(side=tk.LEFT, padx=5)
            ttk.Label(scale_frame, text="%").pack(side=tk.LEFT)
        
        # Correct Answer
        corr_frame = ttk.Frame(self.parent_frame)
        corr_frame.pack(fill=tk.X, pady=10)
        ttk.Label(corr_frame, text="Correct answer index (0-based):", font=('', 10)).pack(side=tk.LEFT)
        self.correct_var = tk.StringVar(value="0")
        ttk.Spinbox(corr_frame, from_=0, to=3, textvariable=self.correct_var, width=10).pack(side=tk.LEFT, padx=5)
    
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
    
    def _add_option_image_control(self, option_index: int):
        """Add option image upload control"""
        opt_frame = ttk.Frame(self.image_options_frame)
        opt_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(opt_frame, text=f"Option {option_index}:", 
                 font=('', 9, 'bold'), width=10).pack(side=tk.LEFT, padx=5)
        
        path_var = tk.StringVar(value="")
        ttk.Label(opt_frame, textvariable=path_var, foreground='gray', 
                 font=('', 8), width=30).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(opt_frame, text="📷 Upload", 
                  command=lambda idx=option_index: self._select_option_image(idx)).pack(side=tk.LEFT, padx=2)
        ttk.Button(opt_frame, text="✕", width=3,
                  command=lambda idx=option_index: self._remove_option_image(idx)).pack(side=tk.LEFT, padx=2)
        
        self.image_controls[f'option_{option_index}'] = {
            'path_var': path_var,
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
            # Show warning for missing file
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
    
    def _select_option_image(self, index: int):
        """Select option image"""
        filepath = select_image_file(self.parent_frame, f"Select Option {index} Image")
        if filepath:
            self.temp_image_paths[f'option_{index}'] = filepath
            self.image_controls[f'option_{index}']['path_var'].set(os.path.basename(filepath))
    
    def _remove_option_image(self, index: int):
        """Remove option image"""
        key = f'option_{index}'
        if key in self.temp_image_paths:
            del self.temp_image_paths[key]
        self.image_controls[key]['path_var'].set("")
    
    def toggle_option_images(self):
        """Toggle between text and image options"""
        if self.use_option_images_var.get():
            # Save text options
            self.saved_text_options = [o.strip() for o in self.options_text.get('1.0', tk.END).split('\n') if o.strip()]
            
            # Hide text, show images
            self.text_options_frame.pack_forget()
            self.image_options_frame.pack(fill=tk.X, pady=5)
            
            # Restore saved image options if any
            for i in range(4):
                key = f'option_{i}'
                if key in self.saved_image_options:
                    self.temp_image_paths[key] = self.saved_image_options[key]
                    self.image_controls[key]['path_var'].set(os.path.basename(self.saved_image_options[key]))
        else:
            # Save image options
            for i in range(4):
                key = f'option_{i}'
                if key in self.temp_image_paths:
                    self.saved_image_options[key] = self.temp_image_paths[key]
            
            # Hide images, show text
            self.image_options_frame.pack_forget()
            self.text_options_frame.pack(fill=tk.X, pady=5)
            
            # Restore saved text options
            if self.saved_text_options:
                self.options_text.delete('1.0', tk.END)
                self.options_text.insert('1.0', '\n'.join(self.saved_text_options))
    
    def load_data(self):
        """Load data from question object (edit mode)"""
        if not self.question:
            return
        
        # Load question text
        self.question_text.insert('1.0', self.question.question)
        
        # Load question image
        if IMAGE_HELPER_AVAILABLE and hasattr(self.question, 'questionImage') and self.question.questionImage:
            # Path already saved in JSON - keep as-is
            self.temp_image_paths['question'] = self.question.questionImage
            self.image_controls['question']['path_var'].set(os.path.basename(self.question.questionImage))
            
            if hasattr(self.question, 'questionImageScale'):
                self.image_controls['question']['scale_var'].set(self.question.questionImageScale)
            
            self._update_question_image_preview()
        
        # Check if using option images
        if IMAGE_HELPER_AVAILABLE and hasattr(self.question, 'optionImages') and self.question.optionImages:
            # Set checkbox to trigger toggle
            self.use_option_images_var.set(True)
            self.toggle_option_images()  # This will show image frame
            
            # Load option images
            for idx, path in self.question.optionImages.items():
                key = f'option_{int(idx)}'
                # Path already saved - keep as-is
                self.temp_image_paths[key] = path
                self.image_controls[key]['path_var'].set(os.path.basename(path))
                
                # Check if file exists and show warning
                if not os.path.exists(path):
                    self.image_controls[key]['path_var'].set(f"⚠ {os.path.basename(path)} (missing)")
            
            # Load option scale
            if hasattr(self.question, 'optionImageScale'):
                self.option_scale_var.set(self.question.optionImageScale)
        else:
            # Using text options
            self.options_text.insert('1.0', '\n'.join(self.question.options))
        
        # Load correct answer
        self.correct_var.set(str(self.question.correct))
    
    def collect_data(self) -> Optional[Dict[str, Any]]:
        """Collect data from form"""
        try:
            data = {}
            
            # Question text
            data['question'] = self.question_text.get('1.0', tk.END).strip()
            
            # Question image - CRITICAL PATH HANDLING
            if 'question' in self.temp_image_paths:
                img_path = self.temp_image_paths['question']
                # If editing and path already saved (starts with 'images/'), keep it
                if img_path.startswith('images/'):
                    data['questionImage'] = img_path
                    data['questionImageScale'] = self.image_controls['question']['scale_var'].get()
                else:
                    # New image - needs to be copied
                    # Get question ID (from existing question or will be assigned by caller)
                    q_id = self.question.id if self.question else None
                    if q_id:
                        rel_path = copy_image_to_subject(img_path, self.subject.name, q_id, 'main')
                        if rel_path:
                            data['questionImage'] = rel_path
                            data['questionImageScale'] = validate_scale(
                                self.image_controls['question']['scale_var'].get()
                            )
            
            # Options handling
            if self.use_option_images_var.get():
                # Using images
                data['use_option_images'] = True
                data['option_images_temp'] = {}
                for i in range(4):
                    key = f'option_{i}'
                    if key in self.temp_image_paths:
                        data['option_images_temp'][i] = self.temp_image_paths[key]
                data['option_scale'] = self.option_scale_var.get()
                # Use placeholder text
                data['options'] = [f"Option {i}" for i in range(4)]
            else:
                # Using text
                data['use_option_images'] = False
                data['options'] = [o.strip() for o in 
                                  self.options_text.get('1.0', tk.END).split('\n') 
                                  if o.strip()]
            
            # Correct answer
            data['correct'] = int(self.correct_var.get())
            
            return data
            
        except Exception as e:
            print(f"Error collecting data: {str(e)}")
            return None
    
    def validate(self) -> Tuple[bool, str]:
        """Validate form data"""
        question_text = self.question_text.get('1.0', tk.END).strip()
        
        if not question_text:
            return False, "Question text is required"
        
        # Validate options
        if self.use_option_images_var.get():
            # Validate all 4 images present
            for i in range(4):
                if f'option_{i}' not in self.temp_image_paths:
                    return False, f"Please upload image for Option {i}"
            
            # Check if files exist (for edit mode)
            for i in range(4):
                path = self.temp_image_paths[f'option_{i}']
                if not path.startswith('images/') and not os.path.exists(path):
                    return False, f"Option {i} image file not found"
        else:
            # Validate text options
            opts = [o.strip() for o in self.options_text.get('1.0', tk.END).split('\n') if o.strip()]
            
            if len(opts) < 2:
                return False, "Need at least 2 options"
            
            for i, opt in enumerate(opts):
                if not opt:
                    return False, f"Option {i} is empty"
        
        # Validate correct answer
        try:
            correct = int(self.correct_var.get())
            
            if self.use_option_images_var.get():
                if correct < 0 or correct > 3:
                    return False, "Correct answer must be between 0 and 3"
            else:
                opts = [o.strip() for o in self.options_text.get('1.0', tk.END).split('\n') if o.strip()]
                if correct < 0 or correct >= len(opts):
                    return False, f"Correct answer must be between 0 and {len(opts)-1}"
        except ValueError:
            return False, "Invalid correct answer index"
        
        return True, ""
