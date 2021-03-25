---
title: 'diyepw: A Python package for Do-It-Yourself EnergyPlus Weather files'
tags:
  - Python
  - EnergyPlus
  - building energy modeling
  - weather data
  - meteorological year
authors:
  - name: Amanda D. Smith^[Corresponding author]
    orcid: 0000-0003-2990-2190
    affiliation: 1
  - name: Benjamin St&uuml;rmer
    orcid: 0000-0003-2007-929X
    affiliation: 2
  - name: Travis Thurber
    orcid: 0000-0002-4370-9971
    affiliation: 1
  - name: Chris Vernon
    orcid: 0000-0002-3406-6214
    affiliation: 1
affiliations:
 - name: Joint Global Change Research Institute, Pacific Northwest National Laboratory, College Park, MD, USA
   index: 1
date: 07 October 2020
bibliography: paper.bib
---

# Summary

`DIY EPW` allows for quick and easy generation of a set of EnergyPlus weather (EPW) files for a given set of weather station location(s) over selected historical year(s). Building energy modelers can use these auto-generated weather files in building performance simulations to represent the actual observed weather conditions in the location(s) of interest, based on meteorological observations obtained from the National Oceanic and Atmospheric Administration's Integrated Surface Database [@NOAA_ISD]. Because observed weather data are not available for every meteorological variable specified in the EPW format  [@EPWdd], DIY EPW starts with a widely-used set of typical meteorological year (TMY) files [@eplus-weather-data], using them as the template to generate new actual meterological year (AMY) files by substituting in the observed values of meteorological variables that are known to affect building energy performance.

DIY EPW provides a weather file or group of weather files as output which can be used directly with any building performance simulation software that uses EnergyPlus [@EnergyPlus] as its simulation engine. These weather files are output in the EPW format and can be used directly in EnergyPlus simulations, as the software checks for conformity to the requirements of the EPW data dictionary [@EPWdd]. `DIY EPW` is available here as a Python package [@github_diyepw], and as a set of scripts in a separate repository [@github_diyepw-scripts]. It can be called directly as a package to incorporate EPW file generation into a custom script, or used as a command-line tool, and is customizable according to the modeler's needs.

# Statement of need

Building energy modeling (BEM) practitioners and researchers have few options for obtaining weather files outside of those typically used with EnergyPlus, which are typical meteorological year (TMY) files that do not represent any given historical year and are usually only available for airport weather station locations.  In our case, the Building ENergy Demand (BEND) modeling team, working as part of the Integrated Multisector Multiscale Modeling (IM3) project [@IM3web], needed a way to use observed weather data to drive simulations of model buildings using EnergyPlus. Commercial providers do offer weather files for given year(s) and location(s) but they may charge for each weather file, and the source data and code used to process it will not be transparent to the user. A software package using reliable, quality-checked, publicly available weather data that can process it into weather files ready be directly used in EnergyPlus simulations will benefit the BEM community. 

# Relationship to other resources in this research area

DIY EPW is inspired by the Local Actual Meteorological Year File (LAF) app [@Bianchi2019-lm]. DIY EPW addresses some of its key limitations: 

- LAF's process requires downloading and clicking and it does not have a fully automated workflow.
- LAF is no longer developed or maintained.
- LAF relies on an API for downloading observed weather data that has limitations on the amount of data that can be downloaded without a paid account.
- LAF is not directly extensible to other sources of weather data, such as the NOAA ISD Lite format used here.

The EnergyPlus website lists additional resources for obtaining BEM weather files [@eplus-weather-data-for-simulation]. Few data providers can produce weather files for specific locations over a given historical period, and when they do provide such EPW files, the raw data used may not be available and the processing of that data to produce the EPWs is not fully documented and reproducible. The user may need to pay to obtain these files and does not have the option to adjust the standards for data quality--for determining which values are acceptable for a given meteorological variable, or for limiting the amount of data that is interpolated or otherwise imputed by the software generating the weather files. 

DIY EPW is freely available and open-source. The user can obtain weather files for free in an entirely automated workflow by simply specifying the location of interest using the World Meteorological Organization weather station number [@WMOstationlist] and a selected historical year or set of years. They also have the ability to see exactly how the file was constructed and to modify it according to their needs.

# Acknowledgements

This work was supported by the U.S. Department of Energy, Office of Science, as part of research in the MultiSector Dynamics, Earth and Environmental System Modeling Program. Pacific Northwest National Laboratory is a multi-program national laboratory operated by Battelle for the U.S. Department of Energy under Contract DE-AC05-76RL01830. A portion of the research was performed using PNNL Institutional Computing at Pacific Northwest National Laboratory. 

# References
