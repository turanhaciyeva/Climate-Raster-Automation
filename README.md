1. Climate Raster Automation Tool

A Python/ArcPy tool for automating district-level analysis of WorldClim monthly climate raster data in ArcGIS.

2. Overview

Processing large numbers of monthly climate rasters manually can be time-consuming and repetitive.

This tool automatically processes climate GeoTIFF files and calculates district-level statistics using administrative boundaries.

3. Supported climate variables

- Maximum temperature (TMAX)
- Minimum temperature (TMIN)
- Precipitation (PREC)

4. Workflow

Climate GeoTIFFs → Python / ArcPy → Zonal Statistics by District → Excel

The tool automatically:

- Detects the climate variable from the raster filename
- Extracts year and month
- Calculates mean raster values for each district
- Processes multiple raster files in a single run
- Exports the results to a structured Excel table

5. Example Input

wc2.1_2.5m_tmax_2019-01.tif

wc2.1_2.5m_tmin_2019-01.tif

wc2.1_2.5m_prec_2019-01.tif


6. Data Source

Climate data used in this workflow is available from WorldClim:

https://www.worldclim.org/
