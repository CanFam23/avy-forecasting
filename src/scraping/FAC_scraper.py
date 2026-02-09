import logging
import re
from datetime import datetime

import pandas as pd
from playwright.sync_api import Page, sync_playwright

logger = logging.getLogger(__name__)

BASE_URLS = ['https://www.flatheadavalanche.org/avalanche-forecast/#/whitefish-range',
             'https://www.flatheadavalanche.org/avalanche-forecast/#/swan-range',
             'https://www.flatheadavalanche.org/avalanche-forecast/#/flathead-range-&-glacier-np']

ARCHIVE_URL = 'https://www.flatheadavalanche.org/avalanche-forecast/#/archive/forecast'

ZONE_MAP = {
    "whitefish range":"Whitefish",
    "swan range":"Swan",
    "flathead range & glacier np":"Glacier/Flathead"
}

class FAC_Scraper():
    """Class to handle scraping forecast data from the FAC website.
    """

    def scrape_current_forecast(self) -> pd.DataFrame:
        """Scrapes the FAC forecast page for the current days forecast.

        Returns:
            pd.DataFrame: Returns a DataFrame consisting of a row for each forecast zone. 
        """
        # Open each forecast zones page and scrape the dangers from it
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            forecast_data = []
            for url in BASE_URLS:
                page.goto(url)

                forecast_data.append(self.scrape_page(page))
            browser.close()

        # Loop through data and validate the forecasts are for the current day
        for i in range(len(forecast_data)-1, -1, -1):
            data = forecast_data[i]
            if data['date'].date() != datetime.now().date():
                logger.warning(
                    f"Most recent forecast ({data['date'].date()}) for {data['zone_name']} not valid for today! Removing from data.")
                forecast_data.pop(i)

        return pd.DataFrame(forecast_data).drop_duplicates()

    def scrape_page(self, page: Page) -> dict:
        """Scrapes the given page for the avalanche danger numbers

        Args:
            page (Page): Page to scrape

        Returns:
            dict: Dict consisting of the zone name, date, and danger rating for each elevation band.
        """
        danger_box = page.locator('div.nac-dangerToday').first
        forecast_data = {}

        # Find zone name
        zone = page.locator(
            "h2.nac-gray-700.nac-m-0.nac-h2").first.inner_text().lower().strip()

        forecast_data['zone_name'] = zone

        # Find date
        date = danger_box.locator(".nac-dangerDate").first.inner_html()

        forecast_data['date'] = datetime.strptime(date, "%A, %B %d, %Y")

        # Container for danger level ratings
        bands = danger_box.locator(".nac-elevationBlock")

        # Extract each danger level
        for i in range(bands.count()):
            elevation_band = bands.nth(i).locator(
                ".nac-elevationLabel").inner_text().split("Elevation")[0].lower().strip()

            danger_rating = bands.nth(i).locator(
                ".nac-dangerLabel").inner_text().split(" - ")[0]

            forecast_data[elevation_band if elevation_band not in [
                "mid-", "low"] else "middle" if elevation_band == "mid-" else "lower"] = int(danger_rating)
        return forecast_data

    def scrape_archives(self, day: datetime) -> pd.DataFrame:
        """Scrapes the FAC archives for the danger ratings for the given day.
        Returns a empty DataFrame if no forecasts are found for the given day

        Args:
            day (datetime): Day to find data for

        Returns:
            pd.DataFrame: Returns a DataFrame consisting of a row for each forecast zone. 
        """
        forecast_data = []

        # Open page
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(ARCHIVE_URL)

            min_date = day

            # While the minimum date seen is greater than the given date and there is a next page,
            # check each archive page for a forecast for the given day
            text_found = []
            while True:
                page.wait_for_selector(
                    "div.nac-card.nac-card-hover.nac-archive-card", timeout=10000)

                cards = page.locator(
                    "div.nac-card.nac-card-hover.nac-archive-card")

                # Loop through each card (Each card is a forecast for one zone for one day)
                for i in range(cards.count()):
                    text = cards.nth(i).text_content()
                    date_split = text.split(" ")[:3]  # type: ignore
                    date_split[2] = re.sub(r"\D", "", date_split[2])
                    date = datetime.strptime(" ".join(date_split), "%b %d, %Y")

                    # Check date matches and haven't seen this card already
                    if date == day and text not in text_found:

                        cards.nth(i).click()
                        logger.info(f"New URL: {page.url}")
                        page.wait_for_load_state('networkidle')

                        # Scrape forecast
                        forecast_data.append(self.scrape_page(page))

                        text_found.append(text)

                        page.go_back()
                        page.wait_for_load_state('networkidle')

                        # IMPORTANT: Re-get the cards locator
                        cards = page.locator("div.nac-card")

                    min_date = min(date, min_date)

                # Forecasts are ordered, so if we pass the date it's not in the archives.
                if min_date < day:
                    logger.info("Date passed")
                    break

                # We should find three forecasts, one for each zone
                if len(forecast_data) == 3:
                    return pd.DataFrame(forecast_data).drop_duplicates()

                # Look for the button to go to the next page of the archives
                page_navs = page.locator("a.nac-page-link")
                next_page = False
                for i in range(cards.count()):
                    if page_navs.nth(i).text_content() == ">":
                        # Go to next page
                        next_page = True

                        try:
                            page_navs.nth(i).click()
                            page.wait_for_load_state(
                                'networkidle', timeout=3000)
                        except Exception:
                            logger.warning("Timed out waiting for locator")

                        break

                # If there is no next page, end the loop
                if not next_page:
                    break
            browser.close()
        return pd.DataFrame(forecast_data).drop_duplicates()

    def update_archives(self, archive_fp: str) -> None:
        """Given a file path to a csv file consisting of previously scraped data, check for missing dates
        and attempt to scrape the data for those dates. Any new data found will be appended to the 
        data in the file and resaved.

        Args:
            archive_fp (str): File path to a csv file with previously scraped data.
        """
        df = pd.read_csv(archive_fp)

        df['date'] = pd.to_datetime(df['date'])

        df_grouped = df.groupby(by='date').size().reset_index().rename(columns={0: "size"})

        # Get missing dates
        date_range = pd.date_range(start=df['date'].min(), end=datetime.now())

        missing_dates = []
        for date in date_range:
            df_date = df_grouped[df_grouped["date"] == date]
            # All dates should have 3 rows (One for each forecast zone)
            if df_date.empty or df_date['size'].iloc[0] < 3:
                missing_dates.append(date)

        if not missing_dates:
            logger.info("No missing dates found")
            return

        # Scrape each date
        for date in missing_dates:
            if date.date() != datetime.now().date():
                logger.info(f"Searching forecast archives for {date}")
                date_data = self.scrape_archives(date)
                if not date_data.empty:
                    df = pd.concat([df, date_data])
                else:
                    logger.warning(f"No forecast found for {date}")
            else:
                logger.info(f"Scraping current forecast ({date})")
                date_data = self.scrape_current_forecast()
                if not date_data.empty:
                    df = pd.concat([df, date_data])
                else:
                    logger.warning(f"No forecast found for {date}")

        df.sort_values(by='date').to_csv(archive_fp, mode='w', index=False)

        # Convert df to a format similar to the df outputted by the model for easier comparison.
        df = df.melt(
            id_vars=["zone_name", "date"],
            value_vars=["upper", "middle", "lower"],
            var_name="elevation_band",
            value_name="actual_danger"
        )

        df['zone_name'] = df['zone_name'].apply(lambda x: ZONE_MAP[x])

        df = df[['date','zone_name','elevation_band','actual_danger']].drop_duplicates()
        df['slope_angle'] = 'slope'

        df.to_csv(archive_fp.split(".")[0] + "_cleaned.csv",mode='w',index=False)

if __name__ == "__main__":
    fp = "data/2526_FAC/FAC_danger_levels_25.csv"
    fs = FAC_Scraper()
    fs.update_archives(fp)
