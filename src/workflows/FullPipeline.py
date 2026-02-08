import logging
from datetime import datetime
from src.config import COORDS_SUBSET_FP
from src.scraping.FAC_scraper import FAC_Scraper
from src.workflows.ForecastPipeline import ForecastPipeline

# Configure logging 
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    process_start = datetime.now()
    
    start_time = datetime.now()
    output_file_dir = "data/fetched"
    output_file_name = "weather_25-26.csv"
    error_file = "logs/operational_error_log.txt"
    date_file = "logs/operational_error_log.txt"
    
    pred_output_file = "data/ops25_26/all_predictions.csv"
    fac_25_fp = "data/2526_FAC/FAC_danger_levels_25.csv"

    try:
        fp = ForecastPipeline()
        fp.run_pipeline(
            output_file_dir,
            output_file_name,
            error_file,
            date_file,
            COORDS_SUBSET_FP,
            pred_output_file,
            "data/models/best_model_4.pkl"
        )

        fs = FAC_Scraper()
        fs.update_archives(fac_25_fp)

        logger.info(f"Pipeline completed in {datetime.now() - process_start}")
    except Exception as e:
        logger.exception("Pipeline failed with an exception")
