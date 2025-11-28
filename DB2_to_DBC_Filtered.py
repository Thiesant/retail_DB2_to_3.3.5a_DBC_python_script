import os
import csv
from pathlib import Path
from collections import defaultdict

# Optional imports for sound downloading
try:
    import requests
    import time
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Configuration
INPUT_DIR = "0_Input"
OUTPUT_DIR = "3_DBC_Filtered"
WOTLK_DIR = "1_DBCWotlk_csv"
DOWNLOAD_DIR = "5_Downloaded_Sounds"
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
            # Extract base name without version (e.g., "CreatureModelData" from "CreatureModelData.11.2.5.64502.csv")
            base_name = filename.split('.')[0]
            if base_name.lower() == table_name_lower:
                return os.path.join(directory, filename)
    return None

def convert_float_to_wdbx(value):
    """
    Convert float value for WDBX format (replace . with ,)
    Returns the converted string.
    """
    if not value:
        return value
    
    value_str = str(value)
    # Replace decimal point with comma
    return value_str.replace('.', ',')

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

def load_soundkit_entries(soundkit_path):
    """
    Load SoundKitEntry data and group by SoundKitID.
    Returns a dictionary: {SoundKitID: [list of entries]}
    """
    soundkit_data = defaultdict(list)
    
    with open(soundkit_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
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
            row_normalized = {k.lower(): v for k, v in row.items()}
            entry_id = row_normalized.get('id', '').strip()
            name = row_normalized.get('name', '').strip()
            if entry_id:
                wotlk_names[entry_id] = name
    
    return wotlk_names

def load_soundkit_advanced(soundkit_advanced_path):
    """
    Load SoundKitAdvanced table data.
    Returns a list of dictionaries with normalized column names.
    """
    soundkit_advanced_data = []
    
    with open(soundkit_advanced_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_normalized = {k.lower(): v for k, v in row.items()}
            soundkit_advanced_data.append(row_normalized)
    
    return soundkit_advanced_data

def filter_sound_entries_advanced(soundkit_advanced_data, filtered_advanced_ids, sound_entries):
    """
    Filter SoundEntriesAdvanced data from SoundKitAdvanced.
    Enriches with Name from SoundEntries.
    Returns a list of dictionaries representing each SoundEntriesAdvanced row.
    """
    sound_entries_names = {entry['ID']: entry.get('Name', '') for entry in sound_entries}
    
    advanced_entries = []
    names_found = 0
    names_missing = 0
    
    for row in soundkit_advanced_data:
        advanced_id = row.get('id', '').strip()
        
        if advanced_id in filtered_advanced_ids:
            entry_data = {
                'ID': advanced_id,
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
                names_found += 1
            else:
                names_missing += 1
            
            advanced_entries.append(entry_data)
    
    print(f"  Names found: {names_found}, Names missing: {names_missing}")
    
    return advanced_entries

def write_sound_entries_advanced(output_path, advanced_entries, wdbx_format=False, append_mode=False):
    """
    Write SoundEntriesAdvanced data to CSV file.
    If wdbx_format is True, quote all fields and convert float decimals from . to ,
    Sorts entries by ID.
    """
    # Load existing data if in append mode
    if append_mode:
        existing_entries = load_existing_csv(output_path)
        if existing_entries:
            print(f"  → Merging with {len(existing_entries)} existing entry(ies)")
            advanced_entries = merge_csv_entries(existing_entries, advanced_entries)
    
    fieldnames = [
        'ID', 'SoundEntryID', 'InnerRadius2D', 'TimeA', 'TimeB', 'TimeC', 'TimeD',
        'RandomOffsetRange', 'Usage', 'TimeIntervalMin', 'TimeIntervalMax',
        'VolumeSliderCategory', 'DuckToSFX', 'DuckToMusic', 'DuckToAmbience',
        'InnerRadiusOfInfluence', 'OuterRadiusOfInfluence', 'TimeToDuck', 'TimeToUnduck',
        'InsideAngle', 'OutsideAngle', 'OutsideVolume', 'OuterRadius2D', 'Name'
    ]
    
    if wdbx_format:
        float_fields = [
            'InnerRadius2D', 'DuckToSFX', 'DuckToMusic', 'DuckToAmbience',
            'InnerRadiusOfInfluence', 'OuterRadiusOfInfluence', 'InsideAngle',
            'OutsideAngle', 'OutsideVolume', 'OuterRadius2D'
        ]
        for entry in advanced_entries:
            for field in float_fields:
                if field in entry:
                    entry[field] = convert_float_to_wdbx(entry[field])
    
    sorted_entries = sorted(advanced_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def load_soundkit_table(soundkit_path):
    """
    Load SoundKit table for enrichment.
    Returns a dictionary: {ID: row_data}
    """
    soundkit_table = {}
    
    with open(soundkit_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_normalized = {k.lower(): v for k, v in row.items()}
            soundkit_id = row_normalized.get('id', '').strip()
            if soundkit_id:
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
        
        # Collect volumes from all entries
        volumes = []
        for entry in entries:
            volume = entry.get('volume', '').strip()
            if volume:
                try:
                    vol_float = float(volume)
                    volumes.append(vol_float)
                except (ValueError, TypeError):
                    volumes.append(0.0)
            else:
                volumes.append(0.0)
        
        # Collect file paths and frequencies (up to 10)
        file_paths = []
        frequencies = []
        is_mapped = []  # Track if FileDataID was successfully mapped
        
        for i, entry in enumerate(entries[:10]):
            file_data_id = entry['filedataid'].strip()
            frequency = entry['frequency'].strip()
            
            # Get file path from audio_files dictionary
            if file_data_id in audio_files:
                file_paths.append(audio_files[file_data_id])
                frequencies.append(frequency)
                is_mapped.append(True)
            else:
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
                    relative_path = path[len(directory_base) + 1:]
                    entry_data[f'File_{i}'] = relative_path
                else:
                    entry_data[f'File_{i}'] = path
            else:
                entry_data[f'File_{i}'] = ''
        
        # Populate Freq_X columns
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
        
        # Set VolumeFloat to the highest volume
        if volumes:
            entry_data['VolumeFloat'] = str(max(volumes))
        
        # Enrich with SoundKit table data
        has_soundkit = False
        if soundkit_id in soundkit_table:
            kit_data = soundkit_table[soundkit_id]
            has_soundkit = True
            
            entry_data['SoundType'] = kit_data.get('soundtype', '').strip()
            
            kit_volume = kit_data.get('volumefloat', '').strip()
            if kit_volume:
                try:
                    kit_vol_float = float(kit_volume)
                    if kit_vol_float > 0:
                        entry_data['VolumeFloat'] = kit_volume
                except (ValueError, TypeError):
                    pass
            
            entry_data['Flags'] = kit_data.get('flags', '').strip()
            entry_data['MinDistance'] = kit_data.get('mindistance', '').strip()
            entry_data['DistanceCutoff'] = kit_data.get('distancecutoff', '').strip()
            entry_data['EAXDef'] = kit_data.get('eaxdef', '').strip()
            entry_data['SoundEntriesAdvancedID'] = kit_data.get('soundkitadvancedid', '').strip()
        
        # Apply defaults if missing
        if not entry_data['SoundType']:
            entry_data['SoundType'] = '18'
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
        
        if not has_soundkit:
            missing_soundkit_ids.append(soundkit_id)
        
        sound_entries.append(entry_data)
    
    return sound_entries, missing_soundkit_ids

def apply_names(sound_entries, use_wotlk, wotlk_names):
    """
    Apply names to SoundEntries from WotLK data or generate from File_1.
    """
    wotlk_matched = 0
    generated = 0
    
    for entry in sound_entries:
        soundkit_id = entry['ID']
        if use_wotlk and soundkit_id in wotlk_names:
            entry['Name'] = wotlk_names[soundkit_id]
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
        print(f"Applied {wotlk_matched} WotLK names, generated {generated} new names from File_1")
    else:
        print(f"Generated {generated} names from File_1")
    
    return sound_entries

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

def write_sound_entries(output_path, sound_entries, wdbx_format=False, append_mode=False):
    """
    Write SoundEntries to CSV file.
    """
    # Load existing data if in append mode
    if append_mode:
        existing_entries = load_existing_csv(output_path)
        if existing_entries:
            print(f"  → Merging with {len(existing_entries)} existing entry(ies)")
            sound_entries = merge_csv_entries(existing_entries, sound_entries)
    
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
        float_fields = ['VolumeFloat', 'MinDistance', 'DistanceCutoff']
        for entry in sound_entries:
            for field in float_fields:
                if field in entry:
                    entry[field] = convert_float_to_wdbx(entry[field])
    
    sorted_entries = sorted(sound_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

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

def filter_creature_display_info(creature_display_data, filtered_model_ids, texture_files, geoset_data, wotlk_display_data, used_fileids):
    """
    Filter CreatureDisplayInfo entries for selected ModelIDs.
    Maps texture FileDataIDs to filenames and calculates geoset data.
    Returns tuple: (filtered_entries, unmapped_texture_ids, geoset_overflows)
    """
    filtered_entries = []
    unmapped_texture_ids = []
    geoset_overflows = []
    
    for row in creature_display_data:
        model_id = row.get('modelid', '').strip()
        
        # Check if this entry matches any filtered ModelID
        if model_id in filtered_model_ids:
            entry_id = row.get('id', '').strip()
            
            # Map texture FileDataIDs to filenames
            texture_var_0_id = row.get('texturevariationfiledataid_0', '').strip()
            texture_var_1_id = row.get('texturevariationfiledataid_1', '').strip()
            texture_var_2_id = row.get('texturevariationfiledataid_2', '').strip()
            portrait_texture_id = row.get('portraittexturefiledataid', '').strip()
            
            # Get texture names or leave empty if not found
            texture_var_1 = ''
            if texture_var_0_id and texture_var_0_id != '0':
                used_fileids.add(texture_var_0_id)
                if texture_var_0_id in texture_files:
                    texture_var_1 = texture_files[texture_var_0_id]
                else:
                    unmapped_texture_ids.append({'ID': entry_id, 'FileDataID': texture_var_0_id, 'Field': 'TextureVariation_1'})
            
            texture_var_2 = ''
            if texture_var_1_id and texture_var_1_id != '0':
                used_fileids.add(texture_var_1_id)
                if texture_var_1_id in texture_files:
                    texture_var_2 = texture_files[texture_var_1_id]
                else:
                    unmapped_texture_ids.append({'ID': entry_id, 'FileDataID': texture_var_1_id, 'Field': 'TextureVariation_2'})
            
            texture_var_3 = ''
            if texture_var_2_id and texture_var_2_id != '0':
                used_fileids.add(texture_var_2_id)
                if texture_var_2_id in texture_files:
                    texture_var_3 = texture_files[texture_var_2_id]
                else:
                    unmapped_texture_ids.append({'ID': entry_id, 'FileDataID': texture_var_2_id, 'Field': 'TextureVariation_3'})
            
            portrait_texture_name = ''
            if portrait_texture_id and portrait_texture_id != '0':
                used_fileids.add(portrait_texture_id)
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
                'ModelID': model_id,
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
            
            filtered_entries.append(entry_data)
    
    return filtered_entries, unmapped_texture_ids, geoset_overflows

def write_creature_display_info(output_path, creature_display_entries, wdbx_format=False, append_mode=False):
    """
    Write CreatureDisplayInfo to CSV file.
    If wdbx_format is True, quote all fields and convert float decimals from . to ,
    Sorts entries by ID.
    """
    # Load existing data if in append mode
    if append_mode:
        existing_entries = load_existing_csv(output_path)
        if existing_entries:
            print(f"  → Merging with {len(existing_entries)} existing entry(ies)")
            creature_display_entries = merge_csv_entries(existing_entries, creature_display_entries)
    
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

def write_creature_display_info_texture_log(log_path, unmapped_texture_ids):
    """
    Write a log file for CreatureDisplayInfo entries with unmapped texture FileDataIDs.
    """
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("CreatureDisplayInfo - Missing Texture FileDataID Mappings (FILTERED)\n")
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
        f.write("CreatureDisplayInfo - CreatureGeosetData Overflow Values (FILTERED)\n")
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

def load_soundkit(soundkit_path):
    """Load SoundKit table from input."""
    soundkit_table = {}
    
    with open(soundkit_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_normalized = {k.lower(): v for k, v in row.items()}
            soundkit_id = row_normalized['id'].strip()
            soundkit_table[soundkit_id] = row_normalized
    
    return soundkit_table

def load_audio_files_for_soundentries(listfile_path):
    """
    Load audio files from listfile for SoundEntries generation.
    Returns a dictionary: {FileID: normalized_path}
    """
    audio_files = {}
    
    with open(listfile_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            if len(row) >= 2:
                file_id = row[0].strip()
                file_path = row[1].strip()
                
                path_lower = file_path.lower()
                if any(path_lower.endswith(ext) for ext in AUDIO_EXTENSIONS):
                    normalized_path = file_path.replace('/', '\\')
                    audio_files[file_id] = normalized_path
    
    return audio_files

def filter_sound_entries(soundkit_data, filtered_sound_entry_ids, audio_files, soundkit_table, listfile_data, used_fileids):
    """
    Filter and generate SoundEntries for selected IDs.
    Returns tuple: (sound_entries, unmapped_filedata_ids)
    """
    sound_entries = []
    unmapped_filedata_ids = []
    
    for soundkit_id, entries in soundkit_data.items():
        # Only process if this SoundKit ID is in our filtered list
        if soundkit_id not in filtered_sound_entry_ids:
            continue
        
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
        
        # Collect volumes from all entries
        volumes = []
        for entry in entries:
            volume = entry.get('volume', '').strip()
            if volume:
                try:
                    vol_float = float(volume)
                    volumes.append(vol_float)
                except (ValueError, TypeError):
                    volumes.append(0.0)
            else:
                volumes.append(0.0)
        
        # Collect file paths and frequencies (up to 10)
        file_paths = []
        frequencies = []
        
        for i, entry in enumerate(entries[:10]):
            file_data_id = entry['filedataid'].strip()
            frequency = entry['frequency'].strip()
            
            # Track FileDataID for listfile
            if file_data_id and file_data_id != '0':
                used_fileids.add(file_data_id)
            
            # Get file path from audio_files dictionary
            if file_data_id in audio_files:
                file_paths.append(audio_files[file_data_id])
                frequencies.append(frequency)
            else:
                if file_data_id and file_data_id != '0':
                    unmapped_filedata_ids.append({
                        'SoundKitID': soundkit_id,
                        'FileDataID': file_data_id
                    })
                # Keep the ID for manual correction
                file_paths.append(file_data_id)
                frequencies.append(frequency)
        
        # Find common directory
        directory_base = find_common_directory(file_paths)
        entry_data['DirectoryBase'] = directory_base
        
        # Remove common directory from file paths and populate File_X columns
        for i in range(1, 11):
            if i <= len(file_paths) and file_paths[i-1]:
                path = file_paths[i-1]
                if directory_base and path.startswith(directory_base + '\\'):
                    relative_path = path[len(directory_base) + 1:]
                    entry_data[f'File_{i}'] = relative_path
                else:
                    entry_data[f'File_{i}'] = path
            else:
                entry_data[f'File_{i}'] = ''
        
        # Populate Freq_X columns
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
        
        # Set VolumeFloat to the highest volume
        if volumes:
            entry_data['VolumeFloat'] = str(max(volumes))
        
        # Enrich with SoundKit table data
        if soundkit_id in soundkit_table:
            kit_data = soundkit_table[soundkit_id]
            
            entry_data['SoundType'] = kit_data.get('soundtype', '').strip()
            
            kit_volume = kit_data.get('volumefloat', '').strip()
            if kit_volume:
                try:
                    kit_vol_float = float(kit_volume)
                    if kit_vol_float > 0:
                        entry_data['VolumeFloat'] = kit_volume
                except (ValueError, TypeError):
                    pass
            
            entry_data['Flags'] = kit_data.get('flags', '').strip()
            entry_data['MinDistance'] = kit_data.get('mindistance', '').strip()
            entry_data['DistanceCutoff'] = kit_data.get('distancecutoff', '').strip()
            entry_data['EAXDef'] = kit_data.get('eaxdef', '').strip()
            entry_data['SoundEntriesAdvancedID'] = kit_data.get('soundentriesadvancedid', '').strip()
        
        # Set default values if still empty
        if not entry_data['VolumeFloat']:
            entry_data['VolumeFloat'] = '1.0'
        if not entry_data['Flags']:
            entry_data['Flags'] = '0'
        if not entry_data['MinDistance']:
            entry_data['MinDistance'] = '8.0'
        if not entry_data['DistanceCutoff']:
            entry_data['DistanceCutoff'] = '45.0'
        if not entry_data['EAXDef']:
            entry_data['EAXDef'] = '0'
        if not entry_data['SoundEntriesAdvancedID']:
            entry_data['SoundEntriesAdvancedID'] = '0'
        
        sound_entries.append(entry_data)
    
    return sound_entries, unmapped_filedata_ids

def write_soundentries(output_path, sound_entries, wdbx_format=False, append_mode=False):
    """Write SoundEntries to CSV file."""
    # Load existing data if in append mode
    if append_mode:
        existing_entries = load_existing_csv(output_path)
        if existing_entries:
            print(f"  → Merging with {len(existing_entries)} existing entry(ies)")
            sound_entries = merge_csv_entries(existing_entries, sound_entries)
    
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
        float_fields = ['VolumeFloat', 'MinDistance', 'DistanceCutoff']
        for entry in sound_entries:
            for field in float_fields:
                if field in entry:
                    entry[field] = convert_float_to_wdbx(entry[field])
    
    sorted_entries = sorted(sound_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def write_soundentries_log(log_path, unmapped_ids):
    """Write log file for SoundEntries with unmapped FileDataIDs."""
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("SoundEntries - Missing Audio FileDataID Mappings (FILTERED)\n")
        f.write("=" * 60 + "\n\n")
        f.write("The following SoundKit entries have FileDataIDs that are not in the listfile.\n\n")
        f.write("=" * 60 + "\n")
        f.write(f"SUMMARY:\n")
        f.write(f"  - Unique FileDataIDs not in listfile: {len(set(item['FileDataID'] for item in unmapped_ids))}\n")
        f.write("=" * 60 + "\n\n")
        
        for entry in unmapped_ids:
            f.write(f"SoundKitID: {entry['SoundKitID']}\n")
            f.write(f"FileDataID: {entry['FileDataID']}\n")
            f.write("-" * 60 + "\n")

def load_object_effect(object_effect_path):
    """
    Load ObjectEffect table from input.
    Returns a list of dictionaries with normalized column names.
    """
    object_effect_data = []
    
    with open(object_effect_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_normalized = {k.lower(): v for k, v in row.items()}
            object_effect_data.append(row_normalized)
    
    return object_effect_data

def filter_object_effect(object_effect_data, filtered_object_effect_group_ids, sound_entries):
    """
    Filter ObjectEffect entries for selected ObjectEffectGroupIDs.
    Gets Name from SoundEntries based on EffectRecID.
    Filters out entries where EffectRecID = 0.
    Returns tuple: (output_entries, zero_effect_rec_ids)
    """
    sound_entries_names = {entry['ID']: entry.get('Name', '') for entry in sound_entries}
    
    output_entries = []
    zero_effect_rec_ids = []
    
    for row in object_effect_data:
        object_effect_group_id = row.get('objecteffectgroupid', '').strip()
        
        if object_effect_group_id in filtered_object_effect_group_ids:
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
                'ObjectEffectGroupID': object_effect_group_id,
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

def generate_object_effect_group_output(object_effect_entries):
    """
    Generate ObjectEffectGroup output from ObjectEffect entries.
    Groups by ObjectEffectGroupID and uses the first non-empty Name found.
    """
    group_names = {}
    
    for entry in object_effect_entries:
        group_id = entry.get('ObjectEffectGroupID', '').strip()
        if group_id and group_id not in group_names:
            name = entry.get('Name', '').strip()
            if name:
                group_names[group_id] = name
            else:
                group_names[group_id] = ''
        elif group_id and group_id in group_names and not group_names[group_id]:
            name = entry.get('Name', '').strip()
            if name:
                group_names[group_id] = name
    
    output_entries = []
    for group_id, name in sorted(group_names.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
        entry_data = {
            'ID': group_id,
            'Name': name
        }
        output_entries.append(entry_data)
    
    return output_entries

def load_object_effect_package_elem(package_elem_path):
    """
    Load ObjectEffectPackageElem table from input.
    """
    package_elem_data = []
    
    with open(package_elem_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row_normalized = {k.lower(): v for k, v in row.items()}
            package_elem_data.append(row_normalized)
    
    return package_elem_data

def filter_object_effect_package_elem(package_elem_data, filtered_object_effect_package_ids, object_effect_group_entries):
    """
    Filter ObjectEffectPackageElem entries for selected ObjectEffectPackageIDs.
    Validates against ObjectEffectGroup entries.
    Returns tuple: (output_entries, skipped_ids, filtered_group_ids)
    """
    valid_group_ids = {entry['ID'] for entry in object_effect_group_entries}
    
    output_entries = []
    skipped_ids = []
    filtered_group_ids = set()
    
    for row in package_elem_data:
        package_id = row.get('objecteffectpackageid', '').strip()
        
        if package_id in filtered_object_effect_package_ids:
            entry_id = row.get('id', '').strip()
            group_id = row.get('objecteffectgroupid', '').strip()
            
            # Skip if ObjectEffectGroupID is not in valid groups
            if group_id and group_id not in valid_group_ids:
                skipped_ids.append({'ID': entry_id, 'ObjectEffectGroupID': group_id})
                continue
            
            if group_id:
                filtered_group_ids.add(group_id)
            
            entry_data = {
                'ID': entry_id,
                'ObjectEffectPackageID': package_id,
                'ObjectEffectGroupID': group_id,
                'StateType': row.get('statetype', '').strip()
            }
            
            output_entries.append(entry_data)
    
    return output_entries, skipped_ids, filtered_group_ids

def generate_object_effect_package_output(package_elem_entries, object_effect_group_entries):
    """
    Generate ObjectEffectPackage output from ObjectEffectPackageElem entries.
    Groups by ObjectEffectPackageID and uses the first non-empty ObjectEffectGroup Name found.
    """
    group_names = {entry['ID']: entry.get('Name', '') for entry in object_effect_group_entries}
    
    package_names = {}
    
    for entry in package_elem_entries:
        package_id = entry.get('ObjectEffectPackageID', '').strip()
        group_id = entry.get('ObjectEffectGroupID', '').strip()
        
        if package_id and package_id not in package_names:
            name = group_names.get(group_id, '')
            if name:
                package_names[package_id] = name
            else:
                package_names[package_id] = ''
        elif package_id and package_id in package_names and not package_names[package_id]:
            name = group_names.get(group_id, '')
            if name:
                package_names[package_id] = name
    
    output_entries = []
    for package_id, name in sorted(package_names.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
        entry_data = {
            'ID': package_id,
            'Name': name
        }
        output_entries.append(entry_data)
    
    return output_entries

def write_object_effect(output_path, object_effect_entries, wdbx_format=False, append_mode=False):
    """Write ObjectEffect to CSV file."""
    # Load existing data if in append mode
    if append_mode:
        existing_entries = load_existing_csv(output_path)
        if existing_entries:
            print(f"  → Merging with {len(existing_entries)} existing entry(ies)")
            object_effect_entries = merge_csv_entries(existing_entries, object_effect_entries)
    
    fieldnames = [
        'ID', 'Name', 'ObjectEffectGroupID', 'TriggerType', 'EventType', 'EffectRecType',
        'EffectRecID', 'Attachment', 'OffsetX', 'OffsetY', 'OffsetZ', 'ObjectEffectModifierID'
    ]
    
    if wdbx_format:
        float_fields = ['OffsetX', 'OffsetY', 'OffsetZ']
        for entry in object_effect_entries:
            for field in float_fields:
                if field in entry:
                    entry[field] = convert_float_to_wdbx(entry[field])
    
    sorted_entries = sorted(object_effect_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def write_object_effect_group(output_path, object_effect_group_entries, wdbx_format=False, append_mode=False):
    """Write ObjectEffectGroup to CSV file."""
    # Load existing data if in append mode
    if append_mode:
        existing_entries = load_existing_csv(output_path)
        if existing_entries:
            print(f"  → Merging with {len(existing_entries)} existing entry(ies)")
            object_effect_group_entries = merge_csv_entries(existing_entries, object_effect_group_entries)
    
    fieldnames = ['ID', 'Name']
    
    sorted_entries = sorted(object_effect_group_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def write_object_effect_package_elem(output_path, package_elem_entries, wdbx_format=False, append_mode=False):
    """Write ObjectEffectPackageElem to CSV file."""
    # Load existing data if in append mode
    if append_mode:
        existing_entries = load_existing_csv(output_path)
        if existing_entries:
            print(f"  → Merging with {len(existing_entries)} existing entry(ies)")
            package_elem_entries = merge_csv_entries(existing_entries, package_elem_entries)
    
    fieldnames = ['ID', 'ObjectEffectPackageID', 'ObjectEffectGroupID', 'StateType']
    
    sorted_entries = sorted(package_elem_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def write_object_effect_package(output_path, package_entries, wdbx_format=False, append_mode=False):
    """Write ObjectEffectPackage to CSV file."""
    # Load existing data if in append mode
    if append_mode:
        existing_entries = load_existing_csv(output_path)
        if existing_entries:
            print(f"  → Merging with {len(existing_entries)} existing entry(ies)")
            package_entries = merge_csv_entries(existing_entries, package_entries)
    
    fieldnames = ['ID', 'Name']
    
    sorted_entries = sorted(package_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
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
            row_normalized = {k.lower(): v for k, v in row.items()}
            object_effect_modifier_data.append(row_normalized)
    
    return object_effect_modifier_data

def filter_object_effect_modifier(object_effect_modifier_data, filtered_modifier_ids):
    """
    Filter ObjectEffectModifier entries for selected IDs.
    Reorders fields (Type fields first, then Params).
    Returns a list of dictionaries for output.
    """
    filtered_entries = []
    
    for row in object_effect_modifier_data:
        modifier_id = row.get('id', '').strip()
        
        if modifier_id in filtered_modifier_ids:
            entry_data = {
                'ID': modifier_id,
                'InputType': row.get('inputtype', '').strip(),
                'MapType': row.get('maptype', '').strip(),
                'OutputType': row.get('outputtype', '').strip(),
                'Param_0': row.get('param_0', '').strip(),
                'Param_1': row.get('param_1', '').strip(),
                'Param_2': row.get('param_2', '').strip(),
                'Param_3': row.get('param_3', '').strip()
            }
            
            filtered_entries.append(entry_data)
    
    return filtered_entries

def write_object_effect_modifier(output_path, modifier_entries, wdbx_format=False, append_mode=False):
    """
    Write ObjectEffectModifier to CSV file.
    If wdbx_format is True, quote all fields and convert float decimals from . to ,
    Sorts entries by ID.
    """
    # Load existing data if in append mode
    if append_mode:
        existing_entries = load_existing_csv(output_path)
        if existing_entries:
            print(f"  → Merging with {len(existing_entries)} existing entry(ies)")
            modifier_entries = merge_csv_entries(existing_entries, modifier_entries)
    
    fieldnames = ['ID', 'InputType', 'MapType', 'OutputType', 'Param_0', 'Param_1', 'Param_2', 'Param_3']
    
    if wdbx_format:
        float_fields = ['Param_0', 'Param_1', 'Param_2', 'Param_3']
        for entry in modifier_entries:
            for field in float_fields:
                if field in entry:
                    entry[field] = convert_float_to_wdbx(entry[field])
    
    sorted_entries = sorted(modifier_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def write_object_effect_log(log_path, zero_effect_rec_ids):
    """Write log file for ObjectEffect entries with EffectRecID = 0."""
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("ObjectEffect - Skipped Entries with EffectRecID = 0 (FILTERED)\n")
        f.write("=" * 60 + "\n\n")
        f.write("The following ObjectEffect entries have EffectRecID = 0 and were excluded\n")
        f.write("from the output as they don't reference any sound.\n\n")
        f.write("=" * 60 + "\n")
        f.write(f"SUMMARY:\n")
        f.write(f"  - Total entries skipped: {len(zero_effect_rec_ids)}\n")
        f.write("=" * 60 + "\n\n")
        
        for entry_id in zero_effect_rec_ids:
            f.write(f"ObjectEffect ID: {entry_id} (EffectRecID = 0)\n")

def write_object_effect_package_elem_log(log_path, skipped_ids):
    """Write log file for ObjectEffectPackageElem entries with invalid ObjectEffectGroupID."""
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("ObjectEffectPackageElem - Skipped Entries (FILTERED)\n")
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

def filter_footstep_terrain_lookup(footstep_data, filtered_creature_footstep_ids, filter_terrain=True):
    """
    Filter FootstepTerrainLookup entries for selected CreatureFootstepIDs.
    If filter_terrain is True, only include WotLK-compatible TerrainSoundIDs (0-10).
    Returns a list of dictionaries for output.
    """
    WOTLK_TERRAIN_IDS = {'0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '10'}
    filtered_entries = []
    terrain_filtered_count = 0
    
    for row in footstep_data:
        creature_footstep_id = row.get('creaturefootstepid', '').strip()
        
        # Check if this entry matches any filtered CreatureFootstepID
        if creature_footstep_id in filtered_creature_footstep_ids:
            terrain_sound_id = row.get('terrainsoundid', '').strip()
            
            # Filter terrain if requested
            if filter_terrain and terrain_sound_id not in WOTLK_TERRAIN_IDS:
                terrain_filtered_count += 1
                continue
            
            entry_data = {
                'ID': row.get('id', '').strip(),
                'CreatureFootstepID': creature_footstep_id,
                'TerrainSoundID': terrain_sound_id,
                'SoundID': row.get('soundid', '').strip(),
                'SoundIDSplash': row.get('soundidsplash', '').strip()
            }
            
            filtered_entries.append(entry_data)
    
    if filter_terrain and terrain_filtered_count > 0:
        print(f"  Filtered out {terrain_filtered_count} entries with non-WotLK terrain types")
    
    return filtered_entries

def write_footstep_terrain_lookup(output_path, footstep_entries, wdbx_format=False, append_mode=False):
    """
    Write FootstepTerrainLookup to CSV file.
    If wdbx_format is True, quote all fields.
    Sorts entries by ID.
    """
    # Load existing data if in append mode
    if append_mode:
        existing_entries = load_existing_csv(output_path)
        if existing_entries:
            print(f"  → Merging with {len(existing_entries)} existing entry(ies)")
            footstep_entries = merge_csv_entries(existing_entries, footstep_entries)
    
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

def filter_npc_sounds(npc_sounds_data, filtered_npc_sound_ids):
    """
    Filter NPCSounds entries for selected NPCSoundIDs.
    Renames SoundID_X (0-3 to 1-4).
    Returns a list of dictionaries for output.
    """
    filtered_entries = []
    
    for row in npc_sounds_data:
        npc_sound_id = row.get('id', '').strip()
        
        # Check if this entry matches any filtered NPCSoundID
        if npc_sound_id in filtered_npc_sound_ids:
            entry_data = {
                'ID': npc_sound_id,
                # Rename SoundID_0-3 to SoundID_1-4
                'SoundID_1': row.get('soundid_0', '').strip(),
                'SoundID_2': row.get('soundid_1', '').strip(),
                'SoundID_3': row.get('soundid_2', '').strip(),
                'SoundID_4': row.get('soundid_3', '').strip()
            }
            
            filtered_entries.append(entry_data)
    
    return filtered_entries

def write_npc_sounds(output_path, npc_entries, wdbx_format=False, append_mode=False):
    """
    Write NPCSounds to CSV file.
    If wdbx_format is True, quote all fields.
    Sorts entries by ID.
    """
    # Load existing data if in append mode
    if append_mode:
        existing_entries = load_existing_csv(output_path)
        if existing_entries:
            print(f"  → Merging with {len(existing_entries)} existing entry(ies)")
            npc_entries = merge_csv_entries(existing_entries, npc_entries)
    
    fieldnames = ['ID', 'SoundID_1', 'SoundID_2', 'SoundID_3', 'SoundID_4']
    
    # Sort by ID
    sorted_entries = sorted(npc_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
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

def filter_particle_color(particle_color_data, filtered_particle_color_ids):
    """
    Filter ParticleColor entries for selected ParticleColorIDs.
    Renames fields (0→1, 1→2, 2→3).
    Returns a list of dictionaries for output.
    """
    filtered_entries = []
    
    for row in particle_color_data:
        particle_color_id = row.get('id', '').strip()
        
        # Check if this entry matches any filtered ParticleColorID
        if particle_color_id in filtered_particle_color_ids:
            entry_data = {
                'ID': particle_color_id,
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
            
            filtered_entries.append(entry_data)
    
    return filtered_entries

def write_particle_color(output_path, particle_entries, wdbx_format=False, append_mode=False):
    """
    Write ParticleColor to CSV file.
    If wdbx_format is True, quote all fields.
    Sorts entries by ID.
    """
    # Load existing data if in append mode
    if append_mode:
        existing_entries = load_existing_csv(output_path)
        if existing_entries:
            print(f"  → Merging with {len(existing_entries)} existing entry(ies)")
            particle_entries = merge_csv_entries(existing_entries, particle_entries)
    
    fieldnames = ['ID', 'Start_1', 'Start_2', 'Start_3', 'Mid_1', 'Mid_2', 'Mid_3', 'End_1', 'End_2', 'End_3']
    
    # Sort by ID
    sorted_entries = sorted(particle_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
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

def filter_creature_sound_data(creature_sound_data, filtered_sound_ids):
    """
    Filter CreatureSoundData entries for selected SoundIDs.
    Recursively includes entries referenced by CreatureSoundDataIDPet.
    Renames SoundFidget_X (0-4 to 1-5) and CustomAttack_X (0-3 to 1-4).
    Returns a list of dictionaries for output.
    """
    # Create a lookup dictionary for faster access
    sound_data_lookup = {}
    for row in creature_sound_data:
        sound_id = row.get('id', '').strip()
        sound_data_lookup[sound_id] = row
    
    filtered_entries = []
    processed_ids = set()
    ids_to_process = set(filtered_sound_ids)
    
    # Process entries recursively to include CreatureSoundDataIDPet references
    while ids_to_process:
        current_id = ids_to_process.pop()
        
        # Skip if already processed
        if current_id in processed_ids:
            continue
        
        processed_ids.add(current_id)
        
        # Check if this ID exists in the data
        if current_id not in sound_data_lookup:
            continue
        
        row = sound_data_lookup[current_id]
        
        # Get CreatureSoundDataIDPet for recursive processing
        pet_sound_id = row.get('creaturesounddataidpet', '').strip()
        if pet_sound_id and pet_sound_id != '0' and pet_sound_id not in processed_ids:
            ids_to_process.add(pet_sound_id)
        
        entry_data = {
            'ID': current_id,
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
            'CreatureSoundDataIDPet': pet_sound_id
        }
        
        filtered_entries.append(entry_data)
    
    return filtered_entries

def write_creature_sound_data(output_path, creature_entries, wdbx_format=False, append_mode=False):
    """
    Write CreatureSoundData to CSV file.
    If wdbx_format is True, quote all fields and convert float decimals from . to ,
    Sorts entries by ID.
    """
    # Load existing data if in append mode
    if append_mode:
        existing_entries = load_existing_csv(output_path)
        if existing_entries:
            print(f"  → Merging with {len(existing_entries)} existing entry(ies)")
            creature_entries = merge_csv_entries(existing_entries, creature_entries)
    
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

def load_listfile(listfile_path):
    """
    Load the listfile and return a dictionary of FileID -> Path
    """
    listfile_data = {}
    
    with open(listfile_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            if len(row) >= 2:
                file_id = row[0].strip()
                file_path = row[1].strip()
                listfile_data[file_id] = file_path
    
    return listfile_data

def search_models_by_name(listfile_data, search_name):
    """
    Search for model files (.m2 or .mdx) containing the search name (case-insensitive).
    Accepts both / and \\ path separators in search string.
    Returns a list of tuples: [(FileID, Path), ...]
    """
    # Normalize search string: convert / to \ and make lowercase
    search_name_normalized = search_name.replace('/', '\\').lower()
    matches = []
    
    for file_id, file_path in listfile_data.items():
        # Normalize path separators
        normalized_path = file_path.replace('/', '\\')
        path_lower = normalized_path.lower()
        
        # Check if it's a model file (.m2 or .mdx)
        if path_lower.endswith('.m2') or path_lower.endswith('.mdx'):
            # Check if normalized search name is in the normalized path
            if search_name_normalized in path_lower:
                matches.append((file_id, normalized_path))
    
    return matches

def prompt_model_selection(listfile_data):
    """
    Prompt user to select model(s) by FileID or name.
    Returns a list of selected FileIDs.
    """
    print("\n" + "=" * 60)
    print("=== MODEL SELECTION ===")
    print("=" * 60)
    
    while True:
        print("\nChoose search method:")
        print("1. Search by FileID (partial match supported)")
        print("2. Search by model name (partial match)")
        choice = input("Enter choice (1 or 2): ").strip()
        
        if choice == '1':
            # Search by FileID (partial match)
            while True:
                file_id_input = input("Enter FileID (or part of FileID): ").strip()
                
                if not file_id_input:
                    print("ERROR: FileID cannot be empty")
                    continue
                
                # Find all FileIDs that contain the input (partial match)
                matches = []
                for file_id, file_path in listfile_data.items():
                    # Normalize path
                    normalized_path = file_path.replace('/', '\\')
                    path_lower = normalized_path.lower()
                    
                    # Check if it's a model file and FileID contains the input
                    if (path_lower.endswith('.m2') or path_lower.endswith('.mdx')) and file_id_input in file_id:
                        matches.append((file_id, normalized_path))
                
                if not matches:
                    print(f"No model files found with FileID containing '{file_id_input}'")
                    print("Please try again.")
                    continue
                
                if len(matches) == 1:
                    # Single match found
                    file_id, file_path = matches[0]
                    print(f"\nFound model:")
                    print(f"  FileID[{file_id}]: {file_path}")
                    return [file_id]
                
                # Multiple matches found
                print(f"\nMultiple models found:")
                for idx, (file_id, file_path) in enumerate(matches, 1):
                    print(f"{idx}. FileID[{file_id}]: {file_path}")
                
                while True:
                    selection = input("\nEnter selection (space-separated numbers, e.g., '1 3 4', or 'all' for all models): ").strip().lower()
                    
                    if selection == 'all':
                        # Select all models
                        selected_ids = [file_id for file_id, _ in matches]
                        print(f"\nSelected all {len(selected_ids)} models")
                        return selected_ids
                    
                    # Try to parse space-separated numbers
                    try:
                        choice_nums = [int(x.strip()) for x in selection.split()]
                        
                        # Validate all numbers are in range
                        if all(1 <= num <= len(matches) for num in choice_nums):
                            selected_ids = [matches[num - 1][0] for num in choice_nums]
                            print(f"\nSelected {len(selected_ids)} model(s):")
                            for num in choice_nums:
                                file_id, file_path = matches[num - 1]
                                print(f"  - FileID[{file_id}]: {file_path}")
                            return selected_ids
                        else:
                            print(f"ERROR: All numbers must be between 1 and {len(matches)}")
                    except ValueError:
                        print(f"ERROR: Invalid input. Please enter space-separated numbers (e.g., '1 3 4') or 'all'")
        
        elif choice == '2':
            # Search by name
            search_name = input("Enter part of the model name: ").strip()
            
            if not search_name:
                print("ERROR: Search name cannot be empty")
                continue
            
            matches = search_models_by_name(listfile_data, search_name)
            
            if not matches:
                print(f"No model files found containing '{search_name}'")
                print("Please try again.")
                continue
            
            if len(matches) == 1:
                # Single match found
                file_id, file_path = matches[0]
                print(f"\nFound model:")
                print(f"  FileID[{file_id}]: {file_path}")
                return [file_id]
            
            # Multiple matches found
            print(f"\nMultiple models found:")
            for idx, (file_id, file_path) in enumerate(matches, 1):
                print(f"{idx}. FileID[{file_id}]: {file_path}")
            
            while True:
                selection = input("\nEnter selection (space-separated numbers, e.g., '1 3 4', or 'all' for all models): ").strip().lower()
                
                if selection == 'all':
                    # Select all models
                    selected_ids = [file_id for file_id, _ in matches]
                    print(f"\nSelected all {len(selected_ids)} models")
                    return selected_ids
                
                # Try to parse space-separated numbers
                try:
                    choice_nums = [int(x.strip()) for x in selection.split()]
                    
                    # Validate all numbers are in range
                    if all(1 <= num <= len(matches) for num in choice_nums):
                        selected_ids = [matches[num - 1][0] for num in choice_nums]
                        print(f"\nSelected {len(selected_ids)} model(s):")
                        for num in choice_nums:
                            file_id, file_path = matches[num - 1]
                            print(f"  - FileID[{file_id}]: {file_path}")
                        return selected_ids
                    else:
                        print(f"ERROR: All numbers must be between 1 and {len(matches)}")
                except ValueError:
                    print(f"ERROR: Invalid input. Please enter space-separated numbers (e.g., '1 3 4') or 'all'")
        
        else:
            print("ERROR: Invalid choice. Please enter 1 or 2.")

def load_creature_model_data(model_data_path):
    """
    Load CreatureModelData entries.
    Returns a list of dictionaries with normalized column names.
    """
    model_data = []
    
    with open(model_data_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize column names to lowercase for case-insensitive matching
            row_normalized = {k.lower(): v for k, v in row.items()}
            model_data.append(row_normalized)
    
    return model_data

def filter_creature_model_data(model_data, selected_fileids, listfile_data):
    """
    Filter CreatureModelData entries for selected FileIDs.
    Returns tuple: (filtered_entries, unmapped_file_ids)
    """
    filtered_entries = []
    unmapped_file_ids = []
    
    for entry in model_data:
        filedata_id = entry.get('filedataid', '').strip()
        
        # Check if this entry matches any selected FileID
        if filedata_id in selected_fileids:
            # Get the model path from listfile
            model_path = listfile_data.get(filedata_id, '')
            
            if model_path:
                # Normalize path: replace / with \ and change .m2 to .mdx
                normalized_path = model_path.replace('/', '\\')
                if normalized_path.lower().endswith('.m2'):
                    normalized_path = normalized_path[:-3] + '.mdx'
                
                model_name = normalized_path
            else:
                # FileDataID not found in listfile
                model_name = filedata_id
                if filedata_id:
                    unmapped_file_ids.append({
                        'ID': entry.get('id', ''),
                        'FileDataID': filedata_id
                    })
            
            # Create output entry using correct column names from DB2
            output_entry = {
                'ID': entry.get('id', '').strip(),
                'Flags': entry.get('flags', '').strip(),
                'ModelName': model_name,
                'SizeClass': entry.get('sizeclass', '').strip(),
                'ModelScale': entry.get('modelscale', '').strip(),
                'BloodID': entry.get('bloodid', '').strip(),
                'FootprintTextureID': entry.get('footprinttextureid', '').strip(),
                'FootprintTextureLength': entry.get('footprinttexturelength', '').strip(),
                'FootprintTextureWidth': entry.get('footprinttexturewidth', '').strip(),
                'FootprintParticleScale': entry.get('footprintparticlescale', '').strip(),
                'FoleyMaterialID': entry.get('foleymaterialid', '').strip(),
                'FootstepShakeSize': entry.get('footstepcameraeffectid', '').strip(),
                'DeathThudShakeSize': entry.get('deaththudcameraeffectid', '').strip(),
                'SoundID': entry.get('soundid', '').strip(),
                'CollisionWidth': entry.get('collisionwidth', '').strip(),
                'CollisionHeight': entry.get('collisionheight', '').strip(),
                'MountHeight': entry.get('mountheight', '').strip(),
                'GeoBoxMinX': entry.get('geobox_0', '').strip(),
                'GeoBoxMinY': entry.get('geobox_1', '').strip(),
                'GeoBoxMinZ': entry.get('geobox_2', '').strip(),
                'GeoBoxMaxX': entry.get('geobox_3', '').strip(),
                'GeoBoxMaxY': entry.get('geobox_4', '').strip(),
                'GeoBoxMaxZ': entry.get('geobox_5', '').strip(),
                'WorldEffectScale': entry.get('worldeffectscale', '').strip(),
                'AttachedEffectScale': entry.get('attachedeffectscale', '').strip(),
                'MissileCollisionRadius': entry.get('missilecollisionradius', '').strip(),
                'MissileCollisionPush': entry.get('missilecollisionpush', '').strip(),
                'MissileCollisionRaise': entry.get('missilecollisionraise', '').strip()
            }
            
            filtered_entries.append(output_entry)
    
    return filtered_entries, unmapped_file_ids

def write_creature_model_data(output_path, model_entries, wdbx_format=False, append_mode=False):
    """
    Write CreatureModelData to CSV file.
    If wdbx_format is True, quote all fields and convert float decimals from . to ,
    Sorts entries by ID.
    """
    # Load existing data if in append mode
    if append_mode:
        existing_entries = load_existing_csv(output_path)
        if existing_entries:
            print(f"  → Merging with {len(existing_entries)} existing entry(ies)")
            model_entries = merge_csv_entries(existing_entries, model_entries)
    
    fieldnames = ['ID', 'Flags', 'ModelName', 'SizeClass', 'ModelScale', 'BloodID',
                 'FootprintTextureID', 'FootprintTextureLength', 'FootprintTextureWidth',
                 'FootprintParticleScale', 'FoleyMaterialID', 'FootstepShakeSize',
                 'DeathThudShakeSize', 'SoundID', 'CollisionWidth', 'CollisionHeight',
                 'MountHeight', 'GeoBoxMinX', 'GeoBoxMinY', 'GeoBoxMinZ',
                 'GeoBoxMaxX', 'GeoBoxMaxY', 'GeoBoxMaxZ', 'WorldEffectScale',
                 'AttachedEffectScale', 'MissileCollisionRadius', 'MissileCollisionPush',
                 'MissileCollisionRaise']
    
    if wdbx_format:
        # Convert float fields for WDBX format
        float_fields = ['ModelScale', 'CollisionWidth', 'CollisionHeight', 'MountHeight',
                       'GeoBoxMinX', 'GeoBoxMinY', 'GeoBoxMinZ', 'GeoBoxMaxX', 'GeoBoxMaxY',
                       'GeoBoxMaxZ', 'WorldEffectScale', 'AttachedEffectScale',
                       'MissileCollisionRadius', 'MissileCollisionPush', 'MissileCollisionRaise',
                       'FootprintTextureLength', 'FootprintTextureWidth', 'FootprintParticleScale']
        for entry in model_entries:
            for field in float_fields:
                if field in entry:
                    entry[field] = convert_float_to_wdbx(entry[field])
    
    # Sort by ID
    sorted_entries = sorted(model_entries, key=lambda x: int(x['ID']) if x['ID'].isdigit() else 0)
    
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL if wdbx_format else csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(sorted_entries)

def write_filtered_listfile(output_path, filtered_fileids, listfile_data):
    """
    Write filtered listfile containing only the FileIDs used in the filtered output.
    Format: FileID;Path (semicolon-separated, no WDBX formatting)
    """
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        
        # Sort FileIDs numerically
        sorted_fileids = sorted(filtered_fileids, key=lambda x: int(x) if x.isdigit() else 0)
        
        for file_id in sorted_fileids:
            if file_id in listfile_data:
                file_path = listfile_data[file_id]
                # Normalize path to use backslashes
                normalized_path = file_path.replace('/', '\\')
                writer.writerow([file_id, normalized_path])

def write_creature_model_log(log_path, unmapped_file_ids):
    """
    Write a log file for CreatureModelData entries with unmapped FileDataIDs.
    """
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write("CreatureModelData - Missing Model FileDataID Mappings (FILTERED)\n")
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

def download_sounds(listfile_path, used_fileids):
    """
    Download audio files from Wago.tools using FileDataIDs.
    
    Args:
        listfile_path: Path to the listfile CSV
        used_fileids: Set of FileDataIDs that were used in the filtered output
    """
    print("\n" + "=" * 60)
    print("=== DOWNLOADING SOUNDS ===")
    print("=" * 60)
    
    # Show locale warning
    print("\n" + "=" * 60)
    print("=== IMPORTANT: SOUND LOCALE INFORMATION ===")
    print("=" * 60)
    print()
    print("Downloaded sounds are enUS locale from Wago.tools.")
    print()
    print("Installation paths:")
    print("  • Most sounds → wow\\data\\ (music, creatures, spells, effects)")
    print("  • Locale-specific sounds → wow\\data\\[locale]\\ (character voices, NPC dialogue)")
    print()
    print("CRITICAL: wow\\data has PRIORITY over wow\\data\\[locale]")
    print("If you put locale-specific sounds in wow\\data, they will override any sounds")
    print("in wow\\data\\[locale], causing English audio to play instead of your locale.")
    print()
    print("Note: Cannot automatically determine which sounds are locale-specific.")
    print("For non-enUS locales, use CASC Explorer or wow.export to obtain locale sounds.")
    print("Put localized sounds from Wago.tools in wow\\data\\enUS (or enGB) unless you don't care.")
    print()
    input("Press Enter to continue...")
    print()
    
    # Load audio files from listfile
    print("Loading audio files from listfile...")
    audio_files = {}
    
    with open(listfile_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            if len(row) >= 2:
                file_id = row[0].strip()
                file_path = row[1].strip()
                
                # Check if file has an audio extension
                path_lower = file_path.lower()
                if any(path_lower.endswith(ext) for ext in AUDIO_EXTENSIONS):
                    # Only include files that were actually used
                    if file_id in used_fileids:
                        # Normalize path: replace / with backslash
                        normalized_path = file_path.replace('/', '\\')
                        audio_files[file_id] = normalized_path
    
    if not audio_files:
        print("No audio files found in filtered FileDataIDs")
        return
    
    print(f"Found {len(audio_files)} audio files to download")
    
    # Create download directory
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    # Download each file
    success_count = 0
    fail_count = 0
    failed_files = []
    
    for idx, (file_id, file_path) in enumerate(audio_files.items(), 1):
        # Extract directory and filename
        if '\\' in file_path:
            sound_folder = '\\'.join(file_path.split('\\')[:-1])
            filename = file_path.split('\\')[-1]
        else:
            sound_folder = ""
            filename = file_path
        
        # Create destination directory
        if sound_folder:
            download_destination = os.path.join(DOWNLOAD_DIR, sound_folder)
        else:
            download_destination = DOWNLOAD_DIR
        os.makedirs(download_destination, exist_ok=True)
        
        # Full file path
        output_file = os.path.join(download_destination, filename)
        
        # Skip if file already exists
        if os.path.exists(output_file):
            print(f"[{idx}/{len(audio_files)}] Skipping (exists): {filename}")
            success_count += 1
            continue
        
        # Download from Wago.tools
        url = f'https://wago.tools/api/casc/{file_id}?download'
        
        try:
            print(f"[{idx}/{len(audio_files)}] Downloading: {filename} (FileID: {file_id})")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                with open(output_file, 'wb') as f:
                    f.write(response.content)
                success_count += 1
                print(f"  → Saved to: {output_file}")
            else:
                fail_count += 1
                failed_files.append((file_id, filename, f"HTTP {response.status_code}"))
                print(f"  → FAILED: HTTP {response.status_code}")
        
        except requests.exceptions.RequestException as e:
            fail_count += 1
            failed_files.append((file_id, filename, str(e)))
            print(f"  → FAILED: {e}")
        
        # Small delay to avoid rate limiting
        if idx < len(audio_files):  # Don't delay after last file
            time.sleep(0.1)
    
    # Summary
    print("\n" + "=" * 60)
    print("=== DOWNLOAD SUMMARY ===")
    print("=" * 60)
    print(f"Total files: {len(audio_files)}")
    print(f"Successfully downloaded/verified: {success_count}")
    print(f"Failed: {fail_count}")
    print(f"Download directory: {DOWNLOAD_DIR}")
    
    if failed_files:
        print("\n!!! FAILED DOWNLOADS !!!")
        log_path = "sound_download_failed.log"
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write("Failed sound downloads\n")
            f.write("=" * 60 + "\n\n")
            for file_id, filename, error in failed_files:
                f.write(f"FileID: {file_id}\n")
                f.write(f"Filename: {filename}\n")
                f.write(f"Error: {error}\n")
                f.write("-" * 60 + "\n")
        print(f"Failed downloads logged to: {log_path}")


def load_existing_csv(file_path):
    """Load existing CSV, return list of dicts."""
    if not os.path.exists(file_path):
        return []
    entries = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(row)
    return entries

def merge_csv_entries(existing, new, id_field='ID'):
    """Merge new with existing, skip duplicates."""
    by_id = {e[id_field]: e for e in existing}
    skipped, added = 0, 0
    for entry in new:
        eid = entry[id_field]
        if eid not in by_id:
            by_id[eid] = entry
            added += 1
        else:
            skipped += 1
    merged = sorted(by_id.values(), key=lambda x: int(x[id_field]))
    if skipped > 0:
        print(f"  → Skipped {skipped} duplicate(s), added {added} new")
    return merged

def load_existing_fileids(listfile_path):
    """Load FileDataIDs from filtered listfile."""
    if not os.path.exists(listfile_path):
        return set()
    fileids = set()
    with open(listfile_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            if len(row) >= 1:
                fileids.add(row[0].strip())
    return fileids


def main():
    """
    Main processing function - Filtered version (Steps 1-2)
    """
    print("=" * 60)
    print("=== DB2 TO DBC CONVERTER (FILTERED VERSION) ===")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR}")
    print()
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Ask for append or overwrite mode
    print("=== OUTPUT MODE SELECTION ===")
    append_mode = False
    while True:
        print("Choose output mode:")
        print("  1. Append to existing files (keep previous data)")
        print("  2. Overwrite existing files (fresh start)")
        mode_input = input("Enter choice (1 or 2): ").strip()
        if mode_input == '1':
            append_mode = True
            print("→ Will append to existing files")
            break
        elif mode_input == '2':
            append_mode = False
            print("→ Will overwrite existing files")
            break
        else:
            print("ERROR: Please enter 1 or 2")
    print()
    
    # Ask if user wants to download sounds
    print("=== SOUND DOWNLOAD PREFERENCE ===")
    download_sounds_flag = False
    
    if not REQUESTS_AVAILABLE:
        print("Note: 'requests' library not installed - sound download unavailable")
        print("To enable: pip install requests")
        print()
    else:
        while True:
            download_input = input("Download sounds after processing? (y/n): ").strip().lower()
            if download_input in ['y', 'yes']:
                download_sounds_flag = True
                print("→ Will download sounds after processing completes")
                break
            elif download_input in ['n', 'no']:
                download_sounds_flag = False
                print("→ Will skip sound downloads")
                break
            else:
                print("Please enter 'y' or 'n'")
        print()
    
    # Ask for WDBX format preference
    print("=== FORMAT SELECTION ===")
    while True:
        wdbx_input = input("Format CSV for WDBX Editor? (quotes all fields, converts decimals . to ,) (y/n): ").strip().lower()
        if wdbx_input in ['y', 'yes']:
            wdbx_format = True
            print("Using WDBX format")
            break
        elif wdbx_input in ['n', 'no']:
            wdbx_format = False
            print("Using standard format")
            break
        else:
            print("Please enter 'y' or 'n'")
    print()
    
    # Ask for SoundEntries naming preference
    print("=== SOUNDENTRIES NAMING PREFERENCE ===")
    use_wotlk_names = False
    wotlk_soundentries_path = os.path.join(WOTLK_DIR, "Wotlk_SoundEntries.csv")
    
    if os.path.exists(wotlk_soundentries_path):
        print(f"Detected WotLK SoundEntries file: {wotlk_soundentries_path}")
        print("\nChoose SoundEntries naming method:")
        print("  1. Use WotLK names (where ID matches) + generate from File_1 (for new IDs)")
        print("  2. Generate all names from File_1 (ignore WotLK names)")
        
        while True:
            naming_choice = input("Enter choice (1 or 2): ").strip()
            if naming_choice == '1':
                use_wotlk_names = True
                print("→ Will use WotLK names + generate missing")
                break
            elif naming_choice == '2':
                use_wotlk_names = False
                print("→ Will generate all names from File_1")
                break
            print("ERROR: Please enter 1 or 2")
    else:
        print(f"WotLK SoundEntries file not found at: {wotlk_soundentries_path}")
        print("→ Will generate all names from File_1")
        use_wotlk_names = False
    print()
    
    # STEP 1: Load listfile and prompt for model selection
    print("\n=== STEP 1: MODEL SELECTION ===")
    listfile_path = find_listfile(INPUT_DIR)
    
    if not listfile_path:
        print(f"ERROR: Listfile not found in {INPUT_DIR}")
        return
    
    print(f"Found listfile: {listfile_path}")
    print("Loading listfile...")
    listfile_data = load_listfile(listfile_path)
    print(f"Loaded {len(listfile_data)} file entries")
    
    print("Loading texture files from listfile...")
    texture_files = load_texture_files(listfile_path)
    print(f"Loaded {len(texture_files)} texture files (.blp)")
    
    # Prompt user for model selection
    selected_fileids = prompt_model_selection(listfile_data)
    
    print(f"\nProceeding with {len(selected_fileids)} selected model(s)")
    
    # Track all FileIDs used in filtered output for listfile generation
    if append_mode:
        listfile_output_path = os.path.join(OUTPUT_DIR, "listfile_filtered.csv")
        existing_fileids = load_existing_fileids(listfile_output_path)
        if existing_fileids:
            print(f"→ Append mode: Loaded {len(existing_fileids)} existing FileID(s)")
        used_fileids = existing_fileids | set(selected_fileids)
    else:
        used_fileids = set(selected_fileids)
    
    # Track filtered ModelIDs for CreatureDisplayInfo filtering
    filtered_model_ids = set()
    
    # Track filtered SoundIDs for CreatureSoundData filtering
    filtered_sound_ids = set()
    
    # Track filtered ParticleColorIDs for ParticleColor filtering
    filtered_particle_color_ids = set()
    
    # Track filtered NPCSoundIDs for NPCSounds filtering
    filtered_npc_sound_ids = set()
    
    # Track filtered CreatureFootstepIDs for FootstepTerrainLookup filtering
    filtered_creature_footstep_ids = set()
    
    # Track filtered ObjectEffectPackageIDs for ObjectEffect chain filtering
    filtered_object_effect_package_ids = set()
    
    # STEP 2: Filter and generate CreatureModelData
    print("\n" + "=" * 60)
    print("=== STEP 2: GENERATING CREATUREMODELDATA (FILTERED) ===")
    print("=" * 60)
    
    model_data_path = find_table_file(INPUT_DIR, "CreatureModelData")
    
    if not model_data_path:
        print(f"WARNING: CreatureModelData table not found in {INPUT_DIR}")
        print("Skipping CreatureModelData generation")
    else:
        print(f"Found CreatureModelData: {model_data_path}")
        print("Loading CreatureModelData...")
        model_data = load_creature_model_data(model_data_path)
        print(f"Loaded {len(model_data)} total CreatureModelData entries")
        
        print("\nFiltering CreatureModelData for selected model(s)...")
        filtered_entries, unmapped_file_ids = filter_creature_model_data(model_data, selected_fileids, listfile_data)
        print(f"Filtered to {len(filtered_entries)} entries")
        
        # Collect ModelIDs for CreatureDisplayInfo filtering
        for entry in filtered_entries:
            filtered_model_ids.add(entry['ID'])
            # Collect SoundIDs from CreatureModelData
            sound_id = entry.get('SoundID', '').strip()
            if sound_id and sound_id != '0':
                filtered_sound_ids.add(sound_id)
        
        if unmapped_file_ids:
            log_path = "CreatureModelData_filtered.log"
            write_creature_model_log(log_path, unmapped_file_ids)
            print(f"WARNING: {len(unmapped_file_ids)} entries have unmapped FileDataIDs")
            print(f"Log written to: {log_path}")
        
        if filtered_entries:
            output_path = os.path.join(OUTPUT_DIR, "CreatureModelData.csv")
            write_creature_model_data(output_path, filtered_entries, wdbx_format, append_mode)
            
            if wdbx_format:
                print(f"Wrote CreatureModelData to: {output_path} (WDBX format)")
            else:
                print(f"Wrote CreatureModelData to: {output_path}")
            
            print("\n=== Sample CreatureModelData (first 3) ===")
            for entry in filtered_entries[:3]:
                print(f"ID: {entry['ID']}")
                for key, value in entry.items():
                    if value and key != 'ID':
                        print(f"  {key}: {value}")
                print()
        else:
            print("WARNING: No CreatureModelData entries found for selected model(s)")
    
    # STEP 3: Filter and generate CreatureDisplayInfo
    print("\n" + "=" * 60)
    print("=== STEP 3: GENERATING CREATUREDISPLAYINFO (FILTERED) ===")
    print("=" * 60)
    
    if not filtered_model_ids:
        print("WARNING: No ModelIDs available from CreatureModelData")
        print("Skipping CreatureDisplayInfo generation")
    else:
        display_info_path = find_table_file(INPUT_DIR, "CreatureDisplayInfo")
        
        if not display_info_path:
            print(f"WARNING: CreatureDisplayInfo table not found in {INPUT_DIR}")
            print("Skipping CreatureDisplayInfo generation")
        else:
            print(f"Found CreatureDisplayInfo: {display_info_path}")
            print("Loading CreatureDisplayInfo...")
            creature_display_data = load_creature_display_info(display_info_path)
            print(f"Loaded {len(creature_display_data)} total CreatureDisplayInfo entries")
            
            # Load geoset data
            print("\nLoading CreatureDisplayInfoGeosetData...")
            geoset_path = find_table_file(INPUT_DIR, "CreatureDisplayInfoGeosetData")
            if geoset_path:
                geoset_data = load_creature_display_info_geoset_data(geoset_path)
                print(f"Loaded geoset data for {len(geoset_data)} CreatureDisplayInfo entries")
            else:
                print("WARNING: CreatureDisplayInfoGeosetData not found")
                geoset_data = {}
            
            # Load WotLK BloodLevel data
            print("\nLoading WotLK CreatureDisplayInfo (BloodLevel)...")
            wotlk_display_path = os.path.join(WOTLK_DIR, "CreatureDisplayInfo.csv")
            wotlk_display_data = load_wotlk_creature_display_info(wotlk_display_path)
            if wotlk_display_data:
                print(f"Loaded BloodLevel data for {len(wotlk_display_data)} entries")
            else:
                print("WARNING: WotLK CreatureDisplayInfo not found, using default BloodLevel")
            
            print(f"\nFiltering CreatureDisplayInfo for {len(filtered_model_ids)} ModelID(s)...")
            display_info_entries, unmapped_texture_ids, geoset_overflows = filter_creature_display_info(
                creature_display_data, filtered_model_ids, texture_files, geoset_data, wotlk_display_data, used_fileids
            )
            print(f"Filtered to {len(display_info_entries)} entries")
            
            # Write logs
            if unmapped_texture_ids:
                log_path = "CreatureDisplayInfo_Textures_filtered.log"
                write_creature_display_info_texture_log(log_path, unmapped_texture_ids)
                print(f"WARNING: {len(set(item['ID'] for item in unmapped_texture_ids))} entries have unmapped texture FileDataIDs")
                print(f"Log written to: {log_path}")
            
            if geoset_overflows:
                log_path = "CreatureDisplayInfo_GeosetOverflow_filtered.log"
                write_creature_display_info_geoset_log(log_path, geoset_overflows)
                print(f"WARNING: {len(geoset_overflows)} entries have CreatureGeosetData overflow")
                print(f"Log written to: {log_path}")
            
            if display_info_entries:
                output_path = os.path.join(OUTPUT_DIR, "CreatureDisplayInfo.csv")
                write_creature_display_info(output_path, display_info_entries, wdbx_format, append_mode)
                
                # Collect SoundIDs, ParticleColorIDs, NPCSoundIDs, and ObjectEffectPackageIDs from CreatureDisplayInfo
                for entry in display_info_entries:
                    sound_id = entry.get('SoundID', '').strip()
                    if sound_id and sound_id != '0':
                        filtered_sound_ids.add(sound_id)
                    
                    particle_color_id = entry.get('ParticleColorID', '').strip()
                    if particle_color_id and particle_color_id != '0':
                        filtered_particle_color_ids.add(particle_color_id)
                    
                    npc_sound_id = entry.get('NPCSoundID', '').strip()
                    if npc_sound_id and npc_sound_id != '0':
                        filtered_npc_sound_ids.add(npc_sound_id)
                    
                    object_effect_package_id = entry.get('ObjectEffectPackageID', '').strip()
                    if object_effect_package_id and object_effect_package_id != '0':
                        filtered_object_effect_package_ids.add(object_effect_package_id)
                
                if wdbx_format:
                    print(f"Wrote CreatureDisplayInfo to: {output_path} (WDBX format)")
                else:
                    print(f"Wrote CreatureDisplayInfo to: {output_path}")
                
                print("\n=== Sample CreatureDisplayInfo (first 3) ===")
                for entry in display_info_entries[:3]:
                    print(f"ID: {entry['ID']}")
                    for key, value in entry.items():
                        if value and key != 'ID':
                            print(f"  {key}: {value}")
                    print()
            else:
                print("WARNING: No CreatureDisplayInfo entries found for filtered ModelIDs")
    
    # STEP 4: Filter and generate CreatureSoundData
    print("\n" + "=" * 60)
    print("=== STEP 4: GENERATING CREATURESOUNDDATA (FILTERED) ===")
    print("=" * 60)
    
    if not filtered_sound_ids:
        print("WARNING: No SoundIDs available from CreatureModelData/CreatureDisplayInfo")
        print("Skipping CreatureSoundData generation")
    else:
        sound_data_path = find_table_file(INPUT_DIR, "CreatureSoundData")
        
        if not sound_data_path:
            print(f"WARNING: CreatureSoundData table not found in {INPUT_DIR}")
            print("Skipping CreatureSoundData generation")
        else:
            print(f"Found CreatureSoundData: {sound_data_path}")
            print("Loading CreatureSoundData...")
            creature_sound_data = load_creature_sound_data(sound_data_path)
            print(f"Loaded {len(creature_sound_data)} total CreatureSoundData entries")
            
            print(f"\nFiltering CreatureSoundData for {len(filtered_sound_ids)} SoundID(s)...")
            print("(including CreatureSoundDataIDPet references recursively)")
            sound_data_entries = filter_creature_sound_data(creature_sound_data, filtered_sound_ids)
            print(f"Filtered to {len(sound_data_entries)} entries")
            
            if sound_data_entries:
                output_path = os.path.join(OUTPUT_DIR, "CreatureSoundData.csv")
                write_creature_sound_data(output_path, sound_data_entries, wdbx_format, append_mode)
                
                # Collect NPCSoundIDs and CreatureFootstepIDs from CreatureSoundData
                for entry in sound_data_entries:
                    npc_sound_id = entry.get('NPCSoundID', '').strip()
                    if npc_sound_id and npc_sound_id != '0':
                        filtered_npc_sound_ids.add(npc_sound_id)
                    
                    # SoundFootstepID is CreatureFootstepID in FootstepTerrainLookup
                    footstep_id = entry.get('SoundFootstepID', '').strip()
                    if footstep_id and footstep_id != '0':
                        filtered_creature_footstep_ids.add(footstep_id)
                
                if wdbx_format:
                    print(f"Wrote CreatureSoundData to: {output_path} (WDBX format)")
                else:
                    print(f"Wrote CreatureSoundData to: {output_path}")
                
                print("\n=== Sample CreatureSoundData (first 3) ===")
                for entry in sound_data_entries[:3]:
                    print(f"ID: {entry['ID']}")
                    for key, value in entry.items():
                        if value and key != 'ID':
                            print(f"  {key}: {value}")
                    print()
            else:
                print("WARNING: No CreatureSoundData entries found for filtered SoundIDs")
    
    # STEP 5: Filter and generate ParticleColor
    print("\n" + "=" * 60)
    print("=== STEP 5: GENERATING PARTICLECOLOR (FILTERED) ===")
    print("=" * 60)
    
    if not filtered_particle_color_ids:
        print("WARNING: No ParticleColorIDs available from CreatureDisplayInfo")
        print("Skipping ParticleColor generation")
    else:
        particle_color_path = find_table_file(INPUT_DIR, "ParticleColor")
        
        if not particle_color_path:
            print(f"WARNING: ParticleColor table not found in {INPUT_DIR}")
            print("Skipping ParticleColor generation")
        else:
            print(f"Found ParticleColor: {particle_color_path}")
            print("Loading ParticleColor...")
            particle_color_data = load_particle_color(particle_color_path)
            print(f"Loaded {len(particle_color_data)} total ParticleColor entries")
            
            print(f"\nFiltering ParticleColor for {len(filtered_particle_color_ids)} ParticleColorID(s)...")
            particle_color_entries = filter_particle_color(particle_color_data, filtered_particle_color_ids)
            print(f"Filtered to {len(particle_color_entries)} entries")
            
            if particle_color_entries:
                output_path = os.path.join(OUTPUT_DIR, "ParticleColor.csv")
                write_particle_color(output_path, particle_color_entries, wdbx_format, append_mode)
                
                if wdbx_format:
                    print(f"Wrote ParticleColor to: {output_path} (WDBX format)")
                else:
                    print(f"Wrote ParticleColor to: {output_path}")
                
                print("\n=== Sample ParticleColor (first 3) ===")
                for entry in particle_color_entries[:3]:
                    print(f"ID: {entry['ID']}")
                    for key, value in entry.items():
                        if value and key != 'ID':
                            print(f"  {key}: {value}")
                    print()
            else:
                print("WARNING: No ParticleColor entries found for filtered ParticleColorIDs")
    
    # STEP 6: Filter and generate NPCSounds
    print("\n" + "=" * 60)
    print("=== STEP 6: GENERATING NPCSOUNDS (FILTERED) ===")
    print("=" * 60)
    
    if not filtered_npc_sound_ids:
        print("WARNING: No NPCSoundIDs available from CreatureDisplayInfo/CreatureSoundData")
        print("Skipping NPCSounds generation")
    else:
        npc_sounds_path = find_table_file(INPUT_DIR, "NPCSounds")
        
        if not npc_sounds_path:
            print(f"WARNING: NPCSounds table not found in {INPUT_DIR}")
            print("Skipping NPCSounds generation")
        else:
            print(f"Found NPCSounds: {npc_sounds_path}")
            print("Loading NPCSounds...")
            npc_sounds_data = load_npc_sounds(npc_sounds_path)
            print(f"Loaded {len(npc_sounds_data)} total NPCSounds entries")
            
            print(f"\nFiltering NPCSounds for {len(filtered_npc_sound_ids)} NPCSoundID(s)...")
            npc_sounds_entries = filter_npc_sounds(npc_sounds_data, filtered_npc_sound_ids)
            print(f"Filtered to {len(npc_sounds_entries)} entries")
            
            if npc_sounds_entries:
                output_path = os.path.join(OUTPUT_DIR, "NPCSounds.csv")
                write_npc_sounds(output_path, npc_sounds_entries, wdbx_format, append_mode)
                
                if wdbx_format:
                    print(f"Wrote NPCSounds to: {output_path} (WDBX format)")
                else:
                    print(f"Wrote NPCSounds to: {output_path}")
                
                print("\n=== Sample NPCSounds (first 3) ===")
                for entry in npc_sounds_entries[:3]:
                    print(f"ID: {entry['ID']}")
                    for key, value in entry.items():
                        if value and key != 'ID':
                            print(f"  {key}: {value}")
                    print()
            else:
                print("WARNING: No NPCSounds entries found for filtered NPCSoundIDs")
    
    # STEP 7: Filter and generate FootstepTerrainLookup
    print("\n" + "=" * 60)
    print("=== STEP 7: GENERATING FOOTSTEPTERRAINLOOKUP (FILTERED) ===")
    print("=" * 60)
    
    if not filtered_creature_footstep_ids:
        print("WARNING: No CreatureFootstepIDs available from CreatureSoundData")
        print("Skipping FootstepTerrainLookup generation")
    else:
        footstep_path = find_table_file(INPUT_DIR, "FootstepTerrainLookup")
        
        if not footstep_path:
            print(f"WARNING: FootstepTerrainLookup table not found in {INPUT_DIR}")
            print("Skipping FootstepTerrainLookup generation")
        else:
            print(f"Found FootstepTerrainLookup: {footstep_path}")
            print("Loading FootstepTerrainLookup...")
            footstep_data = load_footstep_terrain_lookup(footstep_path)
            print(f"Loaded {len(footstep_data)} total FootstepTerrainLookup entries")
            
            print(f"\nFiltering FootstepTerrainLookup for {len(filtered_creature_footstep_ids)} CreatureFootstepID(s)...")
            print("(filtering to WotLK-compatible terrain types only)")
            footstep_entries = filter_footstep_terrain_lookup(footstep_data, filtered_creature_footstep_ids, filter_terrain=True)
            print(f"Filtered to {len(footstep_entries)} entries")
            
            if footstep_entries:
                output_path = os.path.join(OUTPUT_DIR, "FootstepTerrainLookup.csv")
                write_footstep_terrain_lookup(output_path, footstep_entries, wdbx_format, append_mode)
                
                if wdbx_format:
                    print(f"Wrote FootstepTerrainLookup to: {output_path} (WDBX format)")
                else:
                    print(f"Wrote FootstepTerrainLookup to: {output_path}")
                
                print("\n=== Sample FootstepTerrainLookup (first 3) ===")
                for entry in footstep_entries[:3]:
                    print(f"ID: {entry['ID']}")
                    for key, value in entry.items():
                        if value and key != 'ID':
                            print(f"  {key}: {value}")
                    print()
            else:
                print("WARNING: No FootstepTerrainLookup entries found for filtered CreatureFootstepIDs")
    
    # STEP 8: Generate ObjectEffect-related tables (ObjectEffect, ObjectEffectGroup, ObjectEffectPackageElem, ObjectEffectPackage)
    print("\n" + "=" * 60)
    print("=== STEP 8: GENERATING OBJECTEFFECT CHAIN (FILTERED) ===")
    print("=" * 60)
    
    if not filtered_object_effect_package_ids:
        print("WARNING: No ObjectEffectPackageIDs available from CreatureDisplayInfo")
        print("Skipping ObjectEffect chain generation")
    else:
        # Step 8a: Load and filter ObjectEffectPackageElem (first pass to get ObjectEffectGroupIDs)
        print("\n--- Step 8a: ObjectEffectPackageElem (first pass) ---")
        package_elem_path = find_table_file(INPUT_DIR, "ObjectEffectPackageElem")
        
        if not package_elem_path:
            print(f"WARNING: ObjectEffectPackageElem table not found in {INPUT_DIR}")
            print("Skipping ObjectEffect chain generation")
        else:
            print(f"Found ObjectEffectPackageElem: {package_elem_path}")
            print("Loading ObjectEffectPackageElem...")
            package_elem_data = load_object_effect_package_elem(package_elem_path)
            print(f"Loaded {len(package_elem_data)} total ObjectEffectPackageElem entries")
            
            # First pass: get ObjectEffectGroupIDs from filtered packages
            print(f"\nFirst pass: collecting ObjectEffectGroupIDs from {len(filtered_object_effect_package_ids)} package(s)...")
            filtered_object_effect_group_ids = set()
            for row in package_elem_data:
                package_id = row.get('objecteffectpackageid', '').strip()
                if package_id in filtered_object_effect_package_ids:
                    group_id = row.get('objecteffectgroupid', '').strip()
                    if group_id and group_id != '0':
                        filtered_object_effect_group_ids.add(group_id)
            
            print(f"Found {len(filtered_object_effect_group_ids)} ObjectEffectGroupID(s)")
            
            if not filtered_object_effect_group_ids:
                print("WARNING: No ObjectEffectGroupIDs found")
                print("Skipping ObjectEffect chain generation")
            else:
                # Step 8b: Load and filter ObjectEffect
                print("\n--- Step 8b: ObjectEffect ---")
                object_effect_path = find_table_file(INPUT_DIR, "ObjectEffect")
                
                if not object_effect_path:
                    print(f"WARNING: ObjectEffect table not found in {INPUT_DIR}")
                    print("Skipping ObjectEffect chain generation")
                else:
                    print(f"Found ObjectEffect: {object_effect_path}")
                    print("Loading ObjectEffect...")
                    object_effect_data = load_object_effect(object_effect_path)
                    print(f"Loaded {len(object_effect_data)} total ObjectEffect entries")
                    
                    print(f"\nFiltering ObjectEffect for {len(filtered_object_effect_group_ids)} ObjectEffectGroupID(s)...")
                    
                    # From SoundEntries to get names for ObjectEffect
                    
                    sound_entries_for_object_effect = []
                    sound_entries_path = os.path.join(OUTPUT_DIR, "SoundEntries.csv")
                    if os.path.exists(sound_entries_path):
                        print("Loading previously generated SoundEntries for ObjectEffect naming...")
                        with open(sound_entries_path, 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                sound_entries_for_object_effect.append({'ID': row['ID'], 'Name': row.get('Name', '')})
                        print(f"Loaded {len(sound_entries_for_object_effect)} SoundEntries")
                    else:
                        print("NOTE: SoundEntries not found, ObjectEffect names will be empty")
                    
                    object_effect_entries, zero_effect_rec_ids = filter_object_effect(
                        object_effect_data, filtered_object_effect_group_ids, sound_entries_for_object_effect
                    )
                    print(f"Filtered to {len(object_effect_entries)} entries")
                    
                    if zero_effect_rec_ids:
                        log_path = "ObjectEffect_filtered.log"
                        write_object_effect_log(log_path, zero_effect_rec_ids)
                        print(f"WARNING: {len(zero_effect_rec_ids)} entries with EffectRecID = 0 were skipped")
                        print(f"Log written to: {log_path}")
                    
                    if object_effect_entries:
                        output_path = os.path.join(OUTPUT_DIR, "ObjectEffect.csv")
                        write_object_effect(output_path, object_effect_entries, wdbx_format, append_mode)
                        
                        if wdbx_format:
                            print(f"Wrote ObjectEffect to: {output_path} (WDBX format)")
                        else:
                            print(f"Wrote ObjectEffect to: {output_path}")
                        
                        print("\n=== Sample ObjectEffect (first 3) ===")
                        for entry in object_effect_entries[:3]:
                            print(f"ID: {entry['ID']}")
                            for key, value in entry.items():
                                if value and key != 'ID':
                                    print(f"  {key}: {value}")
                            print()
                        
                        # Step 8c: Generate ObjectEffectGroup from ObjectEffect entries
                        print("\n--- Step 8c: ObjectEffectGroup ---")
                        print("Generating ObjectEffectGroup from ObjectEffect entries...")
                        object_effect_group_entries = generate_object_effect_group_output(object_effect_entries)
                        print(f"Generated {len(object_effect_group_entries)} ObjectEffectGroup entries")
                        
                        output_path = os.path.join(OUTPUT_DIR, "ObjectEffectGroup.csv")
                        write_object_effect_group(output_path, object_effect_group_entries, wdbx_format, append_mode)
                        
                        if wdbx_format:
                            print(f"Wrote ObjectEffectGroup to: {output_path} (WDBX format)")
                        else:
                            print(f"Wrote ObjectEffectGroup to: {output_path}")
                        
                        print("\n=== Sample ObjectEffectGroup (first 3) ===")
                        for entry in object_effect_group_entries[:3]:
                            print(f"ID: {entry['ID']}")
                            for key, value in entry.items():
                                if value and key != 'ID':
                                    print(f"  {key}: {value}")
                            print()
                        
                        # Step 8d: Filter ObjectEffectPackageElem (second pass with validation)
                        print("\n--- Step 8d: ObjectEffectPackageElem (second pass with validation) ---")
                        print(f"Filtering ObjectEffectPackageElem for {len(filtered_object_effect_package_ids)} package(s)...")
                        print("Validating against ObjectEffectGroup entries...")
                        package_elem_entries, skipped_package_ids, final_group_ids = filter_object_effect_package_elem(
                            package_elem_data, filtered_object_effect_package_ids, object_effect_group_entries
                        )
                        print(f"Filtered to {len(package_elem_entries)} entries")
                        
                        if skipped_package_ids:
                            log_path = "ObjectEffectPackageElem_filtered.log"
                            write_object_effect_package_elem_log(log_path, skipped_package_ids)
                            print(f"WARNING: {len(skipped_package_ids)} entries with invalid ObjectEffectGroupID were skipped")
                            print(f"Log written to: {log_path}")
                        
                        if package_elem_entries:
                            output_path = os.path.join(OUTPUT_DIR, "ObjectEffectPackageElem.csv")
                            write_object_effect_package_elem(output_path, package_elem_entries, wdbx_format, append_mode)
                            
                            if wdbx_format:
                                print(f"Wrote ObjectEffectPackageElem to: {output_path} (WDBX format)")
                            else:
                                print(f"Wrote ObjectEffectPackageElem to: {output_path}")
                            
                            print("\n=== Sample ObjectEffectPackageElem (first 3) ===")
                            for entry in package_elem_entries[:3]:
                                print(f"ID: {entry['ID']}")
                                for key, value in entry.items():
                                    if value and key != 'ID':
                                        print(f"  {key}: {value}")
                                print()
                            
                            # Step 8e: Generate ObjectEffectPackage from ObjectEffectPackageElem
                            print("\n--- Step 8e: ObjectEffectPackage ---")
                            print("Generating ObjectEffectPackage from ObjectEffectPackageElem entries...")
                            package_entries = generate_object_effect_package_output(package_elem_entries, object_effect_group_entries)
                            print(f"Generated {len(package_entries)} ObjectEffectPackage entries")
                            
                            output_path = os.path.join(OUTPUT_DIR, "ObjectEffectPackage.csv")
                            write_object_effect_package(output_path, package_entries, wdbx_format, append_mode)
                            
                            if wdbx_format:
                                print(f"Wrote ObjectEffectPackage to: {output_path} (WDBX format)")
                            else:
                                print(f"Wrote ObjectEffectPackage to: {output_path}")
                            
                            print("\n=== Sample ObjectEffectPackage (first 3) ===")
                            for entry in package_entries[:3]:
                                print(f"ID: {entry['ID']}")
                                for key, value in entry.items():
                                    if value and key != 'ID':
                                        print(f"  {key}: {value}")
                                print()
                        else:
                            print("WARNING: No valid ObjectEffectPackageElem entries after validation")
                    else:
                        print("WARNING: No ObjectEffect entries found for filtered ObjectEffectGroupIDs")
    
    # STEP 9: Generate SoundEntries
    print("\n" + "=" * 60)
    print("=== STEP 9: GENERATING SOUNDENTRIES (FILTERED) ===")
    print("=" * 60)
    
    # Collect all SoundKit IDs from generated filtered files
    print("Collecting SoundKit IDs from generated files...")
    filtered_soundkit_ids = set()
    
    # Check for M2 hardcoded SoundEntry IDs
    m2_hardcoded_dir = "4_M2_Hardcoded_SoundEntry_ID"
    m2_hardcoded_file = os.path.join(m2_hardcoded_dir, "M2_Hardcoded_SoundEntry_ID.csv")
    m2_soundentry_ids = set()
    
    if os.path.exists(m2_hardcoded_file):
        print(f"\n  Detected M2 hardcoded SoundEntry IDs: {m2_hardcoded_file}")
        print("  Loading hardcoded SoundEntry IDs from M2 files...")
        with open(m2_hardcoded_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sound_entry_id = row.get('SoundEntryID', '').strip()
                if sound_entry_id and sound_entry_id != '0':
                    m2_soundentry_ids.add(sound_entry_id)
        print(f"  Found {len(m2_soundentry_ids)} unique SoundEntry IDs from M2 files: {sorted(m2_soundentry_ids)}")
        
        # These are SoundEntry IDs, we need to find corresponding SoundKit IDs
        # We'll use them directly as IDs since SoundEntry ID = SoundKit ID in the retail-to-wotlk conversion
        print("  Adding as SoundKit IDs for processing...")
        for sound_id in m2_soundentry_ids:
            filtered_soundkit_ids.add(sound_id)
        print(f"  Added {len(m2_soundentry_ids)} SoundKit IDs from M2 hardcoded sounds")
    else:
        print(f"\n  No M2 hardcoded SoundEntry IDs found (checked: {m2_hardcoded_file})")
        print("  Tip: Run m2_Hardcoded_SoundEntry_ID_extractor.py first to extract hardcoded sounds from .m2 files")
    
    # From CreatureSoundData
    creature_sound_path = os.path.join(OUTPUT_DIR, "CreatureSoundData.csv")
    if os.path.exists(creature_sound_path):
        with open(creature_sound_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            sound_fields = ['SoundExertionID', 'SoundExertionCriticalID', 'SoundInjuryID', 
                          'SoundInjuryCriticalID', 'SoundInjuryCrushingBlowID', 'SoundDeathID',
                          'SoundStunID', 'SoundStandID', 'SoundAggroID', 'SoundWingFlapID',
                          'SoundWingGlideID', 'SoundAlertID', 'SoundFidget_1', 'SoundFidget_2',
                          'SoundFidget_3', 'SoundFidget_4', 'SoundFidget_5', 'CustomAttack_1',
                          'CustomAttack_2', 'CustomAttack_3', 'CustomAttack_4', 'LoopSoundID',
                          'SoundJumpStartID', 'SoundJumpEndID', 'SoundPetAttackID', 'SoundPetOrderID',
                          'SoundPetDismissID', 'BirthSoundID', 'SpellCastDirectedSoundID',
                          'SubmergeSoundID', 'SubmergedSoundID']
            for row in reader:
                for field in sound_fields:
                    sound_id = row.get(field, '').strip()
                    if sound_id and sound_id != '0':
                        filtered_soundkit_ids.add(sound_id)
        print(f"  Collected from CreatureSoundData")
    
    # From FootstepTerrainLookup
    footstep_path = os.path.join(OUTPUT_DIR, "FootstepTerrainLookup.csv")
    if os.path.exists(footstep_path):
        with open(footstep_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                sound_id = row.get('SoundID', '').strip()
                if sound_id and sound_id != '0':
                    filtered_soundkit_ids.add(sound_id)
                sound_id_splash = row.get('SoundIDSplash', '').strip()
                if sound_id_splash and sound_id_splash != '0':
                    filtered_soundkit_ids.add(sound_id_splash)
        print(f"  Collected from FootstepTerrainLookup")
    
    # From NPCSounds
    npc_sounds_path = os.path.join(OUTPUT_DIR, "NPCSounds.csv")
    if os.path.exists(npc_sounds_path):
        with open(npc_sounds_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                for i in range(1, 5):
                    sound_id = row.get(f'SoundID_{i}', '').strip()
                    if sound_id and sound_id != '0':
                        filtered_soundkit_ids.add(sound_id)
        print(f"  Collected from NPCSounds")
    
    # From ObjectEffect
    object_effect_path = os.path.join(OUTPUT_DIR, "ObjectEffect.csv")
    if os.path.exists(object_effect_path):
        with open(object_effect_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                effect_rec_id = row.get('EffectRecID', '').strip()
                if effect_rec_id and effect_rec_id != '0':
                    filtered_soundkit_ids.add(effect_rec_id)
        print(f"  Collected from ObjectEffect")
    
    print(f"\nTotal SoundKit IDs collected: {len(filtered_soundkit_ids)}")
    
    if not filtered_soundkit_ids:
        print("WARNING: No SoundKit IDs found to generate SoundEntries")
        print("Skipping SoundEntries generation")
    else:
        # Load SoundKitEntry data
        print("\nLoading SoundKitEntry...")
        soundkit_entry_path = find_table_file(INPUT_DIR, "SoundKitEntry")
        if not soundkit_entry_path:
            print(f"WARNING: SoundKitEntry table not found in {INPUT_DIR}")
            print("Skipping SoundEntries generation")
        else:
            print(f"Found SoundKitEntry: {soundkit_entry_path}")
            soundkit_data_full = load_soundkit_entries(soundkit_entry_path)
            
            # Filter SoundKitEntry data
            print(f"Filtering SoundKitEntry for {len(filtered_soundkit_ids)} SoundKit IDs...")
            filtered_soundkit_data = {}
            for soundkit_id, entries in soundkit_data_full.items():
                if soundkit_id in filtered_soundkit_ids:
                    filtered_soundkit_data[soundkit_id] = entries
            
            print(f"Filtered to {len(filtered_soundkit_data)} SoundKit groups")
            
            # Load SoundKit table for enrichment
            print("\nLoading SoundKit table for enrichment...")
            soundkit_table_path = find_table_file(INPUT_DIR, "SoundKit")
            if soundkit_table_path:
                print(f"Found SoundKit: {soundkit_table_path}")
                soundkit_table_data = load_soundkit_table(soundkit_table_path)
                print(f"Loaded {len(soundkit_table_data)} SoundKit entries")
            else:
                print("WARNING: SoundKit table not found, using defaults")
                soundkit_table_data = {}
            
            # Load audio files (already loaded earlier)
            print("\nUsing previously loaded audio files from listfile")
            audio_files = load_audio_files(listfile_path)
            print(f"Audio files available: {len(audio_files)}")
            
            # Generate SoundEntries
            print("\nGenerating SoundEntries...")
            sound_entries, missing_soundkit_ids = generate_sound_entries(
                filtered_soundkit_data, audio_files, soundkit_table_data
            )
            print(f"Generated {len(sound_entries)} SoundEntries")
            
            if missing_soundkit_ids:
                print(f"WARNING: {len(missing_soundkit_ids)} SoundKit IDs missing from SoundKit table (using defaults)")
            
            # Load WotLK SoundEntries for naming (if user chose to use them)
            if use_wotlk_names:
                print("\nLoading WotLK SoundEntries for naming...")
                wotlk_soundentries_path = os.path.join(WOTLK_DIR, "Wotlk_SoundEntries.csv")
                if os.path.exists(wotlk_soundentries_path):
                    wotlk_names = load_wotlk_soundentries(wotlk_soundentries_path)
                    print(f"Loaded {len(wotlk_names)} WotLK names")
                    
                    # Apply names
                    print("Applying names to SoundEntries...")
                    sound_entries = apply_names(sound_entries, use_wotlk=True, wotlk_names=wotlk_names)
                else:
                    print(f"WARNING: WotLK SoundEntries not found at {wotlk_soundentries_path}")
                    print("Generating names from File_1 only...")
                    sound_entries = apply_names(sound_entries, use_wotlk=False, wotlk_names={})
            else:
                print("\nGenerating all names from File_1...")
                sound_entries = apply_names(sound_entries, use_wotlk=False, wotlk_names={})
            
            # Write SoundEntries
            output_path = os.path.join(OUTPUT_DIR, "SoundEntries.csv")
            write_sound_entries(output_path, sound_entries, wdbx_format, append_mode)
            
            # Collect audio FileIDs for filtered listfile
            print("\nCollecting audio FileIDs from SoundEntries for filtered listfile...")
            for entry in sound_entries:
                # Collect FileDataIDs from File_1 through File_10
                for i in range(1, 11):
                    file_value = entry.get(f'File_{i}', '').strip()
                    if file_value:
                        # Check if it's a numeric FileID (unmapped) or a path
                        if file_value.isdigit():
                            # It's an unmapped FileID, add it
                            used_fileids.add(file_value)
                        else:
                            # It's a path, need to find its FileID from audio_files
                            # Reconstruct full path if needed
                            directory_base = entry.get('DirectoryBase', '').strip()
                            if directory_base:
                                full_path = directory_base + '\\' + file_value
                            else:
                                full_path = file_value
                            
                            # Find FileID for this path
                            for file_id, file_path in audio_files.items():
                                if file_path == full_path:
                                    used_fileids.add(file_id)
                                    break
            
            print(f"Added audio FileIDs, total FileIDs for listfile: {len(used_fileids)}")
            
            if wdbx_format:
                print(f"Wrote SoundEntries to: {output_path} (WDBX format)")
            else:
                print(f"Wrote SoundEntries to: {output_path}")
            
            print("\n=== Sample SoundEntries (first 3) ===")
            for entry in sound_entries[:3]:
                print(f"ID: {entry['ID']}")
                for key, value in entry.items():
                    if value and key != 'ID':
                        print(f"  {key}: {value}")
                print()
            
            # STEP 9.5: Update ObjectEffect names now that SoundEntries exists
            print("\n" + "=" * 60)
            print("=== UPDATING OBJECTEFFECT NAMES ===")
            print("=" * 60)
            
            object_effect_path = os.path.join(OUTPUT_DIR, "ObjectEffect.csv")
            if os.path.exists(object_effect_path):
                print("Updating ObjectEffect with SoundEntries names...")
                
                # Create name lookup from sound_entries
                sound_name_lookup = {entry['ID']: entry.get('Name', '') for entry in sound_entries}
                
                # Read ObjectEffect
                updated_object_effects = []
                with open(object_effect_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        effect_rec_id = row.get('EffectRecID', '').strip()
                        if effect_rec_id in sound_name_lookup:
                            row['Name'] = sound_name_lookup[effect_rec_id]
                        updated_object_effects.append(row)
                
                # Write back ObjectEffect with names
                write_object_effect(object_effect_path, updated_object_effects, wdbx_format, append_mode)
                print(f"Updated {len(updated_object_effects)} ObjectEffect entries with names")
                
                # Update ObjectEffectGroup names based on updated ObjectEffect
                print("Updating ObjectEffectGroup names...")
                group_names = {}
                for effect in updated_object_effects:
                    group_id = effect.get('ObjectEffectGroupID', '').strip()
                    name = effect.get('Name', '').strip()
                    if group_id and name and group_id not in group_names:
                        group_names[group_id] = name
                
                # Read and update ObjectEffectGroup
                object_effect_group_path = os.path.join(OUTPUT_DIR, "ObjectEffectGroup.csv")
                if os.path.exists(object_effect_group_path):
                    updated_groups = []
                    with open(object_effect_group_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            group_id = row.get('ID', '').strip()
                            if group_id in group_names:
                                row['Name'] = group_names[group_id]
                            updated_groups.append(row)
                    
                    # Write back ObjectEffectGroup
                    write_object_effect_group(object_effect_group_path, updated_groups, wdbx_format, append_mode)
                    print(f"Updated {len(updated_groups)} ObjectEffectGroup entries with names")
                
                # Update ObjectEffectPackage names based on updated ObjectEffectGroup
                print("Updating ObjectEffectPackage names...")
                object_effect_package_path = os.path.join(OUTPUT_DIR, "ObjectEffectPackage.csv")
                if os.path.exists(object_effect_package_path):
                    updated_packages = []
                    with open(object_effect_package_path, 'r', encoding='utf-8') as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            # Names come from groups, which we just updated
                            updated_packages.append(row)
                    
                    # Regenerate names from updated groups
                    package_elem_path = os.path.join(OUTPUT_DIR, "ObjectEffectPackageElem.csv")
                    if os.path.exists(package_elem_path):
                        package_names = {}
                        with open(package_elem_path, 'r', encoding='utf-8') as f:
                            reader = csv.DictReader(f)
                            for row in reader:
                                package_id = row.get('ObjectEffectPackageID', '').strip()
                                group_id = row.get('ObjectEffectGroupID', '').strip()
                                if package_id and group_id in group_names:
                                    if package_id not in package_names:
                                        package_names[package_id] = group_names[group_id]
                        
                        # Update package names
                        for pkg in updated_packages:
                            pkg_id = pkg.get('ID', '').strip()
                            if pkg_id in package_names:
                                pkg['Name'] = package_names[pkg_id]
                        
                        write_object_effect_package(object_effect_package_path, updated_packages, wdbx_format, append_mode)
                        print(f"Updated {len(updated_packages)} ObjectEffectPackage entries with names")
                
                print("ObjectEffect chain names updated successfully!")
            else:
                print("NOTE: ObjectEffect.csv not found, skipping name update")
            
            # STEP 10: Generate SoundEntriesAdvanced
            print("\n" + "=" * 60)
            print("=== STEP 10: GENERATING SOUNDENTRIESADVANCED (FILTERED) ===")
            print("=" * 60)
            
            # Collect SoundEntriesAdvancedIDs from SoundEntries
            print("Collecting SoundEntriesAdvancedIDs from SoundEntries...")
            filtered_advanced_ids = set()
            for entry in sound_entries:
                advanced_id = entry.get('SoundEntriesAdvancedID', '').strip()
                if advanced_id and advanced_id != '0':
                    filtered_advanced_ids.add(advanced_id)
            
            print(f"Found {len(filtered_advanced_ids)} SoundEntriesAdvancedID(s)")
            
            if not filtered_advanced_ids:
                print("WARNING: No SoundEntriesAdvancedIDs found in SoundEntries")
                print("Skipping SoundEntriesAdvanced generation")
            else:
                # Load SoundKitAdvanced
                soundkit_advanced_path = find_table_file(INPUT_DIR, "SoundKitAdvanced")
                
                if not soundkit_advanced_path:
                    print(f"WARNING: SoundKitAdvanced table not found in {INPUT_DIR}")
                    print("Skipping SoundEntriesAdvanced generation")
                else:
                    print(f"Found SoundKitAdvanced: {soundkit_advanced_path}")
                    print("Loading SoundKitAdvanced...")
                    soundkit_advanced_data = load_soundkit_advanced(soundkit_advanced_path)
                    print(f"Loaded {len(soundkit_advanced_data)} total SoundKitAdvanced entries")
                    
                    print(f"\nFiltering SoundEntriesAdvanced for {len(filtered_advanced_ids)} ID(s)...")
                    print(f"SoundEntries available for naming: {len(sound_entries)}")
                    
                    # Debug: Show sample SoundEntries IDs
                    sample_sound_ids = [e['ID'] for e in sound_entries[:5]]
                    print(f"Sample SoundEntries IDs: {sample_sound_ids}")
                    
                    advanced_entries = filter_sound_entries_advanced(
                        soundkit_advanced_data, filtered_advanced_ids, sound_entries
                    )
                    print(f"Filtered to {len(advanced_entries)} entries")
                    
                    if advanced_entries:
                        output_path = os.path.join(OUTPUT_DIR, "SoundEntriesAdvanced.csv")
                        write_sound_entries_advanced(output_path, advanced_entries, wdbx_format, append_mode)
                        
                        if wdbx_format:
                            print(f"Wrote SoundEntriesAdvanced to: {output_path} (WDBX format)")
                        else:
                            print(f"Wrote SoundEntriesAdvanced to: {output_path}")
                        
                        print("\n=== Sample SoundEntriesAdvanced (first 3) ===")
                        for entry in advanced_entries[:3]:
                            print(f"ID: {entry['ID']}")
                            for key, value in entry.items():
                                if value and key != 'ID':
                                    print(f"  {key}: {value}")
                            print()
                    else:
                        print("WARNING: No SoundEntriesAdvanced entries found for filtered IDs")
    
    # STEP 11: Generate ObjectEffectModifier
    print("\n" + "=" * 60)
    print("=== STEP 11: GENERATING OBJECTEFFECTMODIFIER (FILTERED) ===")
    print("=" * 60)
    
    # Collect ObjectEffectModifierIDs from ObjectEffect
    print("Collecting ObjectEffectModifierIDs from ObjectEffect...")
    filtered_modifier_ids = set()
    
    object_effect_path = os.path.join(OUTPUT_DIR, "ObjectEffect.csv")
    if os.path.exists(object_effect_path):
        with open(object_effect_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                modifier_id = row.get('ObjectEffectModifierID', '').strip()
                if modifier_id and modifier_id != '0':
                    filtered_modifier_ids.add(modifier_id)
        print(f"  Collected from ObjectEffect")
    
    print(f"\nTotal ObjectEffectModifierIDs collected: {len(filtered_modifier_ids)}")
    
    if not filtered_modifier_ids:
        print("WARNING: No ObjectEffectModifierIDs found in ObjectEffect")
        print("Skipping ObjectEffectModifier generation")
    else:
        # Load ObjectEffectModifier
        modifier_path = find_table_file(INPUT_DIR, "ObjectEffectModifier")
        
        if not modifier_path:
            print(f"WARNING: ObjectEffectModifier table not found in {INPUT_DIR}")
            print("Skipping ObjectEffectModifier generation")
        else:
            print(f"Found ObjectEffectModifier: {modifier_path}")
            print("Loading ObjectEffectModifier...")
            modifier_data = load_object_effect_modifier(modifier_path)
            print(f"Loaded {len(modifier_data)} total ObjectEffectModifier entries")
            
            print(f"\nFiltering ObjectEffectModifier for {len(filtered_modifier_ids)} ID(s)...")
            modifier_entries = filter_object_effect_modifier(modifier_data, filtered_modifier_ids)
            print(f"Filtered to {len(modifier_entries)} entries")
            
            if modifier_entries:
                output_path = os.path.join(OUTPUT_DIR, "ObjectEffectModifier.csv")
                write_object_effect_modifier(output_path, modifier_entries, wdbx_format, append_mode)
                
                if wdbx_format:
                    print(f"Wrote ObjectEffectModifier to: {output_path} (WDBX format)")
                else:
                    print(f"Wrote ObjectEffectModifier to: {output_path}")
                
                print("\n=== Sample ObjectEffectModifier (first 3) ===")
                for entry in modifier_entries[:3]:
                    print(f"ID: {entry['ID']}")
                    for key, value in entry.items():
                        if value and key != 'ID':
                            print(f"  {key}: {value}")
                    print()
            else:
                print("WARNING: No ObjectEffectModifier entries found for filtered IDs")
    
    # Generate filtered listfile
    print("\n" + "=" * 60)
    print("=== GENERATING FILTERED LISTFILE ===")
    print("=" * 60)
    
    listfile_output_path = os.path.join(OUTPUT_DIR, "listfile_filtered.csv")
    write_filtered_listfile(listfile_output_path, used_fileids, listfile_data)
    print(f"Wrote filtered listfile with {len(used_fileids)} entries to: {listfile_output_path}")
    
    print("\n" + "=" * 60)
    print("=== PROCESSING COMPLETE (STEPS 1-11) ===")
    print("=" * 60)
    
    # Show all generated files
    print("\n=== GENERATED FILES ===")
    generated_files = []
    
    # Check for CSV files in output directory
    if os.path.exists(os.path.join(OUTPUT_DIR, "CreatureModelData.csv")):
        generated_files.append(os.path.join(OUTPUT_DIR, "CreatureModelData.csv"))
    if os.path.exists(os.path.join(OUTPUT_DIR, "CreatureDisplayInfo.csv")):
        generated_files.append(os.path.join(OUTPUT_DIR, "CreatureDisplayInfo.csv"))
    if os.path.exists(os.path.join(OUTPUT_DIR, "CreatureSoundData.csv")):
        generated_files.append(os.path.join(OUTPUT_DIR, "CreatureSoundData.csv"))
    if os.path.exists(os.path.join(OUTPUT_DIR, "ParticleColor.csv")):
        generated_files.append(os.path.join(OUTPUT_DIR, "ParticleColor.csv"))
    if os.path.exists(os.path.join(OUTPUT_DIR, "NPCSounds.csv")):
        generated_files.append(os.path.join(OUTPUT_DIR, "NPCSounds.csv"))
    if os.path.exists(os.path.join(OUTPUT_DIR, "FootstepTerrainLookup.csv")):
        generated_files.append(os.path.join(OUTPUT_DIR, "FootstepTerrainLookup.csv"))
    if os.path.exists(os.path.join(OUTPUT_DIR, "ObjectEffect.csv")):
        generated_files.append(os.path.join(OUTPUT_DIR, "ObjectEffect.csv"))
    if os.path.exists(os.path.join(OUTPUT_DIR, "ObjectEffectGroup.csv")):
        generated_files.append(os.path.join(OUTPUT_DIR, "ObjectEffectGroup.csv"))
    if os.path.exists(os.path.join(OUTPUT_DIR, "ObjectEffectPackageElem.csv")):
        generated_files.append(os.path.join(OUTPUT_DIR, "ObjectEffectPackageElem.csv"))
    if os.path.exists(os.path.join(OUTPUT_DIR, "ObjectEffectPackage.csv")):
        generated_files.append(os.path.join(OUTPUT_DIR, "ObjectEffectPackage.csv"))
    if os.path.exists(os.path.join(OUTPUT_DIR, "ObjectEffectModifier.csv")):
        generated_files.append(os.path.join(OUTPUT_DIR, "ObjectEffectModifier.csv"))
    if os.path.exists(os.path.join(OUTPUT_DIR, "SoundEntries.csv")):
        generated_files.append(os.path.join(OUTPUT_DIR, "SoundEntries.csv"))
    if os.path.exists(os.path.join(OUTPUT_DIR, "SoundEntriesAdvanced.csv")):
        generated_files.append(os.path.join(OUTPUT_DIR, "SoundEntriesAdvanced.csv"))
    if os.path.exists(listfile_output_path):
        generated_files.append(listfile_output_path)
    
    if generated_files:
        print("The following files were generated:")
        for file in generated_files:
            print(f"  - {file}")
    else:
        print("No files were generated.")
    
    # Show generated log files summary
    log_files = []
    if os.path.exists("CreatureModelData_filtered.log"):
        log_files.append("CreatureModelData_filtered.log")
    if os.path.exists("CreatureDisplayInfo_Textures_filtered.log"):
        log_files.append("CreatureDisplayInfo_Textures_filtered.log")
    if os.path.exists("CreatureDisplayInfo_GeosetOverflow_filtered.log"):
        log_files.append("CreatureDisplayInfo_GeosetOverflow_filtered.log")
    if os.path.exists("ObjectEffect_filtered.log"):
        log_files.append("ObjectEffect_filtered.log")
    if os.path.exists("ObjectEffectPackageElem_filtered.log"):
        log_files.append("ObjectEffectPackageElem_filtered.log")
    
    if log_files:
        print("\n!!! ATTENTION: Log files generated !!!")
        print("The following log files contain unmapped FileDataIDs that need manual correction:")
        for log_file in log_files:
            print(f"  - {log_file}")
        print("\nPlease review these logs to identify missing entries in the listfile.")
    else:
        print("\nNo issues found - all FileDataIDs were successfully mapped!")
    
    # Download sounds if requested
    if download_sounds_flag:
        download_sounds(listfile_path, used_fileids)
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()