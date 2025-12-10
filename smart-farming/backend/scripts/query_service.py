from pathlib import Path
from rdflib import Graph, Namespace, Literal
from rdflib.namespace import RDF

BASE_URI = "http://example.org/smart-farming#"
SF = Namespace(BASE_URI)

BASE_DIR = Path(__file__).resolve().parent.parent

g = Graph()
g.parse(BASE_DIR / "ontology" / "smart-farming-backup.owl")
g.parse(BASE_DIR / "ontology" / "instances.ttl", format="turtle")

g.bind("sf", SF)
g.bind("", SF)

from threading import Lock
QUERY_LOCK = Lock()

# ---------------------------------------------------------------------
# 1. Plot + year summary
# ---------------------------------------------------------------------
def get_plot_year_summary(plot_id: str, year: int):
    # Query yield data
    yield_query = f"""
    PREFIX sf: <{BASE_URI}>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

    SELECT ?y ?yield ?cropName ?treatmentCode
    WHERE {{
      sf:{plot_id} a sf:Plot .

      ?yr a sf:YieldRecord ;
          sf:aboutPlot sf:{plot_id} ;
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
    }}
    """

    # Query soil data separately
    soil_query = f"""
    PREFIX sf: <{BASE_URI}>

    SELECT ?y ?soil_pH ?P ?K ?Ca ?Mg ?CEC ?OM
    WHERE {{
      sf:{plot_id} a sf:Plot .

      ?sm a sf:SoilMeasurement ;
          sf:aboutPlot sf:{plot_id} ;
          sf:hasYear ?y .

      OPTIONAL {{ ?sm sf:soil_pH ?soil_pH }}
      OPTIONAL {{ ?sm sf:soil_P_mg_per_kg ?P }}
      OPTIONAL {{ ?sm sf:soil_K_mg_per_kg ?K }}
      OPTIONAL {{ ?sm sf:soil_Ca_mg_per_kg ?Ca }}
      OPTIONAL {{ ?sm sf:soil_Mg_mg_per_kg ?Mg }}
      OPTIONAL {{ ?sm sf:soil_CEC ?CEC }}
      OPTIONAL {{ ?sm sf:soil_OM_pct ?OM }}
    }}
    """

    # Query weather data separately
    weather_query = f"""
    PREFIX sf: <{BASE_URI}>

    SELECT ?y ?precip ?tmax ?tmin
    WHERE {{
      sf:{plot_id} a sf:Plot .

      ?ws a sf:WeatherSummary ;
          sf:aboutPlot sf:{plot_id} ;
          sf:hasYear ?y .

      OPTIONAL {{ ?ws sf:totalPrecip_mm ?precip }}
      OPTIONAL {{ ?ws sf:avgTmax_C ?tmax }}
      OPTIONAL {{ ?ws sf:avgTmin_C ?tmin }}
    }}
    """

    try:
        with QUERY_LOCK:
            yield_results = [row for row in g.query(yield_query)]
            soil_results = [row for row in g.query(soil_query)]
            weather_results = [row for row in g.query(weather_query)]
    except Exception as e:
        print(f"ERROR in get_plot_year_summary: {e}")
        return None

    print(f"DEBUG: plot={plot_id}, year={year}")
    print(f"  yields: {len(yield_results)}, soils: {len(soil_results)}, weathers: {len(weather_results)}")

    chosen_yield = None
    for row in yield_results:
        row_year = str(row[0]) if row[0] else ""
        if row_year == str(year):
            chosen_yield = row
            break

    if chosen_yield is None:
        print(f"DEBUG: No yield for {plot_id}/{year}")
        return None

    # Find soil for same year
    soil_data = None
    for row in soil_results:
        row_year = str(row[0]) if row[0] else ""
        if row_year == str(year):
            soil_data = {
                "soil_pH": float(row[1]) if row[1] is not None else None,
                "P": float(row[2]) if row[2] is not None else None,
                "K": float(row[3]) if row[3] is not None else None,
                "Ca": float(row[4]) if row[4] is not None else None,
                "Mg": float(row[5]) if row[5] is not None else None,
                "CEC": float(row[6]) if row[6] is not None else None,
                "OM": float(row[7]) if row[7] is not None else None,
            }
            break

    # Find weather for same year
    weather_data = None
    for row in weather_results:
        row_year = str(row[0]) if row[0] else ""
        if row_year == str(year):
            weather_data = {
                "precip": float(row[1]) if row[1] is not None else None,
                "tmax": float(row[2]) if row[2] is not None else None,
                "tmin": float(row[3]) if row[3] is not None else None,
            }
            break

    def _to_float(x):
        try:
            return float(x) if x is not None else None
        except:
            return None

    return {
        "plot_id": plot_id,
        "year": year,
        "yield_kg_per_ha": _to_float(chosen_yield[1]) if chosen_yield[1] is not None else None,
        "crop_name": str(chosen_yield[2]) if chosen_yield[2] is not None else None,
        "treatment": str(chosen_yield[3]) if chosen_yield[3] is not None else None,
        "soil": {
            "pH": soil_data["soil_pH"] if soil_data else None,
            "P_mg_per_kg": soil_data["P"] if soil_data else None,
            "K_mg_per_kg": soil_data["K"] if soil_data else None,
            "Ca_mg_per_kg": soil_data["Ca"] if soil_data else None,
            "Mg_mg_per_kg": soil_data["Mg"] if soil_data else None,
            "CEC": soil_data["CEC"] if soil_data else None,
            "OM_pct": soil_data["OM"] if soil_data else None,
        },
        "weather": {
            "total_precip_mm": weather_data["precip"] if weather_data else None,
            "avg_tmax_C": weather_data["tmax"] if weather_data else None,
            "avg_tmin_C": weather_data["tmin"] if weather_data else None,
        },
    }


# ---------------------------------------------------------------------
# 2. Utility: list all plots
# ---------------------------------------------------------------------
def list_plots():
    """Return a simple list of all plot IDs that exists."""
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
        with QUERY_LOCK:
            results = list(g.query(query))
    except Exception as e:
        print("ERROR in list_plots:", e)
        return []
    return sorted([str(row["pid"]) for row in results])


# ---------------------------------------------------------------------
# 3. Needs fertilizer
# ---------------------------------------------------------------------
def get_plots_needing_fertilizer():
    """
    Plots that look nutrient-limited (low yield OR low soil P OR low soil N).
    Returns a list of plot IDs.
    """
    query = """
    PREFIX sf: <{}>

    SELECT DISTINCT ?pid ?y ?p ?n ?yield
    WHERE {{
      ?pl a sf:Plot ;
          sf:hasPlotID ?pid .

      # Any low-yield record on this plot
      OPTIONAL {{
        ?yr a sf:YieldRecord ;
            sf:aboutPlot ?pl ;
            sf:yield_kg_per_ha ?yield .
        FILTER (?yield < 1111.0)
      }}

      # Any low soil P on this plot
      OPTIONAL {{
        ?smP a sf:SoilMeasurement ;
             sf:aboutPlot ?pl ;
             sf:soil_P_mg_per_kg ?p .
        FILTER (?p < 15.0)
      }}

      # Any low soil N on this plot
      OPTIONAL {{
        ?smN a sf:SoilMeasurement ;
             sf:aboutPlot ?pl ;
             sf:soil_N_mg_per_kg ?n .
        FILTER (?n < 10.0)
      }}

      # Require that at least one of these three conditions held
      FILTER(BOUND(?yield) || BOUND(?p) || BOUND(?n))
    }}
    ORDER BY ?pid
    """.format(BASE_URI)
    try:
        with QUERY_LOCK:
            results = list(g.query(query))
    except Exception as e:
        print("ERROR in get_plots_needing_fertilizer:", e)
        return []

    rows = list(results)
    print("DEBUG needs-fertilizer rows:", len(rows))
    for r in rows[:5]:
        print("  row:", r)

    return sorted({str(row["pid"]) for row in rows})


# ---------------------------------------------------------------------
# 4. Crop lookup
# ---------------------------------------------------------------------
def get_legume_crops():
    query = """
    PREFIX sf: <{}>

    SELECT ?crop ?name
    WHERE {{
      ?crop a sf:Crop ;
            sf:hasCropName ?name .
      FILTER (lcase(str(?name)) = "glycine max l.")
    }}
    ORDER BY ?name
    """.format(BASE_URI)
    try:
        with QUERY_LOCK:
            results = list(g.query(query))
    except Exception as e:
        print("ERROR in get_legume_crops:", e)
        return []

    return [
        {"uri": str(row["crop"]), "name": str(row["name"])}
        for row in results
    ]


def get_cereal_crops():
    query = """
    PREFIX sf: <{}>

    SELECT ?crop ?name
    WHERE {{
      ?crop a sf:Crop ;
            sf:hasCropName ?name .
      FILTER (lcase(str(?name)) = "zea mays l.")
    }}
    ORDER BY ?name
    """.format(BASE_URI)
    try:
        with QUERY_LOCK:
            results = list(g.query(query))
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
    Plots where soil_P >= 15 AND rainfall > 650.
    Query soil and weather separately then combine.
    """
    soil_query = """
    PREFIX sf: <{}>

    SELECT DISTINCT ?pid ?p
    WHERE {{
      ?pl a sf:Plot ;
          sf:hasPlotID ?pid .
      
      ?sm a sf:SoilMeasurement ;
          sf:aboutPlot ?pl ;
          sf:soil_P_mg_per_kg ?p .
      
      FILTER (?p >= 15.0)
    }}
    ORDER BY ?pid
    """.format(BASE_URI)

    rain_query = """
    PREFIX sf: <{}>

    SELECT DISTINCT ?pid ?rain
    WHERE {{
      ?pl a sf:Plot ;
          sf:hasPlotID ?pid .
      
      ?ws a sf:WeatherSummary ;
          sf:aboutPlot ?pl ;
          sf:forecastRainfallAmount_mm ?rain .
      
      FILTER (?rain > 650.0)
    }}
    ORDER BY ?pid
    """.format(BASE_URI)

    try:
        with QUERY_LOCK:
            soil_results = list(g.query(soil_query))
            rain_results = list(g.query(rain_query))
    except Exception as e:
        print("ERROR in get_plots_to_postpone_fertilizer:", e)
        return []

    # Build sets for efficient intersection
    soil_plots = {}
    for row in soil_results:
        pid = str(row["pid"])
        soil_plots[pid] = float(row["p"])

    rain_plots = {}
    for row in rain_results:
        pid = str(row["pid"])
        rain_plots[pid] = float(row["rain"])

    # Find intersection - plots with BOTH high P AND high rain
    result = []
    for pid in soil_plots:
        if pid in rain_plots:
            result.append({
                "plot_id": pid,
                "soil_P_mg_per_kg": soil_plots[pid],
                "forecast_rainfall_mm": rain_plots[pid],
            })

    return sorted(result, key=lambda d: d["plot_id"])


# ---------------------------------------------------------------------
# 6. High pest risk
# ---------------------------------------------------------------------
def get_plots_high_pest_risk():
    # Get maize plots
    maize_query = """
    PREFIX sf: <{}>

    SELECT DISTINCT ?pid ?crop_name
    WHERE {{
      ?pl a sf:Plot ;
          sf:hasPlotID ?pid .
      
      ?yr a sf:YieldRecord ;
          sf:aboutPlot ?pl ;
          sf:forCrop ?crop .
      
      ?crop sf:hasCropName ?crop_name .
      
      FILTER (lcase(str(?crop_name)) = "zea mays l.")
    }}
    ORDER BY ?pid
    """.format(BASE_URI)

    # Get high rainfall plots
    rain_query = """
    PREFIX sf: <{}>

    SELECT DISTINCT ?pid ?rain
    WHERE {{
      ?pl a sf:Plot ;
          sf:hasPlotID ?pid .
      
      ?ws a sf:WeatherSummary ;
          sf:aboutPlot ?pl ;
          sf:forecastRainfallAmount_mm ?rain .
      
      FILTER (?rain > 950.0)
    }}
    ORDER BY ?pid
    """.format(BASE_URI)

    # Get low yield plots
    yield_query = """
    PREFIX sf: <{}>

    SELECT DISTINCT ?pid ?y
    WHERE {{
      ?pl a sf:Plot ;
          sf:hasPlotID ?pid .
      
      ?yr a sf:YieldRecord ;
          sf:aboutPlot ?pl ;
          sf:yield_kg_per_ha ?y .
      
      FILTER (?y < 2500.0)
    }}
    ORDER BY ?pid
    """.format(BASE_URI)

    try:
        with QUERY_LOCK:
            maize_results = list(g.query(maize_query))
            rain_results = list(g.query(rain_query))
            yield_results = list(g.query(yield_query))
    except Exception as e:
        print("ERROR in get_plots_high_pest_risk:", e)
        return []

    # Build dictionaries
    maize_plots = {}
    for row in maize_results:
        pid = str(row["pid"])
        maize_plots[pid] = str(row["crop_name"])

    rain_plots = {}
    for row in rain_results:
        pid = str(row["pid"])
        rain_plots[pid] = float(row["rain"])

    yield_plots = {}
    for row in yield_results:
        pid = str(row["pid"])
        if pid not in yield_plots or float(row["y"]) < yield_plots[pid]:
            yield_plots[pid] = float(row["y"])

    # Find intersection
    result = []
    for pid in maize_plots:
        if pid in rain_plots and pid in yield_plots:
            result.append({
                "plot_id": pid,
                "crop_name": maize_plots[pid],
                "forecast_rainfall_mm": rain_plots[pid],
                "yield_kg_per_ha": yield_plots[pid],
            })
    return sorted(result, key=lambda d: d["plot_id"])


# ---------------------------------------------------------------------
# 7. Next crop recommendations
# ---------------------------------------------------------------------
def get_next_crop_recommendations():
    """
    Simple crop-rotation recommendation:
      - If current crop is Zea mays L.  -> recommend next crop Glycine max L. (legume)
      - If current crop is Glycine max L. -> recommend next crop Zea mays L. (cereal)
    """

    # Case 1: maize -> recommend soybean
    query_maize = """
    PREFIX sf: <{}>

    SELECT ?pid ?y ?current_name
    WHERE {{
      ?yr a sf:YieldRecord ;
          sf:aboutPlot ?pl ;
          sf:hasYear ?y ;
          sf:forCrop ?crop .

      ?pl sf:hasPlotID ?pid .
      ?crop sf:hasCropName ?current_name .

      FILTER (lcase(str(?current_name)) = "zea mays l.")
    }}
    ORDER BY ?pid ?y
    """.format(BASE_URI)

    # Case 2: soybean -> recommend maize
    query_soy = """
    PREFIX sf: <{}>

    SELECT ?pid ?y ?current_name
    WHERE {{
      ?yr a sf:YieldRecord ;
          sf:aboutPlot ?pl ;
          sf:hasYear ?y ;
          sf:forCrop ?crop .

      ?pl sf:hasPlotID ?pid .
      ?crop sf:hasCropName ?current_name .

      FILTER (lcase(str(?current_name)) = "glycine max l.")
    }}
    ORDER BY ?pid ?y
    """.format(BASE_URI)

    rows_out = []

    try:
        # Maize -> next is soybean
        with QUERY_LOCK:
            res_maize = list(g.query(query_maize))
    except Exception as e:
        print("ERROR in get_next_crop_recommendations (maize query):", e)
        res_maize = []

    try:
        # Soybean -> next is maize
        with QUERY_LOCK:
            res_soy = list(g.query(query_soy))
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

    uniq = {}
    for item in rows_out:
        key = (item["plot_id"], item["year"], item["current_crop"])
        uniq[key] = item

    final_rows = sorted(uniq.values(), key=lambda d: (d["plot_id"], d["year"]))

    return final_rows
