# Speaker Data Standardization System

A comprehensive ETL (Extract, Transform, Load) system that unifies speaker data from multiple speaker bureau websites into a single, standardized MongoDB collection.

## Table of Contents
- [Overview](#overview)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Running the System](#running-the-system)
- [Data Sources](#data-sources)
- [Unified Schema](#unified-schema)
- [Topic Mapping](#topic-mapping)
- [Deduplication](#deduplication)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)
- [Extending the System](#extending-the-system)

## Overview

This system consolidates speaker data from 9 different speaker bureau databases into a unified format, enabling:
- Cross-platform speaker search
- Consistent data structure
- Duplicate speaker detection and merging
- Topic standardization
- Data quality improvement

### Key Features
- **Multi-source Integration**: Processes data from 9 different speaker platforms
- **Smart Deduplication**: Uses fuzzy matching to identify and merge duplicate speakers
- **Topic Mapping**: Standardizes topics to canonical terms for consistent categorization
- **Flexible Schema**: Accommodates varying data availability across sources
- **Source Tracking**: Maintains full traceability to original data sources

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Source DB 1   │     │   Source DB 2   │     │   Source DB N   │
│  (a_speakers)   │     │ (allamerican)   │     │  (speakerhub)   │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         └───────────────────────┴───────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Standardization       │
                    │   ─────────────────     │
                    │ • Extract from DBs      │
                    │ • Transform to unified  │
                    │ • Map topics            │
                    │ • Deduplicate speakers  │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │   Unified Collection    │
                    │  speaker_database.      │
                    │  unified_speakers       │
                    └─────────────────────────┘
```

## Prerequisites

- Python 3.6 or higher
- MongoDB 4.0 or higher
- Network access to MongoDB server
- At least 4GB RAM for processing large datasets

## Installation

1. **Clone or navigate to the project**:
```bash
cd /home/mudassir/work/shafi/standardize_data
```

2. **Create virtual environment** (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## Configuration

### Environment Variables

Set these before running the standardization:

```bash
export MONGO_URI="mongodb://admin:password@host:27017/?authSource=admin"
export TARGET_DATABASE="speaker_database"  # Target database name
```

### Topic Mapping Configuration

The system uses `config/topic_mapping.json` to standardize topics:

```json
{
  "Leadership": [
    "Leadership Development",
    "Executive Leadership",
    "Leading Teams"
  ],
  "Innovation": [
    "Innovation & Creativity",
    "Disruptive Innovation"
  ]
}
```

## Running the System

### Basic Usage

```bash
# Set MongoDB connection
export MONGO_URI="mongodb://your-connection-string"
export TARGET_DATABASE="speaker_database"

# Run standardization
python3 main.py
```

### Using the Setup Script

```bash
# Make script executable
chmod +x setup_and_run.sh

# Run with automatic setup
./setup_and_run.sh
```

### Expected Output

```
Building deduplication index...

Processing a_speakers...
  - Processed 3592 documents

Processing allamericanspeakers...
  - Processed 4666 documents

...

==================================================
Standardization Complete!
==================================================
Ingested  : 50,338
New       : 20,783
Updated   : 29,555
Total now : 46,243
```

## Data Sources

The system processes data from these databases:

| Database | Website | Collection | Document Count |
|----------|---------|------------|----------------|
| `a_speakers` | a-speakers.com | speakers | ~3,500 |
| `allamericanspeakers` | allamericanspeakers.com | speakers | ~4,600 |
| `bigspeak_scraper` | bigspeak.com | speaker_profiles | ~2,200 |
| `eventraptor` | eventraptor.com | speakers | ~3,000 |
| `freespeakerbureau_scraper` | freespeakerbureau.com | speakers_profiles | ~400 |
| `leading_authorities` | leadingauthorities.com | speakers_final_details | ~1,200 |
| `sessionize_scraper` | sessionize.com | speaker_profiles | ~12,800 |
| `speakerhub_scraper` | speakerhub.com | speaker_details | ~18,900 |
| `thespeakerhandbook_scraper` | thespeakerhandbook.com | speaker_profiles | ~3,500 |

## Unified Schema

The standardized schema provides consistent structure across all sources:

### Core Fields
- `_id`: SHA-1 hash of source|source_id
- `name`: Speaker's full name
- `display_name`: Name as displayed on source
- `job_title`: Professional title
- `biography`: Full bio text
- `tagline`: Short positioning statement

### Location
```json
{
  "location": {
    "city": "New York",
    "state": "NY",
    "country": "USA",
    "full_location": "New York, NY, USA"
  }
}
```

### Topics & Categories
- `topics`: Array of canonical topic terms
- `categories`: Duplicate of topics (for compatibility)
- `topics_unmapped`: Topics that need mapping

### Speaking Information
```json
{
  "speaking_info": {
    "fee_ranges": {
      "live_event": "$10,000 - $20,000",
      "virtual_event": "$5,000 - $10,000"
    },
    "languages": ["English", "Spanish"]
  }
}
```

### Media & Reviews
- `media.profile_image`: Main profile photo URL
- `media.videos`: Array of video information
- `reviews`: Array of client reviews
- `ratings`: Aggregate rating information

### Source Tracking
```json
{
  "source_info": {
    "original_source": "speakerhub",
    "source_url": "https://speakerhub.com/speaker/john-doe",
    "scraped_at": "2024-01-15T10:30:00Z",
    "source_id": "12345"
  }
}
```

### Metadata
- `created_at`: When unified record was created
- `updated_at`: Last update timestamp

See [UNIFIED_SCHEMA.md](UNIFIED_SCHEMA.md) for complete field documentation.

## Topic Mapping

Topics are standardized using a mapping configuration:

1. **Raw topics** from sources are cleaned
2. **Mapped** to canonical terms using `config/topic_mapping.json`
3. **Unmapped topics** are preserved for review

Example mapping:
- "AI", "Machine Learning" → "Artificial Intelligence"
- "DEI", "Diversity and Inclusion" → "Diversity & Inclusion"

## Deduplication

The system uses intelligent deduplication:

1. **Name Fingerprinting**: Creates lowercase, alphanumeric fingerprints
2. **Fuzzy Matching**: Uses Levenshtein distance (>90% similarity)
3. **Location Bonus**: Additional weight for matching cities
4. **Update vs Insert**: Existing records are updated, not duplicated

## Verification

After standardization, verify the results:

```bash
python3 verify_results.py
```

This shows:
- Total unified speakers
- Distribution by source
- Data quality metrics
- Top topics
- Unmapped topics needing attention

## Troubleshooting

### MongoDB Connection Issues
```bash
# Test connection
python3 check_data.py

# Common fixes:
- Verify MongoDB is running
- Check authentication credentials
- Ensure network connectivity
- Verify database permissions
```

### Missing Source Data
- Ensure source databases exist
- Check collection names match configuration
- Verify data has been scraped

### Memory Issues
For large datasets:
```bash
# Increase batch size in main.py
if len(bulk_ops) >= 2000:  # Increase from 1000
```

### Topic Mapping
Review unmapped topics:
```javascript
// In MongoDB shell
db.unified_speakers.distinct("topics_unmapped")
```

## Extending the System

### Adding a New Source

1. **Add to SRC_DATABASES** in `main.py`:
```python
"new_source": {
    "collection": "speakers",
    "transformer": "unify_new_source"
}
```

2. **Create transformer function**:
```python
def unify_new_source(doc):
    topics, unmapped = norm_topics(doc.get("topics"))
    return {
        "_id": sha_id("new_source|" + str(doc["_id"])),
        "name": doc.get("name"),
        # ... map other fields
    }
```

### Modifying Topic Mappings

Edit `config/topic_mapping.json`:
```json
{
  "New Category": [
    "raw term 1",
    "raw term 2"
  ]
}
```

### Custom Deduplication Rules

Modify `find_duplicate()` in `main.py` to add custom matching logic.

## Performance Optimization

- **Batch Processing**: Operations are batched at 1000 documents
- **Index Usage**: Deduplication index is built in memory
- **Bulk Writes**: Uses MongoDB bulk operations

For very large datasets (>1M documents), consider:
- Running source databases separately
- Increasing system RAM
- Using MongoDB sharding

## Data Quality

Regular maintenance tasks:

1. **Review unmapped topics** monthly
2. **Check for duplicate speakers** quarterly
3. **Validate image/video URLs** periodically
4. **Update topic mappings** as needed

## Support

For issues or questions:
1. Check error messages and logs
2. Verify MongoDB connectivity
3. Review source data availability
4. Ensure sufficient system resources

---

Last Updated: January 2024