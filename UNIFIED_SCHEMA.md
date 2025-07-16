# Unified Speaker Schema Documentation

## Overview
This document details the standardized schema used for unifying speaker data from multiple sources. The schema is designed to accommodate data from various speaker bureau websites while maintaining consistency and enabling cross-platform search and analysis.

## Schema Design Principles

1. **Completeness**: Capture all essential speaker information
2. **Flexibility**: Handle varying data availability across sources
3. **Consistency**: Use standard formats for common fields
4. **Traceability**: Maintain source information for each record
5. **Searchability**: Structure data for efficient querying

## Field-by-Field Documentation

### Core Identification
```json
{
  "_id": "string",
  "name": "string", 
  "display_name": "string"
}
```
- **_id**: SHA-1 hash of `source|source_id` for uniqueness
- **name**: Cleaned full name for matching/search
- **display_name**: Name as displayed on source site (may include titles)

### Professional Information
```json
{
  "job_title": "string",
  "description": "string", 
  "biography": "string",
  "tagline": "string"
}
```
- **job_title**: Current professional title/position
- **description**: Brief professional description (1-2 paragraphs)
- **biography**: Full biographical text
- **tagline**: Short motto or positioning statement

### Location Data
```json
{
  "location": {
    "city": "string",
    "state": "string",
    "country": "string",
    "full_location": "string"
  }
}
```
- Parsed from various formats: "City, State, Country" or structured data
- **full_location**: Original location string for reference

### Speaking Information
```json
{
  "speaking_info": {
    "fee_ranges": {
      "live_event": "string",
      "virtual_event": "string"
    },
    "languages": ["string"]
  }
}
```
- **fee_ranges**: May be exact amounts or ranges (e.g., "$5,000 - $10,000")
- **languages**: Speaking languages (not programming languages)

### Topics and Expertise
```json
{
  "topics": ["string"],
  "categories": ["string"],
  "topics_unmapped": ["string"]
}
```
- **topics**: Canonical topic terms after mapping
- **categories**: Duplicate of topics for backward compatibility
- **topics_unmapped**: Original terms that couldn't be mapped

### Content and Programs
```json
{
  "keynotes": [
    {
      "id": "string",
      "title": "string",
      "description": "string"
    }
  ]
}
```
- Specific speaking programs or keynote presentations
- Structure varies by source

### Reviews and Ratings
```json
{
  "reviews": [
    {
      "rating": "number",
      "text": "string",
      "author": "string",
      "author_title": "string",
      "author_organization": "string"
    }
  ],
  "ratings": {
    "average_rating": "number",
    "total_reviews": "number",
    "review_count": "number"
  }
}
```
- Not all sources provide reviews
- Rating scales may vary (typically 1-5)

### Media Assets
```json
{
  "media": {
    "profile_image": "string",
    "images": ["string"],
    "videos": [
      {
        "url": "string",
        "title": "string",
        "type": "string",
        "platform": "string"
      }
    ]
  }
}
```
- **profile_image**: Primary headshot/profile photo
- **videos**: May be objects or simple URL arrays depending on source

### Contact Information
```json
{
  "contact": {
    "email": "string",
    "phone": "string",
    "website": "string"
  }
}
```
- Only populated when publicly available
- May be empty for privacy reasons

### Publications
```json
{
  "books": [
    {
      "title": "string",
      "url": "string",
      "image_url": "string",
      "publisher": "string",
      "year": "string"
    }
  ]
}
```
- Books and other publications
- Structure varies significantly by source

### Source Tracking
```json
{
  "source_info": {
    "original_source": "string",
    "source_url": "string",
    "scraped_at": "datetime",
    "source_id": "string"
  }
}
```
- **original_source**: Which scraper provided this data
- **source_url**: Link to original profile
- **scraped_at**: When data was originally collected
- **source_id**: ID in source system

### Metadata
```json
{
  "created_at": "datetime",
  "updated_at": "datetime"
}
```
- **created_at**: When unified record was first created
- **updated_at**: Last modification in unified system

## Data Type Specifications

### Strings
- UTF-8 encoded
- Trimmed of leading/trailing whitespace
- Empty strings stored as null

### Dates
- ISO 8601 format
- UTC timezone
- Parsed from various source formats

### Arrays
- Empty arrays stored as empty `[]` not null
- Duplicates removed where appropriate

### Numbers
- Ratings: Float 0.0-5.0
- Counts: Integer >= 0

## Source-Specific Mappings

### A-Speakers
- Strong review/rating data
- Detailed keynote descriptions
- Video metadata

### AllAmericanSpeakers
- Comprehensive speaking topics
- Fee ranges for different event types
- Image galleries

### BigSpeak
- Nested location structure
- Topic objects with URLs
- "Please Inquire" for fees

### EventRaptor
- Email contact information
- Business areas as topics
- Event associations

### FreeSpeakerBureau
- Detailed contact information
- Member levels
- Areas of expertise + speaking topics

### LeadingAuthorities
- Books and publications
- Video collections
- Client testimonials

### Sessionize
- Tech-focused speakers
- Session history
- Social media links

### SpeakerHub
- Detailed fee structures
- Multiple location fields
- Professional titles

### TheSpeakerHandbook
- API-based data
- Membership information
- Gender and nationality

## Query Patterns

### Find by Name
```javascript
db.unified_speakers.find({
  "name": /john.*doe/i
})
```

### Find by Topic
```javascript
db.unified_speakers.find({
  "topics": "Leadership"
})
```

### Find by Location
```javascript
db.unified_speakers.find({
  "location.state": "California"
})
```

### Find by Fee Range
```javascript
db.unified_speakers.find({
  "speaking_info.fee_ranges.live_event": /$5,000/
})
```

### Find by Source
```javascript
db.unified_speakers.find({
  "source_info.original_source": "bigspeak"
})
```

## Indexes

Recommended indexes for performance:

```javascript
// Name search
db.unified_speakers.createIndex({"name": "text"})

// Topic search  
db.unified_speakers.createIndex({"topics": 1})

// Location search
db.unified_speakers.createIndex({"location.state": 1, "location.country": 1})

// Source tracking
db.unified_speakers.createIndex({"source_info.original_source": 1})

// Deduplication
db.unified_speakers.createIndex({"name": 1, "location.city": 1})
```

## Data Quality Considerations

1. **Name Variations**: Same speaker may have different name formats
2. **Location Granularity**: Some sources provide city, others just country
3. **Fee Transparency**: Many sources hide exact fees
4. **Topic Consistency**: Mapping required for cross-source search
5. **Media Availability**: Image/video URLs may expire
6. **Review Authenticity**: No verification of reviews across sources

## Future Enhancements

1. **Social Media Integration**: Standardize social profile links
2. **Availability Calendar**: Add booking availability
3. **Language Proficiency**: Structured language skills with levels
4. **Industry Specialization**: Additional categorization
5. **Certification Tracking**: Professional certifications
6. **Event History**: Past speaking engagements