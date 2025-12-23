import pandas as pd
import os
import io


def read_file_columns(filepath, nrows=5):
    """Leer el archivo (CSV o Excel) y devolver la lista de columnas.

    Lanza excepción si el archivo no puede abrirse.
    """
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(filepath, nrows=nrows)
    else:
        # Excel (xls, xlsx, xlsm)
        df = pd.read_excel(filepath, nrows=nrows, engine="openpyxl")
    return list(df.columns)


def _read_full_dataframe(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(filepath, dtype=str)
    else:
        df = pd.read_excel(filepath, dtype=str, engine="openpyxl")
    return df


def process_to_csv(filepath, mapping, defaults=None, discount_pct=0.0, gain_pct=0.0):
    """Procesa el archivo y devuelve bytes del CSV final.

    - mapping: dict donde key=required_field, value=source_column or None
    - defaults: dict de valores por defecto para campos no mapeados
    - discount_pct/gain_pct: porcentajes (ej. 10.0 para 10%)
    """
    if defaults is None:
        defaults = {}

    df = _read_full_dataframe(filepath)

    required_fields = [k for k in mapping.keys()]

    out_rows = []
    for idx, row in df.iterrows():
        out = {}
        for field in required_fields:
            src = mapping.get(field)
            if src and src in df.columns:
                val = row.get(src)
            else:
                # fallback to default if provided
                val = defaults.get(field, "")

            if pd.isna(val):
                val = defaults.get(field, "")

            out[field] = val

        # Apply numeric transforms on 'rate' and 'setup' if present
        for num_field in ["rate", "setup"]:
            if num_field in out:
                try:
                    raw = str(out[num_field]).strip()
                    if raw == "":
                        out[num_field] = ""
                        continue
                    v = float(raw.replace(",", "."))
                    # discount then gain
                    v = v * (1 - (discount_pct or 0.0) / 100.0)
                    v = v * (1 + (gain_pct or 0.0) / 100.0)
                    out[num_field] = f"{v:.6f}"
                except Exception:
                    # keep original if cannot parse
                    pass

        out_rows.append(out)

    out_df = pd.DataFrame(out_rows, columns=required_fields)
    buf = io.StringIO()
    out_df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")
