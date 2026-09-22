# GS08 · D-14 verificada — `db/init/*.sql` y la revisión inicial de Alembic son el mismo esquema

**Autor:** @analista · **Fecha:** 21/09/2026 · **Sprint 1** · **Cierra:** D-14 (una sola fuente de verdad
del esquema) y la parte de datos que @qa dejó pendiente («falta la mitad de Alembic»).

**Conclusión: los dos caminos dejan exactamente lo mismo.** 170 líneas de catálogo en cada lado,
**0 diferencias**, y las 5 secuencias en el mismo valor. La migración `0001_esquema_inicial` de @dev
incluye lo que el esquema necesita y no solo las tablas: `unaccent`, el trigger de RN-14, las 2 vistas,
los 18 comentarios y el seed con la sincronización de secuencias.

---

## 1. Cómo se comprobó (mecánico, no leyendo código)

`bash db/verificacion/comparar_con_alembic.sh` levanta **dos bases limpias** en una red propia (no toca el
stack de @devops ni la base de verificación de @analista):

1. **Base A**: PostgreSQL 16.15 con `db/init/` montado como `docker-entrypoint-initdb.d` → corre
   `01-schema.sql`, `02-view.sql`, `03-seed.sql`, `04-notas.sql`.
2. **Base B**: la misma imagen **vacía** → `alembic upgrade head` con la imagen `gs08-api:local`
   (trae Alembic y las dependencias) y el `backend/` del repo montado, o sea la migración tal como está
   en el repositorio hoy.
3. **Foto del catálogo en las dos** con `db/verificacion/catalogo_esquema.sql`: una línea por objeto
   (extensiones, tablas, columnas con tipo/nulabilidad/default, constraints con su definición completa,
   índices con su definición, vistas, funciones con el `md5` de su cuerpo, triggers con su definición,
   secuencias y comentarios) más el **conteo de filas** de cada tabla.
4. **`diff` de las dos fotos.**

```
== 2. Esperando las dos bases (la primera tiene que haber corrido 01 a 04) ==
   db/init lista con 5 tablas en 3s
== 3. alembic upgrade head sobre la base vacia (imagen gs08-api:local) ==
   revision aplicada: 0001_esquema_inicial
== 4. Foto del catalogo de las dos bases ==
  170 catalogo-dbinit.txt
  170 catalogo-alembic.txt
== 5. Comparacion linea por linea ==
   IDENTICOS: los dos caminos dejan el mismo esquema y los mismos datos
== 6. Secuencias: el catalogo compara que existan, no su last_value ==
   usuarios     db/init=1    alembic=1    OK
   estudiantes  db/init=12   alembic=12   OK
   cursos       db/init=7    alembic=7    OK
   matriculas   db/init=24   alembic=24   OK
```

`docs/analisis/evidencia/resumen-d14.txt` (salida completa, exit 0) · `catalogo-dbinit.txt` ·
`catalogo-alembic.txt` · `catalogo-diff.txt` (**vacío**: es la prueba, no un archivo que falta).

### Qué se comparó, contado

| Objeto | Cuántos | Iguales |
|---|---|---|
| Extensiones | 1 (`unaccent` v1.1) | ✅ |
| Tablas | 5 (4 del legacy + `notas`) | ✅ |
| Columnas | 74 (con tipo, nulabilidad y default) | ✅ |
| Constraints | 34 (CHECK, UNIQUE, PK, FK, con su definición completa) | ✅ |
| Índices | 20 (con su definición, incluidos los de las FK) | ✅ |
| Vistas | 2 (`v_matriculas_detalle`, `v_notas_detalle`) | ✅ |
| Funciones | 5 (con `md5` del cuerpo: el de RN-14 y los de `unaccent`) | ✅ |
| Triggers | 1 (`tr_notas_matricula_activa BEFORE INSERT ON notas`) | ✅ |
| Secuencias | 5 (y en el mismo valor: 1 / 12 / 7 / 24) | ✅ |
| Comentarios | 18 (de tabla y de columna) | ✅ |
| Datos del seed | 1 usuario · 12 estudiantes · 7 cursos · 24 matrículas · 0 notas | ✅ |

## 2. Extra: el `downgrade` también es real

`alembic downgrade base` sobre la base migrada deja **0 tablas de negocio, 0 vistas, 0 triggers y 0
`unaccent`**; solo queda `alembic_version`, la tabla de control de Alembic (correcto). Es decir, la
migración sabe volver, no solo avanzar. Evidencia: `docs/analisis/evidencia/d14-downgrade.txt`.

## 3. Un falso verde que encontré en el camino (y por qué importa)

La **primera** corrida del script imprimió «IDENTICOS» con dos archivos de **1 línea**: `docker cp` no
entiende las rutas MSYS (`/d/dev/...`) y las fotos salieron con `GetFileAttributesEx D:\d:`. El `diff` de
dos archivos con el mismo error es, obviamente, idéntico. Agregué al script una **guarda**: si una foto
tiene menos de 100 líneas o contiene `ERROR`/`GetFileAttributes`, sale con **exit 2** y no declara nada.
Vale como lección de retrospectiva: *un verificador que no falla cuando el insumo está roto es peor que no
tenerlo* — el mismo patrón que BUG-01 de @qa con Prometheus.

## 4. Qué NO cubre esta comparación (para no venderla de más)

- **Dueños y permisos** (`OWNER`, `GRANT`): en las dos bases todo lo crea el mismo usuario (`gs08`), así
  que no hay diferencia que medir; si algún día hay roles separados, hay que agregarlo al catálogo.
- **Parámetros físicos** (tablespaces, `fillfactor`, storage): ninguno de los dos caminos los usa.
- **Planes de consulta y estadísticas**: dependen de `ANALYZE` y del volumen; no son parte del esquema.

## 5. Para re-ejecutarlo

```bash
bash db/verificacion/comparar_con_alembic.sh          # exit 0 = identicas; 2 = la foto fallo
docker rm -f gs08-d14-init gs08-d14-alembic && docker network rm gs08-d14-net   # limpiar
```

Requiere la imagen `gs08-api:local`. Si @dev cambia la migración inicial o el `db/init/`, este script es
lo que dice en 40 segundos si siguen siendo el mismo esquema: **es el control de D-14**, y debería correr
en el CI cuando el repo tenga remoto (tarea sugerida para @devops).
