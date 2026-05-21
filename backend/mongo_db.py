"""
backend/mongo_db.py
===================
Optional MongoDB interface using PyMongo.
Set MONGO_URI in .env to activate. The app works with SQLite by default.
"""

from pymongo import MongoClient
from datetime import datetime
from config import Config
import json


_client = None
_db     = None


def get_db():
    global _client, _db
    if _db is None:
        _client = MongoClient(Config.MONGO_URI)
        _db     = _client['resume_analyzer']
    return _db


def save_analysis(data: dict) -> str:
    """Insert one analysis document; return its inserted _id as string."""
    collection = get_db()['analyses']
    data['created_at'] = datetime.utcnow()
    result = collection.insert_one(data)
    return str(result.inserted_id)


def get_all_analyses(limit: int = 100) -> list[dict]:
    """Fetch the most recent `limit` analysis documents."""
    collection = get_db()['analyses']
    docs = collection.find({}, {'_id': 1, 'filename': 1, 'ats_score': 1,
                                 'ats_grade': 1, 'created_at': 1}) \
                     .sort('created_at', -1).limit(limit)
    results = []
    for doc in docs:
        doc['id'] = str(doc.pop('_id'))
        results.append(doc)
    return results


def get_analysis_by_id(doc_id: str) -> dict | None:
    """Fetch a single analysis by its MongoDB ObjectId string."""
    from bson import ObjectId
    collection = get_db()['analyses']
    doc = collection.find_one({'_id': ObjectId(doc_id)})
    if doc:
        doc['id'] = str(doc.pop('_id'))
    return doc


def get_stats() -> dict:
    """Return aggregate stats for the admin dashboard."""
    collection = get_db()['analyses']
    pipeline = [
        {
            '$group': {
                '_id': None,
                'total':     {'$sum': 1},
                'avg_score': {'$avg': '$ats_score'},
                'max_score': {'$max': '$ats_score'},
                'min_score': {'$min': '$ats_score'},
            }
        }
    ]
    result = list(collection.aggregate(pipeline))
    return result[0] if result else {}
