"""
Shared Constants and Configuration
Version: 2.4 - Added dropdown question type constants
"""

# Application Info
APP_NAME = "Quiz Admin"
APP_VERSION = "2.4"
APP_TITLE = f"{APP_NAME} v{APP_VERSION} - Modular Edition"

# Question Types
QUESTION_TYPES = [
    "multiple_choice",
    "multiple_choice_multiple",
    "true_false",
    "fill_in_blank",
    "dropdown",
    "matching",
    "reordering",
    "reading_comprehension"
]

QUESTION_TYPE_NAMES = {
    'multiple_choice': 'Multiple Choice',
    'multiple_choice_multiple': 'Multiple Choice (Multiple Answers)',
    'true_false': 'True/False',
    'fill_in_blank': 'Fill in the Blank',
    'dropdown': 'Drop-Down Selection',
    'matching': 'Matching',
    'reordering': 'Reordering',
    'reading_comprehension': 'Reading Comprehension'
}

QUESTION_TYPE_ICONS = {
    'multiple_choice': 'MC',
    'multiple_choice_multiple': 'MCM',
    'true_false': 'TF',
    'fill_in_blank': 'FILL',
    'dropdown': 'DD',
    'matching': 'MATCH',
    'reordering': 'REORD',
    'reading_comprehension': 'READ'
}

# File Settings
QUESTIONS_FILE_PREFIX = "questions-"
QUESTIONS_FILE_SUFFIX = ".json"
IMAGES_FOLDER = "images"

# Image Settings
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB
SUPPORTED_IMAGE_FORMATS = ('.jpg', '.jpeg', '.png', '.gif', '.webp')
DEFAULT_IMAGE_SCALE = 50
MIN_IMAGE_SCALE = 25
MAX_IMAGE_SCALE = 200
IMAGE_SCALE_INCREMENT = 25

# UI Settings
TREE_HEIGHT = 25
DETAILS_WIDTH = 450
WINDOW_STATE = 'zoomed'  # Full screen on launch

# Tree View Icons
ICON_LESSON = "⋮⋮"
ICON_OTHERS = "📂"
ICON_IMAGE = "🖼️"

# Colors
COLOR_CORRECT = '#d4edda'
COLOR_INCORRECT = '#f8d7da'
COLOR_INFO = '#d1ecf1'

# Validation
MIN_OPTIONS_MC = 2
MIN_PAIRS_MATCHING = 2
MIN_ITEMS_REORDERING = 2
MIN_ANSWERS_FILL = 1
MIN_SUBQUESTIONS_READING = 1
MIN_CORRECT_ANSWERS_MCM = 1

# Fill in the Blank - Multi-Blank Support
MAX_BLANKS_FILL = 10  # Maximum number of blanks allowed
BLANK_PLACEHOLDER_PREFIX = "_Q"  # Placeholder format: _Q1_, _Q2_, etc.
BLANK_PLACEHOLDER_SUFFIX = "_"
BLANK_PLACEHOLDER_PATTERN = r'_Q(\d+)_'  # Regex pattern for validation

# NEW: Drop-Down Selection - Multi-Dropdown Support
MIN_DROPDOWNS = 1  # Minimum dropdowns in a question
MAX_DROPDOWNS = 5  # Maximum dropdowns in a question
MIN_OPTIONS_PER_DROPDOWN = 3  # Minimum options per dropdown
MAX_OPTIONS_PER_DROPDOWN = 4  # Maximum options per dropdown
DROPDOWN_PLACEHOLDER_PREFIX = "[DD"  # Placeholder format: [DD1], [DD2], etc.
DROPDOWN_PLACEHOLDER_SUFFIX = "]"
DROPDOWN_PLACEHOLDER_PATTERN = r'\[DD(\d+)\]'  # Regex pattern for validation

# Default Values
DEFAULT_NUM_QUESTIONS = 5
DEFAULT_LESSON_ID_PREFIX = "L"
DEFAULT_LESSON_ID_PADDING = 3

# Messages
MSG_SELECT_SUBJECT = "Select a subject first"
MSG_SELECT_LESSON = "Select a lesson first"
MSG_SELECT_QUESTION = "Select a question first"
MSG_CONFIRM_DELETE = "Are you sure you want to delete?"
MSG_UNSAVED_CHANGES = "You have unsaved changes. Continue?"

# Special Categories
OTHERS_CATEGORY = "Others"
OTHERS_DISPLAY = f"{ICON_OTHERS} {OTHERS_CATEGORY}"
