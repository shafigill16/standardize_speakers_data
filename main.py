"""
Speaker Data Standardization System
Author: Shafi Gill
Created: 2025-01-16

This script unifies speaker data from 9 different MongoDB databases into a single
standardized collection. It handles data transformation, topic mapping, and 
intelligent deduplication to create a comprehensive speaker database.

Usage:
    export MONGO_URI="mongodb://admin:password@host:27017/?authSource=admin"
    export TARGET_DATABASE="speaker_database"
    python3 main.py
"""

import os
import re
import json
import hashlib
from datetime import datetime
from collections import defaultdict
from dateutil import parser as dt
from pymongo import MongoClient, UpdateOne
from rapidfuzz import fuzz, process

# ──────────────────────────────────────────────────────────────────────────────
# 0. CONFIG
# ──────────────────────────────────────────────────────────────────────────────
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
TARGET_DB_NAME = os.getenv("TARGET_DATABASE", "speaker_database")  # Where unified data goes

# Map of database names to their collection names and transformer functions
SRC_DATABASES = {
    "a_speakers": {
        "collection": "speakers",  # Collection name within the database
        "transformer": "unify_a_speakers"
    },
    "allamericanspeakers": {
        "collection": "speakers",
        "transformer": "unify_allamerican"
    },
    "bigspeak_scraper": {
        "collection": "speaker_profiles",
        "transformer": "unify_bigspeak"
    },
    "eventraptor": {
        "collection": "speakers",
        "transformer": "unify_eventraptor"
    },
    "freespeakerbureau_scraper": {
        "collection": "speakers_profiles",
        "transformer": "unify_freespeaker"
    },
    "leading_authorities": {
        "collection": "speakers_final_details",
        "transformer": "unify_leadingauth"
    },
    "sessionize_scraper": {
        "collection": "speaker_profiles",
        "transformer": "unify_sessionize"
    },
    "speakerhub_scraper": {
        "collection": "speaker_details",
        "transformer": "unify_speakerhub"
    },
    "thespeakerhandbook_scraper": {
        "collection": "speaker_profiles",
        "transformer": "unify_tsh"
    }
}

with open("/home/mudassir/work/shafi/standardize_data/config/topic_mapping.json", "r", encoding="utf-8") as f:
    TOPIC_MAP = json.load(f)        # {"Canonical Term": ["raw1", "raw2", ...]}

REV_TOPIC_MAP = {raw:tgt for tgt,v in TOPIC_MAP.items() for raw in v}

# ──────────────────────────────────────────────────────────────────────────────
# 1. UTILITIES
# ──────────────────────────────────────────────────────────────────────────────
def sha_id(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()

def parse_location(loc: str) -> dict:
    """
    Splits common 'City, State, Country' patterns.
    If a dict is already supplied (e.g., BigSpeak), it is passed through.
    """
    if not loc:
        return {}
    if isinstance(loc, dict):
        return {
            "city"         : loc.get("city"),
            "state"        : loc.get("state") or loc.get("state_province"),
            "country"      : loc.get("country"),
            "full_location": ", ".join([v for v in loc.values() if v])
        }
    parts = [p.strip() for p in loc.split(",")]
    if len(parts) == 3:
        city, state, country = parts
    elif len(parts) == 2:
        city, state, country = parts[0], None, parts[1]
    else:
        city, state, country = None, None, parts[0]
    return {
        "city"         : city,
        "state"        : state,
        "country"      : country,
        "full_location": loc
    }

def norm_topics(topics):
    """Convert list of topic strings to canonical list + unmapped list."""
    canon, unmapped = set(), set()
    for t in topics or []:
        t_clean = re.sub(r"\s+", " ", t).strip()
        if t_clean in REV_TOPIC_MAP:
            canon.add(REV_TOPIC_MAP[t_clean])
        else:
            canon.add(t_clean)
            unmapped.add(t_clean)
    return sorted(canon), sorted(unmapped)

def safe_date(value):
    try:
        return dt.parse(value) if isinstance(value, str) else value
    except Exception:
        return None

# ──────────────────────────────────────────────────────────────────────────────
# 2. TRANSFORMERS (one per source)
# ──────────────────────────────────────────────────────────────────────────────
def unify_a_speakers(doc: dict) -> dict:
    topics, unmapped = norm_topics(doc.get("topics"))
    return {
        "_id"          : sha_id("a_speakers|" + str(doc["_id"])),
        "name"         : doc.get("name"),
        "display_name" : doc.get("name"),
        "job_title"    : doc.get("job_title"),
        "description"  : doc.get("description"),
        "biography"    : doc.get("full_bio"),
        "tagline"      : None,
        "location"     : parse_location(doc.get("location")),
        "speaking_info": {
            "fee_ranges": {"live_event": doc.get("fee_range")},
            "languages" : [doc.get("languages")] if doc.get("languages") else None
        },
        "topics"            : topics,
        "categories"        : topics,
        "topics_unmapped"   : unmapped,
        "keynotes"          : doc.get("keynotes", []),
        "reviews"           : doc.get("reviews", []),
        "ratings"           : {
            "average_rating": doc.get("average_rating"),
            "total_reviews" : doc.get("total_reviews")
        },
        "media": {
            "profile_image": doc.get("image_url"),
            "videos"       : doc.get("videos")
        },
        "source_info": {
            "original_source": "a_speakers",
            "source_url"     : doc.get("url"),
            "scraped_at"     : safe_date(doc.get("scraped_at")),
            "source_id"      : str(doc.get("_id"))
        }
    }

def unify_allamerican(doc):
    tops, unmapped = norm_topics(doc.get("categories", []) + [t["title"] for t in doc.get("speaking_topics", [])])
    return {
        "_id"        : sha_id("allamerican|" + doc["speaker_id"]),
        "name"       : doc.get("name"),
        "display_name": doc.get("name"),
        "job_title"  : doc.get("job_title"),
        "biography"  : doc.get("biography"),
        "location"   : parse_location(doc.get("location")),
        "speaking_info": {
            "fee_ranges": doc.get("fee_range")
        },
        "topics"     : tops,
        "categories" : tops,
        "topics_unmapped": unmapped,
        "keynotes"   : doc.get("speaking_topics"),
        "media": {
            "profile_image": next((i["url"] for i in doc.get("images", []) if i["type"]=="profile"), None),
            "videos" : doc.get("videos")
        },
        "ratings": doc.get("rating"),
        "reviews": doc.get("reviews"),
        "source_info": {
            "original_source": "allamericanspeakers",
            "source_url"     : doc.get("url"),
            "scraped_at"     : safe_date(doc.get("scraped_at")),
            "source_id"      : doc.get("speaker_id")
        }
    }

def unify_bigspeak(doc):
    topics, unmapped = norm_topics([t["name"] for t in doc.get("topics", [])])
    return {
        "_id"         : sha_id("bigspeak|" + doc["speaker_id"]),
        "name"        : doc.get("name"),
        "display_name": doc.get("name"),
        "job_title"   : None,
        "description" : doc.get("description"),
        "biography"   : doc.get("description"),
        "location"    : parse_location(doc.get("location", {}).get("travels_from")),
        "speaking_info": {
            "fee_ranges": {"live_event": doc.get("fee_range")}
        },
        "topics"     : topics,
        "categories" : topics,
        "topics_unmapped": unmapped,
        "media": {
            "profile_image": doc.get("image_url")
        },
        "source_info": {
            "original_source": "bigspeak",
            "source_url"     : doc.get("profile_url"),
            "scraped_at"     : safe_date(doc.get("scraped_at")),
            "source_id"      : doc.get("speaker_id")
        }
    }

def unify_eventraptor(doc):
    topics, unmapped = norm_topics(doc.get("business_areas"))
    return {
        "_id"        : sha_id("eventraptor|" + doc["speaker_id"]),
        "name"       : doc.get("name"),
        "display_name": doc.get("name"),
        "tagline"    : doc.get("tagline"),
        "biography"  : doc.get("biography"),
        "contact": {
            "email": doc.get("email")
        },
        "location": {},
        "topics"     : topics,
        "categories" : topics,
        "topics_unmapped": unmapped,
        "media": {
            "profile_image": doc.get("profile_image")
        },
        "source_info": {
            "original_source": "eventraptor",
            "source_url"     : doc.get("url"),
            "scraped_at"     : safe_date(doc.get("scraped_at")),
            "source_id"      : doc.get("speaker_id")
        }
    }

def unify_freespeaker(doc):
    topics, unmapped = norm_topics(doc.get("areas_of_expertise", []) + doc.get("speaking_topics", []))
    return {
        "_id"         : sha_id("freespeaker|" + str(doc["_id"])),
        "name"        : doc.get("name"),
        "display_name": doc.get("name"),
        "job_title"   : doc.get("role"),
        "biography"   : doc.get("biography"),
        "location"    : parse_location(doc.get("location")),
        "speaking_info": {
            "fee_ranges": None
        },
        "topics"      : topics,
        "categories"  : topics,
        "topics_unmapped": unmapped,
        "media": {
            "profile_image": doc.get("image_url")
        },
        "contact": {
            "phone": doc.get("contact_info", {}).get("phone"),
            "website": doc.get("website")
        },
        "source_info": {
            "original_source": "freespeakerbureau",
            "source_url"     : doc.get("profile_url"),
            "scraped_at"     : safe_date(doc.get("scraped_at")),
            "source_id"      : str(doc["_id"])
        }
    }

def unify_leadingauth(doc):
    topics, unmapped = norm_topics([t["name"] for t in doc.get("topics_and_types", [])])
    return {
        "_id"        : sha_id("leadingauth|" + doc["speaker_page_url"]),
        "name"       : doc.get("name"),
        "job_title"  : doc.get("job_title"),
        "description": doc.get("description"),
        "biography"  : doc.get("description"),
        "location"   : {},
        "speaking_info": {
            "fee_ranges": doc.get("speaker_fees")
        },
        "topics"     : topics,
        "categories" : topics,
        "topics_unmapped": unmapped,
        "books"      : doc.get("books_and_publications"),
        "media": {
            "profile_image": doc.get("speaker_image_url"),
            "videos"       : doc.get("videos")
        },
        "source_info": {
            "original_source": "leadingauthorities",
            "source_url"     : doc.get("speaker_page_url"),
            "scraped_at"     : safe_date(doc.get("scraped_at")),
            "source_id"      : str(doc.get("_id"))
        }
    }

def unify_sessionize(doc):
    tops, unmapped = norm_topics(doc.get("professional_info", {}).get("topics", []))
    basic = doc.get("basic_info", {})
    username = basic.get("username") or doc.get("username") or str(doc.get("_id", ""))
    return {
        "_id"         : sha_id("sessionize|" + username),
        "name"        : basic.get("name") or doc.get("name"),
        "display_name": basic.get("name") or doc.get("name"),
        "tagline"     : basic.get("tagline"),
        "biography"   : basic.get("bio"),
        "location"    : parse_location(basic.get("location")),
        "topics"      : tops,
        "categories"  : tops,
        "topics_unmapped": unmapped,
        "media": {
            "profile_image": basic.get("profile_picture")
        },
        "source_info": {
            "original_source": "sessionize",
            "source_url"     : basic.get("url"),
            "scraped_at"     : safe_date(doc.get("metadata", {}).get("scraped_at")),
            "source_id"      : username
        }
    }

def unify_speakerhub(doc):
    tops, unmapped = norm_topics(doc.get("topic_categories", []) + doc.get("topics", []))
    # Build location string from available parts
    location_parts = []
    if doc.get("city"):
        location_parts.append(doc.get("city"))
    if doc.get("state_province") or doc.get("state"):
        location_parts.append(doc.get("state_province") or doc.get("state"))
    if doc.get("country"):
        location_parts.append(doc.get("country"))
    location_str = ", ".join(location_parts) if location_parts else ""
    
    return {
        "_id"        : sha_id("speakerhub|" + str(doc.get("_id", ""))),
        "name"       : doc.get("name"),
        "display_name": doc.get("name"),
        "job_title"  : doc.get("job_title") or doc.get("professional_title"),
        "biography"  : doc.get("full_bio") or doc.get("bio_summary"),
        "location"   : parse_location(location_str),
        "speaking_info": {
            "fee_ranges": doc.get("speaker_fees") or doc.get("fee_range")
        },
        "topics"     : tops,
        "categories" : tops,
        "topics_unmapped": unmapped,
        "media": {
            "profile_image": doc.get("profile_picture_url") or doc.get("profile_picture")
        },
        "source_info": {
            "original_source": "speakerhub",
            "source_url"     : doc.get("profile_url"),
            "scraped_at"     : safe_date(doc.get("scraped_at")),
            "source_id"      : str(doc.get("_id", ""))
        }
    }

def unify_tsh(doc):
    tops, unmapped = norm_topics(doc.get("topics"))
    speaker_id = doc.get("speaker_id") or str(doc.get("_id", ""))
    return {
        "_id"        : sha_id("tsh|" + speaker_id),
        "name"       : doc.get("display_name"),
        "display_name": doc.get("display_name"),
        "job_title"  : doc.get("job_title"),
        "biography"  : doc.get("biography"),
        "location"   : parse_location(doc.get("travels_from") or doc.get("home_country")),
        "topics"     : tops,
        "categories" : tops,
        "topics_unmapped": unmapped,
        "media": {
            "profile_image": doc.get("image_url_hd") or doc.get("image_url")
        },
        "source_info": {
            "original_source": "thespeakerhandbook",
            "source_url"     : doc.get("profile_url"),
            "scraped_at"     : safe_date(doc.get("scraped_at")),
            "source_id"      : speaker_id
        }
    }

# ──────────────────────────────────────────────────────────────────────────────
# 3. DEDUPLICATION HELPERS
# ──────────────────────────────────────────────────────────────────────────────
def fingerprint_name(name):
    return re.sub(r"[^a-z]", "", name.lower()) if name else ""

def build_dedupe_index(collection):
    index = defaultdict(list)
    for doc in collection.find({}, {"_id":1, "name":1, "location.city":1}):
        key = fingerprint_name(doc.get("name"))
        if key:
            index[key].append((doc["_id"], doc.get("location", {}).get("city")))
    return index

def find_duplicate(unified_doc, index):
    key = fingerprint_name(unified_doc["name"])
    cands = index.get(key, [])
    best = None
    for _id, city in cands:
        score = fuzz.ratio(unified_doc["name"], unified_doc.get("name"))
        if city and unified_doc["location"].get("city") and city.lower()==unified_doc["location"]["city"].lower():
            score += 10  # bonus for same city
        if score > 90:
            best = _id
            break
    return best

# ──────────────────────────────────────────────────────────────────────────────
# 4. MAIN
# ──────────────────────────────────────────────────────────────────────────────
def run():
    client = MongoClient(MONGO_URI)
    target_db = client[TARGET_DB_NAME]
    unified = target_db["unified_speakers"]

    # Build quick dedupe index from existing unified records
    print("Building deduplication index...")
    dedupe_idx = build_dedupe_index(unified)

    bulk_ops = []
    total_in, total_upd, total_new = 0, 0, 0

    # Process each source database
    for db_name, config in SRC_DATABASES.items():
        print(f"\nProcessing {db_name}...")
        
        # Check if database exists
        if db_name not in client.list_database_names():
            print(f"  - Database not found, skipping")
            continue
            
        src_db = client[db_name]
        collection_name = config["collection"]
        
        # Check if collection exists
        if collection_name not in src_db.list_collection_names():
            # Try to find any collection with 'speaker' in the name
            speaker_collections = [c for c in src_db.list_collection_names() if 'speaker' in c.lower()]
            if speaker_collections:
                collection_name = speaker_collections[0]
                print(f"  - Using collection: {collection_name}")
            else:
                print(f"  - No speaker collection found, skipping")
                continue
        
        src_col = src_db[collection_name]
        transformer = globals()[config["transformer"]]
        
        count = 0
        for doc in src_col.find({}):
            total_in += 1
            count += 1
            u_doc = transformer(doc)
            dup_id = find_duplicate(u_doc, dedupe_idx)

            if dup_id:               # update existing record
                u_doc["updated_at"] = datetime.utcnow()
                # Remove _id from update document as it's immutable
                update_doc = {k: v for k, v in u_doc.items() if k != "_id"}
                bulk_ops.append(
                    UpdateOne({"_id": dup_id}, {"$set": update_doc})
                )
                total_upd += 1
            else:                    # insert new record
                u_doc["created_at"] = datetime.utcnow()
                bulk_ops.append(UpdateOne({"_id": u_doc["_id"]}, {"$setOnInsert": u_doc}, upsert=True))
                total_new += 1
                dedupe_idx[fingerprint_name(u_doc["name"])].append((u_doc["_id"], u_doc["location"].get("city")))

            # Execute every 1k ops to avoid huge batches
            if len(bulk_ops) >= 1000:
                unified.bulk_write(bulk_ops, ordered=False)
                bulk_ops = []
        
        print(f"  - Processed {count} documents")

    if bulk_ops:
        unified.bulk_write(bulk_ops, ordered=False)

    print(f"\n{'='*50}")
    print(f"Standardization Complete!")
    print(f"{'='*50}")
    print(f"Ingested  : {total_in:,}")
    print(f"New       : {total_new:,}")
    print(f"Updated   : {total_upd:,}")
    print(f"Total now : {unified.count_documents({}):,}")

if __name__ == "__main__":
    run()