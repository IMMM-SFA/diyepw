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
    affiliation: 1
  - name: Travis Thurber
    orcid: 0000-0002-4370-9971
    affiliation: 1
  - name: Chris Vernon
    orcid: 0000-0002-3406-6214
    affiliation: "1"
affiliations:
 - name: Pacific Northwest National Laboratory, Richland, WA, USA
   index: 1
 - name: Institution Name
   index: 2
   
date: 2021-03-16

bibliography: paper.bib

---

# Summary

The forces on stars, galaxies, and dark matter under external gravitational
fields lead to the dynamical evolution of structures in the universe. The orbits
of these bodies are therefore key to understanding the formation, history, and
future state of galaxies. The field of "galactic dynamics," which aims to model
the gravitating components of galaxies to study their structure and evolution,
is now well-established, commonly taught, and frequently used in astronomy.
Aside from toy problems and demonstrations, the majority of problems require
efficient numerical tools, many of which require the same base code (e.g., for
performing numerical orbit integration).


`DIY EPW` allows for quick and easy automated generation of a set of EnergyPlus weather (EPW) files for a
given set of weather station locations over a selected historical year(s). This provides a weather file that can be
used with building energy performance simulation to represent observed weather in a given year(s). `DIY EPW` is provided as both a set of scripts (https://github.com/IMMM-SFA/diyepw-scripts) and as a Python
package (https://github.com/IMMM-SFA/diyepw). Therefore it can be used as a command-line tool, or as a
package to incorporate EPW file generation into a custom script.

# Statement of need

`Gala` is an Astropy-affiliated Python package for galactic dynamics. Python
enables wrapping low-level languages (e.g., C) for speed without losing
flexibility or ease-of-use in the user-interface. The API for `Gala` was
designed to provide a class-based and user-friendly interface to fast (C or
Cython-optimized) implementations of common operations such as gravitational
potential and force evaluation, orbit integration, dynamical transformations,
and chaos indicators for nonlinear dynamics. `Gala` also relies heavily on and
interfaces well with the implementations of physical units and astronomical
coordinate systems in the `Astropy` package [@astropy] (`astropy.units` and
`astropy.coordinates`).

`Gala` was designed to be used by both astronomical researchers and by
students in courses on gravitational dynamics or astronomy. It has already been
used in a number of scientific publications [@Pearson:2017] and has also been
used in graduate courses on Galactic dynamics to, e.g., provide interactive
visualizations of textbook material [@Binney:2008]. The combination of speed,
design, and support for Astropy functionality in `Gala` will enable exciting
scientific explorations of forthcoming data releases from the *Gaia* mission
[@gaia] by students and experts alike.

The IM3 project's (https://im3.pnnl.gov/) Building Energy Demand modeling team needed a way to convert
observed weather data (and, eventually, future projected weather data) into weather files that are ready to be
used in EnergyPlus simulation.

# Relationship to other resources in this research area

DIY EPW is inspired by the Local Actual Meteorological Year File (LAF) app \cite{Bianchi2019-lm}. DIY EPW addresses some of its key limitations: 
- LAF relies on an API for downloading observed weather data that has limitations on the amount of data that can be downloaded without a paid account.
- LAF's process is not fully automated--it requires downloading and clicking and does not have a fully automated workflow.
- LAF is no longer developed or maintained.
- LAF is not directly extensible to other sources of weather data, such as the NOAA ISD Lite format used here.

DIY EPW was inspired by LAF and shares one author in common, [@amandadsmith](https://github.com/amandadsmith). DIY EPW has adapted functionality for reading and writing EPWs from code developed by [@carlobianchi89].

Other resources exist for obtaining weather files, but the raw data used is typically not available, the process for producing the EPWs is not fully documented and reproducible, and they are often paid products. DIY EPW is available free and open-source, so that the user does not need to pay for each individual weather file and has the ability to see exactly how the file was constructed.

# Mathematics

Single dollars ($) are required for inline mathematics e.g. $f(x) = e^{\pi/x}$

Double dollars make self-standing equations:

$$\Theta(x) = \left\{\begin{array}{l}
0\textrm{ if } x < 0\cr
1\textrm{ else}
\end{array}\right.$$

You can also use plain \LaTeX for equations
\begin{equation}\label{eq:fourier}
\hat f(\omega) = \int_{-\infty}^{\infty} f(x) e^{i\omega x} dx
\end{equation}
and refer to \autoref{eq:fourier} from text.

# Citations

Citations to entries in paper.bib should be in
[rMarkdown](http://rmarkdown.rstudio.com/authoring_bibliographies_and_citations.html)
format.

If you want to cite a software repository URL (e.g. something on GitHub without a preferred
citation) then you can do it with the example BibTeX entry below for @fidgit.

For a quick reference, the following citation commands can be used:
- `@author:2001`  ->  "Author et al. (2001)"
- `[@author:2001]` -> "(Author et al., 2001)"
- `[@author1:2001; @author2:2001]` -> "(Author1 et al., 2001; Author2 et al., 2002)"

# Figures

Figures can be included like this:
![Caption for example figure.\label{fig:example}](figure.png)
and referenced from text using \autoref{fig:example}.

Figure sizes can be customized by adding an optional second parameter:
![Caption for example figure.](figure.png){ width=20% }

# Acknowledgements

This research was supported by the U.S. Department of Energy, Office of Science, as part of research in the MultiSector Dynamics, Earth and Environmental System Modeling Program. Pacific Northwest National Laboratory is a multi-program national laboratory operated by Battelle for the U.S. Department of Energy under Contract DE-AC05-76RL01830. A portion of the research was performed using PNNL Institutional Computing at Pacific Northwest National Laboratory. 

# References
