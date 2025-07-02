#!/usr/bin/env python3
"""
Seed script to populate the database with default expense categories.
Run this script to add common expense categories to your database.
"""

import logging
import sys
from pathlib import Path

# Add the project root to the Python path so we can import our modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.app.config.logging import get_logger, setup_logging
from backend.app.db.database import SessionLocal
from backend.app.models.expenses import Category

# Initialize logging
setup_logging()
logger = get_logger("seed")

# Common expense categories
DEFAULT_CATEGORIES = [
    {
        "name": "Food & Dining",
        "description": "Restaurants, groceries, and food expenses",
    },
    {"name": "Transportation", "description": "Gas, public transport, car maintenance"},
    {"name": "Shopping", "description": "Clothing, electronics, and general purchases"},
    {
        "name": "Entertainment",
        "description": "Movies, games, books, and leisure activities",
    },
    {
        "name": "Bills & Utilities",
        "description": "Electricity, water, internet, phone bills",
    },
    {
        "name": "Healthcare",
        "description": "Medical expenses, pharmacy, health insurance",
    },
    {"name": "Travel", "description": "Vacation, business trips, accommodation"},
    {"name": "Education", "description": "Courses, books, training, school fees"},
    {"name": "Home & Garden", "description": "Home improvement, furniture, gardening"},
    {"name": "Insurance", "description": "Life, car, home insurance payments"},
    {"name": "Investments", "description": "Stocks, bonds, retirement contributions"},
    {"name": "Gifts & Donations", "description": "Presents, charity, donations"},
    {"name": "Personal Care", "description": "Haircuts, cosmetics, personal hygiene"},
    {"name": "Business", "description": "Business expenses, office supplies"},
    {"name": "Taxes", "description": "Income tax, property tax, other tax payments"},
    {
        "name": "Miscellaneous",
        "description": "Other expenses that don't fit other categories",
    },
]


def seed_categories():
    """Add default categories to the database"""
    logger.info("🌱 Starting category seeding process...")

    db = SessionLocal()
    created_count = 0

    try:
        logger.info(f"📝 Processing {len(DEFAULT_CATEGORIES)} default categories")

        for category_data in DEFAULT_CATEGORIES:
            # Check if category already exists
            existing_category = (
                db.query(Category)
                .filter(Category.name == category_data["name"])
                .first()
            )

            if existing_category:
                logger.debug(
                    f"⏭️  Category '{category_data['name']}' already exists, skipping..."
                )
                continue

            # Create new category
            new_category = Category(
                name=category_data["name"],
                description=category_data["description"],
            )
            db.add(new_category)
            created_count += 1
            logger.info(f"✅ Created category: {category_data['name']}")

        # Commit all changes
        db.commit()
        logger.info(f"🎉 Successfully created {created_count} new categories!")

        # Show final count
        total_count = db.query(Category).count()
        logger.info(f"📊 Total categories in database: {total_count}")

    except Exception as e:
        logger.error(f"❌ Error seeding categories: {e}")
        db.rollback()
        raise
    finally:
        db.close()
        logger.info("🔒 Database connection closed")


if __name__ == "__main__":
    logger.info("🚀 Starting seed script for categories")
    try:
        seed_categories()
        logger.info("✅ Seed script completed successfully")
    except Exception as e:
        logger.error(f"💥 Seed script failed: {e}")
        sys.exit(1)
