-- Migration: Add a status override + caveat to earth_metrics
--
-- Some indicators can look "fine" by their own official definition while
-- missing a real, well-documented problem measured a different way. UN SDG
-- 6.4.2 (freshwater withdrawal as a % of renewable flow) is the first case:
-- it reads as moderate globally, but NASA GRACE/GRACE-FO satellite
-- gravimetry shows rapid real freshwater storage decline (groundwater
-- depletion especially) that a withdrawal-vs-renewable-flow ratio can't see,
-- since it compares against a fixed historical-average baseline rather than
-- actual current availability.
--
-- Rather than fudge the underlying number or its thresholds (which would
-- misrepresent the cited source's own methodology), this adds an explicit,
-- citable override: the badge can show a stronger status than the raw
-- calculation implies, with a footnote explaining why.
--
-- The caveat's citation is plain text/URL columns rather than a foreign key
-- to data_sources: unlike reading sources (genuinely shared across many
-- rows), a status caveat is a one-off annotation on a single metric, so a
-- relationship would be more machinery than the data warrants.

ALTER TABLE alter_earth.earth_metrics
    ADD COLUMN status_override VARCHAR(20) NULL,
    ADD COLUMN status_caveat TEXT NULL,
    ADD COLUMN status_caveat_source_name VARCHAR(200) NULL,
    ADD COLUMN status_caveat_source_url VARCHAR(1000) NULL;

COMMENT ON COLUMN alter_earth.earth_metrics.status_override IS 'Overrides the threshold-computed status (critical/warning/good) when the underlying indicator is known to understate real-world severity. NULL means use the normal computation.';
COMMENT ON COLUMN alter_earth.earth_metrics.status_caveat IS 'Explanatory footnote shown next to the status badge when status_override is set, citing why the raw computed status is misleading.';
