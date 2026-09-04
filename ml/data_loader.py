"""
Carrega leituras_mic.csv (ou qualquer CSV no mesmo formato, gerado por
tools/serial_looger.py) num DataFrame pronto pra windowing.py.

Fica separado de windowing.py de propósito: quando a fonte dos dados
trocar de "CSV gravado" pra "stream serial ao vivo", só este arquivo
muda - a lógica de janela de observação/decisão continua igual.
"""
from __future__ import annotations

import pandas as pd

from features import RAW_FEATURE_COLUMNS


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)

    missing = [c for c in RAW_FEATURE_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Colunas esperadas ausentes no CSV: {missing}")
    if "timestamp" not in df.columns:
        raise ValueError('CSV precisa de uma coluna "timestamp" (ver tools/serial_looger.py)')

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df
