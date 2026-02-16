import type {WeatherRow} from "../types.ts";
import {dangerMap, dangerMapName} from "../utils/dangers.ts";
import {fmtDate, aziToCardinal} from "../utils/utils.ts";

function DangerPill({ level }: { level: number }) {
    const text= dangerMapName.get(level);

    return (
        <span className="inline-flex items-center rounded-full border px-2 py-0.5 text-sm font-medium"
              style={{
                  backgroundColor: `var(--danger-${dangerMap.get(level)})`,
              }}
        >
      {text}
    </span>
    );
}

export function WeatherTable({ rows }: { rows: WeatherRow[] }) {
    return (
        <div className="self-center mt-8 max-w-6xl w-full">
            <p>Averaged over 7am of date - 7am next day</p>

            <div className="mt-4 w-full max-w-full overflow-x-auto rounded-2xl border">
                <table className="w-max min-w-full table-auto">
                    <thead className="bg-gray-50">
                    <tr className="text-left">
                        <th className="p-3 font-semibold whitespace-nowrap">Date</th>
                        <th className="p-3 font-semibold whitespace-nowrap">Zone</th>
                        <th className="p-3 font-semibold whitespace-nowrap">Band</th>
                        <th className="p-3 font-semibold whitespace-nowrap">Aspect</th>
                        <th className="p-3 font-semibold whitespace-nowrap">Temp (°F)</th>
                        <th className="p-3 font-semibold whitespace-nowrap">RH (%)</th>
                        <th className="p-3 font-semibold whitespace-nowrap">Wind (mph)</th>
                        <th className="p-3 font-semibold whitespace-nowrap">New Snow 24 (in)</th>
                        <th className="p-3 font-semibold whitespace-nowrap hidden md:table-cell">Precip 24 (in)</th>
                        <th className="p-3 font-semibold whitespace-nowrap hidden lg:table-cell">Snow Depth (in)</th>
                        <th className="p-3 font-semibold whitespace-nowrap hidden lg:table-cell">SWE</th>
                        <th className="p-3 font-semibold whitespace-nowrap">Danger</th>
                    </tr>
                    </thead>

                    <tbody className="divide-y">
                    {rows.map((r, idx) => (
                        <tr key={`${r.zone_name}-${r.elevation_band}-${r.date_epoch}-${idx}`} className="hover:bg-gray-50">
                            <td className="p-3 whitespace-nowrap">{fmtDate(r.date_epoch)}</td>
                            <td className="p-3 whitespace-nowrap">{r.zone_name}</td>
                            <td className="p-3 whitespace-nowrap capitalize">{r.elevation_band}</td>
                            <td className="p-3 whitespace-nowrap">{aziToCardinal(r.slope_azi)}</td>
                            <td className="p-3 whitespace-nowrap">{r.temp_avg.toFixed(1)}</td>
                            <td className="p-3 whitespace-nowrap">{r.rh_avg.toFixed(0)}</td>
                            <td className="p-3 whitespace-nowrap">{r.wind_avg.toFixed(1)}</td>
                            <td className="p-3 whitespace-nowrap">{r.new_snow_24.toFixed(1)}</td>
                            <td className="p-3 whitespace-nowrap hidden md:table-cell">{r.precip_total.toFixed(2)}</td>
                            <td className="p-3 whitespace-nowrap hidden lg:table-cell">{r.snow_depth_avg.toFixed(1)}</td>
                            <td className="p-3 whitespace-nowrap hidden lg:table-cell">{r.swe_avg.toFixed(2)}</td>
                            <td className="p-3 whitespace-nowrap"><DangerPill level={r.danger_level} /></td>
                        </tr>
                    ))}
                    </tbody>
                </table>
            </div>

            <p className="mt-2 text-xs text-gray-500 md:hidden">
                Swipe horizontally to see more columns.
            </p>
        </div>
    );
}
