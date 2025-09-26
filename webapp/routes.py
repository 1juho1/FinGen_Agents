from __future__ import annotations

import logging
from typing import Any, Dict

from flask import Blueprint, jsonify, render_template, request

from analytics import fetch_returns_plot, figure_to_data_url
from run_pipeline import run_agent_pipeline
from test_trader import run_trader_simulation
from ticker_search import search_tickers

LOGGER = logging.getLogger(__name__)

blueprint = Blueprint("web", __name__)


def init_app(app):  # type: ignore[no-untyped-def]
    app.register_blueprint(blueprint)


@blueprint.route("/")
def index():  # type: ignore[no-untyped-def]
    return render_template("index.html")


@blueprint.get("/api/search")
def api_search():  # type: ignore[no-untyped-def]
    query = (request.args.get("q") or "").strip()
    if len(query) < 2:
        return jsonify([])

    suggestions = search_tickers(query)
    return jsonify(
        [
            {
                "label": item["label"],
                "symbol": item["symbol"],
                "logo": item["logo_data_url"],
            }
            for item in suggestions
        ]
    )


@blueprint.post("/api/run")
def api_run():  # type: ignore[no-untyped-def]
    payload: Dict[str, Any] = request.get_json(force=True)

    ticker = payload.get("ticker")
    if not ticker:
        return jsonify({"error": "Ticker is required"}), 400

    risk = payload.get("risk", "moderate")
    period = payload.get("period", "5y")
    freq = payload.get("freq", "Y")

    LOGGER.info("Running pipeline for ticker=%s risk=%s", ticker, risk)

    summary, strategy = run_agent_pipeline(ticker=ticker, risk_profile=risk)
    trader_fig, trader_stats = run_trader_simulation(ticker=ticker, close_figure=False)
    trader_chart = figure_to_data_url(trader_fig)

    returns_fig = fetch_returns_plot(ticker, period=period, freq=freq)
    returns_chart = figure_to_data_url(returns_fig) if returns_fig else None

    return jsonify(
        {
            "summary": summary,
            "strategy": strategy,
            "traderStats": trader_stats,
            "traderChart": trader_chart,
            "returnsChart": returns_chart,
        }
    )
