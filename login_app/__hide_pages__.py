import os
import sys

# This script renames the "pages" folder temporarily during import
# to prevent Streamlit from detecting it as a multi-page app

ORIGINAL_NAME = "pages"
TEMP_NAME = "_pages_hidden"

# Only run if the original folder exists
if os.path.exists(ORIGINAL_NAME) and os.path.isdir(ORIGINAL_NAME):
    try:
        # Rename folder before Streamlit loads
        os.rename(ORIGINAL_NAME, TEMP_NAME)
        
        # Register function to rename back on exit
        import atexit
        def restore_folder_name():
            if os.path.exists(TEMP_NAME) and os.path.isdir(TEMP_NAME):
                os.rename(TEMP_NAME, ORIGINAL_NAME)
        atexit.register(restore_folder_name)
    except Exception as e:
        print(f"Error hiding pages folder: {e}")