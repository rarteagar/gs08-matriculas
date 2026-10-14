# ============================================================
# GS08 · Matrículas y Notas | tests/dobles.py
# Autor: @dev | Rubrica: BD hibrida, cache y logging
# Dobles de prueba para la segunda base (Mongo), la cache (Redis) y el servidor de
# logs (Loki). Sirven para probar el codigo de verdad SIN depender de tener los
# servicios levantados: la suite del CI solo trae PostgreSQL.
# ============================================================
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from types import SimpleNamespace


class CursorFalso:
    """Imita el cursor de pymongo: .sort(...).limit(...) y luego iterable."""

    def __init__(self, documentos: list) -> None:
        self.documentos = list(documentos)

    def sort(self, campo: str, direccion: int = -1):
        self.documentos.sort(key=lambda d: d.get(campo), reverse=direccion == -1)
        return self

    def limit(self, cantidad: int):
        self.documentos = self.documentos[:cantidad]
        return self

    def __iter__(self):
        return iter(self.documentos)


class ColeccionFalsa:
    def __init__(self) -> None:
        self.documentos: list[dict] = []
        self.indices: list = []

    def create_index(self, campos, **opciones):
        self.indices.append((campos, opciones))
        return "indice"

    def insert_one(self, documento):
        self.documentos.append(dict(documento))
        return SimpleNamespace(inserted_id=len(self.documentos))

    def find(self, filtro=None, proyeccion=None):
        filtro = filtro or {}
        salida = [d for d in self.documentos if all(d.get(k) == v for k, v in filtro.items())]
        if proyeccion:
            salida = [{k: v for k, v in d.items() if k != "_id"} for d in salida]
        return CursorFalso(salida)

    def count_documents(self, filtro=None) -> int:
        filtro = filtro or {}
        return sum(1 for d in self.documentos if all(d.get(k) == v for k, v in filtro.items()))

    def find_one(self, filtro=None, proyeccion=None):
        for documento in self.find(filtro, proyeccion):
            return documento
        return None

    def replace_one(self, filtro, documento, upsert=False):
        for posicion, existente in enumerate(self.documentos):
            if all(existente.get(k) == v for k, v in filtro.items()):
                self.documentos[posicion] = dict(documento)
                return SimpleNamespace(modified_count=1)
        if upsert:
            self.documentos.append(dict(documento))
        return SimpleNamespace(modified_count=0)

    def estimated_document_count(self) -> int:
        return len(self.documentos)


class BaseFalsa:
    """Imita el objeto base de pymongo: base["coleccion"]."""

    def __init__(self) -> None:
        self.colecciones: dict[str, ColeccionFalsa] = {}

    def __getitem__(self, nombre: str) -> ColeccionFalsa:
        return self.colecciones.setdefault(nombre, ColeccionFalsa())


class RedisFalso:
    def __init__(self) -> None:
        self.valores: dict[str, str] = {}
        self.ttls: dict[str, int | None] = {}
        self.borrados: list[str] = []

    def ping(self) -> bool:
        return True

    def get(self, clave: str):
        return self.valores.get(clave)

    def set(self, clave: str, valor: str, ex: int | None = None) -> bool:
        self.valores[clave] = valor
        self.ttls[clave] = ex
        return True

    def delete(self, *claves: str) -> int:
        self.borrados.extend(claves)
        return sum(1 for clave in claves if self.valores.pop(clave, None) is not None)


class ServidorLoki:
    """Servidor HTTP de juguete que hace de Loki: guarda lo que le empujan."""

    def __init__(self) -> None:
        self.peticiones: list[dict] = []
        padre = self

        class Manejador(BaseHTTPRequestHandler):
            def do_POST(self):  # noqa: N802 (nombre impuesto por la librería)
                largo = int(self.headers.get("Content-Length", 0))
                padre.peticiones.append(json.loads(self.rfile.read(largo)))
                self.send_response(204)
                self.end_headers()

            def log_message(self, *args):  # silencio: no ensucia la salida de pytest
                return

        self.servidor = HTTPServer(("127.0.0.1", 0), Manejador)
        self.puerto = self.servidor.server_address[1]
        self.hilo = threading.Thread(target=self.servidor.serve_forever, daemon=True)
        self.hilo.start()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.puerto}"

    def detener(self) -> None:
        self.servidor.shutdown()
        self.servidor.server_close()
