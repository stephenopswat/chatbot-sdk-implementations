# Data Preprocessing Scripts

This folder contains Python scripts for cleaning, organizing, and preprocessing documentation data from various sources (Confluence exports and Github website scrapes) into structured JSON formats suitable for chatbot training or knowledge base creation.

## 📁 Scripts Overview

### 1. `preprocess_docs.py` - Confluence Text Processor
**Purpose**: Converts raw Confluence text files into clean, structured JSON format

**Input**: 
- Raw `.txt` files exported from Confluence
- Files should be in a source directory (configurable)

**Output**: 
- Individual `.json` files (one per document)
- Each JSON contains: source path, extracted date, filename, cleaned content, and brief summary

**Key Features**:
- Removes HTML tags and formatting
- Strips URLs and unwanted characters
- Extracts dates from filenames (YYYY.MM.DD format)
- Generates automatic brief summaries (first 30 words)
- Normalizes whitespace and encoding

### 2. `data2process.py` - Website JSONL Cleaner  
**Purpose**: Cleans and preprocesses JSONL data scraped from OPSWAT website

**Input**: 
- `opswat_docs.jsonl` - Raw website scrape data in JSONL format

**Output**: 
- `opswat_docs_cleaned.jsonl` - Cleaned and structured data

**Key Features**:
- Removes privacy/cookie/consent content
- Cleans HTML tags and unwanted text sections
- Filters out irrelevant links and headings
- Adds content type summaries
- Preserves important documentation structure

### 3. `group.py` - Simple File Organizer
**Purpose**: Basic organization of JSON files by filename prefix

**Input**: 
- Individual JSON files in the same directory

**Output**: 
- `Grouped_JSONs/` folder with subfolders organized by prefix
- Files grouped by text before first underscore in filename

**Key Features**:
- Automatic folder creation based on prefixes
- Moves files into appropriate subdirectories
- Simple and fast organization

### 4. `contentGroup.py` - Advanced Grouping & Combining
**Purpose**: Advanced file processing that both groups AND combines JSON files

**Input**: 
- Individual JSON files in the same directory

**Output**: 
- `Grouped_JSONs/` - Files organized by prefix (like group.py)
- `Combined_JSONs/` - Combined files with metadata

**Key Features**:
- Groups files by prefix into subdirectories
- Combines all files in each group into single JSON
- Preserves source file information and metadata
- Adds timestamps and processing statistics
- Creates comprehensive combined datasets

## 🚀 Usage Instructions

### Option A: Processing Confluence Text Files

1. **Prepare your data**: Place Confluence `.txt` files in a source directory
2. **Configure paths**: Edit `preprocess_docs.py` to set correct input/output paths:
   ```python
   process_all_files(
       r"C:\path\to\confluence\exports",  # Input directory
       r"C:\path\to\output\json"          # Output directory
   )
   ```
3. **Run preprocessing**:
   ```bash
   cd "Data Preprocessing"
   python preprocess_docs.py
   ```
4. **Organize and combine** (choose one):
   ```bash
   # Simple grouping only
   python group.py
   
   # OR advanced grouping + combining
   python contentGroup.py
   ```

### Option B: Processing Website JSONL Data

1. **Prepare data**: Ensure `opswat_docs.jsonl` is in the Data Preprocessing directory
2. **Clean the data**:
   ```bash
   cd "Data Preprocessing"
   python data2process.py
   ```
3. **Process cleaned data**: 
   - Convert JSONL to individual JSON files (manual step or modify scripts)
   - Then run `contentGroup.py` for organization

### Option C: Processing Existing JSON Files

If you already have individual JSON files:

1. **Place JSON files** in the Data Preprocessing directory
2. **Run advanced processing**:
   ```bash
   cd "Data Preprocessing"
   python contentGroup.py
   ```

## 📊 Expected Output Structure

After running the complete pipeline:

```
Data Preprocessing/
├── Grouped_JSONs/           # Files organized by prefix
│   ├── prefix1/
│   │   ├── prefix1_file1.json
│   │   └── prefix1_file2.json
│   └── prefix2/
│       └── prefix2_file1.json
├── Combined_JSONs/          # Combined datasets
│   ├── prefix1_combined_20241030_143052.json
│   └── prefix2_combined_20241030_143052.json
└── [original files remain unchanged]
```

### Combined JSON Structure:
```json
{
  "metadata": {
    "combined_timestamp": "20241030_143052",
    "source_folder": "prefix1",
    "total_files_processed": 5,
    "file_list": ["file1.json", "file2.json", ...]
  },
  "combined_data": [
    {
      "source_file": "file1.json",
      "data": { /* original file content */ }
    },
    ...
  ]
}
```

## 🔧 Configuration & Customization

### Modifying File Paths
Edit the path variables in each script:
- `preprocess_docs.py`: Modify input/output directories in main function
- `data2process.py`: Change `input_path` and `output_path` variables

### Adjusting Cleaning Rules
- **HTML removal**: Modify BeautifulSoup parsing in cleaning functions
- **Content filtering**: Update `ignore_keywords` lists for different filtering
- **Summary generation**: Adjust `max_words` parameter for brief length

### File Organization
- **Grouping logic**: Modify prefix extraction logic (currently splits on "_")
- **Output naming**: Customize timestamp format and filename patterns

## 📋 Requirements

```bash
pip install beautifulsoup4 pathlib
```

## ⚠️ Important Notes

- **Backup your data**: Scripts preserve original files, but always backup important data
- **Encoding**: Scripts handle UTF-8 encoding and ignore problematic characters
- **Memory usage**: Large datasets may require chunked processing for very large files
- **File conflicts**: Existing output files are overwritten - check before running

## 🔄 Processing Flow Summary

```
Raw Data → Clean → Group → Combine → Ready for Chatbot Training
    ↓         ↓       ↓        ↓            ↓
[.txt/.jsonl] → [.json] → [folders] → [combined] → [structured dataset]
```

Choose the appropriate scripts based on your data source and processing needs!
