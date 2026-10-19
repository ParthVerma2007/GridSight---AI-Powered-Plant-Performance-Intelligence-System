import re
import math
import json
from datetime import datetime, timezone
from typing import Dict, Any, Tuple, Optional, List
import pandas as pd
from app.config import settings

class DataValidator:
    """
    Normalizes timestamps, units, and asset IDs.
    Validates data types and schema constraints.
    Detects duplicates and invalid values without silent dropping.
    """

    @staticmethod
    def normalize_timestamp(raw_val: Any) -> Tuple[Optional[datetime], Optional[str]]:
        """
        Normalizes various timestamp formats into a timezone-aware UTC datetime.
        Returns (normalized_datetime, error_message).
        """
        if raw_val is None or pd.isna(raw_val) or str(raw_val).strip() == "":
            return None, "Timestamp is missing or null"
        
        raw_str = str(raw_val).strip()
        
        # Check if numeric epoch timestamp
        try:
            if raw_str.replace(".", "", 1).isdigit():
                num = float(raw_str)
                # If milliseconds (e.g. 1700000000000)
                if num > 1e11:
                    num /= 1000.0
                return datetime.fromtimestamp(num, tz=timezone.utc).replace(tzinfo=None), None
        except Exception:
            pass

        # Try pandas to_datetime which handles ISO 8601, 'YYYY-MM-DD HH:MM:SS', etc.
        try:
            dt = pd.to_datetime(raw_str, utc=True)
            if pd.isna(dt):
                return None, f"Could not parse timestamp '{raw_str}'"
            # Return naive UTC datetime for database compatibility
            return dt.tz_convert(None).to_pydatetime(), None
        except Exception as e:
            return None, f"Invalid timestamp format '{raw_str}': {str(e)}"

    @staticmethod
    def normalize_asset_id(raw_val: Any) -> Tuple[Optional[str], Optional[str]]:
        """
        Standardizes asset IDs (e.g., 'inv04', 'INV_04', 'inverter-4' -> 'INV-04').
        """
        if raw_val is None or pd.isna(raw_val) or str(raw_val).strip() == "":
            return None, None  # Asset ID can be optional for plant-level records
        
        raw_str = str(raw_val).strip().upper()
        # Inverter pattern matching
        m = re.match(r'^(?:INV|INVERTER)[-_ ]*0*(\d+)$', raw_str)
        if m:
            num = int(m.group(1))
            return f"INV-{num:02d}", None
        
        # Pyranometer / Weather station pattern
        if "PYR" in raw_str or "MET" in raw_str or "WEATHER" in raw_str:
            return "MET-01", None
            
        # Transformer
        m_tx = re.match(r'^(?:TX|TRANSFORMER)[-_ ]*0*(\d+)$', raw_str)
        if m_tx:
            return f"TX-{int(m_tx.group(1)):02d}", None
            
        # Default cleaned string
        cleaned = re.sub(r'[^A-Z0-9_-]', '', raw_str)
        return cleaned, None

    @staticmethod
    def normalize_float(raw_val: Any, field_name: str, min_val: Optional[float] = None, max_val: Optional[float] = None, unit_from: Optional[str] = None, unit_to: Optional[str] = None) -> Tuple[Optional[float], Optional[str]]:
        """
        Parses float and handles unit conversions (e.g. kW to MW, W/m2, etc.).
        Crucially: does NOT convert None or missing to zero!
        """
        if raw_val is None or pd.isna(raw_val) or str(raw_val).strip() == "":
            return None, f"Missing required numerical value for {field_name}"
        
        try:
            val = float(raw_val)
        except (ValueError, TypeError):
            return None, f"Malformed non-numeric value '{raw_val}' for {field_name}"
            
        if math.isnan(val) or math.isinf(val):
            return None, f"Invalid numeric value (NaN or Inf) for {field_name}"
            
        # Unit conversion
        if unit_from == "kw" and unit_to == "mw":
            val = val / 1000.0
        elif unit_from == "kwh" and unit_to == "mwh":
            val = val / 1000.0
        elif unit_from == "w" and unit_to == "mw":
            val = val / 1_000_000.0
        elif unit_from == "deg_f" and unit_to == "deg_c":
            val = (val - 32.0) * 5.0 / 9.0

        # Range checks
        if min_val is not None and val < min_val:
            return None, f"Value {val} for {field_name} is below minimum allowed {min_val}"
        if max_val is not None and val > max_val:
            return None, f"Value {val} for {field_name} exceeds maximum allowed {max_val}"

        return round(val, 4), None
