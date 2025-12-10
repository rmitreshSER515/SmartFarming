#!/usr/bin/env python3
"""
Generate instances (TTL) from the smart-farming OWL schema and kbs_2024.csv.

"""

import csv
import re
from pathlib import Path

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD


# -------------------------------------------------------------------
# Paths & config
# -------------------------------------------------------------------

SCRIPTS_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS_DIR.parent  # ../backend

OWL_PATH = PROJECT_ROOT / "ontology" / "smart-farming.owl"
CSV_PATH = PROJECT_ROOT / "data" / "kbs_2024.csv"
OUTPUT_TTL = PROJECT_ROOT / "ontology" / "instances.ttl"

BASE_URI = "http://example.org/smart-farming#"
SF = Namespace(BASE_URI)


# -------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------

def slugify(value: str) -> str:
    """Generate a safe URI fragment: lowercase, alnum + underscore."""
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "unnamed"


def to_float(val: str):
    if val is None:
        return None
    val = val.strip()
    if not val:
        return None
    try:
        return float(val)
    except ValueError:
        return None


def to_bool_from_01(val: str):
    if val is None:
        return None
    val = val.strip()
    if not val:
        return None
    if val in {"1", "true", "True"}:
        return True
    if val in {"0", "false", "False"}:
        return False
    return None


# -------------------------------------------------------------------
# Load ontology
# -------------------------------------------------------------------

if not OWL_PATH.exists():
    raise FileNotFoundError(f"OWL file not found at {OWL_PATH}")

if not CSV_PATH.exists():
    raise FileNotFoundError(f"CSV file not found at {CSV_PATH}")

g = Graph()
g.parse(OWL_PATH, format="xml")

# Bind prefixes for nicer TTL
g.bind("sf", SF)
g.bind("", SF)


# -------------------------------------------------------------------
# Registries to avoid duplicate individuals
# -------------------------------------------------------------------

plots = {}       # PlotID -> URIRef
crops = {}       # crop name -> URIRef
treatments = {}  # treatment code -> URIRef


def get_plot(plot_id: str) -> URIRef:
    """Return (and create if needed) a Plot individual for PlotID."""
    if plot_id in plots:
        return plots[plot_id]
    uri = SF[plot_id]
    g.add((uri, RDF.type, SF.Plot))
    g.add((uri, SF.hasPlotID, Literal(plot_id, datatype=XSD.string)))
    plots[plot_id] = uri
    return uri


def get_crop(crop_name: str) -> URIRef:
    """Return (and create if needed) a Crop individual based on crop name."""
    if crop_name in crops:
        return crops[crop_name]

    slug = "crop_" + slugify(crop_name)
    uri = SF[slug]
    g.add((uri, RDF.type, SF.Crop))
    g.add((uri, SF.hasCropName, Literal(crop_name, datatype=XSD.string)))
    crops[crop_name] = uri
    return uri


def get_treatment(treatment_code: str) -> URIRef:
    """Return (and create if needed) a Treatment individual based on code."""
    if treatment_code in treatments:
        return treatments[treatment_code]

    slug = "treatment_" + slugify(treatment_code)
    uri = SF[slug]
    g.add((uri, RDF.type, SF.Treatment))
    g.add((uri, RDFS.label, Literal(treatment_code, datatype=XSD.string)))
    treatments[treatment_code] = uri
    return uri


# -------------------------------------------------------------------
# Process CSV -> instances
# -------------------------------------------------------------------

with CSV_PATH.open(newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)  # default delimiter=","
    for idx, row in enumerate(reader, start=1):
        year = (row.get("Year") or "").strip()
        plot_id = (row.get("PlotID") or "").strip()
        treatment_code = (row.get("Treatment") or "").strip()
        replicate = (row.get("Replicate") or "").strip()
        crop_name = (row.get("Crop") or "").strip()

        if not year or not plot_id:
            print(f"Skipping row {idx}: missing Year or PlotID")
            continue

        plot_uri = get_plot(plot_id)
        crop_uri = get_crop(crop_name) if crop_name else None
        treatment_uri = get_treatment(treatment_code) if treatment_code else None

        # ----------------------------------------------------------------
        # YieldRecord individual
        # ----------------------------------------------------------------
        yr_slug = f"yield_{year}_{plot_id}_{replicate or 'no_rep'}"
        yr_uri = SF[slugify(yr_slug)]

        g.add((yr_uri, RDF.type, SF.YieldRecord))
        g.add((yr_uri, SF.aboutPlot, plot_uri))
        if crop_uri:
            g.add((yr_uri, SF.forCrop, crop_uri))
        if treatment_uri:
            g.add((yr_uri, SF.withTreatment, treatment_uri))
        if year:
            g.add((yr_uri, SF.hasYear, Literal(year, datatype=XSD.gYear)))
        if replicate:
            g.add((yr_uri, SF.hasReplicate, Literal(replicate, datatype=XSD.string)))

        yld = to_float(row.get("Yield_kg_ha"))
        if yld is not None:
            g.add((yr_uri, SF.yield_kg_per_ha, Literal(yld, datatype=XSD.float)))

        # ----------------------------------------------------------------
        # SoilMeasurement individual
        # ----------------------------------------------------------------
        sm_slug = f"soil_{year}_{plot_id}_{replicate or 'no_rep'}"
        sm_uri = SF[slugify(sm_slug)]

        g.add((sm_uri, RDF.type, SF.SoilMeasurement))
        g.add((sm_uri, SF.aboutPlot, plot_uri))
        if crop_uri:
            g.add((sm_uri, SF.forCrop, crop_uri))
        if year:
            g.add((sm_uri, SF.hasYear, Literal(year, datatype=XSD.gYear)))
        if replicate:
            g.add((sm_uri, SF.hasReplicate, Literal(replicate, datatype=XSD.string)))

        # Soil properties
        val = to_float(row.get("Soil_pH"))
        if val is not None:
            g.add((sm_uri, SF.soil_pH, Literal(val, datatype=XSD.float)))

        val = to_float(row.get("P"))
        if val is not None:
            g.add((sm_uri, SF.soil_P_mg_per_kg, Literal(val, datatype=XSD.float)))

        val = to_float(row.get("K"))
        if val is not None:
            g.add((sm_uri, SF.soil_K_mg_per_kg, Literal(val, datatype=XSD.float)))

        val = to_float(row.get("Ca"))
        if val is not None:
            g.add((sm_uri, SF.soil_Ca_mg_per_kg, Literal(val, datatype=XSD.float)))

        val = to_float(row.get("Mg"))
        if val is not None:
            g.add((sm_uri, SF.soil_Mg_mg_per_kg, Literal(val, datatype=XSD.float)))

        val = to_float(row.get("CEC"))
        if val is not None:
            g.add((sm_uri, SF.soil_CEC, Literal(val, datatype=XSD.float)))

        val = to_float(row.get("OM"))
        if val is not None:
            g.add((sm_uri, SF.soil_OM_pct, Literal(val, datatype=XSD.float)))

        sm_flag = to_bool_from_01(row.get("Soil_Measured"))
        if sm_flag is not None:
            g.add((sm_uri, SF.soilMeasured, Literal(sm_flag, datatype=XSD.boolean)))

        # ----------------------------------------------------------------
        # WeatherSummary individual
        # ----------------------------------------------------------------
        ws_slug = f"weather_{year}_{plot_id}_{replicate or 'no_rep'}"
        ws_uri = SF[slugify(ws_slug)]

        g.add((ws_uri, RDF.type, SF.WeatherSummary))
        g.add((ws_uri, SF.aboutPlot, plot_uri))
        if crop_uri:
            g.add((ws_uri, SF.forCrop, crop_uri))
        if year:
            g.add((ws_uri, SF.hasYear, Literal(year, datatype=XSD.gYear)))
        if replicate:
            g.add((ws_uri, SF.hasReplicate, Literal(replicate, datatype=XSD.string)))

        val = to_float(row.get("TotalPrecip_mm"))
        if val is not None:
            g.add((ws_uri, SF.totalPrecip_mm, Literal(val, datatype=XSD.float)))

        val = to_float(row.get("AvgTmax_C"))
        if val is not None:
            g.add((ws_uri, SF.avgTmax_C, Literal(val, datatype=XSD.float)))

        val = to_float(row.get("AvgTmin_C"))
        if val is not None:
            g.add((ws_uri, SF.avgTmin_C, Literal(val, datatype=XSD.float)))

# -------------------------------------------------------------------
# Serialize
# -------------------------------------------------------------------

OUTPUT_TTL.parent.mkdir(parents=True, exist_ok=True)
g.serialize(destination=str(OUTPUT_TTL), format="turtle")
print(f"Wrote instances to {OUTPUT_TTL}")
