---
title: 'DIY EPW: A Python package for Do-It-Yourself EnergyPlus Weather files'
tags:
  - Python
  - EnergyPlus
  - building energy modeling
  - weather data
  - meteorological year
authors:
  - name: Amanda D. Smith^[Corresponding author: https://energyenvironment.pnnl.gov/staff/staff_info.asp?staff_num=3681]
    orcid: 0000-0003-2990-2190
    affiliation: "1" # (Multiple affiliations must be quoted)
  - name: Benjamin St\"urmer
    orcid: 0000-0003-2007-929X
    affiliation: 2
  - name: Travis Thurber
    orcid: 0000-0002-4370-9971
    affiliation: 1
  - name: Chris Vernon
    orcid: 0000-0002-3406-6214
    affiliation: "1"
affiliations:
 - name: Pacific Northwest National Laboratory, Richland, WA, USA
   index: 1
 - name: Independent Researcher
   index: 2
   
date: 2021-03-16

bibliography: paper.bib

---

# Summary

`DIY EPW` allows for quick and easy generation of a set of EnergyPlus weather (EPW) files for a
given set of weather station location(s) over selected historical year(s). Building energy modelers can use these auto-generated weather files in building performance simulations to represent the actual observed weather conditions in the location(s) of interest, based on meteorological observations obtained from the National Oceanic and Atmospheric Administration's Integrated Surface Database `[@NOAA_ISD]`.  DIY EPW provides a weather file or group of weather files as output which can be used directly with any building performance simulation software that uses EnergyPlus `[@EnergyPlus]` as its simulation engine. These weather files are output in the EPW format `[@EPWdd]` and can be used directly in simulations that employ EnergyPlus as their simulation engine. `DIY EPW` is available  as a Python
package in this repository, and as a set of scripts in a separate repository. It can be used as a command-line tool, customized if the modeler desires, or called directly as a package to incorporate EPW file generation into a custom script.

# Statement of need

The Building ENergy Demand (BEND) modeling team, as part of the Integrated Multisector Multiscale Modeling (IM3) project `[@IM3web]`, needed a way to use observed weather data to drive simulations of model buildings using EnergyPlus. They wanted to use reliable, quality-checked, publicly available data and process it into weather files that can be directly used
used in EnergyPlus simulations. 

Prior work by members of the BEND team `[@Burleyson2018-sb]`

Future project work will require the team to use projections for future weather conditions to simulate model buildings under different climate change scenarios throughout the the 21st century. Therefore, it is important that data obtained from disparate data sources can be processed by DIY EPW. --INSERT something about the abstractions made, the functions of the classes?--

# Relationship to other resources in this research area

DIY EPW is inspired by the Local Actual Meteorological Year File (LAF) app `[@Bianchi2019-lm]`. DIY EPW addresses some of its key limitations: 
- LAF relies on an API for downloading observed weather data that has limitations on the amount of data that can be downloaded without a paid account.
- LAF's process requires downloading and clicking and it does not have a fully automated workflow.
- LAF is no longer developed or maintained.
- LAF is not directly extensible to other sources of weather data, such as the NOAA ISD Lite format used here.

Other resources exist for obtaining weather files, but the raw data used is typically not available, the process for producing the EPWs is not fully documented and reproducible, and they are often paid products. DIY EPW is available free and open-source, so that the user does not need to pay for each individual weather file and has the ability to see exactly how the file was constructed.


# Acknowledgements

This work was supported by the U.S. Department of Energy, Office of Science, as part of research in the MultiSector Dynamics, Earth and Environmental System Modeling Program. Pacific Northwest National Laboratory is a multi-program national laboratory operated by Battelle for the U.S. Department of Energy under Contract DE-AC05-76RL01830. A portion of the research was performed using PNNL Institutional Computing at Pacific Northwest National Laboratory. 

# References
