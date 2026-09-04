# Modelo de IA — classificação do sinal capturado

Código em [`../ml/`](../ml). Este documento explica **por que** o pipeline
é desenhado em torno de duas janelas distintas — de observação e de
decisão — e não apenas "rodar o modelo a cada leitura".

## O problema de classificar leitura a leitura

O firmware ([`firmware.md`](firmware.md)) emite uma linha de features a
cada ~200 ms, cobrindo uma janela de áudio de apenas ~32 ms. Se o modelo
classificasse cada leitura isoladamente, dois problemas apareceriam de
imediato:

1. **32 ms não é um evento acústico.** A maioria dos eventos relevantes
   (uma vocalização, um ruído ambiental, um padrão sustentado) se
   manifesta ao longo de várias janelas de 32 ms, não em uma única. Um
   classificador por leitura não tem contexto temporal suficiente pra
   distinguir "início de um evento real" de "um transiente qualquer".

2. **O próprio hardware é ruidoso.** A análise em
   [`analise-dados.md`](analise-dados.md) mediu, nos dados reais
   capturados, **12,5% das leituras brutas com o pico colado no teto do
   ADC** e saltos de RMS entre leituras consecutivas maiores que o valor
   típico do sinal — assinatura de mau contato elétrico, não de som. Um
   classificador ingênuo, leitura a leitura, herdaria esse ruído
   diretamente na saída: ficaria "piscando" entre classes a cada 200 ms,
   mesmo sem nenhuma mudança real no ambiente.

A solução para os dois problemas não é a mesma janela — são **duas
janelas com propósitos diferentes**, aplicadas em dois estágios do
pipeline.

## Janela de observação (`ObservationWindow`)

**O que é:** o intervalo de tempo (ex: 1 segundo) cujas leituras brutas são
agregadas — média, desvio-padrão, mínimo e máximo de cada feature — em
**um único vetor** que alimenta o modelo.

**Por que existe:** dá ao modelo contexto temporal suficiente pra
representar um evento de verdade, em vez de uma amostra instantânea. O
desvio-padrão dentro da janela, em particular, é o que torna picos
isolados de saturação visíveis ao modelo como algo estatisticamente
anômalo — é essa mesma ideia que o `IsolationForest` em
[`../ml/classifier.py`](../ml/classifier.py) usa para separar
`sinal_valido` de `ruido_contato`.

**Trade-off ao escolher o tamanho:**

| Janela menor | Janela maior |
|---|---|
| Mais responsiva, mas mais sujeita a ruído de curto prazo | Mais robusta a ruído, mas mais latência pra reagir a um evento novo |
| Boa pra eventos rápidos e bem definidos | Boa pra padrões sustentados (ex: nível de ruído ambiente ao longo do tempo) |

O padrão em `ml/windowing.py` (`ObservationWindowConfig`, default
`duration_s=1.0`) usa o **timestamp real** de cada leitura, não uma
contagem fixa de amostras — importante porque o loop do firmware sofre
jitter (o `delay(200)` não garante período exato) e porque leituras podem
se perder; contar amostras distorceria o tamanho real da janela no tempo.

## Janela de decisão (`DecisionWindow`)

**O que é:** o número de classificações consecutivas de janelas de
observação (ex: 3) que precisam concordar — numa proporção mínima, ex: 60%
— antes que a **decisão emitida** mude.

**Por que existe:** é uma camada de estabilização em cima da anterior. A
janela de observação já reduz ruído dentro de si mesma, mas uma janela
individual ainda pode ser classificada errado (ex: uma rajada de mau
contato que dura o segundo inteiro). Sem a janela de decisão, cada
classificação de observação vira uma "decisão" nova — e num sistema que
vai disparar alertas, logs ou ações a partir dessa decisão, isso significa
alarme falso a cada janela ruim isolada.

**Exemplo real**, rodando `ml/infer.py` sobre `leituras_mic.csv` com
`--decision-size 3 --decision-ratio 0.6`:

```
[21:37:07] janela=sinal_valido   decisão=sinal_valido
[21:37:08] janela=ruido_contato  decisão=sinal_valido   <- 1 de 3 não muda a decisão
[21:37:09] janela=sinal_valido   decisão=sinal_valido
...
[21:37:17] janela=sinal_valido   decisão=sinal_valido
[21:37:18] janela=ruido_contato  decisão=ruido_contato  <- 2 de 3 (>=60%) muda a decisão
[21:37:19] janela=sinal_valido   decisão=sinal_valido
```

Uma classificação ruim isolada (21:37:08) é absorvida e não altera a
decisão estável; só quando o padrão se repete o suficiente dentro da
janela de decisão (21:37:18) é que a saída realmente muda. É esse
comportamento — não o modelo em si — que torna o sistema utilizável em
produção com um sensor que sabemos ser eletricamente instável.

**Trade-off ao escolher `size`/`ratio`:**

- `size` maior e/ou `ratio` mais alto → decisão mais estável, mas mais
  lenta pra confirmar uma mudança real de estado.
- `size` menor e/ou `ratio` mais baixo → decisão mais reativa, mas mais
  vulnerável a ruído correlacionado (ex: uma rajada de mau contato que
  dura vários segundos seguidos ainda pode "vencer" o quórum).

## Por que as duas janelas não podem ser fundidas em uma só

É tentador simplificar para "só uma janela grande resolve os dois
problemas" — mas elas otimizam objetivos diferentes:

- A janela de observação define **o que o modelo vê** (a unidade de
  entrada/contexto). Mudar seu tamanho muda a própria natureza do que está
  sendo classificado.
- A janela de decisão define **quando confiar no que o modelo disse** (a
  unidade de saída/ação). Mudar seu tamanho não muda o que o modelo vê,
  só quão rápido o sistema reage à sequência de classificações.

Separá-las permite, por exemplo, manter uma janela de observação curta
(reativa, boa resolução temporal) e ainda assim ter uma saída estável,
via uma janela de decisão maior — algo impossível se as duas fossem a
mesma janela.

## Estado atual do modelo

Sem dataset rotulado, o modelo hoje é um detector de anomalia
(`sinal_valido` vs. `ruido_contato`) — ver justificativa e parâmetros em
[`../ml/classifier.py`](../ml/classifier.py). Ele já resolve um problema
real (sinalizar automaticamente os trechos afetados pelo mau contato do
INMP441, documentados em [`analise-dados.md`](analise-dados.md)). Quando
houver rótulos reais de classes acústicas de interesse, o mesmo pipeline
de janelas passa a alimentar um classificador supervisionado
(`train_supervised()`), sem precisar mudar `windowing.py` nem os scripts
de CLI.
