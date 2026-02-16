import Navbar from "./components/Navbar";
import Disclaimer from "./components/Disclaimer";
import {Forecast} from "./components/Forecast.tsx";
import Footer from "./components/Footer.tsx";
import {useEffect, useState} from "react";
import TimeSeriesPlot from "./plots/TimeSeriesPlot.tsx";

function App() {

    const [dayPreds, setDayPreds] = useState([]);
    const [actDang, setActDang] = useState([]);

    const [forecastDis, setForecastDis] = useState([]);
    const [weather, setWeather] = useState([]);

    const [latestDay, setLatestDay] = useState(0);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [predRes, actRes, disRes, weatherRes] = await Promise.all([
                    fetch("/data/ai_forecast.json"),
                    fetch("/data/actual_forecast.json"),
                    fetch("/data/forecast_discussion.json"),
                    fetch("/data/weather.json")
                ]);

                const predictionData = await predRes.json();
                const actResData = await actRes.json();
                const disResData = await disRes.json();
                const weatherResData = await weatherRes.json();

                setDayPreds(predictionData.predictions);
                setActDang(actResData.dangers);
                setLatestDay(predictionData.meta.latest_day);

                setForecastDis(disResData.forecasts);

                setWeather(weatherResData.weather);
            } catch (err) {
                console.error(err);
            }

            setLoading(false);
        }

        fetchData();
    }, []);

    if (loading) return <div>Loading...</div>;

    return (
        <>
            <Navbar navNames={["Forecast", "Performance", "About"]}/>
            <main className="justify-center mx-10 md:mx-60 my-5 min-h-screen">
                <Disclaimer/>
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
            </main>
            <Footer/>
        </>
    );
}

export default App;
