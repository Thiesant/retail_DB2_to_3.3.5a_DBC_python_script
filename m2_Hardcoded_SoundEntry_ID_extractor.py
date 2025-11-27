#!/usr/bin/env python3
"""
M2 Sound Event Extractor for WoW 3.3.5a and Legion+
Extracts hardcoded SoundEntry IDs from .m2 files
Supports both MD20 (pre-Legion) and MD21 (Legion+) formats

Credits:
    This script's M2 format parsing is based on the 010 Editor M2.bt template
    maintained by Alastor Strix'Efuartus. The template provided essential 
    insights into the M2 file structure, header offsets, and event definitions
    that made this extraction tool possible.
"""

import struct
import os
import sys
from typing import List, Dict, Tuple, Optional


class M2SoundEvent:
    """Represents a sound event from M2 file"""
    def __init__(self, identifier: str, sound_entry_id: int, parent_bone: int, 
                 position: Tuple[float, float, float], file_offset: int):
        self.identifier = identifier
        self.sound_entry_id = sound_entry_id
        self.parent_bone = parent_bone
        self.position = position
        self.file_offset = file_offset
    
    def __repr__(self):
        return (f"M2SoundEvent(identifier='{self.identifier}', "
                f"sound_entry_id={self.sound_entry_id}, "
                f"parent_bone={self.parent_bone}, "
                f"position={self.position})")


class M2Parser:
    """
    Parser for WoW M2 (model) files
    Supports both MD20 (pre-Legion) and MD21 (Legion+) formats
    """
    
    # Sound event identifiers we're interested in
    SOUND_EVENT_IDS = ['$CSD', '$DSL', '$DSO', '$SND']
    
    # Class variable to track MD21 detections
    md21_detected_files = []
    
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.data = None
        self.is_chunked = False  # MD21 (Legion+) vs MD20 (pre-Legion)
        self.version = 0
        
    def load(self) -> bool:
        """Load M2 file into memory"""
        try:
            with open(self.filepath, 'rb') as f:
                self.data = f.read()
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False
    
    def read_uint32(self, offset: int) -> int:
        """Read uint32 at offset"""
        return struct.unpack('<I', self.data[offset:offset+4])[0]
    
    def read_int32(self, offset: int) -> int:
        """Read int32 at offset"""
        return struct.unpack('<i', self.data[offset:offset+4])[0]
    
    def read_uint16(self, offset: int) -> int:
        """Read uint16 at offset"""
        return struct.unpack('<H', self.data[offset:offset+2])[0]
    
    def read_int16(self, offset: int) -> int:
        """Read int16 at offset"""
        return struct.unpack('<h', self.data[offset:offset+2])[0]
    
    def read_float(self, offset: int) -> float:
        """Read float at offset"""
        return struct.unpack('<f', self.data[offset:offset+4])[0]
    
    def read_string(self, offset: int, length: int) -> str:
        """Read string at offset"""
        return self.data[offset:offset+length].decode('ascii', errors='ignore')
    
    def parse_header(self) -> Optional[Tuple[int, int]]:
        """Parse M2 header to get Events array info"""
        if len(self.data) < 8:
            print("File too small to be valid M2")
            return None
        
        # Read magic
        magic = self.read_string(0, 4)
        if magic not in ['MD20', 'MD21']:
            print(f"Invalid M2 magic: {magic}")
            return None
        
        self.is_chunked = (magic == 'MD21')
        
        # Read version
        self.version = self.read_uint32(4)
        
        print(f"Format: {magic}, Version: {self.version}, Chunked: {self.is_chunked}")
        
        # Warn if MD21 detected
        if self.is_chunked:
            print("    WARNING: MD21 format detected!")
            print("    This is either:")
            print("    1. A Legion+ (7.0+) model")
            print("    2. A fucked up downport of a 3.3.5a .m2 file")
            print()
            # Track MD21 file
            M2Parser.md21_detected_files.append(self.filepath)
        
        # MD21 (Legion+) has an 8-byte chunk header before the actual MD20 data
        # MD20 (pre-Legion) data starts immediately at offset 0
        chunk_offset = 8 if self.is_chunked else 0
        
        # Events are at:
        # nEvents at offset 0x100 + chunk_offset
        # ofsEvents at offset 0x104 + chunk_offset
        events_count_offset = 0x100 + chunk_offset
        events_offset_offset = 0x104 + chunk_offset
        
        if len(self.data) < events_offset_offset + 4:
            print("File too small to contain Events array")
            return None
        
        events_count = self.read_uint32(events_count_offset)
        events_offset = self.read_uint32(events_offset_offset)
        
        # For MD21, the events_offset is relative to the chunk, so add chunk_offset
        if self.is_chunked:
            events_offset += chunk_offset
        
        return (events_count, events_offset)
    
    def calculate_m2track_size(self, offset: int) -> int:
        """
        Return M2Track structure size for Event Timer field.
        
        The M2Track in Events is always 12 bytes for ALL formats (MD20 and MD21):
        - uint16 interpolation_type (2 bytes)
        - int16 global_sequence (2 bytes)
        - uint32 nTimestampPairs (4 bytes)
        - uint32 ofsTimestampPairs (4 bytes)
        Total: 2 + 2 + 4 + 4 = 12 bytes
        
        This gives total Event structure size of 36 bytes:
        - 24 bytes (Identifier + Data + ParentBone + Position)
        - 12 bytes (M2Track Timer)
        
        The actual timestamp DATA is stored elsewhere (referenced by ofsTimestampPairs),
        not inline in the Event structure.
        """
        return 12  # Always 12 bytes for Event Timer
    
    def parse_event(self, offset: int) -> Optional[Dict]:
        """Parse a single event structure"""
        try:
            # Read identifier (4 bytes)
            identifier = self.read_string(offset, 4)
            
            # Read data (uint32) - this is the SoundEntryID for sound events
            data = self.read_uint32(offset + 4)
            
            # Read parent bone (uint32)
            parent_bone = self.read_uint32(offset + 8)
            
            # Read position (3 floats = 12 bytes)
            pos_x = self.read_float(offset + 12)
            pos_y = self.read_float(offset + 16)
            pos_z = self.read_float(offset + 20)
            
            # Calculate M2Track size (starts at offset + 24)
            m2track_size = self.calculate_m2track_size(offset + 24)
            
            # Total event size
            event_size = 24 + m2track_size  # 24 bytes before M2Track + M2Track size
            
            return {
                'identifier': identifier,
                'data': data,
                'parent_bone': parent_bone,
                'position': (pos_x, pos_y, pos_z),
                'offset': offset,
                'size': event_size
            }
        except Exception as e:
            print(f"Error parsing event at offset {hex(offset)}: {e}")
            return None
    
    def extract_sound_events(self) -> List[M2SoundEvent]:
        """Extract all sound events from M2 file"""
        sound_events = []
        
        # Parse header to get Events array
        header_info = self.parse_header()
        if not header_info:
            return sound_events
        
        events_count, events_offset = header_info
        
        if events_count == 0:
            print(f"No events found in {os.path.basename(self.filepath)}")
            return sound_events
        
        print(f"Found {events_count} total events at offset {hex(events_offset)}")
        
        # Parse each event
        current_offset = events_offset
        for i in range(events_count):
            event = self.parse_event(current_offset)
            if not event:
                break
            
            # Check if this is a sound event
            if event['identifier'] in self.SOUND_EVENT_IDS:
                sound_event = M2SoundEvent(
                    identifier=event['identifier'],
                    sound_entry_id=event['data'],
                    parent_bone=event['parent_bone'],
                    position=event['position'],
                    file_offset=event['offset']
                )
                sound_events.append(sound_event)
                
                print(f"  [{i}] {event['identifier']}: SoundEntryID={event['data']}, "
                      f"Bone={event['parent_bone']}, Pos={event['position']}")
            
            # Move to next event
            current_offset += event['size']
        
        return sound_events


def parse_m2_file(filepath: str) -> List[M2SoundEvent]:
    """Parse a single M2 file and return sound events"""
    print(f"\nParsing: {filepath}")
    print("=" * 60)
    
    parser = M2Parser(filepath)
    if not parser.load():
        return []
    
    sound_events = parser.extract_sound_events()
    
    print(f"\nExtracted {len(sound_events)} sound events")
    return sound_events


def parse_directory(directory: str) -> Dict[str, List[M2SoundEvent]]:
    """Parse all M2 files in a directory (recursively)"""
    results = {}
    
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if filename.lower().endswith('.m2'):
                filepath = os.path.join(root, filename)
                sound_events = parse_m2_file(filepath)
                if sound_events:
                    results[filepath] = sound_events
    
    return results


def export_to_csv(results: Dict[str, List[M2SoundEvent]], output_dir: str = "4_M2_Hardcoded_SoundEntry_ID", append_mode: bool = False):
    """Export results to CSV format"""
    import csv
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, "M2_Hardcoded_SoundEntry_ID.csv")
    
    # Prepare new entries as dicts
    new_entries = []
    for filepath, events in results.items():
        for event in events:
            new_entries.append({
                'Filename': os.path.basename(filepath),
                'EventType': event.identifier,
                'SoundEntryID': str(event.sound_entry_id),
                'M2Offset': hex(event.file_offset)
            })
    
    # Load and merge if in append mode
    if append_mode:
        existing_entries = load_existing_csv(output_file)
        if existing_entries:
            print(f"  → Merging with {len(existing_entries)} existing entry(ies)")
            new_entries = merge_m2_entries(existing_entries, new_entries)
    
    # Write CSV
    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Filename', 'EventType', 'SoundEntryID', 'M2Offset'])
        
        for entry in new_entries:
            writer.writerow([
                entry['Filename'],
                entry['EventType'],
                entry['SoundEntryID'],
                entry['M2Offset']
            ])
    
    print(f"\nCSV exported to: {output_file}")


def export_to_list(results: Dict[str, List[M2SoundEvent]]) -> List[int]:
    """Extract unique SoundEntry IDs and return as sorted list"""
    sound_ids = set()
    
    for filepath, events in results.items():
        for event in events:
            sound_ids.add(event.sound_entry_id)
    
    return sorted(list(sound_ids))


def write_md21_log(output_dir: str = "4_M2_Hardcoded_SoundEntry_ID"):
    """Write log file for detected MD21 files"""
    if M2Parser.md21_detected_files:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, "M2_Hardcoded_SoundEntry_ID.log")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"MD21 detected: {len(M2Parser.md21_detected_files)}\n\n")
            f.write("The following files are using MD21 format.\n")
            f.write("This indicates either:\n")
            f.write("  1. Legion+ (7.0+) models\n")
            f.write("  2. Questioning 3.3.5a downport .m2\n\n")
            
            # Write files with index
            for idx, filepath in enumerate(M2Parser.md21_detected_files):
                f.write(f"{os.path.basename(filepath)} (index {idx})\n")
        
        print(f"\nMD21 log written to: {output_file}")


def load_existing_csv(csv_path):
    """Load existing CSV data."""
    import csv
    if not os.path.exists(csv_path):
        return []
    entries = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            entries.append(row)
    return entries


def merge_m2_entries(existing, new):
    """Merge M2 entries, skip duplicates by Filename+EventType+SoundEntryID."""
    # Create unique key for each entry
    by_key = {}
    for entry in existing:
        key = (entry['Filename'], entry['EventType'], entry['SoundEntryID'])
        by_key[key] = entry
    
    skipped, added = 0, 0
    for entry in new:
        key = (entry['Filename'], entry['EventType'], entry['SoundEntryID'])
        if key not in by_key:
            by_key[key] = entry
            added += 1
        else:
            skipped += 1
    
    if skipped > 0:
        print(f"  → Skipped {skipped} duplicate(s), added {added} new")
    
    # Sort by filename, then SoundEntryID
    merged = sorted(by_key.values(), 
                    key=lambda x: (x['Filename'], int(x['SoundEntryID'])))
    return merged



def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python m2_sound_extractor.py <file.m2>")
        print("  python m2_sound_extractor.py <directory>")
        sys.exit(1)
    
    input_path = sys.argv[1]
    
    # Ask for append or overwrite mode
    print("=== OUTPUT MODE SELECTION ===")
    append_mode = False
    while True:
        print("Choose output mode:")
        print("  1. Append to existing CSV (keep previous data)")
        print("  2. Overwrite existing CSV (fresh start)")
        mode_input = input("Enter choice (1 or 2): ").strip()
        if mode_input == '1':
            append_mode = True
            print("→ Will append to existing CSV")
            break
        elif mode_input == '2':
            append_mode = False
            print("→ Will overwrite existing CSV")
            break
        else:
            print("ERROR: Please enter 1 or 2")
    print()
    
    # Reset MD21 tracking
    M2Parser.md21_detected_files = []
    
    if os.path.isfile(input_path):
        # Single file
        sound_events = parse_m2_file(input_path)
        
        if sound_events:
            print("\n" + "=" * 60)
            print("SUMMARY")
            print("=" * 60)
            for event in sound_events:
                print(f"{event.identifier}: {event.sound_entry_id}")
            
            # Output as Python list
            sound_ids = sorted(list(set([e.sound_entry_id for e in sound_events])))
            print(f"\nUnique SoundEntry IDs: {sound_ids}")
            
            # Create results dict for export functions
            results = {input_path: sound_events}
            
            # Export CSV
            export_to_csv(results, append_mode=append_mode)
            
    elif os.path.isdir(input_path):
        # Directory
        results = parse_directory(input_path)
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Total M2 files with sound events: {len(results)}")
        
        # Get all unique sound IDs
        sound_ids = export_to_list(results)
        print(f"Unique SoundEntry IDs found: {len(sound_ids)}")
        print(f"IDs: {sound_ids}")
        
        # Export CSV
        export_to_csv(results, append_mode=append_mode)
        
    else:
        print(f"Error: {input_path} is not a valid file or directory")
        sys.exit(1)
    
    # Write MD21 log if any were detected
    if M2Parser.md21_detected_files:
        write_md21_log()


if __name__ == "__main__":
    main()