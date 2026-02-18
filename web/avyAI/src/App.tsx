import {useEffect, useState} from "react";
import Home from "./pages/Home.tsx";
import Performance from "./pages/Performance.tsx";
import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar.tsx";
import Footer from "./components/Footer.tsx";
import Disclaimer from "./components/Disclaimer.tsx";
import type {PerformanceMetric} from "./types.ts";

function App() {

    const [dayPreds, setDayPreds] = useState([]);
    const [actDang, setActDang] = useState([]);

    const [forecastDis, setForecastDis] = useState([]);
    const [weather, setWeather] = useState([]);

    const [metrics, setMetrics] = useState<PerformanceMetric | null>( null);

    const [latestDay, setLatestDay] = useState(0);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [predRes, actRes, disRes, weatherRes, metricsRes] = await Promise.all([
                    fetch("/data/ai_forecast.json"),
                    fetch("/data/actual_forecast.json"),
                    fetch("/data/forecast_discussion.json"),
                    fetch("/data/weather.json"),
                    fetch("/performance/performance_metrics.json"),
                ]);

                const predictionData = await predRes.json();
                const actResData = await actRes.json();
                const disResData = await disRes.json();
                const weatherResData = await weatherRes.json();
                const metricsResData = await metricsRes.json();

                setDayPreds(predictionData.predictions);
                setActDang(actResData.dangers);
                setLatestDay(predictionData.meta.latest_day);

                setForecastDis(disResData.forecasts);

                setMetrics(metricsResData);

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
            <Navbar
                navNames={{
                    Forecast: "/",
                    Performance: "/performance",
                    About: "/about"
                }}
            />
            <main className="justify-center mx-10 md:mx-60 my-5 min-h-screen">
                <Disclaimer/>
                <Routes>
                    <Route path="/" element={<Home
                        dayPreds={dayPreds}
                        forecastDis={forecastDis}
                        weather={weather}
                        latestDay={latestDay}
                        actDang={actDang}
                    />} />
                    <Route path="/performance" element={<Performance
                        dayPreds={dayPreds}
                        actDang={actDang}
                        performanceMetrics={metrics}
                    />} />
                </Routes>
            </main>

            <Footer/>
        </>
    );
}

export default App;
