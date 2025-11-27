# DB2_to_DBC.py - Full Converter Documentation

## Description
This Python script converts World of Warcraft Retail .DB2 files to WotLK 3.3.5a .DBC format.

This is the **full converter** that processes all entries from DB2 files. For selective model conversion, see [DB2_to_DBC_Filtered_README.md](DB2_to_DBC_Filtered_README.md).

## Requirements

### Python Version
- **Python 3.6 or higher**

### Python Standard Libraries
All required libraries are part of Python's standard library:
- `os` - File and directory operations
- `csv` - CSV file reading/writing
- `pathlib` - Path handling
- `collections.defaultdict` - Data grouping

### Setup Directory Structure
```
/
├── DB2_to_DBC.py
├── 0_Input/
│   ├── Community-listfile (https://github.com/wowdev/wow-listfile)
│   └── [table].[version].csv (https://wago.tools/db2)
├── 1_DBCWotlk_csv/
│   ├── Wotlk_CreatureDisplayInfo.csv  # BloodLevel entries for CreatureDisplayInfo
│   ├── Wotlk_VocalUISounds.csv        # PissedSoundID_1, PissedSoundID_2 for VocalUISounds
│   └── Wotlk_SoundEntries.csv         # WotLK reference for SoundEntries names
└── 2_DBCRetail_to_Wotlk_csv/          # Output with downported .csv
```

The script requires three directories in the same folder as the script:

#### 1. `0_Input/` - Retail DBC/DB2 Data (Required)
Must contain:
- **Listfile CSV** (any filename containing "listfile", case-insensitive)
  - Format: `FileDataID;FilePath` (semicolon-separated)
  - Maps FileDataIDs to actual file paths
  
- **Retail DB2 Tables** (CSV format, `[table].[version].csv` or `[table].csv)
  - Required tables:
    - `SoundKit.csv` or `SoundKit.[version].csv`
    - `SoundKitEntry.csv`
    - `CreatureDisplayInfo.csv`
    - `CreatureModelData.csv`
    - `CreatureSoundData.csv`
    - `NPCSounds.csv`
    - `FootstepTerrainLookup.csv`
    - `ZoneMusic.csv`
    - `ZoneIntroMusicTable.csv`
    - `VocalUISounds.csv`
    - `SoundProviderPreferences.csv`
    - `SoundFilter.csv`
    - `SoundFilterElem.csv`
    - `SoundEmitters.csv`
    - `SoundAmbience.csv`
    - `WeaponImpactSounds.csv`
    - `ParticleColor.csv`
    - `ObjectEffect.csv`
    - `ObjectEffectModifier.csv`
    - `ObjectEffectPackageElem.csv`
    - `SoundKitAdvanced.csv`
    - `CreatureDisplayInfoGeosetData.csv` (for CreatureGeosetData calculation I used : Σ(GeosetValue × 16^GeosetIndex), meaning that you may have to edit the .m2 that have GeosetIndex is > 8 (WoW Blender Studio)

#### 2. `1_DBCWotlk_csv/` - WotLK Reference Data (Optional)
- **`Wotlk_SoundEntries.csv`**
  - Used when you select "yes" to using WotLK names
  - If provided, matching IDs will use original WotLK names instead of generated names

#### 3. `2_DBCRetail_to_Wotlk_csv/` - Output Directory
- This directory will be **automatically created** by the script
- All converted DBC files will be saved here

### File Format Notes
- All input CSV files should be UTF-8 encoded
- CSV files can have version numbers in their names (e.g., `SoundKit.11.2.5.64502.csv`)
- The script will automatically find the correct file regardless of version numbering

## How to Use

### Related Tools
This is part of a suite of tools:
- **[m2_Hardcoded_SoundEntry_ID_extractor.py](M2_Sound_Events_Extractor_README.md)** - Extract M2 hardcoded sounds (run first for best results)
- **[DB2_to_DBC_Filtered.py](DB2_to_DBC_Filtered_README.md)** - Filtered converter for specific models (with audio download)
- **DB2_to_DBC.py** - This full converter (processes all data)

### 1. Prepare Input Files
1. Get DB2 tables from [wago.tools](https://wago.tools/db2) and place them in `0_Input/`
2. Get the listfile from [wow-listfile community](https://github.com/wowdev/wow-listfile)
3. Don't use duplicate tables with different versions (keep only one version per table)

### 2. Run the Script
Open terminal in the script's folder and run:

```bash
python DB2_to_DBC.py
```

### 3. Answer Configuration Prompts

The script will ask three questions:

#### Prompt 1: WotLK Names
```
Use WoW 3.3.5a (WotLK) SoundEntries names? (y/n):
```
- **Yes**: Use original WotLK names from `Wotlk_SoundEntries.csv` where available
  - Matching IDs will preserve their original WotLK names
  - New IDs will have generated names based on file paths
- **No**: Generate all names from file paths (File_1)
  - All names will be auto-generated from the first audio file

#### Prompt 2: WDBX Format
```
Format CSV for WDBX Editor? (quotes all fields, converts decimals . to ,) (y/n):
```
- **Yes**: Format for WDBX Editor compatibility
  - All fields will be quoted
  - Decimal separators changed from `.` to `,` (e.g., `1.5` → `1,5`)
- **No**: Standard CSV format
  - Minimal quoting
  - Standard decimal notation with periods

#### Prompt 3: Terrain Filtering
```
Filter FootstepTerrainLookup to WotLK-compatible terrain types only? (recommended) (y/n):
```
- **Yes** (recommended): Only include terrain types that exist in WotLK
  - Prevents incompatible terrain types from causing issues
- **No**: Include all terrain types from Retail
  - May cause issues with terrain types that don't exist in WotLK (most likely that game will crashes)

### 4. Processing

The script will:
1. Load and parse all input files
2. Process each DBC table
3. Generate converted output files
4. Create log files for any issues found
5. Display progress and samples

### 5. Review Output

Check the `2_DBCRetail_to_Wotlk_csv/` folder for:
- **22 converted DBC CSV files** (ready for WotLK)
- **Log files** (if any issues were found)

#### Log Files
The script may generate log files for issues that need manual review:

- **`SoundEntries.log`** - FileDataIDs not found in listfile (for audio files)
- **`SoundEntries_SoundKit.log`** - Missing SoundKit data (defaults applied)
- **`CreatureModelData.log`** - Model FileDataIDs not in listfile
- **`CreatureDisplayInfo_Textures.log`** - Texture FileDataIDs not in listfile
- **`CreatureDisplayInfo_GeosetOverflow.log`** - Geoset calculations exceeding limits
- **`ObjectEffect.log`** - Entries with EffectRecID = 0 (skipped)
- **`ObjectEffectPackageElem.log`** - Invalid ObjectEffectGroupID references

**Review these logs** to identify missing listfile entries or data issues.

## Output Files

### Downported DBC Files from Retail to WotLK 3.3.5a

The script generates **22 CSV files** compatible with WotLK 3.3.5a:

#### Current DBC wotlk downport list featured (22 files)
1. **SoundEntries.csv** - Main sound definitions
   - Merged from: SoundKit + SoundKitEntry
   - Maps FileDataIDs to audio file paths
   - Includes volume, distance, and audio settings

2. **SoundEntriesAdvanced.csv** - Advanced sound parameters
   - Source: SoundKitAdvanced

3. **CreatureSoundData.csv** 
   - Creature audio events
   ( Attack, death, aggro, footstep, Fidget sounds and custom attacks etc.)

4. **NPCSounds.csv**
   - NPC vocal sound references

5. **SoundAmbience.csv**
   - Ambient sound zones
   - Day and night ambient sound IDs

6. **SoundEmitters.csv**
   - World sound emitters

7. **SoundProviderPreferences.csv**
   - Audio provider settings and priorities

8. **SoundFilter.csv**

9. **SoundFilterElem.csv**

10. **ZoneMusic.csv**
    - Zone background music
    - Day/night music per zone

11. **ZoneIntroMusicTable.csv**
    - Zone intro music
    - Music played when entering zones

12. **VocalUISounds.csv**
    - UI voice-overs (bag full, etc.)

13. **WeaponImpactSounds.csv**
    - Weapon impact sounds, duuh

14. **FootstepTerrainLookup.csv**
    - Links terrain types to footstep sound IDs
    - Optionally filtered to WotLK terrain types only

15. **CreatureDisplayInfo.csv**

16. **CreatureModelData.csv**

17. **ParticleColor.csv**

18. **ObjectEffect.csv**

19. **ObjectEffectModifier.csv**

20. **ObjectEffectGroup.csv**

21. **ObjectEffectPackage.csv**

22. **ObjectEffectPackageElem.csv**

### Key Features of Output Files

- **All files sorted by ID** (smallest to largest)
- **FileDataIDs converted** to file names and absolute paths
- **Option to use WotLK sound entry names** - entries from later expansions have generated names
- **Headers adjusted** to match WDBX 1.1.9.a format
- **File extensions updated** (.m2 → .mdx for CreatureModelData)
- **Path separators normalized** (/ → \\)
- **Optional entry filtering** - FootstepTerrainLookup limited to TerrainSoundID 0-10 (using higher IDs will crash the client without game modifications)
- **Option to format for WDBX Editor** - quotes all fields and converts decimal separators (. → ,)

## Notes

- This script processes **all entries** from DB2 files (not filtered)
- For selective model conversion, use [DB2_to_DBC_Filtered.py](DB2_to_DBC_Filtered_README.md)
- The `2_DBCRetail_to_Wotlk_csv/` directory is automatically created
- Log files are generated in the script's directory for any issues
- All output files are sorted by ID for consistency
- Missing optional files result in warnings but don't stop execution
- The script does **not** include audio file download (use Filtered converter for that)

## Troubleshooting

### Common Issues

**"ERROR: No listfile found in 0_Input"**
- Ensure you have a CSV file with "listfile" in its name in the `0_Input/` folder
- Check that the file has a `.csv` extension

**"WARNING: [TableName] table not found"**
- The script will skip that table and continue (not recommended)
- Some tables are optional (e.g., SoundKitAdvanced)
- All .db2 input should be present for best results

**Generated log files**
- Review any `.log` files in the script directory
- These identify:
  * FileDataIDs that couldn't be mapped to file paths (likely missing from community listfile)
  * Missing SoundKit entry settings (script uses default settings)
  * Skipped EffectRecID = 0 entries (prevents startup crashes)
- You may need to update your listfile or manually correct these entries

**Empty output files**
- Check that your input CSV files have data
- Verify CSV files are properly formatted
- Ensure character encoding is UTF-8

### Performance Notes

- Processing time depends on the size of input files
- Large listfiles (100,000+ entries) may take around 1 min to generate all .csv
- The script provides progress output for each processing step

## Version Compatibility

- **Source**: World of Warcraft Retail (any modern expansion should work but script was tested with 11.0+ retail version)
- **Target**: World of Warcraft 3.3.5a (Wrath of the Lich King)
- **Tested with**: Python 3.14

## Credits

- Blizzard
- https://github.com/wowdev/wow-listfile
- https://wago.tools/