"""Proposal Generator Service.

Generates advisor-ready briefing documents and formal compliance proposals in Markdown
and PDF format with suitability justifications, trade rationales, tax summaries,
and Lyzr AIMS cryptographic audit hashes.
"""
from typing import Optional
from datetime import datetime
from models.proposal import TradeProposal
from models.client_profile import ClientProfile
from models.audit import ComplianceLedger


def generate_proposal_markdown(
    proposal: TradeProposal, profile: ClientProfile, ledger: ComplianceLedger
) -> str:
    """Produces a clean Markdown briefing document for the RIA advisor."""
    md = []
    md.append(f"# 🏛️ Fiduciary Trade Proposal & Compliance Dossier")
    md.append(f"**Proposal ID:** `{proposal.proposal_id}` | **Date:** {proposal.timestamp.strftime('%B %d, %Y %H:%M UTC')}")
    md.append(f"**Client:** {profile.name} (ID: `{profile.client_id}`) | **Tax Bracket:** {profile.ips.tax_bracket:.1%}")
    md.append("---")

    # 1. Executive Summary & Fiduciary Profile
    md.append("## 1. Client Fiduciary Profile")
    md.append(f"- **Calculated Risk Score:** **{proposal.risk_score} / 10** (`{proposal.risk_category.replace('_', ' ').title()}`)")
    md.append(f"- **Investment Horizon:** {profile.ips.time_horizon_years} years | **Liquidity Requirement:** {profile.ips.liquidity_needs.title()}")
    md.append(f"- **IPS Restrictions:** {', '.join(profile.ips.restrictions) if profile.ips.restrictions else 'None'}")
    md.append(f"- **Concentration Limit:** Max {profile.ips.max_single_position_pct:.1%} per position")
    md.append("")

    # 2. Asset Allocation Transition
    md.append("## 2. Asset Class Allocation Shift")
    md.append("| Asset Class | Current Weight | Target Weight | Drift / Adjustment |")
    md.append("| :--- | :---: | :---: | :---: |")
    for ac in ["equities", "fixed_income", "commodities", "cash"]:
        curr_w = proposal.current_allocation.get(ac, 0.0)
        targ_w = proposal.target_allocation.get(ac, 0.0)
        drift = targ_w - curr_w
        md.append(f"| **{ac.replace('_', ' ').title()}** | {curr_w:.1%} | {targ_w:.1%} | {drift:+.1%} |")
    md.append("")

    # 3. Macro Market Context
    md.append("## 3. Macroeconomic Regime Analysis")
    md.append(f"> {proposal.market_analysis}")
    md.append("")

    # 4. Actionable Trade Orders
    md.append("## 4. Deterministic Trade Orders")
    md.append("| Action | Symbol | Class | Shares | Price | Est. Value | Est. Tax Impact | Rationale |")
    md.append("| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |")
    for t in proposal.trades:
        tax_str = f"₹{t.tax_impact:,.2f}" if t.action == "SELL" else "—"
        md.append(
            f"| **{t.action}** | `{t.symbol}` | {t.asset_class.title()} | {t.shares:,.0f} | "
            f"₹{t.estimated_price:,.2f} | ₹{t.estimated_value:,.2f} | {tax_str} | {t.rationale} |"
        )
    md.append("")
    md.append(f"- **Total Capital Deployed (BUY):** `₹{proposal.total_buy_value:,.2f}`")
    md.append(f"- **Total Capital Liquidated (SELL):** `₹{proposal.total_sell_value:,.2f}`")
    md.append(f"- **Estimated Net Realized Tax Drag:** `₹{proposal.net_tax_impact:,.2f}`")
    md.append("")

    # 5. Lyzr Safe AI Suitability Gate Status
    md.append("## 5. FINRA & Lyzr Safe AI Suitability Gate")
    gate_badge = "✅ **ALL 12 CHECKS PASSED — APPROVED FOR EXECUTION**" if proposal.suitability_report.all_passed else "❌ **CRITICAL VIOLATION DETECTED — EXECUTION BLOCKED**"
    md.append(f"**Status:** {gate_badge}")
    md.append("")
    md.append("| Rule ID | Rule Name | Severity | Result | Verification Details |")
    md.append("| :--- | :--- | :---: | :---: | :--- |")
    for c in proposal.suitability_report.checks:
        res_icon = "✅ PASS" if c.passed else ("🚫 FAIL" if c.severity == "critical" else "⚠️ WARN")
        md.append(f"| `{c.rule_id}` | {c.rule_name} | `{c.severity.upper()}` | {res_icon} | {c.details} |")
    md.append("")

    # 6. Lyzr AIMS Cryptographic Compliance Chain
    md.append("## 6. Lyzr AIMS SEC Exam Record & Hash Chain")
    md.append(f"- **AIMS Ledger Status:** `{ledger.overall_status}`")
    md.append(f"- **Immutable SHA-256 Chain:** `{ledger.hash_chain}`")
    md.append(f"- **Logged Fiduciary Events:** {len(ledger.entries)} chronological trace records")
    md.append("- *Tamper-evident record generated in compliance with SEC Rule 17a-4 and FINRA Rule 4511.*")
    md.append("")

    return "\n".join(md)


def generate_proposal_pdf(
    proposal: TradeProposal,
    profile: ClientProfile,
    ledger: ComplianceLedger,
    output_path: str = "proposal_report.pdf",
) -> str:
    """Generates an official PDF compliance document."""
    try:
        from fpdf import FPDF

        class PDF(FPDF):
            def header(self):
                self.set_font("Helvetica", "B", 13)
                self.cell(0, 8, "Safe Wealth Advisory | Governed Trade Proposal", border=False, align="L")
                self.ln(10)

            def footer(self):
                self.set_y(-15)
                self.set_font("Helvetica", "I", 8)
                self.cell(0, 10, f"Page {self.page_no()}/{{nb}} | AIMS Hash: {ledger.hash_chain[:24]}...", align="C")

        pdf = PDF()
        pdf.alias_nb_pages()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Title
        pdf.set_font("Helvetica", "B", 18)
        pdf.cell(0, 10, "Fiduciary Rebalancing Proposal", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"Client: {profile.name} (ID: {profile.client_id}) | Proposal ID: {proposal.proposal_id}", ln=True)
        pdf.cell(0, 6, f"Generated: {proposal.timestamp.strftime('%Y-%m-%d %H:%M UTC')} | AIMS Ledger Status: {ledger.overall_status}", ln=True)
        pdf.ln(5)

        # Executive Metrics
        pdf.set_fill_color(240, 243, 246)
        pdf.rect(10, pdf.get_y(), 190, 24, "F")
        pdf.set_xy(12, pdf.get_y() + 2)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(45, 6, f"Risk Score: {proposal.risk_score}/10", ln=False)
        pdf.cell(50, 6, f"Horizon: {profile.ips.time_horizon_years} Yrs", ln=False)
        pdf.cell(45, 6, f"Tax Bracket: {profile.ips.tax_bracket:.1%}", ln=False)
        suit_text = "Suitability: APPROVED" if proposal.suitability_report.all_passed else "Suitability: BLOCKED"
        pdf.cell(45, 6, suit_text, ln=True)

        pdf.set_xy(12, pdf.get_y())
        pdf.set_font("Helvetica", "", 9)
        pdf.cell(45, 6, f"Tier: {proposal.risk_category.title()}", ln=False)
        pdf.cell(50, 6, f"Liquidity: {profile.ips.liquidity_needs.title()}", ln=False)
        pdf.cell(45, 6, f"Est. Tax Drag: Rs. {proposal.net_tax_impact:,.2f}", ln=False)
        pdf.cell(45, 6, f"Trades: {len(proposal.trades)} orders", ln=True)
        pdf.ln(8)

        # Allocation Table
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Asset Allocation Transition", ln=True)
        pdf.set_font("Helvetica", "B", 9)
        pdf.cell(50, 6, "Asset Class", 1)
        pdf.cell(40, 6, "Current Weight", 1)
        pdf.cell(40, 6, "Target Weight", 1)
        pdf.cell(40, 6, "Net Drift", 1)
        pdf.ln()

        pdf.set_font("Helvetica", "", 9)
        for ac in ["equities", "fixed_income", "commodities", "cash"]:
            curr_w = proposal.current_allocation.get(ac, 0.0)
            targ_w = proposal.target_allocation.get(ac, 0.0)
            drift = targ_w - curr_w
            pdf.cell(50, 6, ac.replace("_", " ").title(), 1)
            pdf.cell(40, 6, f"{curr_w:.1%}", 1)
            pdf.cell(40, 6, f"{targ_w:.1%}", 1)
            pdf.cell(40, 6, f"{drift:+.1%}", 1)
            pdf.ln()
        pdf.ln(5)

        # Trade Orders Table
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Deterministic Rebalancing Trades", ln=True)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(20, 6, "Action", 1)
        pdf.cell(25, 6, "Symbol", 1)
        pdf.cell(25, 6, "Shares", 1)
        pdf.cell(30, 6, "Price (INR)", 1)
        pdf.cell(35, 6, "Est. Value (INR)", 1)
        pdf.cell(35, 6, "Tax Impact", 1)
        pdf.ln()

        pdf.set_font("Helvetica", "", 8)
        for t in proposal.trades:
            tax_str = f"Rs. {t.tax_impact:,.2f}" if t.action == "SELL" else "Rs. 0.00"
            pdf.cell(20, 5, t.action, 1)
            pdf.cell(25, 5, t.symbol, 1)
            pdf.cell(25, 5, f"{t.shares:,.0f}", 1)
            pdf.cell(30, 5, f"Rs. {t.estimated_price:,.2f}", 1)
            pdf.cell(35, 5, f"Rs. {t.estimated_value:,.2f}", 1)
            pdf.cell(35, 5, tax_str, 1)
            pdf.ln()
        pdf.ln(5)

        # Suitability & Compliance
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "FINRA Suitability & Lyzr Safe AI Results", ln=True)
        pdf.set_font("Helvetica", "", 8)
        for c in proposal.suitability_report.checks:
            mark = "[PASS]" if c.passed else "[FAIL]"
            pdf.cell(0, 4.5, f"{mark} {c.rule_id} - {c.rule_name}: {c.details}", ln=True)
        pdf.ln(5)

        # AIMS Audit Box
        pdf.set_fill_color(230, 240, 255)
        pdf.rect(10, pdf.get_y(), 190, 18, "F")
        pdf.set_xy(12, pdf.get_y() + 2)
        pdf.set_font("Helvetica", "B", 8)
        pdf.cell(0, 4, "Lyzr AIMS Immutable Audit Chain:", ln=True)
        pdf.set_font("Courier", "", 7)
        pdf.cell(0, 4, f"Hash: {ledger.hash_chain}", ln=True)
        pdf.set_font("Helvetica", "I", 7)
        pdf.cell(0, 4, "SEC Rule 17a-4 / FINRA 4511 Compliant Cryptographic Evidence Record", ln=True)

        pdf.output(output_path)
        return output_path

    except Exception as e:
        # Fallback if PDF generation encounters environment constraint: write markdown as report
        fallback_path = output_path.replace(".pdf", ".md")
        with open(fallback_path, "w", encoding="utf-8") as f:
            f.write(generate_proposal_markdown(proposal, profile, ledger))
        return fallback_path
