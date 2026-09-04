"""
Janela de observação e janela de decisão.

São dois conceitos DIFERENTES e propositalmente independentes - ver
docs/modelo-ia.md para a justificativa completa. Resumo:

- ObservationWindow: agrega N leituras brutas (uma por ciclo do firmware,
  ~32ms de áudio a cada ~200ms de loop) em UM vetor de features
  estatísticas (média/desvio/min/max) que vira a entrada do modelo. Existe
  porque uma leitura isolada é curta e ruidosa demais pra representar um
  evento acústico - e porque o próprio hardware tem jitter/ruído
  intermitente (ver docs/analise-dados.md), que uma janela maior absorve.

- DecisionWindow: agrega as últimas K classificações (uma por
  ObservationWindow) e só troca a decisão emitida quando há maioria
  suficiente numa direção. Existe pra transformar uma sequência de
  classificações "piscando" (uma janela ruim isolada não deveria virar uma
  decisão nova) numa saída estável e acionável.
"""
from __future__ import annotations

from collections import deque
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class ObservationWindowConfig:
    duration_s: float = 1.0        # tamanho da janela de observação, em segundos
    stride_s: float | None = None  # passo entre janelas; default = duration_s (sem sobreposição)

    def stride(self) -> float:
        return self.stride_s if self.stride_s is not None else self.duration_s


def build_observation_windows(
    df: pd.DataFrame, feature_cols: list[str], config: ObservationWindowConfig
) -> pd.DataFrame:
    """
    Agrega leituras brutas (uma linha por ciclo do firmware) em janelas de
    `config.duration_s` segundos, usando o timestamp REAL de cada leitura -
    não assume período fixo do loop(), já que o hardware sofre jitter e
    leituras atrasadas/perdidas não devem distorcer a janela.

    Para cada feature em `feature_cols`, calcula mean/std/min/max dentro da
    janela. Retorna um DataFrame com uma linha por janela de observação.
    """
    df = df.sort_values("timestamp").reset_index(drop=True)
    if df.empty:
        return pd.DataFrame()

    t0, t_end = df["timestamp"].iloc[0], df["timestamp"].iloc[-1]
    stride = pd.Timedelta(seconds=config.stride())
    duration = pd.Timedelta(seconds=config.duration_s)

    rows = []
    win_start = t0
    while win_start <= t_end:
        win_end = win_start + duration
        chunk = df[(df["timestamp"] >= win_start) & (df["timestamp"] < win_end)]
        if len(chunk) > 0:
            row = {"window_start": win_start, "window_end": win_end, "n_frames": len(chunk)}
            for col in feature_cols:
                vals = chunk[col].to_numpy(dtype=float)
                row[f"{col}_mean"] = float(np.mean(vals))
                row[f"{col}_std"] = float(np.std(vals))
                row[f"{col}_min"] = float(np.min(vals))
                row[f"{col}_max"] = float(np.max(vals))
            rows.append(row)
        win_start += stride

    return pd.DataFrame(rows)


class DecisionWindow:
    """
    Suaviza uma sequência de classificações por ObservationWindow em uma
    decisão estável: só troca o rótulo emitido quando pelo menos
    `min_ratio` das últimas `size` classificações concordam.
    """

    def __init__(self, size: int = 3, min_ratio: float = 0.6):
        if size < 1:
            raise ValueError("size deve ser >= 1")
        if not (0.0 < min_ratio <= 1.0):
            raise ValueError("min_ratio deve estar em (0, 1]")
        self.size = size
        self.min_ratio = min_ratio
        self._buffer: deque = deque(maxlen=size)
        self._current_decision: str | None = None

    def push(self, label: str) -> str | None:
        """
        Registra a classificação mais recente de uma ObservationWindow.
        Retorna a decisão estabilizada (pode repetir a anterior, ou ser
        None enquanto o buffer ainda não encheu o bastante pra decidir).
        """
        self._buffer.append(label)
        if len(self._buffer) < self.size:
            return self._current_decision

        counts: dict[str, int] = {}
        for item in self._buffer:
            counts[item] = counts.get(item, 0) + 1
        best_label, best_count = max(counts.items(), key=lambda kv: kv[1])

        if best_count / len(self._buffer) >= self.min_ratio:
            self._current_decision = best_label
        # se nenhum rótulo atingiu o quorum, mantém a última decisão estável
        return self._current_decision
