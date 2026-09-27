"""Safe Wealth Advisory & Governed Portfolio Rebalancer.

Flask RIA Wealth Manager Portal.
Built on Lyzr Agent API, Lyzr Safe AI Fiduciary Guardrails, and Lyzr AIMS.
"""
import json
import os
import sys

_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR = os.path.dirname(_BACKEND_DIR)
_FRONTEND_DIR = os.path.join(_ROOT_DIR, "frontend")

for p in [_ROOT_DIR, _BACKEND_DIR]:
    if p not in sys.path:
        sys.path.insert(0, p)

from flask import Flask, render_template, redirect, url_for, flash, request, send_file, jsonify

import config
from services.pipeline import AdvisoryPipeline
from engine.risk_scorer import compute_risk_score, get_scoring_explanation
from engine.backtester import run_portfolio_backtest
from services.document_parser import ingest_client_document

# ---------------------------------------------------------------------------
# App Setup
# ---------------------------------------------------------------------------
template_dir = os.path.join(_FRONTEND_DIR, "templates") if os.path.exists(os.path.join(_FRONTEND_DIR, "templates")) else "templates"
static_dir = os.path.join(_FRONTEND_DIR, "static") if os.path.exists(os.path.join(_FRONTEND_DIR, "static")) else "static"

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "safe-wealth-advisory-dev-key")

# Global pipeline (shared across requests – single-process dev server)
pipeline = AdvisoryPipeline()

# In-memory session store (starts empty; prompts for document ingestion first)
_session = {
    "active_client_id": None,
    "profile": None,
    "portfolio": None,
    "proposal": None,
    "ledger": None,
}


def _ensure_session():
    """Make sure active client's data is loaded if any client records exist."""
    clients = pipeline.get_all_clients()
    if not clients:
        _session["active_client_id"] = None
        _session["profile"] = None
        _session["portfolio"] = None
        _session["proposal"] = None
        _session["ledger"] = None
        return

    cid = _session["active_client_id"]
    if cid is None or not any(str(c["client_id"]) == str(cid) for c in clients):
        cid = str(clients[0]["client_id"])
        _session["active_client_id"] = cid

    if _session["profile"] is None or str(_session["profile"].client_id) != str(cid):
        _session["profile"] = pipeline.load_client(cid)
    if _session["portfolio"] is None:
        _session["portfolio"] = pipeline.load_portfolio(cid, use_mock_prices=True)
    if (_session["proposal"] is None or _session["ledger"] is None) and _session["profile"]:
        p, l = pipeline.run_advisory(
            profile=_session["profile"],
            portfolio=_session["portfolio"],
            use_mock_prices=True,
        )
        _session["proposal"] = p
        _session["ledger"] = l


def _switch_client(client_id: str):
    """Switch the active client and reload everything."""
    _session["active_client_id"] = str(client_id)
    _session["profile"] = pipeline.load_client(client_id)
    _session["portfolio"] = pipeline.load_portfolio(client_id, use_mock_prices=True)
    if _session["profile"] and _session["portfolio"]:
        p, l = pipeline.run_advisory(
            profile=_session["profile"],
            portfolio=_session["portfolio"],
            use_mock_prices=True,
        )
        _session["proposal"] = p
        _session["ledger"] = l


def _common_context():
    """Return template variables shared across every page."""
    _ensure_session()
    clients = pipeline.get_all_clients()
    return {
        "clients": clients,
        "active_client_id": _session["active_client_id"],
        "active_client_name": _session["profile"].name if _session["profile"] else None,
        "active_profile": _session["profile"],
        "active_portfolio": _session["portfolio"],
        "active_proposal": _session["proposal"],
        "current_step": 1,
    }


# ---------------------------------------------------------------------------
# JSON helper  (handles numpy, datetime, Pydantic objects)
# ---------------------------------------------------------------------------
def _safe_json(obj):
    """Serialize obj to a JSON string, handling numpy/datetime edge cases."""
    def _default(o):
        if hasattr(o, "tolist"):
            return o.tolist()
        if hasattr(o, "item"):
            return o.item()
        if hasattr(o, "isoformat"):
            return o.isoformat()
        if hasattr(o, "model_dump"):
            return o.model_dump(mode="json")
        return str(o)
    return json.dumps(obj, default=_default)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def dashboard():
    ctx = _common_context()
    ctx["active_page"] = "dashboard"
    ctx["current_step"] = 1
    if not ctx["clients"] or not ctx["active_profile"]:
        return redirect(url_for("upload_page"))
    return render_template("dashboard.html", **ctx)


@app.route("/client/<client_id>")
def client_page(client_id):
    _ensure_session()
    if not _session["profile"]:
        flash("Please complete Step 1 (Ingest Client Document) to view client profile.", "warning")
        return redirect(url_for("upload_page"))

    if client_id != _session["active_client_id"]:
        _switch_client(client_id)

    ctx = _common_context()
    ctx["active_page"] = "client"
    ctx["current_step"] = 2
    profile = _session["profile"]
    ctx["profile"] = profile

    # Risk scoring breakdown
    score, category, breakdown = compute_risk_score(profile.kyc, profile.ips)
    ctx["risk_breakdown"] = breakdown
    ctx["scoring_explanation"] = get_scoring_explanation(breakdown)

    return render_template("client.html", **ctx)


@app.route("/portfolio/<client_id>")
def portfolio_page(client_id):
    _ensure_session()
    if not _session["profile"]:
        flash("Please complete Step 1 (Ingest Client Document) to view portfolio.", "warning")
        return redirect(url_for("upload_page"))

    if client_id != _session["active_client_id"]:
        _switch_client(client_id)

    ctx = _common_context()
    ctx["active_page"] = "portfolio"
    ctx["current_step"] = 3
    ctx["profile"] = _session["profile"]
    ctx["portfolio"] = _session["portfolio"]

    # Allocation JSON for Plotly chart
    ctx["allocation_json"] = _safe_json(_session["portfolio"].allocation)

    # Tax-loss harvesting scan
    ctx["tlh_opportunities"] = pipeline.run_tax_loss_harvesting_scan(_session["portfolio"])

    return render_template("portfolio.html", **ctx)


@app.route("/proposal/<client_id>")
def proposal_page(client_id):
    _ensure_session()
    if not _session["profile"]:
        flash("Please complete Step 1 (Ingest Client Document) to view trade proposals.", "warning")
        return redirect(url_for("upload_page"))

    if client_id != _session["active_client_id"]:
        _switch_client(client_id)

    ctx = _common_context()
    ctx["active_page"] = "proposal"
    ctx["current_step"] = 4
    ctx["profile"] = _session["profile"]
    ctx["portfolio"] = _session["portfolio"]
    ctx["proposal"] = _session["proposal"]
    ctx["ledger"] = _session["ledger"]

    # Allocation comparison JSON
    ctx["allocation_json"] = _safe_json({
        "current": _session["proposal"].current_allocation,
        "target": _session["proposal"].target_allocation,
    })

    # Stress test
    ctx["stress_results"] = pipeline.run_stress_test(
        _session["portfolio"], _session["proposal"]
    )

    return render_template("proposal.html", **ctx)


@app.route("/analysis/<client_id>")
def analysis_page(client_id):
    _ensure_session()
    if not _session["profile"]:
        flash("Please complete Step 1 (Ingest Client Document) to view analysis.", "warning")
        return redirect(url_for("upload_page"))

    if client_id != _session["active_client_id"]:
        _switch_client(client_id)

    ctx = _common_context()
    ctx["active_page"] = "analysis"
    ctx["current_step"] = 4
    ctx["profile"] = _session["profile"]

    # Stress test
    ctx["stress_results"] = pipeline.run_stress_test(
        _session["portfolio"], _session["proposal"]
    )

    # Backtest
    backtest = run_portfolio_backtest(
        initial_capital=8300000,
        drift_threshold=0.05,
        tax_bracket=_session["profile"].ips.tax_bracket,
    )
    ctx["backtest"] = backtest
    # Convert timeseries DataFrame to JSON records for Plotly
    ctx["backtest_json"] = backtest["timeseries"].to_json(orient="records")

    return render_template("analysis.html", **ctx)


@app.route("/audit/<client_id>")
def audit_page(client_id):
    _ensure_session()
    if not _session["profile"]:
        flash("Please complete Step 1 (Ingest Client Document) to view audit ledger.", "warning")
        return redirect(url_for("upload_page"))

    if client_id != _session["active_client_id"]:
        _switch_client(client_id)

    ctx = _common_context()
    ctx["active_page"] = "audit"
    ctx["current_step"] = 5
    ctx["profile"] = _session["profile"]
    ctx["proposal"] = _session["proposal"]
    ctx["ledger"] = _session["ledger"]

    # Integrity verification
    ctx["integrity"] = pipeline.aims.verify_integrity(_session["proposal"].proposal_id)

    # Pre-build ledger export JSON
    raw_entries = []
    for e in _session["ledger"].entries:
        try:
            raw_entries.append(e.model_dump(mode="json"))
        except Exception:
            raw_entries.append(json.loads(_safe_json(e.model_dump())))

    ctx["ledger_json"] = _safe_json({
        "proposal_id": _session["ledger"].proposal_id,
        "client_id": _session["ledger"].client_id,
        "created_at": _session["ledger"].created_at.isoformat(),
        "hash_chain": _session["ledger"].hash_chain,
        "overall_status": _session["ledger"].overall_status,
        "audit_entries": raw_entries,
    })

    return render_template("audit.html", **ctx)


@app.route("/clear_clients", methods=["GET", "POST"])
def clear_clients():
    """Clear all client accounts from database and reset session to step 1."""
    pipeline.clear_all_clients()
    _session["active_client_id"] = None
    _session["profile"] = None
    _session["portfolio"] = None
    _session["proposal"] = None
    _session["ledger"] = None
    flash("All client records have been cleared. Ready to ingest a fresh client document.", "info")
    return redirect(url_for("upload_page"))


@app.route("/seed_demo_clients", methods=["GET", "POST"])
def seed_demo_clients():
    """Load pre-configured demo client archetypes."""
    from seed_clients import seed_database
    seed_database()
    clients = pipeline.get_all_clients()
    if clients:
        _switch_client(clients[0]["client_id"])
    flash("Loaded 8 institutional test archetypes (including FINRA violation benchmarks).", "success")
    return redirect(url_for("dashboard"))


@app.route("/upload", methods=["GET", "POST"])
def upload_page():
    ctx = _common_context()
    ctx["active_page"] = "upload"

    if request.method == "POST":
        file = request.files.get("client_file")
        if not file or not file.filename:
            flash("Please choose a valid client document file (.pdf, .docx, .xlsx, .csv, .json).", "danger")
            return render_template("upload.html", **ctx)

        filename = file.filename
        base_data_dir = os.path.join(os.path.dirname(__file__), "data")
        if os.environ.get("AWS_LAMBDA_FUNCTION_NAME") or os.environ.get("NETLIFY") or not os.access(base_data_dir, os.W_OK):
            upload_dir = os.path.join("/tmp", "uploads")
        else:
            upload_dir = os.path.join(base_data_dir, "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        saved_path = os.path.join(upload_dir, filename)
        file.save(saved_path)

        try:
            profile, portfolio, telemetry = ingest_client_document(saved_path)

            # Persist to database repository
            pipeline.save_new_client(profile, portfolio)

            # Update in-memory session state
            _session["active_client_id"] = profile.client_id
            _session["profile"] = profile
            _session["portfolio"] = portfolio

            # Execute advisory rebalancer & FINRA suitability pipeline
            p, l = pipeline.run_advisory(
                profile=profile,
                portfolio=portfolio,
                use_mock_prices=True,
            )
            _session["proposal"] = p
            _session["ledger"] = l

            flash(f"Successfully ingested {profile.name}! Calculated Risk Score: {profile.risk_score}/10 ({profile.risk_category.replace('_', ' ').title()}). Rebalancing proposal generated.", "success")

            ctx = _common_context()
            ctx["active_page"] = "upload"
            ctx["telemetry"] = telemetry
            ctx["ingested_profile"] = profile
            ctx["ingested_portfolio"] = portfolio
            ctx["ingested_proposal"] = p
            return render_template("upload.html", **ctx)

        except Exception as e:
            flash(f"Error parsing document: {str(e)}", "danger")
            return render_template("upload.html", **ctx)

    return render_template("upload.html", **ctx)


@app.route("/download_sample_template/<fmt>")
def download_sample_template(fmt):
    """Serve sample Excel, Word, or PDF onboarding template."""
    fmt = fmt.lower().strip()
    filename_map = {
        "xlsx": "sample_client_intake.xlsx",
        "docx": "sample_client_intake.docx",
        "pdf": "sample_client_intake.pdf",
        "png": "sample_client_intake.png"
    }
    fname = filename_map.get(fmt, "sample_client_intake.xlsx")
    fpath = os.path.join(os.path.dirname(__file__), "data", "sample_templates", fname)
    if not os.path.exists(fpath):
        flash("Sample template file not found.", "warning")
        return redirect(url_for("upload_page"))
    return send_file(fpath, as_attachment=True, download_name=fname)


# ---------------------------------------------------------------------------
# Action Routes
# ---------------------------------------------------------------------------

@app.route("/run_advisory/<client_id>", methods=["POST"])
def run_advisory(client_id):
    """Re-run the full advisory pipeline for the given client."""
    if client_id != _session["active_client_id"]:
        _switch_client(client_id)
    else:
        p, l = pipeline.run_advisory(
            profile=_session["profile"],
            portfolio=_session["portfolio"],
            use_mock_prices=True,
        )
        _session["proposal"] = p
        _session["ledger"] = l

    flash("Advisory pipeline executed successfully!", "success")
    return redirect(url_for("proposal_page", client_id=client_id))


@app.route("/approve/<client_id>", methods=["POST"])
def approve_proposal(client_id):
    """Advisor approval of the trade proposal."""
    _ensure_session()
    proposal = _session["proposal"]

    if not proposal.suitability_report.all_passed:
        flash("Cannot approve — critical suitability violations exist.", "danger")
        return redirect(url_for("proposal_page", client_id=client_id))

    notes = request.form.get("advisor_notes", "")
    proposal.advisor_approved = True
    proposal.advisor_notes = notes

    pipeline.aims.log_event(
        event_type="ADVISOR_DECISION",
        agent_name="RIA Wealth Advisor (Human-in-the-Loop)",
        input_summary=f"Proposal {proposal.proposal_id}",
        output_summary="EXECUTED_APPROVED",
        reasoning_chain=f"Human Advisor signed off: '{notes}'. Ledger hash confirmed.",
        compliance_status="PASS",
        proposal_id=proposal.proposal_id,
    )

    flash(
        f"Trade Proposal {proposal.proposal_id} APPROVED & queued for execution!",
        "success",
    )
    return redirect(url_for("proposal_page", client_id=client_id))


@app.route("/tamper/<client_id>", methods=["POST"])
def tamper_demo(client_id):
    """Deliberately tamper with an audit record for demo purposes."""
    _ensure_session()
    ledger = _session["ledger"]
    if ledger.entries:
        target_event = ledger.entries[0].event_id
        pipeline.aims.deliberate_tamper_demo(
            event_id=target_event,
            new_reasoning="UNAUTHORIZED OVERRIDE: Force 95% meme crypto allocation.",
        )
        flash(
            f"Tampered with record {target_event}! Re-verification will detect it.",
            "warning",
        )
    return redirect(url_for("audit_page", client_id=client_id))


@app.route("/download_pdf/<client_id>")
def download_pdf(client_id):
    """Generate and download the proposal PDF."""
    _ensure_session()
    from services.proposal_generator import generate_proposal_pdf

    base_dir = "/tmp" if (os.environ.get("AWS_LAMBDA_FUNCTION_NAME") or os.environ.get("NETLIFY") or not os.access(".", os.W_OK)) else "."
    pdf_path = os.path.join(base_dir, f"proposal_{_session['proposal'].proposal_id}.pdf")
    generate_proposal_pdf(
        _session["proposal"], _session["profile"], _session["ledger"],
        output_path=pdf_path,
    )
    return send_file(pdf_path, as_attachment=True, download_name=f"Proposal_{_session['proposal'].proposal_id}.pdf")


@app.route("/export_audit/<client_id>")
def export_audit(client_id):
    """Export the AIMS compliance ledger as JSON."""
    _ensure_session()
    raw_entries = []
    for e in _session["ledger"].entries:
        try:
            raw_entries.append(e.model_dump(mode="json"))
        except Exception:
            raw_entries.append(json.loads(_safe_json(e.model_dump())))

    export = {
        "proposal_id": _session["ledger"].proposal_id,
        "client_id": _session["ledger"].client_id,
        "created_at": _session["ledger"].created_at.isoformat(),
        "hash_chain": _session["ledger"].hash_chain,
        "overall_status": _session["ledger"].overall_status,
        "audit_entries": raw_entries,
    }
    return app.response_class(
        response=json.dumps(export, indent=2, default=str),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment;filename=AIMS_Dossier_{_session['proposal'].proposal_id}.json"},
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("\n  Safe Wealth Advisory -- Flask Portal")
    print("  " + "-" * 40)
    print("  Open http://localhost:5000 in your browser\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
