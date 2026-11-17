#!/usr/bin/env python3
"""Legge in continuo le velocità manuali dei ventilatori (sola lettura).

Con le fasce orarie disattivate, cambia la velocità dal pannello una tacca
alla volta: lo script stampa una riga ogni volta che i valori cambiano.

    1614  velocità mandata in regolazione manuale
    1858  velocità ripresa in regolazione manuale
    639   uscita reale ventilatore mandata
    640   uscita reale ventilatore ripresa

Nessuna dipendenza esterna: usa solo la libreria standard di Python.
Legge con la funzione 03 (Read Holding Registers), non scrive mai nulla.

Uso:
    python3 tools/fan_speed_watch.py 192.168.1.50
    python3 tools/fan_speed_watch.py 192.168.1.50 --interval 1 -o velocita.csv

Ctrl+C (o lo stop di a-Shell) per terminare.
"""

from __future__ import annotations

import argparse
import socket
import struct
import sys
import time

REGISTERS = (
    (1614, "mandata manuale"),
    (1858, "ripresa manuale"),
    (639, "uscita mandata"),
    (640, "uscita ripresa"),
)


class ModbusTcp:
    def __init__(self, host: str, port: int, unit: int, timeout: float) -> None:
        self.host, self.port, self.unit, self.timeout = host, port, unit, timeout
        self.sock: socket.socket | None = None
        self.tid = 0

    def connect(self) -> None:
        self.close()
        self.sock = socket.create_connection((self.host, self.port), self.timeout)
        self.sock.settimeout(self.timeout)

    def close(self) -> None:
        if self.sock:
            self.sock.close()
            self.sock = None

    def _recv(self, n: int) -> bytes:
        buf = b""
        while len(buf) < n:
            chunk = self.sock.recv(n - len(buf))
            if not chunk:
                raise ConnectionError("connessione chiusa dal gateway")
            buf += chunk
        return buf

    def read_holding(self, address: int) -> int:
        self.tid = (self.tid + 1) & 0xFFFF
        pdu = struct.pack(">BHH", 3, address, 1)
        self.sock.sendall(struct.pack(">HHHB", self.tid, 0, len(pdu) + 1, self.unit) + pdu)
        while True:
            tid, _, length, _ = struct.unpack(">HHHB", self._recv(7))
            body = self._recv(length - 1)
            if tid == self.tid:
                break  # scarta eventuali risposte tardive a richieste precedenti
        if body[0] & 0x80:
            raise ConnectionError(f"Modbus exception {body[1]} sul registro {address}")
        return struct.unpack(">H", body[2:4])[0]


def read_all(client: ModbusTcp) -> tuple[float, ...]:
    """Valori in %, nell'ordine di REGISTERS (i registri sono in centesimi)."""
    return tuple(client.read_holding(addr) / 100 for addr, _ in REGISTERS)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("host", help="IP del gateway RS485-Ethernet")
    p.add_argument("--port", type=int, default=502)
    p.add_argument("--unit", type=int, default=1, help="indirizzo Modbus della scheda (H11)")
    p.add_argument("--interval", type=float, default=2.0, help="secondi tra una lettura e l'altra")
    p.add_argument("--timeout", type=float, default=2.0)
    p.add_argument("-o", "--output", help="salva anche le righe in questo file CSV")
    args = p.parse_args()

    client = ModbusTcp(args.host, args.port, args.unit, args.timeout)
    try:
        client.connect()
    except OSError as err:
        print(f"Impossibile collegarsi a {args.host}:{args.port} ({err}).", file=sys.stderr)
        return 1

    out = open(args.output, "w", encoding="utf-8") if args.output else None
    header = "ora," + ",".join(f"{addr} {name}" for addr, name in REGISTERS)
    print(header)
    if out:
        out.write(header + "\n")

    last = None
    try:
        while True:
            try:
                values = read_all(client)
            except (OSError, ConnectionError) as err:
                print(f"errore di lettura ({err}), riprovo...", file=sys.stderr)
                time.sleep(args.interval)
                try:
                    client.connect()
                except OSError:
                    pass
                continue
            if values != last:
                line = time.strftime("%H:%M:%S") + "," + ",".join(f"{v:g}%" for v in values)
                print(line)
                if out:
                    out.write(line + "\n")
                    out.flush()
                last = values
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass
    finally:
        client.close()
        if out:
            out.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
