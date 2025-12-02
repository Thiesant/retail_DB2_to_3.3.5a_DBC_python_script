# DB2_to_DBC_Filtered.py - DOCUMENTATION

## Description
This script generates a filtered subset of World of Warcraft DBC files based on 
selected creature models. Unlike the full DB2_to_DBC.py converter, this creates 
only the data needed for specific models you choose.

FEATURES:
- Interactive model selection (search by FileID or name)
- Generates minimal DBC subset for selected models
- Automatically integrates M2 hardcoded sounds
- Downloads audio files from Wago.tools (requires requests module)
- Ideal for testing or partial conversions

## Requirements

### Python Version
- **Python 3.6 or higher**

### Python Standard Libraries
All required libraries are part of Python's standard library:
- `os` - File and directory operations
- `csv` - CSV file reading/writing
- `pathlib` - Path handling
- `collections.defaultdict` - Data grouping
- `requests module` - **OPTIONAL, for audio download feature**
  * Install with: pip install requests
  * If not installed, script will skip downloading and only generate CSV files
  
### Setup Directory Structure
```
/
├── DB2_to_DBC_Filtered.py
├── 0_Input/
│   ├── Community-listfile (https://github.com/wowdev/wow-listfile)
│   └── [table].[version].csv (https://wago.tools/db2)
├── 1_DBCWotlk_csv/
│   ├── Wotlk_CreatureDisplayInfo.csv  # BloodLevel entries for CreatureDisplayInfo
│   ├── Wotlk_VocalUISounds.csv        # PissedSoundID_1, PissedSoundID_2 for VocalUISounds
│   └── Wotlk_SoundEntries.csv         # WotLK reference for SoundEntries names
└── 3_DBC_Filtered/                    # Output with downported .csv
```
The script requires four directories in the same folder as the script:

#### 1. `0_Input/` - Retail DBC/DB2 Data (Required)

Required files (must contain these table names, version numbers may vary):

- `listfile.csv` OR `community-listfile.csv` OR `community-listfile-withcapitals.csv`
- `CreatureDisplayInfo.[version].csv`            (e.g., CreatureDisplayInfo.11.2.5.64502.csv)
- `CreatureDisplayInfoGeosetData.[version].csv`  (e.g., CreatureDisplayInfoGeosetData.11.2.5.64502.csv)
- `CreatureModelData.[version].csv`              (e.g., CreatureModelData.11.2.5.64502.csv)
- `CreatureSoundData.[version].csv`              (e.g., CreatureSoundData.11.2.5.64502.csv)
- `FootstepTerrainLookup.[version].csv`          (e.g., FootstepTerrainLookup.11.2.5.64502.csv)
- `GameObjectDisplayInfo.[version].csv`          (e.g., GameObjectDisplayInfo.11.2.5.64502.csv)
- `GameObjectDisplayInfoXSoundKit.[version].csv` (e.g., GameObjectDisplayInfoXSoundKit.11.2.5.64502.csv)
- `NPCSounds.[version].csv`                      (e.g., NPCSounds.11.2.5.64502.csv)
- `ObjectEffect.[version].csv`                   (e.g., ObjectEffect.11.2.5.64502.csv)
- `ObjectEffectModifier.[version].csv`           (e.g., ObjectEffectModifier.11.2.5.64502.csv)
- `ObjectEffectPackageElem.[version].csv`        (e.g., ObjectEffectPackageElem.11.2.5.64502.csv)
- `ParticleColor.[version].csv`                  (e.g., ParticleColor.11.2.5.64502.csv)
- `SoundKit.[version].csv`                       (e.g., SoundKit.11.2.5.64502.csv)
- `SoundKitAdvanced.[version].csv`               (e.g., SoundKitAdvanced.11.2.5.64502.csv)
- `SoundKitEntry.[version].csv`                  (e.g., SoundKitEntry.11.2.5.64502.csv)

#### 2. `1_DBCWotlk_csv/` - WotLK Reference Data (Optional but Recommended)

**Optional files:**

1. `Wotlk_SoundEntries.csv`
   - If present, user is prompted to choose naming method:
     * Option 1: Use WotLK names (where ID matches) + generate from File_1 for new IDs
     * Option 2: Generate all names from File_1 (ignore WotLK names)
   - If absent, all names are generated from File_1 automatically

2. `Wotlk-CreatureDisplayInfo.csv`
   - WotLK CreatureDisplayInfo data
   - Used to get BloodLevel values for downporting

#### 3. `3_DBC_Filtered/` - Output Directory
- This directory will be **automatically created** by the script
- All converted CSV files will be saved here

#### 4. `4_M2_Hardcoded_SoundEntry_ID`/ (Optional but Recommended)

This directory is automatically created by `m2_Hardcoded_SoundEntry_ID_extractor.py`

1. `M2_Hardcoded_SoundEntry_ID.csv`
   - If present, SoundEntry IDs are automatically included in Step 9
   - Contains hardcoded sound events from .m2 model files
   - Format: Filename, EventType, SoundEntryID, M2Offset
   
**WORKFLOW INTEGRATION:**
   1. Run `m2_Hardcoded_SoundEntry_ID_extractor.py` on your .m2 files first
   2. Run `DB2_to_DBC_Filtered.py` (automatically detects and uses the M2 data)
   
If this file is NOT present:
   - Script displays a tip suggesting to run the M2 extractor first
   - Only DB2-referenced sounds will be included
   - Hardcoded M2 sounds may be missing from output


## Generated Output Files

### 1. `3_DBC_Filtered/`

The following CSV files are generated (depending on available data):

1.  **CreatureDisplayInfo.csv**
2.  **CreatureModelData.csv**
3.  **CreatureSoundData.csv**
    - Creature audio events   ( Attack, death, aggro, footstep, Fidget sounds and custom attacks etc.)
4.  **FootstepTerrainLookup.csv**
    - Links terrain types to footstep sound IDs
    - Optionally filtered to WotLK terrain types only
5.  **GameObjectDisplayInfo.csv**
6.  **NPCSounds.csv**
    - NPC vocal sound references
7.  **ObjectEffect.csv**
8.  **ObjectEffectGroup.csv**
9.  **ObjectEffectModifier.csv**
10. **ObjectEffectPackage.csv**
11. **ObjectEffectPackageElem.csv**
12. **ParticleColor.csv**
13. **SoundEntries.csv** 
    - Main sound definitions- Merged from: SoundKit + SoundKitEntry
    - Maps FileDataIDs to audio file paths
    - Includes volume, distance, and audio settings
14. **SoundEntriesAdvanced.csv**
    - Advanced sound parameters
    - Source: SoundKitAdvanced

UTILITY FILE:
15. **listfile_filtered.csv**
    - Contains only FileIDs used in filtered output
    - Format: FileID;Path (semicolon-separated)
    - Includes:
      * Model FileIDs (from Step 1 selection)
      * Texture FileIDs (from CreatureDisplayInfo)
      * Audio FileIDs (from SoundEntries)


### 2. `5_Downloaded_Sounds/` (Optional - requires requests module)

Downloaded audio files organized by folder structure (preserves hierarchy):

**AUTOMATIC DOWNLOAD FEATURE:**
- After CSV generation, script offers to download audio files from Wago.tools
- Files are organized in their original folder structure
- Already downloaded files are automatically skipped
- Shows download progress and success rate

**LOCALE INFORMATION:**
- Downloaded sounds are in enUS locale from Wago.tools
- Installation paths:
  * Most sounds → wow\data\ (music, creatures, spells, effects)
  * Locale-specific sounds → wow\data\[locale]\ (character voices, NPC dialogue)

EXAMPLE STRUCTURE:
```
5_Downloaded_Sounds/
  ├── Sound/
  │   ├── Creature/
  │   │   └── Murloc/
  │   │       ├── MurlocAggro01.ogg
  │   │       └── MurlocDeath01.ogg
  │   └── Music/
  │       └── ZoneMusic/
  │           └── Elwynn.mp3
  └── [other sound folders...]
  ```

**REQUIREMENTS:**
- Python requests module must be installed (pip install requests)
- Internet connection to Wago.tools
- Sufficient disk space for audio files

**USER PROMPT:**
During CSV generation completes, you will be asked:
"Download sounds after processing? (y/n):"
  - y: Downloads all audio files referenced in `listfile_filtered.csv`
  - n: Skips downloading, only CSV files are generated


### LOG FILES (Generated in script directory when issues found)

1. CreatureModelData_filtered.log
   - Lists model FileDataIDs not found in listfile
   - Indicates missing model file mappings

2. CreatureDisplayInfo_Textures_filtered.log
   - Lists texture FileDataIDs not found in listfile
   - Shows which texture fields are unmapped
   - Format: ID, Field Name, FileDataID

3. CreatureDisplayInfo_GeosetOverflow_filtered.log
   - Lists entries where CreatureGeosetData calculation exceeded MAX_VALUE
   - Shows calculated value vs capped value (2147483647)

4. GameObjectDisplayInfo_filtered.log
   - Lists model FileDataIDs not found in listfile

5. ObjectEffect_filtered.log
   - Lists ObjectEffect entries with EffectRecID = 0
   - These entries are skipped (no sound reference)

6. ObjectEffectPackageElem_filtered.log
   - Lists ObjectEffectPackageElem entries with invalid ObjectEffectGroupID
   - References groups that don't exist in output


## Script Processing Steps Overview

STEP 1: Model Selection
- User searches by FileID or model name (partial match supported for both option)
- Multiple selection supported (space-separated numbers, e.g., "1 3 4")
- Selected model FileIDs drive all subsequent filtering

STEP 2: CreatureModelData
- Filters by selected model FileIDs
- Collects ModelIDs and SoundIDs for next steps

STEP 2b: GameObjectDisplayInfo
- Model will also be looked in this input in parallel

STEP 3: CreatureDisplayInfo
- Filters by ModelIDs from Step 2
- Collects: SoundIDs, ParticleColorIDs, NPCSoundIDs, ObjectEffectPackageIDs
- Maps texture FileIDs to .blp filenames
- Calculates CreatureGeosetData from geoset values
- Gets BloodLevel from WotLK data

STEP 4: CreatureSoundData
- Filters by SoundIDs from Steps 2 & 3
- Recursively includes CreatureSoundDataIDPet references
- Collects: NPCSoundIDs, SoundFootstepIDs

STEP 5: ParticleColor
- Filters by ParticleColorIDs from Step 3

STEP 6: NPCSounds
- Filters by NPCSoundIDs from Steps 3 & 4

STEP 7: FootstepTerrainLookup
- Filters by SoundFootstepIDs from Step 4
- Only includes WotLK terrain types (0-10)

STEP 8: ObjectEffect Chain (4 tables)
- 8a: ObjectEffectPackageElem (first pass) - collect ObjectEffectGroupIDs
- 8b: ObjectEffect - filter by ObjectEffectGroupIDs, skip EffectRecID=0
- 8c: ObjectEffectGroup - generated from ObjectEffect entries
- 8d: ObjectEffectPackageElem (second pass) - validate against ObjectEffectGroup
- 8e: ObjectEffectPackage - generated from validated elements

STEP 9: SoundEntries
- M2 Integration: Automatically detects and includes hardcoded SoundEntry IDs
  * Checks for 4_M2_Hardcoded_SoundEntry_ID/M2_Hardcoded_SoundEntry_ID.csv
  * If found: adds all hardcoded SoundEntry IDs from .m2 files
  * If not found: displays tip to run m2_Hardcoded_SoundEntry_ID_extractor.py first
- Collects SoundKit IDs from:
  * M2 hardcoded sounds (if available)
  * CreatureSoundData (all sound fields)
  * FootstepTerrainLookup (SoundID, SoundIDSplash)
  * NPCSounds (SoundID_1/2/3/4)
  * ObjectEffect (EffectRecID)
- Generates entries with audio files, frequencies, volumes
- Applies names based on user preference

STEP 9.5: SoundEntries + ObjectEffect Chain
- Update Name field of OvjectEffect related dbc after SoundEntries generation

STEP 10: SoundEntriesAdvanced
- Filters by SoundEntriesAdvancedID from SoundEntries
- Complete names from SoundEntries

STEP 11: ObjectEffectModifier
- Filters by ObjectEffectModifierID from ObjectEffect
- Contains effect modification parameters

Generate listfile_filtered
- Aggregates all FileIDs used across all steps
- Includes models, textures, and audio files

STEP 12: Audio Download (Optional)
- Requires: requests module (pip install requests)
- Requires: `listfile_filtered` generated in previous step
- Downloads audio files from Wago.tools based on filtered SoundEntries
- Organizes files in 5_Downloaded_Sounds/ directory
- Preserves folder structure from listfile paths
- Skips already downloaded files
- Shows progress: downloaded count, failed count, skipped count
- Provides locale installation instructions


## How to Use

### Related Tools
This is part of a suite of tools:
- **[m2_Hardcoded_SoundEntry_ID_extractor.py](M2_Sound_Events_Extractor_README.md)** - Extract M2 hardcoded sounds (run first for best results)
- **[DB2_to_DBC_Filtered.py](DB2_to_DBC_Filtered_README.md)** - Filtered converter for specific models (with audio download)

#### 1. Prepare Input Files
1. Get DB2 tables from [wago.tools](https://wago.tools/db2) and place them in `0_Input/`
2. Get the listfile from [wow-listfile community](https://github.com/wowdev/wow-listfile)
3. Don't use duplicate tables with different versions (keep only one version per table)

#### 2. Run the Script
Open terminal in the script's folder and run:

```bash
python DB2_to_DBC_Filtered.py
```

#### 3. Answer Configuration Prompts

The script will ask five questions:

#### Prompt 1: OUTPUT MODE SELECTION:
```
Choose output mode:
  1. Append to existing files (keep previous data)
  2. Overwrite existing files (fresh start)
Enter choice (1 or 2):
```
- **1**: keep output files from previous generations and add/update entries
- **2**: erase previous data except generated in `3_DBC_Filtered/` - Output Directory

#### Prompt 2: SOUND DOWNLOAD PREFERENCE:
```
"Download sounds after processing? (y/n):"
```
- **Yes** Downloads all audio files referenced in `listfile_filtered.csv`
   If requests module not installed:
   - Script will display error and skip download feature
   - Install with: pip install requests
- **No** Skips downloading, only CSV files are generated

#### Prompt 3: FORMAT SELECTION
```
Format CSV for WDBX Editor? (quotes all fields, converts decimals . to ,) (y/n):
```
- **Yes**: Format for WDBX Editor compatibility
  - All fields will be quoted
  - Decimal separators changed from `.` to `,` (e.g., `1.5` → `1,5`)
- **No**: Standard CSV format
  - Minimal quoting
  - Standard decimal notation with periods

#### Prompt 4: SOUNDENTRIES NAMING PREFERENCE
```
Use WoW 3.3.5a (WotLK) SoundEntries names? (1/2):
```
- **1**: Use original WotLK names from `Wotlk_SoundEntries.csv` where available
  - Matching IDs will preserve their original WotLK names
  - New IDs will have generated names based on file paths
- **2**: Generate all names from file paths (File_1)
  - All names will be auto-generated from the first audio file

#### Prompt 5: MODEL SELECTION
```
Choose search method:
```
Choose search method:
- **1.** Search by FileID (partial match supported)
- **2.** Search by model name (partial match)
   type the name of the model you are looking for then enter, if multiple choices found
   Enter selection (space-separated numbers, e.g., '1 3 4', or 'all' for all models founds)


### FILE FORMAT NOTES

**WDBX Format (when enabled):**
- All CSV fields are quoted
- Decimal points (.) are converted to commas (,) for float values
- Compatible with WDBX Editor tool

**Standard Format:**
- Minimal quoting (only when necessary)
- Standard decimal points (.)
- Compatible with most CSV readers

**Listfile Format:**
- ALWAYS uses standard format (semicolon-separated, no WDBX)
- Format: FileID;Path
- Exemple: 125024;Creature\Murloc\Murloc.m2


### Troubleshooting

#### Common Issues

**"ERROR: No listfile found in 0_Input"**
- Ensure you have a CSV file with "listfile" in its name in the `0_Input/` folder
- Check that the file has a `.csv` extension

**"Table not found":**
- Check that DB2 files exist in 0_Input/
- Verify filenames match pattern: TableName.version.csv
- Script auto-detects version numbers

**"No entries found for filtered IDs":**
- May indicate data chain is incomplete
- Check earlier steps for warnings
- Review log files for unmapped FileDataIDs

**"Column name mismatch":**
- DB2 structure may have changed between versions
- Script expects specific column names (case-insensitive)

**"Download failed / requests module not found":**
- Install requests module: pip install requests
- Check internet connection to Wago.tools
- Some files may not be available on Wago.tools (normal, will be logged)
- Script continues if download fails, CSV files are still generated

**"Downloaded files not working in WoW":**
- Verify file paths match WoW directory structure
- Verify your .dbc
- Most sounds go to wow\data\patch-x.mpq directory
- Locale-specific sounds to wow\data\[locale]\patch-[locale]-x.mpq (e.g., wow\data\enUS\)
- .ogg do WORKS in wow 3.3.5a however some codec version won't (eg. lavf55.33.100)

## NOTES

**GENERAL:**
- The script creates the 3_DBC_Filtered directory if it doesn't exist
- All log files are created in the script's directory (not in output folder)
- Log files use "_filtered" suffix to distinguish from full converter logs
- File version numbers (e.g., 11.2.5.64502) may vary - script auto-detects
- Missing optional files result in warnings but don't stop execution
- Empty or "0" ID values are skipped during filtering
- All output is sorted by ID for consistency

**AUDIO DOWNLOAD:**
- Download feature is optional and requires requests module
- The 5_Downloaded_Sounds directory is created automatically if downloading
- Files are organized in their original folder structure from listfile
- Already downloaded files are skipped (saves time on re-runs)
- Download failures are logged but don't stop the process
- Downloaded files are enUS locale (from Wago.tools)
- No authentication required - files are publicly available

## DIFFERENCES FROM FULL DB2_to_DBC.py

**FULL CONVERTER:**
- Processes ALL entries from DB2 files
- Output directory: 2_DBCRetail_to_Wotlk_csv
- Generates complete WotLK-compatible DBC set
- No user selection required
- No audio download feature

**FILTERED CONVERTER (this script):**
- Processes ONLY selected models and related data
- Output directory: 3_DBC_Filtered
- Generates minimal subset for specific models
- Requires user model selection
- Includes automatic audio download feature (optional, requires requests)
- Downloads files to: 5_Downloaded_Sounds
- Ideal for testing specific models

**THIS SCRIPT IS SKIPPING TERRAIN ID NOT SUPPORTED BY WOTLK BY DEFAULT**
 EDIT SCRIPT IF YOU ARE PLANNING TO ADD GLASS AND OTHER TERRAIN TYPES SUPPORT TO YOUR 3.3.5a Client


## Version Compatibility

- **Source**: World of Warcraft Retail (any modern expansion should work but script was tested with 11.0+ retail version)
- **Target**: World of Warcraft 3.3.5a (Wrath of the Lich King)
- **Tested with**: Python 3.14

## Credits

- Blizzard
- https://github.com/wowdev/wow-listfile
- https://wago.tools/