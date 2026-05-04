"""
Load development-only sample learning data for the default test user.

Usage via Makefile:
    make dev-sample-data

Direct usage inside the backend container:
    DICTO_DEV_SAMPLE_DATA=1 python scripts/dev_sample_data.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.services.dev_sample_data_service import load_dev_sample_data


if __name__ == "__main__":
    print("Loading development sample data...")
    summary = load_dev_sample_data()
    print(
        "Done. "
        f"user={summary['user_email']} "
        f"time_zone={summary['time_zone']} "
        f"review_states={summary['review_states']} "
        f"review_logs={summary['review_logs']} "
        f"pending_reviews={summary['pending_reviews']}"
    )
