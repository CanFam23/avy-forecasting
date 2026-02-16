import { useMemo, useState } from "react";
import Plot from "react-plotly.js";
import type { GraphData } from "../types.ts";

export default function TimeSeriesPlot({ predDangers, actDangers }: GraphData) {
    // Build dropdown options from the data
    const zones = useMemo(() => {
        const s = new Set<string>();
        predDangers.forEach((d) => s.add(d.zone));
        actDangers.forEach((d) => s.add(d.zone));
        return [...s].sort();
    }, [predDangers, actDangers]);

    const elevations = useMemo(() => {
        const s = new Set<string>();
        predDangers.forEach((d) => s.add(d.elevation));
        actDangers.forEach((d) => s.add(d.elevation));
        return [...s].sort();
    }, [predDangers, actDangers]);

    const [zone, setZone] = useState<string>(zones[0] ?? "");
    const [elevation, setElevation] = useState<string>(elevations[0] ?? "");

    // Filter and sort
    const sortedPred = useMemo(() => {
        return predDangers
            .filter((d) => (zone ? d.zone === zone : true))
            .filter((d) => (elevation ? d.elevation === elevation : true))
            .slice()
            .sort((a, b) => a.date - b.date);
    }, [predDangers, zone, elevation]);

    const sortedAct = useMemo(() => {
        return actDangers
            .filter((d) => (zone ? d.zone === zone : true))
            .filter((d) => (elevation ? d.elevation === elevation : true))
            .slice()
            .sort((a, b) => a.date - b.date);
    }, [actDangers, zone, elevation]);

    const predTrace = useMemo(
        () => ({
            x: sortedPred.map((d) => new Date(d.date * 1000)),
            y: sortedPred.map((d) => d.predicted_danger),
            type: "scatter" as const,
            mode: "lines+markers" as const,
            name: "Predicted",
        }),
        [sortedPred]
    );

    const actTrace = useMemo(
        () => ({
            x: sortedAct.map((d) => new Date(d.date * 1000)),
            y: sortedAct.map((d) => d.actual_danger),
            type: "scatter" as const,
            mode: "lines+markers" as const,
            name: "Actual",
        }),
        [sortedAct]
    );

    return (
        <div className="w-full bg-white rounded-xl shadow-md p-6 space-y-4 mt-20">

            <div>
                <h2 className="text-2xl font-semibold tracking-tight">
                    Season Performance
                </h2>
                <p className="text-sm text-gray-500">
                    {zone && elevation
                        ? `${zone} — ${elevation} elevation`
                        : "Select a zone and elevation band"}
                </p>
            </div>

            {/* Controls */}
            <div className="flex flex-col md:flex-row gap-6 items-center">
                <label className="flex items-center gap-2 text-sm font-medium">
                    Zone
                    <select
                        className="border rounded-md px-2 py-1 text-sm"
                        value={zone}
                        onChange={(e) => setZone(e.target.value)}
                    >
                        {zones.map((z) => (
                            <option key={z} value={z}>
                                {z}
                            </option>
                        ))}
                    </select>
                </label>

                <label className="flex items-center gap-2 text-sm font-medium">
                    Elevation
                    <select
                        className="border rounded-md px-2 py-1 text-sm"
                        value={elevation}
                        onChange={(e) => setElevation(e.target.value)}
                    >
                        {elevations.map((el) => (
                            <option key={el} value={el}>
                                {el}
                            </option>
                        ))}
                    </select>
                </label>
            </div>

            {/* Plot */}
            <Plot
                data={[predTrace, actTrace]}
                layout={{
                    xaxis: { type: "date", title: "Date" },
                    yaxis: { title: "Danger Level", dtick: 1 },
                    legend: { orientation: "h" },
                    margin: { l: 50, r: 20, t: 30, b: 50 },
                }}
                config={{ responsive: true }}
                style={{ width: "100%", height: "450px" }}
                useResizeHandler
            />
        </div>
    );
}


