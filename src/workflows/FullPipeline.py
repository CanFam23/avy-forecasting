import logging
from datetime import datetime
from src.config import COORDS_SUBSET_FP
from src.scraping.FAC_scraper import FAC_Scraper
from src.util.file import csv_to_json
from src.util.web import gen_ai_forecast, save_performance_data
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
            "data/models/best_model_4.pkl",
        )

        fs = FAC_Scraper()
        fs.update_archives(fac_25_fp)

        csv_to_json("data/ops25_26/day_predictions.csv","web/avyAI/public/data/ai_forecast.json")

        csv_to_json("data/2526_FAC/FAC_danger_levels_25_cleaned.csv", "web/avyAI/public/data/actual_forecast.json")
        
        gen_ai_forecast(
            actual_dangers_fp="data/2526_FAC/FAC_danger_levels_25_cleaned.csv",
            all_dangers_fp="data/ops25_26/all_predictions.csv",
            day_dangers_fp="data/ops25_26/day_predictions.csv",
            weather_output_fp="web/avyAI/public/data/weather.json",
            forecast_output_fp="web/avyAI/public/data/forecast_discussion.json"
        )

        save_performance_data(actual_fp="data/2526_FAC/FAC_danger_levels_25_cleaned.csv", 
                              predicted_fp="data/ops25_26/day_predictions.csv", 
                              output_dir="web/avyAI/public/performance")

        logger.info(f"Pipeline completed in {datetime.now() - process_start}")
    except Exception as e:
        logger.exception("Pipeline failed with an exception")
