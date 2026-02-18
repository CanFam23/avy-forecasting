import {Forecast} from "../components/Forecast.tsx";
import TimeSeriesPlot from "../plots/TimeSeriesPlot.tsx";
import type {HomeProps} from "../types.ts";

export default function Home({dayPreds, forecastDis, weather, latestDay, actDang}: HomeProps) {
    return (
        <>
            <div
                className="grid grid-cols-3 gap-x-4 items-center w-full mb-[-10px] mt-10 px-4 text-gray-500 text-xs sm:text-sm">
                <p>Forecast Zone</p>
                <p className="text-center">Forecast Date</p>
                <p className="text-end">Low / Mid / Upper Elevation</p>
            </div>
            <Forecast
                dayPreds={dayPreds}
                zone="Whitefish"
                latestDate={latestDay}
                zoneDataName="Whitefish"
                forecastDis={forecastDis}
                weather={weather}
            />
            <Forecast
                dayPreds={dayPreds}
                zone="Flathead & Glacier NP"
                latestDate={latestDay}
                zoneDataName="Glacier/Flathead"
                forecastDis={forecastDis}
                weather={weather}
            />
            <Forecast
                dayPreds={dayPreds}
                zone="Swan"
                latestDate={latestDay}
                zoneDataName="Swan"
                forecastDis={forecastDis}
                weather={weather}
            />

            <TimeSeriesPlot
                predDangers={dayPreds}
                actDangers={actDang}
            />
        </>
    );
}