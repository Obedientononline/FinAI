# 🖥️ Frontend & UI App Clients

This directory houses the user interfaces, dashboards, client-intake wizards, and interactive web client applications that call the Lyzr agents and backend advisory services.

## 📁 Directory Structure

- **`templates/`**: Server-rendered HTML templates for RIA advisors (intake wizard, real-time portfolio dashboard, trade proposals, tamper-evident audit ledger, and document upload).
- **`static/`**: Client-side stylesheets (`css/style.css`) and dynamic visualization scripts (`js/charts.js`).
- **`ui/`**: Modular interactive view components (client intake, dashboard, proposal view, audit view, backtest view).
- **`app.py`**: Streamlit interactive client application connecting directly to the wealth advisory pipeline.
- **`public/`**: Public static assets.

## 🚀 Running the Frontend UI

To launch the Streamlit advisory interface:
```bash
streamlit run frontend/app.py
```

Or access the full portal via the unified backend server on `http://localhost:5000`.
