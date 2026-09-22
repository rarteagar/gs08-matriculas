#!/usr/bin/env python3
"""GS08 · Matrículas y Notas | genera la revisión inicial de Alembic

Autor: @dev | T1.1 | Sprint 1

POR QUE EXISTE ESTE SCRIPT (decisión D-14)
`db/init/*.sql` es el esquema base del volumen de Docker y Alembic es el que
aplica el DDL en el cluster (Job `gs08-migraciones`). Si cada uno se escribe por
su lado hay DOS verdades del esquema. Este script copia los scripts de @analista
tal cual dentro de una revisión de Alembic, y la comprobación de T1.1 compara el
esquema resultante de las dos rutas (deben ser idénticos).

Uso (desde backend/):
    python herramientas/generar_revision_inicial.py
"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
RAIZ = BACKEND.parent
INIT = RAIZ / "db" / "init"
DESTINO = BACKEND / "alembic" / "versions" / "0001_esquema_inicial.py"
ARCHIVOS = ["01-schema.sql", "02-view.sql", "03-seed.sql", "04-notas.sql"]


def quitar_comentarios(script: str) -> str:
    """Los `--` de cabecera son documentación del script, no SQL que se ejecute."""
    return "\n".join(linea for linea in script.splitlines() if not linea.strip().startswith("--"))


def separar_sentencias(script: str) -> list[str]:
    """Separa por ';' respetando el cuerpo de las funciones ($$ ... $$).

    Sin esto, el trigger de RN-14 (04-notas.sql) se partiría por la mitad.
    """
    limpio = quitar_comentarios(script)
    sentencias: list[str] = []
    buffer: list[str] = []
    dentro_de_dolares = False
    i = 0
    while i < len(limpio):
        if limpio.startswith("$$", i):
            dentro_de_dolares = not dentro_de_dolares
            buffer.append("$$")
            i += 2
            continue
        caracter = limpio[i]
        if caracter == ";" and not dentro_de_dolares:
            sentencias.append("".join(buffer).strip())
            buffer = []
        else:
            buffer.append(caracter)
        i += 1
    resto = "".join(buffer).strip()
    if resto:
        sentencias.append(resto)
    return [s for s in sentencias if s]


def escribir(nombre: str, sentencias: list[str]) -> str:
    lineas = [f"    # --- {nombre} ({len(sentencias)} sentencias) ---"]
    for sentencia in sentencias:
        texto = sentencia.replace('"""', '\\"\\"\\"')
        # r""" para que los \. de las expresiones regulares del DDL no sean
        # secuencias de escape inválidas en Python (SyntaxWarning, visto en pytest)
        lineas.append(f'    (\n        "{nombre}",\n        r"""{texto}""",\n    ),')
    return "\n".join(lineas)


def main() -> int:
    bloques = []
    total = 0
    for nombre in ARCHIVOS:
        ruta = INIT / nombre
        if not ruta.exists():
            print(f"FALTA {ruta}", file=sys.stderr)
            return 1
        sentencias = separar_sentencias(ruta.read_text(encoding="utf-8"))
        # unaccent es requisito del esquema base (01-schema.sql) y el trigger de
        # RN-14 vive en 04-notas.sql: las dos cosas entran en esta revisión (D-14)
        bloques.append(escribir(nombre, sentencias))
        total += len(sentencias)
        print(f"  {nombre}: {len(sentencias)} sentencias")

    contenido = '''"""esquema inicial: espejo exacto de db/init/*.sql

Revision ID: 0001_esquema_inicial
Revises:
Create Date: 21/09/2026 (Sprint 1)

GENERADO por backend/herramientas/generar_revision_inicial.py — NO editar a mano.
Fuente: db/init/01-schema.sql, 02-view.sql, 03-seed.sql, 04-notas.sql (autor @analista).

Incluye, como exige D-14:
  * CREATE EXTENSION IF NOT EXISTS unaccent  (sin ella C-08 es incumplible: BUG-07)
  * las 5 tablas (4 del legacy + notas), los CHECK/UNIQUE/FK y los índices
  * las 2 vistas: v_matriculas_detalle y v_notas_detalle
  * el trigger de RN-14 (no se califica una matrícula retirada)
  * los datos del seed (12 estudiantes / 7 cursos / 24 matrículas / 1 admin) con
    ON CONFLICT DO NOTHING y la sincronización de las secuencias IDENTITY

Así `alembic upgrade head` sobre una base limpia deja exactamente el mismo
esquema y los mismos datos que el volumen creado por db/init/.
"""
from collections.abc import Sequence

from alembic import op

revision: str = "0001_esquema_inicial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# (archivo de origen, sentencia SQL) — se ejecutan en el orden de db/init/
SENTENCIAS: list[tuple[str, str]] = [
# __BLOQUES__
]


def upgrade() -> None:
    for origen, sentencia in SENTENCIAS:
        op.execute(sentencia)


def downgrade() -> None:
    """Baja explícita: el esquema del legacy no tiene datos que conservar."""
    op.execute("DROP TRIGGER IF EXISTS tr_notas_matricula_activa ON notas")
    op.execute("DROP FUNCTION IF EXISTS fn_notas_matricula_activa()")
    op.execute("DROP VIEW IF EXISTS v_notas_detalle")
    op.execute("DROP VIEW IF EXISTS v_matriculas_detalle")
    op.execute("DROP TABLE IF EXISTS notas")
    op.execute("DROP TABLE IF EXISTS matriculas")
    op.execute("DROP TABLE IF EXISTS cursos")
    op.execute("DROP TABLE IF EXISTS estudiantes")
    op.execute("DROP TABLE IF EXISTS usuarios")
    op.execute("DROP EXTENSION IF EXISTS unaccent")
'''
    contenido = contenido.replace("# __BLOQUES__", "\n".join(bloques))

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    DESTINO.write_text(contenido, encoding="utf-8", newline="\n")
    print(f"escrito {DESTINO.relative_to(RAIZ)} con {total} sentencias")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
