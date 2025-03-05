import configparser
import psycopg2
import pandas as pd
import requests
from azure.core.credentials import AzureKeyCredential
import json

def safe_float(val):
    """Try to convert a value to float; return None if conversion fails."""
    try:
        if val is None or val == "":
            return None
        return float(val)
    except (ValueError, TypeError):
        return None


def normalize_basic_info(data: dict) -> dict:
    """
    Normalize basic_info data from different sources to a common structure.
    The common structure contains the following keys:
      - orientation
      - BuildingArea
      - LandArea
      - ManagementFee
      - PropertyType
      - PublicArea
      - AuxiliaryBuildingArea

    For the buyRakuya site, we consider:
      - "direction" for orientation.
      - "mainSize" for BuildingArea.
      - "shareSize" for LandArea.
      - "manageFee" for ManagementFee.
      - "itemUseType" for PropertyType.
      - "subSize" for AuxiliaryBuildingArea.
    """
    result = {
        "orientation": None,
        "BuildingArea": None,
        "LandArea": None,
        "ManagementFee": None,
        "PropertyType": None,
        "PublicArea": None,
        "AuxiliaryBuildingArea": None
    }
    # Orientation: prioritize buyRakuya's "direction"
    if "direction" in data and data.get("direction"):
        result["orientation"] = data.get("direction")
    elif "座向" in data and data.get("座向"):
        result["orientation"] = data.get("座向")
    elif "朝向" in data and data.get("朝向"):
        result["orientation"] = data.get("朝向")
    elif "大門朝向" in data and data.get("大門朝向"):
        result["orientation"] = data.get("大門朝向")

    # BuildingArea: use buyRakuya's "mainSize" if available
    if "mainSize" in data and data.get("mainSize"):
        result["BuildingArea"] = data.get("mainSize")
    elif "主建物" in data and data.get("主建物"):
        result["BuildingArea"] = data.get("主建物")
    elif "建坪" in data and data.get("建坪"):
        result["BuildingArea"] = data.get("建坪")

    # LandArea: use buyRakuya's "shareSize" if available
    if "shareSize" in data and data.get("shareSize"):
        result["LandArea"] = data.get("shareSize")
    elif "土地" in data and data.get("土地"):
        result["LandArea"] = data.get("土地")
    elif "土地坪數" in data and data.get("土地坪數"):
        result["LandArea"] = data.get("土地坪數")
    elif "地坪" in data and data.get("地坪"):
        result["LandArea"] = data.get("地坪")

    # ManagementFee: use buyRakuya's "manageFee" if available
    if "manageFee" in data and data.get("manageFee"):
        result["ManagementFee"] = data.get("manageFee")
    elif "管理費" in data and data.get("管理費"):
        result["ManagementFee"] = data.get("管理費")

    # PropertyType: use buyRakuya's "itemUseType" if available
    if "itemUseType" in data and data.get("itemUseType"):
        result["PropertyType"] = data.get("itemUseType")
    elif "型態" in data and data.get("型態"):
        result["PropertyType"] = data.get("型態")
    elif "法定用途" in data and data.get("法定用途"):
        result["PropertyType"] = data.get("法定用途")
    elif "類型" in data and data.get("類型"):
        result["PropertyType"] = data.get("類型")

    # PublicArea: use common keys if available
    if "公設比" in data and data.get("公設比") and data.get("公設比") != "--":
        result["PublicArea"] = data.get("公設比")
    elif "共同使用" in data and data.get("共同使用"):
        result["PublicArea"] = data.get("共同使用")
    elif "公共設施" in data and data.get("公共設施"):
        result["PublicArea"] = data.get("公共設施")

    # AuxiliaryBuildingArea: use buyRakuya's "subSize" if available
    if "subSize" in data and data.get("subSize"):
        result["AuxiliaryBuildingArea"] = data.get("subSize")
    elif "附屬建物" in data and data.get("附屬建物"):
        result["AuxiliaryBuildingArea"] = data.get("附屬建物")

    return result


def safe_float(val):
    """Attempts to convert a value to float; returns None if conversion fails."""
    try:
        if val is None or str(val).strip() == "":
            return None
        return float(val)
    except (ValueError, TypeError):
        return None


def load_json_field(field, row):
    raw = row.get(field)
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except Exception:
            return {}
    elif isinstance(raw, dict) or isinstance(raw, list):
        return raw
    else:
        return {}


def normalize_basic_info(data: dict) -> dict:
    result = {
        "orientation": None,
        "BuildingArea": None,
        "LandArea": None,
        "ManagementFee": None,
        "PropertyType": None,
        "PublicArea": None,
        "AuxiliaryBuildingArea": None
    }
    if "座向" in data and data.get("座向"):
        result["orientation"] = data.get("座向")
    elif "朝向" in data and data.get("朝向"):
        result["orientation"] = data.get("朝向")
    elif "大門朝向" in data and data.get("大門朝向"):
        result["orientation"] = data.get("大門朝向")
    if "主建物" in data and data.get("主建物"):
        result["BuildingArea"] = data.get("主建物")
    elif "建坪" in data and data.get("建坪"):
        result["BuildingArea"] = data.get("建坪")
    if "土地" in data and data.get("土地"):
        result["LandArea"] = data.get("土地")
    elif "土地坪數" in data and data.get("土地坪數"):
        result["LandArea"] = data.get("土地坪數")
    elif "地坪" in data and data.get("地坪"):
        result["LandArea"] = data.get("地坪")
    if "管理費" in data and data.get("管理費"):
        result["ManagementFee"] = data.get("管理費")
    if "型態" in data and data.get("型態"):
        result["PropertyType"] = data.get("型態")
    elif "法定用途" in data and data.get("法定用途"):
        result["PropertyType"] = data.get("法定用途")
    elif "類型" in data and data.get("類型"):
        result["PropertyType"] = data.get("類型")
    if "公設比" in data and data.get("公設比") and data.get("公設比") != "--":
        result["PublicArea"] = data.get("公設比")
    elif "共同使用" in data and data.get("共同使用"):
        result["PublicArea"] = data.get("共同使用")
    elif "公共設施" in data and data.get("公共設施"):
        result["PublicArea"] = data.get("公共設施")
    if "附屬建物" in data and data.get("附屬建物"):
        result["AuxiliaryBuildingArea"] = data.get("附屬建物")
    return result

def normalize_life_info(raw) -> list:
    normalized = []
    if isinstance(raw, dict):
        # 乐屋网 format: dict with keys like "avoid", "school", etc.
        for parent_key, items in raw.items():
            if isinstance(items, list):
                for item in items:
                    if "list" in item and isinstance(item["list"], list):
                        for entry in item["list"]:
                            lat = entry.get("lat")
                            lng = entry.get("lng")
                            distance = safe_float(entry.get("distance"))
                            name = entry.get("name")
                            normalized.append({
                                "geo_location": {"type": "Point", "coordinates": [lng, lat]} if lat is not None and lng is not None else None,
                                "distance": distance,
                                "name": name if name else "",
                                "category": item.get("category", parent_key)
                            })
    elif isinstance(raw, list):
        for element in raw:
            if isinstance(element, dict) and "poiList" in element and isinstance(element["poiList"], list):
                for poi_group in element["poiList"]:
                    if "pois" in poi_group and isinstance(poi_group["pois"], list):
                        for poi in poi_group["pois"]:
                            lat = poi.get("poiLatitude")
                            lng = poi.get("poiLongitude")
                            distance = safe_float(poi.get("distance"))
                            name = poi.get("title")
                            normalized.append({
                                "geo_location": {"type": "Point", "coordinates": [lng, lat]} if lat is not None and lng is not None else None,
                                "distance": distance,
                                "name": name if name else "",
                                "category": "life"
                            })
            elif isinstance(element, dict) and "poiLat" in element and "poiLng" in element:
                lat = element.get("poiLat")
                lng = element.get("poiLng")
                distance = safe_float(element.get("distance"))
                name = element.get("poiTitle") or element.get("name") or element.get("title")
                category = element.get("poiSubName") or element.get("categoryTypeName") or "life"
                normalized.append({
                    "geo_location": {"type": "Point", "coordinates": [lng, lat]} if lat is not None and lng is not None else None,
                    "distance": distance,
                    "name": name if name else "",
                    "category": category
                })
            elif isinstance(element, dict) and "lat" in element and "lng" in element:
                lat = element.get("lat")
                lng = element.get("lng")
                distance = safe_float(element.get("distance"))
                name = element.get("name") or element.get("title")
                category = element.get("categoryTypeName") or "life"
                normalized.append({
                    "geo_location": {"type": "Point", "coordinates": [lng, lat]} if lat is not None and lng is not None else None,
                    "distance": distance,
                    "name": name if name else "",
                    "category": category
                })
    return normalized

def normalize_utility_info(raw) -> list:
    # Reuse the same logic as life_info because format is similar.
    return normalize_life_info(raw)

def aggregate_life_info(raw) -> list:
    """
    Aggregates normalized life_info data to a list.
    Instead of selecting a single item, we now return the full normalized list.
    If no items are found, return an empty list.
    """
    items = normalize_life_info(raw)
    return items if items else []

def aggregate_utility_info(raw) -> list:
    """
    Aggregates normalized utility_info data to a list.
    """
    items = normalize_utility_info(raw)
    return items if items else []

def aggregate_info_to_string(raw) -> str:
    """
    將 life_info 或 utility_info 的原始資料轉換為純文字格式。
    每筆項目以「<名稱> 距離<距離>公尺」的格式呈現，項目間以 " || " 分隔，
    並限制總長度不超過 50000 個字元。
    """
    items = normalize_life_info(raw)  # life_info 與 utility_info 格式相似，均可使用同一函式
    parts = []
    for item in items:
        name = item.get("name", "").strip()
        distance = item.get("distance")
        if name:
            part = name
            if distance is not None:
                # 將距離轉為整數顯示
                part += f" 距離{int(distance)}公尺"
            parts.append(part)
    result = " || ".join(parts)
    return result
def normalize_trade_data_to_string(raw) -> str:
    """
    將 trade_data 資料轉換為純文字格式：
    每筆交易資訊以「成交地址：<地址>，成交日期：<soldDate>，每坪單價：<uniPrice>，
    總價：<totalPrice>，建物面積：<areaBuilding>」格式呈現，
    多筆資訊以 " || " 分隔，最終結果長度限制為 50000 個字元。
    """
    items = normalize_trade_data(raw)
    parts = []
    for item in items:
        address = item.get("address", "").strip()
        soldDate = item.get("soldDate")
        uniPrice = item.get("uniPrice")
        totalPrice = item.get("totalPrice")
        areaBuilding = item.get("areaBuilding")
        part = f"成交地址：{address}"
        if soldDate:
            part += f"，成交日期：{soldDate}"
        if uniPrice is not None:
            part += f"，每坪單價：{uniPrice}"
        if totalPrice is not None:
            part += f"，總價：{totalPrice}"
        if areaBuilding is not None:
            part += f"，建物面積：{areaBuilding}"
        parts.append(part)
    result = " || ".join(parts)
    return result[:50000]
def normalize_trade_data(raw) -> list:
    """
    Normalizes trade_data from various sources into a list of dictionaries.
    The common structure (matching your index) includes:
      - age: Edm.Double
      - floor: Edm.String
      - layout: Edm.String
      - address: Edm.String
      - areaLand: Edm.Double
      - soldDate: Edm.DateTimeOffset (as ISO8601 string or None)
      - uniPrice: Edm.Double
      - totalPrice: Edm.Double
      - areaBuilding: Edm.Double
    """

    def _normalize_item(item: dict) -> dict:
        result = {}
        result["age"] = safe_float(item.get("age") or item.get("Age"))

        if "floor" in item:
            result["floor"] = str(item.get("floor"))
        elif "floorStart" in item and "floorEnd" in item:
            result["floor"] = f"{item.get('floorStart')}~{item.get('floorEnd')}"
        elif "upFloor" in item:
            result["floor"] = str(item.get("upFloor"))
        else:
            result["floor"] = ""

        result["layout"] = item.get("layout") or ""
        result["address"] = item.get("address") or item.get("realAddress") or ""
        result["areaLand"] = safe_float(item.get("areaLand") or item.get("landPin"))

        sold_date_val = item.get("soldDate") or item.get("dealDate")
        if sold_date_val is None or str(sold_date_val).strip() == "":
            result["soldDate"] = None
        else:
            s = str(sold_date_val).strip()
            # If the string is all digits and length equals 5, assume it's in Minguo format
            if s.isdigit() and len(s) == 5:
                minguo_year = int(s[:3])
                month = int(s[3:5])
                year = minguo_year + 1911
                result["soldDate"] = f"{year:04d}-{month:02d}-01T00:00:00Z"
            else:
                result["soldDate"] = s

        result["uniPrice"] = safe_float(item.get("uniPrice"))
        result["totalPrice"] = safe_float(item.get("totalPrice") or item.get("price"))
        result["areaBuilding"] = safe_float(item.get("areaBuilding") or item.get("regPin"))
        return result

    if isinstance(raw, list):
        return [_normalize_item(item) for item in raw if isinstance(item, dict)]
    elif isinstance(raw, dict):
        return [_normalize_item(raw)]
    else:
        return []

# -------------------------------------------------------------------
# Function: Count Documents in Azure AI Search Index using REST API
# -------------------------------------------------------------------
def count_azure_documents(service_name, index_name, api_version, admin_key):
    """
    Counts the number of documents in the Azure AI Search index.

    GET https://{service_name}.search.windows.net/indexes('{index_name}')/docs/$count?api-version={api_version}
    """
    endpoint = f"https://{service_name}.search.windows.net"
    url = f"{endpoint}/indexes('{index_name}')/docs/$count?api-version={api_version}"
    headers = {
        "Content-Type": "application/json",
        "api-key": admin_key
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        try:
            return int(response.text.strip())
        except Exception as e:
            print("Error parsing count response:", e)
            return None
    else:
        print(f"Error counting documents: {response.status_code} {response.text}")
        return None


# -------------------------------------------------------------------
# Function: Delete All Documents by Sequential ID using REST API
# -------------------------------------------------------------------
def delete_all_documents_by_id(service_name, index_name, api_version, admin_key, batch_size=1000):
    """
    Deletes all documents from the Azure AI Search index by generating sequential IDs.
    Assumes that document keys ("id") range from 1 to the current document count.
    Uses the REST API with payload:
      { "value": [ { "@search.action": "delete", "id": "document_id" }, ... ] }
    """
    endpoint = f"https://{service_name}.search.windows.net"
    headers = {
        "Content-Type": "application/json",
        "api-key": admin_key
    }

    total_docs = count_azure_documents(service_name, index_name, api_version, admin_key)
    if total_docs is None:
        print("Failed to retrieve document count; aborting deletion.")
        return
    print(f"Total document count in Azure index: {total_docs}")

    # Generate sequential keys as strings: "1", "2", ..., "total_docs"
    keys = [str(i) for i in range(1, total_docs + 1)]
    delete_url = f"{endpoint}/indexes/{index_name}/docs/index?api-version={api_version}"

    for i in range(0, len(keys), batch_size):
        batch_keys = keys[i:i + batch_size]
        payload = {
            "value": [{"@search.action": "delete", "id": key} for key in batch_keys]
        }
        resp = requests.post(delete_url, headers=headers, json=payload)
        if resp.status_code in (200, 201):
            print(f"Deleted batch {i // batch_size + 1}: {resp.json()}")
        else:
            print(f"Error deleting batch {i // batch_size + 1}: {resp.text}")

    print("All documents removed from Azure index.")


# -------------------------------------------------------------------
# PostgreSQL Helper Functions
# -------------------------------------------------------------------
def get_postgres_total_count(conn, table_name):
    """
    Returns the total number of rows in the given table.
    """
    cursor = conn.cursor()
    query = f"SELECT COUNT(*) FROM {table_name}"
    cursor.execute(query)
    total = cursor.fetchone()[0]
    cursor.close()
    return total


def fetch_data_batch(conn, table_name, offset, limit):
    """
    Fetches a batch of rows from the given table using LIMIT and OFFSET.
    Orders by id.
    """
    query = f"SELECT * FROM {table_name} ORDER BY id LIMIT {limit} OFFSET {offset}"
    df = pd.read_sql_query(query, conn)
    return df


def get_postgres_connection(config_file='config.ini'):
    """
    Reads PostgreSQL connection parameters from config_file and returns a psycopg2 connection.
    """
    config = configparser.ConfigParser()
    config.read(config_file)
    conn = psycopg2.connect(
        host=config['postgres']['host'],
        database=config['postgres']['database'],
        user=config['postgres']['user'],
        password=config['postgres']['password'],
        port=config['postgres']['port']
    )
    return conn


# -------------------------------------------------------------------
# Function: Update (MergeOrUpload) Documents in Azure AI Search Index using REST API
# -------------------------------------------------------------------
def update_azure_index_rest(df, service_name, index_name, api_version, admin_key, update_batch_size=1000):
    endpoint = f"https://{service_name}.search.windows.net"
    headers = {
        "Content-Type": "application/json",
        "api-key": admin_key
    }
    update_url = f"{endpoint}/indexes/{index_name}/docs/index?api-version={api_version}"
    total_docs = len(df)
    print(f"Uploading {total_docs} documents using mergeOrUpload...")

    for i in range(0, total_docs, update_batch_size):
        batch = df.iloc[i:i + update_batch_size]
        documents = []
        for _, row in batch.iterrows():
            doc = {
                "@search.action": "mergeOrUpload",
                "id": str(row["id"]),
                "house_name": str(row["name"]),
                "house_address": str(row["address"]),
                "site": str(row["site"]),
                "url": str(row["url"]),
                "city": str(row["city"]),
                "district": str(row["district"]),
                "price": str(row["price"]),
                "space": str(row["space"]),
                "layout": str(row["layout"]),
                "age": str(row["age"]),
                "floors": str(row["floors"]),
                "community": str(row["community"]),
                "features": str(row["features"]),
                "review": str(row["review"]),
                "house_id": str(row["house_id"]) if "house_id" in row else None
            }
            if "latitude" in row and "longitude" in row and pd.notnull(row["latitude"]) and pd.notnull(row["longitude"]):
                doc["geo_location"] = {"type": "Point", "coordinates": [row["longitude"], row["latitude"]]}
            else:
                doc["geo_location"] = None

            # For basic_info, wrap normalized result in a list (if not empty)
            basic_info_raw = load_json_field("basic_info", row)
            basic_info_norm = normalize_basic_info(basic_info_raw)
            # Set basic_info as a single object (or null) instead of a list
            doc["basic_info"] = basic_info_norm if basic_info_norm and basic_info_norm != {} else None

            # 將 life_info 轉換為純文字字串
            life_info_raw = load_json_field("life_info", row)
            doc["life_info"] = aggregate_info_to_string(life_info_raw)

            # 將 utility_info 轉換為純文字字串
            utility_info_raw = load_json_field("utility_info", row)
            doc["utility_info"] = aggregate_info_to_string(utility_info_raw)

            # For trade_data, wrap normalized result in a list (if not empty)
            trade_data_raw = load_json_field("trade_data", row)
            doc["trade_data"] = normalize_trade_data_to_string(trade_data_raw)

            documents.append(doc)
        payload = {"value": documents}
        resp = requests.post(update_url, headers=headers, json=payload)
        if resp.status_code in (200, 201):
            print(f"Uploaded update batch {i // update_batch_size + 1}: {resp.json()}")
        else:
            print(f"Error uploading update batch {i // update_batch_size + 1}: {resp.text}")

    print("All documents in this batch updated successfully.")

# -------------------------------------------------------------------
# Main Function: Delete Azure Index Data and Update from PostgreSQL in Batches
# -------------------------------------------------------------------
def main():
    config = configparser.ConfigParser()
    config.read('config.ini')
    SERVICE_NAME = config['azure_AIsearch']['SERVICE_NAME']
    INDEX_NAME = config['azure_AIsearch']['INDEX_NAME']
    API_VERSION = config['azure_AIsearch']['API_VERSION']
    ADMIN_KEY = config['azure_AIsearch']['ADMIN_KEY']

    print("Counting documents in Azure AI Search index...")
    count = count_azure_documents(SERVICE_NAME, INDEX_NAME, API_VERSION, ADMIN_KEY)
    if count is not None:
        print(f"Current document count: {count}")
    else:
        print("Failed to get document count.")

    print("Deleting all documents from Azure index...")
    delete_all_documents_by_id(SERVICE_NAME, INDEX_NAME, API_VERSION, ADMIN_KEY, batch_size=1000)

    new_count = count_azure_documents(SERVICE_NAME, INDEX_NAME, API_VERSION, ADMIN_KEY)
    print(f"Document count after deletion: {new_count}")

    print("Connecting to PostgreSQL...")
    conn = get_postgres_connection()

    # Assuming that in config.ini the key 'table_name' is stored under the [postgres] section.
    # If your table is in the public schema, you can prepend "public." to the table name.
    table_name = f"public.{config['postgres']['table_name']}"
    try:
        total_records = get_postgres_total_count(conn, table_name)
        print(f"Total records in PostgreSQL table{table_name}: {total_records}")

        fetch_batch_size = 1000
        for offset in range(0, total_records, fetch_batch_size):
            print(f"Fetching records {offset} to {offset + fetch_batch_size} from PostgreSQL...")
            df_batch = fetch_data_batch(conn, table_name, offset, fetch_batch_size)
            print(f"Fetched {len(df_batch)} records; updating Azure index...")
            update_azure_index_rest(df_batch, SERVICE_NAME, INDEX_NAME, API_VERSION, ADMIN_KEY, update_batch_size=1000)
    finally:
        conn.close()
        print("PostgreSQL connection closed.")

if __name__ == '__main__':
    main()