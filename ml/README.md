# `ml/` — modelo de classificação do sinal capturado

Pipeline Python que consome as leituras do firmware (`RMS`, `Peak`, `Crest`,
`ZCR_Hz`, `dB`, `MFCC_1..13`, ver [`../docs/firmware.md`](../docs/firmware.md))
e classifica o sinal capturado em **janelas de observação**, estabilizando
a saída numa **janela de decisão**. A justificativa completa desses dois
conceitos está em [`../docs/modelo-ia.md`](../docs/modelo-ia.md) — leia
antes de mexer nos parâmetros `--obs-window` / `--decision-size` abaixo.

## Instalação

```bash
cd ml
python3 -m venv .venv && source .venv/bin/activate   # opcional, mas recomendado
pip install -r requirements.txt
```

## Treinar

Hoje `leituras_mic.csv` não tem rótulos, então o padrão é treinar um
detector de anomalia **não supervisionado** (`IsolationForest`) que aprende
o padrão estatístico normal das janelas de observação e sinaliza como
`ruido_contato` qualquer janela fora desse padrão:

```bash
python3 train.py --data ../leituras_mic.csv --obs-window 1.0 --out models/quality_model.joblib
```

Quando existir um CSV com uma coluna de rótulo real (ex: `classe`), treine
em modo supervisionado (`RandomForestClassifier`) em vez disso:

```bash
python3 train.py --data dataset_rotulado.csv --label-column classe --out models/classe_model.joblib
```

## Classificar

```bash
python3 infer.py \
  --data ../leituras_mic.csv \
  --model models/quality_model.joblib \
  --obs-window 1.0 \
  --decision-size 3 --decision-ratio 0.6 \
  --out resultado.csv
```

Cada linha impressa mostra a classificação **daquela janela de
observação** e a **decisão estabilizada** pela janela de decisão — repare
como uma janela isolada classificada como `ruido_contato` não muda a
decisão sozinha; só uma sequência consistente muda.

## Arquivos

| Arquivo | Papel |
|---|---|
| `features.py` | nomes das colunas cruas do firmware (fonte única de verdade) |
| `data_loader.py` | carrega o CSV de leituras num DataFrame |
| `windowing.py` | `ObservationWindowConfig`/`build_observation_windows` + `DecisionWindow` |
| `classifier.py` | treino/inferência do modelo (não supervisionado e supervisionado) |
| `train.py` | CLI de treino |
| `infer.py` | CLI de inferência (pipeline completo) |
| `models/` | modelos treinados (`.joblib`) — reproduzíveis via `train.py`, não versionados no git |
