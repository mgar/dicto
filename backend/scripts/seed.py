"""
Seed script: populates the database with initial Spanish learning content.

Usage (via Makefile):
    make seed

Direct usage inside container:
    python scripts/seed.py

The actual seeding logic lives in app/services/seed_service.py and is also
called automatically on every app startup, so running this script manually
is only necessary to seed outside of the normal startup flow.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.seed_service import seed_content

if __name__ == "__main__":
    print("Seeding database...")
    seed_content()
    print("Done.")
