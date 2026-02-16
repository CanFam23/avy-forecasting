import {useEffect, useState} from "react";
import Home from "./pages/Home.tsx";
import { Routes, Route } from "react-router-dom";

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
        <Routes>
            <Route path="/" element={<Home
            dayPreds={dayPreds}
            forecastDis={forecastDis}
            weather={weather}
            latestDay={latestDay}
            actDang={actDang}
            />} />
        </Routes>
    );
}

export default App;
