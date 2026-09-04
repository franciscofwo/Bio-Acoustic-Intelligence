"""
Nomes das features brutas emitidas pelo firmware (src/main.cpp), na ordem
em que aparecem no CSV/serial. Ponto único de verdade usado por
data_loader.py e windowing.py - se o firmware ganhar/perder uma coluna,
só precisa mudar aqui.
"""

RAW_FEATURE_COLUMNS = [
    "RMS", "Peak", "Crest", "ZCR_Hz", "dB",
    "MFCC_1", "MFCC_2", "MFCC_3", "MFCC_4", "MFCC_5", "MFCC_6",
    "MFCC_7", "MFCC_8", "MFCC_9", "MFCC_10", "MFCC_11", "MFCC_12", "MFCC_13",
]

# Teto teórico de uma amostra depois do realinhamento ">> 8" em
# src/main.cpp (int32 do I2S -> 24 bits úteis). Usado pelo classificador
# de qualidade de sinal pra reconhecer picos colados no limite do ADC
# (ver docs/analise-dados.md - ~12,5% das leituras brutas bateram aqui).
PEAK_SATURATION_THRESHOLD = 0.9 * (2 ** 23)
