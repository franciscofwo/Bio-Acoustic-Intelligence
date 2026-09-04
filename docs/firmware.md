# Firmware — `src/main.cpp`

Pipeline executado a cada janela de **512 amostras @ 16 kHz** (~32 ms),
repetido a cada ~200 ms no `loop()`.

## 1. Captura I2S

`setupI2SMic()` configura o driver I2S legado em modo mestre/RX, 32 bits por
amostra, canal direito apenas (pegadinha conhecida do INMP441 com esse
driver). Cada frame de 32 bits é realinhado para os 24 bits úteis do sensor
com `sample >> 8` (`main.cpp:249`), gerando o array `rawSamples`.

## 2. Métricas no domínio do tempo (`analyzeTimeDomain`)

Calculadas direto sobre `rawSamples`, sem janela nem pré-ênfase:

- **RMS** — raiz da média dos quadrados das amostras.
- **Peak** — maior amostra em módulo na janela.
- **Crest Factor** — `Peak / RMS` (mede o quão "pontudo" é o sinal; ruído
  puro tende a ~1, transientes/impulsos têm crest factor alto).
- **ZCR (Zero Crossing Rate)** — nº de trocas de sinal por segundo,
  proxy grosseiro de frequência dominante / ruído de alta frequência.
- **dB** — `20·log10(RMS)`, com piso em `RMS = 1.0` para evitar `log(0)`
  (por isso `dB:0.00` não significa silêncio perfeito, e sim RMS ≤ 1).

## 3. Pipeline espectral → MFCC

1. **Pré-ênfase** (`y[n] = x[n] − 0.97·x[n−1]`) realça altas frequências.
2. **Janela de Hamming**, pré-calculada uma vez em `setupHammingWindow()`.
3. **FFT** radix-2 Cooley-Tukey in-place (`fft()`), 512 pontos.
4. **Banco de filtros mel** (26 filtros triangulares, bordas pré-calculadas
   em `setupMelFilterbank()` via conversão Hz↔Mel) aplicado ao espectro de
   potência, com log de cada energia (`+1e-6` de epsilon para evitar
   `log(0)`).
5. **DCT-II**, mantendo os 13 primeiros coeficientes → `MFCC_1..MFCC_13`.

`MFCC_1` corresponde ao coeficiente `c=0` da DCT — é essencialmente a soma
(log-energia total) dos 26 filtros, por isso tende a ter magnitude bem maior
que os demais coeficientes.

## 4. Saída serial

Uma linha por janela, formato `Label:valor` separado por vírgula
(compatível com o Serial Plotter do Arduino IDE e com plotters web):

```
RMS:955.92,Peak:21630.00,Crest:22.63,ZCR_Hz:93.7,dB:59.61,MFCC_1:535.151,MFCC_2:-51.457,...
```

Os scripts em `tools/` (`listen.py`, `serial_looger.py`) leem essa saída da
porta serial e gravam em CSV com timestamp — é assim que `leituras_mic.csv`
foi gerado.
