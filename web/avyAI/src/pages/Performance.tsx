import type {PerformanceProps} from "../types.ts";
import TimeSeriesPlot from "../plots/TimeSeriesPlot.tsx";
import {useState} from "react";

export default function Performance({ dayPreds, actDang, performanceMetrics }: PerformanceProps) {
    const [showNorm, setShowNorm] = useState(false);

    return (
        <>
            <section className="flex flex-col text-center space-y-5 shadow-md mt-10 rounded-lg p-2">
                <h1 className="text-xl md:text-3xl font-bold text-center">Model Performance</h1>

                <h2 className="text:md md:text-xl font-bold">Accuracy for the 25–26 season</h2>

                {
                    performanceMetrics && (
                        <>
                            <strong className="text-sm md:text-md">Overall:</strong>{" "}
                            <p className="text-sm md:text-md">
                                {(performanceMetrics.accuracy * 100).toFixed(2)}%
                            </p>

                            <strong className="text-sm md:text-md">Balanced:</strong>{" "}
                            <p className="text-sm md:text-md">
                                {(performanceMetrics.balanced_accuracy * 100).toFixed(2)}%
                            </p>
                        </>
                    )
                }


                <div className="text-xs md:text-sm opacity-60">
                    <p>*<strong>Overall</strong> accuracy represents the percent of correct predictions</p>
                    <p>*<strong>Balanced</strong> accuracy represents the average accuracy across the 4 danger levels</p>
                </div>
            </section>

            <section className="flex flex-col text-center items-center space-y-5 shadow-md mt-10 rounded-lg p-2">

                <div className="flex flex-col text-center items-center">
                    <h3 className="text-lg md:text-xl font-bold text-left w-full ml-24">Confusion Matrix</h3>
                    <button
                        onClick={() => setShowNorm(!showNorm)}
                        className="bg-[var(--color-primary)] w-fit p-1 m-3 text-white text-xs md:text-sm font-bold rounded-lg shadow-md hover:cursor-pointer"
                    >Show {showNorm ? `standard` : `normalized`} matrix</button>

                    {!showNorm && <img src="/performance/cm.svg" alt="Confusion Matrix" className="p-4"/>}
                    {showNorm && <img src="/performance/norm_cm.svg" alt="Normalized Confusion Matrix"  className="p-4"/>}
                    <p className="text-xs lg:text-md opacity-90 px-10 leading-relaxed">
                        The confusion matrix above compares the model’s predicted danger levels to the actual forecasted danger levels.
                        A well-performing model will show high {showNorm ? "percentages" : "counts"} along the diagonal of the matrix,
                        indicating correct classifications. The x-axis represents the model’s predicted danger level,
                        while the y-axis represents the true danger level issued by the FAC.
                    </p>

                    <p className="text-xs lg:text-md opacity-90 px-10 leading-relaxed">
                        The model was trained on the past five years of forecast data provided by the FAC.
                        During this period, an avalanche danger rating of 5 was never issued. As a result,
                        only four danger levels appear in the confusion matrix.
                    </p>

                    <hr className="my-6 border-1 border-black opacity-30 rounded-lg w-full" />
                </div>


                <div className="flex flex-col text-center items-center">
                    <h3 className="text-md md:text-xl font-bold w-full text-center md:text-left">
                        Confusion Matrix of Forecast Zones and Elevation Bands
                    </h3>
                    <img src="/performance/zone_ele_perf.svg" alt="Performance across zones and elevations" className="p-4"/>

                    <p className="text-xs lg:text-md lg:text-md opacity-90 px-10 leading-relaxed">
                        The confusion matrix above shows the model’s performance across all forecast zones
                        and elevation bands. The Whitefish – upper cell displays “N/A” because none of the
                        forecast points in the Whitefish Mountain Range used to train the model are above
                        6,500 feet. Expanding the training data to include more points and higher elevations is a planned
                        improvement.
                    </p>

                    <hr className="my-6 border-1 border-black opacity-30 rounded-lg w-full" />
                </div>

                <TimeSeriesPlot
                    predDangers={dayPreds}
                    actDangers={actDang}
                />
            </section>
        </>
    );
}
