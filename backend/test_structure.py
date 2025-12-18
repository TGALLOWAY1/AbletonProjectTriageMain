import os
import time

# --- CONFIGURATION ---
# Add the path to your big "Music Production" folder here
TEST_ROOT = "/Users/tjgalloway/Library/Mobile Documents/com~apple~CloudDocs/MUSIC PRODUCTION" 

def get_project_type(path, dirnames, filenames):
    """
    Decides if the current folder is a 'Project Root', a 'Bucket', or just a container.
    """
    # 1. STRONG INDICATOR: Has standard Ableton structure
    has_samples = "Samples" in dirnames
    has_backup = "Backup" in dirnames
    has_project_info = "Project Info" in dirnames
    
    if has_samples or has_backup or has_project_info:
        return "PROJECT_FOLDER"
    
    # 2. LOOSE FILE INDICATOR: Just contains .als files
    als_files = [f for f in filenames if f.endswith('.als')]
    if als_files:
        return "LOOSE_CONTAINER"
        
    return "CATEGORY_FOLDER"

def print_tree(start_path):
    print(f"\nScanning Structure for: {start_path}\n")
    print(f"📂 [ROOT] {os.path.basename(start_path)}")
    
    project_count = 0
    
    # We use os.walk but we modify 'dirnames' to stop recursion when we find a project
    for root, dirnames, filenames in os.walk(start_path):
        
        # Calculate depth to format the visual tree
        rel_path = os.path.relpath(root, start_path)
        if rel_path == ".":
            depth = 0
        else:
            depth = rel_path.count(os.sep) + 1
            
        indent = "    " * depth
        folder_name = os.path.basename(root)
        
        # IGNORE SYSTEM FOLDERS
        if folder_name.startswith('.') or folder_name in ["__MACOSX"]:
            continue

        # ANALYZE THE FOLDER
        folder_type = get_project_type(root, dirnames, filenames)
        
        if folder_type == "PROJECT_FOLDER":
            # LOGIC: It's a proper project folder.
            # 1. Identify the Champion (Newest .als)
            als_files = [f for f in filenames if f.endswith('.als')]
            champion = "No .als found"
            if als_files:
                full_paths = [os.path.join(root, f) for f in als_files]
                champion = os.path.basename(max(full_paths, key=os.path.getmtime))
            
            # 2. Print the Entry
            print(f"{indent}├── 🎵 [PROJECT] {folder_name}")
            print(f"{indent}│      └── Main File: {champion} (+{len(als_files)-1} versions)")
            
            project_count += 1
            
            # 3. STOP RECURSION: Don't look inside 'Samples' or 'Backup'
            # We clear the list of subdirectories so os.walk doesn't go deeper here
            dirnames[:] = [] 
            
        elif folder_type == "LOOSE_CONTAINER":
            # LOGIC: It's a folder with random .als files (maybe a "Sound Design" bucket)
            # Check if we are already inside a Project Folder (handled above), 
            # if not, this is a "Bucket"
            
            als_files = [f for f in filenames if f.endswith('.als')]
            als_files.sort() # Alphabetical
            
            print(f"{indent}├── 📦 [BUCKET] {folder_name}")
            for f in als_files:
                 print(f"{indent}│      └── 📄 {f}")
                 
        else:
            # LOGIC: It's a category folder (e.g. "Dubstep", "2023")
            # We verify it's not the root itself before printing
            if rel_path != ".":
                print(f"{indent}├── 📂 {folder_name}")
            
            # Allow recursion to continue to find projects inside
            
    print(f"\n--- Scan Complete. Found {project_count} Proper Projects. ---")

if __name__ == "__main__":
    if os.path.exists(TEST_ROOT):
        print_tree(TEST_ROOT)
    else:
        print("Error: Path not found. Check your TEST_ROOT string.")
