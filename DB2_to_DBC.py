import os
import csv
from pathlib import Path
from collections import defaultdict

# Configuration
INPUT_DIR = "0_Input"
OUTPUT_DIR = "2_DBCRetail_to_Wotlk_csv"
WOTLK_DIR = "1_DBCWotlk_csv"
AUDIO_EXTENSIONS = {'.wav', '.mp3', '.ogg'}
MODEL_EXTENSIONS = {'.m2'}
TEXTURE_EXTENSIONS = {'.blp'}

def find_listfile(directory):
    """
    Find a file containing 'listfile' in its name (case-insensitive).
    Returns the full path to the file, or None if not found.
    """
    for filename in os.listdir(directory):
        if 'listfile' in filename.lower() and filename.lower().endswith('.csv'):
            return os.path.join(directory, filename)
    return None

def find_table_file(directory, table_name):
    """
    Find a CSV file matching the table name (case-insensitive, ignoring version).
    Returns the full path to the file, or None if not found.
    """
    table_name_lower = table_name.lower()
    for filename in os.listdir(directory):
        if filename.lower().endswith('.csv'):
            # Extract base name without version (e.g., "SoundKitEntry" from "SoundKitEntry.11.2.5.64502.csv")
            base_name = filename.split('.')[0]
            if base_name.lower() == table_name_lower:
                return os.path.join(directory, filename)
    return None

def load_audio_files(listfile_path):
    """
    Load audio files from listfile.
    Returns a dictionary: {FileID: normalized_path}
    Only includes .wav, .mp3, and .ogg files (case-insensitive).
    Normalizes paths to use backslashes.
    """
    audio_files = {}
    
    with open(listfile_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            if len(row) >= 2:
                file_id = row[0].strip()
                file_path = row[1].strip()
                
                # Check if file has an audio extension (case-insensitive)
                path_lower = file_path.lower()
                if any(path_lower.endswith(ext) for ext in AUDIO_EXTENSIONS):
                    # Normalize path: replace / with \
                    normalized_path = file_path.replace('/', '\\')
                    audio_files[file_id] = normalized_path
    
    return audio_files

def load_model_files(listfile_path):
    """
    Load model files (.m2) from listfile.
    Returns a dictionary: {FileID: normalized_path_with_mdx}
    Replaces .m2 extension with .mdx in the path.
    Normalizes paths to use backslashes.
    """
    model_files = {}
    
    with open(listfile_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            if len(row) >= 2:
                file_id = row[0].strip()
                file_path = row[1].strip()
                
                # Check if file has .m2 extension (case-insensitive)
                path_lower = file_path.lower()
                if path_lower.endswith('.m2'):
                    # Normalize path: replace / with \
                    normalized_path = file_path.replace('/', '\\')
                    # Replace .m2 with .mdx
                    mdx_path = normalized_path[:-3] + '.mdx'
                    model_files[file_id] = mdx_path
    
    return model_files

def load_texture_files(listfile_path):
    """
    Load texture files (.blp) from listfile.
    Returns a dictionary: {FileID: filename_without_extension}
    Extracts only the filename without path and without .blp extension.
    """
    texture_files = {}
    
    with open(listfile_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            if len(row) >= 2:
                file_id = row[0].strip()
                file_path = row[1].strip()
                
                # Check if file has .blp extension (case-insensitive)
                path_lower = file_path.lower()
                if path_lower.endswith('.blp'):
                    # Normalize path: replace / with \
                    normalized_path = file_path.replace('/', '\\')
                    # Extract filename without path and extension
                    if '\\' in normalized_path:
                        filename = normalized_path.split('\\')[-1]
                    else:
                        filename = normalized_path
                    # Remove .blp extension
                    filename_no_ext = filename[:-4]
                    texture_files[file_id] = filename_no_ext
    
    return texture_files

def load_soundkit_entries(soundkit_path):
    """
    Load SoundKitEntry data and group by SoundKitID.
    Returns a dictionary: {SoundKitID: [list of entries]}
    """
    soundkit_data = defaultdict(list)
    
    with open(soundkit_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            soundkit_id = row_normalized['soundkitid'].strip()
            soundkit_data[soundkit_id].append(row_normalized)
    
    return soundkit_data

def find_common_directory(paths):
    """
    Find the common directory path from a list of file paths.
    Returns the common directory WITHOUT trailing backslash if ALL files share the same directory.
    Returns empty string if files are in different directories.
    """
    if not paths:
        return ""
    
    # Filter out empty paths
    valid_paths = [p for p in paths if p]
    if not valid_paths:
        return ""
    
    if len(valid_paths) == 1:
        # Single file: extract its directory
        parts = valid_paths[0].split('\\')
        if len(parts) > 1:
            return '\\'.join(parts[:-1])
        return ""
    
    # Extract directories from all paths (everything except filename)
    directories = []
    for path in valid_paths:
        parts = path.split('\\')
        if len(parts) > 1:
            directories.append('\\'.join(parts[:-1]))
        else:
            directories.append("")
    
    # Check if all directories are exactly the same
    if len(set(directories)) == 1:
        return directories[0]
    
    # Different directories, return empty
    return ""

def load_wotlk_soundentries(wotlk_path):
    """
    Load WotLK SoundEntries data.
    Returns a dictionary: {ID: Name}
    """
    wotlk_names = {}
    
    with open(wotlk_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            entry_id = row_normalized.get('id', '').strip()
            name = row_normalized.get('name', '').strip()
            if entry_id:
                wotlk_names[entry_id] = name
    
    return wotlk_names

def generate_name_from_file(file_path):
    """
    Generate a name from a file path by:
    1. Extracting only the filename (removing directory path)
    2. Removing the file extension
    3. Removing spaces
    """
    if not file_path:
        return ""
    
    # Get filename (everything after last \)
    if '\\' in file_path:
        filename = file_path.split('\\')[-1]
    else:
        filename = file_path
    
    # Remove extension (case-insensitive)
    filename_lower = filename.lower()
    for ext in AUDIO_EXTENSIONS:
        if filename_lower.endswith(ext):
            filename = filename[:-len(ext)]
            break
    
    # Remove spaces
    filename = filename.replace(' ', '')
    
    return filename

def has_audio_extension(file_path):
    """
    Check if a file path has an audio extension.
    """
    if not file_path:
        return False
    file_lower = file_path.lower()
    return any(file_lower.endswith(ext) for ext in AUDIO_EXTENSIONS)

def check_missing_audio_files(sound_entries):
    """
    Check for File_1 to File_10 entries that don't have audio extensions.
    This includes FileDataIDs that weren't found in the listfile.
    Returns a list of problematic entries.
    """
    issues = []
    
    for entry in sound_entries:
        entry_id = entry['ID']
        problematic_files = []
        
        # Check all File_X for missing extensions or unmapped FileDataIDs
        for i in range(1, 11):
            file_path = entry.get(f'File_{i}', '').strip()
            if file_path:
                # Check if it's a pure number (unmapped FileDataID) or missing extension
                if file_path.isdigit() or not has_audio_extension(file_path):
                    problematic_files.append((i, file_path))
        
        if problematic_files:
            issues.append({
                'ID': entry_id,
                'files': problematic_files
            })
    
    return issues

def write_soundkit_missing_log(log_path, missing_soundkit_ids):
    """
    Write a log file for SoundEntries with missing SoundKit data.
    """
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("SoundEntries - Missing SoundKit Settings\n")
        f.write("=" * 60 + "\n\n")
        f.write("The following SoundEntries have missing or incomplete SoundKit data.\n")
        f.write("Default values have been applied:\n")
        f.write("  - SoundType: 18 (Test/Temporary)\n")
        f.write("  - Flags, MinDistance, DistanceCutoff, EAXDef, SoundEntriesAdvancedID: 0\n\n")
        f.write("=" * 60 + "\n")
        f.write(f"SUMMARY:\n")
        f.write(f"  - Total entries with missing SoundKit: {len(missing_soundkit_ids)}\n")
        f.write("=" * 60 + "\n\n")
        
        for soundkit_id in missing_soundkit_ids:
            f.write(f"SoundEntries ID: {soundkit_id} (missing or incomplete SoundKit data)\n")

def write_log(log_path, issues):
    """
    Write a log file for entries with unmapped FileDataIDs or missing audio extensions.
    """
    # Count unique FileDataIDs and files with missing extensions
    unique_unmapped_ids = set()
    unique_missing_extensions = set()
    
    for issue in issues:
        for file_idx, file_path in issue['files']:
            if file_path.isdigit():
                unique_unmapped_ids.add(file_path)
            else:
                unique_missing_extensions.add(file_path)
    
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("SoundEntries - Missing FileDataID Mappings\n")
        f.write("=" * 60 + "\n\n")
        f.write("The following entries have FileDataIDs that are not in the listfile\n")
        f.write("or have File_X values without audio extensions (.wav, .mp3, .ogg).\n\n")
        f.write("NOTE: Frequency (Freq_X) has been set to 0 for all unmapped FileDataIDs\n")
        f.write("to prevent the game from attempting to play non-existent files.\n\n")
        f.write("These FileDataIDs need to be manually corrected once the listfile\n")
        f.write("is updated with the missing file paths.\n\n")
        f.write("=" * 60 + "\n")
        f.write(f"SUMMARY:\n")
        f.write(f"  - Unique FileDataIDs not in listfile: {len(unique_unmapped_ids)}\n")
        f.write(f"  - Unique files with missing audio extension: {len(unique_missing_extensions)}\n")
        f.write(f"  - Total entries affected: {len(issues)}\n")
        f.write("=" * 60 + "\n\n")
        
        for issue in issues:
            f.write(f"ID: {issue['ID']}\n")
            
            for file_idx, file_path in issue['files']:
                if file_path.isdigit():
                    f.write(f"  File_{file_idx}: {file_path} (FileDataID not in listfile, Freq_{file_idx} = 0)\n")
                else:
                    f.write(f"  File_{file_idx}: {file_path} (missing audio extension)\n")
            
            f.write("\n")

def apply_names(sound_entries, use_wotlk):
    """
    Apply names to SoundEntries.
    If use_wotlk is True, load WotLK names and use them where available.
    Generate names from File_1 for missing entries.
    """
    wotlk_names = {}
    
    if use_wotlk:
        wotlk_path = os.path.join(WOTLK_DIR, "Wotlk_SoundEntries.csv")
        if os.path.exists(wotlk_path):
            print(f"Loading WotLK names from: {wotlk_path}")
            wotlk_names = load_wotlk_soundentries(wotlk_path)
            print(f"Loaded {len(wotlk_names)} WotLK names")
        else:
            print(f"WARNING: WotLK file not found at {wotlk_path}")
    
    # Apply names
    wotlk_matched = 0
    generated = 0
    
    for entry in sound_entries:
        entry_id = entry['ID']
        
        if use_wotlk and entry_id in wotlk_names:
            # Use WotLK name
            entry['Name'] = wotlk_names[entry_id]
            wotlk_matched += 1
        else:
            # Generate from File_1
            file_1 = entry.get('File_1', '').strip()
            if file_1:
                entry['Name'] = generate_name_from_file(file_1)
                generated += 1
            else:
                entry['Name'] = ""
    
    if use_wotlk:
        print(f"Applied {wotlk_matched} WotLK names, generated {generated} new names")
    else:
        print(f"Generated {generated} names from File_1")

def load_creature_display_info(creature_display_path):
    """
    Load CreatureDisplayInfo table from input.
    Returns a list of dictionaries with normalized column names.
    """
    creature_display_data = []
    
    with open(creature_display_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            creature_display_data.append(row_normalized)
    
    return creature_display_data

def generate_object_effect_package_output(package_elem_entries, object_effect_group_entries):
    """
    Generate ObjectEffectPackage output from ObjectEffectPackageElem entries.
    Groups by ObjectEffectPackageID and uses the first non-empty ObjectEffectGroup Name found.
    Returns a list of dictionaries for output.
    """
    # Create lookup dictionary for ObjectEffectGroup names
    group_names = {entry['ID']: entry.get('Name', '') for entry in object_effect_group_entries}
    
    # Group by ObjectEffectPackageID and collect first non-empty name
    package_names = {}
    
    for entry in package_elem_entries:
        package_id = entry.get('ObjectEffectPackageID', '').strip()
        group_id = entry.get('ObjectEffectGroupID', '').strip()
        
        if package_id and package_id not in package_names:
            # Get name from ObjectEffectGroup
            name = group_names.get(group_id, '')
            if name:
                package_names[package_id] = name
            else:
                # Reserve the slot but with empty name for now
                package_names[package_id] = ''
        elif package_id and package_id in package_names and not package_names[package_id]:
            # If we already have this package but with empty name, update if we find non-empty
            name = group_names.get(group_id, '')
            if name:
                package_names[package_id] = name
    
    # Generate output entries
    output_entries = []
    for package_id, name in sorted(package_names.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
        entry_data = {
            'ID': package_id,
            'Name': name
        }
        output_entries.append(entry_data)
    
    return output_entries

def write_object_effect_package(output_path, package_entries, wdbx_format=False):
    """
    Write ObjectEffectPackage to CSV file.
    If wdbx_format is True, quote all fields.
    Sorts entries by ID.
    """
    fieldnames = ['ID', 'Name']
    
    # Sort by ID
    sorted_entries = sorted(package_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def load_object_effect_package_elem(package_elem_path):
    """
    Load ObjectEffectPackageElem table from input.
    Returns a list of dictionaries with normalized column names.
    """
    package_elem_data = []
    
    with open(package_elem_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            package_elem_data.append(row_normalized)
    
    return package_elem_data

def generate_object_effect_package_elem_output(package_elem_data, object_effect_group_entries):
    """
    Generate ObjectEffectPackageElem output from input data.
    Filters out entries where ObjectEffectGroupID doesn't exist in ObjectEffectGroup.
    Returns a tuple: (output_entries, skipped_ids)
    """
    # Create set of valid ObjectEffectGroupIDs
    valid_group_ids = {entry['ID'] for entry in object_effect_group_entries}
    
    output_entries = []
    skipped_ids = []
    
    for row in package_elem_data:
        entry_id = row.get('id', '').strip()
        group_id = row.get('objecteffectgroupid', '').strip()
        
        # Skip if ObjectEffectGroupID is not in valid groups
        if group_id and group_id not in valid_group_ids:
            skipped_ids.append({'ID': entry_id, 'ObjectEffectGroupID': group_id})
            continue
        
        entry_data = {
            'ID': entry_id,
            'ObjectEffectPackageID': row.get('objecteffectpackageid', '').strip(),
            'ObjectEffectGroupID': group_id,
            'StateType': row.get('statetype', '').strip()
        }
        
        output_entries.append(entry_data)
    
    return output_entries, skipped_ids

def write_object_effect_package_elem_log(log_path, skipped_ids):
    """
    Write a log file for ObjectEffectPackageElem entries with invalid ObjectEffectGroupID.
    """
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("ObjectEffectPackageElem - Skipped Entries\n")
        f.write("=" * 60 + "\n\n")
        f.write("The following ObjectEffectPackageElem entries reference ObjectEffectGroupIDs\n")
        f.write("that don't exist in the ObjectEffectGroup output (likely because all their\n")
        f.write("ObjectEffect entries had EffectRecID = 0).\n\n")
        f.write("=" * 60 + "\n")
        f.write(f"SUMMARY:\n")
        f.write(f"  - Total entries skipped: {len(skipped_ids)}\n")
        f.write("=" * 60 + "\n\n")
        
        for item in skipped_ids:
            f.write(f"ObjectEffectPackageElem ID: {item['ID']}\n")
            f.write(f"  ObjectEffectGroupID: {item['ObjectEffectGroupID']} (group not found)\n\n")

def write_object_effect_package_elem(output_path, package_elem_entries, wdbx_format=False):
    """
    Write ObjectEffectPackageElem to CSV file.
    If wdbx_format is True, quote all fields.
    Sorts entries by ID.
    """
    fieldnames = ['ID', 'ObjectEffectPackageID', 'ObjectEffectGroupID', 'StateType']
    
    # Sort by ID
    sorted_entries = sorted(package_elem_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def generate_object_effect_group_output(object_effect_entries):
    """
    Generate ObjectEffectGroup output from ObjectEffect entries.
    Groups by ObjectEffectGroupID and uses the first non-empty Name found.
    Returns a list of dictionaries for output.
    """
    # Group by ObjectEffectGroupID and collect first non-empty name
    group_names = {}
    
    for entry in object_effect_entries:
        group_id = entry.get('ObjectEffectGroupID', '').strip()
        if group_id and group_id not in group_names:
            # Store first non-empty name found for this group
            name = entry.get('Name', '').strip()
            if name:
                group_names[group_id] = name
            else:
                # Reserve the slot but with empty name for now
                group_names[group_id] = ''
        elif group_id and group_id in group_names and not group_names[group_id]:
            # If we already have this group but with empty name, update if we find non-empty
            name = entry.get('Name', '').strip()
            if name:
                group_names[group_id] = name
    
    # Generate output entries
    output_entries = []
    for group_id, name in sorted(group_names.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
        entry_data = {
            'ID': group_id,
            'Name': name
        }
        output_entries.append(entry_data)
    
    return output_entries

def write_object_effect_group(output_path, object_effect_group_entries, wdbx_format=False):
    """
    Write ObjectEffectGroup to CSV file.
    If wdbx_format is True, quote all fields.
    Sorts entries by ID.
    """
    fieldnames = ['ID', 'Name']
    
    # Sort by ID
    sorted_entries = sorted(object_effect_group_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def load_object_effect(object_effect_path):
    """
    Load ObjectEffect table from input.
    Returns a list of dictionaries with normalized column names.
    """
    object_effect_data = []
    
    with open(object_effect_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            object_effect_data.append(row_normalized)
    
    return object_effect_data

def generate_object_effect_output(object_effect_data, sound_entries):
    """
    Generate ObjectEffect output from input data.
    Renames Offset_0-2 to OffsetX/Y/Z and reorders fields.
    Gets Name from SoundEntries based on EffectRecID.
    Filters out entries where EffectRecID = 0.
    Returns a tuple: (output_entries, zero_effect_rec_ids)
    """
    # Create lookup dictionary for SoundEntries names
    sound_entries_names = {entry['ID']: entry.get('Name', '') for entry in sound_entries}
    
    output_entries = []
    zero_effect_rec_ids = []
    
    for row in object_effect_data:
        effect_rec_id = row.get('effectrecid', '').strip()
        entry_id = row.get('id', '').strip()
        
        # Skip entries with EffectRecID = 0 and log them
        if effect_rec_id == '0':
            zero_effect_rec_ids.append(entry_id)
            continue
        
        # Get name from SoundEntries if EffectRecID matches
        name = sound_entries_names.get(effect_rec_id, '')
        
        entry_data = {
            'ID': entry_id,
            'Name': name,
            'ObjectEffectGroupID': row.get('objecteffectgroupid', '').strip(),
            'TriggerType': row.get('triggertype', '').strip(),
            'EventType': row.get('eventtype', '').strip(),
            'EffectRecType': row.get('effectrectype', '').strip(),
            'EffectRecID': effect_rec_id,
            'Attachment': row.get('attachment', '').strip(),
            'OffsetX': row.get('offset_0', '').strip(),
            'OffsetY': row.get('offset_1', '').strip(),
            'OffsetZ': row.get('offset_2', '').strip(),
            'ObjectEffectModifierID': row.get('objecteffectmodifierid', '').strip()
        }
        
        output_entries.append(entry_data)
    
    return output_entries, zero_effect_rec_ids

def write_object_effect_log(log_path, zero_effect_rec_ids):
    """
    Write a log file for ObjectEffect entries with EffectRecID = 0.
    """
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("ObjectEffect - Skipped Entries with EffectRecID = 0\n")
        f.write("=" * 60 + "\n\n")
        f.write("The following ObjectEffect entries have EffectRecID = 0 and were excluded\n")
        f.write("from the output as they don't reference any sound.\n\n")
        f.write("=" * 60 + "\n")
        f.write(f"SUMMARY:\n")
        f.write(f"  - Total entries skipped: {len(zero_effect_rec_ids)}\n")
        f.write("=" * 60 + "\n\n")
        
        for entry_id in zero_effect_rec_ids:
            f.write(f"ObjectEffect ID: {entry_id} (EffectRecID = 0)\n")

def write_object_effect(output_path, object_effect_entries, wdbx_format=False):
    """
    Write ObjectEffect to CSV file.
    If wdbx_format is True, quote all fields and convert float decimals from . to ,
    Sorts entries by ID.
    """
    fieldnames = [
        'ID', 'Name', 'ObjectEffectGroupID', 'TriggerType', 'EventType', 'EffectRecType',
        'EffectRecID', 'Attachment', 'OffsetX', 'OffsetY', 'OffsetZ', 'ObjectEffectModifierID'
    ]
    
    if wdbx_format:
        # Convert float fields for WDBX format
        float_fields = ['OffsetX', 'OffsetY', 'OffsetZ']
        for entry in object_effect_entries:
            for field in float_fields:
                if field in entry:
                    entry[field] = convert_float_to_wdbx(entry[field])
    
    # Sort by ID
    sorted_entries = sorted(object_effect_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def load_object_effect_modifier(object_effect_modifier_path):
    """
    Load ObjectEffectModifier table from input.
    Returns a list of dictionaries with normalized column names.
    """
    object_effect_modifier_data = []
    
    with open(object_effect_modifier_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            object_effect_modifier_data.append(row_normalized)
    
    return object_effect_modifier_data

def generate_object_effect_modifier_output(object_effect_modifier_data):
    """
    Generate ObjectEffectModifier output from input data.
    Reorders fields (Type fields first, then Params).
    Returns a list of dictionaries for output.
    """
    output_entries = []
    
    for row in object_effect_modifier_data:
        entry_data = {
            'ID': row.get('id', '').strip(),
            'InputType': row.get('inputtype', '').strip(),
            'MapType': row.get('maptype', '').strip(),
            'OutputType': row.get('outputtype', '').strip(),
            'Param_0': row.get('param_0', '').strip(),
            'Param_1': row.get('param_1', '').strip(),
            'Param_2': row.get('param_2', '').strip(),
            'Param_3': row.get('param_3', '').strip()
        }
        
        output_entries.append(entry_data)
    
    return output_entries

def write_object_effect_modifier(output_path, object_effect_entries, wdbx_format=False):
    """
    Write ObjectEffectModifier to CSV file.
    If wdbx_format is True, quote all fields and convert float decimals from . to ,
    Sorts entries by ID.
    """
    fieldnames = ['ID', 'InputType', 'MapType', 'OutputType', 'Param_0', 'Param_1', 'Param_2', 'Param_3']
    
    if wdbx_format:
        # Convert float fields for WDBX format
        float_fields = ['Param_0', 'Param_1', 'Param_2', 'Param_3']
        for entry in object_effect_entries:
            for field in float_fields:
                if field in entry:
                    entry[field] = convert_float_to_wdbx(entry[field])
    
    # Sort by ID
    sorted_entries = sorted(object_effect_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def load_particle_color(particle_color_path):
    """
    Load ParticleColor table from input.
    Returns a list of dictionaries with normalized column names.
    """
    particle_color_data = []
    
    with open(particle_color_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            particle_color_data.append(row_normalized)
    
    return particle_color_data

def generate_particle_color_output(particle_color_data):
    """
    Generate ParticleColor output from input data.
    Renames fields (0→1, 1→2, 2→3).
    Returns a list of dictionaries for output.
    """
    output_entries = []
    
    for row in particle_color_data:
        entry_data = {
            'ID': row.get('id', '').strip(),
            'Start_1': row.get('start_0', '').strip(),
            'Start_2': row.get('start_1', '').strip(),
            'Start_3': row.get('start_2', '').strip(),
            'Mid_1': row.get('mid_0', '').strip(),
            'Mid_2': row.get('mid_1', '').strip(),
            'Mid_3': row.get('mid_2', '').strip(),
            'End_1': row.get('end_0', '').strip(),
            'End_2': row.get('end_1', '').strip(),
            'End_3': row.get('end_2', '').strip()
        }
        
        output_entries.append(entry_data)
    
    return output_entries

def write_particle_color(output_path, particle_entries, wdbx_format=False):
    """
    Write ParticleColor to CSV file.
    If wdbx_format is True, quote all fields.
    Sorts entries by ID.
    """
    fieldnames = ['ID', 'Start_1', 'Start_2', 'Start_3', 'Mid_1', 'Mid_2', 'Mid_3', 'End_1', 'End_2', 'End_3']
    
    # Sort by ID
    sorted_entries = sorted(particle_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def load_creature_display_info_geoset_data(geoset_path):
    """
    Load CreatureDisplayInfoGeosetData table from input.
    Returns a dictionary: {CreatureDisplayInfoID: [(GeosetIndex, GeosetValue), ...]}
    """
    geoset_data = defaultdict(list)
    
    with open(geoset_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            display_info_id = row_normalized.get('creaturedisplayinfoid', '').strip()
            geoset_index = row_normalized.get('geosetindex', '').strip()
            geoset_value = row_normalized.get('geosetvalue', '').strip()
            
            if display_info_id and geoset_index and geoset_value:
                try:
                    geoset_data[display_info_id].append((int(geoset_index), int(geoset_value)))
                except (ValueError, TypeError):
                    pass
    
    return geoset_data

def calculate_creature_geoset(geoset_entries):
    """
    Calculate CreatureGeoset value.
    Formula: Σ(GeosetValue × 16^GeosetIndex)
    Returns tuple: (capped_value, actual_value, overflowed)
    """
    MAX_VALUE = 2147483647
    total = 0
    
    for geoset_index, geoset_value in geoset_entries:
        total += geoset_value * (16 ** geoset_index)
    
    if total > MAX_VALUE:
        return (MAX_VALUE, total, True)
    else:
        return (total, total, False)

def load_wotlk_creature_display_info(wotlk_display_path):
    """
    Load WotLK CreatureDisplayInfo data for BloodLevel.
    Returns a dictionary: {ID: BloodLevel}
    """
    wotlk_display_data = {}
    
    if not os.path.exists(wotlk_display_path):
        return wotlk_display_data
    
    with open(wotlk_display_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            entry_id = row_normalized.get('id', '').strip()
            blood_level = row_normalized.get('bloodlevel', '').strip()
            if entry_id:
                wotlk_display_data[entry_id] = blood_level if blood_level else '0'
    
    return wotlk_display_data

def generate_creature_display_info_output(creature_display_data, texture_files, geoset_data, wotlk_display_data):
    """
    Generate CreatureDisplayInfo output from input data.
    Maps texture FileDataIDs to filenames using texture_files dictionary.
    Calculates CreatureGeosetData from geoset_data.
    Gets BloodLevel from wotlk_display_data.
    Returns a tuple: (output_entries, unmapped_texture_ids, geoset_overflows)
    """
    output_entries = []
    unmapped_texture_ids = []
    geoset_overflows = []
    
    for row in creature_display_data:
        entry_id = row.get('id', '').strip()
        
        # Map texture FileDataIDs to filenames
        texture_var_0_id = row.get('texturevariationfiledataid_0', '').strip()
        texture_var_1_id = row.get('texturevariationfiledataid_1', '').strip()
        texture_var_2_id = row.get('texturevariationfiledataid_2', '').strip()
        portrait_texture_id = row.get('portraittexturefiledataid', '').strip()
        
        # Get texture names or leave empty if not found
        texture_var_1 = ''
        if texture_var_0_id and texture_var_0_id != '0':
            if texture_var_0_id in texture_files:
                texture_var_1 = texture_files[texture_var_0_id]
            else:
                unmapped_texture_ids.append({'ID': entry_id, 'FileDataID': texture_var_0_id, 'Field': 'TextureVariation_1'})
        
        texture_var_2 = ''
        if texture_var_1_id and texture_var_1_id != '0':
            if texture_var_1_id in texture_files:
                texture_var_2 = texture_files[texture_var_1_id]
            else:
                unmapped_texture_ids.append({'ID': entry_id, 'FileDataID': texture_var_1_id, 'Field': 'TextureVariation_2'})
        
        texture_var_3 = ''
        if texture_var_2_id and texture_var_2_id != '0':
            if texture_var_2_id in texture_files:
                texture_var_3 = texture_files[texture_var_2_id]
            else:
                unmapped_texture_ids.append({'ID': entry_id, 'FileDataID': texture_var_2_id, 'Field': 'TextureVariation_3'})
        
        portrait_texture_name = ''
        if portrait_texture_id and portrait_texture_id != '0':
            if portrait_texture_id in texture_files:
                portrait_texture_name = texture_files[portrait_texture_id]
            else:
                unmapped_texture_ids.append({'ID': entry_id, 'FileDataID': portrait_texture_id, 'Field': 'PortraitTextureName'})
        
        # Calculate CreatureGeosetData
        creature_geoset_value = '0'  # Default to 0 if no data
        if entry_id in geoset_data:
            capped_value, actual_value, overflowed = calculate_creature_geoset(geoset_data[entry_id])
            creature_geoset_value = str(capped_value)
            if overflowed:
                geoset_overflows.append({
                    'ID': entry_id,
                    'CalculatedValue': actual_value,
                    'CappedValue': capped_value
                })
        
        # Get BloodLevel from WotLK data, default to 0 if not found
        blood_level = wotlk_display_data.get(entry_id, '0')
        
        entry_data = {
            'ID': entry_id,
            'ModelID': row.get('modelid', '').strip(),
            'SoundID': row.get('soundid', '').strip(),
            'ExtendedDisplayInfoID': row.get('extendeddisplayinfoid', '').strip(),
            'CreatureModelScale': row.get('creaturemodelscale', '').strip(),
            'CreatureModelAlpha': row.get('creaturemodelalpha', '').strip(),
            'TextureVariation_1': texture_var_1,
            'TextureVariation_2': texture_var_2,
            'TextureVariation_3': texture_var_3,
            'PortraitTextureName': portrait_texture_name,
            'BloodLevel': blood_level,
            'BloodID': row.get('bloodid', '').strip(),
            'NPCSoundID': row.get('npcsoundid', '').strip(),
            'ParticleColorID': row.get('particlecolorid', '').strip(),
            'CreatureGeosetData': creature_geoset_value,
            'ObjectEffectPackageID': row.get('objecteffectpackageid', '').strip()
        }
        
        output_entries.append(entry_data)
    
    return output_entries, unmapped_texture_ids, geoset_overflows

def write_creature_display_info_texture_log(log_path, unmapped_texture_ids):
    """
    Write a log file for CreatureDisplayInfo entries with unmapped texture FileDataIDs.
    """
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("CreatureDisplayInfo - Missing Texture FileDataID Mappings\n")
        f.write("=" * 60 + "\n\n")
        f.write("The following entries have FileDataIDs (.blp textures) that are not in the listfile.\n")
        f.write("These FileDataIDs need to be manually corrected once the listfile\n")
        f.write("is updated with the missing texture paths.\n\n")
        f.write("=" * 60 + "\n")
        f.write(f"SUMMARY:\n")
        f.write(f"  - Unique FileDataIDs not in listfile: {len(set(item['FileDataID'] for item in unmapped_texture_ids))}\n")
        f.write(f"  - Total entries affected: {len(set(item['ID'] for item in unmapped_texture_ids))}\n")
        f.write("=" * 60 + "\n\n")
        
        # Group by ID
        current_id = None
        for item in unmapped_texture_ids:
            if current_id != item['ID']:
                if current_id is not None:
                    f.write("\n")
                current_id = item['ID']
                f.write(f"CreatureDisplayInfo ID: {item['ID']}\n")
            f.write(f"  {item['Field']}: {item['FileDataID']} (texture not in listfile)\n")
        if current_id is not None:
            f.write("\n")

def write_creature_display_info_geoset_log(log_path, geoset_overflows):
    """
    Write a log file for CreatureDisplayInfo entries with CreatureGeosetData overflow.
    """
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("CreatureDisplayInfo - CreatureGeosetData Overflow Values\n")
        f.write("=" * 60 + "\n\n")
        f.write("The following entries have calculated CreatureGeosetData values that exceed\n")
        f.write("the maximum allowed value of 2147483647. The value has been capped.\n\n")
        f.write("=" * 60 + "\n")
        f.write(f"SUMMARY:\n")
        f.write(f"  - Total entries with overflow: {len(geoset_overflows)}\n")
        f.write("=" * 60 + "\n\n")
        
        for item in geoset_overflows:
            f.write(f"CreatureDisplayInfo ID: {item['ID']}\n")
            f.write(f"  Calculated Value: {item['CalculatedValue']}\n")
            f.write(f"  Capped Value: {item['CappedValue']}\n\n")

def write_creature_display_info(output_path, creature_display_entries, wdbx_format=False):
    """
    Write CreatureDisplayInfo to CSV file.
    If wdbx_format is True, quote all fields and convert float decimals from . to ,
    Sorts entries by ID.
    """
    fieldnames = [
        'ID', 'ModelID', 'SoundID', 'ExtendedDisplayInfoID', 'CreatureModelScale',
        'CreatureModelAlpha', 'TextureVariation_1', 'TextureVariation_2', 'TextureVariation_3',
        'PortraitTextureName', 'BloodLevel', 'BloodID', 'NPCSoundID', 'ParticleColorID',
        'CreatureGeosetData', 'ObjectEffectPackageID'
    ]
    
    if wdbx_format:
        # Convert float fields for WDBX format
        float_fields = ['CreatureModelScale']
        for entry in creature_display_entries:
            for field in float_fields:
                if field in entry:
                    entry[field] = convert_float_to_wdbx(entry[field])
    
    # Sort by ID
    sorted_entries = sorted(creature_display_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def load_creature_model_data(creature_model_path):
    """
    Load CreatureModelData table from input.
    Returns a list of dictionaries with normalized column names.
    """
    creature_model_data = []
    
    with open(creature_model_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            creature_model_data.append(row_normalized)
    
    return creature_model_data

def generate_creature_model_data_output(creature_model_data, model_files):
    """
    Generate CreatureModelData output from input data.
    Maps FileDataID to ModelName using model_files dictionary.
    Returns a tuple: (output_entries, unmapped_file_ids)
    """
    output_entries = []
    unmapped_file_ids = []
    
    for row in creature_model_data:
        file_data_id = row.get('filedataid', '').strip()
        
        # Get model path from model_files dictionary, or keep FileDataID if not found
        if file_data_id in model_files:
            model_name = model_files[file_data_id]
        else:
            model_name = file_data_id
            if file_data_id:  # Only log if FileDataID is not empty
                unmapped_file_ids.append({
                    'ID': row.get('id', '').strip(),
                    'FileDataID': file_data_id
                })
        
        entry_data = {
            'ID': row.get('id', '').strip(),
            'Flags': row.get('flags', '').strip(),
            'ModelName': model_name,
            'SizeClass': row.get('sizeclass', '').strip(),
            'ModelScale': row.get('modelscale', '').strip(),
            'BloodID': row.get('bloodid', '').strip(),
            'FootprintTextureID': row.get('footprinttextureid', '').strip(),
            'FootprintTextureLength': row.get('footprinttexturelength', '').strip(),
            'FootprintTextureWidth': row.get('footprinttexturewidth', '').strip(),
            'FootprintParticleScale': row.get('footprintparticlescale', '').strip(),
            'FoleyMaterialID': row.get('foleymaterialid', '').strip(),
            'FootstepShakeSize': row.get('footstepcameraeffectid', '').strip(),
            'DeathThudShakeSize': row.get('deaththudcameraeffectid', '').strip(),
            'SoundID': row.get('soundid', '').strip(),
            'CollisionWidth': row.get('collisionwidth', '').strip(),
            'CollisionHeight': row.get('collisionheight', '').strip(),
            'MountHeight': row.get('mountheight', '').strip(),
            'GeoBoxMinX': row.get('geobox_0', '').strip(),
            'GeoBoxMinY': row.get('geobox_1', '').strip(),
            'GeoBoxMinZ': row.get('geobox_2', '').strip(),
            'GeoBoxMaxX': row.get('geobox_3', '').strip(),
            'GeoBoxMaxY': row.get('geobox_4', '').strip(),
            'GeoBoxMaxZ': row.get('geobox_5', '').strip(),
            'WorldEffectScale': row.get('worldeffectscale', '').strip(),
            'AttachedEffectScale': row.get('attachedeffectscale', '').strip(),
            'MissileCollisionRadius': row.get('missilecollisionradius', '').strip(),
            'MissileCollisionPush': row.get('missilecollisionpush', '').strip(),
            'MissileCollisionRaise': row.get('missilecollisionraise', '').strip()
        }
        
        output_entries.append(entry_data)
    
    return output_entries, unmapped_file_ids

def write_creature_model_log(log_path, unmapped_file_ids):
    """
    Write a log file for CreatureModelData entries with unmapped FileDataIDs.
    """
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("CreatureModelData - Missing Model FileDataID Mappings\n")
        f.write("=" * 60 + "\n\n")
        f.write("The following entries have FileDataIDs (.m2 models) that are not in the listfile.\n")
        f.write("These FileDataIDs need to be manually corrected once the listfile\n")
        f.write("is updated with the missing model paths.\n\n")
        f.write("=" * 60 + "\n")
        f.write(f"SUMMARY:\n")
        f.write(f"  - Unique FileDataIDs not in listfile: {len(set(item['FileDataID'] for item in unmapped_file_ids))}\n")
        f.write(f"  - Total entries affected: {len(unmapped_file_ids)}\n")
        f.write("=" * 60 + "\n\n")
        
        for item in unmapped_file_ids:
            f.write(f"CreatureModelData ID: {item['ID']}\n")
            f.write(f"  FileDataID: {item['FileDataID']} (model not in listfile)\n\n")

def write_creature_model_data(output_path, creature_model_entries, wdbx_format=False):
    """
    Write CreatureModelData to CSV file.
    If wdbx_format is True, quote all fields and convert float decimals from . to ,
    Sorts entries by ID.
    """
    fieldnames = [
        'ID', 'Flags', 'ModelName', 'SizeClass', 'ModelScale', 'BloodID',
        'FootprintTextureID', 'FootprintTextureLength', 'FootprintTextureWidth',
        'FootprintParticleScale', 'FoleyMaterialID', 'FootstepShakeSize',
        'DeathThudShakeSize', 'SoundID', 'CollisionWidth', 'CollisionHeight',
        'MountHeight', 'GeoBoxMinX', 'GeoBoxMinY', 'GeoBoxMinZ', 'GeoBoxMaxX',
        'GeoBoxMaxY', 'GeoBoxMaxZ', 'WorldEffectScale', 'AttachedEffectScale',
        'MissileCollisionRadius', 'MissileCollisionPush', 'MissileCollisionRaise'
    ]
    
    if wdbx_format:
        # Convert float fields for WDBX format
        float_fields = [
            'ModelScale', 'FootprintParticleScale', 'FootstepShakeSize', 'CollisionWidth',
            'CollisionHeight', 'MountHeight', 'GeoBoxMinX', 'GeoBoxMinY', 'GeoBoxMinZ',
            'GeoBoxMaxX', 'GeoBoxMaxY', 'GeoBoxMaxZ', 'WorldEffectScale', 'AttachedEffectScale',
            'MissileCollisionRadius', 'MissileCollisionPush', 'MissileCollisionRaise',
            'FootprintTextureLength', 'FootprintTextureWidth'
        ]
        for entry in creature_model_entries:
            for field in float_fields:
                if field in entry:
                    entry[field] = convert_float_to_wdbx(entry[field])
    
    # Sort by ID
    sorted_entries = sorted(creature_model_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def load_zone_music(zone_music_path):
    """
    Load ZoneMusic table from input.
    Returns a list of dictionaries with normalized column names.
    """
    zone_music_data = []
    
    with open(zone_music_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            zone_music_data.append(row_normalized)
    
    return zone_music_data

def generate_zone_music_output(zone_music_data):
    """
    Generate ZoneMusic output from input data.
    Renames fields (0→1, 1→2).
    Returns a list of dictionaries for output.
    """
    output_entries = []
    
    for row in zone_music_data:
        entry_data = {
            'ID': row.get('id', '').strip(),
            'SetName': row.get('setname', '').strip(),
            'SilenceIntervalMin_1': row.get('silenceintervalmin_0', '').strip(),
            'SilenceIntervalMin_2': row.get('silenceintervalmin_1', '').strip(),
            'SilenceIntervalMax_1': row.get('silenceintervalmax_0', '').strip(),
            'SilenceIntervalMax_2': row.get('silenceintervalmax_1', '').strip(),
            'Sounds_1': row.get('sounds_0', '').strip(),
            'Sounds_2': row.get('sounds_1', '').strip()
        }
        
        output_entries.append(entry_data)
    
    return output_entries

def write_zone_music(output_path, zone_music_entries, wdbx_format=False):
    """
    Write ZoneMusic to CSV file.
    If wdbx_format is True, quote all fields.
    Sorts entries by ID.
    """
    fieldnames = ['ID', 'SetName', 'SilenceIntervalMin_1', 'SilenceIntervalMin_2', 
                  'SilenceIntervalMax_1', 'SilenceIntervalMax_2', 'Sounds_1', 'Sounds_2']
    
    # Sort by ID
    sorted_entries = sorted(zone_music_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def load_zone_intro_music_table(zone_intro_path):
    """
    Load ZoneIntroMusicTable table from input.
    Returns a list of dictionaries with normalized column names.
    """
    zone_intro_data = []
    
    with open(zone_intro_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            zone_intro_data.append(row_normalized)
    
    return zone_intro_data

def generate_zone_intro_music_output(zone_intro_data):
    """
    Generate ZoneIntroMusicTable output from input data.
    Direct 1:1 mapping.
    Returns a list of dictionaries for output.
    """
    output_entries = []
    
    for row in zone_intro_data:
        entry_data = {
            'ID': row.get('id', '').strip(),
            'Name': row.get('name', '').strip(),
            'SoundID': row.get('soundid', '').strip(),
            'Priority': row.get('priority', '').strip(),
            'MinDelayMinutes': row.get('mindelayminutes', '').strip()
        }
        
        output_entries.append(entry_data)
    
    return output_entries

def write_zone_intro_music_table(output_path, zone_entries, wdbx_format=False):
    """
    Write ZoneIntroMusicTable to CSV file.
    If wdbx_format is True, quote all fields.
    Sorts entries by ID.
    """
    fieldnames = ['ID', 'Name', 'SoundID', 'Priority', 'MinDelayMinutes']
    
    # Sort by ID
    sorted_entries = sorted(zone_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def load_vocal_ui_sounds(vocal_ui_path):
    """
    Load VocalUISounds table from input.
    Returns a list of dictionaries with normalized column names.
    """
    vocal_ui_data = []
    
    with open(vocal_ui_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            vocal_ui_data.append(row_normalized)
    
    return vocal_ui_data

def load_wotlk_vocal_ui_sounds(wotlk_vocal_path):
    """
    Load WotLK VocalUISounds data for PissedSoundID fields.
    Returns a dictionary: {ID: {PissedSoundID_1, PissedSoundID_2}}
    """
    wotlk_vocal_data = {}
    
    if not os.path.exists(wotlk_vocal_path):
        return wotlk_vocal_data
    
    with open(wotlk_vocal_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            entry_id = row_normalized.get('id', '').strip()
            if entry_id:
                wotlk_vocal_data[entry_id] = {
                    'PissedSoundID_1': row_normalized.get('pissedsoundid_1', '').strip(),
                    'PissedSoundID_2': row_normalized.get('pissedsoundid_2', '').strip()
                }
    
    return wotlk_vocal_data

def generate_vocal_ui_sounds_output(vocal_ui_data, wotlk_vocal_data):
    """
    Generate VocalUISounds output from input data.
    Renames NormalSoundID_0-1 to NormalSoundID_1-2.
    Gets PissedSoundID fields from WotLK data, or sets to 0 if not found.
    Returns a list of dictionaries for output.
    """
    output_entries = []
    
    for row in vocal_ui_data:
        entry_id = row.get('id', '').strip()
        
        # Get PissedSoundID from WotLK data or default to 0
        pissed_data = wotlk_vocal_data.get(entry_id, {})
        pissed_1 = pissed_data.get('PissedSoundID_1', '0') or '0'
        pissed_2 = pissed_data.get('PissedSoundID_2', '0') or '0'
        
        entry_data = {
            'ID': entry_id,
            'VocalUIEnum': row.get('vocaluienum', '').strip(),
            'RaceID': row.get('raceid', '').strip(),
            'NormalSoundID_1': row.get('normalsoundid_0', '').strip(),
            'NormalSoundID_2': row.get('normalsoundid_1', '').strip(),
            'PissedSoundID_1': pissed_1,
            'PissedSoundID_2': pissed_2
        }
        
        output_entries.append(entry_data)
    
    return output_entries

def write_vocal_ui_sounds(output_path, vocal_entries, wdbx_format=False):
    """
    Write VocalUISounds to CSV file.
    If wdbx_format is True, quote all fields.
    Sorts entries by ID.
    """
    fieldnames = ['ID', 'VocalUIEnum', 'RaceID', 'NormalSoundID_1', 'NormalSoundID_2', 'PissedSoundID_1', 'PissedSoundID_2']
    
    # Sort by ID
    sorted_entries = sorted(vocal_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def load_sound_provider_preferences(sound_provider_path):
    """
    Load SoundProviderPreferences table from input.
    Returns a list of dictionaries with normalized column names.
    """
    sound_provider_data = []
    
    with open(sound_provider_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            sound_provider_data.append(row_normalized)
    
    return sound_provider_data

def generate_sound_provider_preferences_output(sound_provider_data):
    """
    Generate SoundProviderPreferences output from input data.
    Reorders fields (Flags moved after Description).
    Returns a list of dictionaries for output.
    """
    output_entries = []
    
    for row in sound_provider_data:
        entry_data = {
            'ID': row.get('id', '').strip(),
            'Description': row.get('description', '').strip(),
            'Flags': row.get('flags', '').strip(),
            'EAXEnvironmentSelection': row.get('eaxenvironmentselection', '').strip(),
            'EAXDecayTime': row.get('eaxdecaytime', '').strip(),
            'EAX2EnvironmentSize': row.get('eax2environmentsize', '').strip(),
            'EAX2EnvironmentDiffusion': row.get('eax2environmentdiffusion', '').strip(),
            'EAX2Room': row.get('eax2room', '').strip(),
            'EAX2RoomHF': row.get('eax2roomhf', '').strip(),
            'EAX2DecayHFRatio': row.get('eax2decayhfratio', '').strip(),
            'EAX2Reflections': row.get('eax2reflections', '').strip(),
            'EAX2ReflectionsDelay': row.get('eax2reflectionsdelay', '').strip(),
            'EAX2Reverb': row.get('eax2reverb', '').strip(),
            'EAX2ReverbDelay': row.get('eax2reverbdelay', '').strip(),
            'EAX2RoomRolloff': row.get('eax2roomrolloff', '').strip(),
            'EAX2AirAbsorption': row.get('eax2airabsorption', '').strip(),
            'EAX3RoomLF': row.get('eax3roomlf', '').strip(),
            'EAX3DecayLFRatio': row.get('eax3decaylfratio', '').strip(),
            'EAX3EchoTime': row.get('eax3echotime', '').strip(),
            'EAX3EchoDepth': row.get('eax3echodepth', '').strip(),
            'EAX3ModulationTime': row.get('eax3modulationtime', '').strip(),
            'EAX3ModulationDepth': row.get('eax3modulationdepth', '').strip(),
            'EAX3HFReference': row.get('eax3hfreference', '').strip(),
            'EAX3LFReference': row.get('eax3lfreference', '').strip()
        }
        
        output_entries.append(entry_data)
    
    return output_entries

def write_sound_provider_preferences(output_path, provider_entries, wdbx_format=False):
    """
    Write SoundProviderPreferences to CSV file.
    If wdbx_format is True, quote all fields and convert float decimals from . to ,
    Sorts entries by ID.
    """
    fieldnames = [
        'ID', 'Description', 'Flags', 'EAXEnvironmentSelection', 'EAXDecayTime',
        'EAX2EnvironmentSize', 'EAX2EnvironmentDiffusion', 'EAX2Room', 'EAX2RoomHF',
        'EAX2DecayHFRatio', 'EAX2Reflections', 'EAX2ReflectionsDelay', 'EAX2Reverb',
        'EAX2ReverbDelay', 'EAX2RoomRolloff', 'EAX2AirAbsorption', 'EAX3RoomLF',
        'EAX3DecayLFRatio', 'EAX3EchoTime', 'EAX3EchoDepth', 'EAX3ModulationTime',
        'EAX3ModulationDepth', 'EAX3HFReference', 'EAX3LFReference'
    ]
    
    if wdbx_format:
        # Convert float fields for WDBX format
        float_fields = [
            'EAXDecayTime', 'EAX2EnvironmentSize', 'EAX2EnvironmentDiffusion',
            'EAX2ReflectionsDelay', 'EAX2ReverbDelay', 'EAX2RoomRolloff',
            'EAX2AirAbsorption', 'EAX3DecayLFRatio', 'EAX3EchoTime', 'EAX3EchoDepth',
            'EAX3ModulationTime', 'EAX3ModulationDepth', 'EAX3HFReference',
            'EAX3LFReference', 'EAX2DecayHFRatio'
        ]
        for entry in provider_entries:
            for field in float_fields:
                if field in entry:
                    entry[field] = convert_float_to_wdbx(entry[field])
    
    # Sort by ID
    sorted_entries = sorted(provider_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def load_sound_filter_elem(sound_filter_elem_path):
    """
    Load SoundFilterElem table from input.
    Returns a list of dictionaries with normalized column names.
    """
    sound_filter_elem_data = []
    
    with open(sound_filter_elem_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            sound_filter_elem_data.append(row_normalized)
    
    return sound_filter_elem_data

def generate_sound_filter_elem_output(sound_filter_elem_data):
    """
    Generate SoundFilterElem output from input data.
    Adds OrderIndex field that increments for each occurrence of the same SoundFilterID.
    Returns a list of dictionaries for output.
    """
    output_entries = []
    order_index_tracker = {}  # Track OrderIndex per SoundFilterID
    
    for row in sound_filter_elem_data:
        sound_filter_id = row.get('soundfilterid', '').strip()
        
        # Get or initialize OrderIndex for this SoundFilterID
        if sound_filter_id not in order_index_tracker:
            order_index_tracker[sound_filter_id] = 0
        else:
            order_index_tracker[sound_filter_id] += 1
        
        entry_data = {
            'ID': row.get('id', '').strip(),
            'SoundFilterID': sound_filter_id,
            'OrderIndex': str(order_index_tracker[sound_filter_id]),
            'FilterType': row.get('filtertype', '').strip(),
            'Params_0': row.get('params_0', '').strip(),
            'Params_1': row.get('params_1', '').strip(),
            'Params_2': row.get('params_2', '').strip(),
            'Params_3': row.get('params_3', '').strip(),
            'Params_4': row.get('params_4', '').strip(),
            'Params_5': row.get('params_5', '').strip(),
            'Params_6': row.get('params_6', '').strip(),
            'Params_7': row.get('params_7', '').strip(),
            'Params_8': row.get('params_8', '').strip()
        }
        
        output_entries.append(entry_data)
    
    return output_entries

def write_sound_filter_elem(output_path, filter_elem_entries, wdbx_format=False):
    """
    Write SoundFilterElem to CSV file.
    If wdbx_format is True, quote all fields and convert float decimals from . to ,
    Sorts entries by ID.
    """
    fieldnames = ['ID', 'SoundFilterID', 'OrderIndex', 'FilterType', 
                  'Params_0', 'Params_1', 'Params_2', 'Params_3', 'Params_4',
                  'Params_5', 'Params_6', 'Params_7', 'Params_8']
    
    if wdbx_format:
        # Convert float fields for WDBX format
        float_fields = ['Params_0', 'Params_1', 'Params_2', 'Params_3', 'Params_4',
                       'Params_5', 'Params_6', 'Params_7', 'Params_8']
        for entry in filter_elem_entries:
            for field in float_fields:
                if field in entry:
                    entry[field] = convert_float_to_wdbx(entry[field])
    
    # Sort by ID
    sorted_entries = sorted(filter_elem_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def load_sound_filter(sound_filter_path):
    """
    Load SoundFilter table from input.
    Returns a list of dictionaries with normalized column names.
    """
    sound_filter_data = []
    
    with open(sound_filter_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            sound_filter_data.append(row_normalized)
    
    return sound_filter_data

def generate_sound_filter_output(sound_filter_data):
    """
    Generate SoundFilter output from input data.
    Direct 1:1 mapping.
    Returns a list of dictionaries for output.
    """
    output_entries = []
    
    for row in sound_filter_data:
        entry_data = {
            'ID': row.get('id', '').strip(),
            'Name': row.get('name', '').strip()
        }
        
        output_entries.append(entry_data)
    
    return output_entries

def write_sound_filter(output_path, filter_entries, wdbx_format=False):
    """
    Write SoundFilter to CSV file.
    If wdbx_format is True, quote all fields.
    Sorts entries by ID.
    """
    fieldnames = ['ID', 'Name']
    
    # Sort by ID
    sorted_entries = sorted(filter_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def load_sound_emitters(sound_emitters_path):
    """
    Load SoundEmitters table from input.
    Returns a list of dictionaries with normalized column names.
    """
    sound_emitters_data = []
    
    with open(sound_emitters_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            sound_emitters_data.append(row_normalized)
    
    return sound_emitters_data

def generate_sound_emitters_output(sound_emitters_data):
    """
    Generate SoundEmitters output from input data.
    Renames Position_X to PositionX, Direction_X to DirectionX.
    Returns a list of dictionaries for output.
    """
    output_entries = []
    
    for row in sound_emitters_data:
        entry_data = {
            'ID': row.get('id', '').strip(),
            'PositionX': row.get('position_0', '').strip(),
            'PositionY': row.get('position_1', '').strip(),
            'PositionZ': row.get('position_2', '').strip(),
            'DirectionX': row.get('direction_0', '').strip(),
            'DirectionY': row.get('direction_1', '').strip(),
            'DirectionZ': row.get('direction_2', '').strip(),
            'SoundEntriesID': row.get('soundentriesid', '').strip(),
            'MapID': row.get('mapid', '').strip(),
            'Name': row.get('name', '').strip()
        }
        
        output_entries.append(entry_data)
    
    return output_entries

def write_sound_emitters(output_path, emitter_entries, wdbx_format=False):
    """
    Write SoundEmitters to CSV file.
    If wdbx_format is True, quote all fields and convert float decimals from . to ,
    Sorts entries by ID.
    """
    fieldnames = ['ID', 'PositionX', 'PositionY', 'PositionZ', 'DirectionX', 'DirectionY', 'DirectionZ', 'SoundEntriesID', 'MapID', 'Name']
    
    if wdbx_format:
        # Convert float fields for WDBX format
        float_fields = ['PositionX', 'PositionY', 'PositionZ', 'DirectionX', 'DirectionY', 'DirectionZ']
        for entry in emitter_entries:
            for field in float_fields:
                if field in entry:
                    entry[field] = convert_float_to_wdbx(entry[field])
    
    # Sort by ID
    sorted_entries = sorted(emitter_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def load_sound_ambience(sound_ambience_path):
    """
    Load SoundAmbience table from input.
    Returns a list of dictionaries with normalized column names.
    """
    sound_ambience_data = []
    
    with open(sound_ambience_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            sound_ambience_data.append(row_normalized)
    
    return sound_ambience_data

def generate_sound_ambience_output(sound_ambience_data):
    """
    Generate SoundAmbience output from input data.
    Only keeps ID, AmbienceID_0, AmbienceID_1.
    Returns a list of dictionaries for output.
    """
    output_entries = []
    
    for row in sound_ambience_data:
        entry_data = {
            'ID': row.get('id', '').strip(),
            'AmbienceID_0': row.get('ambienceid_0', '').strip(),
            'AmbienceID_1': row.get('ambienceid_1', '').strip()
        }
        
        output_entries.append(entry_data)
    
    return output_entries

def write_sound_ambience(output_path, ambience_entries, wdbx_format=False):
    """
    Write SoundAmbience to CSV file.
    If wdbx_format is True, quote all fields.
    Sorts entries by ID.
    """
    fieldnames = ['ID', 'AmbienceID_0', 'AmbienceID_1']
    
    # Sort by ID
    sorted_entries = sorted(ambience_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def load_weapon_impact_sounds(weapon_impact_path):
    """
    Load WeaponImpactSounds table from input.
    Returns a list of dictionaries with normalized column names.
    """
    weapon_impact_data = []
    
    with open(weapon_impact_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            weapon_impact_data.append(row_normalized)
    
    return weapon_impact_data

def generate_weapon_impact_sounds_output(weapon_impact_data):
    """
    Generate WeaponImpactSounds output from input data.
    - Renames ImpactSoundID_X (0-9 to 1-10, drops _10)
    - Renames CritImpactSoundID_X (0-9 to 1-10, drops _10)
    - Ignores ImpactSource, PierceImpactSoundID_*, PierceCritImpactSoundID_*
    Returns a list of dictionaries for output.
    """
    output_entries = []
    
    for row in weapon_impact_data:
        entry_data = {
            'ID': row.get('id', '').strip(),
            'WeaponSubClassID': row.get('weaponsubclassid', '').strip(),
            'ParrySoundType': row.get('parrysoundtype', '').strip(),
            # Rename ImpactSoundID_0-9 to ImpactSoundID_1-10 (drop _10)
            'ImpactSoundID_1': row.get('impactsoundid_0', '').strip(),
            'ImpactSoundID_2': row.get('impactsoundid_1', '').strip(),
            'ImpactSoundID_3': row.get('impactsoundid_2', '').strip(),
            'ImpactSoundID_4': row.get('impactsoundid_3', '').strip(),
            'ImpactSoundID_5': row.get('impactsoundid_4', '').strip(),
            'ImpactSoundID_6': row.get('impactsoundid_5', '').strip(),
            'ImpactSoundID_7': row.get('impactsoundid_6', '').strip(),
            'ImpactSoundID_8': row.get('impactsoundid_7', '').strip(),
            'ImpactSoundID_9': row.get('impactsoundid_8', '').strip(),
            'ImpactSoundID_10': row.get('impactsoundid_9', '').strip(),
            # Rename CritImpactSoundID_0-9 to CritImpactSoundID_1-10 (drop _10)
            'CritImpactSoundID_1': row.get('critimpactsoundid_0', '').strip(),
            'CritImpactSoundID_2': row.get('critimpactsoundid_1', '').strip(),
            'CritImpactSoundID_3': row.get('critimpactsoundid_2', '').strip(),
            'CritImpactSoundID_4': row.get('critimpactsoundid_3', '').strip(),
            'CritImpactSoundID_5': row.get('critimpactsoundid_4', '').strip(),
            'CritImpactSoundID_6': row.get('critimpactsoundid_5', '').strip(),
            'CritImpactSoundID_7': row.get('critimpactsoundid_6', '').strip(),
            'CritImpactSoundID_8': row.get('critimpactsoundid_7', '').strip(),
            'CritImpactSoundID_9': row.get('critimpactsoundid_8', '').strip(),
            'CritImpactSoundID_10': row.get('critimpactsoundid_9', '').strip()
        }
        
        output_entries.append(entry_data)
    
    return output_entries

def write_weapon_impact_sounds(output_path, weapon_entries, wdbx_format=False):
    """
    Write WeaponImpactSounds to CSV file.
    If wdbx_format is True, quote all fields.
    Sorts entries by ID.
    """
    fieldnames = [
        'ID', 'WeaponSubClassID', 'ParrySoundType',
        'ImpactSoundID_1', 'ImpactSoundID_2', 'ImpactSoundID_3', 'ImpactSoundID_4', 'ImpactSoundID_5',
        'ImpactSoundID_6', 'ImpactSoundID_7', 'ImpactSoundID_8', 'ImpactSoundID_9', 'ImpactSoundID_10',
        'CritImpactSoundID_1', 'CritImpactSoundID_2', 'CritImpactSoundID_3', 'CritImpactSoundID_4', 'CritImpactSoundID_5',
        'CritImpactSoundID_6', 'CritImpactSoundID_7', 'CritImpactSoundID_8', 'CritImpactSoundID_9', 'CritImpactSoundID_10'
    ]
    
    # Sort by ID
    sorted_entries = sorted(weapon_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def load_footstep_terrain_lookup(footstep_path):
    """
    Load FootstepTerrainLookup table from input.
    Returns a list of dictionaries with normalized column names.
    """
    footstep_data = []
    
    with open(footstep_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            footstep_data.append(row_normalized)
    
    return footstep_data

def generate_footstep_terrain_lookup_output(footstep_data, filter_terrain=True):
    """
    Generate FootstepTerrainLookup output from input data.
    If filter_terrain is True, only include WotLK-compatible TerrainSoundIDs (0-10).
    Returns a list of dictionaries for output.
    """
    WOTLK_TERRAIN_IDS = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'}
    output_entries = []
    filtered_count = 0
    
    for row in footstep_data:
        terrain_sound_id = row.get('terrainsoundid', '').strip()
        
        # Filter terrain if requested
        if filter_terrain and terrain_sound_id not in WOTLK_TERRAIN_IDS:
            filtered_count += 1
            continue
        
        entry_data = {
            'ID': row.get('id', '').strip(),
            'CreatureFootstepID': row.get('creaturefootstepid', '').strip(),
            'TerrainSoundID': terrain_sound_id,
            'SoundID': row.get('soundid', '').strip(),
            'SoundIDSplash': row.get('soundidsplash', '').strip()
        }
        
        output_entries.append(entry_data)
    
    if filter_terrain and filtered_count > 0:
        print(f"  Filtered out {filtered_count} entries with non-WotLK terrain types")
    
    return output_entries

def write_footstep_terrain_lookup(output_path, footstep_entries, wdbx_format=False):
    """
    Write FootstepTerrainLookup to CSV file.
    If wdbx_format is True, quote all fields.
    Sorts entries by ID.
    """
    fieldnames = ['ID', 'CreatureFootstepID', 'TerrainSoundID', 'SoundID', 'SoundIDSplash']
    
    # Sort by ID
    sorted_entries = sorted(footstep_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def load_npc_sounds(npc_sounds_path):
    """
    Load NPCSounds table from input.
    Returns a list of dictionaries with normalized column names.
    """
    npc_sounds_data = []
    
    with open(npc_sounds_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            npc_sounds_data.append(row_normalized)
    
    return npc_sounds_data

def generate_npc_sounds_output(npc_sounds_data):
    """
    Generate NPCSounds output from input data.
    Renames SoundID_X (0-3 to 1-4).
    Returns a list of dictionaries for output.
    """
    output_entries = []
    
    for row in npc_sounds_data:
        entry_data = {
            'ID': row.get('id', '').strip(),
            # Rename SoundID_0-3 to SoundID_1-4
            'SoundID_1': row.get('soundid_0', '').strip(),
            'SoundID_2': row.get('soundid_1', '').strip(),
            'SoundID_3': row.get('soundid_2', '').strip(),
            'SoundID_4': row.get('soundid_3', '').strip()
        }
        
        output_entries.append(entry_data)
    
    return output_entries

def write_npc_sounds(output_path, npc_entries, wdbx_format=False):
    """
    Write NPCSounds to CSV file.
    If wdbx_format is True, quote all fields.
    Sorts entries by ID.
    """
    fieldnames = ['ID', 'SoundID_1', 'SoundID_2', 'SoundID_3', 'SoundID_4']
    
    # Sort by ID
    sorted_entries = sorted(npc_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def load_creature_sound_data(creature_sound_path):
    """
    Load CreatureSoundData table from input.
    Returns a list of dictionaries with normalized column names.
    """
    creature_sound_data = []
    
    with open(creature_sound_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            creature_sound_data.append(row_normalized)
    
    return creature_sound_data

def generate_creature_sound_data_output(creature_sound_data):
    """
    Generate CreatureSoundData output from input data.
    Renames SoundFidget_X (0-4 to 1-5) and CustomAttack_X (0-3 to 1-4).
    Returns a list of dictionaries for output.
    """
    output_entries = []
    
    for row in creature_sound_data:
        entry_data = {
            'ID': row.get('id', '').strip(),
            'SoundExertionID': row.get('soundexertionid', '').strip(),
            'SoundExertionCriticalID': row.get('soundexertioncriticalid', '').strip(),
            'SoundInjuryID': row.get('soundinjuryid', '').strip(),
            'SoundInjuryCriticalID': row.get('soundinjurycriticalid', '').strip(),
            'SoundInjuryCrushingBlowID': row.get('soundinjurycrushingblowid', '').strip(),
            'SoundDeathID': row.get('sounddeathid', '').strip(),
            'SoundStunID': row.get('soundstunid', '').strip(),
            'SoundStandID': row.get('soundstandid', '').strip(),
            'SoundFootstepID': row.get('soundfootstepid', '').strip(),
            'SoundAggroID': row.get('soundaggroid', '').strip(),
            'SoundWingFlapID': row.get('soundwingflapid', '').strip(),
            'SoundWingGlideID': row.get('soundwingglideid', '').strip(),
            'SoundAlertID': row.get('soundalertid', '').strip(),
            # Rename SoundFidget_0-4 to SoundFidget_1-5
            'SoundFidget_1': row.get('soundfidget_0', '').strip(),
            'SoundFidget_2': row.get('soundfidget_1', '').strip(),
            'SoundFidget_3': row.get('soundfidget_2', '').strip(),
            'SoundFidget_4': row.get('soundfidget_3', '').strip(),
            'SoundFidget_5': row.get('soundfidget_4', '').strip(),
            # Rename CustomAttack_0-3 to CustomAttack_1-4
            'CustomAttack_1': row.get('customattack_0', '').strip(),
            'CustomAttack_2': row.get('customattack_1', '').strip(),
            'CustomAttack_3': row.get('customattack_2', '').strip(),
            'CustomAttack_4': row.get('customattack_3', '').strip(),
            'NPCSoundID': row.get('npcsoundid', '').strip(),
            'LoopSoundID': row.get('loopsoundid', '').strip(),
            'CreatureImpactType': row.get('creatureimpacttype', '').strip(),
            'SoundJumpStartID': row.get('soundjumpstartid', '').strip(),
            'SoundJumpEndID': row.get('soundjumpendid', '').strip(),
            'SoundPetAttackID': row.get('soundpetattackid', '').strip(),
            'SoundPetOrderID': row.get('soundpetorderid', '').strip(),
            'SoundPetDismissID': row.get('soundpetdismissid', '').strip(),
            'FidgetDelaySecondsMin': row.get('fidgetdelaysecondsmin', '').strip(),
            'FidgetDelaySecondsMax': row.get('fidgetdelaysecondsmax', '').strip(),
            'BirthSoundID': row.get('birthsoundid', '').strip(),
            'SpellCastDirectedSoundID': row.get('spellcastdirectedsoundid', '').strip(),
            'SubmergeSoundID': row.get('submergesoundid', '').strip(),
            'SubmergedSoundID': row.get('submergedsoundid', '').strip(),
            'CreatureSoundDataIDPet': row.get('creaturesounddataidpet', '').strip()
        }
        
        output_entries.append(entry_data)
    
    return output_entries

def write_creature_sound_data(output_path, creature_entries, wdbx_format=False):
    """
    Write CreatureSoundData to CSV file.
    If wdbx_format is True, quote all fields and convert float decimals from . to ,
    Sorts entries by ID.
    """
    fieldnames = [
        'ID', 'SoundExertionID', 'SoundExertionCriticalID', 'SoundInjuryID',
        'SoundInjuryCriticalID', 'SoundInjuryCrushingBlowID', 'SoundDeathID',
        'SoundStunID', 'SoundStandID', 'SoundFootstepID', 'SoundAggroID',
        'SoundWingFlapID', 'SoundWingGlideID', 'SoundAlertID',
        'SoundFidget_1', 'SoundFidget_2', 'SoundFidget_3', 'SoundFidget_4', 'SoundFidget_5',
        'CustomAttack_1', 'CustomAttack_2', 'CustomAttack_3', 'CustomAttack_4',
        'NPCSoundID', 'LoopSoundID', 'CreatureImpactType',
        'SoundJumpStartID', 'SoundJumpEndID', 'SoundPetAttackID', 'SoundPetOrderID',
        'SoundPetDismissID', 'FidgetDelaySecondsMin', 'FidgetDelaySecondsMax',
        'BirthSoundID', 'SpellCastDirectedSoundID', 'SubmergeSoundID',
        'SubmergedSoundID', 'CreatureSoundDataIDPet'
    ]
    
    if wdbx_format:
        # Convert float fields for WDBX format
        float_fields = ['FidgetDelaySecondsMin', 'FidgetDelaySecondsMax']
        for entry in creature_entries:
            for field in float_fields:
                if field in entry:
                    entry[field] = convert_float_to_wdbx(entry[field])
    
    # Sort by ID
    sorted_entries = sorted(creature_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def load_soundkit_advanced(soundkit_advanced_path):
    """
    Load SoundKitAdvanced table data.
    Returns a list of dictionaries with normalized column names.
    """
    soundkit_advanced_data = []
    
    with open(soundkit_advanced_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            soundkit_advanced_data.append(row_normalized)
    
    return soundkit_advanced_data

def generate_sound_entries_advanced(soundkit_advanced_data, sound_entries):
    """
    Generate SoundEntriesAdvanced data from SoundKitAdvanced.
    Enriches with Name from SoundEntries.
    Returns a list of dictionaries representing each SoundEntriesAdvanced row.
    """
    # Create a lookup dictionary for SoundEntries names
    sound_entries_names = {entry['ID']: entry.get('Name', '') for entry in sound_entries}
    
    advanced_entries = []
    
    for row in soundkit_advanced_data:
        entry_data = {
            'ID': row.get('id', '').strip(),
            'SoundEntryID': row.get('soundkitid', '').strip(),
            'InnerRadius2D': row.get('innerradius2d', '').strip(),
            'TimeA': row.get('timea', '').strip(),
            'TimeB': row.get('timeb', '').strip(),
            'TimeC': row.get('timec', '').strip(),
            'TimeD': row.get('timed', '').strip(),
            'RandomOffsetRange': row.get('randomoffsetrange', '').strip(),
            'Usage': row.get('usage', '').strip(),
            'TimeIntervalMin': row.get('timeintervalmin', '').strip(),
            'TimeIntervalMax': row.get('timeintervalmax', '').strip(),
            'VolumeSliderCategory': row.get('volumeslidercategory', '').strip(),
            'DuckToSFX': row.get('ducktosfx', '').strip(),
            'DuckToMusic': row.get('ducktomusic', '').strip(),
            'DuckToAmbience': row.get('ducktoambience', '').strip(),
            'InnerRadiusOfInfluence': row.get('innerradiusofinfluence', '').strip(),
            'OuterRadiusOfInfluence': row.get('outerradiusofinfluence', '').strip(),
            'TimeToDuck': row.get('timetoduck', '').strip(),
            'TimeToUnduck': row.get('timetounduck', '').strip(),
            'InsideAngle': row.get('insideangle', '').strip(),
            'OutsideAngle': row.get('outsideangle', '').strip(),
            'OutsideVolume': row.get('outsidevolume', '').strip(),
            'OuterRadius2D': row.get('outerradius2d', '').strip(),
            'Name': ''
        }
        
        # Get Name from SoundEntries based on SoundEntryID
        sound_entry_id = entry_data['SoundEntryID']
        if sound_entry_id in sound_entries_names:
            entry_data['Name'] = sound_entries_names[sound_entry_id]
        
        advanced_entries.append(entry_data)
    
    return advanced_entries

def write_sound_entries_advanced(output_path, advanced_entries, wdbx_format=False):
    """
    Write SoundEntriesAdvanced data to CSV file.
    If wdbx_format is True, quote all fields and convert float decimals from . to ,
    Sorts entries by ID.
    """
    fieldnames = [
        'ID', 'SoundEntryID', 'InnerRadius2D', 'TimeA', 'TimeB', 'TimeC', 'TimeD',
        'RandomOffsetRange', 'Usage', 'TimeIntervalMin', 'TimeIntervalMax',
        'VolumeSliderCategory', 'DuckToSFX', 'DuckToMusic', 'DuckToAmbience',
        'InnerRadiusOfInfluence', 'OuterRadiusOfInfluence', 'TimeToDuck', 'TimeToUnduck',
        'InsideAngle', 'OutsideAngle', 'OutsideVolume', 'OuterRadius2D', 'Name'
    ]
    
    if wdbx_format:
        # Convert float fields for WDBX format
        float_fields = [
            'InnerRadius2D', 'DuckToSFX', 'DuckToMusic', 'DuckToAmbience',
            'InnerRadiusOfInfluence', 'OuterRadiusOfInfluence', 'InsideAngle',
            'OutsideAngle', 'OutsideVolume', 'OuterRadius2D'
        ]
        for entry in advanced_entries:
            for field in float_fields:
                if field in entry:
                    entry[field] = convert_float_to_wdbx(entry[field])
    
    # Sort by ID
    sorted_entries = sorted(advanced_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def load_soundkit_table(soundkit_path):
    """
    Load SoundKit table data.
    Returns a dictionary: {SoundKitID: row_data}
    """
    soundkit_table = {}
    
    with open(soundkit_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            soundkit_id = row_normalized['id'].strip()
            soundkit_table[soundkit_id] = row_normalized
    
    return soundkit_table

def generate_sound_entries(soundkit_data, audio_files, soundkit_table):
    """
    Generate SoundEntries data from SoundKitEntry grouped data.
    Enriches with data from SoundKit table.
    Returns a tuple: (sound_entries, missing_soundkit_ids)
    """
    sound_entries = []
    missing_soundkit_ids = []
    
    for soundkit_id, entries in soundkit_data.items():
        entry_data = {
            'ID': soundkit_id,
            'SoundType': '',
            'Name': '',
            'File_1': '', 'File_2': '', 'File_3': '', 'File_4': '', 'File_5': '',
            'File_6': '', 'File_7': '', 'File_8': '', 'File_9': '', 'File_10': '',
            'Freq_1': '', 'Freq_2': '', 'Freq_3': '', 'Freq_4': '', 'Freq_5': '',
            'Freq_6': '', 'Freq_7': '', 'Freq_8': '', 'Freq_9': '', 'Freq_10': '',
            'DirectoryBase': '',
            'VolumeFloat': '',
            'Flags': '',
            'MinDistance': '',
            'DistanceCutoff': '',
            'EAXDef': '',
            'SoundEntriesAdvancedID': ''
        }
        
        # First, collect ALL volumes from ALL entries for this SoundKitID (not just first 10)
        volumes = []
        for entry in entries:  # All entries, not limited to 10
            volume = entry.get('volume', '').strip()
            if volume:
                try:
                    vol_float = float(volume)
                    volumes.append(vol_float)
                except (ValueError, TypeError):
                    volumes.append(0.0)
            else:
                volumes.append(0.0)
        
        # Now collect file paths and frequencies (up to 10)
        file_paths = []
        frequencies = []
        is_mapped = []  # Track if FileDataID was successfully mapped
        
        for i, entry in enumerate(entries[:10]):  # Limit to 10 entries
            file_data_id = entry['filedataid'].strip()
            frequency = entry['frequency'].strip()
            
            # Get file path from audio_files dictionary
            if file_data_id in audio_files:
                file_paths.append(audio_files[file_data_id])
                frequencies.append(frequency)
                is_mapped.append(True)
            else:
                # FileDataID not found in listfile - keep the ID number for manual correction
                file_paths.append(file_data_id)
                frequencies.append('0')  # Set frequency to 0 for unmapped files
                is_mapped.append(False)
        
        # Find common directory
        directory_base = find_common_directory(file_paths)
        entry_data['DirectoryBase'] = directory_base
        
        # Remove common directory from file paths and populate File_X columns
        for i in range(1, 11):
            if i <= len(file_paths) and file_paths[i-1]:
                path = file_paths[i-1]
                if directory_base and path.startswith(directory_base + '\\'):
                    # Remove directory base from path
                    relative_path = path[len(directory_base) + 1:]
                    entry_data[f'File_{i}'] = relative_path
                else:
                    entry_data[f'File_{i}'] = path
            else:
                entry_data[f'File_{i}'] = ''
        
        # Populate Freq_X columns - always has a value (frequency or 0)
        for i in range(1, 11):
            file_value = entry_data.get(f'File_{i}', '')
            if file_value:
                # Check if this file was mapped
                if i-1 < len(is_mapped) and not is_mapped[i-1]:
                    # Unmapped FileDataID - force frequency to 0
                    entry_data[f'Freq_{i}'] = '0'
                elif i-1 < len(frequencies) and frequencies[i-1]:
                    # Mapped file - use actual frequency
                    entry_data[f'Freq_{i}'] = frequencies[i-1]
                else:
                    # Mapped file but no frequency - default to 1
                    entry_data[f'Freq_{i}'] = '1'
            else:
                # File is empty, set freq to 0
                entry_data[f'Freq_{i}'] = '0'
        
        # Set VolumeFloat to the highest volume from SoundKitEntry
        if volumes:
            entry_data['VolumeFloat'] = str(max(volumes))
        
        # Enrich with SoundKit table data (Step 3)
        has_soundkit = False
        if soundkit_id in soundkit_table:
            kit_data = soundkit_table[soundkit_id]
            has_soundkit = True
            
            # SoundType
            entry_data['SoundType'] = kit_data.get('soundtype', '').strip()
            
            # VolumeFloat - replace if new value > 0
            kit_volume = kit_data.get('volumefloat', '').strip()
            if kit_volume:
                try:
                    kit_vol_float = float(kit_volume)
                    if kit_vol_float > 0:
                        entry_data['VolumeFloat'] = kit_volume
                except (ValueError, TypeError):
                    pass
            
            # Flags
            entry_data['Flags'] = kit_data.get('flags', '').strip()
            
            # MinDistance
            entry_data['MinDistance'] = kit_data.get('mindistance', '').strip()
            
            # DistanceCutoff
            entry_data['DistanceCutoff'] = kit_data.get('distancecutoff', '').strip()
            
            # EAXDef
            entry_data['EAXDef'] = kit_data.get('eaxdef', '').strip()
            
            # SoundEntriesAdvancedID (from SoundKitAdvancedID)
            entry_data['SoundEntriesAdvancedID'] = kit_data.get('soundkitadvancedid', '').strip()
        
        # Check if SoundKit fields are empty and apply defaults
        if not entry_data['SoundType']:
            entry_data['SoundType'] = '18'  # Test/Temporary
            has_soundkit = False
        if not entry_data['Flags']:
            entry_data['Flags'] = '0'
            has_soundkit = False
        if not entry_data['MinDistance']:
            entry_data['MinDistance'] = '0'
            has_soundkit = False
        if not entry_data['DistanceCutoff']:
            entry_data['DistanceCutoff'] = '0'
            has_soundkit = False
        if not entry_data['EAXDef']:
            entry_data['EAXDef'] = '0'
            has_soundkit = False
        if not entry_data['SoundEntriesAdvancedID']:
            entry_data['SoundEntriesAdvancedID'] = '0'
            has_soundkit = False
        
        # Log if missing SoundKit data
        if not has_soundkit:
            missing_soundkit_ids.append(soundkit_id)
        
        sound_entries.append(entry_data)
    
    return sound_entries, missing_soundkit_ids

def convert_float_to_wdbx(value):
    """
    Convert float value for WDBX format.
    - Replace . with ,
    - Remove trailing .0 (1.0 becomes 1, 1.1 becomes 1,1)
    """
    if not value:
        return value
    
    value_str = str(value).strip()
    
    # Check if it's a number
    try:
        float_val = float(value_str)
        # Remove .0 if it's a whole number
        if float_val == int(float_val):
            return str(int(float_val))
        else:
            # Replace . with ,
            return value_str.replace('.', ',')
    except (ValueError, TypeError):
        return value_str

def write_sound_entries(output_path, sound_entries, wdbx_format=False):
    """
    Write SoundEntries data to CSV file.
    If wdbx_format is True, quote all fields and convert float decimals from . to ,
    Sorts entries by ID.
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    fieldnames = [
        'ID', 'SoundType', 'Name',
        'File_1', 'File_2', 'File_3', 'File_4', 'File_5',
        'File_6', 'File_7', 'File_8', 'File_9', 'File_10',
        'Freq_1', 'Freq_2', 'Freq_3', 'Freq_4', 'Freq_5',
        'Freq_6', 'Freq_7', 'Freq_8', 'Freq_9', 'Freq_10',
        'DirectoryBase', 'VolumeFloat', 'Flags', 'MinDistance',
        'DistanceCutoff', 'EAXDef', 'SoundEntriesAdvancedID'
    ]
    
    if wdbx_format:
        # Convert float fields for WDBX format
        float_fields = ['VolumeFloat', 'MinDistance', 'DistanceCutoff']
        for entry in sound_entries:
            for field in float_fields:
                if field in entry:
                    entry[field] = convert_float_to_wdbx(entry[field])
    
    # Sort by ID
    sorted_entries = sorted(sound_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

# Main execution
if __name__ == "__main__":
    print("=" * 60)
    print("=== DBC AUDIO PROCESSOR ===")
    print("=" * 60)
    
    # Ask user preferences upfront
    print("\n=== USER PREFERENCES ===")
    
    # Ask for WotLK names
    while True:
        use_wotlk_input = input("Use WoW 3.3.5a (WotLK) SoundEntries names? (y/n): ").strip().lower()
        if use_wotlk_input in ['y', 'yes']:
            use_wotlk = True
            break
        elif use_wotlk_input in ['n', 'no']:
            use_wotlk = False
            break
        else:
            print("Please enter 'y' or 'n'")
    
    # Ask for WDBX format
    while True:
        wdbx_input = input("Format CSV for WDBX Editor? (quotes all fields, converts decimals . to ,) (y/n): ").strip().lower()
        if wdbx_input in ['y', 'yes']:
            wdbx_format = True
            break
        elif wdbx_input in ['n', 'no']:
            wdbx_format = False
            break
        else:
            print("Please enter 'y' or 'n'")
    
    # Ask for terrain filtering
    while True:
        filter_input = input("Filter FootstepTerrainLookup to WotLK-compatible terrain types only? (recommended) (y/n): ").strip().lower()
        if filter_input in ['y', 'yes', '']:  # Default to yes if empty
            filter_terrain = True
            break
        elif filter_input in ['n', 'no']:
            filter_terrain = False
            break
        else:
            print("Please enter 'y' or 'n' (press Enter for default 'y')")
    
    print("\n" + "=" * 60)
    print("=== PROCESSING ===")
    print("=" * 60)
    
    print("\n=== Step 1: Loading audio files from listfile ===")
    listfile_path = find_listfile(INPUT_DIR)
    
    if not listfile_path:
        print(f"ERROR: No listfile found in {INPUT_DIR}")
        exit(1)
    
    print(f"Found listfile: {listfile_path}")
    audio_files = load_audio_files(listfile_path)
    print(f"Loaded {len(audio_files)} audio files (.wav, .mp3, .ogg)")
    
    # Load model files (.m2 → .mdx)
    model_files = load_model_files(listfile_path)
    print(f"Loaded {len(model_files)} model files (.m2 → .mdx)")
    
    # Load texture files (.blp → filename only)
    texture_files = load_texture_files(listfile_path)
    print(f"Loaded {len(texture_files)} texture files (.blp → filename)")
    
    print("\n=== Step 2: Loading SoundKit table ===")
    soundkit_table_path = find_table_file(INPUT_DIR, "SoundKit")
    
    if not soundkit_table_path:
        print(f"WARNING: SoundKit table not found in {INPUT_DIR}")
        soundkit_table = {}
    else:
        print(f"Found SoundKit: {soundkit_table_path}")
        soundkit_table = load_soundkit_table(soundkit_table_path)
        print(f"Loaded {len(soundkit_table)} SoundKit entries")
    
    print("\n=== Step 3: Loading SoundKitEntry and generating SoundEntries.csv ===")
    soundkit_entry_path = find_table_file(INPUT_DIR, "SoundKitEntry")
    
    if not soundkit_entry_path:
        print(f"ERROR: SoundKitEntry table not found in {INPUT_DIR}")
        exit(1)
    
    print(f"Found SoundKitEntry: {soundkit_entry_path}")
    soundkit_data = load_soundkit_entries(soundkit_entry_path)
    print(f"Loaded {len(soundkit_data)} unique SoundKitIDs")
    
    sound_entries, missing_soundkit_ids = generate_sound_entries(soundkit_data, audio_files, soundkit_table)
    print(f"Generated {len(sound_entries)} SoundEntries")
    
    # Log missing SoundKit data
    if missing_soundkit_ids:
        soundkit_log_path = "SoundEntries_SoundKit.log"
        write_soundkit_missing_log(soundkit_log_path, missing_soundkit_ids)
        print(f"WARNING: Found {len(missing_soundkit_ids)} entries with missing SoundKit data")
        print(f"Log written to: {soundkit_log_path}")
    
    print("\n=== Step 4: Applying names to SoundEntries ===")
    apply_names(sound_entries, use_wotlk)
    
    print("\n=== Checking for unmapped FileDataIDs ===")
    issues = check_missing_audio_files(sound_entries)
    
    if issues:
        log_path = "SoundEntries.log"  # Place in script directory
        write_log(log_path, issues)
        print(f"WARNING: Found {len(issues)} entries with unmapped FileDataIDs or missing extensions")
        print(f"Log written to: {log_path}")
    else:
        print("All FileDataIDs successfully mapped!")
    
    print(f"\n=== Writing SoundEntries.csv ===")
    output_path = os.path.join(OUTPUT_DIR, "SoundEntries.csv")
    write_sound_entries(output_path, sound_entries, wdbx_format)
    
    if wdbx_format:
        print(f"Wrote SoundEntries to: {output_path} (WDBX format)")
    else:
        print(f"Wrote SoundEntries to: {output_path}")
    
    print("\n=== Sample SoundEntries (first 3) ===")
    for entry in sound_entries[:3]:
        print(f"ID: {entry['ID']}")
        for key, value in entry.items():
            if value and key != 'ID':  # Show all non-empty fields except ID (already shown)
                print(f"  {key}: {value}")
        print()
    
    print("\n" + "=" * 60)
    print("=== GENERATING SOUNDENTRIESADVANCED ===")
    print("=" * 60)
    
    print("\n=== Loading SoundKitAdvanced ===")
    soundkit_advanced_path = find_table_file(INPUT_DIR, "SoundKitAdvanced")
    
    if not soundkit_advanced_path:
        print(f"WARNING: SoundKitAdvanced table not found in {INPUT_DIR}")
        print("Skipping SoundEntriesAdvanced generation")
    else:
        print(f"Found SoundKitAdvanced: {soundkit_advanced_path}")
        soundkit_advanced_data = load_soundkit_advanced(soundkit_advanced_path)
        print(f"Loaded {len(soundkit_advanced_data)} SoundKitAdvanced entries")
        
        print("\n=== Generating SoundEntriesAdvanced ===")
        advanced_entries = generate_sound_entries_advanced(soundkit_advanced_data, sound_entries)
        print(f"Generated {len(advanced_entries)} SoundEntriesAdvanced entries")
        
        print("\n=== Writing SoundEntriesAdvanced.csv ===")
        advanced_output_path = os.path.join(OUTPUT_DIR, "SoundEntriesAdvanced.csv")
        write_sound_entries_advanced(advanced_output_path, advanced_entries, wdbx_format)
        
        if wdbx_format:
            print(f"Wrote SoundEntriesAdvanced to: {advanced_output_path} (WDBX format)")
        else:
            print(f"Wrote SoundEntriesAdvanced to: {advanced_output_path}")
        
        print("\n=== Sample SoundEntriesAdvanced (first 3) ===")
        for entry in advanced_entries[:3]:
            print(f"ID: {entry['ID']}")
            for key, value in entry.items():
                if value and key != 'ID':
                    print(f"  {key}: {value}")
            print()
    
    print("\n" + "=" * 60)
    print("=== GENERATING CREATURESOUNDDATA ===")
    print("=" * 60)
    
    print("\n=== Loading CreatureSoundData ===")
    creature_sound_path = find_table_file(INPUT_DIR, "CreatureSoundData")
    
    if not creature_sound_path:
        print(f"WARNING: CreatureSoundData table not found in {INPUT_DIR}")
        print("Skipping CreatureSoundData generation")
    else:
        print(f"Found CreatureSoundData: {creature_sound_path}")
        creature_sound_data = load_creature_sound_data(creature_sound_path)
        print(f"Loaded {len(creature_sound_data)} CreatureSoundData entries")
        
        print("\n=== Generating CreatureSoundData output ===")
        creature_entries = generate_creature_sound_data_output(creature_sound_data)
        print(f"Generated {len(creature_entries)} CreatureSoundData entries")
        
        print("\n=== Writing CreatureSoundData.csv ===")
        creature_output_path = os.path.join(OUTPUT_DIR, "CreatureSoundData.csv")
        write_creature_sound_data(creature_output_path, creature_entries, wdbx_format)
        
        if wdbx_format:
            print(f"Wrote CreatureSoundData to: {creature_output_path} (WDBX format)")
        else:
            print(f"Wrote CreatureSoundData to: {creature_output_path}")
        
        print("\n=== Sample CreatureSoundData (first 3) ===")
        for entry in creature_entries[:3]:
            print(f"ID: {entry['ID']}")
            for key, value in entry.items():
                if value and key != 'ID':
                    print(f"  {key}: {value}")
            print()
    
    print("\n" + "=" * 60)
    print("=== GENERATING NPCSOUNDS ===")
    print("=" * 60)
    
    print("\n=== Loading NPCSounds ===")
    npc_sounds_path = find_table_file(INPUT_DIR, "NPCSounds")
    
    if not npc_sounds_path:
        print(f"WARNING: NPCSounds table not found in {INPUT_DIR}")
        print("Skipping NPCSounds generation")
    else:
        print(f"Found NPCSounds: {npc_sounds_path}")
        npc_sounds_data = load_npc_sounds(npc_sounds_path)
        print(f"Loaded {len(npc_sounds_data)} NPCSounds entries")
        
        print("\n=== Generating NPCSounds output ===")
        npc_entries = generate_npc_sounds_output(npc_sounds_data)
        print(f"Generated {len(npc_entries)} NPCSounds entries")
        
        print("\n=== Writing NPCSounds.csv ===")
        npc_output_path = os.path.join(OUTPUT_DIR, "NPCSounds.csv")
        write_npc_sounds(npc_output_path, npc_entries, wdbx_format)
        
        if wdbx_format:
            print(f"Wrote NPCSounds to: {npc_output_path} (WDBX format)")
        else:
            print(f"Wrote NPCSounds to: {npc_output_path}")
        
        print("\n=== Sample NPCSounds (first 3) ===")
        for entry in npc_entries[:3]:
            print(f"ID: {entry['ID']}")
            for key, value in entry.items():
                if value and key != 'ID':
                    print(f"  {key}: {value}")
            print()
    
    print("\n" + "=" * 60)
    print("=== GENERATING FOOTSTEPTERRAINLOOKUP ===")
    print("=" * 60)
    
    print("\n=== Loading FootstepTerrainLookup ===")
    footstep_path = find_table_file(INPUT_DIR, "FootstepTerrainLookup")
    
    if not footstep_path:
        print(f"WARNING: FootstepTerrainLookup table not found in {INPUT_DIR}")
        print("Skipping FootstepTerrainLookup generation")
    else:
        print(f"Found FootstepTerrainLookup: {footstep_path}")
        footstep_data = load_footstep_terrain_lookup(footstep_path)
        print(f"Loaded {len(footstep_data)} FootstepTerrainLookup entries")
        
        print("\n=== Generating FootstepTerrainLookup output ===")
        footstep_entries = generate_footstep_terrain_lookup_output(footstep_data, filter_terrain)
        print(f"Generated {len(footstep_entries)} FootstepTerrainLookup entries")
        
        print("\n=== Writing FootstepTerrainLookup.csv ===")
        footstep_output_path = os.path.join(OUTPUT_DIR, "FootstepTerrainLookup.csv")
        write_footstep_terrain_lookup(footstep_output_path, footstep_entries, wdbx_format)
        
        if wdbx_format:
            print(f"Wrote FootstepTerrainLookup to: {footstep_output_path} (WDBX format)")
        else:
            print(f"Wrote FootstepTerrainLookup to: {footstep_output_path}")
        
        print("\n=== Sample FootstepTerrainLookup (first 3) ===")
        for entry in footstep_entries[:3]:
            print(f"ID: {entry['ID']}")
            for key, value in entry.items():
                if value and key != 'ID':
                    print(f"  {key}: {value}")
            print()
    
    print("\n" + "=" * 60)
    print("=== GENERATING WEAPONIMPACTSOUNDS ===")
    print("=" * 60)
    
    print("\n=== Loading WeaponImpactSounds ===")
    weapon_impact_path = find_table_file(INPUT_DIR, "WeaponImpactSounds")
    
    if not weapon_impact_path:
        print(f"WARNING: WeaponImpactSounds table not found in {INPUT_DIR}")
        print("Skipping WeaponImpactSounds generation")
    else:
        print(f"Found WeaponImpactSounds: {weapon_impact_path}")
        weapon_impact_data = load_weapon_impact_sounds(weapon_impact_path)
        print(f"Loaded {len(weapon_impact_data)} WeaponImpactSounds entries")
        
        print("\n=== Generating WeaponImpactSounds output ===")
        weapon_entries = generate_weapon_impact_sounds_output(weapon_impact_data)
        print(f"Generated {len(weapon_entries)} WeaponImpactSounds entries")
        
        print("\n=== Writing WeaponImpactSounds.csv ===")
        weapon_output_path = os.path.join(OUTPUT_DIR, "WeaponImpactSounds.csv")
        write_weapon_impact_sounds(weapon_output_path, weapon_entries, wdbx_format)
        
        if wdbx_format:
            print(f"Wrote WeaponImpactSounds to: {weapon_output_path} (WDBX format)")
        else:
            print(f"Wrote WeaponImpactSounds to: {weapon_output_path}")
        
        print("\n=== Sample WeaponImpactSounds (first 3) ===")
        for entry in weapon_entries[:3]:
            print(f"ID: {entry['ID']}")
            for key, value in entry.items():
                if value and key != 'ID':
                    print(f"  {key}: {value}")
            print()
    
    print("\n" + "=" * 60)
    print("=== GENERATING SOUNDAMBIENCE ===")
    print("=" * 60)
    
    print("\n=== Loading SoundAmbience ===")
    sound_ambience_path = find_table_file(INPUT_DIR, "SoundAmbience")
    
    if not sound_ambience_path:
        print(f"WARNING: SoundAmbience table not found in {INPUT_DIR}")
        print("Skipping SoundAmbience generation")
    else:
        print(f"Found SoundAmbience: {sound_ambience_path}")
        sound_ambience_data = load_sound_ambience(sound_ambience_path)
        print(f"Loaded {len(sound_ambience_data)} SoundAmbience entries")
        
        print("\n=== Generating SoundAmbience output ===")
        ambience_entries = generate_sound_ambience_output(sound_ambience_data)
        print(f"Generated {len(ambience_entries)} SoundAmbience entries")
        
        print("\n=== Writing SoundAmbience.csv ===")
        ambience_output_path = os.path.join(OUTPUT_DIR, "SoundAmbience.csv")
        write_sound_ambience(ambience_output_path, ambience_entries, wdbx_format)
        
        if wdbx_format:
            print(f"Wrote SoundAmbience to: {ambience_output_path} (WDBX format)")
        else:
            print(f"Wrote SoundAmbience to: {ambience_output_path}")
        
        print("\n=== Sample SoundAmbience (first 3) ===")
        for entry in ambience_entries[:3]:
            print(f"ID: {entry['ID']}")
            for key, value in entry.items():
                if value and key != 'ID':
                    print(f"  {key}: {value}")
            print()
    
    print("\n" + "=" * 60)
    print("=== GENERATING SOUNDEMITTERS ===")
    print("=" * 60)
    
    print("\n=== Loading SoundEmitters ===")
    sound_emitters_path = find_table_file(INPUT_DIR, "SoundEmitters")
    
    if not sound_emitters_path:
        print(f"WARNING: SoundEmitters table not found in {INPUT_DIR}")
        print("Skipping SoundEmitters generation")
    else:
        print(f"Found SoundEmitters: {sound_emitters_path}")
        sound_emitters_data = load_sound_emitters(sound_emitters_path)
        print(f"Loaded {len(sound_emitters_data)} SoundEmitters entries")
        
        print("\n=== Generating SoundEmitters output ===")
        emitter_entries = generate_sound_emitters_output(sound_emitters_data)
        print(f"Generated {len(emitter_entries)} SoundEmitters entries")
        
        print("\n=== Writing SoundEmitters.csv ===")
        emitters_output_path = os.path.join(OUTPUT_DIR, "SoundEmitters.csv")
        write_sound_emitters(emitters_output_path, emitter_entries, wdbx_format)
        
        if wdbx_format:
            print(f"Wrote SoundEmitters to: {emitters_output_path} (WDBX format)")
        else:
            print(f"Wrote SoundEmitters to: {emitters_output_path}")
        
        print("\n=== Sample SoundEmitters (first 3) ===")
        for entry in emitter_entries[:3]:
            print(f"ID: {entry['ID']}")
            for key, value in entry.items():
                if value and key != 'ID':
                    print(f"  {key}: {value}")
            print()
    
    print("\n" + "=" * 60)
    print("=== GENERATING SOUNDFILTER ===")
    print("=" * 60)
    
    print("\n=== Loading SoundFilter ===")
    sound_filter_path = find_table_file(INPUT_DIR, "SoundFilter")
    
    if not sound_filter_path:
        print(f"WARNING: SoundFilter table not found in {INPUT_DIR}")
        print("Skipping SoundFilter generation")
    else:
        print(f"Found SoundFilter: {sound_filter_path}")
        sound_filter_data = load_sound_filter(sound_filter_path)
        print(f"Loaded {len(sound_filter_data)} SoundFilter entries")
        
        print("\n=== Generating SoundFilter output ===")
        filter_entries = generate_sound_filter_output(sound_filter_data)
        print(f"Generated {len(filter_entries)} SoundFilter entries")
        
        print("\n=== Writing SoundFilter.csv ===")
        filter_output_path = os.path.join(OUTPUT_DIR, "SoundFilter.csv")
        write_sound_filter(filter_output_path, filter_entries, wdbx_format)
        
        if wdbx_format:
            print(f"Wrote SoundFilter to: {filter_output_path} (WDBX format)")
        else:
            print(f"Wrote SoundFilter to: {filter_output_path}")
        
        print("\n=== Sample SoundFilter (first 3) ===")
        for entry in filter_entries[:3]:
            print(f"ID: {entry['ID']}")
            for key, value in entry.items():
                if value and key != 'ID':
                    print(f"  {key}: {value}")
            print()
    
    print("\n" + "=" * 60)
    print("=== GENERATING SOUNDFILTERELEM ===")
    print("=" * 60)
    
    print("\n=== Loading SoundFilterElem ===")
    sound_filter_elem_path = find_table_file(INPUT_DIR, "SoundFilterElem")
    
    if not sound_filter_elem_path:
        print(f"WARNING: SoundFilterElem table not found in {INPUT_DIR}")
        print("Skipping SoundFilterElem generation")
    else:
        print(f"Found SoundFilterElem: {sound_filter_elem_path}")
        sound_filter_elem_data = load_sound_filter_elem(sound_filter_elem_path)
        print(f"Loaded {len(sound_filter_elem_data)} SoundFilterElem entries")
        
        print("\n=== Generating SoundFilterElem output ===")
        filter_elem_entries = generate_sound_filter_elem_output(sound_filter_elem_data)
        print(f"Generated {len(filter_elem_entries)} SoundFilterElem entries")
        
        print("\n=== Writing SoundFilterElem.csv ===")
        filter_elem_output_path = os.path.join(OUTPUT_DIR, "SoundFilterElem.csv")
        write_sound_filter_elem(filter_elem_output_path, filter_elem_entries, wdbx_format)
        
        if wdbx_format:
            print(f"Wrote SoundFilterElem to: {filter_elem_output_path} (WDBX format)")
        else:
            print(f"Wrote SoundFilterElem to: {filter_elem_output_path}")
        
        print("\n=== Sample SoundFilterElem (first 3) ===")
        for entry in filter_elem_entries[:3]:
            print(f"ID: {entry['ID']}")
            for key, value in entry.items():
                if value and key != 'ID':
                    print(f"  {key}: {value}")
            print()
    
    print("\n" + "=" * 60)
    print("=== GENERATING SOUNDPROVIDERPREFERENCES ===")
    print("=" * 60)
    
    print("\n=== Loading SoundProviderPreferences ===")
    sound_provider_path = find_table_file(INPUT_DIR, "SoundProviderPreferences")
    
    if not sound_provider_path:
        print(f"WARNING: SoundProviderPreferences table not found in {INPUT_DIR}")
        print("Skipping SoundProviderPreferences generation")
    else:
        print(f"Found SoundProviderPreferences: {sound_provider_path}")
        sound_provider_data = load_sound_provider_preferences(sound_provider_path)
        print(f"Loaded {len(sound_provider_data)} SoundProviderPreferences entries")
        
        print("\n=== Generating SoundProviderPreferences output ===")
        provider_entries = generate_sound_provider_preferences_output(sound_provider_data)
        print(f"Generated {len(provider_entries)} SoundProviderPreferences entries")
        
        print("\n=== Writing SoundProviderPreferences.csv ===")
        provider_output_path = os.path.join(OUTPUT_DIR, "SoundProviderPreferences.csv")
        write_sound_provider_preferences(provider_output_path, provider_entries, wdbx_format)
        
        if wdbx_format:
            print(f"Wrote SoundProviderPreferences to: {provider_output_path} (WDBX format)")
        else:
            print(f"Wrote SoundProviderPreferences to: {provider_output_path}")
        
        print("\n=== Sample SoundProviderPreferences (first 3) ===")
        for entry in provider_entries[:3]:
            print(f"ID: {entry['ID']}")
            for key, value in entry.items():
                if value and key != 'ID':
                    print(f"  {key}: {value}")
            print()
    
    print("\n" + "=" * 60)
    print("=== GENERATING VOCALUISOUNDS ===")
    print("=" * 60)
    
    print("\n=== Loading VocalUISounds ===")
    vocal_ui_path = find_table_file(INPUT_DIR, "VocalUISounds")
    
    if not vocal_ui_path:
        print(f"WARNING: VocalUISounds table not found in {INPUT_DIR}")
        print("Skipping VocalUISounds generation")
    else:
        print(f"Found VocalUISounds: {vocal_ui_path}")
        vocal_ui_data = load_vocal_ui_sounds(vocal_ui_path)
        print(f"Loaded {len(vocal_ui_data)} VocalUISounds entries")
        
        # Load WotLK VocalUISounds for PissedSoundID data
        wotlk_vocal_path = os.path.join(WOTLK_DIR, "Wotlk-VocalUISounds.csv")
        if os.path.exists(wotlk_vocal_path):
            print(f"Loading WotLK VocalUISounds from: {wotlk_vocal_path}")
            wotlk_vocal_data = load_wotlk_vocal_ui_sounds(wotlk_vocal_path)
            print(f"Loaded {len(wotlk_vocal_data)} WotLK VocalUISounds entries for PissedSoundID")
        else:
            print(f"WARNING: WotLK VocalUISounds not found at {wotlk_vocal_path}")
            wotlk_vocal_data = {}
        
        print("\n=== Generating VocalUISounds output ===")
        vocal_entries = generate_vocal_ui_sounds_output(vocal_ui_data, wotlk_vocal_data)
        print(f"Generated {len(vocal_entries)} VocalUISounds entries")
        
        print("\n=== Writing VocalUISounds.csv ===")
        vocal_output_path = os.path.join(OUTPUT_DIR, "VocalUISounds.csv")
        write_vocal_ui_sounds(vocal_output_path, vocal_entries, wdbx_format)
        
        if wdbx_format:
            print(f"Wrote VocalUISounds to: {vocal_output_path} (WDBX format)")
        else:
            print(f"Wrote VocalUISounds to: {vocal_output_path}")
        
        print("\n=== Sample VocalUISounds (first 3) ===")
        for entry in vocal_entries[:3]:
            print(f"ID: {entry['ID']}")
            for key, value in entry.items():
                if value and key != 'ID':
                    print(f"  {key}: {value}")
            print()
    
    print("\n" + "=" * 60)
    print("=== GENERATING ZONEINTROMUSICTABLE ===")
    print("=" * 60)
    
    print("\n=== Loading ZoneIntroMusicTable ===")
    zone_intro_path = find_table_file(INPUT_DIR, "ZoneIntroMusicTable")
    
    if not zone_intro_path:
        print(f"WARNING: ZoneIntroMusicTable table not found in {INPUT_DIR}")
        print("Skipping ZoneIntroMusicTable generation")
    else:
        print(f"Found ZoneIntroMusicTable: {zone_intro_path}")
        zone_intro_data = load_zone_intro_music_table(zone_intro_path)
        print(f"Loaded {len(zone_intro_data)} ZoneIntroMusicTable entries")
        
        print("\n=== Generating ZoneIntroMusicTable output ===")
        zone_entries = generate_zone_intro_music_output(zone_intro_data)
        print(f"Generated {len(zone_entries)} ZoneIntroMusicTable entries")
        
        print("\n=== Writing ZoneIntroMusicTable.csv ===")
        zone_output_path = os.path.join(OUTPUT_DIR, "ZoneIntroMusicTable.csv")
        write_zone_intro_music_table(zone_output_path, zone_entries, wdbx_format)
        
        if wdbx_format:
            print(f"Wrote ZoneIntroMusicTable to: {zone_output_path} (WDBX format)")
        else:
            print(f"Wrote ZoneIntroMusicTable to: {zone_output_path}")
        
        print("\n=== Sample ZoneIntroMusicTable (first 3) ===")
        for entry in zone_entries[:3]:
            print(f"ID: {entry['ID']}")
            for key, value in entry.items():
                if value and key != 'ID':
                    print(f"  {key}: {value}")
            print()
    
    print("\n" + "=" * 60)
    print("=== GENERATING ZONEMUSIC ===")
    print("=" * 60)
    
    print("\n=== Loading ZoneMusic ===")
    zone_music_path = find_table_file(INPUT_DIR, "ZoneMusic")
    
    if not zone_music_path:
        print(f"WARNING: ZoneMusic table not found in {INPUT_DIR}")
        print("Skipping ZoneMusic generation")
    else:
        print(f"Found ZoneMusic: {zone_music_path}")
        zone_music_data = load_zone_music(zone_music_path)
        print(f"Loaded {len(zone_music_data)} ZoneMusic entries")
        
        print("\n=== Generating ZoneMusic output ===")
        zone_music_entries = generate_zone_music_output(zone_music_data)
        print(f"Generated {len(zone_music_entries)} ZoneMusic entries")
        
        print("\n=== Writing ZoneMusic.csv ===")
        zone_music_output_path = os.path.join(OUTPUT_DIR, "ZoneMusic.csv")
        write_zone_music(zone_music_output_path, zone_music_entries, wdbx_format)
        
        if wdbx_format:
            print(f"Wrote ZoneMusic to: {zone_music_output_path} (WDBX format)")
        else:
            print(f"Wrote ZoneMusic to: {zone_music_output_path}")
        
        print("\n=== Sample ZoneMusic (first 3) ===")
        for entry in zone_music_entries[:3]:
            print(f"ID: {entry['ID']}")
            for key, value in entry.items():
                if value and key != 'ID':
                    print(f"  {key}: {value}")
            print()
    
    print("\n" + "=" * 60)
    print("=== GENERATING CREATUREMODELDATA ===")
    print("=" * 60)
    
    print("\n=== Loading CreatureModelData ===")
    creature_model_path = find_table_file(INPUT_DIR, "CreatureModelData")
    
    if not creature_model_path:
        print(f"WARNING: CreatureModelData table not found in {INPUT_DIR}")
        print("Skipping CreatureModelData generation")
    else:
        print(f"Found CreatureModelData: {creature_model_path}")
        creature_model_data = load_creature_model_data(creature_model_path)
        print(f"Loaded {len(creature_model_data)} CreatureModelData entries")
        
        print("\n=== Generating CreatureModelData output ===")
        creature_model_entries, unmapped_file_ids = generate_creature_model_data_output(creature_model_data, model_files)
        print(f"Generated {len(creature_model_entries)} CreatureModelData entries")
        
        # Check for unmapped model FileDataIDs
        if unmapped_file_ids:
            log_path = "CreatureModelData.log"
            write_creature_model_log(log_path, unmapped_file_ids)
            print(f"WARNING: Found {len(unmapped_file_ids)} entries with unmapped model FileDataIDs")
            print(f"Log written to: {log_path}")
        else:
            print("All model FileDataIDs successfully mapped!")
        
        print("\n=== Writing CreatureModelData.csv ===")
        creature_model_output_path = os.path.join(OUTPUT_DIR, "CreatureModelData.csv")
        write_creature_model_data(creature_model_output_path, creature_model_entries, wdbx_format)
        
        if wdbx_format:
            print(f"Wrote CreatureModelData to: {creature_model_output_path} (WDBX format)")
        else:
            print(f"Wrote CreatureModelData to: {creature_model_output_path}")
        
        print("\n=== Sample CreatureModelData (first 3) ===")
        for entry in creature_model_entries[:3]:
            print(f"ID: {entry['ID']}")
            for key, value in entry.items():
                if value and key != 'ID':
                    print(f"  {key}: {value}")
            print()
    
    print("\n" + "=" * 60)
    print("=== GENERATING CREATUREDISPLAYINFO ===")
    print("=" * 60)
    
    print("\n=== Loading CreatureDisplayInfo ===")
    creature_display_path = find_table_file(INPUT_DIR, "CreatureDisplayInfo")
    
    if not creature_display_path:
        print(f"WARNING: CreatureDisplayInfo table not found in {INPUT_DIR}")
        print("Skipping CreatureDisplayInfo generation")
    else:
        print(f"Found CreatureDisplayInfo: {creature_display_path}")
        creature_display_data = load_creature_display_info(creature_display_path)
        print(f"Loaded {len(creature_display_data)} CreatureDisplayInfo entries")
        
        # Load CreatureDisplayInfoGeosetData
        geoset_path = find_table_file(INPUT_DIR, "CreatureDisplayInfoGeosetData")
        if geoset_path:
            print(f"Found CreatureDisplayInfoGeosetData: {geoset_path}")
            geoset_data = load_creature_display_info_geoset_data(geoset_path)
            print(f"Loaded CreatureDisplayInfoGeosetData for {len(geoset_data)} display info IDs")
        else:
            print(f"WARNING: CreatureDisplayInfoGeosetData not found - CreatureGeosetData will default to 0")
            geoset_data = {}
        
        # Load WotLK CreatureDisplayInfo for BloodLevel
        wotlk_display_path = os.path.join(WOTLK_DIR, "Wotlk-CreatureDisplayInfo.csv")
        if os.path.exists(wotlk_display_path):
            print(f"Loading WotLK CreatureDisplayInfo from: {wotlk_display_path}")
            wotlk_display_data = load_wotlk_creature_display_info(wotlk_display_path)
            print(f"Loaded {len(wotlk_display_data)} WotLK CreatureDisplayInfo entries for BloodLevel")
        else:
            print(f"WARNING: WotLK CreatureDisplayInfo not found at {wotlk_display_path} - BloodLevel will default to 0")
            wotlk_display_data = {}
        
        print("\n=== Generating CreatureDisplayInfo output ===")
        creature_display_entries, unmapped_texture_ids, geoset_overflows = generate_creature_display_info_output(creature_display_data, texture_files, geoset_data, wotlk_display_data)
        print(f"Generated {len(creature_display_entries)} CreatureDisplayInfo entries")
        
        # Write separate logs if needed
        if unmapped_texture_ids:
            texture_log_path = "CreatureDisplayInfo_Textures.log"
            write_creature_display_info_texture_log(texture_log_path, unmapped_texture_ids)
            print(f"WARNING: Found {len(set(item['ID'] for item in unmapped_texture_ids))} entries with unmapped texture FileDataIDs")
            print(f"Texture log written to: {texture_log_path}")
        else:
            print("All texture FileDataIDs successfully mapped!")
        
        if geoset_overflows:
            geoset_log_path = "CreatureDisplayInfo_GeosetOverflow.log"
            write_creature_display_info_geoset_log(geoset_log_path, geoset_overflows)
            print(f"WARNING: Found {len(geoset_overflows)} entries with CreatureGeosetData overflow")
            print(f"Geoset overflow log written to: {geoset_log_path}")
        
        print("\n=== Writing CreatureDisplayInfo.csv ===")
        creature_display_output_path = os.path.join(OUTPUT_DIR, "CreatureDisplayInfo.csv")
        write_creature_display_info(creature_display_output_path, creature_display_entries, wdbx_format)
        
        if wdbx_format:
            print(f"Wrote CreatureDisplayInfo to: {creature_display_output_path} (WDBX format)")
        else:
            print(f"Wrote CreatureDisplayInfo to: {creature_display_output_path}")
        
        print("\n=== Sample CreatureDisplayInfo (first 3) ===")
        for entry in creature_display_entries[:3]:
            print(f"ID: {entry['ID']}")
            for key, value in entry.items():
                if value and key != 'ID':
                    print(f"  {key}: {value}")
            print()
    
    print("\n" + "=" * 60)
    print("=== GENERATING PARTICLECOLOR ===")
    print("=" * 60)
    
    print("\n=== Loading ParticleColor ===")
    particle_color_path = find_table_file(INPUT_DIR, "ParticleColor")
    
    if not particle_color_path:
        print(f"WARNING: ParticleColor table not found in {INPUT_DIR}")
        print("Skipping ParticleColor generation")
    else:
        print(f"Found ParticleColor: {particle_color_path}")
        particle_color_data = load_particle_color(particle_color_path)
        print(f"Loaded {len(particle_color_data)} ParticleColor entries")
        
        print("\n=== Generating ParticleColor output ===")
        particle_entries = generate_particle_color_output(particle_color_data)
        print(f"Generated {len(particle_entries)} ParticleColor entries")
        
        print("\n=== Writing ParticleColor.csv ===")
        particle_output_path = os.path.join(OUTPUT_DIR, "ParticleColor.csv")
        write_particle_color(particle_output_path, particle_entries, wdbx_format)
        
        if wdbx_format:
            print(f"Wrote ParticleColor to: {particle_output_path} (WDBX format)")
        else:
            print(f"Wrote ParticleColor to: {particle_output_path}")
        
        print("\n=== Sample ParticleColor (first 3) ===")
        for entry in particle_entries[:3]:
            print(f"ID: {entry['ID']}")
            for key, value in entry.items():
                if value and key != 'ID':
                    print(f"  {key}: {value}")
            print()
    
    print("\n" + "=" * 60)
    print("=== GENERATING OBJECTEFFECTMODIFIER ===")
    print("=" * 60)
    
    print("\n=== Loading ObjectEffectModifier ===")
    object_effect_modifier_path = find_table_file(INPUT_DIR, "ObjectEffectModifier")
    
    if not object_effect_modifier_path:
        print(f"WARNING: ObjectEffectModifier table not found in {INPUT_DIR}")
        print("Skipping ObjectEffectModifier generation")
    else:
        print(f"Found ObjectEffectModifier: {object_effect_modifier_path}")
        object_effect_modifier_data = load_object_effect_modifier(object_effect_modifier_path)
        print(f"Loaded {len(object_effect_modifier_data)} ObjectEffectModifier entries")
        
        print("\n=== Generating ObjectEffectModifier output ===")
        object_effect_entries = generate_object_effect_modifier_output(object_effect_modifier_data)
        print(f"Generated {len(object_effect_entries)} ObjectEffectModifier entries")
        
        print("\n=== Writing ObjectEffectModifier.csv ===")
        object_effect_modifier_output_path = os.path.join(OUTPUT_DIR, "ObjectEffectModifier.csv")
        write_object_effect_modifier(object_effect_modifier_output_path, object_effect_entries, wdbx_format)
        
        if wdbx_format:
            print(f"Wrote ObjectEffectModifier to: {object_effect_modifier_output_path} (WDBX format)")
        else:
            print(f"Wrote ObjectEffectModifier to: {object_effect_modifier_output_path}")
        
        print("\n=== Sample ObjectEffectModifier (first 3) ===")
        for entry in object_effect_entries[:3]:
            print(f"ID: {entry['ID']}")
            for key, value in entry.items():
                if value and key != 'ID':
                    print(f"  {key}: {value}")
            print()
    
    print("\n" + "=" * 60)
    print("=== GENERATING OBJECTEFFECT ===")
    print("=" * 60)
    
    print("\n=== Loading ObjectEffect ===")
    object_effect_path = find_table_file(INPUT_DIR, "ObjectEffect")
    
    if not object_effect_path:
        print(f"WARNING: ObjectEffect table not found in {INPUT_DIR}")
        print("Skipping ObjectEffect generation")
    else:
        print(f"Found ObjectEffect: {object_effect_path}")
        object_effect_data = load_object_effect(object_effect_path)
        print(f"Loaded {len(object_effect_data)} ObjectEffect entries")
        
        print("\n=== Generating ObjectEffect output ===")
        object_effect_entries, zero_effect_rec_ids = generate_object_effect_output(object_effect_data, sound_entries)
        print(f"Generated {len(object_effect_entries)} ObjectEffect entries")
        
        # Log entries with EffectRecID = 0
        if zero_effect_rec_ids:
            object_effect_log_path = "ObjectEffect.log"
            write_object_effect_log(object_effect_log_path, zero_effect_rec_ids)
            print(f"WARNING: Skipped {len(zero_effect_rec_ids)} entries with EffectRecID = 0")
            print(f"Log written to: {object_effect_log_path}")
        
        print("\n=== Writing ObjectEffect.csv ===")
        object_effect_output_path = os.path.join(OUTPUT_DIR, "ObjectEffect.csv")
        write_object_effect(object_effect_output_path, object_effect_entries, wdbx_format)
        
        if wdbx_format:
            print(f"Wrote ObjectEffect to: {object_effect_output_path} (WDBX format)")
        else:
            print(f"Wrote ObjectEffect to: {object_effect_output_path}")
        
        print("\n=== Sample ObjectEffect (first 3) ===")
        for entry in object_effect_entries[:3]:
            print(f"ID: {entry['ID']}")
            for key, value in entry.items():
                if value and key != 'ID':
                    print(f"  {key}: {value}")
            print()
        
        print("\n=== Generating ObjectEffectGroup ===")
        object_effect_group_entries = generate_object_effect_group_output(object_effect_entries)
        print(f"Generated {len(object_effect_group_entries)} ObjectEffectGroup entries")
        
        print("\n=== Writing ObjectEffectGroup.csv ===")
        object_effect_group_output_path = os.path.join(OUTPUT_DIR, "ObjectEffectGroup.csv")
        write_object_effect_group(object_effect_group_output_path, object_effect_group_entries, wdbx_format)
        
        if wdbx_format:
            print(f"Wrote ObjectEffectGroup to: {object_effect_group_output_path} (WDBX format)")
        else:
            print(f"Wrote ObjectEffectGroup to: {object_effect_group_output_path}")
        
        print("\n=== Sample ObjectEffectGroup (first 3) ===")
        for entry in object_effect_group_entries[:3]:
            print(f"ID: {entry['ID']}")
            for key, value in entry.items():
                if value and key != 'ID':
                    print(f"  {key}: {value}")
            print()
    
    print("\n" + "=" * 60)
    print("=== GENERATING OBJECTEFFECTPACKAGEELEM ===")
    print("=" * 60)
    
    print("\n=== Loading ObjectEffectPackageElem ===")
    package_elem_path = find_table_file(INPUT_DIR, "ObjectEffectPackageElem")
    
    if not package_elem_path:
        print(f"WARNING: ObjectEffectPackageElem table not found in {INPUT_DIR}")
        print("Skipping ObjectEffectPackageElem generation")
    else:
        print(f"Found ObjectEffectPackageElem: {package_elem_path}")
        package_elem_data = load_object_effect_package_elem(package_elem_path)
        print(f"Loaded {len(package_elem_data)} ObjectEffectPackageElem entries")
        
        print("\n=== Generating ObjectEffectPackageElem output ===")
        package_elem_entries, skipped_package_ids = generate_object_effect_package_elem_output(package_elem_data, object_effect_group_entries)
        print(f"Generated {len(package_elem_entries)} ObjectEffectPackageElem entries")
        
        # Log skipped entries
        if skipped_package_ids:
            package_elem_log_path = "ObjectEffectPackageElem.log"
            write_object_effect_package_elem_log(package_elem_log_path, skipped_package_ids)
            print(f"WARNING: Skipped {len(skipped_package_ids)} entries with invalid ObjectEffectGroupID")
            print(f"Log written to: {package_elem_log_path}")
        
        print("\n=== Writing ObjectEffectPackageElem.csv ===")
        package_elem_output_path = os.path.join(OUTPUT_DIR, "ObjectEffectPackageElem.csv")
        write_object_effect_package_elem(package_elem_output_path, package_elem_entries, wdbx_format)
        
        if wdbx_format:
            print(f"Wrote ObjectEffectPackageElem to: {package_elem_output_path} (WDBX format)")
        else:
            print(f"Wrote ObjectEffectPackageElem to: {package_elem_output_path}")
        
        print("\n=== Sample ObjectEffectPackageElem (first 3) ===")
        for entry in package_elem_entries[:3]:
            print(f"ID: {entry['ID']}")
            for key, value in entry.items():
                if value and key != 'ID':
                    print(f"  {key}: {value}")
            print()
        
        print("\n=== Generating ObjectEffectPackage ===")
        package_entries = generate_object_effect_package_output(package_elem_entries, object_effect_group_entries)
        print(f"Generated {len(package_entries)} ObjectEffectPackage entries")
        
        print("\n=== Writing ObjectEffectPackage.csv ===")
        package_output_path = os.path.join(OUTPUT_DIR, "ObjectEffectPackage.csv")
        write_object_effect_package(package_output_path, package_entries, wdbx_format)
        
        if wdbx_format:
            print(f"Wrote ObjectEffectPackage to: {package_output_path} (WDBX format)")
        else:
            print(f"Wrote ObjectEffectPackage to: {package_output_path}")
        
        print("\n=== Sample ObjectEffectPackage (first 3) ===")
        for entry in package_entries[:3]:
            print(f"ID: {entry['ID']}")
            for key, value in entry.items():
                if value and key != 'ID':
                    print(f"  {key}: {value}")
            print()
    
    print("\n" + "=" * 60)
    print("=== PROCESSING COMPLETE ===")
    print("=" * 60)
    
    # Show generated log files summary
    log_files = []
    if os.path.exists("SoundEntries.log"):
        log_files.append("SoundEntries.log")
    if os.path.exists("SoundEntries_SoundKit.log"):
        log_files.append("SoundEntries_SoundKit.log")
    if os.path.exists("CreatureModelData.log"):
        log_files.append("CreatureModelData.log")
    if os.path.exists("CreatureDisplayInfo_Textures.log"):
        log_files.append("CreatureDisplayInfo_Textures.log")
    if os.path.exists("CreatureDisplayInfo_GeosetOverflow.log"):
        log_files.append("CreatureDisplayInfo_GeosetOverflow.log")
    if os.path.exists("ObjectEffect.log"):
        log_files.append("ObjectEffect.log")
    if os.path.exists("ObjectEffectPackageElem.log"):
        log_files.append("ObjectEffectPackageElem.log")
    
    if log_files:
        print("\n!!! ATTENTION: Log files generated !!!")
        print("The following log files contain unmapped FileDataIDs that need manual correction:")
        for log_file in log_files:
            print(f"  - {log_file}")
        print("\nPlease review these logs to identify missing entries in the listfile.")
    else:
        print("\nNo issues found - all FileDataIDs were successfully mapped!")
    
    print("\n" + "=" * 60)