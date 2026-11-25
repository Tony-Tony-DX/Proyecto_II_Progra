"""Generador de datos simulados con semilla fija (reproducible).

Genera en data/:
- titularidad.csv          cliente - cuenta (grafo bipartito)
- transacciones.csv        registro de eventos de transferencias (junio 2026)
- retiros_atm.csv          retiros con tarjeta en cajeros
- patrones_esperados.json  patrones insertados a propósito (resultado esperado)

Tráfico normal (sin ciclos, para que los ciclos insertados sean el resultado
esperado):
- persona -> comercio (pagos de 20 a 800 soles)
- comercio -> mayorista (compras de 1 000 a 9 000 soles)
- persona -> persona solo de un índice menor a uno mayor (50 a 500 soles)

Patrones insertados (tipologías inspiradas en la UIF-Perú):
- Pitufeo:          18 depósitos de 2 500 a 2 990 soles (justo bajo el umbral
                    simulado de 3 000) desde 8 cuentas hacia E_ORO01 en 48 horas,
                    a través de agentes de Ocongate y Quincemil.
- Ciclo de fondos:  E_COM1 -> E_COM2 -> E_COM3 -> E_COM4 -> E_COM1, tres veces.
- Cuenta puente:    B_PUENTE01 recibe 50 000 y reenvía ~97 % en menos de 6 h.
- Estratificación:  LY_ORIG -> 3 cuentas -> 2 cuentas -> LY_FINAL (3 capas).
- Viaje imposible:  tarjetas T9001 y T9002 usadas en ciudades distintas en menos
                    tiempo del que toma viajar entre ellas.

Ejecución:  python -m src.generador_datos
"""

import json
import random
from datetime import datetime, timedelta

from src.utils import escribir_csv, ruta_datos

SEMILLA = 2026
INICIO = datetime(2026, 6, 1)
DIAS = 30
CANALES = ["agencia", "banca_movil", "billetera", "agente"]
AGENCIAS = ["CUS_CEN", "CUS_WAN", "SSB", "SJE", "URU_AG", "CAL", "PIS", "OLL",
            "MPP", "QUI_AG", "SIC_AG", "URC", "ANT"]
CAJEROS_POR_CIUDAD = {
    "Cusco": ["ATM_PLZ", "ATM_SOL", "ATM_AER"],
    "Urubamba": ["ATM_URU"],
    "Ollantaytambo": ["ATM_OLL"],
    "Machupicchu": ["ATM_MPP"],
    "Sicuani": ["ATM_SIC"],
}


def _hora(rng, dia, h_min=7, h_max=21):
    return INICIO + timedelta(days=dia, hours=rng.randint(h_min, h_max - 1),
                              minutes=rng.randint(0, 59))


def _f(fecha):
    return fecha.strftime("%Y-%m-%d %H:%M")


def generar(semilla=SEMILLA):
    rng = random.Random(semilla)

    personas = [f"P{i:04d}" for i in range(1, 301)]
    comercios = [f"C{i:03d}" for i in range(1, 81)]
    mayoristas = [f"M{i:02d}" for i in range(1, 21)]

    # ---------------------------------------------------------- titularidad
    titularidad = []
    for p in personas:
        titularidad.append({"cliente": "CL" + p, "cuenta": p, "tipo_cliente": "persona",
                            "agencia": rng.choice(AGENCIAS)})
    for c in comercios:
        titularidad.append({"cliente": "CL" + c, "cuenta": c, "tipo_cliente": "comercio",
                            "agencia": rng.choice(AGENCIAS)})
    for m in mayoristas:
        titularidad.append({"cliente": "CL" + m, "cuenta": m, "tipo_cliente": "mayorista",
                            "agencia": rng.choice(AGENCIAS)})

    pit_origenes = [f"S{i:02d}" for i in range(1, 9)]
    ciclo = ["E_COM1", "E_COM2", "E_COM3", "E_COM4"]
    puente_receptores = ["R01", "R02", "R03"]
    capa1 = ["LY_C1A", "LY_C1B", "LY_C1C"]
    capa2 = ["LY_C2A", "LY_C2B"]
    especiales = {
        "persona": pit_origenes + puente_receptores,
        "empresa": ["E_ORO01"] + ciclo + ["X_ORIG01", "B_PUENTE01", "LY_ORIG"]
                   + capa1 + capa2 + ["LY_FINAL"],
    }
    for tipo, cuentas in especiales.items():
        for c in cuentas:
            titularidad.append({"cliente": "CL" + c, "cuenta": c, "tipo_cliente": tipo,
                                "agencia": rng.choice(["OCO", "QCM", "CUS_CEN", "QUI_AG"])})
    # Una empresa con dos cuentas (relación cliente - cuenta 1 a N)
    titularidad.append({"cliente": "CLE_COM1", "cuenta": "E_COM1B",
                        "tipo_cliente": "empresa", "agencia": "CUS_CEN"})

    # --------------------------------------------------------- transacciones
    tx = []

    def agregar(origen, destino, monto, fecha, canal, agencia=None):
        tx.append({"origen": origen, "destino": destino, "monto": round(monto, 2),
                   "fecha_hora": _f(fecha), "canal": canal,
                   "agencia": agencia or rng.choice(AGENCIAS)})

    for _ in range(3500):
        agregar(rng.choice(personas), rng.choice(comercios), rng.uniform(20, 800),
                _hora(rng, rng.randrange(DIAS)), rng.choice(CANALES))
    for _ in range(1000):
        agregar(rng.choice(comercios), rng.choice(mayoristas), rng.uniform(1000, 9000),
                _hora(rng, rng.randrange(DIAS)), rng.choice(["agencia", "banca_movil"]))
    for _ in range(500):
        i, j = sorted(rng.sample(range(len(personas)), 2))
        agregar(personas[i], personas[j], rng.uniform(50, 500),
                _hora(rng, rng.randrange(DIAS)), rng.choice(["banca_movil", "billetera"]))

    # Pitufeo: 18 depósitos fraccionados en 48 horas (10 y 11 de junio)
    base = datetime(2026, 6, 10, 8, 0)
    for k in range(18):
        agregar(pit_origenes[k % 8], "E_ORO01", rng.uniform(2500, 2990),
                base + timedelta(minutes=k * 160), "agente",
                rng.choice(["OCO", "QCM"]))

    # Ciclo de fondos entre comercializadoras relacionadas (3 rondas)
    for ronda, dia in enumerate([5, 12, 19]):
        monto = 90000 - ronda * 1500
        t = datetime(2026, 6, dia, 9, 0)
        for a, b in zip(ciclo, ciclo[1:] + ciclo[:1]):
            agregar(a, b, monto, t, "banca_movil", "CUS_CEN")
            monto *= 0.985
            t += timedelta(hours=5)

    # Cuenta puente: recibe 50 000 y reenvía casi todo en menos de 6 horas
    agregar("X_ORIG01", "B_PUENTE01", 50000, datetime(2026, 6, 15, 9, 0), "agencia", "QUI_AG")
    for k, (r, m) in enumerate(zip(puente_receptores, [16200, 15900, 16400])):
        agregar("B_PUENTE01", r, m, datetime(2026, 6, 15, 11 + k, 30), "banca_movil", "QUI_AG")

    # Estratificación en tres capas
    for c in capa1:
        agregar("LY_ORIG", c, 40000, datetime(2026, 6, 20, 10, 0), "banca_movil", "CUS_CEN")
    agregar("LY_C1A", "LY_C2A", 38500, datetime(2026, 6, 21, 9, 0), "banca_movil")
    agregar("LY_C1B", "LY_C2A", 19800, datetime(2026, 6, 21, 10, 0), "banca_movil")
    agregar("LY_C1B", "LY_C2B", 19500, datetime(2026, 6, 21, 10, 30), "banca_movil")
    agregar("LY_C1C", "LY_C2B", 38800, datetime(2026, 6, 21, 11, 0), "banca_movil")
    agregar("LY_C2A", "LY_FINAL", 57600, datetime(2026, 6, 22, 15, 0), "banca_movil")
    agregar("LY_C2B", "LY_FINAL", 57400, datetime(2026, 6, 22, 16, 0), "banca_movil")

    # Vínculos de las cuentas sospechosas con cuentas normales (proximidad)
    agregar("P0007", "E_COM1", 350, datetime(2026, 6, 8, 12, 0), "billetera")
    agregar("P0123", "E_COM1", 420, datetime(2026, 6, 9, 16, 0), "billetera")
    agregar("R01", "C005", 4800, datetime(2026, 6, 16, 10, 0), "banca_movil")
    agregar("E_ORO01", "M03", 6500, datetime(2026, 6, 13, 9, 0), "agencia")

    tx.sort(key=lambda t: t["fecha_hora"])
    for i, t in enumerate(tx, start=1):
        t["id"] = f"TX{i:05d}"

    # ----------------------------------------------------------- retiros ATM
    retiros = []
    ciudades = list(CAJEROS_POR_CIUDAD)
    pesos_ciudad = [0.6, 0.12, 0.08, 0.12, 0.08]
    for i in range(1, 301):
        tarjeta = f"T{i:04d}"
        ciudad = rng.choices(ciudades, pesos_ciudad)[0]
        dias = rng.sample(range(DIAS), rng.randint(1, 4))  # máximo un retiro por día
        for d in dias:
            retiros.append({"tarjeta": tarjeta, "cajero": rng.choice(CAJEROS_POR_CIUDAD[ciudad]),
                            "fecha_hora": _f(_hora(rng, d, 6, 22)),
                            "monto": rng.choice([100, 200, 300, 400, 500])})
    # Turista legítimo: Cusco por la mañana y Machupicchu por la noche (9 h después)
    retiros.append({"tarjeta": "T0250", "cajero": "ATM_PLZ", "fecha_hora": "2026-06-10 08:00", "monto": 400})
    retiros.append({"tarjeta": "T0250", "cajero": "ATM_MPP", "fecha_hora": "2026-06-10 17:00", "monto": 300})
    # Viajes imposibles (tarjetas clonadas)
    retiros.append({"tarjeta": "T9001", "cajero": "ATM_PLZ", "fecha_hora": "2026-06-24 10:05", "monto": 500})
    retiros.append({"tarjeta": "T9001", "cajero": "ATM_MPP", "fecha_hora": "2026-06-24 11:20", "monto": 500})
    retiros.append({"tarjeta": "T9002", "cajero": "ATM_AER", "fecha_hora": "2026-06-24 08:00", "monto": 400})
    retiros.append({"tarjeta": "T9002", "cajero": "ATM_SIC", "fecha_hora": "2026-06-24 09:30", "monto": 400})
    retiros = [r for r in retiros if not (r["tarjeta"] == "T0250" and r["fecha_hora"][:10] == "2026-06-10"
                                         and r["cajero"] not in ("ATM_PLZ", "ATM_MPP"))]
    retiros.sort(key=lambda r: (r["tarjeta"], r["fecha_hora"]))
    for i, r in enumerate(retiros, start=1):
        r["id"] = f"RT{i:04d}"

    esperado = {
        "pitufeo": {"destino": "E_ORO01", "origenes": pit_origenes},
        "ciclo": ciclo,
        "cuenta_puente": "B_PUENTE01",
        "estratificacion": {"origen": "LY_ORIG", "final": "LY_FINAL", "capas": 3},
        "viaje_imposible": ["T9001", "T9002"],
        "viaje_legitimo": ["T0250"],
        "umbral_monto": 3000,
    }
    return titularidad, tx, retiros, esperado


def guardar(semilla=SEMILLA):
    titularidad, tx, retiros, esperado = generar(semilla)
    escribir_csv(ruta_datos("titularidad.csv"), titularidad,
                 ["cliente", "cuenta", "tipo_cliente", "agencia"])
    escribir_csv(ruta_datos("transacciones.csv"), tx,
                 ["id", "origen", "destino", "monto", "fecha_hora", "canal", "agencia"])
    escribir_csv(ruta_datos("retiros_atm.csv"), retiros,
                 ["id", "tarjeta", "cajero", "fecha_hora", "monto"])
    with open(ruta_datos("patrones_esperados.json"), "w", encoding="utf-8") as f:
        json.dump(esperado, f, ensure_ascii=False, indent=2)
    return len(titularidad), len(tx), len(retiros)


if __name__ == "__main__":
    n_cuentas, n_tx, n_ret = guardar()
    print(f"Datos generados con semilla {SEMILLA}: {n_cuentas} cuentas, "
          f"{n_tx} transacciones, {n_ret} retiros en cajeros.")
