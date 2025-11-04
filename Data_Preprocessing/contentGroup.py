"""Group JSON files by prefix and combine them into single JSON files with metadata."""

import os
import json
import shutil
from datetime import datetime

# Current directory where this script and JSON files are located
source_dir = os.path.dirname(os.path.abspath(__file__))

# Destination directory for grouped JSON files
grouped_dir = os.path.join(source_dir, "Grouped_JSONs")
os.makedirs(grouped_dir, exist_ok=True)

# Destination directory for combined JSON files
combined_dir = os.path.join(source_dir, "Combined_JSONs")
os.makedirs(combined_dir, exist_ok=True)

# First, group JSON files by prefix (existing functionality)
print("Grouping JSON files by prefix...")
for file_name in os.listdir(source_dir):
    # Only process JSON files
    if file_name.endswith(".json"):
        # Take prefix before first underscore as folder name
        prefix = file_name.split("_")[0]
        folder_path = os.path.join(grouped_dir, prefix)
        os.makedirs(folder_path, exist_ok=True)

        # Copy JSON file into the folder (changed from move to copy to preserve originals)
        source_file = os.path.join(source_dir, file_name)
        dest_file = os.path.join(folder_path, file_name)
        if not os.path.exists(dest_file):
            shutil.copy2(source_file, dest_file)

print("JSON files have been grouped into subfolders!")

# Now, combine JSON files within each folder
print("Combining JSON files within each folder...")

def combine_json_files(folder_path, folder_name):
    """Combine all JSON files in a folder into a single JSON structure"""
    combined_data = []
    json_files = []
    
    # Get all JSON files in the folder
    for file_name in os.listdir(folder_path):
        if file_name.endswith(".json"):
            json_files.append(file_name)
    
    if not json_files:
        print(f"No JSON files found in folder: {folder_name}")
        return None
    
    print(f"Processing folder '{folder_name}' with {len(json_files)} JSON files...")
    
    for json_file in json_files:
        file_path = os.path.join(folder_path, json_file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
                # Create a structure that preserves the source file information
                file_entry = {
                    "source_file": json_file,
                    "data": data
                }
                combined_data.append(file_entry)
                
        except json.JSONDecodeError as e:
            print(f"Error reading JSON file {json_file}: {e}")
            continue
        except Exception as e:
            print(f"Error processing file {json_file}: {e}")
            continue
    
    return combined_data

# Process each folder in Grouped_JSONs
for folder_name in os.listdir(grouped_dir):
    folder_path = os.path.join(grouped_dir, folder_name)
    
    # Skip if not a directory
    if not os.path.isdir(folder_path):
        continue
    
    # Combine JSON files in this folder
    combined_data = combine_json_files(folder_path, folder_name)
    
    if combined_data:
        # Create output file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"{folder_name}_combined_{timestamp}.json"
        output_path = os.path.join(combined_dir, output_filename)
        
        # Create metadata for the combined file
        metadata = {
            "combined_timestamp": timestamp,
            "source_folder": folder_name,
            "total_files_processed": len(combined_data),
            "file_list": [entry["source_file"] for entry in combined_data]
        }
        
        # Final structure
        final_output = {
            "metadata": metadata,
            "combined_data": combined_data
        }
        
        # Save combined JSON
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(final_output, f, indent=2, ensure_ascii=False)
            print(f"✓ Combined {len(combined_data)} files from '{folder_name}' -> {output_filename}")
        except Exception as e:
            print(f"✗ Error saving combined file for '{folder_name}': {e}")

print(f"\nCombination complete! Check the 'Combined_JSONs' folder for results.")