"""
Classificador aplicado a cada janela de observação.

Hoje não existe dataset rotulado - leituras_mic.csv só tem features cruas,
sem coluna de classe. Por isso o modelo padrão é NÃO SUPERVISIONADO: um
IsolationForest treinado sobre as próprias janelas de observação, que
aprende o padrão estatístico "normal" dos dados e sinaliza como anomalia
qualquer janela fora desse padrão. Na prática, isso já entrega valor real
hoje: é exatamente o comportamento descrito em docs/analise-dados.md
(picos colados na saturação do ADC, saltos abruptos de RMS por mau
contato) que vira "ruido_contato" automaticamente.

Quando existir uma coluna de rótulo de verdade (ex: "classe" com valores
como "silencio", "evento_biologico", "ruido_ambiente"), basta chamar
train_supervised() em vez de train_unsupervised() - a API de inferência
(predict_label) é idêntica nos dois modos, então o resto do pipeline
(ObservationWindow -> classificador -> DecisionWindow) não precisa mudar.
"""
from __future__ import annotations

from dataclasses import dataclass

import joblib
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler

UNSUPERVISED_LABELS = {1: "sinal_valido", -1: "ruido_contato"}


@dataclass
class SignalClassifier:
    scaler: StandardScaler
    model: object
    feature_names: list[str]
    mode: str  # "unsupervised" ou "supervised"

    def predict_label(self, observation_row: pd.Series) -> str:
        x = observation_row[self.feature_names].to_numpy(dtype=float).reshape(1, -1)
        x_scaled = self.scaler.transform(x)
        if self.mode == "unsupervised":
            pred = int(self.model.predict(x_scaled)[0])  # 1 = normal, -1 = anomalia
            return UNSUPERVISED_LABELS[pred]
        return str(self.model.predict(x_scaled)[0])

    def save(self, path: str) -> None:
        joblib.dump(self, path)

    @staticmethod
    def load(path: str) -> "SignalClassifier":
        return joblib.load(path)


def train_unsupervised(
    observation_df: pd.DataFrame,
    feature_names: list[str],
    contamination: float = 0.15,
    random_state: int = 42,
) -> SignalClassifier:
    """
    contamination=0.15 por padrão porque docs/analise-dados.md mediu ~12,5%
    das leituras brutas coladas na saturação do ADC nesse hardware.
    Recalibre esse número pro seu próprio equipamento: quanto mais estável
    for a fiação, menor deve ser a contamination esperada.
    """
    X = observation_df[feature_names].to_numpy(dtype=float)
    scaler = StandardScaler().fit(X)
    X_scaled = scaler.transform(X)

    model = IsolationForest(contamination=contamination, random_state=random_state)
    model.fit(X_scaled)

    return SignalClassifier(scaler=scaler, model=model, feature_names=feature_names, mode="unsupervised")


def train_supervised(
    observation_df: pd.DataFrame,
    feature_names: list[str],
    label_column: str,
    random_state: int = 42,
) -> SignalClassifier:
    X = observation_df[feature_names].to_numpy(dtype=float)
    y = observation_df[label_column].to_numpy()

    scaler = StandardScaler().fit(X)
    X_scaled = scaler.transform(X)

    model = RandomForestClassifier(n_estimators=200, random_state=random_state)
    model.fit(X_scaled, y)

    return SignalClassifier(scaler=scaler, model=model, feature_names=feature_names, mode="supervised")
