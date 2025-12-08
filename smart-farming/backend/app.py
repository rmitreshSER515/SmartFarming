# backend/app.py
from flask import Flask, jsonify, send_file
from rdflib import Graph, Namespace
import os

app = Flask(__name__)
BASE = os.path.dirname(__file__)
INFERRED_OWL = os.path.join(BASE, "ontology", "smart-farming.owl")
INSTANCES_TTL = os.path.join(BASE, "ontology", "instances.ttl")
NS = "http://example.org/smart-farming#"

def load_graph():
    g = Graph()
    if os.path.exists(INFERRED_OWL):
        g.parse(INFERRED_OWL)
    else:
        g.parse(INSTANCES_TTL, format="turtle")
    return g


############################################
# API 1: Base Yield + Soil + Weather Data  #
############################################
@app.route("/api/records/<plot>/<year>")
def records(plot, year):
    g = load_graph()

    q = f"""
    PREFIX sf:<{NS}>
    SELECT ?cropName ?yieldVal ?precip ?ph WHERE {{
      ?r a sf:YieldRecord ;
         sf:aboutPlot sf:{plot} ;
         sf:hasYear ?yy ;
         sf:forCrop ?crop .

      FILTER(STR(?yy) = "{year}")

      OPTIONAL {{ ?crop sf:hasCropName ?cropName . }}
      OPTIONAL {{ ?r sf:yield_kg_per_ha ?yieldVal . }}
      OPTIONAL {{ ?r sf:usesWeatherSummary ?w .
                  ?w sf:forecastRainfallAmount_mm ?precip . }}
      OPTIONAL {{ ?r sf:usesSoilMeasurement ?s .
                  ?s sf:soil_pH ?ph . }}
    }}
    """

    results = g.query(q)

    out = []
    for row in results:
        out.append({
            "crop": str(row.cropName) if row.cropName else None,
            "yield_kg_ha": float(row["yieldVal"]) if row["yieldVal"] else None,
            "precip_mm": float(row["precip"]) if row["precip"] else None,
            "soil_pH": float(row["ph"]) if row["ph"] else None,
        })

    return jsonify(out)


##############################################
# API 2: Fertilizer Recommendations          #
##############################################
@app.route("/api/fertilizer/<plot>/<year>")
def fertilizer(plot, year):
    g = load_graph()

    q = f"""
    PREFIX sf:<{NS}>
    SELECT ?action ?just WHERE {{
      ?fr a sf:FertilizerRecommendation ;
          sf:targetsPlot sf:{plot} ;
          sf:forYear ?yy ;
          sf:recommendedFertilizerAction ?action ;
          sf:hasJustificationText ?just .

      FILTER(STR(?yy) = "{year}")
    }}
    """

    results = g.query(q)

    return jsonify([
        {"action": str(row["action"]), "justification": str(row["just"])}
        for row in results
    ])


##############################################
# API 3: Crop Rotation Recommendations       #
##############################################
@app.route("/api/croprot/<plot>/<year>")
def croprot(plot, year):
    g = load_graph()

    q = f"""
    PREFIX sf:<{NS}>
    SELECT ?crop ?just WHERE {{
      ?cr a sf:CropRotationRecommendation ;
          sf:targetsPlot sf:{plot} ;
          sf:forYear ?yy ;
          sf:recommendsCrop ?crop ;
          sf:hasJustificationText ?just .

      FILTER(STR(?yy) = "{year}")
    }}
    """

    results = g.query(q)
    out = []
    for row in results:
        out.append({
            "recommended_crop": str(row["crop"]).split("#")[-1],
            "justification": str(row["just"])
        })
    return jsonify(out)


############################
# Download Reasoned Ontology
############################
@app.route("/api/download_inferred")
def download_inferred():
    if os.path.exists(INFERRED_OWL):
        return send_file(INFERRED_OWL, as_attachment=True)
    return ("No inferred OWL found. Save from Protégé first.", 404)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
