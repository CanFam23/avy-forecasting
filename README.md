# Avalanche Danger Classifier

Predicts daily avalanche danger for mountain ranges around Whitefish, Montana using weather data and snowpack simulations.

## Overview

This project combines weather forecasts and snowpack modeling to predict avalanche danger levels. It uses a **Random Forest classifier** trained on historical weather and snowpack data. Predictions are updated daily by pulling the latest data from the **HRRR weather model** and running simulations with **SNOWPACK**.

* **Training Accuracy:** 90%
* **Testing Accuracy:** ~60% (varies with seasonal conditions)
  * Currently struggling with generalization.

## Features

* Automatic daily prediction pipeline
* Data integration from HRRR and SNOWPACK
* Supports missing data simulation for incomplete datasets
* Random Forest classifier for danger prediction

## Installation

TBD

## Usage

TBD

## Data Sources

* **HRRR Weather Model:** Hourly high-resolution forecasts
* **SNOWPACK:** Snowpack simulation for stability and energy balance
* **FAC Coordinates:** Avalanche observation points

## Notes

* Model performance may decrease in unusual snow seasons due to poor generalization.
* Designed for local mountain ranges around Whitefish, MT.