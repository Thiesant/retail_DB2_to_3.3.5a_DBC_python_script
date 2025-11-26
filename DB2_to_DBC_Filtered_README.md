================================================================================
DB2_to_DBC_Filtered.py - DOCUMENTATION
================================================================================

OVERVIEW:
This script generates a filtered subset of World of Warcraft DBC files based on 
selected creature models. Unlike the full DB2_to_DBC.py converter, this creates 
only the data needed for specific models you choose.

================================================================================
REQUIRED INPUT FILES
================================================================================

DIRECTORY: 0_Input/
--------------------
Required files (must contain these table names, version numbers may vary):

1. listfile.csv OR community-listfile.csv OR community-listfile-withcapitals.csv

2. CreatureModelData.[version].csv (e.g., CreatureModelData.11.2.5.64502.csv)

3. CreatureDisplayInfo.[version].csv (e.g., CreatureDisplayInfo.11.2.5.64502.csv)

4. CreatureDisplayInfoGeosetData.[version].csv (e.g., CreatureDisplayInfoGeosetData.11.2.5.64502.csv)

5. CreatureSoundData.[version].csv (e.g., CreatureSoundData.11.2.5.64502.csv)

6. ParticleColor.[version].csv (e.g., ParticleColor.11.2.5.64502.csv)

7. NPCSounds.[version].csv (e.g., NPCSounds.11.2.5.64502.csv)

8. FootstepTerrainLookup.[version].csv (e.g., FootstepTerrainLookup.11.2.5.64502.csv)

9. ObjectEffect.[version].csv (e.g., ObjectEffect.11.2.5.64502.csv)

10. ObjectEffectModifier.[version].csv (e.g., ObjectEffectModifier.11.2.5.64502.csv)

11. ObjectEffectPackageElem.[version].csv (e.g., ObjectEffectPackageElem.11.2.5.64502.csv)

12. SoundKitEntry.[version].csv (e.g., SoundKitEntry.11.2.5.64502.csv)

13. SoundKit.[version].csv (e.g., SoundKit.11.2.5.64502.csv)

14. SoundKitAdvanced.[version].csv (e.g., SoundKitAdvanced.11.2.5.64502.csv)


DIRECTORY: 1_DBCWotlk_csv/
---------------------------
Optional files:

1. Wotlk_SoundEntries.csv
   - If present, user is prompted to choose naming method:
     * Option 1: Use WotLK names (where ID matches) + generate from File_1 for new IDs
     * Option 2: Generate all names from File_1 (ignore WotLK names)
   - If absent, all names are generated from File_1 automatically

2. CreatureDisplayInfo.csv
   - WotLK CreatureDisplayInfo data
   - Used to get BloodLevel values for downporting


DIRECTORY: 4_M2_Hardcoded_SoundEntry_ID/ (Optional but Recommended)
--------------------------------------------------------------------
This directory is automatically created by m2_Hardcoded_SoundEntry_ID_extractor.py

1. M2_Hardcoded_SoundEntry_ID.csv
   - If present, SoundEntry IDs are automatically included in Step 9
   - Contains hardcoded sound events from .m2 model files
   - Format: Filename, EventType, SoundEntryID, M2Offset
   
WORKFLOW INTEGRATION:
   1. Run m2_Hardcoded_SoundEntry_ID_extractor.py on your .m2 files first
   2. Run DB2_to_DBC_Filtered.py (automatically detects and uses the M2 data)
   
If this file is NOT present:
   - Script displays a tip suggesting to run the M2 extractor first
   - Only DB2-referenced sounds will be included
   - Hardcoded M2 sounds may be missing from output


================================================================================
GENERATED OUTPUT FILES
================================================================================

DIRECTORY: 3_DBC_Filtered/
---------------------------
The following CSV files are generated (depending on available data):

MAIN CREATURE DBC:
1. CreatureModelData.csv
   - Filtered creature model definitions
   - Contains only models selected by user

2. CreatureDisplayInfo.csv
   - Filtered display information
   - Only entries for selected models

3. CreatureSoundData.csv
   - Filtered creature sound data
   - Includes recursively collected CreatureSoundDataIDPet references

VISUAL DBC:
4. ParticleColor.csv
   - Filtered particle colors
   - Based on ParticleColorID from CreatureDisplayInfo

SOUND DBC:
5. NPCSounds.csv
   - Filtered NPC sound sets
   - Based on NPCSoundID from CreatureDisplayInfo and CreatureSoundData

6. FootstepTerrainLookup.csv
   - Filtered footstep sounds
   - Based on SoundFootstepID from CreatureSoundData
   - Only includes WotLK-compatible terrain types (0-10)

7. SoundEntries.csv
   - Filtered sound entries
   - Generated from all sound references across tables
   - Names applied based on user preference (WotLK or generated)

8. SoundEntriesAdvanced.csv
   - Filtered advanced sound properties
   - Based on SoundEntriesAdvancedID from SoundEntries

OBJECT EFFECTS (4 files):
The following are responsable for sounds based on model state anim that are not covered in CreatureSoundData

9. ObjectEffect.csv
   - Filtered object effects
   - Based on ObjectEffectPackageID chain from CreatureDisplayInfo

10. ObjectEffectGroup.csv
    - Generated from filtered ObjectEffect entries
    - Groups effects with names

11. ObjectEffectPackageElem.csv
    - Filtered effect package elements
    - Validated against ObjectEffectGroup

12. ObjectEffectPackage.csv
    - Generated from filtered ObjectEffectPackageElem
    - Package definitions with names

13. ObjectEffectModifier.csv
    - Filtered effect modifiers
    - Based on ObjectEffectModifierID from ObjectEffect

UTILITY FILE:
14. listfile_filtered.csv
    - Contains only FileIDs used in filtered output
    - Format: FileID;Path (semicolon-separated)
    - Includes:
      * Model FileIDs (from Step 1 selection)
      * Texture FileIDs (from CreatureDisplayInfo)
      * Audio FileIDs (from SoundEntries)


================================================================================
LOG FILES (Generated in script directory when issues found)
================================================================================

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

4. ObjectEffect_filtered.log
   - Lists ObjectEffect entries with EffectRecID = 0
   - These entries are skipped (no sound reference)

5. ObjectEffectPackageElem_filtered.log
   - Lists ObjectEffectPackageElem entries with invalid ObjectEffectGroupID
   - References groups that don't exist in output


================================================================================
PROCESSING STEPS OVERVIEW
================================================================================

STEP 1: Model Selection
- User searches by FileID or model name (partial match supported for both option)
- Multiple selection supported (space-separated numbers, e.g., "1 3 4")
- Selected model FileIDs drive all subsequent filtering

STEP 2: CreatureModelData
- Filters by selected model FileIDs
- Collects ModelIDs and SoundIDs for next steps

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

STEP 10: SoundEntriesAdvanced
- Filters by SoundEntriesAdvancedID from SoundEntries
- Complete names from SoundEntries

STEP 11: ObjectEffectModifier
- Filters by ObjectEffectModifierID from ObjectEffect
- Contains effect modification parameters

FINAL: Filtered Listfile
- Aggregates all FileIDs used across all steps
- Includes models, textures, and audio files


================================================================================
USER PROMPTS
================================================================================

1. WDBX Format:
   "Format CSV for WDBX Editor? (quotes all fields, converts decimals . to ,) (y/n):"
   - y: All fields quoted, decimal point changed to comma for floats
   - n: Standard CSV format

2. SoundEntries Naming (if Wotlk_SoundEntries.csv exists):
   "Choose SoundEntries naming method:"
   - 1: Use WotLK names (where ID matches) + generate from File_1 (for new IDs)
   - 2: Generate all names from File_1 (ignore WotLK names)

3. Model Selection:
   "Choose search method:"
   - 1: Search by FileID (partial match supported)
   - 2: Search by model name (partial match)
   
   If multiple matches found:
   "Enter selection (space-separated numbers, e.g., '1 3 4', or 'all' for all models):"


================================================================================
FILE FORMAT NOTES
================================================================================

WDBX Format (when enabled):
- All CSV fields are quoted
- Decimal points (.) are converted to commas (,) for float values
- Compatible with WDBX Editor tool

Standard Format:
- Minimal quoting (only when necessary)
- Standard decimal points (.)
- Compatible with most CSV readers

Listfile Format:
- ALWAYS uses standard format (semicolon-separated, no WDBX)
- Format: FileID;Path
- Exemple: 125024;Creature\Murloc\Murloc.m2


================================================================================
NOTES
================================================================================

- The script creates the 3_DBC_Filtered directory if it doesn't exist
- All log files are created in the script's directory (not in output folder)
- Log files use "_filtered" suffix to distinguish from full converter logs
- File version numbers (e.g., 11.2.5.64502) may vary - script auto-detects
- Missing optional files result in warnings but don't stop execution
- Empty or "0" ID values are skipped during filtering
- All output is sorted by ID for consistency


================================================================================
TROUBLESHOOTING
================================================================================

"Listfile not found":
- Ensure listfile.csv or community-listfile.csv exists in 0_Input/
- File must end with .csv extension

"Table not found":
- Check that DB2 files exist in 0_Input/
- Verify filenames match pattern: TableName.version.csv
- Script auto-detects version numbers

"No entries found for filtered IDs":
- May indicate data chain is incomplete
- Check earlier steps for warnings
- Review log files for unmapped FileDataIDs

"Column name mismatch":
- DB2 structure may have changed between versions
- Script expects specific column names (case-insensitive)


================================================================================
DIFFERENCES FROM FULL DB2_to_DBC.py
================================================================================

FULL CONVERTER:
- Processes ALL entries from DB2 files
- Output directory: 2_DBCRetail_to_Wotlk_csv
- Generates complete WotLK-compatible DBC set
- No user selection required

FILTERED CONVERTER (this script):
- Processes ONLY selected models and related data
- Output directory: 3_DBC_Filtered
- Generates minimal subset for specific models
- Requires user model selection
- Ideal for testing specific models or partial conversions


================================================================================
VERSION COMPATIBILITY
================================================================================

This script is designed for:
- Source: World of Warcraft 11.0+ (Retail) DB2 files
- Target: WotLK 3.3.5a DBC format


================================================================================