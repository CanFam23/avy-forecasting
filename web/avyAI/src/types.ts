import {type JSX} from "react";
import * as React from "react";

type ElevationBand = "lower" | "middle" | "upper";

export interface ForecastDay {
    date: number;
    zone: string;
    elevation: ElevationBand;
    predicted_danger: -1 | 1 | 2 | 3 | 4;
}

export interface ForecastDiscussion {
    zone: string;
    primary_concern: string;
    discussion: string;
    travel_advice: string;
}

export type WeatherRow = {
    zone_name: string;
    elevation_band: "lower" | "middle" | "upper" | string;
    slope_azi: number;
    temp_avg: number;
    rh_avg: number;
    wind_avg: number;
    new_snow_24: number;
    precip_total: number;
    snow_depth_avg: number;
    swe_avg: number;
    danger_level: number;
    date_epoch: number;
};

export interface ForecastProps {
    dayPreds: ForecastDay[];
    zone: string;
    latestDate: number;
    zoneDataName: string;
    forecastDis: ForecastDiscussion[];
    weather: WeatherRow[];
}

export interface NavbarProps {
    navNames: Record<string, string>;
}

export interface hamProps {
    navHTML: JSX.Element[];
    display: boolean;
    setDisplay: React.Dispatch<React.SetStateAction<boolean>>;
}

export type GraphData = {
    predDangers: ForecastDay[];
    actDangers: ForecastDay[];
}

export type PageProps = {
    dayPreds: ForecastDay[];
    actDang: ForecastDay[];
}

export type HomeProps = PageProps & {
    forecastDis: ForecastDiscussion[];
    weather: WeatherRow[];
    latestDay: number;
}

export type PerformanceMetric = {
    accuracy: number;
    balanced_accuracy: number
    mae: number;
}

export type PerformanceProps = PageProps & {
    performanceMetrics: PerformanceMetric | null;
}