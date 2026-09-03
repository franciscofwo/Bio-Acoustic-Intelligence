"""
Le a saida Serial do ESP32 no formato "Chave:valor,Chave:valor,..." (o formato
que o sketch mic_i2s_esp32s3_mfcc.ino / metrics.ino imprime), mostra cada
linha recebida no console (seu "terminal") e, ao lado, plota RMS e Peak
(amplitude do sinal) em tempo real. Salva TODAS as colunas (incluindo os
MFCCs) num CSV para analise posterior.

Requisitos (rode no SEU computador, onde o ESP32 esta conectado via USB):
    pip install pyserial matplotlib

Uso:
    python esp32_serial_logger_v2.py --port COM5          (Windows)
    python esp32_serial_logger_v2.py --port /dev/ttyUSB0  (Linux)
    python esp32_serial_logger_v2.py --port /dev/cu.usbserial-XXXX  (macOS)

Dica: feche o Serial Monitor/Plotter do Arduino IDE antes de rodar este
script - so um programa pode segurar a porta serial por vez.
"""

import argparse
import csv
import time
from collections import deque
from datetime import datetime

#import serial
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


def parse_line(raw: str):
    """Converte 'RMS:123.45,Peak:456.7,dB:80.1' num dict {'RMS': 123.45, ...}.
    Ignora silenciosamente linhas que nao seguem esse formato (ex.: mensagens
    de boot do ESP32)."""
    fields = {}
    for chunk in raw.split(","):
        if ":" not in chunk:
            return None
        key, _, value = chunk.partition(":")
        key = key.strip()
        try:
            fields[key] = float(value.strip())
        except ValueError:
            return None
    return fields if fields else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--port",
        default="/dev/cu.usbmodem1201",  # porta do seu ESP32-S3 (USB JTAG/serial nativo)
        help="Porta serial do ESP32, ex: COM5, /dev/ttyUSB0 ou /dev/cu.usbmodem1201",
    )
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--csv", default="leituras_mic.csv", help="Arquivo CSV de saida (todas as colunas)")
    parser.add_argument("--window", type=int, default=100, help="Quantos pontos manter visiveis no grafico")
    args = parser.parse_args()

    ser = serial.Serial(args.port, args.baud, timeout=1)
    time.sleep(2)  # da tempo do ESP32 resetar apos abrir a porta

    csv_file = None
    csv_writer = None
    csv_header = None

    times = deque(maxlen=args.window)
    rms_values = deque(maxlen=args.window)
    peak_values = deque(maxlen=args.window)

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.suptitle("Amplitude do sinal sonoro (RMS e Peak) em tempo real")

    line_rms, = ax.plot([], [], color="#2a78d6", linewidth=2, label="RMS (amplitude media)")
    line_peak, = ax.plot([], [], color="#eb6834", linewidth=2, label="Peak (amplitude maxima)")
    ax.set_xlabel("tempo (s)")
    ax.set_ylabel("amplitude (unidade bruta do ADC)")
    ax.legend(loc="upper left")
    ax.grid(True, alpha=0.3)

    start_time = time.time()

    def update(_frame):
        nonlocal csv_file, csv_writer, csv_header

        while ser.in_waiting:
            raw = ser.readline().decode(errors="ignore").strip()
            if not raw:
                continue

            # Mostra a linha crua no console - e o "terminal" rodando junto do grafico
            print(raw)

            fields = parse_line(raw)
            if fields is None:
                continue  # linha de boot/erro, sem o formato Chave:valor

            # Cria o CSV com o cabecalho assim que a primeira linha valida chegar
            if csv_writer is None:
                csv_header = ["timestamp"] + list(fields.keys())
                csv_file = open(args.csv, "w", newline="", encoding="utf-8")
                csv_writer = csv.writer(csv_file)
                csv_writer.writerow(csv_header)

            now = datetime.now().isoformat()
            csv_writer.writerow([now] + [fields.get(k, "") for k in csv_header[1:]])
            csv_file.flush()

            t = time.time() - start_time
            times.append(t)
            rms_values.append(fields.get("RMS", 0.0))
            peak_values.append(fields.get("Peak", 0.0))

        if times:
            line_rms.set_data(times, rms_values)
            line_peak.set_data(times, peak_values)
            ax.set_xlim(max(0, times[0]), times[-1] + 0.5)
            top = max(max(rms_values, default=1), max(peak_values, default=1))
            ax.set_ylim(0, top * 1.1 + 1)

        return line_rms, line_peak

    ani = FuncAnimation(fig, update, interval=200, cache_frame_data=False)
    plt.tight_layout()
    plt.show()

    ser.close()
    if csv_file:
        csv_file.close()


if __name__ == "__main__":
    main()