# Troubleshooting — histórico

## `Serial.print` não aparecia no monitor

**Sintoma:** upload e build funcionando, monitor conectando na porta certa,
mas nenhuma linha aparecia.

**Causa:** a definição da placa
(`~/.platformio/platforms/espressif32/boards/4d_systems_esp32s3_gen4_r8n16.json`)
injeta por padrão `-DARDUINO_USB_MODE=1` e `-DARDUINO_USB_CDC_ON_BOOT=1`,
o que redireciona o objeto `Serial` para o **USB nativo do ESP32-S3**
(pinos D+/D- dedicados). Só que a porta física realmente conectada ao Mac é
um **conversor USB-UART externo (chip WCH, VID `0x1A86`)**, ligado ao UART0
físico da placa — um barramento diferente.

**Fix:** sobrescrever a flag no `platformio.ini` do projeto:

```ini
build_flags =
    -D ARDUINO_USB_CDC_ON_BOOT=0
```

Isso força `Serial` de volta para o UART0, onde o bridge WCH está
escutando. O warning `"ARDUINO_USB_CDC_ON_BOOT" redefined` que aparece no
build é esperado e inofensivo — é só o GCC avisando que a flag da placa foi
sobrescrita pela do projeto (a última definição na linha de comando vence).

## Porta `/dev/cu.usbmodemXXXXXXXX` "busy" ou "no such file"

Duas causas distintas, mesmo texto de erro parecido:

- **"the port is busy"** → outro processo já tem a porta aberta (ex: um
  `pio device monitor` anterior que não foi encerrado). Diagnóstico:
  `lsof /dev/cu.usbmodemXXXXXXXX` mostra o PID culpado; encerre-o
  (Ctrl+C no terminal onde está rodando).
- **"No such file or directory"** → a porta simplesmente não existe mais.
  O macOS troca o nome do dispositivo (`usbmodemXXXXXXXX`) toda vez que o
  cabo é desconectado/reconectado. Diagnóstico: `ls /dev/cu.*` para ver o
  nome atual e atualizar `monitor_port` / `upload_port` no
  `platformio.ini` se necessário.

## Placa não enumerava via hub USB

Conectar a placa através de um hub/adaptador USB-C introduziu falhas de
enumeração (porta nunca aparecia em `/dev/cu.*`, LED da placa piscando em
vez de estabilizar). Hubs baratos costumam ter problemas com dispositivos
USB full-speed/baixa potência como esse bridge WCH. Teste decisivo: conectar
a placa direto no Mac (sem hub) para isolar a causa.

## Leituras do microfone zeradas / com ruído

Ver [analise-dados.md](analise-dados.md) — diagnosticado como mau contato
elétrico na fiação do INMP441, evoluindo de "ruído/saturação intermitente"
para "silêncio total" (contato aberto).

## Repositório git raiz era o HOME inteiro

O `.git` inicial do ambiente estava na raiz de `/Users/francisco-oliveira`
(pasta pessoal inteira), sem nenhum commit. Corrigido criando um
repositório git **aninhado**, próprio, dentro de `Acoustic Intelligence/`,
isolando o histórico do projeto do resto da máquina.
