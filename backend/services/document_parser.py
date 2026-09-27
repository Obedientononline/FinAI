"""Document Parser and Ingestion Pipeline for Client Profiling.

Supports extracting KYC (Know Your Customer) and IPS (Investment Policy Statement)
parameters as well as portfolio holdings from:
- PDF (.pdf)
- Microsoft Word (.docx)
- Microsoft Excel (.xlsx, .xls)
- CSV (.csv)
- JSON (.json)
"""
import os
import re
import json
from datetime import date
from typing import Dict, Any, Tuple, List, Optional

import pandas as pd
from models.client_profile import ClientProfile, KYC, IPS
from models.portfolio import Portfolio, Position
import config


def _clean_number(val_str: str) -> float:
    """Extract numeric float from string with currency symbols, commas, or Lakh/Crore notation."""
    if isinstance(val_str, (int, float)):
        return float(val_str)
    if not val_str:
        return 0.0

    s = str(val_str).strip().replace(",", "").replace("₹", "").replace("Rs.", "").replace("Rs", "").replace("$", "")
    
    # Handle Lakh / Crore multipliers
    multiplier = 1.0
    lower_s = s.lower()
    if "crore" in lower_s or "cr" in lower_s:
        multiplier = 10000000.0
        s = re.sub(r'(?i)(crore|cr)', '', s)
    elif "lakh" in lower_s or "lac" in lower_s or "l" in lower_s:
        multiplier = 100000.0
        s = re.sub(r'(?i)(lakh|lac|l)', '', s)
    elif "k" in lower_s:
        multiplier = 1000.0
        s = re.sub(r'(?i)k', '', s)

    match = re.search(r"[-+]?\d*\.?\d+", s)
    if match:
        try:
            return float(match.group()) * multiplier
        except ValueError:
            return 0.0
    return 0.0


def _clean_pct(val_str: str) -> float:
    """Extract percentage as decimal e.g. '30%' -> 0.30 or '0.30' -> 0.30."""
    if isinstance(val_str, (int, float)):
        return float(val_str) if val_str <= 1.0 else float(val_str) / 100.0
    s = str(val_str).strip().replace("%", "")
    val = _clean_number(s)
    if val > 1.0:
        return val / 100.0
    return val


def parse_text_key_values(text: str) -> Dict[str, Any]:
    """Extract profile fields from unstructured or semi-structured text via regex heuristics."""
    data = {}
    lines = text.splitlines()

    # Field pattern mappings
    patterns = {
        "name": [r"(?:client\s+)?name\s*[:=\-]\s*([^\n\r,]+)", r"full\s+name\s*[:=\-]\s*([^\n\r,]+)"],
        "client_id": [r"client\s*id\s*[:=\-]\s*([A-Za-z0-9\-_]+)", r"account\s*(?:no|id|number)\s*[:=\-]\s*([A-Za-z0-9\-_]+)"],
        "age": [r"age\s*[:=\-]\s*(\d{1,3})", r"client\s+age\s*[:=\-]\s*(\d{1,3})"],
        "annual_income": [r"(?:annual\s+)?income\s*[:=\-]\s*([^\n\r;]+)", r"salary\s*[:=\-]\s*([^\n\r;]+)"],
        "net_worth": [r"(?:investable\s+)?net\s*worth\s*[:=\-]\s*([^\n\r;]+)", r"total\s+wealth\s*[:=\-]\s*([^\n\r;]+)", r"aum\s*[:=\-]\s*([^\n\r;]+)"],
        "experience": [r"(?:investment\s+)?experience\s*[:=\-]\s*([^\n\r,;]+)"],
        "employment": [r"employment(?:\s+status)?\s*[:=\-]\s*([^\n\r,;]+)", r"occupation\s*[:=\-]\s*([^\n\r,;]+)"],
        "dependents": [r"dependents?\s*[:=\-]\s*(\d+)", r"no(?:\.|\s+of)?\s+dependents\s*[:=\-]\s*(\d+)"],
        "objective": [r"(?:investment\s+)?objective\s*[:=\-]\s*([^\n\r,;]+)", r"goal\s*[:=\-]\s*([^\n\r,;]+)"],
        "tolerance": [r"(?:risk\s+)?tolerance\s*[:=\-]\s*([^\n\r,;]+)", r"risk\s+profile\s*[:=\-]\s*([^\n\r,;]+)"],
        "horizon": [r"(?:time\s+)?horizon(?:\s*\(?years?\)?)?\s*[:=\-]\s*(\d+)", r"investment\s+duration\s*[:=\-]\s*(\d+)"],
        "liquidity": [r"liquidity(?:\s+needs?)?\s*[:=\-]\s*([^\n\r,;]+)"],
        "tax_bracket": [r"tax\s*(?:bracket|rate)\s*[:=\-]\s*([^\n\r,;]+)"],
        "restrictions": [r"(?:ips\s+)?restrictions?\s*[:=\-]\s*([^\n\r;]+)", r"negative\s*screens?\s*[:=\-]\s*([^\n\r;]+)"],
        "max_position": [r"max(?:imum)?\s*(?:single\s+)?position\s*[:=\-]\s*([^\n\r,;]+)"],
    }

    for key, regex_list in patterns.items():
        for reg in regex_list:
            match = re.search(reg, text, re.IGNORECASE)
            if match:
                data[key] = match.group(1).strip()
                break

    return data


def extract_from_image_ocr(filepath: str) -> str:
    """Extract text from scanned image/document using Windows Native OCR or Tesseract on Linux."""
    try:
        from PIL import Image
        img = Image.open(filepath)
        # 1. Try Windows native OCR
        try:
            import winocr
            result = winocr.recognize_pil_sync(img, lang="en")
            if isinstance(result, dict) and "lines" in result and result["lines"]:
                return "\n".join([line.get("text", "").strip() for line in result.get("lines", [])])
            elif isinstance(result, dict) and "text" in result:
                return result["text"]
            elif hasattr(result, "text"):
                return str(result.text)
        except Exception:
            pass

        # 2. Try pytesseract (standard on Linux / Docker)
        try:
            import pytesseract
            return pytesseract.image_to_string(img)
        except Exception:
            pass

        return ""
    except Exception as e:
        print(f"[OCR_PARSE_ERR] {e}")
        return ""


def extract_from_pdf(filepath: str) -> Tuple[str, List[List[str]]]:
    """Extract plain text and any detected tables from a PDF, with OCR fallback for scans."""
    full_text = []
    tables = []

    try:
        import pdfplumber
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                txt = page.extract_text()
                if txt:
                    full_text.append(txt)
                tbls = page.extract_tables()
                if tbls:
                    for t in tbls:
                        tables.extend(t)
    except Exception:
        # Fallback to pypdf
        try:
            import pypdf
            reader = pypdf.PdfReader(filepath)
            for page in reader.pages:
                txt = page.extract_text()
                if txt:
                    full_text.append(txt)
        except Exception as e:
            print(f"[PDF_PARSE_ERR] {e}")

    extracted_str = "\n".join(full_text)

    # Scanned PDF OCR fallback if no embedded text found
    if len(extracted_str.strip()) < 30:
        try:
            import pypdfium2 as pdfium
            import winocr
            pdf = pdfium.PdfDocument(filepath)
            ocr_parts = []
            for i in range(min(len(pdf), 3)): # Scan first 3 pages
                page = pdf[i]
                pil_image = page.render(scale=2.0).to_pil()
                res = winocr.recognize_pil_sync(pil_image, lang="en")
                if isinstance(res, dict) and "text" in res:
                    ocr_parts.append(res["text"])
                elif hasattr(res, "text"):
                    ocr_parts.append(str(res.text))
            if ocr_parts:
                extracted_str = "\n".join(ocr_parts)
        except Exception as ocr_err:
            print(f"[PDF_OCR_FALLBACK_ERR] {ocr_err}")

    return extracted_str, tables


def extract_from_docx(filepath: str) -> Tuple[str, List[List[str]]]:
    """Extract plain text and table cells from a .docx file."""
    import docx
    doc = docx.Document(filepath)
    text_parts = [p.text for p in doc.paragraphs if p.text.strip()]
    
    tables_data = []
    for table in doc.tables:
        for row in table.rows:
            row_vals = [cell.text.strip() for cell in row.cells]
            tables_data.append(row_vals)
            if len(row_vals) >= 2:
                text_parts.append(f"{row_vals[0]}: {row_vals[1]}")

    return "\n".join(text_parts), tables_data


def extract_from_excel(filepath: str) -> Tuple[str, Dict[str, Any]]:
    """Extract key-values and tables from an Excel file using openpyxl directly."""
    text_parts = []
    tables = {}

    try:
        import openpyxl
        wb = openpyxl.load_workbook(filepath, data_only=True)
        for sheet_name in wb.sheetnames:
            ws = wb[sheet_name]
            sheet_rows = []
            for row in ws.iter_rows(values_only=True):
                non_empty = [str(c).strip() for c in row if c is not None and str(c).strip()]
                if not non_empty:
                    continue
                sheet_rows.append(non_empty)
                if len(non_empty) >= 2:
                    text_parts.append(f"{non_empty[0]}: {non_empty[1]}")
                elif len(non_empty) == 1:
                    text_parts.append(non_empty[0])
            tables[sheet_name] = sheet_rows
    except Exception as e:
        print(f"[EXCEL_PARSE_ERR] {e}")

    return "\n".join(text_parts), tables


def build_profile_from_parsed(extracted: Dict[str, Any], default_id: Optional[str] = None) -> ClientProfile:
    """Build a strongly typed, validated ClientProfile from extracted dictionary values."""
    from engine.risk_scorer import compute_risk_score

    name = extracted.get("name") or "New Client"
    cid = extracted.get("client_id") or default_id or f"C-{date.today().strftime('%Y%m%d')}-{abs(hash(name)) % 1000:03d}"
    
    # KYC
    age = int(_clean_number(extracted.get("age", 40)))
    if age < 18: age = 40
    income = _clean_number(extracted.get("annual_income", 1500000))
    net_worth = _clean_number(extracted.get("net_worth", 10000000))
    
    exp_raw = str(extracted.get("experience", "experienced")).lower().strip()
    if "soph" in exp_raw:
        experience = "sophisticated"
    elif "lim" in exp_raw:
        experience = "limited"
    elif "none" in exp_raw:
        experience = "none"
    else:
        experience = "experienced"

    emp_status = extracted.get("employment", "Employed")
    dependents = int(_clean_number(extracted.get("dependents", 1)))

    kyc = KYC(
        age=age,
        annual_income=income,
        net_worth=net_worth,
        investment_experience=experience,
        employment_status=emp_status,
        dependents=dependents
    )

    # IPS
    obj_raw = str(extracted.get("objective", "growth_and_income")).lower().replace(" ", "_")
    if "cap" in obj_raw or "pres" in obj_raw:
        objective = "capital_preservation"
    elif "income" in obj_raw and "growth" not in obj_raw:
        objective = "income"
    elif "growth" in obj_raw and "income" in obj_raw:
        objective = "growth_and_income"
    else:
        objective = "growth"

    tol_raw = str(extracted.get("tolerance", "moderate")).lower().replace(" ", "_").replace("-", "_")
    if "cons" in tol_raw and "mod" not in tol_raw:
        tolerance = "conservative"
    elif "mod_cons" in tol_raw or "moderate_conservative" in tol_raw:
        tolerance = "moderate_conservative"
    elif "agg" in tol_raw and "mod" not in tol_raw:
        tolerance = "aggressive"
    elif "mod_agg" in tol_raw or "moderate_aggressive" in tol_raw:
        tolerance = "moderate_aggressive"
    else:
        tolerance = "moderate"

    horizon = int(_clean_number(extracted.get("horizon", 10)))
    if horizon < 1: horizon = 10

    liq_raw = str(extracted.get("liquidity", "low")).lower()
    if "high" in liq_raw:
        liquidity = "high"
    elif "mod" in liq_raw:
        liquidity = "moderate"
    else:
        liquidity = "low"

    tax_bracket = _clean_pct(extracted.get("tax_bracket", 0.30))
    if tax_bracket <= 0: tax_bracket = 0.30

    max_pos = _clean_pct(extracted.get("max_position", 0.10))
    if max_pos <= 0: max_pos = 0.10

    # Restrictions
    restrictions_raw = extracted.get("restrictions", "")
    restrictions = []
    if isinstance(restrictions_raw, list):
        restrictions = restrictions_raw
    elif isinstance(restrictions_raw, str) and restrictions_raw.strip():
        for r in re.split(r"[,;/\n]+", restrictions_raw):
            clean_r = r.strip().lower().replace(" ", "_")
            if clean_r:
                if not clean_r.startswith("no_"):
                    clean_r = f"no_{clean_r}"
                restrictions.append(clean_r)

    ips = IPS(
        investment_objective=objective,
        risk_tolerance=tolerance,
        time_horizon_years=horizon,
        liquidity_needs=liquidity,
        tax_bracket=tax_bracket,
        restrictions=restrictions,
        max_single_position_pct=max_pos,
        rebalance_threshold_pct=0.05
    )

    score, category, _ = compute_risk_score(kyc, ips)

    return ClientProfile(
        client_id=cid,
        name=name,
        ips=ips,
        kyc=kyc,
        risk_score=score,
        risk_category=category
    )


def build_default_portfolio_for_client(profile: ClientProfile) -> Portfolio:
    """Generate a realistic starting holdings portfolio in INR aligned with client Net Worth."""
    nw = profile.kyc.net_worth if profile.kyc.net_worth > 500000 else 5000000.0
    
    # 8 standard holdings calibrated in INR
    positions = [
        Position(symbol="SPY", shares=round((nw * 0.30) / 45000, 1), cost_basis_per_share=40000.0, current_price=45250.0, holding_period_days=400, asset_class="equities"),
        Position(symbol="AGG", shares=round((nw * 0.25) / 8400, 1), cost_basis_per_share=8200.0, current_price=8400.0, holding_period_days=300, asset_class="fixed_income"),
        Position(symbol="GLD", shares=round((nw * 0.10) / 19300, 1), cost_basis_per_share=18000.0, current_price=19300.0, holding_period_days=250, asset_class="commodities"),
        Position(symbol="AAPL", shares=round((nw * 0.12) / 16200, 1), cost_basis_per_share=14500.0, current_price=16250.0, holding_period_days=380, asset_class="equities"),
        Position(symbol="MSFT", shares=round((nw * 0.10) / 34500, 1), cost_basis_per_share=31000.0, current_price=34500.0, holding_period_days=200, asset_class="equities"),
        Position(symbol="BND", shares=round((nw * 0.05) / 6150, 1), cost_basis_per_share=6000.0, current_price=6150.0, holding_period_days=500, asset_class="fixed_income"),
        Position(symbol="CASH", shares=round(nw * 0.08, 0), cost_basis_per_share=1.0, current_price=1.0, holding_period_days=90, asset_class="cash"),
    ]
    return Portfolio(positions=positions)


def ingest_client_document(filepath: str) -> Tuple[ClientProfile, Portfolio, Dict[str, Any]]:
    """Master ingestion function that reads any uploaded file and returns (ClientProfile, Portfolio, Telemetry)."""
    ext = os.path.splitext(filepath)[1].lower()
    raw_text = ""
    extracted_fields = {}

    if ext == ".pdf":
        raw_text, tables = extract_from_pdf(filepath)
        extracted_fields = parse_text_key_values(raw_text)
    elif ext in [".docx", ".doc"]:
        raw_text, tables = extract_from_docx(filepath)
        extracted_fields = parse_text_key_values(raw_text)
    elif ext in [".xlsx", ".xls"]:
        raw_text, dfs = extract_from_excel(filepath)
        extracted_fields = parse_text_key_values(raw_text)
    elif ext == ".csv":
        df = pd.read_csv(filepath)
        for _, row in df.iterrows():
            if len(row) >= 2:
                raw_text += f"\n{row.iloc[0]}: {row.iloc[1]}"
        extracted_fields = parse_text_key_values(raw_text)
    elif ext == ".json":
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, dict):
                extracted_fields = data
                raw_text = json.dumps(data, indent=2)
    elif ext in [".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".webp"]:
        raw_text = extract_from_image_ocr(filepath)
        extracted_fields = parse_text_key_values(raw_text)
    else:
        # Fallback to plain text read
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            raw_text = f.read()
            extracted_fields = parse_text_key_values(raw_text)

    # Build validated profile
    profile = build_profile_from_parsed(extracted_fields)
    portfolio = build_default_portfolio_for_client(profile)

    telemetry = {
        "file_name": os.path.basename(filepath),
        "file_type": ext,
        "raw_text_length": len(raw_text),
        "extracted_fields_count": len(extracted_fields),
        "extracted_fields": extracted_fields,
    }

    return profile, portfolio, telemetry
