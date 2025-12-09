# backend/scripts/query_service.py

from pathlib import Path
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF

BASE_URI = "http://example.org/smart-farming#"
SF = Namespace(BASE_URI)

BASE_DIR = Path(__file__).resolve().parent.parent

g = Graph()
# Load ontology (schema + rules)
g.parse(BASE_DIR / "ontology" / "smart-farming-backup.owl")
# Load instance data generated from CSV
g.parse(BASE_DIR / "ontology" / "instances.ttl", format="turtle")

g.bind("sf", SF)
g.bind("", SF)


# ---------------------------------------------------------------------
# 1. Plot + year summary (used by the dashboard panel)
# ---------------------------------------------------------------------
def get_plot_year_summary(plot_id: str, year: int):
    """
    Robust version:
    - Pull all yield/soil/weather rows for the plot (ANY year)
    - Filter by year in Python using str(row["y"]) == str(year)
    This avoids rdflib parser issues with gYear / filtering.
    """
    query = f"""
    PREFIX sf:   <{BASE_URI}>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?y ?yield ?soil_pH ?P ?K ?Ca ?Mg ?CEC ?OM
           ?precip ?tmax ?tmin ?cropName ?treatmentCode
    WHERE {{
      ?plot a sf:Plot ;
            sf:hasPlotID "{plot_id}" .

      # Get all yield records for this plot
      ?yr a sf:YieldRecord ;
          sf:aboutPlot ?plot ;
          sf:hasYear ?y ;
          sf:yield_kg_per_ha ?yield .

      OPTIONAL {{
        ?yr sf:forCrop ?crop .
        ?crop sf:hasCropName ?cropName .
      }}

      OPTIONAL {{
        ?yr sf:withTreatment ?treat .
        ?treat rdfs:label ?treatmentCode .
      }}

      # Soil measurements (same plot & year)
      OPTIONAL {{
        ?sm a sf:SoilMeasurement ;
            sf:aboutPlot ?plot ;
            sf:hasYear ?y .

        OPTIONAL {{ ?sm sf:soil_pH           ?soil_pH }}
        OPTIONAL {{ ?sm sf:soil_P_mg_per_kg  ?P }}
        OPTIONAL {{ ?sm sf:soil_K_mg_per_kg  ?K }}
        OPTIONAL {{ ?sm sf:soil_Ca_mg_per_kg ?Ca }}
        OPTIONAL {{ ?sm sf:soil_Mg_mg_per_kg ?Mg }}
        OPTIONAL {{ ?sm sf:soil_CEC          ?CEC }}
        OPTIONAL {{ ?sm sf:soil_OM_pct       ?OM }}
      }}

      # Weather summary (same plot & year)
      OPTIONAL {{
        ?ws a sf:WeatherSummary ;
            sf:aboutPlot ?plot ;
            sf:hasYear ?y .

        OPTIONAL {{ ?ws sf:totalPrecip_mm ?precip }}
        OPTIONAL {{ ?ws sf:avgTmax_C      ?tmax }}
        OPTIONAL {{ ?ws sf:avgTmin_C      ?tmin }}
      }}
    }}
    """

    # Run SPARQL
    try:
        results = list(g.query(query))
    except Exception as e:
        print("ERROR in get_plot_year_summary:", e)
        return None

    # Debug helper: show what years exist for this plot
    print(f"DEBUG: plot={plot_id}, requested year={year}")
    print("Available years in data:", [str(r["y"]) for r in results])

    # Filter by exact year match (string compare)
    chosen = None
    for row in results:
        if str(row["y"]) == str(year):   # ← most robust check
            chosen = row
            break

    if chosen is None:
        print("DEBUG: No exact match found for this plot/year.")
        return None

    # Build output JSON
    row = chosen

    return {
        "plot_id": plot_id,
        "year": year,
        "yield_kg_per_ha": float(row["yield"]) if row["yield"] is not None else None,
        "crop_name": str(row.cropName) if row.cropName is not None else None,
        "treatment": str(row.treatmentCode) if row.treatmentCode is not None else None,
        "soil": {
            "pH": float(row.soil_pH) if row.soil_pH is not None else None,
            "P_mg_per_kg": float(row.P) if row.P is not None else None,
            "K_mg_per_kg": float(row.K) if row.K is not None else None,
            "Ca_mg_per_kg": float(row.Ca) if row.Ca is not None else None,
            "Mg_mg_per_kg": float(row.Mg) if row.Mg is not None else None,
            "CEC": float(row.CEC) if row.CEC is not None else None,
            "OM_pct": float(row.OM) if row.OM is not None else None,
        },
        "weather": {
            "total_precip_mm": float(row.precip) if row.precip is not None else None,
            "avg_tmax_C": float(row.tmax) if row.tmax is not None else None,
            "avg_tmin_C": float(row.tmin) if row.tmin is not None else None,
        },
    }


# ---------------------------------------------------------------------
# 2. Utility: list all plots
# ---------------------------------------------------------------------
def list_plots():
    """Return a simple list of all plot IDs that exist in the KG."""
    query = f"""
    PREFIX sf: <{BASE_URI}>

    SELECT DISTINCT ?pid
    WHERE {{
      ?plot a sf:Plot ;
            sf:hasPlotID ?pid .
    }}
    ORDER BY ?pid
    """
    try:
        results = g.query(query)
    except Exception as e:
        print("ERROR in list_plots:", e)
        return []
    return [str(row.pid) for row in results]


# ---------------------------------------------------------------------
# 3. Needs fertilizer
# ---------------------------------------------------------------------
def get_plots_needing_fertilizer():
    """
    Plots that look nutrient-limited (low yield OR low soil P OR low soil N).
    Returns a list of plot IDs.
    """
    query = """
    PREFIX sf: <http://example.org/smart-farming#>

    SELECT DISTINCT ?pid ?y ?p ?n ?yield
    WHERE {
      ?pl a sf:Plot ;
          sf:hasPlotID ?pid .

      # Any low-yield record on this plot
      OPTIONAL {
        ?yr a sf:YieldRecord ;
            sf:aboutPlot ?pl ;
            sf:yield_kg_per_ha ?yield .
        FILTER (?yield < 1111.0)
      }

      # Any low soil P on this plot
      OPTIONAL {
        ?smP a sf:SoilMeasurement ;
             sf:aboutPlot ?pl ;
             sf:soil_P_mg_per_kg ?p .
        FILTER (?p < 15.0)
      }

      # Any low soil N on this plot
      OPTIONAL {
        ?smN a sf:SoilMeasurement ;
             sf:aboutPlot ?pl ;
             sf:soil_N_mg_per_kg ?n .
        FILTER (?n < 10.0)
      }

      # Require that at least one of these three conditions held
      FILTER(BOUND(?yield) || BOUND(?p) || BOUND(?n))
    }
    ORDER BY ?pid
    """
    try:
        results = g.query(query)
    except Exception as e:
        print("ERROR in get_plots_needing_fertilizer:", e)
        return []

    rows = list(results)
    print("DEBUG needs-fertilizer rows:", len(rows))
    for r in rows[:5]:
        print("  row:", r)

    return sorted({str(row["pid"]) for row in rows})


# ---------------------------------------------------------------------
# 4. Crop lookup (used in frontend but simple)
# ---------------------------------------------------------------------
def get_legume_crops():
    query = """
    PREFIX sf: <http://example.org/smart-farming#>

    SELECT ?crop ?name
    WHERE {
      ?crop a sf:Crop ;
            sf:hasCropName ?name .
      FILTER (lcase(str(?name)) = "glycine max l.")
    }
    ORDER BY ?name
    """
    try:
        results = g.query(query)
    except Exception as e:
        print("ERROR in get_legume_crops:", e)
        return []

    return [
        {"uri": str(row["crop"]), "name": str(row["name"])}
        for row in results
    ]


def get_cereal_crops():
    query = """
    PREFIX sf: <http://example.org/smart-farming#>

    SELECT ?crop ?name
    WHERE {
      ?crop a sf:Crop ;
            sf:hasCropName ?name .
      FILTER (lcase(str(?name)) = "zea mays l.")
    }
    ORDER BY ?name
    """
    try:
        results = g.query(query)
    except Exception as e:
        print("ERROR in get_cereal_crops:", e)
        return []

    return [
        {"uri": str(row["crop"]), "name": str(row["name"])}
        for row in results
    ]


# ---------------------------------------------------------------------
# 5. Postpone fertilizer (deduplicate per plot)
# ---------------------------------------------------------------------
def get_plots_to_postpone_fertilizer():
    """
    Plots where:
      - soil_P_mg_per_kg >= 15
      - forecastRainfallAmount_mm > 650
    joined by aboutPlot.

    We deduplicate by plot_id in Python to avoid massive duplicate rows.
    """
    query = """
    PREFIX sf: <http://example.org/smart-farming#>

    SELECT ?pid ?p ?rain
    WHERE {
      ?sm a sf:SoilMeasurement ;
          sf:soil_P_mg_per_kg ?p ;
          sf:aboutPlot ?pl .

      ?ws a sf:WeatherSummary ;
          sf:forecastRainfallAmount_mm ?rain ;
          sf:aboutPlot ?pl .

      ?pl sf:hasPlotID ?pid .

      FILTER (?p >= 15.0)
      FILTER (?rain > 650.0)
    }
    ORDER BY ?pid
    """
    try:
        results = g.query(query)
    except Exception as e:
        print("ERROR in get_plots_to_postpone_fertilizer:", e)
        return []

    rows = list(results)
    print("DEBUG postpone rows:", len(rows))
    for r in rows[:5]:
        print("  row:", r)

    # Deduplicate per plot; keep the *highest* rain as representative
    per_plot = {}
    for row in rows:
        pid = str(row["pid"])
        p_val = float(row["p"])
        rain_val = float(row["rain"])
        if pid not in per_plot:
            per_plot[pid] = {
                "plot_id": pid,
                "soil_P_mg_per_kg": p_val,
                "forecast_rainfall_mm": rain_val,
            }
        else:
            # Keep the max rainfall; P is pretty constant anyway
            if rain_val > per_plot[pid]["forecast_rainfall_mm"]:
                per_plot[pid]["forecast_rainfall_mm"] = rain_val
                per_plot[pid]["soil_P_mg_per_kg"] = p_val

    return sorted(per_plot.values(), key=lambda d: d["plot_id"])


# ---------------------------------------------------------------------
# 6. High pest risk (simplified, no BIND)
# ---------------------------------------------------------------------
def get_plots_high_pest_risk():
    """
    Define 'high pest risk' heuristically as:
      - crop is Zea mays L. (maize)
      - forecast rainfall is high
      - yield is relatively low
    """
    query = """
    PREFIX sf: <http://example.org/smart-farming#>

    SELECT DISTINCT ?pid ?rain ?y ?name
    WHERE {
      ?pl a sf:Plot ;
          sf:hasPlotID ?pid .

      # Weather: high rainfall
      ?ws a sf:WeatherSummary ;
          sf:aboutPlot ?pl ;
          sf:forecastRainfallAmount_mm ?rain .

      # Yield + crop
      ?yr a sf:YieldRecord ;
          sf:aboutPlot ?pl ;
          sf:yield_kg_per_ha ?y ;
          sf:forCrop ?crop .

      ?crop sf:hasCropName ?name .

      # THRESHOLDS – tweak as needed
      FILTER (?rain > 950.0)
      FILTER (?y < 2500.0)
      FILTER (lcase(str(?name)) = "zea mays l.")
    }
    ORDER BY ?pid ?y
    """
    try:
        results = g.query(query)
    except Exception as e:
        print("ERROR in get_plots_high_pest_risk:", e)
        return []

    rows = list(results)
    print("DEBUG high-pest rows:", len(rows))
    for r in rows[:5]:
        print("  row:", r)

    # Deduplicate by plot_id; keep worst-case (highest rain & lowest yield)
    per_plot = {}
    for row in rows:
        pid = str(row["pid"])
        rain = float(row["rain"])
        yld = float(row["y"])
        name = str(row["name"])
        if pid not in per_plot:
            per_plot[pid] = {
                "plot_id": pid,
                "crop_name": name,
                "forecast_rainfall_mm": rain,
                "yield_kg_per_ha": yld,
            }
        else:
            # Higher rain + lower yield = more stressed
            if rain >= per_plot[pid]["forecast_rainfall_mm"] and yld <= per_plot[pid]["yield_kg_per_ha"]:
                per_plot[pid]["forecast_rainfall_mm"] = rain
                per_plot[pid]["yield_kg_per_ha"] = yld

    return sorted(per_plot.values(), key=lambda d: d["plot_id"])


# ---------------------------------------------------------------------
# 7. Next crop recommendations (NO BIND/IF/UNION – two simple queries)
# ---------------------------------------------------------------------
def get_next_crop_recommendations():
    """
    Simple crop-rotation recommendation:
      - If current crop is Zea mays L.  -> recommend next crop Glycine max L. (legume)
      - If current crop is Glycine max L. -> recommend next crop Zea mays L. (cereal)

    Implemented as two separate simple SPARQL queries to avoid tricky SPARQL
    features that trigger rdflib parser bugs.
    """

    # Case 1: maize -> recommend soybean
    query_maize = """
    PREFIX sf: <http://example.org/smart-farming#>

    SELECT ?pid ?y ?current_name
    WHERE {
      ?yr a sf:YieldRecord ;
          sf:aboutPlot ?pl ;
          sf:hasYear ?y ;
          sf:forCrop ?crop .

      ?pl sf:hasPlotID ?pid .
      ?crop sf:hasCropName ?current_name .

      FILTER (lcase(str(?current_name)) = "zea mays l.")
    }
    ORDER BY ?pid ?y
    """

    # Case 2: soybean -> recommend maize
    query_soy = """
    PREFIX sf: <http://example.org/smart-farming#>

    SELECT ?pid ?y ?current_name
    WHERE {
      ?yr a sf:YieldRecord ;
          sf:aboutPlot ?pl ;
          sf:hasYear ?y ;
          sf:forCrop ?crop .

      ?pl sf:hasPlotID ?pid .
      ?crop sf:hasCropName ?current_name .

      FILTER (lcase(str(?current_name)) = "glycine max l.")
    }
    ORDER BY ?pid ?y
    """

    rows_out = []

    try:
        # Maize -> next is soybean
        res_maize = g.query(query_maize)
    except Exception as e:
        print("ERROR in get_next_crop_recommendations (maize query):", e)
        res_maize = []

    try:
        # Soybean -> next is maize
        res_soy = g.query(query_soy)
    except Exception as e:
        print("ERROR in get_next_crop_recommendations (soy query):", e)
        res_soy = []

    res_maize = list(res_maize)
    res_soy = list(res_soy)
    print("DEBUG next-crop maize rows:", len(res_maize))
    print("DEBUG next-crop soy rows:", len(res_soy))

    for r in res_maize[:5]:
        print("  maize row:", r)
    for r in res_soy[:5]:
        print("  soy row:", r)

    # Build unified output
    for row in res_maize:
        rows_out.append(
            {
                "plot_id": str(row["pid"]),
                "year": int(str(row["y"])),
                "current_crop": str(row["current_name"]),
                "recommended_next_crop": "Glycine max L.",
                "recommended_next_crop_class": "LegumeCrop",
            }
        )

    for row in res_soy:
        rows_out.append(
            {
                "plot_id": str(row["pid"]),
                "year": int(str(row["y"])),
                "current_crop": str(row["current_name"]),
                "recommended_next_crop": "Zea mays L.",
                "recommended_next_crop_class": "CerealCrop",
            }
        )

    # Optional: sort and deduplicate by (plot_id, year, current_crop)
    uniq = {}
    for item in rows_out:
        key = (item["plot_id"], item["year"], item["current_crop"])
        uniq[key] = item

    final_rows = sorted(uniq.values(), key=lambda d: (d["plot_id"], d["year"]))

    print("DEBUG next-crop final rows:", len(final_rows))
    return final_rows
