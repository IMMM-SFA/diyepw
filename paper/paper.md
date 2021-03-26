---
title: 'diyepw: A Python package for Do-It-Yourself EnergyPlus weather file generation'
tags:
  - Python
  - EnergyPlus
  - building energy modeling
  - weather data
  - meteorological year
authors:
  - name: Amanda D. Smith^[Corresponding author]
    orcid: 0000-0003-2990-2190
    affiliation: "1"
  - name: Benjamin St&uuml;rmer
    orcid: 0000-0003-2007-929X
    affiliation: "2"
  - name: Travis Thurber
    orcid: 0000-0002-4370-9971
    affiliation: "1"
  - name: Chris R. Vernon
    orcid: 0000-0002-3406-6214
    affiliation: "1"
affiliations:
 - name: Pacific Northwest National Laboratory, Richland, WA, USA
   index: 1
 - name: Independent Researcher
   index: 2
date: 24 March 2021
bibliography: paper.bib
---

# Summary

`diyepw` allows for quick and easy generation of a set of EnergyPlus weather (EPW) files for a given location over a given historical period. The user can obtain weather files for free in an automated workflow by simply specifying the location of interest using the World Meteorological Organization weather station number [@WMOstationlist], and specifying a year or set of years for which to generate EPW files. Building energy modelers can use these auto-generated weather files in building performance simulations to represent the actual observed weather conditions in the location(s) of interest, based on meteorological observations obtained from the National Oceanic and Atmospheric Administration's Integrated Surface Database [@NOAA_ISD]. Because observed weather data are not available for every meteorological variable specified in the EPW format [@EPWdd], `diyepw` starts with a widely-used set of typical meteorological year (TMY) files [@eplus-weather-data], using them as the template to generate new EPW files by substituting in the observed values of selected meteorological variables that are known to affect building energy performance. Its output is a weather file or group of weather files that conform to the data standards associated with the EPW format so they can be used with any building performance simulation software employing EnergyPlus [@EnergyPlus] as its simulation engine.

`diyepw` is available here as a Python package [@github_diyepw], and as a set of scripts in a separate repository [@github_diyepw-scripts]. It can be called directly as a package to incorporate EPW file generation into a custom script, or used as a command-line tool, and is customizable according to the modeler's needs. A step-by-step example tutorial is provided as a quick start option here: [Tutorial](https://diyepw.readthedocs.io/en/latest/README.html).

# Statement of need

Building energy modeling (BEM) practitioners and researchers have few options for obtaining weather files outside those shipped with EnergyPlus, which are typical meteorological year (TMY) files that do not represent any given historical year and are usually only available for airport weather station locations.  In our case, the Building ENergy Demand (BEND) modeling team, working as part of the Integrated Multisector Multiscale Modeling (IM3) project [@IM3web], needed a way to use observed weather data to drive simulations of model buildings using EnergyPlus. Previous IM3 research [@Burleyson2018-sb] showed that for regional-scale BEM, where many buildings are aggregated, a model that is forced with weather files taken from stations throughout the region will have lower bias in predicting the aggregate load than a model forced with only a few weather files that don't capture the heterogeneity in the region. Some commercial providers will offer weather files for given year(s) and location(s), but they may charge for each weather file and the source data and code used to process it will not be transparent to the user. Some modelers have created their own EPW files, but it is a labor-intensive process and no open-source, automated, reproducible software package exists to produce EPW files from publicly available weather observations until `diyepw`. This software will benefit the BEM community by allowing for easy use of reliable, quality-checked, publicly available weather data in their simulations. 

# Relationship to other resources in this research area

`diyepw` was inspired by the Local Actual Meteorological Year File (LAF) application [@Bianchi2019-lm]. `diyepw` addresses some of its key limitations: 

- LAF's workflow requires downloading and clicking and is not fully automated.
- LAF is no longer developed or maintained.
- LAF relies on an API for downloading observed weather data that has limitations on the amount of data that can be downloaded without a paid account.
- LAF is not directly extensible to other sources of weather data, such as the NOAA ISD Lite format used here.

The EnergyPlus website lists additional resources for obtaining BEM weather files [@eplus-weather-data-for-simulation]. Few data providers can produce weather files for specific locations over a given historical period, and when they do provide such EPW files, the raw data used may not be available and thus the processing of that data to produce the EPWs is not fully documented and reproducible. The user may be required to pay for these files and would not have the option to adjust the standards for data quality--for determining which values are acceptable for a given meteorological variable, or for limiting the amount of data that is interpolated or otherwise imputed by the software generating the weather files.

# Acknowledgements

This work was supported by the U.S. Department of Energy, Office of Science, as part of research in the MultiSector Dynamics, Earth and Environmental System Modeling Program. Pacific Northwest National Laboratory is a multi-program national laboratory operated by Battelle for the U.S. Department of Energy under Contract DE-AC05-76RL01830. A portion of the research was performed using PNNL Institutional Computing at Pacific Northwest National Laboratory. 

# References
