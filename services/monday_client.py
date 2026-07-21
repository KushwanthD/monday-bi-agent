"""
Monday.com GraphQL API Client with High-Performance In-Memory Caching.
Connects dynamically to Monday.com v2 API with read-only Bearer token authentication.
Caches board data with a 15-second TTL to ensure sub-millisecond tab switching and lightning-fast page loads.
"""

import os
import csv
import json
import time
import urllib.request
import urllib.error

class MondayClient:
    def __init__(self):
        self.api_url = "https://api.monday.com/v2"
        self.api_token = os.getenv("MONDAY_API_TOKEN", os.getenv("MONDAY_API_KEY", "")).strip()
        self.work_orders_board_id = os.getenv("MONDAY_WORK_ORDERS_BOARD_ID", "").strip()
        self.deals_board_id = os.getenv("MONDAY_DEALS_BOARD_ID", "").strip()
        self.sample_dir = os.path.join(os.path.dirname(__file__), "..", "sample_data")

        # In-Memory Cache (15s TTL)
        self._cache = None
        self._cache_time = 0
        self._cache_ttl = 15  # seconds

        # Load config.json if present
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if cfg.get("monday_api_key"):
                        self.api_token = cfg["monday_api_key"].strip()
                    if cfg.get("deals_board_id"):
                        self.deals_board_id = cfg["deals_board_id"].strip()
                    if cfg.get("work_orders_board_id"):
                        self.work_orders_board_id = cfg["work_orders_board_id"].strip()
            except Exception as e:
                print(f"[MondayClient Config Warning] {e}")

    def is_configured(self) -> bool:
        return bool(self.api_token)

    def execute_query(self, query: str, variables: dict = None) -> dict:
        """Executes a GraphQL query against Monday.com API securely with timeout"""
        if not self.api_token:
            raise ValueError("Monday.com API Token is not configured.")

        payload = json.dumps({"query": query, "variables": variables or {}}).encode("utf-8")
        headers = {
            "Authorization": self.api_token,
            "Content-Type": "application/json",
            "API-Version": "2023-10"
        }

        req = urllib.request.Request(self.api_url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = response.read().decode("utf-8")
                return json.loads(res_body)
        except urllib.error.HTTPError as e:
            err_msg = e.read().decode("utf-8")
            raise Exception(f"Monday API HTTP Error {e.code}: {err_msg}")
        except Exception as e:
            raise Exception(f"Monday API Request Failed: {str(e)}")

    def fetch_all_workspace_boards(self, force_refresh: bool = False) -> list:
        """Fetches ALL boards and internal Groups with sub-millisecond 15s in-memory caching"""
        now = time.time()
        if not force_refresh and self._cache is not None and (now - self._cache_time) < self._cache_ttl:
            return self._cache

        if not self.is_configured():
            return []

        query = """
        query {
          boards {
            id
            name
            groups {
              id
              title
            }
            columns {
              id
              title
            }
            items_page(limit: 500) {
              items {
                id
                name
                group {
                  id
                  title
                }
                column_values {
                  id
                  text
                }
              }
            }
          }
        }
        """
        try:
            data = self.execute_query(query)
            boards_data = data.get("data", {}).get("boards", [])
            result_boards = []

            for board in boards_data:
                b_id = board.get("id")
                b_name = board.get("name", "Unnamed Board")
                b_groups = board.get("groups", [])
                column_title_map = {col["id"]: col["title"] for col in board.get("columns", [])}
                raw_items = board.get("items_page", {}).get("items", [])
                
                parsed_items = []
                for item in raw_items:
                    item_name = item.get("name", "")
                    grp_title = item.get("group", {}).get("title", "Main Group")
                    grp_id = item.get("group", {}).get("id", "main")

                    row = {
                        "Deal Name": item_name,
                        "Deal name masked": item_name,
                        "Project Name": item_name,
                        "group_title": grp_title,
                        "group_id": grp_id
                    }
                    for cv in item.get("column_values", []):
                        col_id = cv.get("id")
                        col_title = column_title_map.get(col_id, col_id)
                        col_text = cv.get("text", "")
                        row[col_title] = col_text
                        row[col_id] = col_text
                    parsed_items.append(row)

                result_boards.append({
                    "id": b_id,
                    "name": b_name,
                    "groups": b_groups,
                    "items_count": len(parsed_items),
                    "items": parsed_items
                })

            self._cache = result_boards
            self._cache_time = now
            return result_boards
        except Exception as e:
            print(f"[MondayClient Warning] fetch_all_workspace_boards failed: {e}")
            if self._cache is not None:
                return self._cache
            return []

    def load_deals_data(self) -> list:
        """Loads Deals data from cached API if configured, else fallback to official CSV dataset"""
        if self.is_configured():
            try:
                boards = self.fetch_all_workspace_boards()
                deals_items = []
                for b in boards:
                    for item in b["items"]:
                        grp = item.get("group_title", "").lower()
                        if "deal" in grp or "funnel" in grp:
                            deals_items.append(item)
                if deals_items:
                    return deals_items
            except Exception as e:
                print(f"[MondayClient Warning] Deals API query failed ({e}). Using official local dataset.")

        filepath = os.path.join(self.sample_dir, "Deal_funnel_Data.csv")
        if os.path.exists(filepath):
            with open(filepath, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                return [dict(row) for row in reader]
        return []

    def load_work_orders_data(self) -> list:
        """Loads Work Orders data from cached API if configured, else fallback to official CSV dataset"""
        if self.is_configured():
            try:
                boards = self.fetch_all_workspace_boards()
                order_items = []
                for b in boards:
                    for item in b["items"]:
                        grp = item.get("group_title", "").lower()
                        if "work" in grp or "order" in grp or "tracker" in grp:
                            order_items.append(item)
                if order_items:
                    return order_items
            except Exception as e:
                print(f"[MondayClient Warning] Work Orders API query failed ({e}). Using official local dataset.")

        filepath = os.path.join(self.sample_dir, "Work_Order_Tracker_Data.csv")
        if os.path.exists(filepath):
            with open(filepath, mode="r", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                return [dict(row) for row in reader]
        return []
