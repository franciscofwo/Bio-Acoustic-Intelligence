# Documentação — Bio-Acoustic Intelligence

Firmware para ESP32-S3 que captura áudio de um microfone I2S (INMP441) e
extrai, em tempo real, métricas no domínio do tempo (RMS, Peak, Crest, ZCR,
dB) e coeficientes MFCC (1 a 13) no domínio da frequência — a base para
classificação/monitoramento acústico (ex: aplicações de bio-acústica, ESG,
monitoramento ambiental).

## Índice

- [hardware.md](hardware.md) — placa, microfone, pinagem e conexão USB
- [firmware.md](firmware.md) — arquitetura do pipeline de captura e extração de features
- [analise-dados.md](analise-dados.md) — análise das leituras em `leituras_mic.csv`
- [modelo-ia.md](modelo-ia.md) — modelo de classificação, e por que ele é dividido em janela de observação e janela de decisão
- [troubleshooting.md](troubleshooting.md) — histórico de problemas encontrados e soluções

## Como compilar e gravar

```bash
cd "Acoustic Intelligence"
pio run --target upload --target monitor
```

A porta serial é fixada em `platformio.ini` (`monitor_port` / `upload_port`).
Se o macOS renomear a porta USB (comum após desconectar/reconectar o cabo),
rode `ls /dev/cu.*` para achar o novo nome e atualize esses dois campos.

## Estrutura do projeto

```
src/main.cpp        firmware principal (captura I2S + métricas + MFCC)
platformio.ini       configuração de build/upload da placa
tools/                scripts Python para logar a saída serial em CSV
leituras_mic.csv       exemplo de captura (ver análise em analise-dados.md)
ml/                    modelo de IA que classifica o sinal capturado (ver modelo-ia.md)
docs/                  esta documentação
```
