import pandas as pd
import re
import os
import sys

base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if base_dir not in sys.path:
    sys.path.append(base_dir)

from scripts.utils.paths import SQL_FILE, CLEANED_CSV, ensure_dirs

def sql_to_csv():
    ensure_dirs()

    if not os.path.exists(SQL_FILE):
        print(f"Error: {SQL_FILE} not found. Ensure the SQL is in data/raw/")
        return

    print(f"Reading SQL from: {SQL_FILE}")
    with open(SQL_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    print("Parsing SQL INSERT statements...")
    pattern = re.compile(r"INSERT INTO \"?rets_property\"? .*? VALUES\s*\((.*?)\);", re.DOTALL | re.IGNORECASE)
    matches = pattern.findall(content.replace('`', '"'))

    if not matches:
        print("No INSERT statements found. Check if table name matches 'rets_property'.")
        return

    all_rows = []
    for match in matches:
        row = re.findall(r"(?:'[^']*'|[^,])+", match)
        row = [item.strip().strip("'").strip('"') for item in row]
        all_rows.append(row)

    columns = [
        "id", "L_ListingID", "L_DisplayId", "L_Address", "L_Zip", "LM_char10_70",
        "L_AddressStreet", "L_City", "L_State", "L_Class", "L_Type_", "L_Keyword2",
        "LM_Dec_3", "L_Keyword1", "L_Keyword5", "L_Keyword7", "L_SystemPrice",
        "LM_Int2_3", "ModificationTimestamp", "ListingContractDate", "LMD_MP_Latitude",
        "LMD_MP_Longitude", "LA1_UserFirstName", "LA1_UserLastName", "L_Status",
        "LO1_OrganizationName", "L_Remarks", "L_Photos"
    ]

    df = pd.DataFrame(all_rows)
    num_cols = min(len(columns), df.shape[1])
    df = df.iloc[:, :num_cols]
    df.columns = columns[:num_cols]

    df.to_csv(CLEANED_CSV, index=False)
    print(f"Successfully converted!")
    print(f"Source:      {SQL_FILE}")
    print(f"Destination: {CLEANED_CSV}")
    print(f"Rows:        {len(df)}")

if __name__ == "__main__":
    sql_to_csv()