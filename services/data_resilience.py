"""
Data Resilience & Sanitization Engine
Handles real-world messy data from Skylark Drones official datasets:
missing values, date format normalization, text/casing unification, and data quality warnings.
"""

import re
from datetime import datetime

class DataResilienceEngine:
    def __init__(self):
        self.sector_aliases = {
            "energy": "Energy",
            "energy sector": "Energy",
            "powerline": "Energy",
            "renewables": "Energy",
            "mining": "Mining",
            "infrastructure": "Infrastructure",
            "construction": "Infrastructure",
            "railways": "Infrastructure",
            "agriculture": "Agriculture",
            "dsp": "DSP",
            "tender": "Tender"
        }

    def clean_currency(self, val) -> tuple[float, bool]:
        """Parses currency strings like '₹120,000', '489360', '', returning (amount, is_valid)"""
        if val is None:
            return 0.0, False
        val_str = str(val).strip().replace("₹", "").replace("$", "").replace(",", "").replace("Rs.", "")
        if not val_str or val_str.upper() in ["#VALUE!", "NA", "N/A", "NONE", "-"]:
            return 0.0, False
        try:
            return float(val_str), True
        except ValueError:
            return 0.0, False

    def normalize_sector(self, sector_str: str) -> str:
        """Normalizes sector text casing and synonyms"""
        if not sector_str or str(sector_str).strip() in ["", "Others"]:
            return "General Industry"
        cleaned = str(sector_str).strip().lower()
        for alias, canonical in self.sector_aliases.items():
            if alias in cleaned:
                return canonical
        return sector_str.strip().capitalize()

    def normalize_date(self, date_str: str) -> tuple[str, bool]:
        """Normalizes various date formats to YYYY-MM-DD"""
        if not date_str or not str(date_str).strip():
            return "Unspecified Date", False
            
        ds = str(date_str).strip()
        formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%m-%d-%Y",
            "%b %d %Y",
            "%B %d %Y"
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(ds, fmt)
                return dt.strftime("%Y-%m-%d"), True
            except ValueError:
                continue
                
        match = re.search(r'20\d{2}', ds)
        if match:
            return f"{match.group(0)}-01-01", True
            
        return ds, False

    def process_deals(self, raw_deals: list) -> tuple[list, list]:
        """Cleans Deals list from official CSV / GraphQL and returns (cleaned_deals, quality_caveats)"""
        cleaned = []
        caveats = []
        missing_values_count = 0
        date_issues_count = 0

        for idx, item in enumerate(raw_deals):
            deal_name = (item.get("Deal Name") or item.get("deal_name") or f"Deal-{idx+1}").strip()
            client = (item.get("Client Code") or item.get("Client Name") or item.get("Client") or "Unknown Client").strip()
            
            raw_sector = item.get("Sector/service") or item.get("Sector") or ""
            sector = self.normalize_sector(raw_sector)
            
            raw_val = item.get("Masked Deal value") or item.get("Deal Value ($)") or item.get("Value") or ""
            val, val_valid = self.clean_currency(raw_val)
            if not val_valid:
                missing_values_count += 1
                
            stage = (item.get("Deal Stage") or item.get("Deal Status") or item.get("Pipeline Stage") or "Open").strip()
            deal_status = (item.get("Deal Status") or "Open").strip()
            
            raw_date = item.get("Close Date (A)") or item.get("Tentative Close Date") or item.get("Expected Close Date") or ""
            close_date, date_valid = self.normalize_date(raw_date)
            if not date_valid and raw_date:
                date_issues_count += 1
                
            owner = (item.get("Owner code") or item.get("Deal Owner") or "Unassigned").strip()
            
            cleaned.append({
                "deal_id": f"D-{idx+100}",
                "deal_name": deal_name,
                "client": client,
                "sector": sector,
                "value": val,
                "val_is_valid": val_valid,
                "stage": stage,
                "deal_status": deal_status,
                "close_date": close_date,
                "owner": owner
            })

        if missing_values_count > 0:
            caveats.append(f"⚠️ {missing_values_count} deal(s) contained missing or unquantified values and were defaulted to ₹0.00.")
        if date_issues_count > 0:
            caveats.append(f"🗓️ {date_issues_count} deal close date(s) were normalized to standard date format.")
            
        return cleaned, caveats

    def process_work_orders(self, raw_orders: list) -> tuple[list, list]:
        """Cleans Work Orders list from official CSV / GraphQL and returns (cleaned_orders, quality_caveats)"""
        cleaned = []
        caveats = []
        missing_costs_count = 0

        for idx, item in enumerate(raw_orders):
            wo_id = (item.get("Serial #") or item.get("Work Order ID") or f"WO-{idx+500}").strip()
            deal_name = (item.get("Deal name masked") or item.get("Project Name") or item.get("Deal Name") or "Unnamed Project").strip()
            client = (item.get("Customer Name Code") or item.get("Client") or "Unknown Client").strip()
            sector = self.normalize_sector(item.get("Sector") or "")
            status = (item.get("Execution Status") or item.get("Flight Status") or "Ongoing").strip()
            pilots = (item.get("BD/KAM Personnel code") or item.get("Pilots Assigned") or "Unassigned").strip()
            
            start_date, _ = self.normalize_date(item.get("Probable Start Date") or item.get("Start Date") or "")
            comp_date, comp_valid = self.normalize_date(item.get("Data Delivery Date") or item.get("Probable End Date") or "")
            
            raw_cost = item.get("Amount in Rupees (Excl of GST) (Masked)") or item.get("Billed Value in Rupees (Excl of GST.) (Masked)") or item.get("Operational Cost ($)") or ""
            cost, cost_valid = self.clean_currency(raw_cost)
            if not cost_valid and raw_cost != "":
                missing_costs_count += 1
                
            deliverables = (item.get("WO Status (billed)") or item.get("Billing Status") or item.get("Deliverables Status") or "Pending").strip()

            cleaned.append({
                "work_order_id": wo_id,
                "deal_id": wo_id,
                "project_name": deal_name,
                "client": client,
                "sector": sector,
                "status": status,
                "pilots": pilots,
                "start_date": start_date,
                "completion_date": comp_date if comp_valid else "In Progress",
                "cost": cost,
                "deliverables": deliverables
            })

        if missing_costs_count > 0:
            caveats.append(f"⚠️ {missing_costs_count} work order(s) contained unbilled or masked financial amounts.")
            
        return cleaned, caveats
