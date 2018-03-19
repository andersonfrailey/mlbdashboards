# Introduction

This directory contains Python scripts that use data from MLB Statcast to create
interactive dashboards for exploring pitch-by-pitch data.

The primary tools used are [pybaseball](https://github.com/jldbc/pybaseball/tree/master/pybaseball) (version 1.0.3)
and [Bokeh](https://bokeh.pydata.org/en/latest/) (version 0.12.13).

## Current Dashboards

* `baseballmatchups.py`: view every pitch between a selected pitcher and batter in a given timeframe.
  * To run, navigate to the dashboards directory and use `bokeh serve baseballmatchups.py`