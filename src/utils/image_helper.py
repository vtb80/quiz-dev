"""
Image Helper Module for Quiz Admin Tool
Handles image selection, validation, copying, and preview
Version: 1.1 - Added delete_question_images function
Required: pip install Pillow
"""

import os
import shutil
from tkinter import filedialog, messagebox
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Configuration
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB in bytes
SUPPORTED_FORMATS = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
DEFAULT_SCALE = 50  # Default image scale percentage

def is_pil_available():
    """Check if PIL/Pillow is installed"""
    return PIL_AVAILABLE

def validate_image_file(filepath):
    """
    Validate image file
    Returns: (is_valid, error_message)
    """
    if not filepath:
        return False, "No file selected"
    
    if not os.path.exists(filepath):
        return False, "File does not exist"
    
    # Check extension
    ext = os.path.splitext(filepath)[1].lower()
    if ext not in SUPPORTED_FORMATS:
        return False, f"Unsupported format. Use: {', '.join(SUPPORTED_FORMATS)}"
    
    # Check file size
    file_size = os.path.getsize(filepath)
    if file_size > MAX_IMAGE_SIZE:
        size_mb = file_size / (1024 * 1024)
        return False, f"File too large ({size_mb:.1f}MB). Max 5MB allowed"
    
    # Try to open as image
    if PIL_AVAILABLE:
        try:
            img = Image.open(filepath)
            img.verify()
            return True, None
        except Exception as e:
            return False, f"Invalid image file: {str(e)}"
    
    # If PIL not available, assume valid based on extension
    return True, None

def select_image_file(parent_widget, title="Select Image"):
    """
    Open file dialog to select an image
    Returns: filepath or None
    """
    filetypes = [
        ("Image files", "*.jpg *.jpeg *.png *.gif *.webp"),
        ("JPEG files", "*.jpg *.jpeg"),
        ("PNG files", "*.png"),
        ("GIF files", "*.gif"),
        ("WebP files", "*.webp"),
        ("All files", "*.*")
    ]
    
    filepath = filedialog.askopenfilename(
        parent=parent_widget,
        title=title,
        filetypes=filetypes
    )
    
    if not filepath:
        return None
    
    # Validate
    is_valid, error = validate_image_file(filepath)
    if not is_valid:
        messagebox.showerror("Invalid Image", error)
        return None
    
    return filepath

def copy_image_to_subject(source_path, subject_name, question_id, image_type="main"):
    """
    Copy image to subject's images folder with organized naming
    
    Args:
        source_path: Original image file path
        subject_name: Subject name (for folder)
        question_id: Question ID
        image_type: 'main', 'option_0', 'option_1', 'passage', etc.
    
    Returns: Relative path for JSON storage, or None if failed
    """
    if not source_path or not os.path.exists(source_path):
        return None
    
    # Get file extension
    _, ext = os.path.splitext(source_path)
    
    # Create destination folder
    dest_folder = f"images/{subject_name}"
    os.makedirs(dest_folder, exist_ok=True)
    
    # Create filename: q{id}_{type}{ext}
    filename = f"q{question_id}_{image_type}{ext}"
    dest_path = os.path.join(dest_folder, filename)
    
    try:
        # Copy file
        shutil.copy2(source_path, dest_path)
        
        # Return relative path for JSON
        return dest_path.replace('\\', '/')  # Use forward slashes for cross-platform
    
    except Exception as e:
        messagebox.showerror("Copy Error", f"Failed to copy image: {str(e)}")
        return None

def delete_image_file(image_path):
    """
    Delete image file safely
    Returns: True if deleted, False otherwise
    """
    if not image_path or not os.path.exists(image_path):
        return False
    
    try:
        os.remove(image_path)
        return True
    except Exception as e:
        print(f"Warning: Could not delete image: {str(e)}")
        return False

def delete_question_images(subject_name, question_id):
    """
    Delete all images associated with a question
    
    Args:
        subject_name: Subject name
        question_id: Question ID
    
    Returns: Number of files deleted
    """
    folder = f"images/{subject_name}"
    if not os.path.exists(folder):
        return 0
    
    deleted = 0
    prefix = f"q{question_id}_"
    
    try:
        for filename in os.listdir(folder):
            if filename.startswith(prefix):
                filepath = os.path.join(folder, filename)
                try:
                    os.remove(filepath)
                    deleted += 1
                    print(f"Deleted image: {filename}")
                except Exception as e:
                    print(f"Could not delete {filename}: {e}")
    except Exception as e:
        print(f"Error during image cleanup: {e}")
    
    return deleted

def get_image_info(image_path):
    """
    Get image information
    Returns: dict with width, height, size, format or None
    """
    if not image_path or not os.path.exists(image_path):
        return None
    
    if not PIL_AVAILABLE:
        # Basic info without PIL
        file_size = os.path.getsize(image_path)
        return {
            'width': 'Unknown',
            'height': 'Unknown',
            'size': file_size,
            'format': os.path.splitext(image_path)[1].upper()
        }
    
    try:
        img = Image.open(image_path)
        return {
            'width': img.width,
            'height': img.height,
            'size': os.path.getsize(image_path),
            'format': img.format
        }
    except Exception as e:
        return None

def create_image_preview(image_path, max_width=400, scale_percent=50):
    """
    Create PIL PhotoImage for Tkinter preview
    
    Args:
        image_path: Path to image file
        max_width: Maximum width for preview
        scale_percent: Scale percentage (25-200)
    
    Returns: (PhotoImage, actual_width, actual_height) or (None, 0, 0)
    """
    if not PIL_AVAILABLE or not image_path or not os.path.exists(image_path):
        return None, 0, 0
    
    try:
        img = Image.open(image_path)
        
        # Calculate size based on scale
        width, height = img.size
        new_width = int(width * scale_percent / 100)
        new_height = int(height * scale_percent / 100)
        
        # Limit to max_width
        if new_width > max_width:
            ratio = max_width / new_width
            new_width = max_width
            new_height = int(new_height * ratio)
        
        # Resize
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Convert to PhotoImage
        photo = ImageTk.PhotoImage(img_resized)
        
        return photo, new_width, new_height
    
    except Exception as e:
        print(f"Error creating preview: {str(e)}")
        return None, 0, 0

def validate_scale(scale_value):
    """
    Validate and normalize scale value
    Returns: Valid scale (25-200) or default
    """
    try:
        scale = int(scale_value)
        if scale < 25:
            return 25
        elif scale > 200:
            return 200
        return scale
    except:
        return DEFAULT_SCALE

def format_file_size(size_bytes):
    """
    Format file size for display
    Returns: Human-readable size string
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

def get_unique_filename(dest_folder, base_name, extension):
    """
    Get unique filename if file already exists
    Appends (1), (2), etc.
    """
    filename = f"{base_name}{extension}"
    filepath = os.path.join(dest_folder, filename)
    
    counter = 1
    while os.path.exists(filepath):
        filename = f"{base_name}_{counter}{extension}"
        filepath = os.path.join(dest_folder, filename)
        counter += 1
    
    return filename

def cleanup_unused_images(subject_name, used_image_paths):
    """
    Clean up unused images in subject folder
    
    Args:
        subject_name: Subject name
        used_image_paths: List of image paths currently in use
    
    Returns: Number of files deleted
    """
    folder = f"images/{subject_name}"
    if not os.path.exists(folder):
        return 0
    
    # Normalize paths
    used_paths = set(path.replace('\\', '/') for path in used_image_paths if path)
    
    deleted = 0
    try:
        for filename in os.listdir(folder):
            filepath = os.path.join(folder, filename).replace('\\', '/')
            
            # Check if it's an image file
            if os.path.splitext(filename)[1].lower() in SUPPORTED_FORMATS:
                # If not in used paths, delete
                if filepath not in used_paths:
                    try:
                        os.remove(filepath)
                        deleted += 1
                    except:
                        pass
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")
    
    return deleted

# Helper functions for question dialog integration

def add_image_controls(parent_frame, current_image_path=None, scale=DEFAULT_SCALE, label_text="Image:"):
    """
    Add image attachment controls to a frame
    Returns: dict with widgets and control functions
    """
    import tkinter as tk
    from tkinter import ttk
    
    controls = {
        'image_path': current_image_path,
        'scale': scale,
        'photo_ref': None
    }
    
    # Container frame
    img_frame = ttk.LabelFrame(parent_frame, text=label_text)
    img_frame.pack(fill=tk.X, pady=5)
    
    # Button frame
    btn_frame = ttk.Frame(img_frame)
    btn_frame.pack(fill=tk.X, padx=5, pady=5)
    
    # Path label
    path_label = ttk.Label(btn_frame, text="No image", foreground='gray')
    path_label.pack(side=tk.LEFT, padx=5)
    
    # Preview frame
    preview_frame = ttk.Frame(img_frame)
    preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Scale controls frame
    scale_frame = ttk.Frame(img_frame)
    scale_frame.pack(fill=tk.X, padx=5, pady=5)
    
    scale_label = ttk.Label(scale_frame, text="Scale:")
    scale_label.pack(side=tk.LEFT, padx=5)
    
    scale_var = tk.IntVar(value=scale)
    scale_spinbox = ttk.Spinbox(scale_frame, from_=25, to=200, increment=25, 
                                textvariable=scale_var, width=8)
    scale_spinbox.pack(side=tk.LEFT, padx=5)
    
    ttk.Label(scale_frame, text="%").pack(side=tk.LEFT)
    
    def update_preview():
        # Clear preview
        for widget in preview_frame.winfo_children():
            widget.destroy()
        
        if not controls['image_path']:
            path_label.config(text="No image", foreground='gray')
            return
        
        # Update path label
        path_label.config(text=os.path.basename(controls['image_path']), foreground='black')
        
        # Show preview if PIL available
        if PIL_AVAILABLE and os.path.exists(controls['image_path']):
            photo, w, h = create_image_preview(controls['image_path'], 
                                              max_width=400, 
                                              scale_percent=scale_var.get())
            if photo:
                controls['photo_ref'] = photo  # Keep reference
                label = tk.Label(preview_frame, image=photo)
                label.pack(pady=5)
                
                # Show info
                info = get_image_info(controls['image_path'])
                if info:
                    info_text = f"{info['width']}x{info['height']} • {format_file_size(info['size'])}"
                    ttk.Label(preview_frame, text=info_text, font=('', 8), 
                             foreground='gray').pack()
    
    def select_image():
        filepath = select_image_file(parent_frame, "Select Image")
        if filepath:
            controls['image_path'] = filepath
            controls['scale'] = scale_var.get()
            update_preview()
    
    def remove_image():
        controls['image_path'] = None
        controls['scale'] = DEFAULT_SCALE
        scale_var.set(DEFAULT_SCALE)
        update_preview()
    
    def update_scale(event=None):
        controls['scale'] = validate_scale(scale_var.get())
        scale_var.set(controls['scale'])
        if controls['image_path']:
            update_preview()
    
    # Attach button
    attach_btn = ttk.Button(btn_frame, text="📎 Attach Image", command=select_image)
    attach_btn.pack(side=tk.LEFT, padx=5)
    
    # Remove button
    remove_btn = ttk.Button(btn_frame, text="✕ Remove", command=remove_image)
    remove_btn.pack(side=tk.LEFT, padx=5)
    
    # Bind scale change
    scale_spinbox.bind('<Return>', update_scale)
    scale_spinbox.bind('<FocusOut>', update_scale)
    
    # Initial preview
    update_preview()
    
    controls['update_preview'] = update_preview
    controls['get_path'] = lambda: controls['image_path']
    controls['get_scale'] = lambda: controls['scale']
    controls['set_path'] = lambda p: (setattr(controls, 'image_path', p), update_preview())
    
    return controls

# Utility function for saving images during question save
def save_question_images(question_data, subject_name, temp_image_paths):
    """
    Save images for a question and update question_data with paths
    
    Args:
        question_data: Question dict
        subject_name: Subject name
        temp_image_paths: Dict with keys like 'main', 'option_0', etc. mapping to file paths
    
    Returns: Updated question_data
    """
    q_id = question_data.get('id', 1)
    
    # Save main question image
    if temp_image_paths.get('main'):
        rel_path = copy_image_to_subject(temp_image_paths['main'], subject_name, q_id, 'main')
        if rel_path:
            question_data['questionImage'] = rel_path
    
    # Save option images
    option_images = {}
    for key, path in temp_image_paths.items():
        if key.startswith('option_') and path:
            option_idx = key.split('_')[1]
            rel_path = copy_image_to_subject(path, subject_name, q_id, key)
            if rel_path:
                option_images[option_idx] = rel_path
    
    if option_images:
        question_data['optionImages'] = option_images
    
    return question_data
