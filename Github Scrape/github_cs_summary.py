import requests
import base64
import os

# —– Configuration —–
owner = "OPSWAT"
repo = "endpointsecsdk"
base_dir_path = "HelloWorld/src"  # Base directory to explore
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

def summarize_cs_files_in_project(project_dir):
    """Summarize .cs files in a project directory"""
    contents = list_directory_contents(project_dir)
    if not contents:
        return []
    
    cs_files = []
    for item in contents:
        if item["type"] == "file" and item["name"].endswith(".cs"):
            cs_files.append(item["name"])
    
    return cs_files

# 1. First, list all directories in HelloWorld/src and summarize C# files
print(f"Exploring base directory: {base_dir_path}")
base_contents = list_directory_contents(base_dir_path)

if not base_contents:
    print("No contents found in base directory")
    exit(1)

# Find all subdirectories (project folders) and their C# files
project_summary = {}
for item in base_contents:
    if item["type"] == "dir":
        project_name = item["name"]
        project_path = f"{base_dir_path}/{project_name}"
        cs_files = summarize_cs_files_in_project(project_path)
        if cs_files:
            project_summary[project_name] = cs_files

print(f"\n{'='*60}")
print("C# FILES SUMMARY")
print(f"{'='*60}")

for project, files in project_summary.items():
    print(f"\n📁 {project}:")
    for file in files:
        print(f"   📄 {file}")

print(f"\n{'='*60}")
print("DETAILED FILE CONTENTS")
print(f"{'='*60}")

# Now fetch and display content for each C# file
for project_name, cs_files in project_summary.items():
    print(f"\n🔍 PROJECT: {project_name}")
    print("="*50)
    
    for cs_file in cs_files:
        file_path = f"{base_dir_path}/{project_name}/{cs_file}"
        print(f"\n📄 FILE: {cs_file}")
        print("-" * 40)
        
        content = fetch_file_content(file_path)
        if content:
            # Show first 30 lines to keep output manageable
            lines = content.split('\n')
            if len(lines) > 30:
                print('\n'.join(lines[:30]))
                print(f"\n... [File continues for {len(lines) - 30} more lines] ...")
                print(f"Total lines: {len(lines)}")
            else:
                print(content)
        else:
            print("❌ Failed to fetch file content")
        
        print("-" * 40)

# Export to markdown file
output_file = "HelloWorld_CSharp_Files_Documentation.md"
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("# OPSWAT MetaDefender Security Endpoint SDK - HelloWorld C# Files\n\n")
    f.write("This document contains all the C# source files from the HelloWorld samples.\n\n")
    f.write(f"Generated on: {owner}/{repo} - {branch} branch\n\n")
    
    f.write("## Table of Contents\n\n")
    for project_name in project_summary.keys():
        f.write(f"- [{project_name}](#{project_name.lower()})\n")
        for cs_file in project_summary[project_name]:
            file_anchor = cs_file.replace('.', '').lower()
            f.write(f"  - [{cs_file}](#{project_name.lower()}-{file_anchor})\n")
    f.write("\n---\n\n")
    
    # Write detailed content
    for project_name, cs_files in project_summary.items():
        f.write(f"## {project_name}\n\n")
        
        for cs_file in cs_files:
            file_path = f"{base_dir_path}/{project_name}/{cs_file}"
            file_anchor = cs_file.replace('.', '').lower()
            f.write(f"### {project_name} - {cs_file}\n\n")
            f.write(f"**File Path:** `{file_path}`\n\n")
            
            content = fetch_file_content(file_path)
            if content:
                f.write("```csharp\n")
                f.write(content)
                f.write("\n```\n\n")
            else:
                f.write("❌ Failed to fetch file content\n\n")
            
            f.write("---\n\n")

print(f"\n{'='*60}")
print("🎉 Exploration complete!")
print(f"Found C# files in {len(project_summary)} projects")
total_files = sum(len(files) for files in project_summary.values())
print(f"Total C# files: {total_files}")
print(f"📄 Documentation exported to: {output_file}")
print(f"{'='*60}")