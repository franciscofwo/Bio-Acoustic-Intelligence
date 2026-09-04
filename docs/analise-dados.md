# Análise de `leituras_mic.csv`

Captura de exemplo gerada pelo `tools/serial_looger.py`, com uma janela de
áudio (~32 ms) por linha.

- **Linhas:** 1.480
- **Período:** 2026-09-01T21:36:55 → 2026-09-01T21:41:56 (~5 minutos)

## Estatísticas gerais

| Métrica | Mínimo | Mediana | Média | Máximo |
|---|---|---|---|---|
| RMS | 0,89 | 63.259 | 122.804 | 524.288 |
| Peak | 1,0 | 1.379.293 | 2.643.916 | 8.388.608 |
| dB | 0,00 | 96,03 | 81,63 | 114,39 |

(dB acima de ~100 num microfone MEMS de baixo custo já é fisicamente
implausível para som ambiente comum — referência: uma britadeira a 1 m
fica em torno de 100 dB SPL.)

## Evidência de mau contato elétrico

Duas observações nos dados apontam para **problema de fiação**, não para
som real sendo captado:

1. **12,5% das linhas (185 de 1.480) têm `Peak` acima de 90% do teto
   teórico do ADC** (`2^23 ≈ 8.388.608`, o limite de uma amostra de 24 bits
   após o realinhamento `>>8` em `main.cpp:249`). Ou seja, uma em cada oito
   janelas está batendo no limite de saturação do conversor — extremamente
   incomum em áudio ambiente real, e típico de uma linha de dados I2S
   captando ruído digital de alta amplitude por mau contato.

2. **Salto médio de ~150.000 em RMS entre leituras consecutivas** (janelas
   de apenas 32 ms de diferença), contra uma mediana de RMS de ~63.000 —
   ou seja, o salto típico entre uma janela e a próxima é **maior que o
   próprio valor típico**. Áudio real não oscila de forma tão binária
   janela a janela; esse padrão (valor baixo → pico quase saturado → valor
   baixo de novo, em milissegundos) é a assinatura clássica de um sinal
   I2S com contato intermitente.

## Conclusão

Os dados de `leituras_mic.csv`, embora não estejam "zerados" (o que se
observou depois, em sessão de monitor ao vivo, quando o contato piorou até
abrir completamente), **já mostram o mesmo problema em estágio
intermediário**: a fiação do INMP441 está com mau contato, gerando
principalmente ruído/lixo digital em vez de sinal acústico limpo.

**Recomendação:** antes de usar essas leituras (ou novas capturas) como
base para qualquer análise ou modelo, refazer as conexões físicas do
microfone (ver [hardware.md](hardware.md)) e validar que, em ambiente
silencioso, o RMS fica estável e baixo (dezenas/centenas, não
alternando com picos próximos da saturação).
