# backend/scripts/generate_instances_batch.py
# Creates different sized instance files for testing

import pandas as pd
from rdflib import Graph, Namespace, Literal, RDF, URIRef
from rdflib.namespace import XSD
import os

BASE = os.path.dirname(os.path.dirname(__file__))
CSV_PATH = os.path.join(BASE, "data", "kbs_2024.csv")
OUT_DIR = os.path.join(BASE, "ontology")
NS = "http://example.org/smart-farming#"
sf = Namespace(NS)

df = pd.read_csv(CSV_PATH, sep=",", dtype=str).fillna("")

# Create different sized files
sizes = [
    (5, "tiny"),      # 5 rows - 5 seconds
    (20, "small"),    # 20 rows - 10 seconds
    (100, "medium"),  # 100 rows - 30 seconds
    (500, "large"),   # 500 rows - 2 minutes
]

def create_instances(data, size_name):
    """Create instance file from data"""
    g = Graph()
    g.bind("sf", sf)
    g.bind("xsd", XSD)
    
    crops_created = set()
    
    for idx, row in data.iterrows():
        year = row["Year"].strip()
        plot = row["PlotID"].strip().replace(" ", "_")
        
        # Create YieldRecord
        rec_id = f"YieldRecord_{plot}_{year}_{idx}"
        rec = URIRef(NS + rec_id)
        g.add((rec, RDF.type, sf.YieldRecord))
        
        # Create Plot
        plot_uri = URIRef(NS + plot)
        g.add((plot_uri, RDF.type, sf.Plot))
        g.add((rec, sf.aboutPlot, plot_uri))
        
        # Create Crop with hasCropName
        crop_name = row["Crop"].strip() or "UnknownCrop"
        crop_label = crop_name.replace(" ", "_").replace(".", "")
        crop_uri = URIRef(NS + crop_label)
        
        if crop_label not in crops_created:
            g.add((crop_uri, RDF.type, sf.Crop))
            g.add((crop_uri, sf.hasCropName, Literal(crop_name, datatype=XSD.string)))
            crops_created.add(crop_label)
        
        g.add((rec, sf.forCrop, crop_uri))
        g.add((rec, sf.hasYear, Literal(year, datatype=XSD.gYear)))
        
        # Yield
        yld = row.get("Yield_kg_ha", "")
        if yld != "":
            try:
                g.add((rec, sf.yield_kg_per_ha, Literal(float(yld), datatype=XSD.float)))
            except (ValueError, TypeError):
                pass
        
        # SoilMeasurement
        soil_id = f"SoilMeasurement_{plot}_{year}_{idx}"
        soil = URIRef(NS + soil_id)
        g.add((soil, RDF.type, sf.SoilMeasurement))
        g.add((soil, sf.aboutPlot, plot_uri))
        g.add((soil, sf.hasYear, Literal(year, datatype=XSD.gYear)))
        
        # Soil properties
        for col, pred in [
            ("Soil_pH", "soil_pH"),
            ("P", "soil_P_mg_per_kg"),
            ("K", "soil_K_mg_per_kg"),
        ]:
            if col in row and row[col] != "":
                try:
                    g.add((soil, sf[pred], Literal(float(row[col]), datatype=XSD.float)))
                except (ValueError, TypeError):
                    pass
        
        g.add((rec, sf.usesSoilMeasurement, soil))
    
    return g, len(crops_created)

def get_expected_time(rows):
    if rows <= 10:
        return "5-10 seconds"
    elif rows <= 50:
        return "15-30 seconds"
    elif rows <= 200:
        return "30-60 seconds"
    else:
        return "1-3 minutes"

print("="*70)
print("GENERATING BATCH INSTANCE FILES")
print("="*70)

for row_count, size_name in sizes:
    data_subset = df.head(row_count)
    g, crop_count = create_instances(data_subset, size_name)
    
    # Save as RDF/XML for owlready2 compatibility
    output_file = os.path.join(OUT_DIR, f"instances_{size_name}.owl")
    g.serialize(destination=output_file, format="xml")
    
    print(f"\n✓ {size_name.upper():8} ({row_count:3} rows)")
    print(f"  File: instances_{size_name}.owl")
    print(f"  Triples: {len(g)}")
    print(f"  Crops: {crop_count}")
    print(f"  Expected reasoning time: {get_expected_time(row_count)}")

print("\n" + "="*70)
print("TESTING INSTRUCTIONS:")
print("="*70)
print("1. Start with: instances_tiny.ttl (fastest)")
print("2. Load in Protégé and test SWRL rule")
print("3. If works, move to: instances_small.ttl")
print("4. Continue until you find the size that works")
print("="*70)