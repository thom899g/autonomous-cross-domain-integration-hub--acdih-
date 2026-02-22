"""
Firebase Firestore Client with Connection Pooling and Error Recovery
Implements singleton pattern with automatic reconnection and connection pooling
"""
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime
from threading import Lock
import time

import firebase_admin
from firebase_admin import credentials, firestore, initialize_app, get_app, delete_app
from google.cloud.firestore_v1.client import Client as FirestoreClient
from google.cloud.firestore_v1.collection import CollectionReference
from google.cloud.firestore_v1.document import DocumentReference

from config.settings import config

logger = logging.getLogger(__name__)


class FirebaseConnectionPool:
    """Firebase connection pool for