"""
Seed script for the Earth Health Dashboard: cited data sources, the first
two real metrics (CO2 and global temperature anomaly), and their full
historical reading series.

This proves out the earth_metrics pipeline end to end before backfilling
the rest of the dashboard's metrics. Run again any time to append newer
years - it's idempotent (upserts by id / (metric_id, reading_date)).

Sources:
- NOAA Global Monitoring Laboratory, Mauna Loa Observatory annual mean CO2
  (1959-present, instrumental record): https://gml.noaa.gov/ccgg/trends/
- NASA GISS Surface Temperature Analysis v4 (GISTEMP), global annual mean
  land-ocean temperature anomaly vs. the 1951-1980 baseline (1880-present):
  https://data.giss.nasa.gov/gistemp/

Note: CO2 before 1959 (pre-instrumental) is available from ice-core
reconstructions (e.g. Law Dome), but isn't seeded here yet - the exact
figures need to be pulled from the primary data file directly rather than
a secondhand summary, to keep this a reliable source. Follow-up work.
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
        select(EarthMetricReading.reading_date).where(EarthMetricReading.metric_id == metric_id)
    )
    existing_dates = {row[0] for row in result.all()}

    added = 0
    for year, value in annual_values.items():
        reading_date = date(year, month, day)
        if reading_date in existing_dates:
            continue
        session.add(EarthMetricReading(
            metric_id=metric_id,
            reading_date=reading_date,
            value=value,
            source_id=source_id,
        ))
        added += 1
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

        co2_added = await _upsert_readings(session, co2_metric.id, noaa_co2.id, CO2_ANNUAL_MEAN_PPM)
        temp_added = await _upsert_readings(session, temp_metric.id, nasa_gistemp.id, GLOBAL_TEMP_ANOMALY_C)

        await session.commit()
        print(f"CO2: {co2_added} new readings added ({len(CO2_ANNUAL_MEAN_PPM)} total years)")
        print(f"Global temp anomaly: {temp_added} new readings added ({len(GLOBAL_TEMP_ANOMALY_C)} total years)")


if __name__ == "__main__":
    asyncio.run(seed())
