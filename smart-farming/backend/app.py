from flask import Flask, jsonify
from flask_cors import CORS
from scripts.query_service import (
    list_plots,
    get_plot_year_summary,
    get_plots_needing_fertilizer,
    get_legume_crops,
    get_cereal_crops,
    get_plots_to_postpone_fertilizer,
    get_plots_high_pest_risk,
    get_next_crop_recommendations,
)

app = Flask(__name__)
CORS(app)


@app.route("/api/plots", methods=["GET"])
def api_list_plots():
    plots = list_plots()
    return jsonify({"plots": plots})


@app.route("/api/plots/<plot_id>/year/<int:year>", methods=["GET"])
def api_plot_year(plot_id, year):
    data = get_plot_year_summary(plot_id, year)
    if data is None:
        return jsonify({"error": "No data found", "plot_id": plot_id, "year": year}), 404
    return jsonify(data)

@app.route("/api/recommendations/needs-fertilizer", methods=["GET"])
def api_needs_fertilizer():
    plots = get_plots_needing_fertilizer()
    return jsonify({
        "recommendation": "NeedsFertilizerPlot",
        "plots": plots,
    })


@app.route("/api/crops/legumes", methods=["GET"])
def api_legume_crops():
    crops = get_legume_crops()
    return jsonify({"legume_crops": crops})


@app.route("/api/crops/cereals", methods=["GET"])
def api_cereal_crops():
    crops = get_cereal_crops()
    return jsonify({"cereal_crops": crops})


@app.route("/api/recommendations/postpone-fertilizer", methods=["GET"])
def api_postpone_fertilizer():
    plots = get_plots_to_postpone_fertilizer()
    return jsonify({
        "recommendation": "PostponeFertilizerPlot",
        "plots": plots,
    })

@app.route("/api/recommendations/high-pest-risk", methods=["GET"])
def api_high_pest_risk():
    plots = get_plots_high_pest_risk()
    return jsonify({
        "recommendation": "HighPestRiskPlot",
        "plots": plots,
    })

@app.route("/api/recommendations/next-crop", methods=["GET"])
def api_next_crop():
    recs = get_next_crop_recommendations()
    return jsonify({
        "recommendation": "NextCropRotation",
        "items": recs,
    })


if __name__ == "__main__":
    app.run(debug=True)
