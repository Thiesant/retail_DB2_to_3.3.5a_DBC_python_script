# retail_DB2_to_3.3.5a_DBC_python_script

## Description
This Python script converts World of Warcraft Retail .DB2 to WotLK 3.3.5a .DBC format.

Check Output sections to see which one are covered in this readme.md.

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
│   ├──Community-listifle (https://github.com/wowdev/wow-listfile)
│   └──`[table].[version]`.csv (https://wago.tools/db2)
├── 1_DBCWotlk_csv/
│   ├──Wotlk-CreatureDisplayInfo.csv #`BloodLevel` entries for CreatureDisplayInfo)
│   ├──Wotlk_VocalUISounds.csv   #`PissedSoundID_1`,`PissedSoundID_2` entries for VocalUISounds
│   └── Wotlk_SoundEntries.csv        # WotLK reference used for SounEntries wotlk names
└── 2_DBCRetail_to_Wotlk_csv/          # Output with downported .csv
````

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

### 1. Check files
Get the db2 version you want from wago.tools and put them in 0_Input
Get listfile from the listfile-community
Don't use duplicated tables with different version

### 2. Run the Script
Open terminal in scripts folder and use 

py DB2_to_DBC.py

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

**All files sorted by ID** (smallest to largest)
**FileDataIDs converted** file names and absolute paths
**Option to use WotLK sound entries name** entries from later expansion have generated name
**Header adjusted** to match WDBX 1.1.9.a
**File extensions updated** (.m2 → .mdx for CreatureModelData)
**Path separators normalized** (/ → \\)
**Option to skip some entries** (FootstepTerrainLookup is limited to TerrainSoundID from 0 to 10, using above id will crash the client without changes to the game)
**Option to format csv for WDBX Editor** (when enabled : quote all fields and convert float fields from . to ,)

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
- These identify FileDataIDs that couldn't be mapped to file paths (most likely missing from community-listfile), missing SoundKit entry settings (resort to arbitrary default settings), skipped EffectRecID = 0 (to avoid crash on start up)
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