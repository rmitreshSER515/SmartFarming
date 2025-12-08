# backend/scripts/generate_instances.py
import pandas as pd
from rdflib import Graph, Namespace, Literal, RDF, URIRef
from rdflib.namespace import XSD
import os

BASE = os.path.dirname(os.path.dirname(__file__))
CSV_PATH = os.path.join(BASE, "data", "kbs_2024.csv")
OUT_TTL = os.path.join(BASE, "ontology", "instances.ttl")
NS = "http://example.org/smart-farming#"
sf = Namespace(NS)

df = pd.read_csv(CSV_PATH, sep=",", dtype=str).fillna("")

g = Graph()
g.bind("sf", sf)
g.bind("xsd", XSD)

for idx, row in df.iterrows():
    year = row["Year"].strip()
    plot = row["PlotID"].strip().replace(" ", "_")
    rec_id = f"YieldRecord_{plot}_{year}_{idx}"
    rec = URIRef(NS + rec_id)
    g.add((rec, RDF.type, sf.YieldRecord))

    plot_uri = URIRef(NS + plot)
    g.add((plot_uri, RDF.type, sf.Plot))
    g.add((rec, sf.aboutPlot, plot_uri))

    crop_name = row["Crop"].strip() or "UnknownCrop"
    crop_label = crop_name.replace(" ", "_")
    crop_uri = URIRef(NS + crop_label)
    g.add((crop_uri, RDF.type, sf.Crop))
    # Add a data property with crop name for SWRL string checks
    g.add((crop_uri, sf.hasCropName, Literal(crop_name)))

    g.add((rec, sf.forCrop, crop_uri))

    # year
    g.add((rec, sf.hasYear, Literal(year, datatype=XSD.gYear)))

    # yield
    yld = row.get("Yield_kg_ha", "")
    if yld != "":
        try:
            g.add((rec, sf.yield_kg_per_ha, Literal(float(yld), datatype=XSD.float)))
        except (ValueError, TypeError):
            g.add((rec, sf.yield_kg_per_ha, Literal(yld)))

    # soil measurement
    soil_id = f"SoilMeasurement_{plot}_{year}_{idx}"
    soil = URIRef(NS + soil_id)
    g.add((soil, RDF.type, sf.SoilMeasurement))
    g.add((soil, sf.aboutPlot, plot_uri))
    g.add((soil, sf.hasYear, Literal(year, datatype=XSD.gYear)))
    for col, pred in [
        ("Soil_pH", "soil_pH"),
        ("P", "soil_P_mg_per_kg"),
        ("K", "soil_K_mg_per_kg"),
        ("Ca", "soil_Ca_mg_per_kg"),
        ("Mg", "soil_Mg_mg_per_kg"),
        ("CEC", "soil_CEC"),
        ("OM", "soil_OM_pct")
    ]:
        if col in row and row[col] != "":
            try:
                g.add((soil, sf[pred], Literal(float(row[col]), datatype=XSD.float)))
            except (ValueError, TypeError):
                g.add((soil, sf[pred], Literal(row[col])))

    g.add((rec, sf.usesSoilMeasurement, soil))

    # weather summary
    weather_id = f"Weather_{plot}_{year}_{idx}"
    w = URIRef(NS + weather_id)
    g.add((w, RDF.type, sf.WeatherSummary))
    g.add((w, sf.aboutPlot, plot_uri))
    if "TotalPrecip_mm" in row and row["TotalPrecip_mm"] != "":
        try:
            g.add((w, sf.forecastRainfallAmount_mm, Literal(float(row[
                "TotalPrecip_mm"]), datatype=XSD.float)))
        except (ValueError, TypeError):
            g.add((w, sf.forecastRainfallAmount_mm, Literal(row[
                "TotalPrecip_mm"])))
    g.add((rec, sf.usesWeatherSummary, w))

# serialize to TTL
g.serialize(destination=OUT_TTL, format="turtle")
print("Wrote:", OUT_TTL)