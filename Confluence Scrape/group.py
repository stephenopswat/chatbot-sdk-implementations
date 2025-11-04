"""Group JSON files into subfolders based on filename prefixes."""
import os
import shutil

def group(source_dir):

    # Destination directory for grouped JSON files
    dest_dir = os.path.join(source_dir, "Grouped_JSONs")
    os.makedirs(dest_dir, exist_ok=True)

    # Loop through all files in the current directory
    for file_name in os.listdir(source_dir):
        # Only process JSON files
        if file_name.endswith(".json"):
            # Take prefix before first underscore as folder name
            prefix = file_name.split("_")[0]
            folder_path = os.path.join(dest_dir, prefix)
            os.makedirs(folder_path, exist_ok=True)

            # Move JSON file into the folder
            shutil.move(os.path.join(source_dir, file_name), os.path.join(folder_path, file_name))

    print("All JSON files have been grouped into subfolders!")
