import requests
import base64
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# —– Configuration —–
owner = "OPSWAT"
repo = "endpointsecsdk"
base_dir_path = ""  # Empty string means explore entire repository
branch = "main"  # or whichever branch the examples live on
token = os.getenv("GITHUB_TOKEN")  # Get token from environment variable

if not token:
    raise RuntimeError("Please set GITHUB_TOKEN environment variable")

headers = {
    "Authorization": f"Bearer {token}",
    "Accept": "application/vnd.github.v3+json"
}

def list_directory_contents(dir_path):
    """List contents of a directory in the GitHub repo"""
    list_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{dir_path}?ref={branch}"
    resp = requests.get(list_url, headers=headers)
    if resp.status_code != 200:
        print(f"Error listing directory {dir_path}:", resp.status_code, resp.text)
        return []
    return resp.json()

def fetch_file_content(file_path):
    """Fetch content of a specific file"""
    file_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}?ref={branch}"
    resp = requests.get(file_url, headers=headers)
    if resp.status_code != 200:
        print(f"Error fetching file {file_path}:", resp.status_code, resp.text)
        return None
    
    file_data = resp.json()
    # The content is base64-encoded
    content = base64.b64decode(file_data["content"]).decode("utf-8")
    return content

def explore_directory_recursively(dir_path, max_depth=5, current_depth=0):
    """Recursively explore directory and find all code files"""
    if current_depth > max_depth:
        with open("endpointsecsdk_exploration_log.txt", 'a', encoding='utf-8') as log:
            log.write(f"⚠️  Max depth reached for {dir_path}\n")
        return {"files": [], "subdirs": {}}
    
    with open("endpointsecsdk_exploration_log.txt", 'a', encoding='utf-8') as log:
        log.write(f"{'  ' * current_depth}📁 Exploring: {dir_path if dir_path else 'ROOT'}\n")
    
    contents = list_directory_contents(dir_path)
    if not contents:
        return {"files": [], "subdirs": {}}
    
    result = {"files": [], "subdirs": {}}
    
    for item in contents:
        if item["type"] == "file":
            # Look for various code file types and documentation
            file_extensions = [".cs", ".cpp", ".c", ".h", ".hpp", ".py", ".java", ".js", ".ts", ".go", ".rs", ".swift", ".kt", 
                             ".md", ".txt", ".json", ".xml", ".yml", ".yaml", ".cmake", ".makefile", ".sh", ".bat", ".ps1",
                             ".html", ".css", ".scss", ".less", ".sql", ".php", ".rb", ".pl", ".r", ".m", ".mm"]
            
            # Skip files that are typically too large or binary
            skip_extensions = [".exe", ".dll", ".so", ".dylib", ".bin", ".zip", ".tar", ".gz", ".rar", ".7z", 
                             ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".ico", ".pdf", ".doc", ".docx", ".xls", ".xlsx"]
            
            file_size = item.get("size", 0)
            file_name_lower = item["name"].lower()
            
            # Skip very large files (>1MB) to avoid API limits
            if file_size > 1024 * 1024:
                with open("endpointsecsdk_exploration_log.txt", 'a', encoding='utf-8') as log:
                    log.write(f"{'  ' * (current_depth + 1)}⚠️  Skipping large file: {item['name']} ({file_size/1024/1024:.1f}MB)\n")
                continue
            
            # Check if it's a code/text file we want
            if (any(file_name_lower.endswith(ext) for ext in file_extensions) and 
                not any(file_name_lower.endswith(ext) for ext in skip_extensions)):
                
                # Handle root directory path
                if dir_path:
                    file_path = f"{dir_path}/{item['name']}"
                else:
                    file_path = item['name']
                
                result["files"].append({
                    "name": item["name"],
                    "path": file_path,
                    "size": file_size
                })
                with open("endpointsecsdk_exploration_log.txt", 'a', encoding='utf-8') as log:
                    log.write(f"{'  ' * (current_depth + 1)}📄 Found: {item['name']} ({file_size/1024:.1f}KB)\n")
        
        elif item["type"] == "dir":
            # Handle root directory path
            if dir_path:
                subdir_path = f"{dir_path}/{item['name']}"
            else:
                subdir_path = item['name']
            
            subdir_result = explore_directory_recursively(subdir_path, max_depth, current_depth + 1)
            if subdir_result and (subdir_result.get("files") or subdir_result.get("subdirs")):
                result["subdirs"][item["name"]] = subdir_result
    
    return result

def collect_all_files_from_structure(structure, base_path=""):
    """Flatten the nested structure to get all files"""
    all_files = []
    
    # Add files from current level
    for file_info in structure.get("files", []):
        all_files.append(file_info)
    
    # Recursively add files from subdirectories
    for subdir_name, subdir_structure in structure.get("subdirs", {}).items():
        all_files.extend(collect_all_files_from_structure(subdir_structure, f"{base_path}/{subdir_name}"))
    
    return all_files

# 1. Recursively explore the entire EndpointSecSDK repository
if base_dir_path:
    print(f"🔍 Starting recursive exploration of directory: {base_dir_path}")
else:
    print(f"🔍 Starting recursive exploration of ENTIRE repository: {owner}/{repo}")
    print("⚠️  WARNING: This will download ALL code files from the repository!")
    print("   This may take several minutes and use significant bandwidth.")

# Create log file for the exploration process
log_file = "endpointsecsdk_exploration_log.txt"
with open(log_file, 'w', encoding='utf-8') as log:
    if base_dir_path:
        log.write(f"🔍 Starting recursive exploration of directory: {base_dir_path}\n")
    else:
        log.write(f"🔍 Starting recursive exploration of ENTIRE repository: {owner}/{repo}\n")
    log.write("="*60 + "\n")

directory_structure = explore_directory_recursively(base_dir_path)

if not directory_structure["files"] and not directory_structure["subdirs"]:
    print("❌ No code files found in base directory")
    exit(1)

# Collect all files from the nested structure
all_files = collect_all_files_from_structure(directory_structure)

print(f"🎯 Found {len(all_files)} total code files")

# Group files by their directory for better organization
files_by_directory = {}
for file_info in all_files:
    dir_path = "/".join(file_info["path"].split("/")[:-1])
    if dir_path not in files_by_directory:
        files_by_directory[dir_path] = []
    files_by_directory[dir_path].append(file_info)

# Write summary to log file
with open("endpointsecsdk_exploration_log.txt", 'a', encoding='utf-8') as log:
    log.write(f"\n{'='*60}\n")
    log.write("CODE FILES SUMMARY\n")
    log.write(f"{'='*60}\n")

    for directory, files in files_by_directory.items():
        log.write(f"\n📁 {directory}:\n")
        for file_info in files:
            file_size_kb = file_info["size"] / 1024 if file_info["size"] else 0
            log.write(f"   📄 {file_info['name']} ({file_size_kb:.1f}KB)\n")

# Create detailed content log
content_log_file = "endpointsecsdk_complete_file_contents.txt"
with open(content_log_file, 'w', encoding='utf-8') as content_log:
    content_log.write(f"{'='*60}\n")
    content_log.write("DETAILED FILE CONTENTS\n")
    content_log.write(f"{'='*60}\n")

    # Now fetch and save content for each code file
    for directory, files in files_by_directory.items():
        content_log.write(f"\n🔍 DIRECTORY: {directory}\n")
        content_log.write("="*50 + "\n")
        
        for file_info in files:
            content_log.write(f"\n📄 FILE: {file_info['name']}\n")
            content_log.write("-" * 40 + "\n")
            
            print(f"📥 Fetching: {file_info['path']}")
            content = fetch_file_content(file_info['path'])
            if content:
                content_log.write(content + "\n")
                lines = content.split('\n')
                content_log.write(f"\n[Total lines: {len(lines)}]\n")
            else:
                content_log.write("❌ Failed to fetch file content\n")
            
            content_log.write("-" * 40 + "\n")

# Export to markdown file
output_file = "EndpointSecSDK_Complete_Repository_Documentation.md"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("# OPSWAT MetaDefender Security Endpoint SDK - Complete Repository\n\n")
    f.write("This document contains all the source code and documentation files from the entire EndpointSecSDK repository.\n\n")
    f.write(f"Generated from: {owner}/{repo} - {branch} branch\n\n")
    f.write(f"Total files found: {len(all_files)}\n\n")
    
    f.write("## Table of Contents\n\n")
    for directory in sorted(files_by_directory.keys()):
        dir_anchor = directory.replace('/', '-').replace(' ', '-').lower()
        f.write(f"- [{directory}](#{dir_anchor})\n")
        for file_info in files_by_directory[directory]:
            file_anchor = file_info['name'].replace('.', '').replace(' ', '-').lower()
            f.write(f"  - [{file_info['name']}](#{dir_anchor}-{file_anchor})\n")
    f.write("\n---\n\n")
    
    # Write detailed content
    for directory in sorted(files_by_directory.keys()):
        dir_anchor = directory.replace('/', '-').replace(' ', '-').lower()
        f.write(f"## {directory}\n\n")
        
        for file_info in files_by_directory[directory]:
            file_anchor = file_info['name'].replace('.', '').replace(' ', '-').lower()
            f.write(f"### {file_info['name']}\n\n")
            f.write(f"**File Path:** `{file_info['path']}`\n\n")
            f.write(f"**File Size:** {file_info['size']} bytes\n\n")
            
            content = fetch_file_content(file_info['path'])
            if content:
                # Determine language for syntax highlighting
                ext = file_info['name'].split('.')[-1].lower()
                lang_map = {
                    'cs': 'csharp', 'cpp': 'cpp', 'c': 'c', 'h': 'c', 'hpp': 'cpp',
                    'py': 'python', 'java': 'java', 'js': 'javascript', 'ts': 'typescript',
                    'go': 'go', 'rs': 'rust', 'swift': 'swift', 'kt': 'kotlin'
                }
                language = lang_map.get(ext, ext)
                
                f.write(f"```{language}\n")
                f.write(content)
                f.write("\n```\n\n")
            else:
                f.write("❌ Failed to fetch file content\n\n")
            
            f.write("---\n\n")

print(f"\n{'='*60}")
print("🎉 Exploration complete!")
print(f"Found code files in {len(files_by_directory)} directories")
print(f"Total code files: {len(all_files)}")

# Show file type breakdown
file_types = {}
for file_info in all_files:
    ext = file_info['name'].split('.')[-1].lower()
    file_types[ext] = file_types.get(ext, 0) + 1

print(f"\n📊 File type breakdown:")
for ext, count in sorted(file_types.items()):
    print(f"   .{ext}: {count} files")

# Write final summary to log
with open("endpointsecsdk_exploration_log.txt", 'a', encoding='utf-8') as log:
    log.write(f"\n{'='*60}\n")
    log.write("🎉 Exploration complete!\n")
    log.write(f"Found code files in {len(files_by_directory)} directories\n")
    log.write(f"Total code files: {len(all_files)}\n")
    
    log.write(f"\n📊 File type breakdown:\n")
    for ext, count in sorted(file_types.items()):
        log.write(f"   .{ext}: {count} files\n")
    
    log.write(f"{'='*60}\n")

print(f"\n📄 Files created:")
print(f"   📊 Exploration log: endpointsecsdk_exploration_log.txt")
print(f"   📄 Detailed content: {content_log_file}")
print(f"   📚 Markdown documentation: {output_file}")
print(f"{'='*60}")