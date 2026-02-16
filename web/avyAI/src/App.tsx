import Navbar from "./components/Navbar";
import Disclaimer from "./components/Disclaimer";
import {Forecast} from "./components/Forecast.tsx";
import Footer from "./components/Footer.tsx";
import {useEffect, useState} from "react";
import {WeatherTable} from "./components/WeatherTable.tsx";

function App() {

    const [dayPreds, setDayPreds] = useState([]);
    const [forecastDis, setForecastDis] = useState([]);
    const [weather, setWeather] = useState([]);

    const [latestDay, setLatestDay] = useState(0);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [predRes, disRes, weatherRes] = await Promise.all([
                    fetch("/data/ai_forecast.json"),
                    fetch("/data/forecast_discussion.json"),
                    fetch("/data/weather.json")
                ]);

                const predictionData = await predRes.json();
                const disResData = await disRes.json();
                const weatherResData = await weatherRes.json();

                setDayPreds(predictionData.predictions);
                setLatestDay(predictionData.meta.latest_day);

                setForecastDis(disResData.forecasts);

                setWeather(weatherResData.weather);
                console.log(weatherResData);
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
            <main className="justify-center mx-10 md:mx-30 my-5 min-h-screen">
                <Disclaimer/>
                <div className="grid grid-cols-3 gap-x-4 items-center w-full mb-[-10px] mt-10 px-4 text-gray-500 text-xs sm:text-sm">
                    <p>Forecast Zone</p>
                    <p>Forecast Date</p>
                    <p>Low / Mid / Upper Elevation</p>
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
            </main>
            <Footer/>
        </>
    );
}

export default App;
