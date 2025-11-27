# WoW Retail DB2 to WotLK 3.3.5a DBC Converter Suite

A collection of Python tools for downporting World of Warcraft Retail (11.0+) database files to WotLK 3.3.5a DBC format, with support for creature models, sounds, and visual effects.

## 🎯 Quick Overview

This suite contains three complementary tools:

1. **M2 Sound Events Extractor** - Extract hardcoded sound IDs from .m2 model files
2. **Full DB2 to DBC Converter** - Convert complete retail DB2 datasets to WotLK format  
3. **Filtered DB2 to DBC Converter** - Generate minimal DBC subsets for specific creature models

## 📦 Tools

### 1. M2 Sound Events Extractor
**File:** `m2_Hardcoded_SoundEntry_ID_extractor.py`

Extracts hardcoded SoundEntry IDs from M2 model files that aren't present in DB2 data.

**Usage:**
```bash
# Single file
python m2_Hardcoded_SoundEntry_ID_extractor.py /path/to/models/model.m2

# Entire directory (recursive)
python m2_Hardcoded_SoundEntry_ID_extractor.py /path/to/models/
```

**Output:** `4_M2_Hardcoded_SoundEntry_ID/M2_Hardcoded_SoundEntry_ID.csv`

📖 **[Full Documentation](M2_Sound_Events_Extractor_README.md)**

---

### 2. Filtered DB2 to DBC Converter
**File:** `DB2_to_DBC_Filtered.py`

Creates minimal DBC subsets for specific creature models you select.

**Features:**
- Interactive model selection (search by FileID or name)
- Generates only necessary data for selected models
- Automatically integrates M2 hardcoded sounds
- **Downloads audio files** from Wago.tools automatically
- Ideal for testing or partial conversions

**Usage:**
```bash
python DB2_to_DBC_Filtered.py
```

**Output:** 
- `3_DBC_Filtered/` (up to 14 CSV files + filtered listfile)
- `5_Downloaded_Sounds/` (audio files organized by folder structure)

📖 **[Full Documentation](DB2_to_DBC_Filtered_README.md)**

---

### 3. Full DB2 to DBC Converter
**File:** `DB2_to_DBC.py`

Converts complete retail DB2 datasets to WotLK 3.3.5a DBC format. Use this when you need complete DBC resources or want to create a comprehensive sound patch.

**Features:**
- Processes 22 different DBC tables
- Converts FileDataIDs to file paths
- Optional WotLK naming preservation
- WDBX Editor format support

**Usage:**
```bash
python DB2_to_DBC.py
```

**Output:** `2_DBCRetail_to_Wotlk_csv/` (22 CSV files)

📖 **[Full Documentation](DB2_to_DBC_README.md)**

---

## 🔄 Recommended Workflow

### For Specific Models (Most Common)
```
1. Run m2_Hardcoded_SoundEntry_ID_extractor.py → Extract M2 sounds
2. Run DB2_to_DBC_Filtered.py → Select models + generate minimal DBCs + download sounds
```

### For Complete DBC Resources / Mega Sound Patch
```
1. Run m2_Hardcoded_SoundEntry_ID_extractor.py → Extract M2 sounds (optional but recommended)
2. Run DB2_to_DBC.py → Full DBC dataset (all 22 tables)
```

## 📁 Required Directory Structure

```
/
├── DB2_to_DBC.py                      # Python script
├── DB2_to_DBC_Filtered.py                      # Python script
├── DB2_to_DBC.py                      # Python script
├── 0_Input/                           # Input files (required)
│   ├── listfile.csv                   # Community listfile
│   └── [Table].[version].csv          # DB2 tables from wago.tools
├── 1_DBCWotlk_csv/                    # WotLK reference data (optional)
│   ├── Wotlk_SoundEntries.csv
│   ├── Wotlk_VocalUISounds.csv
│   └── Wotlk_CreatureDisplayInfo.csv
├── 2_DBCRetail_to_Wotlk_csv/          # Full converter output
├── 3_DBC_Filtered/                    # Filtered converter output
├── 4_M2_Hardcoded_SoundEntry_ID/      # M2 extractor output
└── 5_Downloaded_Sounds/               # Downloaded audio files (filtered converter)
```

## 📋 Requirements

### Python Environment
- **Python 3.6+**
- **Standard library only** for most features
- **Optional:** `requests` module (for audio download feature in Filtered converter)

### Installing Optional Dependencies
```bash
# For audio download feature (Filtered converter only)
pip install requests
```

**Note:** If `requests` is not installed, the Filtered converter will skip the download feature and only generate CSV files.

### Required Input Files

**0_Input/ directory must contain:**
- Listfile CSV (from [wow-listfile](https://github.com/wowdev/wow-listfile))
- DB2 tables in CSV format (from [wago.tools](https://wago.tools/db2))

**Required tables** (minimum for core functionality):
- SoundKit, SoundKitEntry, SoundKitAdvanced
- CreatureDisplayInfo, CreatureModelData, CreatureSoundData
- CreatureDisplayInfoGeosetData
- NPCSounds, FootstepTerrainLookup
- ParticleColor
- ObjectEffect, ObjectEffectModifier, ObjectEffectPackageElem
- And more (see individual tool documentation)

## 🎮 Output Format

All tools generate **CSV files** compatible with:
- **WDBX Editor** (optional format with quoted fields)
- **Standard CSV** readers
- **WotLK 3.3.5a** DBC structure

## 🎵 Audio File Download (Filtered Converter Only)

The **Filtered DB2 to DBC Converter** includes an automatic sound download feature:

**Requirements:**
- Python `requests` module (install with: `pip install requests`)
- If not installed, the script will skip downloading and only generate CSV files

**Features:**
- Downloads audio files directly from Wago.tools
- Organizes files by folder structure (preserves hierarchy)
- Skips already downloaded files
- Shows download progress and success rate
- Provides locale installation instructions

**Output Directory:** `5_Downloaded_Sounds/`

**Locale Information:**
- Downloaded sounds are in **enUS locale**
- Most sounds go to `wow\data\` (music, creatures, spells, effects)
- Locale-specific sounds to `wow\data\[locale]\` (voices, NPC dialogue)

This feature makes it easy to get all necessary audio files for your filtered models in one step!
Though, if you need to use other locale sounds, then don't put the localized sounds in wow\data but in wow\data\[locale]
else main data will have priority over locale and you'll have english localized sound from wow.tools instead of your locale.

The download option does not feature other locale, you'll have to use wow.export or casc explorer for them.

## 🔍 What Gets Converted

### Covered Systems (22 DBC Tables)
✅ **Creature Sounds** - Attack, death, aggro, fidget, footsteps  
✅ **NPC Vocals** - Voice-overs and speech  
✅ **Ambient Sounds** - Day/night zone ambience  
✅ **Zone Music** - Background and intro music  
✅ **UI Sounds** - Vocal UI  
✅ **Weapon Sounds** - Impact sounds  
✅ **Emitters** - World sound emitters  
✅ **Effects** - Particle colors, object effects related sounds 
✅ **Creature Display** - Models, textures, geosets  

### Key Features
- **FileDataID → File Path** conversion
- **MD20/MD21** M2 format support
- **Recursive sound data** collection
- **Geoset calculation** for creature models
- **Texture mapping** for creature skins
- **Audio file downloads** to make .mpq patch faster
- **Terrain-based footsteps** (WotLK-compatible filtering)
- **Object effect chains** (state-based sounds, will filter missing SoundEntries ID to avoid game crash)

## 📊 Version Compatibility

- **Source:** WoW Retail 11.0+ (tested with 11.2.5)
- **Target:** WoW 3.3.5a (Wrath of the Lich King)
- **Tested:** Python 3.14

## 🚨 Important Notes

- **M2 extractor should run first** for best results (detects hardcoded sounds)
- **Filtered converter auto-detects** M2 extractor output
- **Log files generated** for unmapped FileDataIDs and data issues
- **Review logs** to identify missing listfile entries

## 📖 Detailed Documentation

Each tool has comprehensive documentation:

- **[DB2_to_DBC_README.md](DB2_to_DBC_README.md)** - Full converter guide
- **[DB2_to_DBC_Filtered_README.md](DB2_to_DBC_Filtered_README.md)** - Filtered converter guide  
- **[M2_Sound_Events_Extractor_README.md](M2_Sound_Events_Extractor_README.md)** - M2 extractor guide

## 🙏 Credits

- **Blizzard Entertainment** - World of Warcraft
- **[wow-listfile](https://github.com/wowdev/wow-listfile)** - Community listfile
- **[wago.tools](https://wago.tools/)** - DB2 data extraction
- **Alastor Strix'Efuartus** - M2.bt template (010 Editor)

## 📝 License

This project is provided as-is for World of Warcraft modding and research purposes.

---

**Questions?** Check the individual tool documentation or review the generated log files for troubleshooting.