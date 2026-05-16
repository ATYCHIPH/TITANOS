import uuid
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..config.settings import settings
from ..utils.logging import logger

class Session:
    """
    Represents a TITANOS user session.
    """
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.start_time = datetime.now()
        self.history: List[Dict[str, Any]] = []
        self.file_path = settings.DATA_DIR / "sessions" / f"{self.session_id}.json"
        
        # Ensure sessions directory exists
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if session_id:
            self.load()

    def add_interaction(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Adds a message to the session history."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
            "metadata": metadata or {}
        }
        self.history.append(entry)
        self.save()

    def save(self):
        """Saves the session to disk."""
        data = {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "history": self.history
        }
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save session {self.session_id}: {e}")

    def load(self):
        """Loads the session from disk."""
        if self.file_path.exists():
            try:
                with open(self.file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.start_time = datetime.fromisoformat(data["start_time"])
                    self.history = data["history"]
            except Exception as e:
                logger.error(f"Failed to load session {self.session_id}: {e}")

class SessionManager:
    """
    Manages multiple TITANOS sessions.
    """
    def __init__(self):
        self.sessions_dir = settings.DATA_DIR / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.active_session: Optional[Session] = None

    def create_session(self) -> Session:
        self.active_session = Session()
        logger.info(f"Created new session: {self.active_session.session_id}")
        return self.active_session

    def get_session(self, session_id: str) -> Session:
        return Session(session_id)

    def list_sessions(self) -> List[Dict[str, Any]]:
        sessions = []
        for p in self.sessions_dir.glob("*.json"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    sessions.append({
                        "id": data["session_id"],
                        "start_time": data["start_time"],
                        "message_count": len(data["history"])
                    })
            except Exception:
                continue
        return sorted(sessions, key=lambda x: x["start_time"], reverse=True)

# Global session manager
session_manager = SessionManager()
