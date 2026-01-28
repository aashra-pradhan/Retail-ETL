from src.extract import extract_tables
from src.transform import clean_and_transform
from src.load import load_to_dw
from src.utils import setup_logger

logger = setup_logger()

def run_etl():
    logger.info("Starting ETL pipeline...")

    logger.info("Extracting data...")
    raw_data = extract_tables()
    logger.info("Extraction complete.")

    logger.info("Transforming data...")
    dims, fact = clean_and_transform(raw_data)
    logger.info("Transformation complete.")

    logger.info("Loading data to DW...")
    load_to_dw(dims, fact)
    logger.info("ETL pipeline completed successfully!")

if __name__ == "__main__":
    run_etl()
