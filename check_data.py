#!/usr/bin/env python3
"""
Diagnostic script to check available data before standardization
"""

import os
from pymongo import MongoClient
from datetime import datetime

def check_collections():
    """Check what collections and data are available"""
    
    # Configuration
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    DB_NAME = os.getenv("DATABASE", "speakers_db")
    
    print(f"Connecting to MongoDB...")
    print(f"URI: {MONGO_URI}")
    print(f"Database: {DB_NAME}")
    print("-" * 50)
    
    try:
        # Connect to MongoDB
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        db = client[DB_NAME]
        
        # Test connection
        client.server_info()
        print("✓ Connected to MongoDB successfully\n")
        
        # List all collections
        collections = db.list_collection_names()
        print(f"Found {len(collections)} collections in database:\n")
        
        # Expected source collections
        expected_collections = {
            "a_speakers": "A-Speakers.com data",
            "allamericanspeakers": "AllAmericanSpeakers.com data",
            "bigspeak_scraper": "BigSpeak.com data",
            "eventraptor": "EventRaptor.com data",
            "freespeakerbureau_scraper": "FreeSpeakerBureau.com data",
            "leading_authorities": "LeadingAuthorities.com data",
            "sessionize_scraper": "Sessionize.com data",
            "speakerhub_scraper": "SpeakerHub.com data",
            "thespeakerhandbook_scraper": "TheSpeakerHandbook.com data"
        }
        
        # Check each expected collection
        total_documents = 0
        found_collections = 0
        
        for collection_name, description in expected_collections.items():
            if collection_name in collections:
                count = db[collection_name].count_documents({})
                total_documents += count
                found_collections += 1
                print(f"✓ {collection_name:<30} {count:>8} documents - {description}")
                
                # Show sample document structure
                sample = db[collection_name].find_one()
                if sample:
                    fields = list(sample.keys())[:5]  # First 5 fields
                    print(f"  Sample fields: {', '.join(fields)}...")
            else:
                print(f"✗ {collection_name:<30} NOT FOUND - {description}")
        
        print(f"\nSummary:")
        print(f"- Found {found_collections}/{len(expected_collections)} expected collections")
        print(f"- Total source documents: {total_documents:,}")
        
        # Check if unified collection exists
        if "unified_speakers" in collections:
            unified_count = db["unified_speakers"].count_documents({})
            print(f"- Unified speakers collection: {unified_count:,} documents")
            
            if unified_count > 0:
                # Show last update time
                last_doc = db["unified_speakers"].find_one(
                    {}, 
                    sort=[("updated_at", -1), ("created_at", -1)]
                )
                if last_doc:
                    last_update = last_doc.get("updated_at") or last_doc.get("created_at")
                    if last_update:
                        print(f"- Last update: {last_update}")
        else:
            print("- Unified speakers collection: NOT CREATED YET")
        
        # Check for other collections
        other_collections = [c for c in collections if c not in expected_collections and c != "unified_speakers"]
        if other_collections:
            print(f"\nOther collections found:")
            for collection in other_collections:
                count = db[collection].count_documents({})
                print(f"  - {collection}: {count:,} documents")
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        print("\nTroubleshooting:")
        print("1. Make sure MongoDB is running")
        print("2. Check if the database name is correct")
        print("3. Verify MongoDB connection string")
        return False
    
    return True

if __name__ == "__main__":
    print("=== MongoDB Data Check ===\n")
    check_collections()