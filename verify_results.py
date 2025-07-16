#!/usr/bin/env python3
"""
Verify standardization results
"""

import os
from pymongo import MongoClient
from collections import Counter

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
TARGET_DATABASE = os.getenv("TARGET_DATABASE", "speaker_database")

def verify_results():
    client = MongoClient(MONGO_URI)
    db = client[TARGET_DATABASE]
    unified = db["unified_speakers"]
    
    print("=== Standardization Verification ===\n")
    
    # Basic stats
    total_count = unified.count_documents({})
    print(f"Total unified speakers: {total_count:,}")
    
    # Source distribution
    print("\nSpeakers by source:")
    sources = list(unified.aggregate([
        {"$group": {"_id": "$source_info.original_source", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}}
    ]))
    for source in sources:
        print(f"  {source['_id']:<30} {source['count']:>8,}")
    
    # Sample data quality checks
    print("\nData quality metrics:")
    
    # Check fields population
    with_bio = unified.count_documents({"biography": {"$ne": None, "$ne": ""}})
    with_location = unified.count_documents({"location.city": {"$ne": None, "$ne": ""}})
    with_topics = unified.count_documents({"topics": {"$ne": [], "$exists": True}})
    with_image = unified.count_documents({"media.profile_image": {"$ne": None, "$ne": ""}})
    
    print(f"  With biography: {with_bio:,} ({with_bio/total_count*100:.1f}%)")
    print(f"  With location:  {with_location:,} ({with_location/total_count*100:.1f}%)")
    print(f"  With topics:    {with_topics:,} ({with_topics/total_count*100:.1f}%)")
    print(f"  With image:     {with_image:,} ({with_image/total_count*100:.1f}%)")
    
    # Top topics
    print("\nTop 20 topics:")
    topic_pipeline = [
        {"$unwind": "$topics"},
        {"$group": {"_id": "$topics", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 20}
    ]
    topics = list(unified.aggregate(topic_pipeline))
    for topic in topics:
        print(f"  {topic['_id']:<30} {topic['count']:>6,}")
    
    # Unmapped topics
    print("\nTop unmapped topics (need mapping):")
    unmapped_pipeline = [
        {"$unwind": "$topics_unmapped"},
        {"$group": {"_id": "$topics_unmapped", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 10}
    ]
    unmapped = list(unified.aggregate(unmapped_pipeline))
    for topic in unmapped:
        print(f"  {topic['_id']:<30} {topic['count']:>6,}")
    
    # Sample speakers
    print("\nSample unified speakers:")
    samples = unified.find().limit(3)
    for i, speaker in enumerate(samples, 1):
        print(f"\n{i}. {speaker.get('name', 'Unknown')}")
        print(f"   Source: {speaker.get('source_info', {}).get('original_source')}")
        print(f"   Topics: {', '.join(speaker.get('topics', [])[:5])}")
        if speaker.get('location', {}).get('city'):
            print(f"   Location: {speaker['location'].get('city')}, {speaker['location'].get('country')}")

if __name__ == "__main__":
    verify_results()