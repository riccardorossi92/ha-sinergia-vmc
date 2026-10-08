#!/usr/bin/env python3
"""Scansione (sola lettura) dei holding register della VMC via gateway Modbus TCP.

Nessuna dipendenza esterna: usa solo la libreria standard di Python.
Legge con la funzione 03 (Read Holding Registers), non scrive mai nulla.

Uso:
    python3 tools/modbus_scan.py 192.168.1.50
    python3 tools/modbus_scan.py 192.168.1.50 --start 0 --end 3000 --unit 1 -o scan.csv

Il CSV contiene per ogni indirizzo: valore senza segno, con segno, esadecimale,
oppure l'errore Modbus restituito dalla scheda (es. "illegal data address"
per i registri non esistenti).
"""

from __future__ import annotations

import argparse
import csv
import socket
import struct
import sys
import time

EXCEPTIONS = {
    1: "illegal function",
    2: "illegal data address",
    3: "illegal data value",
    4: "device failure",
    6: "device busy",
    10: "gateway path unavailable",
    11: "gateway target no response",
}


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

    def read_holding(self, address: int, count: int) -> list[int] | str:
        """Ritorna la lista di valori, oppure una stringa con l'errore Modbus."""
        self.tid = (self.tid + 1) & 0xFFFF
        pdu = struct.pack(">BHH", 3, address, count)
        self.sock.sendall(struct.pack(">HHHB", self.tid, 0, len(pdu) + 1, self.unit) + pdu)
        while True:
            tid, _, length, _ = struct.unpack(">HHHB", self._recv(7))
            body = self._recv(length - 1)
            if tid == self.tid:
                break  # scarta eventuali risposte tardive a richieste precedenti
        if body[0] & 0x80:
            return EXCEPTIONS.get(body[1], f"exception {body[1]}")
        nbytes = body[1]
        return list(struct.unpack(f">{nbytes // 2}H", body[2 : 2 + nbytes]))


def read_one(client: ModbusTcp, address: int, retries: int) -> int | str:
    for attempt in range(retries + 1):
        try:
            result = client.read_holding(address, 1)
            return result if isinstance(result, str) else result[0]
        except (OSError, ConnectionError) as err:
            if attempt == retries:
                return f"timeout/errore: {err}"
            time.sleep(0.5)
            client.connect()
    return "errore"


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("host", help="IP del gateway RS485-Ethernet")
    p.add_argument("--port", type=int, default=502)
    p.add_argument("--unit", type=int, default=1, help="indirizzo Modbus della scheda (H11)")
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--end", type=int, default=3000, help="ultimo indirizzo incluso")
    p.add_argument("--block", type=int, default=20, help="registri per richiesta (0/1 = uno alla volta)")
    p.add_argument("--timeout", type=float, default=2.0)
    p.add_argument("--retries", type=int, default=2)
    p.add_argument("--delay", type=float, default=0.03, help="pausa tra richieste (s)")
    p.add_argument("-o", "--output", default="modbus_scan.csv")
    args = p.parse_args()

    client = ModbusTcp(args.host, args.port, args.unit, args.timeout)
    try:
        client.connect()
    except OSError as err:
        print(
            f"Impossibile collegarsi a {args.host}:{args.port} ({err}).\n"
            "Controlla che sia l'IP del gateway RS485-Ethernet (lo stesso configurato "
            "in Home Assistant) e che il Mac sia sulla stessa rete.",
            file=sys.stderr,
        )
        return 1
    results: dict[int, int | str] = {}
    block = max(1, args.block)

    addr = args.start
    while addr <= args.end:
        count = min(block, args.end - addr + 1)
        try:
            values = client.read_holding(addr, count) if count > 1 else None
        except (OSError, ConnectionError):
            client.connect()
            values = None
        if isinstance(values, list) and len(values) == count:
            for i, v in enumerate(values):
                results[addr + i] = v
        else:
            # blocco non leggibile (registri inesistenti in mezzo): uno alla volta
            for a in range(addr, addr + count):
                results[a] = read_one(client, a, args.retries)
                time.sleep(args.delay)
        addr += count
        print(f"\r{addr - args.start}/{args.end - args.start + 1} registri", end="", file=sys.stderr)
        time.sleep(args.delay)
    client.close()
    print(file=sys.stderr)

    found = 0
    with open(args.output, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["indirizzo", "valore", "con_segno", "hex", "errore"])
        for a in sorted(results):
            v = results[a]
            if isinstance(v, int):
                found += 1
                w.writerow([a, v, v - 0x10000 if v >= 0x8000 else v, f"0x{v:04X}", ""])
            else:
                w.writerow([a, "", "", "", v])
    print(f"Fatto: {found} registri leggibili su {len(results)}. Salvato in {args.output}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
