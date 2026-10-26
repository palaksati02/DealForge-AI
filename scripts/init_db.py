import sys
import os

# Add root directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.logging import logger
from app.db.base import Base
from app.db.session import engine, check_db_connection
from app.db.seed import seed_database


def init():
    logger.info("Initializing DealForge Database...")
    if not check_db_connection():
        logger.error(
            "Could not connect to database. Ensure MySQL is running on port 3306 and check credentials in .env.\n"
            "If using Docker, run: docker compose up -d mysql"
        )
        sys.exit(1)

    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully. Seeding initial demonstration data...")
    seed_database()
    logger.info("Database initialization complete!")


if __name__ == "__main__":
    init()
