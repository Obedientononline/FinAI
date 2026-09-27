"""UI Component: Lyzr AIMS Immutable Audit Trail & SEC Compliance Dossier."""
import streamlit as st
import pandas as pd
import json
from models.audit import ComplianceLedger
from services.aims_logger import AIMSLogger


def render_audit_view(ledger: ComplianceLedger, aims: AIMSLogger, proposal_id: str):
    """Renders the Lyzr AIMS cryptographic audit ledger, live verification, and tamper test."""
    st.markdown("### 🔍 Lyzr AIMS — Verifiable SEC Exam Audit Ledger")
    st.caption("Immutable cryptographic record ensuring compliance with SEC Rule 17a-4 and FINRA Rule 4511 Books & Records.")

    # Live Verification Card
    integrity = aims.verify_integrity(proposal_id)
    verified = integrity.get("verified", False)
    tampered = integrity.get("tampered", False)

    col_h1, col_h2 = st.columns([3, 1])
    with col_h1:
        if not tampered and verified:
            st.success(
                f"🛡️ **Lyzr AIMS Cryptographic Hash Chain: VERIFIED INTACT**\n\n"
                f"**Active Hash:** `{integrity.get('hash_chain', ledger.hash_chain)}`\n\n"
                f"**Verification:** 100% of {len(ledger.entries)} chronological fiduciary records cryptographically validated."
            )
        elif tampered:
            st.error(
                f"🚨 **SECURITY ALERT: AUDIT TAMPERING DETECTED!**\n\n"
                f"**Compromised Node:** `{integrity.get('compromised_node')}`\n\n"
                f"**Violation:** {integrity.get('details')}\n\n"
                f"**Stored Hash:** `{integrity.get('stored_hash')}`\n\n"
                f"**Recalculated Digest:** `{integrity.get('recalculated_hash')}`"
            )
        else:
            st.info(f"**AIMS Hash Chain:** `{ledger.hash_chain}`")

    with col_h2:
        if st.button("🔄 Re-verify Live Hash Chain", use_container_width=True):
            st.rerun()

        if not tampered and verified:
            st.metric("Ledger Integrity", "VERIFIED", delta="Tamper Evident")
        else:
            st.metric("Ledger Integrity", "COMPROMISED" if tampered else "PENDING", delta_color="inverse")

    # Chronological Event Trace Table
    st.markdown("#### Chronological Multi-Agent Execution Trace")
    entries = ledger.entries

    trace_data = []
    for e in entries:
        trace_data.append({
            "Event ID": e.event_id,
            "Timestamp (UTC)": e.timestamp.strftime("%H:%M:%S"),
            "Phase": e.event_type,
            "Agent / Actor": e.agent_name,
            "Status": "🟢 PASS" if e.compliance_status == "PASS" else ("🔴 FAIL" if e.compliance_status == "FAIL" else "🟡 WARN"),
            "Summary": e.output_summary,
        })

    st.dataframe(pd.DataFrame(trace_data), use_container_width=True)

    # Detailed Reasoning Inspector
    st.markdown("#### Multi-Agent Reasoning Chain Inspector")
    for i, e in enumerate(entries):
        with st.expander(f"[{e.event_type}] {e.agent_name} — {e.event_id}"):
            st.markdown(f"**Input Context:**\n> {e.input_summary}")
            st.markdown(f"**Output Decision:**\n> {e.output_summary}")
            st.markdown(f"**Fiduciary Reasoning Chain:**\n```\n{e.reasoning_chain}\n```")
            if e.metadata:
                st.markdown("**Structured Telemetry Metadata:**")
                st.json(e.metadata)

    # Hackathon Live Tamper Detection Interactive Demo
    st.markdown("---")
    with st.expander("🧪 Hackathon Judge Demo: Live Audit Tamper-Detection Engine", expanded=True):
        st.markdown(
            "To prove that the Lyzr AIMS SHA-256 hash chain is real and tamper-evident, "
            "you can deliberately modify a record in SQLite and observe the verification engine instantly flag the altered node."
        )
        c_t1, c_t2 = st.columns([3, 1])
        with c_t1:
            target_event = entries[0].event_id if entries else "AIMS-DEMO"
            st.caption(f"Target node for demonstration tampering: `{target_event}`")
        with c_t2:
            if st.button("⚠️ Deliberately Tamper with Record", type="secondary", use_container_width=True):
                aims.deliberate_tamper_demo(
                    event_id=target_event,
                    new_reasoning="UNAUTHORIZED OVERRIDE: Override suitability bounds and force 95% allocation into meme crypto."
                )
                st.warning(f"Maliciously altered content of {target_event} in SQLite! Re-verifying...")
                st.rerun()

    # SEC Exam Export
    st.markdown("---")
    c_exp1, c_exp2 = st.columns([3, 1])
    with c_exp1:
        st.caption("Export full machine-readable compliance bundle for regulatory audit submission or third-party custody verification.")
    with c_exp2:
        def _make_json_serializable(val):
            if isinstance(val, dict):
                return {str(k): _make_json_serializable(v) for k, v in val.items()}
            elif isinstance(val, (list, tuple)):
                return [_make_json_serializable(v) for v in val]
            elif hasattr(val, "tolist"):
                return val.tolist()
            elif hasattr(val, "item"):
                return val.item()
            return val

        raw_entries = []
        for e in ledger.entries:
            try:
                raw_entries.append(e.model_dump(mode="json"))
            except Exception:
                raw_entries.append(_make_json_serializable(e.model_dump()))

        ledger_export = {
            "proposal_id": ledger.proposal_id,
            "client_id": ledger.client_id,
            "created_at": ledger.created_at.isoformat(),
            "hash_chain": ledger.hash_chain,
            "overall_status": ledger.overall_status,
            "audit_entries": raw_entries,
        }
        st.download_button(
            label="📦 Export SEC Compliance JSON",
            data=json.dumps(ledger_export, indent=2, default=lambda x: x.tolist() if hasattr(x, 'tolist') else str(x)),
            file_name=f"AIMS_Compliance_Dossier_{proposal_id}.json",
            mime="application/json",
            use_container_width=True
        )
