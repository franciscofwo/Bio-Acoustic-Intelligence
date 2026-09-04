# Hardware

## Placa

**4D Systems GEN4-ESP32 16MB (ESP32S3-R8N16)**

- MCU: ESP32-S3, 240 MHz
- RAM: 320 KB (+ 8 MB PSRAM)
- Flash: 16 MB
- `board` no PlatformIO: `4d_systems_esp32s3_gen4_r8n16`

## Microfone: INMP441 (I2S, MEMS)

| Sinal | Pino ESP32-S3 | Define no firmware |
|---|---|---|
| SCK (BCLK) | GPIO4  | `I2S_SCK_PIN` |
| WS (LRCLK) | GPIO5  | `I2S_WS_PIN`  |
| SD (DOUT)  | GPIO6  | `I2S_SD_PIN`  |
| VDD        | 3V3    | — |
| GND        | GND    | — |
| L/R        | GND (canal direito) | — |

Esses três pinos (4, 5, 6) foram escolhidos por evitarem a faixa reservada
GPIO26-37, além dos pinos 0, 19, 20, 45 e 46 (usados internamente / boot
strapping no ESP32-S3).

O firmware lê `I2S_CHANNEL_FMT_ONLY_RIGHT` — **o pino L/R do INMP441 precisa
estar aterrado (GND)** para o módulo falar no canal direito. Se estiver em
VDD, o firmware vai ler silêncio mesmo com o microfone funcionando.

## Conexão USB / porta serial

A placa expõe a porta serial através de um **conversor USB-UART externo
(chip WCH, VID 0x1A86)**, não pelo USB nativo do ESP32-S3. No macOS ela
aparece como `/dev/cu.usbmodemXXXXXXXX`. Ver [troubleshooting.md](troubleshooting.md)
para o porquê disso importar na configuração de build.

## Ponto de atenção — mau contato

As capturas em `leituras_mic.csv` mostram evidência forte de **mau contato
elétrico** nas conexões do INMP441 (ver [analise-dados.md](analise-dados.md)):
saltos abruptos de amplitude e picos colados no teto teórico do ADC, típicos
de fiação solta, não de sinal acústico real. Antes de confiar nas
leituras, reconecte fisicamente VDD, GND, SCK, WS e SD com firmeza (idealmente
solda ou conector JST em vez de jumpers soltos em protoboard).
