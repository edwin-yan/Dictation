#!/usr/bin/env python3
"""
Seed script for Spelling Dictation application.
Extracts 4th Grade word lists from '4th Grade Non-negotiation List.pdf' and seeds mock students & histories.
"""
import sys
import argparse
from app import create_app
from app.models import db
from app.services.seeder import seed_database


def main():
    parser = argparse.ArgumentParser(description="Seed Dictation SQLite Database")
    parser.add_argument("--force", action="store_true", help="Drop existing tables and reseed from scratch")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        seed_database(app=app, force=args.force)


if __name__ == "__main__":
    main()
