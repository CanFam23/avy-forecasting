import {ChevronDown, ChevronRight} from "lucide-react";
import {type JSX, useState} from "react";
import type {ForecastProps, ForecastDay, ForecastDiscussion} from "../types.ts";
import {WeatherTable} from "./WeatherTable.tsx";
import {dangerMap, dangerMapName} from "../utils/dangers.ts";

export function Forecast({ dayPreds, zone, latestDate, zoneDataName, forecastDis, weather }: ForecastProps) {
    const offset: number = 5;
    const height: number = 66;

    const lastestDateEpoch: number = latestDate;
    const date: Date = new Date(lastestDateEpoch * 1000);
    const daySeconds: number = 24 * 60 * 60;

    const dangerLevels: number[] = [];
    const dangerLevelsJSX: JSX.Element[] = [];

    for (const e of ["lower", "middle", "upper"] as const) {
        const dayData: ForecastDay | null =
            dayPreds.find(
                (dayPred) =>
                    dayPred.elevation === e &&
                    dayPred.date === latestDate &&
                    dayPred.zone === zoneDataName
            ) ?? null;

        if (dayData) {
            dangerLevelsJSX.push(
                <div
                    key={e}
                    className="w-6 md:w-15 h-6 md:h-15 skew-x-[-30deg] border-2 border-black"
                    style={{
                        backgroundColor: `var(--danger-${dangerMap.get(dayData.predicted_danger)})`,
                    }}
                />
            );
            dangerLevels.push(dayData.predicted_danger);
        } else {
            dangerLevelsJSX.push(
                <div
                    key={e}
                    className="w-6 md:w-15 h-6 md:h-15 skew-x-[-30deg] border-2 border-black"
                    style={{ backgroundColor: `var(--danger-${dangerMap.get(-1)})` }}
                />
            );
            dangerLevels.push(-1);
        }
    }

    const prevDangers: JSX.Element[] = [];
    for (let i = 5; i >= 1; i--) {
        const currDayEpoch = lastestDateEpoch - daySeconds * i;

        const dayData: ForecastDay | null =
            dayPreds.find(
                d =>
                    d.elevation === "upper" &&
                    d.date === currDayEpoch &&
                    d.zone === zoneDataName
            )
            ??
            dayPreds.find(
                d =>
                    d.elevation === "middle" &&
                    d.date === currDayEpoch &&
                    d.zone === zoneDataName
            )
            ??
            null;

        if (dayData) {
            const currDate: string = new Date(currDayEpoch * 1000).toLocaleDateString("en-US", {
                month: "short",
                day: "numeric",
            });

            const currDateShort = date.toLocaleDateString("en-US", {
                month: "numeric",
                day: "numeric",
            });

            prevDangers.push(
                <div key={i}>
                    <p className="hidden sm:block">{currDate}</p>
                    <p className="sm:hidden">{currDateShort}</p>
                    <div
                        className="w-9 md:w-15 h-9 md:h-15 border-2 border-black"
                        style={{
                            backgroundColor: `var(--danger-${dangerMap.get(dayData.predicted_danger)})`,
                        }}
                    />
                </div>
            );
        }
    }

    const forecastData: ForecastDiscussion | null =
        forecastDis.find(
            (dayForc) =>
                dayForc.zone === zoneDataName
        ) ?? null;

    const [expanded, setExpanded] = useState(true);

    const dateShort = date.toLocaleDateString("en-US", {
        month: "numeric",
        day: "numeric",
        year: "2-digit",
    });

    const dateLong = date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });

    return (
        <>
            <section className="bg-[var(--color-secondary)] my-2 p-2 rounded-sm">
                {!expanded && <div className="flex space-x justify-between items-center">
                  <div className="grid grid-cols-3 gap-x-4 items-center w-full mr-6 md:mr-10 lg:mr-20">
                      {/* Left column - zone name */}
                    <h2 className="font-black text-lg sm:text-xl md:text-3xl">
                        {zone}
                    </h2>

                      {/* Middle column - date */}
                    <div className="text-center">
                      <p className="hidden lg:block font-bold text-l md:text-2xl">
                          {dateLong}
                      </p>
                      <p className="lg:hidden font-bold text-l md:text-2xl">
                          {dateShort}
                      </p>
                    </div>

                      {/* Right column - danger levels */}
                    <div className="flex space-x-2 justify-end">
                        {dangerLevelsJSX}
                    </div>
                  </div>

                  <ChevronRight className="hover:cursor-pointer" size={32} onClick={() => setExpanded(!expanded)}/>
                </div>}

                {expanded && <div className="flex flex-col justify-between text-center">
                  <div className="flex justify-between items-center">
                    <h2 className="font-black text-2xl md:text-3xl">{zone}</h2>
                    <ChevronDown className="hover:cursor-pointer" size={32} onClick={() => setExpanded(!expanded)}/>
                  </div>

                  <p className="font-bold text-l md:text-2xl pb-10">{dateLong}</p>
                  <h3 className="text-xl md:text-2xl font-bold ml-[10vw] xl:ml-[14vw] mr-auto text-start">Avalanche
                    Danger</h3>

                  <div className="flex justify-center bg-white lg:w-[80%] xl:w-[70%] mx-auto py-3">
                    <div
                      className="flex flex-col justify-between py-5 space-y-5 text-[8px] xs:text-[10px] md:text-[12px]">
                      <p>Upper Elevation (Above 6500 ft)</p>
                      <p>Mid-Elevation (5000-6500 ft)</p>
                      <p>Low Elevation (Below 5000 ft)</p>
                    </div>
                    <svg className="w-1/2 lg:w-1/3 h-auto" viewBox={`0 0 200 ${height * 3}`}>
                        {/* Top section */}
                      <polygon points={`100,0 75,${height} 125,${height}`} className="stroke-black stroke-2"
                               style={{fill: `var(--danger-${dangerMap.get(dangerLevels[2])})`}}/>
                        {/* Middle section */}
                      <polygon
                        points={`75,${height + offset} 125,${height + offset} 150,${height * 2}, 50,${height * 2}`}
                        className="stroke-black stroke-2"
                        style={{fill: `var(--danger-${dangerMap.get(dangerLevels[1])})`}}/>
                        {/* Bottom section */}
                      <polygon
                        points={`25,${height * 3}, 175,${height * 3}, 150,${height * 2 + offset}, 50,${height * 2 + offset}`}
                        className="stroke-black stroke-2"
                        style={{fill: `var(--danger-${dangerMap.get(dangerLevels[0])})`}}/>
                    </svg>
                    <div className="flex flex-col justify-between py-5 font-bold text-[10px] md:text-[14px]">
                      <p>{dangerLevels[2]} - {dangerMapName.get(dangerLevels[2])}</p>
                      <p>{dangerLevels[1]} - {dangerMapName.get(dangerLevels[1])}</p>
                      <p>{dangerLevels[0]} - {dangerMapName.get(dangerLevels[0])}</p>
                    </div>

                  </div>

                    <h3 className="text-xl md:text-2xl font-bold ml-[10vw] xl:ml-[14vw] mr-auto text-start mt-10">
                    Forecast Details
                  </h3>

                  <div className="mt-6 space-y-6 max-w-3xl mx-auto text-center">
                      {[
                          { label: "Primary Concern", value: forecastData?.primary_concern },
                          { label: "Discussion", value: forecastData?.discussion },
                          { label: "Travel Advice", value: forecastData?.travel_advice },
                      ].map(({ label, value }) => (
                          <section key={label}>
                              <h4 className="font-semibold text-lg mb-1">{label}</h4>
                              <p className="text-xs md:text-lg text-gray-700 leading-relaxed">
                                  {value ?? "—"}
                              </p>
                          </section>
                      ))}
                  </div>

                  <h3 className="text-xl md:text-2xl font-bold mt-10 text-cetner">Last {prevDangers.length} days</h3>
                  <div className="flex space-x-5 justify-center">
                      {prevDangers}
                  </div>

                  <h3 className="text-xl md:text-2xl font-bold ml-[10vw] xl:ml-[14vw] mr-auto text-start mt-10">Weather
                    Forecast</h3>
                  <WeatherTable rows={weather.filter(r => r.zone_name == zoneDataName)} />

                </div>}
            </section>
        </>
    )
}