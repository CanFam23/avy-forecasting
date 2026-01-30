import Navbar from "./components/Navbar";
import Disclaimer from "./components/Disclaimer";

function App() {

  return (
    <>
      <Navbar navNames={["Forecast","Performance","About"]}/>
        <main className="justify-center m-10">
            <Disclaimer/>
        </main>
      <h1 className="text-3xl font-bold underline text-black">Hello world!</h1>
    </>
  );
}

export default App;
