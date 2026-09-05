"""
Seed script for the Earth Health Dashboard: cited data sources, real
metrics, and their full historical reading series. Idempotent - safe to
run again any time to append newer years (upserts by id / (metric_id,
reading_date)).

Sources:
- NOAA GML Mauna Loa annual mean CO2 (1959-present): https://gml.noaa.gov/ccgg/trends/
- NOAA GML global annual mean CH4 (1984-present): https://gml.noaa.gov/ccgg/trends_ch4/
- NASA GISTEMP v4 global annual temp anomaly (1880-present): https://data.giss.nasa.gov/gistemp/
- Our World in Data (OWID), each citing its own primary source:
  - Sea level: Church & White (2011) + UHSLC tide gauge reconstruction, 1880-2020
  - Renewable share of electricity: Ember / Energy Institute Statistical Review, 1900-present
  - Arctic sea ice minimum extent: NSIDC Sea Ice Index, 1979-present
  - Deforestation: FAO Forest Resources Assessment, 1990-2020 (5-yearly, FAO's native resolution)
  - Red List Index (extinction risk): IUCN, 1993-present
  - Population-weighted PM2.5: Health Effects Institute State of Global Air, 1998-present
  - Living Planet Index (wildlife health): WWF / ZSL, 1970-present
  - Freshwater withdrawal stress: UN SDG indicator 6.4.2, 2000-present
- Ocean pH: Hawaii Ocean Time-series, Station ALOHA, 1988-present (decadal readings)
- Coral reef health: GCRMN "Status of Coral Reefs of the World: 2020", 4 epoch points
- Ocean plastic pollution: Jambeck et al. 2015 (Science), single 2010 point estimate

All 14 of the dashboard's original metrics are now backed by real, cited
data. Every OWID figure was pulled as raw CSV via their grapher API and
parsed directly with Python (not summarized through an LLM), to keep this
a reliable source of truth. The final 3 (ocean pH, coral reefs, ocean
plastic) were researched via a separate LLM session with a citation-first
prompt, then cross-checked against known published figures before being
seeded here. Ocean plastic intentionally seeds only a single data point
rather than fabricate a trend from incompatible study methodologies (see
OCEAN_PLASTIC_MMT_PER_YEAR below).

Note: CO2 before 1959 (pre-instrumental) is available from ice-core
reconstructions (e.g. Law Dome), but isn't seeded here yet - the exact
figures need to be pulled from the primary data file directly rather than
a secondhand summary, to keep this a reliable source.
"""

import asyncio
from datetime import date
from sqlalchemy import select

from app.core.database import get_async_session, create_async_database_engine
from app.models.earth_metric import DataSource, EarthMetric, EarthMetricReading


# NOAA GML Mauna Loa annual mean CO2, ppm. https://gml.noaa.gov/webdata/ccgg/trends/co2/co2_annmean_mlo.txt
CO2_ANNUAL_MEAN_PPM = {
    1959: 315.98, 1960: 316.91, 1961: 317.64, 1962: 318.45, 1963: 318.99,
    1964: 319.62, 1965: 320.04, 1966: 321.37, 1967: 322.18, 1968: 323.05,
    1969: 324.62, 1970: 325.68, 1971: 326.32, 1972: 327.46, 1973: 329.68,
    1974: 330.19, 1975: 331.13, 1976: 332.03, 1977: 333.84, 1978: 335.41,
    1979: 336.84, 1980: 338.76, 1981: 340.12, 1982: 341.48, 1983: 343.15,
    1984: 344.87, 1985: 346.35, 1986: 347.61, 1987: 349.31, 1988: 351.69,
    1989: 353.20, 1990: 354.45, 1991: 355.70, 1992: 356.54, 1993: 357.21,
    1994: 358.96, 1995: 360.97, 1996: 362.74, 1997: 363.88, 1998: 366.84,
    1999: 368.54, 2000: 369.71, 2001: 371.32, 2002: 373.45, 2003: 375.98,
    2004: 377.70, 2005: 379.98, 2006: 382.09, 2007: 384.02, 2008: 385.83,
    2009: 387.64, 2010: 390.10, 2011: 391.85, 2012: 394.06, 2013: 396.74,
    2014: 398.81, 2015: 401.01, 2016: 404.41, 2017: 406.76, 2018: 408.72,
    2019: 411.65, 2020: 414.21, 2021: 416.41, 2022: 418.53, 2023: 421.08,
    2024: 424.61, 2025: 427.35,
}

# NASA GISTEMP v4 global annual (J-D) mean surface temp anomaly, degrees C
# vs. 1951-1980 baseline. https://data.giss.nasa.gov/gistemp/tabledata_v4/GLB.Ts+dSST.csv
GLOBAL_TEMP_ANOMALY_C = {
    1880: -0.17, 1881: -0.09, 1882: -0.11, 1883: -0.17, 1884: -0.28, 1885: -0.33,
    1886: -0.32, 1887: -0.36, 1888: -0.18, 1889: -0.11, 1890: -0.36, 1891: -0.22,
    1892: -0.27, 1893: -0.31, 1894: -0.30, 1895: -0.23, 1896: -0.12, 1897: -0.11,
    1898: -0.28, 1899: -0.18, 1900: -0.09, 1901: -0.15, 1902: -0.28, 1903: -0.37,
    1904: -0.48, 1905: -0.27, 1906: -0.23, 1907: -0.39, 1908: -0.43, 1909: -0.49,
    1910: -0.44, 1911: -0.45, 1912: -0.37, 1913: -0.35, 1914: -0.16, 1915: -0.15,
    1916: -0.36, 1917: -0.46, 1918: -0.30, 1919: -0.28, 1920: -0.28, 1921: -0.19,
    1922: -0.28, 1923: -0.26, 1924: -0.27, 1925: -0.22, 1926: -0.11, 1927: -0.22,
    1928: -0.20, 1929: -0.36, 1930: -0.16, 1931: -0.09, 1932: -0.16, 1933: -0.29,
    1934: -0.13, 1935: -0.20, 1936: -0.15, 1937: -0.03, 1938: 0.00, 1939: -0.02,
    1940: 0.12, 1941: 0.18, 1942: 0.06, 1943: 0.09, 1944: 0.20, 1945: 0.09,
    1946: -0.07, 1947: -0.03, 1948: -0.11, 1949: -0.11, 1950: -0.17, 1951: -0.07,
    1952: 0.01, 1953: 0.08, 1954: -0.13, 1955: -0.14, 1956: -0.19, 1957: 0.05,
    1958: 0.06, 1959: 0.03, 1960: -0.02, 1961: 0.06, 1962: 0.03, 1963: 0.05,
    1964: -0.20, 1965: -0.11, 1966: -0.06, 1967: -0.02, 1968: -0.08, 1969: 0.05,
    1970: 0.03, 1971: -0.08, 1972: 0.01, 1973: 0.16, 1974: -0.07, 1975: -0.01,
    1976: -0.10, 1977: 0.18, 1978: 0.07, 1979: 0.16, 1980: 0.26, 1981: 0.32,
    1982: 0.14, 1983: 0.31, 1984: 0.15, 1985: 0.12, 1986: 0.18, 1987: 0.32,
    1988: 0.39, 1989: 0.27, 1990: 0.45, 1991: 0.40, 1992: 0.22, 1993: 0.23,
    1994: 0.31, 1995: 0.44, 1996: 0.33, 1997: 0.46, 1998: 0.61, 1999: 0.38,
    2000: 0.39, 2001: 0.53, 2002: 0.63, 2003: 0.62, 2004: 0.53, 2005: 0.68,
    2006: 0.64, 2007: 0.66, 2008: 0.54, 2009: 0.66, 2010: 0.73, 2011: 0.61,
    2012: 0.65, 2013: 0.68, 2014: 0.75, 2015: 0.90, 2016: 1.01, 2017: 0.92,
    2018: 0.85, 2019: 0.98, 2020: 1.01, 2021: 0.85, 2022: 0.89, 2023: 1.17,
    2024: 1.28, 2025: 1.19,
}

# NOAA GML global annual mean CH4, ppb. https://gml.noaa.gov/webdata/ccgg/trends/ch4/ch4_annmean_gl.txt
METHANE_ANNUAL_MEAN_PPB = {
    1984: 1644.84, 1985: 1657.29, 1986: 1670.09, 1987: 1682.71, 1988: 1693.19,
    1989: 1704.53, 1990: 1714.46, 1991: 1724.79, 1992: 1735.47, 1993: 1736.48,
    1994: 1742.08, 1995: 1748.88, 1996: 1751.30, 1997: 1754.51, 1998: 1765.57,
    1999: 1772.30, 2000: 1773.22, 2001: 1771.29, 2002: 1772.68, 2003: 1777.33,
    2004: 1777.13, 2005: 1774.23, 2006: 1774.94, 2007: 1781.33, 2008: 1787.01,
    2009: 1793.52, 2010: 1798.92, 2011: 1803.03, 2012: 1808.07, 2013: 1813.42,
    2014: 1822.59, 2015: 1834.19, 2016: 1843.18, 2017: 1849.62, 2018: 1857.34,
    2019: 1866.59, 2020: 1878.72, 2021: 1894.81, 2022: 1910.95, 2023: 1921.38,
    2024: 1929.40, 2025: 1935.94,
}

# OWID (Church & White 2011 + UHSLC), annual mean of quarterly global sea
# level change vs. the 1993-2008 baseline, mm. https://ourworldindata.org/grapher/sea-level
SEA_LEVEL_MM = {
    1880: -180.24, 1881: -173.04, 1882: -191.58, 1883: -190.46, 1884: -166.6, 1885: -168.56,
    1886: -169.6, 1887: -176.76, 1888: -174.16, 1889: -171.48, 1890: -169.88, 1891: -173.36,
    1892: -168.66, 1893: -164.78, 1894: -174.3, 1895: -162.26, 1896: -168.62, 1897: -164.24,
    1898: -157.48, 1899: -148.06, 1900: -152.38, 1901: -154.01, 1902: -148.87, 1903: -140.87,
    1904: -149.96, 1905: -156.65, 1906: -150.3, 1907: -150.71, 1908: -153.63, 1909: -150.01,
    1910: -149.21, 1911: -142.05, 1912: -144.09, 1913: -142.17, 1914: -138.25, 1915: -126.31,
    1916: -130.64, 1917: -133.83, 1918: -135.71, 1919: -134.67, 1920: -133.52, 1921: -131.21,
    1922: -132.56, 1923: -129.73, 1924: -138.27, 1925: -136.76, 1926: -129.44, 1927: -130.5,
    1928: -133.96, 1929: -133.75, 1930: -129.59, 1931: -129.72, 1932: -124.73, 1933: -119.18,
    1934: -125.1, 1935: -119.34, 1936: -123.59, 1937: -118.25, 1938: -114.93, 1939: -109.91,
    1940: -115.56, 1941: -102.91, 1942: -103.52, 1943: -102.1, 1944: -109.47, 1945: -106.89,
    1946: -98.98, 1947: -97.58, 1948: -90.75, 1949: -92.24, 1950: -90.9, 1951: -80.57,
    1952: -84.04, 1953: -78.17, 1954: -82.74, 1955: -80.3, 1956: -85.34, 1957: -73.88,
    1958: -71.82, 1959: -70.49, 1960: -67.83, 1961: -60.72, 1962: -66.44, 1963: -67.08,
    1964: -76.0, 1965: -65.07, 1966: -69.13, 1967: -69.29, 1968: -67.95, 1969: -60.75,
    1970: -63.05, 1971: -57.6, 1972: -49.26, 1973: -55.22, 1974: -42.47, 1975: -44.11,
    1976: -45.53, 1977: -46.98, 1978: -39.91, 1979: -46.3, 1980: -39.86, 1981: -27.45,
    1982: -33.01, 1983: -23.77, 1984: -25.51, 1985: -35.11, 1986: -34.9, 1987: -34.75,
    1988: -29.61, 1989: -25.96, 1990: -23.97, 1991: -20.98, 1992: -17.96, 1993: -21.85,
    1994: -19.66, 1995: -14.69, 1996: -9.88, 1997: -2.78, 1998: -8.36, 1999: -3.11,
    2000: -2.31, 2001: 2.49, 2002: 0.89, 2003: 10.16, 2004: 10.26, 2005: 9.79, 2006: 10.99,
    2007: 13.77, 2008: 24.29, 2009: 28.93, 2010: 36.2, 2011: 36.18, 2012: 42.34, 2013: 42.03,
    2014: 49.9, 2015: 52.18, 2016: 56.33, 2017: 55.11, 2018: 52.08, 2019: 60.98, 2020: 66.0,
}

# OWID/Ember, renewable share of global electricity generation, %.
# https://ourworldindata.org/grapher/share-electricity-renewables
RENEWABLE_ELECTRICITY_SHARE_PCT = {
    1900: 41.224, 1901: 39.497, 1902: 38.169, 1903: 36.229, 1904: 35.182, 1905: 35.086,
    1906: 35.999, 1907: 36.742, 1908: 38.57, 1909: 39.166, 1910: 39.934, 1911: 41.482,
    1912: 42.327, 1913: 41.474, 1914: 40.83, 1915: 41.676, 1916: 41.981, 1917: 41.688,
    1918: 47.124, 1919: 50.957, 1920: 44.536, 1921: 43.922, 1922: 43.61, 1923: 42.119,
    1924: 41.701, 1925: 40.425, 1926: 42.124, 1927: 42.422, 1928: 43.406, 1929: 41.878,
    1930: 42.268, 1931: 41.561, 1932: 44.42, 1933: 44.019, 1934: 41.96, 1935: 43.172,
    1936: 40.812, 1937: 40.986, 1938: 40.342, 1939: 38.355, 1940: 37.654, 1941: 37.128,
    1942: 37.294, 1943: 37.636, 1944: 38.029, 1945: 39.667, 1946: 41.128, 1947: 38.001,
    1948: 36.968, 1949: 36.062, 1950: 35.647, 1951: 34.668, 1952: 34.331, 1953: 32.472,
    1954: 31.959, 1955: 30.743, 1956: 30.374, 1957: 30.634, 1958: 32.09, 1959: 30.055,
    1960: 29.924, 1961: 29.594, 1962: 28.693, 1963: 27.914, 1964: 26.582, 1965: 27.804,
    1966: 27.51, 1967: 26.487, 1968: 25.633, 1969: 24.965, 1970: 24.232, 1971: 23.875,
    1972: 23.067, 1973: 21.776, 1974: 23.308, 1975: 22.761, 1976: 21.229, 1977: 20.977,
    1978: 21.549, 1979: 21.706, 1980: 21.505, 1981: 21.557, 1982: 21.81, 1983: 21.868,
    1984: 21.468, 1985: 20.817, 1986: 20.545, 1987: 19.914, 1988: 19.683, 1989: 18.83,
    1990: 19.06, 1991: 19.107, 1992: 19.006, 1993: 19.707, 1994: 19.378, 1995: 19.72,
    1996: 19.406, 1997: 19.362, 1998: 19.061, 1999: 18.754, 2000: 18.716, 2001: 18.044,
    2002: 17.908, 2003: 17.442, 2004: 17.982, 2005: 18.096, 2006: 18.228, 2007: 17.974,
    2008: 18.908, 2009: 19.467, 2010: 19.721, 2011: 20.016, 2012: 20.977, 2013: 21.712,
    2014: 22.263, 2015: 22.967, 2016: 23.732, 2017: 24.466, 2018: 25.089, 2019: 26.071,
    2020: 27.987, 2021: 28.102, 2022: 29.47, 2023: 30.323, 2024: 31.935, 2025: 33.76,
}

# OWID/NSIDC, Arctic sea ice minimum (September) extent, million km^2.
# https://ourworldindata.org/grapher/arctic-sea-ice
ARCTIC_ICE_MIN_EXTENT_MKM2 = {
    1979: 7.051, 1980: 7.667, 1981: 7.138, 1982: 7.302, 1983: 7.395, 1984: 6.805, 1985: 6.698,
    1986: 7.411, 1987: 7.279, 1988: 7.369, 1989: 7.008, 1990: 6.143, 1991: 6.473, 1992: 7.474,
    1993: 6.397, 1994: 7.138, 1995: 6.08, 1996: 7.583, 1997: 6.686, 1998: 6.536, 1999: 6.117,
    2000: 6.246, 2001: 6.732, 2002: 5.827, 2003: 6.116, 2004: 5.984, 2005: 5.504, 2006: 5.862,
    2007: 4.267, 2008: 4.687, 2009: 5.262, 2010: 4.865, 2011: 4.561, 2012: 3.566, 2013: 5.208,
    2014: 5.22, 2015: 4.616, 2016: 4.528, 2017: 4.822, 2018: 4.785, 2019: 4.364, 2020: 4.001,
    2021: 4.952, 2022: 4.897, 2023: 4.381, 2024: 4.351, 2025: 4.747,
}

# OWID/FAO Forest Resources Assessment, net deforestation, million hectares/year.
# 5-yearly - FAO's native assessment resolution. https://ourworldindata.org/grapher/annual-deforestation
DEFORESTATION_M_HA_PER_YEAR = {
    1990: 15.819, 2000: 13.329, 2010: 9.881, 2015: 9.474, 2020: 8.49,
}

# OWID/IUCN, Red List Index (1 = no species threatened with extinction).
# https://ourworldindata.org/grapher/red-list-index
RED_LIST_INDEX = {
    1993: 0.81, 1994: 0.81, 1995: 0.8, 1996: 0.8, 1997: 0.8, 1998: 0.8, 1999: 0.8, 2000: 0.8,
    2001: 0.8, 2002: 0.79, 2003: 0.79, 2004: 0.79, 2005: 0.79, 2006: 0.79, 2007: 0.79,
    2008: 0.78, 2009: 0.78, 2010: 0.78, 2011: 0.78, 2012: 0.77, 2013: 0.77, 2014: 0.77,
    2015: 0.77, 2016: 0.77, 2017: 0.76, 2018: 0.76, 2019: 0.76, 2020: 0.76, 2021: 0.75,
    2022: 0.75, 2023: 0.75, 2024: 0.75,
}

# OWID/Health Effects Institute State of Global Air, population-weighted
# ambient PM2.5, ug/m^3. https://ourworldindata.org/grapher/pm25-air-pollution
PM25_UGM3 = {
    1998: 24.42, 1999: 23.68, 2000: 27.3, 2001: 28.32, 2002: 29.01, 2003: 30.49, 2004: 30.39,
    2005: 31.14, 2006: 32.44, 2007: 33.1, 2008: 33.61, 2009: 33.22, 2010: 33.33, 2011: 35.01,
    2012: 33.69, 2013: 34.08, 2014: 34.7, 2015: 35.89, 2016: 35.07, 2017: 34.27, 2018: 33.41,
    2019: 32.18, 2020: 30.16, 2021: 30.9, 2022: 30.4, 2023: 30.06, 2024: 29.9,
}

# OWID/WWF-ZSL Living Planet Index, global, indexed to 100 in 1970.
# https://ourworldindata.org/grapher/global-living-planet-index
LIVING_PLANET_INDEX = {
    1970: 100.0, 1971: 99.41, 1972: 98.14, 1973: 96.62, 1974: 94.81, 1975: 92.66, 1976: 89.99,
    1977: 86.37, 1978: 82.87, 1979: 80.26, 1980: 78.43, 1981: 77.01, 1982: 74.73, 1983: 72.18,
    1984: 69.71, 1985: 67.67, 1986: 66.17, 1987: 64.42, 1988: 62.68, 1989: 61.36, 1990: 60.09,
    1991: 58.82, 1992: 57.28, 1993: 55.24, 1994: 53.25, 1995: 51.15, 1996: 50.25, 1997: 48.92,
    1998: 47.5, 1999: 45.68, 2000: 44.37, 2001: 43.13, 2002: 42.01, 2003: 40.93, 2004: 39.98,
    2005: 38.87, 2006: 37.45, 2007: 35.95, 2008: 34.36, 2009: 32.71, 2010: 31.1, 2011: 29.6,
    2012: 28.67, 2013: 28.41, 2014: 28.5, 2015: 28.57, 2016: 27.79, 2017: 27.37, 2018: 27.1,
    2019: 27.33, 2020: 27.13,
}

# OWID/UN SDG indicator 6.4.2, freshwater withdrawal as % of available
# internal renewable freshwater resources, global.
# https://ourworldindata.org/grapher/freshwater-withdrawals-as-a-share-of-internal-resources
WATER_STRESS_PCT = {
    2000: 17.47, 2001: 17.64, 2002: 17.76, 2003: 17.91, 2004: 17.92, 2005: 17.92, 2006: 18.43,
    2007: 18.54, 2008: 18.14, 2009: 18.07, 2010: 18.12, 2011: 17.98, 2012: 18.03, 2013: 17.92,
    2014: 17.97, 2015: 17.83, 2016: 17.91, 2017: 17.99, 2018: 17.96, 2019: 18.01, 2020: 17.81,
    2021: 17.79, 2022: 17.77, 2023: 17.59,
}

# Hawaii Ocean Time-series (HOT), Station ALOHA surface ocean pH (Total
# Scale). Approximate decadal readings from the published record - not
# exact annual values, since HOT-DOGS requires an interactive query tool
# rather than a flat downloadable file. https://hahana.soest.hawaii.edu/hot/hot-dogs/
OCEAN_PH = {
    1988: 8.110, 2000: 8.085, 2010: 8.065, 2020: 8.048,
}

# GCRMN "Status of Coral Reefs of the World: 2020" report (published 2021):
# global average hard coral cover by assessment epoch, 1978-2019 dataset.
# GCRMN publishes epoch assessments, not an annual series - years below
# are representative midpoints of each reported epoch.
CORAL_COVER_PCT = {
    1990: 31.0,  # 1978-1997 pre-bleaching baseline (30.2-32.0%)
    1998: 27.0,  # 1st global mass bleaching event (El Nino)
    2009: 33.0,  # inter-bleaching recovery peak
    2018: 28.8,  # after 2nd/3rd global bleaching events (2014-2017)
}

# Ocean plastic pollution has no continuous annual time series - published
# estimates use incompatible methodologies/scopes (coastal input vs.
# riverine-only vs. all aquatic ecosystems), so blending them into one
# series would misrepresent a trend that doesn't exist. Seeding a single
# point from the most directly comparable, widely-cited estimate instead.
# Jambeck et al. 2015, Science, DOI 10.1126/science.1260352: mismanaged
# coastal plastic waste entering the ocean, assessment year 2010.
OCEAN_PLASTIC_MMT_PER_YEAR = {
    2010: 8.0,  # midpoint of reported 4.8-12.7 million metric tons/year
}


async def _get_or_create_source(session, name, organization, url, description):
    result = await session.execute(select(DataSource).where(DataSource.name == name))
    existing = result.scalar_one_or_none()
    if existing:
        return existing
    source = DataSource(name=name, organization=organization, url=url, description=description)
    session.add(source)
    await session.flush()
    return source


async def _upsert_metric(session, **fields):
    result = await session.execute(select(EarthMetric).where(EarthMetric.id == fields['id']))
    existing = result.scalar_one_or_none()
    if existing:
        for key, value in fields.items():
            setattr(existing, key, value)
        return existing
    metric = EarthMetric(**fields)
    session.add(metric)
    await session.flush()
    return metric


async def _upsert_readings(session, metric_id, source_id, annual_values, month=7, day=1):
    result = await session.execute(
        select(EarthMetricReading).where(EarthMetricReading.metric_id == metric_id)
    )
    existing_by_date = {r.reading_date: r for r in result.scalars().all()}

    added = 0
    updated = 0
    for year, value in annual_values.items():
        reading_date = date(year, month, day)
        existing = existing_by_date.get(reading_date)
        if existing:
            # Keep existing rows in sync if the value or cited source changes
            # upstream (e.g. a citation fix) - not just insert-if-missing.
            if existing.value != value or existing.source_id != source_id:
                existing.value = value
                existing.source_id = source_id
                updated += 1
            continue
        session.add(EarthMetricReading(
            metric_id=metric_id,
            reading_date=reading_date,
            value=value,
            source_id=source_id,
        ))
        added += 1
    if updated:
        print(f"  ({metric_id}: {updated} existing readings updated - value/source changed)")
    return added


async def seed():
    create_async_database_engine()

    async for session in get_async_session():
        noaa_co2 = await _get_or_create_source(
            session,
            name="NOAA GML Mauna Loa CO2 Annual Mean",
            organization="NOAA Global Monitoring Laboratory",
            url="https://gml.noaa.gov/ccgg/trends/",
            description="Instrumental atmospheric CO2 record measured at Mauna Loa Observatory, Hawaii, since 1958 (Keeling Curve).",
        )
        nasa_gistemp = await _get_or_create_source(
            session,
            name="NASA GISTEMP v4 Global Annual Mean",
            organization="NASA Goddard Institute for Space Studies",
            url="https://data.giss.nasa.gov/gistemp/",
            description="Global-mean surface temperature anomaly relative to the 1951-1980 base period.",
        )
        noaa_ch4 = await _get_or_create_source(
            session,
            name="NOAA GML Global Annual Mean CH4",
            organization="NOAA Global Monitoring Laboratory",
            url="https://gml.noaa.gov/ccgg/trends_ch4/",
            description="Global mean atmospheric methane concentration from the NOAA cooperative air sampling network.",
        )
        owid_sea_level = await _get_or_create_source(
            session,
            name="Global Mean Sea Level (Church & White 2011 + UHSLC)",
            organization="Our World in Data",
            url="https://ourworldindata.org/grapher/sea-level",
            description="Reconstructed global mean sea level change vs. the 1993-2008 average, from tide gauges and satellite altimetry.",
        )
        owid_renewables = await _get_or_create_source(
            session,
            name="Share of Electricity from Renewables",
            organization="Our World in Data (Ember / Energy Institute)",
            url="https://ourworldindata.org/grapher/share-electricity-renewables",
            description="Share of global electricity generation from renewable sources (hydro, wind, solar, etc).",
        )
        owid_arctic_ice = await _get_or_create_source(
            session,
            name="Arctic Sea Ice Minimum Extent",
            organization="Our World in Data (NSIDC)",
            url="https://ourworldindata.org/grapher/arctic-sea-ice",
            description="Annual September (summer) minimum Arctic sea ice extent from satellite observations.",
        )
        owid_deforestation = await _get_or_create_source(
            session,
            name="Net Deforestation",
            organization="Our World in Data (FAO Forest Resources Assessment)",
            url="https://ourworldindata.org/grapher/annual-deforestation",
            description="Global net forest loss per year, from FAO's 5-yearly Forest Resources Assessment.",
        )
        owid_red_list = await _get_or_create_source(
            session,
            name="Red List Index",
            organization="Our World in Data (IUCN)",
            url="https://ourworldindata.org/grapher/red-list-index",
            description="IUCN Red List Index of species survival; 1.0 means no species are expected to go extinct in the near future.",
        )
        owid_pm25 = await _get_or_create_source(
            session,
            name="Population-Weighted PM2.5 Exposure",
            organization="Our World in Data (Health Effects Institute, State of Global Air)",
            url="https://ourworldindata.org/grapher/pm25-air-pollution",
            description="Global population-weighted average exposure to ambient fine particulate matter (PM2.5).",
        )
        owid_lpi = await _get_or_create_source(
            session,
            name="LPI 2026. Living Planet Index database. <www.livingplanetindex.org/>",
            organization="Zoological Society of London (ZSL) & WWF International",
            url="https://www.livingplanetindex.org/",
            description=(
                "Global index tracking the abundance of thousands of monitored vertebrate populations, indexed to 100 in 1970. "
                "Values sourced via Our World in Data (https://ourworldindata.org/grapher/global-living-planet-index). "
                "The published global/regional/system LPI trends are licensed CC BY-SA 4.0 by ZSL/WWF (the underlying "
                "species-level dataset is not reproduced here) - see https://livingplanetindex.org/documents/data_agreement.pdf. "
                "Any further redistribution of this data should carry the same CC BY-SA 4.0 terms."
            ),
        )
        owid_water_stress = await _get_or_create_source(
            session,
            name="Freshwater Withdrawal as Share of Internal Resources (SDG 6.4.2)",
            organization="Our World in Data (UN SDG Indicator 6.4.2)",
            url="https://ourworldindata.org/grapher/freshwater-withdrawals-as-a-share-of-internal-resources",
            description="Global freshwater withdrawn as a percentage of total available internal renewable freshwater resources. The global aggregate masks much more severe stress in specific regions and countries.",
        )
        # Not a data_sources row: this is a one-off status-caveat citation on
        # a single metric, not a reading source shared across many rows (see
        # migration 009's comment for why that's a plain URL, not a FK).
        GRACE_FRESHWATER_DECLINE_NAME = "Rodell et al. 2025, Science Advances (NASA GRACE)"
        GRACE_FRESHWATER_DECLINE_URL = "https://www.science.org/doi/10.1126/sciadv.adx0298"
        hot_ocean_ph = await _get_or_create_source(
            session,
            name="Hawaii Ocean Time-series (HOT), Station ALOHA",
            organization="University of Hawai'i at Manoa / NSF",
            url="https://hahana.soest.hawaii.edu/hot/hot-dogs/",
            description="Surface ocean pH (Total Scale) from monthly sampling at Station ALOHA in the Pacific since October 1988.",
        )
        gcrmn_coral = await _get_or_create_source(
            session,
            name="Status of Coral Reefs of the World: 2020 (GCRMN)",
            organization="Global Coral Reef Monitoring Network / ICRI / UNEP",
            url="https://gcrmn.net/2020-report/",
            description="Global average hard coral cover by assessment epoch (1978-2019 dataset), synthesized from over 300 contributing institutions and thousands of reef sites.",
        )
        jambeck_plastic = await _get_or_create_source(
            session,
            name="Jambeck et al. 2015, Plastic waste inputs from land into the ocean",
            organization="Science (journal), DOI 10.1126/science.1260352",
            url="https://doi.org/10.1126/science.1260352",
            description="Modeled estimate of mismanaged coastal plastic waste entering the ocean, single assessment year (2010). Not a repeated time series.",
        )

        co2_metric = await _upsert_metric(
            session,
            id="co2-level",
            category="Atmosphere & Climate",
            name="Carbon Dioxide Level",
            simplified_name="Climate Balance",
            icon="\U0001F4A8",
            unit="ppm",
            target_value=350,
            target_description="Safe level is 350 ppm",
            description="CO₂ concentration is a core metric for climate change, directly affecting global temperatures and ocean acidification.",
            action_info="Reduce carbon emissions through renewable energy, sustainable transportation, and carbon capture technologies.",
            higher_is_worse=True,
            warning_threshold=350,
            critical_threshold=400,
            display_order=1,
        )
        temp_metric = await _upsert_metric(
            session,
            id="global-temp",
            category="Atmosphere & Climate",
            name="Global Temperature Anomaly",
            simplified_name="Global Fever",
            icon="\U0001F321️",
            unit="°C",
            target_value=1.5,
            target_description="Paris Agreement goal: below +1.5°C",
            description="Measures how much warmer the planet is compared to the pre-industrial (1951-1980) baseline.",
            action_info="Support climate policies, reduce personal carbon footprint, and advocate for systemic change.",
            higher_is_worse=True,
            warning_threshold=1.0,
            critical_threshold=1.5,
            display_order=2,
        )

        methane_metric = await _upsert_metric(
            session,
            id="methane-level",
            category="Atmosphere & Climate",
            name="Methane Concentration",
            simplified_name="Methane Level",
            icon="\U0001F525",
            unit="ppb",
            target_value=1750,
            target_description="Pre-industrial level ~750 ppb",
            description="Methane is a potent greenhouse gas, 25-80x more powerful than CO₂ over 20 years. Rising levels accelerate global warming.",
            action_info="Reduce livestock emissions, prevent methane leaks from oil/gas operations, and support regenerative agriculture.",
            higher_is_worse=True,
            warning_threshold=1750,
            critical_threshold=1900,
            display_order=3,
        )
        sea_level_metric = await _upsert_metric(
            session,
            id="sea-level",
            category="Oceans",
            name="Global Mean Sea Level",
            simplified_name="Sea Level",
            icon="\U0001F4C8",
            unit="mm vs. 1993-2008 avg",
            target_value=0,
            target_description="Stabilize relative to the 1993-2008 average",
            description="Cumulative global mean sea level change from tide gauges and satellites, threatening coastal communities and ecosystems as it rises.",
            action_info="Address climate change root causes and support coastal adaptation strategies.",
            higher_is_worse=True,
            warning_threshold=50,
            critical_threshold=150,
            display_order=6,
        )
        ocean_ph_metric = await _upsert_metric(
            session,
            id="ocean-ph",
            category="Oceans",
            name="Ocean pH Level",
            simplified_name="Ocean Acidity",
            icon="\U0001F30A",
            unit="pH",
            target_value=8.2,
            target_description="Pre-industrial pH was ~8.2",
            description="Surface ocean pH from the Hawaii Ocean Time-series at Station ALOHA. Falling pH means more acidic oceans, harming marine life and coral reefs.",
            action_info="Reduce CO₂ emissions, protect marine ecosystems, and support ocean conservation efforts.",
            higher_is_worse=False,
            # Pre-industrial was ~8.2. Today's ~8.05 already represents a real,
            # documented ~30% rise in ocean acidity (NOAA/IPCC), harming
            # calcifying marine life - so it's treated as already in warning
            # territory rather than "good", with critical reserved for the
            # 7.8-7.9 range where severe/widespread ecosystem effects are
            # discussed in the literature.
            warning_threshold=8.15,
            critical_threshold=8.0,
            display_order=5,
        )
        coral_metric = await _upsert_metric(
            session,
            id="coral-reefs",
            category="Oceans",
            name="Coral Reef Health",
            simplified_name="Coral Health",
            icon="\U0001FAB8",
            unit="% hard coral cover",
            target_value=32,
            target_description="Restore to pre-1998 bleaching baseline (~30-32%)",
            description="Global average hard coral cover from GCRMN epoch assessments. Coral reefs support 25% of marine life; warming waters and acidification cause mass bleaching.",
            action_info="Reduce emissions, prevent coastal pollution, support reef restoration projects, and use reef-safe sunscreen.",
            higher_is_worse=False,
            warning_threshold=30,
            critical_threshold=25,
            display_order=7,
        )
        ocean_plastic_metric = await _upsert_metric(
            session,
            id="ocean-plastic",
            category="Oceans",
            name="Ocean Plastic Pollution",
            simplified_name="Ocean Plastic",
            icon="♻️",
            unit="million metric tons/year",
            target_value=0,
            target_description="Zero plastic entering oceans",
            description="Modeled estimate (Jambeck et al. 2015) of mismanaged coastal plastic waste entering the ocean. No continuous time series exists - published studies use incompatible methodologies, so this is a single cited estimate rather than a trend.",
            action_info="Reduce single-use plastics, support cleanup efforts, improve waste management, and advocate for plastic regulations.",
            higher_is_worse=True,
            warning_threshold=5,
            critical_threshold=10,
            display_order=8,
        )
        renewable_metric = await _upsert_metric(
            session,
            id="renewable-energy",
            category="Pollution & Resources",
            name="Renewable Electricity Share",
            simplified_name="Clean Energy",
            icon="⚡",
            unit="% of global electricity",
            target_value=100,
            target_description="100% renewable electricity",
            description="Share of the world's electricity generated from renewable sources. Transitioning to renewables is essential for reducing emissions.",
            action_info="Support renewable energy policies, install solar panels, choose green energy providers, and invest in clean tech.",
            higher_is_worse=False,
            warning_threshold=50,
            critical_threshold=25,
            display_order=14,
        )
        arctic_ice_metric = await _upsert_metric(
            session,
            id="arctic-ice",
            category="Atmosphere & Climate",
            name="Arctic Sea Ice Minimum Extent",
            simplified_name="Arctic Ice",
            icon="\U0001F9CA",
            unit="million km²",
            target_value=7.0,
            target_description="1979-2000 average minimum was ~7 million km²",
            description="Annual summer minimum Arctic sea ice extent. Arctic ice reflects sunlight and regulates global climate; rapid decline accelerates warming.",
            action_info="Address root causes of climate change, support Arctic conservation, and reduce black carbon emissions.",
            higher_is_worse=False,
            warning_threshold=5.5,
            critical_threshold=4.0,
            display_order=4,
        )
        deforestation_metric = await _upsert_metric(
            session,
            id="forest-cover",
            category="Land & Forests",
            name="Net Deforestation",
            simplified_name="Forest Cover",
            icon="\U0001F333",
            unit="million hectares/year",
            target_value=0,
            target_description="Net zero deforestation",
            description="Global net forest loss per year (FAO 5-yearly assessment), impacting biodiversity, carbon sequestration, and indigenous communities.",
            action_info="Support reforestation projects, sustainable forestry, and reduce consumption of deforestation-linked products.",
            higher_is_worse=True,
            warning_threshold=5,
            critical_threshold=10,
            display_order=9,
        )
        red_list_metric = await _upsert_metric(
            session,
            id="extinction-risk",
            category="Biodiversity",
            name="IUCN Red List Index",
            # "Extinction Risk" as a headline paired with a number like 0.75
            # reads as "75% risk, bad" - but higher is actually safer here
            # (1.0 = no species expected to go extinct). Renamed so the
            # headline's direction matches the number's direction.
            simplified_name="Species Safety",
            icon="\U0001F98F",
            unit="index (0-1)",
            target_value=1.0,
            target_description="1 = no species threatened",
            description="Tracks how safe assessed species groups are from extinction (IUCN Red List Index). A value of 1 means no species are expected to go extinct in the near future.",
            action_info="Support biodiversity conservation, protect endangered species, and advocate for habitat preservation.",
            higher_is_worse=False,
            warning_threshold=0.8,
            critical_threshold=0.6,
            display_order=12,
        )
        pm25_metric = await _upsert_metric(
            session,
            id="air-quality",
            category="Pollution & Resources",
            name="Global Air Quality (PM2.5)",
            simplified_name="Air Quality",
            icon="\U0001F4A8",
            unit="µg/m³ PM2.5",
            target_value=10,
            target_description="WHO guideline: 10 µg/m³",
            description="Population-weighted average exposure to fine particulate matter. PM2.5 penetrates deep into lungs, causing respiratory disease.",
            action_info="Reduce fossil fuel use, support clean energy, improve public transit, and enforce emission standards.",
            higher_is_worse=True,
            warning_threshold=15,
            critical_threshold=25,
            display_order=13,
        )

        lpi_metric = await _upsert_metric(
            session,
            id="wildlife-health",
            category="Biodiversity",
            name="Living Planet Index",
            simplified_name="Wildlife Health",
            icon="\U0001F43E",
            unit="index (1970=100)",
            target_value=100,
            target_description="Halt decline (return to 1970 baseline)",
            description="Tracks the abundance of thousands of monitored vertebrate populations globally, indexed to 100 in 1970.",
            action_info="Protect habitats, combat poaching, support conservation organizations, and reduce pollution.",
            higher_is_worse=False,
            warning_threshold=50,
            critical_threshold=30,
            display_order=11,
        )
        water_stress_metric = await _upsert_metric(
            session,
            id="freshwater",
            category="Land & Forests",
            name="Freshwater Withdrawal Stress",
            simplified_name="Fresh Water",
            icon="\U0001F4A7",
            unit="% of available resources withdrawn",
            target_value=25,
            target_description="Below 25% is considered water-secure (UN SDG 6.4.2 threshold)",
            description="Global freshwater withdrawn as a share of available renewable resources (UN SDG 6.4.2). The global average is moderate, but masks severe water stress in specific regions.",
            action_info="Conserve water, support sustainable water management, and protect watersheds.",
            higher_is_worse=True,
            warning_threshold=25,
            critical_threshold=50,
            display_order=10,
            # SDG 6.4.2 compares withdrawal against a fixed historical-average
            # renewable-flow baseline, so it can't see stock depletion
            # (groundwater mined faster than it recharges). NASA GRACE
            # satellite data shows real freshwater storage is declining
            # rapidly worldwide even though this ratio reads as moderate -
            # floor the badge at "warning" and cite why.
            status_override='warning',
            status_caveat=(
                "This ratio can look moderate even as real freshwater is disappearing: it compares withdrawal "
                "against a fixed historical-average renewable-flow baseline, not actual current availability, so "
                "it can't see groundwater being mined faster than it recharges. NASA satellite data shows global "
                "freshwater storage has been declining rapidly since 2002, with about 75% of the world's population "
                "living in areas of continuous freshwater decline."
            ),
            status_caveat_source_name=GRACE_FRESHWATER_DECLINE_NAME,
            status_caveat_source_url=GRACE_FRESHWATER_DECLINE_URL,
        )

        co2_added = await _upsert_readings(session, co2_metric.id, noaa_co2.id, CO2_ANNUAL_MEAN_PPM)
        temp_added = await _upsert_readings(session, temp_metric.id, nasa_gistemp.id, GLOBAL_TEMP_ANOMALY_C)
        methane_added = await _upsert_readings(session, methane_metric.id, noaa_ch4.id, METHANE_ANNUAL_MEAN_PPB)
        sea_level_added = await _upsert_readings(session, sea_level_metric.id, owid_sea_level.id, SEA_LEVEL_MM)
        renewable_added = await _upsert_readings(session, renewable_metric.id, owid_renewables.id, RENEWABLE_ELECTRICITY_SHARE_PCT)
        arctic_ice_added = await _upsert_readings(session, arctic_ice_metric.id, owid_arctic_ice.id, ARCTIC_ICE_MIN_EXTENT_MKM2)
        deforestation_added = await _upsert_readings(session, deforestation_metric.id, owid_deforestation.id, DEFORESTATION_M_HA_PER_YEAR)
        red_list_added = await _upsert_readings(session, red_list_metric.id, owid_red_list.id, RED_LIST_INDEX)
        pm25_added = await _upsert_readings(session, pm25_metric.id, owid_pm25.id, PM25_UGM3)
        lpi_added = await _upsert_readings(session, lpi_metric.id, owid_lpi.id, LIVING_PLANET_INDEX)
        water_stress_added = await _upsert_readings(session, water_stress_metric.id, owid_water_stress.id, WATER_STRESS_PCT)
        ocean_ph_added = await _upsert_readings(session, ocean_ph_metric.id, hot_ocean_ph.id, OCEAN_PH)
        coral_added = await _upsert_readings(session, coral_metric.id, gcrmn_coral.id, CORAL_COVER_PCT)
        ocean_plastic_added = await _upsert_readings(session, ocean_plastic_metric.id, jambeck_plastic.id, OCEAN_PLASTIC_MMT_PER_YEAR)

        await session.commit()
        print(f"CO2: {co2_added} new readings added ({len(CO2_ANNUAL_MEAN_PPM)} total years)")
        print(f"Global temp anomaly: {temp_added} new readings added ({len(GLOBAL_TEMP_ANOMALY_C)} total years)")
        print(f"Methane: {methane_added} new readings added ({len(METHANE_ANNUAL_MEAN_PPB)} total years)")
        print(f"Sea level: {sea_level_added} new readings added ({len(SEA_LEVEL_MM)} total years)")
        print(f"Renewable electricity: {renewable_added} new readings added ({len(RENEWABLE_ELECTRICITY_SHARE_PCT)} total years)")
        print(f"Arctic ice: {arctic_ice_added} new readings added ({len(ARCTIC_ICE_MIN_EXTENT_MKM2)} total years)")
        print(f"Deforestation: {deforestation_added} new readings added ({len(DEFORESTATION_M_HA_PER_YEAR)} total years)")
        print(f"Red List Index: {red_list_added} new readings added ({len(RED_LIST_INDEX)} total years)")
        print(f"PM2.5: {pm25_added} new readings added ({len(PM25_UGM3)} total years)")
        print(f"Living Planet Index: {lpi_added} new readings added ({len(LIVING_PLANET_INDEX)} total years)")
        print(f"Water stress: {water_stress_added} new readings added ({len(WATER_STRESS_PCT)} total years)")
        print(f"Ocean pH: {ocean_ph_added} new readings added ({len(OCEAN_PH)} total years)")
        print(f"Coral cover: {coral_added} new readings added ({len(CORAL_COVER_PCT)} total years)")
        print(f"Ocean plastic: {ocean_plastic_added} new readings added ({len(OCEAN_PLASTIC_MMT_PER_YEAR)} total years)")


if __name__ == "__main__":
    asyncio.run(seed())
