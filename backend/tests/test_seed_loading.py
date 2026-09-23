import unittest

from sqlalchemy import MetaData, String, create_engine, event
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Session

from app.db import Base
from app.models import TeamProfile
from app.seed import TEAM_IDS, seed_database


class SeedLoadingTests(unittest.TestCase):
    def test_foreign_keys_and_repeat_preserve_existing_data(self):
        engine = create_engine("sqlite://")

        @event.listens_for(engine, "connect")
        def enforce_foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")

        # SQLite must store numeric-only UUIDs as text, not rounded numbers.
        metadata = MetaData()
        for table in Base.metadata.sorted_tables:
            clone = table.to_metadata(metadata)
            for column in clone.columns:
                if isinstance(column.type, UUID):
                    column.type = String(32)
        metadata.create_all(engine)
        try:
            with Session(engine, autoflush=False) as session:
                self.assertEqual(seed_database(session), dict.fromkeys(
                    ("drafts", "cards", "teams", "proposals"), 5))
                team = session.get(TeamProfile, TEAM_IDS[0])
                team.name = "Edited team"
                session.commit()
                self.assertEqual(seed_database(session), dict.fromkeys(
                    ("drafts", "cards", "teams", "proposals"), 0))
                session.expire_all()
                self.assertEqual(session.get(TeamProfile, TEAM_IDS[0]).name, "Edited team")
        finally:
            engine.dispose()
