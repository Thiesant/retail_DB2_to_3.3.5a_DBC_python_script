# M2 Sound Events Extractor

Python script to extract hardcoded SoundEntry IDs from World of Warcraft M2 model files.

## Purpose

Extracts sound event data ($CSD, $DSL, $DSO, $SND) from M2 files to identify hardcoded SoundEntry IDs that may not be present in DB2/CSV data. Essential for complete DBC downporting workflows.

## Compatibility

- **MD20 Format**
- **MD21 Format**

## Credits

This script's M2 format parsing is based on the 010 Editor M2.bt template maintained by Alastor Strix'Efuartus. The template provided essential insights into the M2 file structure, header offsets, and event definitions.

## Requirements

- Python 3.6+
- No external dependencies (uses only standard library)

## Usage

### Single File
```bash
python m2_Hardcoded_SoundEntry_ID_extractor.py /path/to/models/model.m2
```
Processes a single M2 file and generates output folder with CSV.

### Directory (Recursive)
```bash
python m2_Hardcoded_SoundEntry_ID_extractor.py /path/to/models/
```
Processes all M2 files recursively and generates output folder with CSV.

## Output

### Folder Structure
```
m2_Hardcoded_SoundEntry_ID_extractor.py
4_M2_Hardcoded_SoundEntry_ID/
  ├── M2_Hardcoded_SoundEntry_ID.csv
  └── M2_Hardcoded_SoundEntry_ID.log (only if MD21 files detected)
```

### CSV Format

**Columns:**
- `Filename`: M2 file name
- `EventType`: Event identifier ($CSD, $DSL, $DSO, $SND)
- `SoundEntryID`: The extracted sound ID (references SoundEntries.dbc)
- `M2Offset`: Hex offset of the event in the M2 file

### Log Format (MD21 Detection)
```
MD21 detected: 2

The following files are using MD21 format.
This indicates either:
  1. Legion+ (7.0+) models
  2. Questionable 3.3.5a downport .m2

model1.m2
model2.m2
```

## Event Types


 `$CSD` : PlayEmoteSound    
 `$DSL` : GameObject Sound  
 `$DSO` : DoodadSoundOneShot
 `$SND` : PlaySoundKit      

## Console Output

### MD20 (Standard)
```
Parsing: model.m2
============================================================
Format: MD20, Version: 264, Chunked: False
Found 1 total events at offset 0xb439
  [0] $DSL: SoundEntryID=125265, Bone=7, Pos=(-0.0, 0.0, 0.0)

Extracted 1 sound events
```

### MD21 (With Warning)
```
Parsing: legion_model.m2
============================================================
Format: MD21, Version: 274, Chunked: True
    WARNING: MD21 format detected!
    This is either:
    1. A Legion+ (7.0+) model
    2. A questionable downport of a 3.3.5a .m2 file

Found 2 total events at offset 0xc520
  [0] $DSL: SoundEntryID=145678, Bone=3, Pos=(1.2, 0.0, -0.5)
  [1] $CSD: SoundEntryID=145679, Bone=5, Pos=(0.0, 0.0, 0.0)

Extracted 2 sound events
```

## Technical Details

### M2 File Structure

**MD20 (Pre-Legion):**
- Magic: "MD20"
- nEvents at offset: 0x100
- ofsEvents at offset: 0x104

**MD21 (Legion+):**
- Magic: "MD21"
- 8-byte chunk header before MD20 data
- nEvents at offset: 0x108 (0x100 + 8)
- ofsEvents at offset: 0x10C (0x104 + 8)

### Event Structure
```
Offset | Field        | Size  | Type
+0x00  | Identifier   | 4 B   | CHAR[4] ($CSD, $DSL, etc.)
+0x04  | Data         | 4 B   | uint32 (SoundEntryID)
+0x08  | ParentBone   | 4 B   | uint32
+0x0C  | Position     | 12 B  | float[3] (x, y, z)
+0x18  | Timer        | 20 B  | M2Track structure

Total: 44 bytes per event
```

### M2Track Structure
The Timer field is an M2Track structure (20 bytes):
- uint16 interpolation_type (2 bytes)
- int16 global_sequence (2 bytes)
- M2Array timestamps (8 bytes: count + offset)
- M2Array values (8 bytes: count + offset)

Note: The actual timestamp/value data is stored elsewhere (referenced by offsets), not inline in the event.

## Integration Examples

### DBC Downporting Workflow
1. Run `m2_Hardcoded_SoundEntry_ID_extractor.py` on your M2 file/directory
2. Run `DB2_to_DBC_Filtered.py` to generate related models downport DBC

## Notes

- **Both modes create output**: CSV and log files are always generated in output folder
- **Directory mode**: Scans all subdirectories recursively
- **MD21 detection**: Automatically warns about potentially problematic files
- **Performance**: Processes hundreds of files in seconds

## Troubleshooting

**No events found?**
- This is normal - not all M2 files contain hardcoded sound events

**MD21 warning appearing?**
- Check if files are actually Legion+ models
- If supposed to be 3.3.5a, the downport may be incorrect
- Review the generated log file for list of affected files

**Offset mismatches?**
- Verify M2 file isn't corrupted
- Script may need to be updated
- Compare with 010 Editor using M2.bt template