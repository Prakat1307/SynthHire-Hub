
from sqlalchemy.orm import Session as DBSession
from sqlalchemy import desc
from typing import Optional, Dict, List
from uuid import UUID
from datetime import datetime
import json
import os

class ModelRegistry:

    def __init__(self, db: DBSession):
        self.db = db

    def register_model(
        self,
        model_name: str,
        version: str,
        model_type: str,
        artifact_path: str,
        metrics: Dict = None,
        config: Dict = None,
    ) -> str:

        self.db.execute(
            """
            INSERT INTO ml_model_registry 
            (id, model_name, version, model_type, artifact_path, metrics, config, is_active, trained_at, created_at)
            VALUES (gen_random_uuid(), :name, :version, :type, :path, :metrics, :config, false, :trained, now())
            """,
            {
                "name": model_name,
                "version": version,
                "type": model_type,
                "path": artifact_path,
                "metrics": json.dumps(metrics or {}),
                "config": json.dumps(config or {}),
                "trained": datetime.utcnow(),
            },
        )
        self.db.commit()
        print(f"📝 Registered model: {model_name} v{version}")
        return version

    def activate_model(self, model_name: str, version: str):

        self.db.execute(
            "UPDATE ml_model_registry SET is_active = false WHERE model_name = :name",
            {"name": model_name},
        )
        
        self.db.execute(
            "UPDATE ml_model_registry SET is_active = true WHERE model_name = :name AND version = :version",
            {"name": model_name, "version": version},
        )
        self.db.commit()
        print(f"✅ Activated: {model_name} v{version}")

    def get_active_model(self, model_name: str) -> Optional[Dict]:

        result = self.db.execute(
            "SELECT * FROM ml_model_registry WHERE model_name = :name AND is_active = true LIMIT 1",
            {"name": model_name},
        ).fetchone()

        if result:
            return {
                "model_name": result.model_name,
                "version": result.version,
                "artifact_path": result.artifact_path,
                "metrics": json.loads(result.metrics) if result.metrics else {},
                "config": json.loads(result.config) if result.config else {},
            }
        return None

    def rollback(self, model_name: str) -> Optional[str]:

        results = self.db.execute(
            """
            SELECT version FROM ml_model_registry 
            WHERE model_name = :name 
            ORDER BY created_at DESC LIMIT 2
            """,
            {"name": model_name},
        ).fetchall()

        if len(results) < 2:
            print("⚠️ No previous version to rollback to")
            return None

        previous_version = results[1].version
        self.activate_model(model_name, previous_version)
        print(f"🔄 Rolled back {model_name} to v{previous_version}")
        return previous_version

    def list_versions(self, model_name: str) -> List[Dict]:

        results = self.db.execute(
            """
            SELECT model_name, version, is_active, metrics, created_at 
            FROM ml_model_registry 
            WHERE model_name = :name 
            ORDER BY created_at DESC
            """,
            {"name": model_name},
        ).fetchall()

        return [
            {
                "version": r.version,
                "is_active": r.is_active,
                "metrics": json.loads(r.metrics) if r.metrics else {},
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in results
        ]