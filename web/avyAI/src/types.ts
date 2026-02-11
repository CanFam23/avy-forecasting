import {type JSX} from "react";
import * as React from "react";

type ElevationBand = "lower" | "middle" | "upper";

export interface ForecastDay {
    date: number;
    zone: string;
    elevation: ElevationBand;
    predicted_danger: -1 | 1 | 2 | 3 | 4;
}

export interface ForecastProps {
    dayPreds: ForecastDay[];
    zone: string;
    latestDate: number;
    zoneDataName: string;
}

export interface navbarProps {
    navNames: string[];
}

export interface hamProps {
    navHTML: JSX.Element[];
    display: boolean;
    setDisplay: React.Dispatch<React.SetStateAction<boolean>>;
}