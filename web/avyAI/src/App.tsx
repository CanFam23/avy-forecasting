import Navbar from "./components/Navbar";

function App() {

  return (
    <>
      <Navbar navNames={["Forecast","Performance","About"]}/>
      <h1 className="text-3xl font-bold underline text-black">Hello world!</h1>
    </>
  );
}

export default App;
