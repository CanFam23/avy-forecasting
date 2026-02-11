import Navbar from "./components/Navbar";
import Disclaimer from "./components/Disclaimer";
import {Forecast} from "./components/Forecast.tsx";
import Footer from "./components/Footer.tsx";
import {useEffect, useState} from "react";

function App() {

    const [dayPreds, setDayPreds] = useState([]);
    const [latestDay, setLatestDay] = useState(0);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('/data/ai_forecast.json')
            .then(response => response.json())
            .then(data => {
                setDayPreds(data.predictions);
                setLatestDay(data.meta.latest_day);
                setLoading(false);
            })
            .catch(error => console.error('Error:', error));
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
                />
                <Forecast
                    dayPreds={dayPreds}
                    zone="Flathead & Glacier NP"
                    latestDate={latestDay}
                    zoneDataName="Glacier/Flathead"
                />
                <Forecast
                    dayPreds={dayPreds}
                    zone="Swan"
                    latestDate={latestDay}
                    zoneDataName="Swan"
                />
            </main>
            <Footer/>
        </>
    );
}

export default App;
