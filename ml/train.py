#!/usr/bin/env python3
"""
Treina o classificador de janela de observação a partir de um CSV de
leituras (formato de leituras_mic.csv, gerado por tools/serial_looger.py).

Exemplos:
    # modo padrão: não supervisionado (IsolationForest), sem precisar de rótulos
    python3 train.py --data ../leituras_mic.csv --out models/quality_model.joblib

    # modo supervisionado, se o CSV tiver uma coluna de classe
    python3 train.py --data dataset_rotulado.csv --label-column classe --out models/classe_model.joblib
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from classifier import train_supervised, train_unsupervised  # noqa: E402
from data_loader import load_csv  # noqa: E402
from features import RAW_FEATURE_COLUMNS  # noqa: E402
from windowing import ObservationWindowConfig, build_observation_windows  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data", required=True, help="CSV de entrada (formato leituras_mic.csv)")
    parser.add_argument("--obs-window", type=float, default=1.0,
                         help="tamanho da janela de observação, em segundos (default: 1.0)")
    parser.add_argument("--stride", type=float, default=None,
                         help="passo entre janelas de observação, em segundos (default: = obs-window)")
    parser.add_argument("--label-column", default=None,
                         help="coluna de rótulo no CSV, se existir (ativa o modo supervisionado)")
    parser.add_argument("--contamination", type=float, default=0.15,
                         help="fração esperada de janelas anômalas, modo não supervisionado (default: 0.15)")
    parser.add_argument("--out", default="models/quality_model.joblib", help="onde salvar o modelo treinado")
    args = parser.parse_args()

    df = load_csv(args.data)
    config = ObservationWindowConfig(duration_s=args.obs_window, stride_s=args.stride)
    obs_df = build_observation_windows(df, RAW_FEATURE_COLUMNS, config)
    if obs_df.empty:
        raise SystemExit("Nenhuma janela de observação gerada - dados insuficientes ou janela grande demais.")

    feature_names = [c for c in obs_df.columns if c not in ("window_start", "window_end", "n_frames")]

    if args.label_column:
        clf = train_supervised(obs_df, feature_names, args.label_column)
        print(f"Modelo supervisionado treinado com {len(obs_df)} janelas de observação "
              f"(coluna de rótulo: {args.label_column}).")
    else:
        clf = train_unsupervised(obs_df, feature_names, contamination=args.contamination)
        print(f"Modelo não supervisionado (IsolationForest) treinado com {len(obs_df)} janelas de observação.")

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    clf.save(args.out)
    print(f"Modelo salvo em {args.out}")


if __name__ == "__main__":
    main()
