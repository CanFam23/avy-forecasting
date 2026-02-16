import {ChevronDown, ChevronRight} from "lucide-react";
import {type JSX, useState} from "react";
import type {ForecastProps, ForecastDay, ForecastDiscussion} from "../types.ts";
import {WeatherTable} from "./WeatherTable.tsx";
import {dangerMap, dangerMapName} from "../utils/dangers.ts";

export function Forecast({
                             dayPreds,
                             zone,
                             latestDate,
                             zoneDataName,
                             forecastDis,
                             weather,
                         }: ForecastProps) {
    const offset = 5;
    const height = 66;

    const lastestDateEpoch = latestDate;
    const date = new Date(lastestDateEpoch * 1000);
    const daySeconds = 24 * 60 * 60;

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

        const level = dayData?.predicted_danger ?? -1;

        dangerLevelsJSX.push(
            <div
                key={e}
                className="h-7 w-7 sm:h-9 sm:w-9 md:h-10 md:w-10 skew-x-[-30deg] rounded-sm border border-black/70 shadow-sm"
                style={{backgroundColor: `var(--danger-${dangerMap.get(level)})`}}
                title={`${e}: ${level} - ${dangerMapName.get(level) ?? "Unknown"}`}
            />
        );

        dangerLevels.push(level);
    }

    const prevDangers: JSX.Element[] = [];
    for (let i = 5; i >= 1; i--) {
        const currDayEpoch = lastestDateEpoch - daySeconds * i;

        const dayData: ForecastDay | null =
            dayPreds.find(
                (d) =>
                    d.elevation === "upper" &&
                    d.date === currDayEpoch &&
                    d.zone === zoneDataName
            ) ??
            dayPreds.find(
                (d) =>
                    d.elevation === "middle" &&
                    d.date === currDayEpoch &&
                    d.zone === zoneDataName
            ) ??
            null;

        if (!dayData) continue;

        const currDate = new Date(currDayEpoch * 1000).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
        });

        const currDateShort = new Date(currDayEpoch * 1000).toLocaleDateString(
            "en-US",
            {month: "numeric", day: "numeric"}
        );

        prevDangers.push(
            <div key={i} className="flex flex-col items-center gap-1">
                <p className="hidden sm:block text-xs text-gray-700">{currDate}</p>
                <p className="sm:hidden text-[10px] text-gray-700">{currDateShort}</p>
                <div
                    className="h-10 w-10 sm:h-11 sm:w-11 md:h-12 md:w-12 rounded-md border border-black/70 shadow-sm"
                    style={{
                        backgroundColor: `var(--danger-${dangerMap.get(
                            dayData.predicted_danger
                        )})`,
                    }}
                    title={`${dayData.predicted_danger} - ${
                        dangerMapName.get(dayData.predicted_danger) ?? ""
                    }`}
                />
            </div>
        );
    }

    const forecastData: ForecastDiscussion | null =
        forecastDis.find((dayForc) => dayForc.zone === zoneDataName) ?? null;

    const [expanded, setExpanded] = useState(false);

    const dateShort = date.toLocaleDateString("en-US", {
        month: "numeric",
        day: "numeric",
        year: "2-digit",
    });

    const dateLong = date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
    });

    return (
        <section className="my-3 rounded-xl border border-black/10 bg-[var(--color-secondary)] shadow-sm">
            {/* Collapsed header */}
            {!expanded && (
                <div className="grid grid-cols-[1fr_auto_1fr] items-center gap-3 p-4 sm:p-5">
                    <h2 className="text-lg sm:text-xl md:text-2xl font-extrabold tracking-tight leading-tight break-words">
                        {zone}
                    </h2>

                    <div className="text-center text-sm sm:text-base md:text-lg font-semibold text-black/80">
                        <span className="hidden lg:inline">{dateLong}</span>
                        <span className="lg:hidden">{dateShort}</span>
                    </div>

                    <div className="flex items-center justify-end gap-3">
                        <div className="flex gap-2">{dangerLevelsJSX}</div>
                        <button
                            type="button"
                            onClick={() => setExpanded(true)}
                            className="rounded-md p-2 hover:bg-black/5 active:bg-black/10"
                            aria-label="Expand forecast"
                        >
                            <ChevronRight size={24}/>
                        </button>
                    </div>
                </div>
            )}

            {/* Expanded */}
            {expanded && (
                <div className="p-4 sm:p-6">
                    <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                            <h2 className="text-2xl md:text-3xl font-extrabold tracking-tight leading-tight break-words">
                                {zone}
                            </h2>
                            <p className="mt-1 text-sm md:text-base font-semibold text-black/70">
                                {dateLong}
                            </p>
                        </div>

                        <button
                            type="button"
                            onClick={() => setExpanded(false)}
                            className="rounded-md p-2 hover:bg-black/5 active:bg-black/10"
                            aria-label="Collapse forecast"
                        >
                            <ChevronDown size={24}/>
                        </button>
                    </div>

                    {/* Section: Avalanche Danger */}
                    <div className="mt-8 w-fit">
                        <h3 className="text-lg md:text-xl font-bold tracking-tight">
                            Avalanche Danger
                        </h3>

                        <div className="mt-4 rounded-xl bg-white/90 p-4 sm:p-5 border border-black/10 shadow-sm">
                            <div className="grid grid-cols-[minmax(0,1fr)_auto_minmax(0,1fr)] gap-4 items-center">
                                <div
                                    className="space-y-4 md:space-y-8 lg:space-y-16 text-xs sm:text-sm md:text-base text-black/80">
                                    <p>Upper Elevation (Above 6500 ft)</p>
                                    <p>Mid-Elevation (5000–6500 ft)</p>
                                    <p>Low Elevation (Below 5000 ft)</p>
                                </div>

                                <div className="flex justify-center">
                                    <svg
                                        className="w-56 sm:w-64 md:w-72 h-auto"
                                        viewBox={`0 0 200 ${height * 3}`}
                                        aria-label="Avalanche danger by elevation"
                                    >
                                        <polygon
                                            points={`100,0 75,${height} 125,${height}`}
                                            className="stroke-black stroke-2"
                                            style={{
                                                fill: `var(--danger-${dangerMap.get(dangerLevels[2])})`,
                                            }}
                                        />
                                        <polygon
                                            points={`75,${height + offset} 125,${height + offset} 150,${height * 2}, 50,${height * 2}`}
                                            className="stroke-black stroke-2"
                                            style={{
                                                fill: `var(--danger-${dangerMap.get(dangerLevels[1])})`,
                                            }}
                                        />
                                        <polygon
                                            points={`25,${height * 3}, 175,${height * 3}, 150,${
                                                height * 2 + offset
                                            }, 50,${height * 2 + offset}`}
                                            className="stroke-black stroke-2"
                                            style={{
                                                fill: `var(--danger-${dangerMap.get(dangerLevels[0])})`,
                                            }}
                                        />
                                    </svg>
                                </div>

                                <div
                                    className="space-y-12 md:space-y-16 lg:space-y-20 text-xs sm:text-sm md:text-base font-semibold">
                                    <p>
                                        {dangerLevels[2]} — {dangerMapName.get(dangerLevels[2])}
                                    </p>
                                    <p>
                                        {dangerLevels[1]} — {dangerMapName.get(dangerLevels[1])}
                                    </p>
                                    <p>
                                        {dangerLevels[0]} — {dangerMapName.get(dangerLevels[0])}
                                    </p>
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Section: Forecast Details */}
                    <div className="mt-10">
                        <h3 className="text-lg md:text-xl font-bold tracking-tight">
                            Forecast Details
                        </h3>

                        <div className="mt-4 max-w-3xl">
                            <div className="space-y-6">
                                {[
                                    {label: "Primary Concern", value: forecastData?.primary_concern},
                                    {label: "Discussion", value: forecastData?.discussion},
                                    {label: "Travel Advice", value: forecastData?.travel_advice},
                                ].map(({label, value}) => (
                                    <section
                                        key={label}
                                        className="rounded-xl bg-white/80 border border-black/10 p-4 shadow-sm"
                                    >
                                        <h4 className="text-base md:text-lg font-semibold">
                                            {label}
                                        </h4>
                                        <p className="mt-2 text-sm md:text-base text-gray-700 leading-relaxed">
                                            {value ?? "—"}
                                        </p>
                                    </section>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* Section: Previous Days */}
                    <div className="mt-10">
                        <h3 className="text-lg md:text-xl font-bold tracking-tight">
                            Last {prevDangers.length} days
                        </h3>
                        <div className="mt-4 flex flex-wrap justify-center gap-4">
                            {prevDangers}
                        </div>
                    </div>

                    {/* Section: Weather */}
                    <div className="mt-10">
                        <h3 className="text-lg md:text-xl font-bold tracking-tight">
                            Weather Forecast
                        </h3>
                        <div className="mt-4">
                            <WeatherTable rows={weather.filter((r) => r.zone_name === zoneDataName)}/>
                        </div>
                    </div>
                </div>
            )}
        </section>
    );
}

