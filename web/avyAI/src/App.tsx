import Navbar from "./components/Navbar";
import Disclaimer from "./components/Disclaimer";
import Forecast from "./components/Forecast.tsx";

function App() {

  return (
    <>
      <Navbar navNames={["Forecast","Performance","About"]}/>
        <main className="justify-center mx-10 md:mx-30 my-5 ">
            <Disclaimer/>
            <div className="flex justify-between mb-[-10px] mt-10 px-4 text-gray-500 text-xs sm:text-sm">
                <p>Forecast Zone</p>
                <p>Forecast Date</p>
                <p>Low / Mid / Upper Elevation</p>
                <p></p>
            </div>
            <Forecast/>
        </main>
      <h1 className="text-3xl font-bold underline text-black">Hello world!</h1>
    </>
  );
}

export default App;
