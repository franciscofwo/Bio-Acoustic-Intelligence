"""
Grava audio do ESP32-S3 (I2S -> INMP441) e salva como .wav pra voce ouvir.

Como funciona: quando voce digita 'r' e aperta Enter, o script manda o
caractere 'r' pela serial. O firmware entao para de imprimir as metricas
por alguns segundos, grava audio bruto (16 bits) e transmite pela mesma
porta USB entre dois marcadores de texto (RECORDING_START / RECORDING_END).
Este script le esses bytes, monta um .wav de verdade (usando o modulo
'wave', que ja vem com o Python - nao precisa instalar mais nada alem do
pyserial) e toca automaticamente com 'afplay' (nativo do macOS).

Requisitos:
    pip3 install pyserial

Uso:
    python3 esp32_wav_recorder.py --port /dev/cu.usbmodem1201
"""

import argparse
import re
import subprocess
import sys
import time
import wave
from datetime import datetime

import serial

START_PATTERN = re.compile(r"RECORDING_START:(\d+):(\d+):(\d+)")


def gravar_uma_vez(ser: serial.Serial, saida_dir: str) -> str:
    ser.reset_input_buffer()
    ser.write(b"r")

    print("Aguardando o ESP32 iniciar a gravacao...")

    # Le linhas de texto ate encontrar o marcador RECORDING_START
    while True:
        linha = ser.readline().decode(errors="ignore").strip()
        if not linha:
            continue
        print("  ESP32:", linha)
        match = START_PATTERN.search(linha)
        if match:
            sample_rate = int(match.group(1))
            bits = int(match.group(2))
            total_bytes = int(match.group(3))
            break

    print(f"Gravando... ({total_bytes / (sample_rate * 2):.1f}s de audio, {total_bytes} bytes)")

    # A partir daqui e leitura binaria pura - sem parsing de texto/linha
    dados = bytearray()
    inicio = time.time()
    while len(dados) < total_bytes:
        pedaco = ser.read(total_bytes - len(dados))
        if not pedaco:
            # timeout sem receber nada - evita loop infinito se a conexao cair
            if time.time() - inicio > 30:
                print("AVISO: parou de receber dados antes do esperado.")
                break
            continue
        dados.extend(pedaco)

    # Consome o resto da linha em branco + "RECORDING_END" antes de voltar
    # ao modo texto normal
    for _ in range(3):
        linha = ser.readline().decode(errors="ignore").strip()
        if linha:
            print("  ESP32:", linha)
        if linha == "RECORDING_END":
            break

    nome_arquivo = f"{saida_dir}/gravacao_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav"
    with wave.open(nome_arquivo, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(bits // 8)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(bytes(dados))

    print(f"Salvo em: {nome_arquivo}")
    return nome_arquivo


def tocar(caminho_wav: str):
    try:
        subprocess.run(["afplay", caminho_wav], check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print(f"(Nao consegui tocar automaticamente - abra o arquivo manualmente: {caminho_wav})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default="/dev/cu.usbmodem1201", help="Porta serial do ESP32")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument("--saida", default=".", help="Pasta onde salvar os .wav")
    args = parser.parse_args()

    ser = serial.Serial(args.port, args.baud, timeout=1)
    time.sleep(2)  # da tempo do ESP32 resetar apos abrir a porta
    ser.reset_input_buffer()

    print("Conectado. Digite 'r' + Enter para gravar 5s de audio, ou 'q' + Enter para sair.")

    while True:
        comando = input("> ").strip().lower()
        if comando == "q":
            break
        if comando == "r":
            caminho = gravar_uma_vez(ser, args.saida)
            tocar(caminho)
        else:
            print("Comando nao reconhecido. Use 'r' para gravar ou 'q' para sair.")

    ser.close()


if __name__ == "__main__":
    main()