"""Convierte uno o varios NFA en DFA mediante construcción de subconjuntos."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from collections import deque
from dataclasses import dataclass
from pathlib import Path


class ErrorEntrada(ValueError):
    """Indica que la entrada no cumple el formato de la práctica."""


@dataclass
class NFA:
    estados: frozenset[int]
    alfabeto: tuple[str, ...]
    iniciales: frozenset[int]
    finales: frozenset[int]
    transiciones: dict[tuple[int, str], frozenset[int]]


@dataclass
class DFA:
    alfabeto: tuple[str, ...]
    estados: list[frozenset[int]]
    inicial: frozenset[int]
    finales: set[frozenset[int]]
    transiciones: dict[tuple[frozenset[int], str], frozenset[int]]


PATRON_CONJUNTO = re.compile(r"\{([^{}]*)\}|0")


def leer_conjunto(texto: str, contexto: str) -> frozenset[int]:
    """Lee '1 2', '{1 2}' o '0' y devuelve un conjunto inmutable."""
    texto = texto.strip()
    if texto in ("", "0"):
        return frozenset()
    if texto.startswith("{") and texto.endswith("}"):
        texto = texto[1:-1].strip()
    try:
        numeros = [int(valor) for valor in texto.split()]
    except ValueError as error:
        raise ErrorEntrada(f"{contexto}: se esperaban estados naturales") from error
    if any(numero <= 0 for numero in numeros):
        raise ErrorEntrada(f"{contexto}: los estados deben ser positivos; use 0 para vacío")
    return frozenset(numeros)


def validar_estados(conjunto: frozenset[int], validos: frozenset[int], contexto: str) -> None:
    desconocidos = sorted(conjunto - validos)
    if desconocidos:
        lista = " ".join(map(str, desconocidos))
        raise ErrorEntrada(f"{contexto}: estado(s) inexistente(s): {lista}")


def leer_casos(archivo) -> list[NFA]:
    """Lee todos los NFA siguiendo exactamente el formato de la guía."""
    lineas = [linea.strip() for linea in archivo if linea.strip()]
    posicion = 0

    def siguiente(contexto: str) -> str:
        nonlocal posicion
        if posicion >= len(lineas):
            raise ErrorEntrada(f"fin inesperado de la entrada al leer {contexto}")
        linea = lineas[posicion]
        posicion += 1
        return linea

    try:
        cantidad = int(siguiente("la cantidad de casos"))
    except ValueError as error:
        raise ErrorEntrada("la cantidad de casos debe ser un entero") from error
    if cantidad <= 0:
        raise ErrorEntrada("la cantidad de casos debe ser mayor que cero")

    casos = []
    for numero_caso in range(1, cantidad + 1):
        try:
            cantidad_estados = int(siguiente(f"los estados del caso {numero_caso}"))
        except ValueError as error:
            raise ErrorEntrada(f"caso {numero_caso}: cantidad de estados inválida") from error
        if cantidad_estados <= 0:
            raise ErrorEntrada(f"caso {numero_caso}: debe existir al menos un estado")

        estados = frozenset(range(1, cantidad_estados + 1))
        iniciales = leer_conjunto(siguiente("los estados iniciales"), "estados iniciales")
        validar_estados(iniciales, estados, "estados iniciales")

        alfabeto = tuple(siguiente("el alfabeto").split())
        if not alfabeto or len(alfabeto) != len(set(alfabeto)):
            raise ErrorEntrada("el alfabeto debe contener símbolos únicos")
        if any(len(simbolo) != 1 or not ("a" <= simbolo <= "z") for simbolo in alfabeto):
            raise ErrorEntrada("el alfabeto solo puede contener letras minúsculas de a a z")

        finales = leer_conjunto(siguiente("los estados finales"), "estados finales")
        validar_estados(finales, estados, "estados finales")

        transiciones = {}
        for estado_esperado in range(1, cantidad_estados + 1):
            fila = siguiente(f"la fila del estado {estado_esperado}")
            partes = fila.split(maxsplit=1)
            if len(partes) != 2 or not partes[0].isdigit():
                raise ErrorEntrada(f"fila {estado_esperado}: formato incorrecto")
            estado = int(partes[0])
            if estado != estado_esperado:
                raise ErrorEntrada(f"se esperaba la fila del estado {estado_esperado}, no la del {estado}")

            coincidencias = list(PATRON_CONJUNTO.finditer(partes[1]))
            if len(coincidencias) != len(alfabeto):
                raise ErrorEntrada(
                    f"fila {estado}: se esperaban {len(alfabeto)} transiciones"
                )

            # Verifica que no haya texto extraño entre los conjuntos.
            resto = PATRON_CONJUNTO.sub("", partes[1])
            if resto.strip():
                raise ErrorEntrada(f"fila {estado}: conjunto de transición incorrecto")

            for simbolo, coincidencia in zip(alfabeto, coincidencias):
                destino = leer_conjunto(coincidencia.group(0), f"transición ({estado}, {simbolo})")
                validar_estados(destino, estados, f"transición ({estado}, {simbolo})")
                transiciones[(estado, simbolo)] = destino

        casos.append(NFA(estados, alfabeto, iniciales, finales, transiciones))

    if posicion != len(lineas):
        raise ErrorEntrada("hay contenido adicional después del último caso")
    return casos


def convertir_a_dfa(nfa: NFA) -> DFA:
    """Aplica construcción de subconjuntos y conserva solo estados alcanzables."""
    inicial = nfa.iniciales
    estados = [inicial]
    descubiertos = {inicial}
    pendientes = deque([inicial])
    transiciones = {}

    while pendientes:
        actual = pendientes.popleft()
        for simbolo in nfa.alfabeto:
            destino = frozenset(
                estado_destino
                for estado in actual
                for estado_destino in nfa.transiciones[(estado, simbolo)]
            )
            transiciones[(actual, simbolo)] = destino
            if destino not in descubiertos:
                descubiertos.add(destino)
                estados.append(destino)
                pendientes.append(destino)

    finales = {estado for estado in estados if estado & nfa.finales}
    return DFA(nfa.alfabeto, estados, inicial, finales, transiciones)


def mostrar_conjunto(conjunto: frozenset[int], separador: str = " ") -> str:
    if not conjunto:
        return "0"
    return "{" + separador.join(map(str, sorted(conjunto))) + "}"


def crear_tabla(dfa: DFA, numero_caso: int) -> str:
    """Crea la misma tabla de salida que la versión original."""
    nombres = {estado: f"D{indice}" for indice, estado in enumerate(dfa.estados)}
    encabezados = ["Type", "State", "Subset", *dfa.alfabeto]
    filas = []

    for estado in dfa.estados:
        inicial = estado == dfa.inicial
        final = estado in dfa.finales
        marca = "->*" if inicial and final else "->" if inicial else "*" if final else "-"
        fila = [marca, nombres[estado], mostrar_conjunto(estado)]
        fila += [nombres[dfa.transiciones[(estado, simbolo)]] for simbolo in dfa.alfabeto]
        filas.append(fila)

    anchos = [
        max(len(encabezados[columna]), *(len(fila[columna]) for fila in filas))
        for columna in range(len(encabezados))
    ]

    def alinear(fila: list[str]) -> str:
        return "  ".join(valor.ljust(anchos[i]) for i, valor in enumerate(fila)).rstrip()

    return "\n".join([f"Case {numero_caso}", alinear(encabezados), *(alinear(fila) for fila in filas)])


def citar_dot(texto: str) -> str:
    texto = texto.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{texto}"'


def diagrama_nfa(nfa: NFA) -> str:
    lineas = ["digraph NFA {", "  rankdir=LR;", "  node [shape=circle];", "  __inicio [shape=point];"]
    for estado in sorted(nfa.estados):
        forma = "doublecircle" if estado in nfa.finales else "circle"
        lineas.append(f"  q{estado} [label={citar_dot(str(estado))}, shape={forma}];")
    for estado in sorted(nfa.iniciales):
        lineas.append(f"  __inicio -> q{estado};")

    aristas = {}
    for origen in sorted(nfa.estados):
        for simbolo in nfa.alfabeto:
            for destino in sorted(nfa.transiciones[(origen, simbolo)]):
                aristas.setdefault((origen, destino), []).append(simbolo)
    for (origen, destino), simbolos in sorted(aristas.items()):
        lineas.append(f"  q{origen} -> q{destino} [label={citar_dot(', '.join(simbolos))}];")
    return "\n".join(lineas + ["}", ""])


def diagrama_dfa(dfa: DFA) -> str:
    nombres = {estado: f"D{indice}" for indice, estado in enumerate(dfa.estados)}
    lineas = ["digraph DFA {", "  rankdir=LR;", "  node [shape=circle];", "  __inicio [shape=point];"]
    for estado in dfa.estados:
        nombre = nombres[estado]
        etiqueta = f"{nombre} = {mostrar_conjunto(estado, ', ')}"
        forma = "doublecircle" if estado in dfa.finales else "circle"
        lineas.append(f"  {nombre} [label={citar_dot(etiqueta)}, shape={forma}];")
    lineas.append(f"  __inicio -> {nombres[dfa.inicial]};")

    aristas = {}
    for origen in dfa.estados:
        for simbolo in dfa.alfabeto:
            destino = dfa.transiciones[(origen, simbolo)]
            aristas.setdefault((origen, destino), []).append(simbolo)
    for (origen, destino), simbolos in aristas.items():
        lineas.append(
            f"  {nombres[origen]} -> {nombres[destino]} [label={citar_dot(', '.join(simbolos))}];"
        )
    return "\n".join(lineas + ["}", ""])


def guardar_diagramas(nfas: list[NFA], dfas: list[DFA], carpeta: Path, formato: str) -> None:
    carpeta.mkdir(parents=True, exist_ok=True)
    if formato != "dot" and shutil.which("dot") is None:
        raise RuntimeError("no se encontró Graphviz; instálelo o use --diagram-format dot")

    for numero, (nfa, dfa) in enumerate(zip(nfas, dfas), start=1):
        for nombre, contenido in (("nfa", diagrama_nfa(nfa)), ("dfa", diagrama_dfa(dfa))):
            ruta_dot = carpeta / f"case_{numero}_{nombre}.dot"
            ruta_dot.write_text(contenido, encoding="utf-8")
            if formato != "dot":
                ruta_salida = ruta_dot.with_suffix(f".{formato}")
                subprocess.run(["dot", f"-T{formato}", str(ruta_dot), "-o", str(ruta_salida)], check=True)
                ruta_dot.unlink()


def argumentos():
    analizador = argparse.ArgumentParser(description="Convierte NFA en DFA mediante subconjuntos.")
    analizador.add_argument("--input", type=Path, help="archivo de entrada; por defecto se usa la terminal")
    analizador.add_argument("--output", type=Path, help="archivo de salida; por defecto se usa la terminal")
    analizador.add_argument("--diagram-dir", type=Path, help="carpeta opcional para guardar los diagramas")
    analizador.add_argument(
        "--diagram-format",
        choices=("dot", "svg", "png", "pdf"),
        default="dot",
        help="formato de los diagramas; SVG, PNG y PDF requieren Graphviz",
    )
    return analizador.parse_args()


def ejecutar() -> None:
    opciones = argumentos()
    if opciones.input:
        with opciones.input.open(encoding="utf-8") as archivo:
            nfas = leer_casos(archivo)
    else:
        nfas = leer_casos(sys.stdin)

    dfas = [convertir_a_dfa(nfa) for nfa in nfas]
    salida = "\n".join(crear_tabla(dfa, numero) for numero, dfa in enumerate(dfas, start=1)) + "\n"

    if opciones.output:
        opciones.output.write_text(salida, encoding="utf-8")
    else:
        sys.stdout.write(salida)

    if opciones.diagram_dir:
        guardar_diagramas(nfas, dfas, opciones.diagram_dir, opciones.diagram_format)


if __name__ == "__main__":
    try:
        ejecutar()
    except (ErrorEntrada, OSError, RuntimeError, subprocess.CalledProcessError) as error:
        print(f"Error: {error}", file=sys.stderr)
        raise SystemExit(1)
    