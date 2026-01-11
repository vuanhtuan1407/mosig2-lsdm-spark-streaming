import json
import pandas as pd


def parse_schema_to_dict(schema_path, output_path):
    df = pd.read_csv(schema_path)
    schema_dict = {}
    for _, row in df.iterrows():
        file_pattern = row["file pattern"].split("/")[0]
        if file_pattern not in schema_dict:
            schema_dict[file_pattern] = {
                "col_content": [],
                "col_format": [],
                "col_mandatory": []
            }

        schema_dict[file_pattern]["col_content"].append(row["content"].replace(" ", "_"))
        schema_dict[file_pattern]["col_format"].append(row["format"])
        schema_dict[file_pattern]["col_mandatory"].append(1 if row["mandatory"] == "YES" else 0)

    # Save to JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(schema_dict, f, ensure_ascii=False, indent=4)

    print(f"Schema dictionary has been saved to '{output_path}'")


def format_df_to_dict(df: pd.DataFrame, schema: dict):
    df = df.copy()
    df.columns = schema["col_content"]
    return df.to_dict(orient='records')


if __name__ == "__main__":
    SCHEMA_CSV_PATH = 'data/clusterdata-2011-2/schema.csv'
    OUTPUT_JSON_PATH = 'output/schema_dict.json'
    parse_schema_to_dict(SCHEMA_CSV_PATH, OUTPUT_JSON_PATH)