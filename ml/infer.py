#!/usr/bin/env python3
"""
Roda o pipeline completo - janela de observação -> classificador -> janela
de decisão - sobre um CSV de leituras, e imprime/salva a decisão
estabilizada ao longo do tempo.

Exemplo:
    python3 infer.py --data ../leituras_mic.csv --model models/quality_model.joblib \
        --obs-window 1.0 --decision-size 3 --decision-ratio 0.6 --out resultado.csv
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from classifier import SignalClassifier  # noqa: E402
from data_loader import load_csv  # noqa: E402
from features import RAW_FEATURE_COLUMNS  # noqa: E402
from windowing import DecisionWindow, ObservationWindowConfig, build_observation_windows  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--obs-window", type=float, default=1.0,
                         help="tamanho da janela de observação, em segundos (deve bater com o treino)")
    parser.add_argument("--stride", type=float, default=None)
    parser.add_argument("--decision-size", type=int, default=3,
                         help="quantas ObservationWindows entram na janela de decisão")
    parser.add_argument("--decision-ratio", type=float, default=0.6,
                         help="fração mínima de concordância pra trocar a decisão estável")
    parser.add_argument("--out", default=None, help="CSV opcional pra salvar o resultado por janela")
    args = parser.parse_args()

    df = load_csv(args.data)
    config = ObservationWindowConfig(duration_s=args.obs_window, stride_s=args.stride)
    obs_df = build_observation_windows(df, RAW_FEATURE_COLUMNS, config)
    if obs_df.empty:
        raise SystemExit("Nenhuma janela de observação gerada - dados insuficientes ou janela grande demais.")

    clf = SignalClassifier.load(args.model)
    decision_window = DecisionWindow(size=args.decision_size, min_ratio=args.decision_ratio)

    results = []
    for _, row in obs_df.iterrows():
        raw_label = clf.predict_label(row)
        decision = decision_window.push(raw_label)
        results.append({
            "window_start": row["window_start"],
            "window_end": row["window_end"],
            "n_frames": int(row["n_frames"]),
            "classificacao_janela": raw_label,
            "decisao_estavel": decision,
        })
        print(f"[{row['window_start']}] n_frames={int(row['n_frames']):3d}  "
              f"janela={raw_label:16s}  decisão={decision}")

    if args.out:
        import pandas as pd
        pd.DataFrame(results).to_csv(args.out, index=False)
        print(f"\nResultado salvo em {args.out}")


if __name__ == "__main__":
    main()
