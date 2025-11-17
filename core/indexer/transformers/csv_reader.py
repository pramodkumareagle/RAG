import chardet
import pandas as pd

def read_csv_file(path: str, max_rows: int = 5000) -> str:
    # Detect encoding
    with open(path, "rb") as f:
        enc_hint = chardet.detect(f.read(4096)).get("encoding") or "utf-8"

    df = pd.read_csv(path, encoding=enc_hint)

    lines = [f"CSV Columns: {list(df.columns)}"]

    df = df.astype(str).head(max_rows)

    for _, row in df.head(50).iterrows():
        lines.append("; ".join(f"{k}={v}" for k, v in row.items()))

    return "\n".join(lines)

