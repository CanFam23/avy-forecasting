import {ChevronDown, ChevronRight} from "lucide-react";
import {type JSX, useState} from "react";

export default function Forecast() {
    const offset: number = 5;
    const height: number = 66;
    const dangerMap = new Map();
    dangerMap.set(0, "low");
    dangerMap.set(1, "mod");
    dangerMap.set(2, "con");

    const dangerLevels: JSX.Element[] = [];

    for (let i = 0; i < 3; i++) {
        dangerLevels.push(
            <div
                key={i}
                className="w-6 md:w-15 h-6 md:h-15 skew-x-[-30deg] border-2 border-black"
                style={{ backgroundColor: `var(--danger-${dangerMap.get(i)})` }}
            ></div>
        );
    }

    const prevDangers: JSX.Element[] = [];
    for (let i = 14; i < 19; i++) {
        const color: string = i % 2 === 0 ? "low" : "mod";
        prevDangers.push(
            <div
                key={i}
            >
                <p>Jan {i}</p>
                <div className="w-6 md:w-15 h-6 md:h-15 border-2 border-black"
                     style={{ backgroundColor: `var(--danger-${color})` }}
                ></div>
            </div>
        );
    }


    const [expanded, setExpanded] = useState(false);

    const dateStr = "January 30, 2026";
    const date = new Date(dateStr);

    const dateShort = date.toLocaleDateString("en-US", {
        month: "numeric",
        day: "numeric",
        year: "2-digit",
    });

    return (
        <>
            <section className="bg-[var(--color-secondary)] my-2 p-2 rounded-sm">
                {!expanded && <div className="flex space-x justify-between items-center">
                  <h2 className="font-black text-lg sm:text-xl md:text-3xl">Whitefish</h2>
                  <p className="hidden lg:block font-bold text-l md:text-2xl">January 30, 2026</p>
                  <p className="lg:hidden font-bold text-l md:text-2xl">{dateShort}</p>

                  <div className="flex space-x-2">
                      {dangerLevels}
                  </div>

                  <ChevronRight className="hover:cursor-pointer" size={32} onClick={() => setExpanded(!expanded)}/>
                </div>}

                {expanded && <div className="flex flex-col justify-between text-center">
                  <div className="flex justify-between items-center">
                    <h2 className="font-black text-2xl md:text-3xl">Whitefish</h2>
                    <ChevronDown className="hover:cursor-pointer" size={32} onClick={() => setExpanded(!expanded)}/>
                  </div>

                  <p className="font-bold text-l md:text-2xl pb-10">{dateStr}</p>
                  <h3 className="text-xl md:text-2xl font-bold ml-[10vw] xl:ml-[14vw] mr-auto text-start">Avalanche Danger</h3>

                  <div className="flex justify-center bg-white lg:w-[80%] xl:w-[70%] mx-auto py-3">
                    <div className="flex flex-col justify-between py-5 space-y-5 text-[8px] xs:text-[10px] md:text-[12px]">
                      <p>Upper Elevation (Above 6500 ft)</p>
                      <p>Mid-Elevation (5000-6500 ft)</p>
                      <p>Low Elevation (Below 5000 ft)</p>
                    </div>
                    <svg className="w-1/2 lg:w-1/3 h-auto" viewBox={`0 0 200 ${height * 3}`}>
                        {/* Top section */}
                      <polygon points={`100,0 75,${height} 125,${height}`} className="stroke-black stroke-2"
                               style={{fill: `var(--danger-${dangerMap.get(2)})`}}/>
                        {/* Middle section */}
                      <polygon
                        points={`75,${height + offset} 125,${height + offset} 150,${height * 2}, 50,${height * 2}`}
                        className="stroke-black stroke-2" style={{fill: `var(--danger-${dangerMap.get(1)})`}}/>
                        {/* Bottom section */}
                      <polygon
                        points={`25,${height * 3}, 175,${height * 3}, 150,${height * 2 + offset}, 50,${height * 2 + offset}`}
                        className="stroke-black stroke-2" style={{fill: `var(--danger-${dangerMap.get(0)})`}}/>
                    </svg>
                    <div className="flex flex-col justify-between py-5 font-bold text-[10px] md:text-[14px]">
                      <p>3 - Considerable</p>
                      <p>2 - Moderate</p>
                      <p>1 - Low</p>
                    </div>

                  </div>

                  <h3 className="text-xl md:text-2xl font-bold ml-[10vw] xl:ml-[14vw] mr-auto text-start mt-10">Weather Forecast</h3>
                    <p>TBD</p>

                  <h3 className="text-xl md:text-2xl font-bold ml-[10vw] xl:ml-[14vw] mr-auto text-start mt-10">Discussion</h3>
                    <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>

                  <h3 className="text-xl md:text-2xl font-bold mt-10 text-cetner">Last 5 days</h3>
                  <div className="flex space-x-5 justify-center">
                      {prevDangers}
                  </div>
                </div>}
            </section>
        </>
    )
}