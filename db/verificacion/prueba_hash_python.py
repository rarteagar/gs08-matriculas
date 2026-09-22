"""GS08 - Matriculas y Notas | prueba del hash del seed con la libreria del API
Autor: @analista | Sprint 0

Comprueba que el hash $2y$ del legacy (usuario admin / Admin123!) se verifica con
`bcrypt` de PyPI, que es la libreria que usara el backend FastAPI. Se corre en un
contenedor python para no instalar nada en la maquina:

    docker run --rm -v "D:/dev/equipo/gs08-matriculas/db/verificacion/prueba_hash_python.py:/p.py:ro" \
      python:3.12-slim sh -c "pip install -q bcrypt==4.2.1 && python /p.py"

Salida real guardada en docs/analisis/evidencia/hash-legacy-python-bcrypt.txt:
    prefijo $2y$ (tal cual el legacy)  Admin123!          -> True
    prefijo $2y$ (tal cual el legacy)  clave_equivocada   -> False
"""
import bcrypt

HASH_LEGACY = b"$2y$10$Tzgm/meEuR9o/nxq1ocKBu01ncP.pbnMay7a1aqWsuwXA4Q9Y9nzu"
HASH_2B = HASH_LEGACY.replace(b"$2y$", b"$2b$")

print("bcrypt (PyPI) version:", bcrypt.__version__)
for etiqueta, h in (("prefijo $2y$ (tal cual el legacy)", HASH_LEGACY),
                    ("prefijo $2b$ (mismo digest)", HASH_2B)):
    for pw in (b"Admin123!", b"clave_equivocada"):
        try:
            print(f"{etiqueta:34s} {pw.decode():18s} -> {bcrypt.checkpw(pw, h)}")
        except Exception as e:
            print(f"{etiqueta:34s} {pw.decode():18s} -> ERROR {type(e).__name__}: {e}")
