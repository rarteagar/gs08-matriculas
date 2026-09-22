#!/usr/bin/env bash
# ============================================================
# GS08 - Matriculas y Notas | smoke_api.sh        (T1.7 - @qa)
#
# Prueba de humo de la API. Corre en tres grupos:
#   A) infraestructura por el proxy  (AP-09: health, metrics, balanceo, SPA)
#   B) contrato de la API            (AP-01..AP-08: codigos HTTP y datos del seed)
#   C) recorrido completo            (§3 pasos 1-10 "de la matricula a la nota")
#
# Uso:
#   bash scripts/smoke_api.sh                  # grupos A+B (lo que la API permita hoy)
#   bash scripts/smoke_api.sh --infra          # solo grupo A: lo unico ejecutable con el stub
#   bash scripts/smoke_api.sh --e2e            # A+B+C (crea datos con codigo unico y los borra al final)
#   bash scripts/smoke_api.sh --sin-escritura  # no hace POST/PUT/DELETE
#   bash scripts/smoke_api.sh --url http://otro-host:8080
#
# Variables de entorno: WEB_URL, API_URL, DB_PORT, SMOKE_USUARIO, SMOKE_CLAVE
#
# Codigos de salida:
#   0  todo lo probado salio OK
#   1  hay FALLAS (la API responde, pero incumple un criterio)
#   2  no se pudo conectar (stack caido)
#   3  la API no esta implementada todavia (stub de infraestructura): hallazgos BLOQUEADOS
#
# No usa jq: solo curl + grep/sed (en la maquina de desarrollo jq NO esta instalado y
# el script tiene que correr igual en git-bash, en Ubuntu del CI y en un contenedor).
# Evidencia: docs/qa/evidencia/smoke-api-<fecha>.txt
# ============================================================
set -uo pipefail

RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
EVID="$RAIZ/docs/qa/evidencia"
mkdir -p "$EVID"
TMP="$(mktemp -d)"
# curl es un binario nativo: en git-bash/Windows no entiende la ruta /tmp de MSYS,
# asi que se le pasa la ruta nativa (cygpath) mientras bash sigue leyendo la de MSYS.
# En Linux no existe cygpath y la ruta se usa tal cual.
TMP_NAT="$TMP"
command -v cygpath >/dev/null 2>&1 && TMP_NAT="$(cygpath -w "$TMP" 2>/dev/null || printf '%s' "$TMP")"
SALIDA="$EVID/smoke-api-$(date +%Y%m%d-%H%M%S).txt"

WEB_URL="${WEB_URL:-http://localhost:8080}"
API_URL="${API_URL:-http://localhost:8000}"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_PASS="${GRAFANA_ADMIN_PASSWORD:-gs08_grafana}"
USUARIO="${SMOKE_USUARIO:-admin}"
CLAVE="${SMOKE_CLAVE:-Admin123!}"
EMAIL_SEED="admin@horizonte.edu.pe"     # dato real del seed (db/init/03-seed.sql)
TIMEOUT=10
BASE="$WEB_URL"
MODO="completo"
ESCRITURA=1
E2E=0

while [ $# -gt 0 ]; do
  case "$1" in
    --infra)         MODO="infra" ;;
    --solo-contrato) MODO="contrato" ;;
    --e2e)           E2E=1 ;;
    --sin-escritura) ESCRITURA=0 ;;
    --url)           BASE="$2"; shift ;;
    --directa)       BASE="$API_URL" ;;
    --usuario)       USUARIO="$2"; shift ;;
    --clave)         CLAVE="$2"; shift ;;
    --timeout)       TIMEOUT="$2"; shift ;;
    -h|--ayuda)      sed -n '2,30p' "$0"; exit 0 ;;
    *) echo "opcion desconocida: $1 (usa --ayuda)"; exit 2 ;;
  esac
  shift
done

N_OK=0
N_FALLA=0
N_BLOQ=0
DETALLE_OK=()
DETALLE_FALLA=()
DETALLE_BLOQ=()

registrar() { # OK|FALLA|BLOQ  "<id y criterio>" "<detalle>"
  case "$1" in
    OK)    N_OK=$((N_OK+1));     DETALLE_OK+=("$2 -> $3") ;;
    FALLA) N_FALLA=$((N_FALLA+1)); DETALLE_FALLA+=("$2 -> $3") ;;
    BLOQ)  N_BLOQ=$((N_BLOQ+1));  DETALLE_BLOQ+=("$2 -> $3") ;;
  esac
}

comprobar() { # "<id y criterio>" "<esperado>" "<obtenido>" "<condicion: ok|falla>"
  if [ "$4" = "ok" ]; then
    registrar OK "$1" "esperado $2, obtenido $3"
  else
    registrar FALLA "$1" "esperado $2, obtenido $3"
  fi
}

peticion() { # METODO RUTA [CUERPO] [TOKEN]
  local metodo="$1" ruta="$2" cuerpo="${3:-}" token="${4:-}"
  local args=(-s -m "$TIMEOUT" -o "$TMP_NAT/cuerpo" -D "$TMP_NAT/cabeceras" -w '%{http_code}' -X "$metodo")
  [ -n "$cuerpo" ] && args+=(-H 'Content-Type: application/json' --data "$cuerpo")
  [ -n "$token" ]  && args+=(-H "Authorization: Bearer $token")
  CODIGO="$(curl "${args[@]}" "${BASE}${ruta}" 2>/dev/null)" || CODIGO="000"
  [ -z "$CODIGO" ] && CODIGO="000"
  if [ "$CODIGO" = "000" ]; then
    # Sin respuesta hay que BORRAR lo anterior: los archivos temporales siguen teniendo
    # el cuerpo de la peticion anterior y en la evidencia pareceria que la API contesto.
    CRUDO=""; CUERPO=""; : > "$TMP/compacto"; CABECERAS=""
    return
  fi
  CRUDO="$(head -c 500 "$TMP/cuerpo" 2>/dev/null | tr -d '\r\n')"
  # El cuerpo completo (sin recortar) se guarda aparte: las aserciones de conteo
  # no pueden depender de los 500 caracteres que se muestran como evidencia.
  tr -d ' \t\r\n' < "$TMP/cuerpo" 2>/dev/null > "$TMP/compacto"
  CUERPO="$(head -c 500 "$TMP/compacto")"
  CABECERAS="$(cat "$TMP/cabeceras" 2>/dev/null)"
}

json_campo() { # nombre  -> valor (string) desde el cuerpo completo compacto
  sed -n "s/.*\"$1\":\"\([^\"]*\)\".*/\1/p" "$TMP/compacto" 2>/dev/null | head -1
}
json_numero() { # nombre -> valor numerico
  sed -n "s/.*\"$1\":\([0-9][0-9]*\).*/\1/p" "$TMP/compacto" 2>/dev/null | head -1
}
contar() { # subcadena, sobre el cuerpo completo (no el recorte de evidencia)
  grep -o "$1" "$TMP/compacto" 2>/dev/null | wc -l | tr -d ' '
}

echo "===== GS08 smoke_api.sh  $(date '+%Y-%m-%d %H:%M:%S') ====="
echo "base=$BASE  api_directa=$API_URL  modo=$MODO  escritura=$ESCRITURA  e2e=$E2E"
echo

# ------------------------------------------------------------
# Puerta de conexion: si no responde ni el proxy ni la API, se corta con exit 2
# (distinto de FALLA: aqui no hay nada que probar, no un criterio incumplido)
# ------------------------------------------------------------
CONEX_PROXY="$(curl -s -m 5 -o /dev/null -w '%{http_code}' "${BASE}/api/v1/health" 2>/dev/null)"
CONEX_API="$(curl -s -m 5 -o /dev/null -w '%{http_code}' "${API_URL}/api/v1/health" 2>/dev/null)"
if [ "$CONEX_PROXY" = "000" ] && [ "$CONEX_API" = "000" ]; then
  echo "SIN CONEXION: no responden ni $BASE/api/v1/health ni $API_URL/api/v1/health."
  echo "Levanta el stack:  docker compose --profile obs up -d   (o revisa --url / API_URL)"
  exit 2
fi

if [ "$MODO" = "contrato" ]; then
  echo "(modo --solo-contrato: se salta el grupo A de infraestructura)"
else
# ------------------------------------------------------------
# Grupo A - infraestructura (AP-09). Corre incluso con el stub.
# ------------------------------------------------------------
peticion GET /healthz
comprobar "SM-01 [C-34] nginx responde /healthz" "HTTP 200 + 'ok'" "HTTP $CODIGO, cuerpo='${CRUDO:0:40}'" \
  "$([ "$CODIGO" = 200 ] && [ "${CUERPO}" = "ok" ] && echo ok || echo falla)"

peticion GET /api/v1/health
comprobar "SM-02 [C-34] /api/v1/health por el proxy" "HTTP 200 status=ok" "HTTP $CODIGO, $CUERPO" \
  "$([ "$CODIGO" = 200 ] && printf '%s' "$CUERPO" | grep -q '"status":"ok"' && echo ok || echo falla)"

peticion GET /api/v1/health  # misma ruta contra la API directa
CODIGO_API="$CODIGO"; CUERPO_API="$CUERPO"
BASE_TMP="$BASE"; BASE="$API_URL"
peticion GET /api/v1/health
comprobar "SM-03 [C-34] /api/v1/health directo al API" "HTTP 200" "HTTP $CODIGO" \
  "$([ "$CODIGO" = 200 ] && echo ok || echo falla)"
# /metrics es texto Prometheus largo: se pide completo (no cabe en el recorte de $CRUDO)
COD_MET="$(curl -s -m "$TIMEOUT" -o "$TMP_NAT/metricas" -w '%{http_code}' "${API_URL}/metrics" 2>/dev/null)"
METRICAS="$(cat "$TMP/metricas" 2>/dev/null)"
comprobar "SM-04 [C-34] /metrics expone Prometheus" "HTTP 200 + http_requests_total + histograma de latencia" \
  "HTTP $COD_MET, $(printf '%s' "$METRICAS" | grep -c '^http_requests_total' ) lineas http_requests_total, $(printf '%s' "$METRICAS" | grep -c 'http_request_duration_seconds_bucket') series de histograma" \
  "$([ "$COD_MET" = 200 ] && printf '%s' "$METRICAS" | grep -q 'http_requests_total' && printf '%s' "$METRICAS" | grep -q 'http_request_duration_seconds_bucket' && echo ok || echo falla)"
BASE="$BASE_TMP"

# SM-05 balanceo: 6 peticiones, deben caer en 2 instancias distintas
UPSTREAMS="$(for _ in 1 2 3 4 5 6; do
  curl -s -m "$TIMEOUT" -o /dev/null -D - "${BASE}/api/v1/health" 2>/dev/null | sed -n 's/^[Xx]-Upstream-Addr: *//p' | tr -d '\r'
done | sort | uniq -c | tr '\n' ' ')"
comprobar "SM-05 [C-35] balanceo nginx entre 2 instancias" "2 direcciones distintas" "reparto: $UPSTREAMS" \
  "$([ "$(printf '%s' "$UPSTREAMS" | grep -o ':8000' | wc -l | tr -d ' ')" -ge 2 ] && echo ok || echo falla)"

# SM-06 SPA y rutas profundas (try_files -> index.html)
peticion GET /
ES_SPA=$([ "$CODIGO" = 200 ] && printf '%s' "$CUERPO" | grep -qi '<html\|<div id="app"' && echo ok || echo falla)
peticion GET /estudiantes
comprobar "SM-06 [C-33] SPA servida y ruta profunda" "HTTP 200 en / y en /estudiantes" "/ -> $ES_SPA, /estudiantes -> HTTP $CODIGO" \
  "$([ "$ES_SPA" = ok ] && [ "$CODIGO" = 200 ] && echo ok || echo falla)"

# SM-07 no se filtra la version del servidor web
peticion GET /healthz
VERSION_NGINX="$(printf '%s' "$CABECERAS" | sed -n 's/^[Ss]erver: *//p' | tr -d '\r')"
comprobar "SM-07 [C-33] server_tokens off" "cabecera Server sin version" "Server: $VERSION_NGINX" \
  "$(printf '%s' "$VERSION_NGINX" | grep -qE 'nginx/[0-9]' && echo falla || echo ok)"

# SM-08 dashboard de Grafana provisionado desde archivo
CODIGO_GRAF="$(curl -s -m "$TIMEOUT" -o /dev/null -w '%{http_code}' -u "admin:${GRAFANA_PASS}" \
  "${GRAFANA_URL}/api/dashboards/uid/gs08-matriculas" 2>/dev/null)"
comprobar "SM-08 [C-36] Grafana con el dashboard provisionado" "HTTP 200" "HTTP $CODIGO_GRAF" \
  "$([ "$CODIGO_GRAF" = 200 ] && echo ok || echo falla)"

fi   # fin del grupo A (se salta con --solo-contrato)

if [ "$MODO" = "infra" ]; then
  echo "(modo --infra: no se prueban los grupos B y C)"
else
  # ----------------------------------------------------------
  # Grupo B - contrato de la API (AP-01 .. AP-08)
  # ----------------------------------------------------------
  peticion POST /api/v1/auth/login "{\"usuario\":\"$USUARIO\",\"password\":\"$CLAVE\"}"
  if [ "$CODIGO" = "404" ]; then
    registrar BLOQ "SM-09..SM-27 [C-01..C-32] contrato de la API" \
      "HTTP 404 en /api/v1/auth/login: la API real todavia no esta implementada (stub). Todo el grupo B queda BLOQUEADO por T1.1"
    CODIGO=""; CUERPO=""
  else
    TOKEN="$(json_campo access_token)"; [ -z "$TOKEN" ] && TOKEN="$(json_campo token)"
    comprobar "SM-09 [C-01] login con usuario" "HTTP 200 + token" "HTTP $CODIGO, token=${TOKEN:0:12}..." \
      "$([ "$CODIGO" = 200 ] && [ -n "$TOKEN" ] && echo ok || echo falla)"

    peticion POST /api/v1/auth/login "{\"usuario\":\"$EMAIL_SEED\",\"password\":\"$CLAVE\"}"
    comprobar "SM-10 [C-01] login por email del seed ($EMAIL_SEED)" "HTTP 200" "HTTP $CODIGO, $CUERPO" \
      "$([ "$CODIGO" = 200 ] && echo ok || echo falla)"

    peticion POST /api/v1/auth/login "{\"usuario\":\"$USUARIO\",\"password\":\"clave-equivocada\"}"
    comprobar "SM-11 [C-01] clave equivocada no emite token" "HTTP 401" "HTTP $CODIGO, $CUERPO" \
      "$([ "$CODIGO" = 401 ] && echo ok || echo falla)"

    peticion GET /api/v1/estudiantes
    comprobar "SM-12 [C-01] sin token no se lee el listado" "HTTP 401" "HTTP $CODIGO" \
      "$([ "$CODIGO" = 401 ] && echo ok || echo falla)"

    peticion GET /api/v1/estudiantes "" "token.invalido.falsificado"
    comprobar "SM-13 [C-01] token falsificado no sirve" "HTTP 401" "HTTP $CODIGO" \
      "$([ "$CODIGO" = 401 ] && echo ok || echo falla)"

    peticion GET /api/v1/dashboard "" "$TOKEN"
    E12="$(json_numero estudiantes_activos)"; E7="$(json_numero cursos_activos)"
    M23="$(json_numero matriculas_activas)"; U1="$(json_numero usuarios_activos)"
    comprobar "SM-14 [C-05] KPIs del seed 12/7/23/1" "12 | 7 | 23 | 1" "$E12 | $E7 | $M23 | $U1" \
      "$([ "$E12" = 12 ] && [ "$E7" = 7 ] && [ "$M23" = 23 ] && [ "$U1" = 1 ] && echo ok || echo falla)"

    CUENTAS=""
    # OJO: los bytes UTF-8 crudos en la URL hacen que uvicorn responda 400
    # ("Invalid HTTP request received"), asi que la tilde va percent-encoded (%C3%A1 = á).
    for q in huaman Huam%C3%A1n HUAMAN; do
      peticion GET "/api/v1/estudiantes?q=$q" "" "$TOKEN"
      CUENTAS="$CUENTAS$q=$(json_numero total) "
    done
    N1="$(printf '%s' "$CUENTAS" | sed -n 's/.*huaman=\([0-9]*\).*/\1/p')"
    N2="$(printf '%s' "$CUENTAS" | sed -n 's/.*Huam%C3%A1n=\([0-9]*\).*/\1/p')"
    N3="$(printf '%s' "$CUENTAS" | sed -n 's/.*HUAMAN=\([0-9]*\).*/\1/p')"
    # Nota para @dev (BUG-07): ILIKE ignora mayusculas pero NO tildes; hace falta
    # unaccent(...) ILIKE unaccent(...) y la extension CREATE EXTENSION unaccent en db/init.
    comprobar "SM-15 [C-08] buscador ILIKE + unaccent (mayusculas y tildes)" "misma cantidad >=1 en los 3" "$CUENTAS" \
      "$([ "$N1" = "$N2" ] && [ "$N2" = "$N3" ] && [ "${N1:-0}" -ge 1 ] 2>/dev/null && echo ok || echo falla)"

    peticion GET "/api/v1/estudiantes?q=E20260001" "" "$TOKEN"; POR_CODIGO="$(json_numero total)"
    peticion GET "/api/v1/estudiantes?q=45123456" "" "$TOKEN";  POR_DNI="$(json_numero total)"
    comprobar "SM-16 [C-09] busqueda por codigo y por DNI" "1 y 1" "codigo=$POR_CODIGO dni=$POR_DNI" \
      "$([ "$POR_CODIGO" = 1 ] && [ "$POR_DNI" = 1 ] && echo ok || echo falla)"

    peticion GET "/api/v1/estudiantes?page=1&page_size=200" "" "$TOKEN"; P200="$CODIGO"
    peticion GET "/api/v1/estudiantes?page=1&page_size=0" "" "$TOKEN";   P0="$CODIGO"
    comprobar "SM-17 [C-10] page_size fuera de rango" "422 y 422" "200 -> $P200, 0 -> $P0" \
      "$([ "$P200" = 422 ] && [ "$P0" = 422 ] && echo ok || echo falla)"

    peticion GET "/api/v1/estudiantes?page=1&page_size=25" "" "$TOKEN"
    FILAS="$(contar '"codigo"')"; TOTAL="$(json_numero total)"
    # Con 12 estudiantes en el seed, page_size=25 trae 12 (no 25): la pagina trae
    # min(page_size, total). El criterio C-10 pide "25 filas + total" porque asume
    # un volumen mayor; con el seed lo correcto es total=12 y la pagina completa.
    ESPERADAS="$TOTAL"; [ "$ESPERADAS" -gt 25 ] 2>/dev/null && ESPERADAS=25
    comprobar "SM-18 [C-10] listado paginado: 1 pagina completa + total" "min(page_size,total) filas y total=12" \
      "filas=$FILAS total=$TOTAL (esperadas $ESPERADAS)" \
      "$([ "$FILAS" = "$ESPERADAS" ] && [ "$TOTAL" = 12 ] && echo ok || echo falla)"

    # segunda pagina con page_size=5: 12 estudiantes -> 5 + 5 + 2
    peticion GET "/api/v1/estudiantes?page=3&page_size=5" "" "$TOKEN"
    FILAS_P3="$(contar '"codigo"')"
    comprobar "SM-18b [C-10] ultima pagina parcial (page=3, page_size=5)" "2 filas y total=12" \
      "filas=$FILAS_P3 total=$(json_numero total)" \
      "$([ "$FILAS_P3" = 2 ] && [ "$(json_numero total)" = 12 ] && echo ok || echo falla)"

    if [ "$ESCRITURA" = 1 ]; then
      peticion POST /api/v1/estudiantes \
        '{"codigo":"QA-X1","dni":"1234567","nombres":"Prueba","apellidos":"Dni Corto"}' "$TOKEN"
      comprobar "SM-19 [C-11] DNI de 7 digitos" "HTTP 422 (nunca 500)" "HTTP $CODIGO, $CUERPO" \
        "$([ "$CODIGO" = 422 ] && echo ok || echo falla)"

      peticion POST /api/v1/cursos \
        '{"codigo":"QA-C11","nombre":"Curso QA","creditos":11,"horas":10}' "$TOKEN"
      comprobar "SM-20 [C-13] curso con creditos=11" "HTTP 422" "HTTP $CODIGO, $CUERPO" \
        "$([ "$CODIGO" = 422 ] && echo ok || echo falla)"

      peticion POST /api/v1/matriculas \
        '{"estudiante_id":1,"curso_id":6,"periodo":"2026-13","fecha_matricula":"2026-08-01"}' "$TOKEN"
      comprobar "SM-21 [C-18] periodo 2026-13" "HTTP 422" "HTTP $CODIGO, $CUERPO" \
        "$([ "$CODIGO" = 422 ] && echo ok || echo falla)"
    else
      registrar BLOQ "SM-19..SM-21 [C-11/C-13/C-18] altas invalidas" "--sin-escritura: no se probaron"
    fi

    peticion POST /api/v1/matriculas \
      '{"estudiante_id":1,"curso_id":1,"periodo":"2026-02","fecha_matricula":"2026-08-01"}' "$TOKEN"
    comprobar "SM-22 [C-17] matricula duplicada (est 1 + curso 1 + 2026-02)" \
      "HTTP 409 con el mensaje del legacy" "HTTP $CODIGO, $CUERPO" \
      "$([ "$CODIGO" = 409 ] && echo ok || echo falla)"

    if [ "$ESCRITURA" = 1 ]; then
      peticion POST /api/v1/matriculas \
        '{"estudiante_id":99999,"curso_id":1,"periodo":"2026-02","fecha_matricula":"2026-08-01"}' "$TOKEN"
      comprobar "SM-23 [C-19] matricula de estudiante inexistente" "HTTP 404" "HTTP $CODIGO, $CUERPO" \
        "$([ "$CODIGO" = 404 ] && echo ok || echo falla)"
    else
      registrar BLOQ "SM-23 [C-19] FK inexistente" "--sin-escritura: no se probo"
    fi

    peticion GET "/api/v1/matriculas?periodo=2026-02" "" "$TOKEN"
    TOTAL_MAT="$(json_numero total)"
    comprobar "SM-24 [C-16] listado de matriculas del periodo" "HTTP 200 y total=24" "HTTP $CODIGO, total=$TOTAL_MAT" \
      "$([ "$CODIGO" = 200 ] && [ "$TOTAL_MAT" = 24 ] && echo ok || echo falla)"

    if [ "$ESCRITURA" = 1 ]; then
      peticion DELETE "/api/v1/estudiantes/2" "" "$TOKEN"
      COD_DEL="$CODIGO"; BORRADAS="$(json_numero matriculas)"
      peticion GET "/api/v1/estudiantes/2" "" "$TOKEN"
      SIGUE="$CODIGO"
      comprobar "SM-25 [C-30] DELETE con matriculas no borra nada" "409 con matriculas=2 y el estudiante sigue (200)" \
        "DELETE -> HTTP $COD_DEL {'matriculas':$BORRADAS}, GET -> HTTP $SIGUE" \
        "$([ "$COD_DEL" = 409 ] && [ "$BORRADAS" = 2 ] && [ "$SIGUE" = 200 ] && echo ok || echo falla)"
    else
      registrar BLOQ "SM-25 [C-30] borrado con confirmacion" "--sin-escritura: no se probo"
    fi

    if [ "$ESCRITURA" = 1 ]; then
      # SM-26: rol asistente -> 403 en /api/v1/usuarios  (necesita un usuario asistente)
      # IDEMPOTENCIA: si el usuario de prueba ya existe (409) se reusa y NO se borra; si lo
      # creamos nosotros, se borra al final. Sin esto, la segunda corrida ve 2 usuarios
      # activos y tumba SM-14 (C-05) por culpa del propio arnes, no de la API.
      peticion POST /api/v1/usuarios \
        '{"nombre_usuario":"qa_asistente","email":"qa_asistente@horizonte.edu.pe","password":"QaPrueba123!","nombre_completo":"QA Asistente","rol":"asistente"}' "$TOKEN"
      ID_ASIS=""; CREADO_POR_NOSOTROS=0
      if [ "$CODIGO" = 201 ]; then
        ID_ASIS="$(json_numero id)"; CREADO_POR_NOSOTROS=1
      elif [ "$CODIGO" = 409 ]; then
        peticion GET /api/v1/usuarios "" "$TOKEN"
        ID_ASIS="$(json_numero id)"   # el listado no trae ids sueltos: se resuelve abajo
      fi
      if [ "$CODIGO" != "" ]; then
        peticion POST /api/v1/auth/login '{"usuario":"qa_asistente","password":"QaPrueba123!"}'
        TOKEN_ASIS="$(json_campo access_token)"
        peticion GET /api/v1/usuarios "" "$TOKEN_ASIS"
        comprobar "SM-26 [C-23] rol asistente no entra a /usuarios" "HTTP 403" "HTTP $CODIGO, $CUERPO" \
          "$([ "$CODIGO" = 403 ] && echo ok || echo falla)"
        # limpieza: solo si lo creamos nosotros
        if [ "$CREADO_POR_NOSOTROS" = 1 ] && [ -n "$ID_ASIS" ]; then
          peticion DELETE "/api/v1/usuarios/$ID_ASIS?confirmar=true" "" "$TOKEN"
          registrar "$([ "$CODIGO" = 204 ] && echo OK || echo FALLA)" \
            "SM-26b limpieza del usuario de prueba" "DELETE /api/v1/usuarios/$ID_ASIS?confirmar=true -> HTTP $CODIGO"
        fi
      else
        registrar FALLA "SM-26 [C-23] rol asistente no entra a /usuarios" \
          "no se pudo crear el asistente: HTTP $CODIGO $CUERPO"
      fi
    else
      registrar BLOQ "SM-26 [C-23] permisos por rol" "--sin-escritura: no se probo"
    fi

    peticion GET /api/v1/estudiantes/99999 "" "$TOKEN"
    comprobar "SM-27 [C-19] estudiante inexistente" "HTTP 404" "HTTP $CODIGO" \
      "$([ "$CODIGO" = 404 ] && echo ok || echo falla)"
  fi

  # ----------------------------------------------------------
  # Grupo C - recorrido completo §3 (de la matricula a la nota)
  # ----------------------------------------------------------
  if [ "$E2E" = 1 ]; then
    if [ -z "${TOKEN:-}" ]; then
      registrar BLOQ "E2E-01 [§3 pasos 1-10] recorrido completo" "sin API real (grupo B bloqueado)"
    else
      SELLO="$(date +%H%M%S)"
      COD="E2E$SELLO"; DNI="9${SELLO}1"; DNI="${DNI:0:8}"
      peticion POST /api/v1/estudiantes \
        "{\"codigo\":\"$COD\",\"dni\":\"$DNI\",\"nombres\":\"Estudiante\",\"apellidos\":\"De Prueba SMP\",\"email\":\"$COD@correo.pe\"}" "$TOKEN"
      ID_EST="$(json_numero id)"
      comprobar "E2E-01 [paso 4 - C-11] alta de estudiante" "HTTP 201 + id" "HTTP $CODIGO, id=$ID_EST" \
        "$([ "$CODIGO" = 201 ] && [ -n "$ID_EST" ] && echo ok || echo falla)"

      peticion POST /api/v1/matriculas \
        "{\"estudiante_id\":$ID_EST,\"curso_id\":6,\"periodo\":\"2026-02\",\"fecha_matricula\":\"2026-08-01\"}" "$TOKEN"
      ID_MAT="$(json_numero id)"
      comprobar "E2E-01 [paso 6 - C-16] matricula del estudiante nuevo" "HTTP 201 + id" "HTTP $CODIGO, id=$ID_MAT" \
        "$([ "$CODIGO" = 201 ] && [ -n "$ID_MAT" ] && echo ok || echo falla)"

      peticion POST /api/v1/matriculas \
        "{\"estudiante_id\":$ID_EST,\"curso_id\":6,\"periodo\":\"2026-02\",\"fecha_matricula\":\"2026-08-01\"}" "$TOKEN"
      comprobar "E2E-01 [paso 6 - C-17] la segunda matricula igual da 409" "HTTP 409" "HTTP $CODIGO, $CUERPO" \
        "$([ "$CODIGO" = 409 ] && echo ok || echo falla)"

      for par in practica:14 parcial:16 final:18; do
        TIPO="${par%%:*}"; NOTA="${par##*:}"
        peticion POST "/api/v1/matriculas/$ID_MAT/notas" \
          "{\"tipo\":\"$TIPO\",\"numero\":1,\"nota\":$NOTA}" "$TOKEN"
        registrar "$([ "$CODIGO" = 201 ] && echo OK || echo FALLA)" \
          "E2E-01 [paso 8 - C-24] nota $TIPO=$NOTA" "HTTP $CODIGO, $CUERPO"
      done

      peticion POST "/api/v1/matriculas/$ID_MAT/notas" '{"tipo":"practica","numero":1,"nota":20}' "$TOKEN"
      comprobar "E2E-01 [paso 8 - C-25] nota duplicada" "HTTP 409" "HTTP $CODIGO" \
        "$([ "$CODIGO" = 409 ] && echo ok || echo falla)"

      peticion POST "/api/v1/matriculas/$ID_MAT/notas" '{"tipo":"final","numero":2,"nota":21}' "$TOKEN"
      comprobar "E2E-01 [paso 8 - C-25] nota 21 fuera de rango" "HTTP 422" "HTTP $CODIGO" \
        "$([ "$CODIGO" = 422 ] && echo ok || echo falla)"

      peticion GET "/api/v1/estudiantes/$ID_EST/boleta?periodo=2026-02" "" "$TOKEN"
      # Se lee del cuerpo COMPLETO ($TMP/compacto), no del recorte de 500 caracteres de $CUERPO.
      # La API devuelve por curso `nota` + `nota_texto` y el promedio del periodo en `promedio`.
      # No se puede buscar "nota" a ciegas: cada nota suelta tambien trae ese campo, por eso
      # se comprueba `nota_texto` (que solo existe en la nota del curso) y `promedio`.
      PROMEDIO="$(grep -o '"promedio":[0-9.]*' "$TMP/compacto" 2>/dev/null | head -1 | cut -d: -f2)"
      NOTA_TXT="$(grep -o '"nota_texto":"[0-9.]*"' "$TMP/compacto" 2>/dev/null | head -1 | cut -d'"' -f4)"
      NOTA_OK="$(awk -v a="$NOTA_TXT" 'BEGIN{exit !(a+0 == 16)}' && echo ok || echo falla)"
      PROM_OK="$(awk -v a="$PROMEDIO" 'BEGIN{exit !(a+0 == 16)}' && echo ok || echo falla)"
      comprobar "E2E-01 [paso 9 - C-27] boleta: 14/16/18 -> 16 (media aritmetica)" "nota del curso y promedio = 16" \
        "nota_texto=$NOTA_TXT promedio=$PROMEDIO" \
        "$([ "$NOTA_OK" = ok ] && [ "$PROM_OK" = ok ] && echo ok || echo falla)"

      # limpieza: el borrado definitivo es la segunda llamada explicita (AP-08)
      if [ "$ESCRITURA" = 1 ]; then
        peticion DELETE "/api/v1/estudiantes/$ID_EST?confirmar=true" "" "$TOKEN"
        comprobar "E2E-01 [C-31] limpieza con ?confirmar=true" "HTTP 204" "HTTP $CODIGO" \
          "$([ "$CODIGO" = 204 ] && echo ok || echo falla)"
      fi
    fi
  fi
fi

# ------------------------------------------------------------
# Reporte
# ------------------------------------------------------------
{
  echo "===== GS08 smoke_api.sh  $(date '+%Y-%m-%d %H:%M:%S') ====="
  echo "base=$BASE api_directa=$API_URL modo=$MODO escritura=$ESCRITURA e2e=$E2E"
  echo
  for l in "${DETALLE_OK[@]:-}";    do [ -n "$l" ] && echo "OK    $l"; done
  for l in "${DETALLE_BLOQ[@]:-}";  do [ -n "$l" ] && echo "BLOQ  $l"; done
  for l in "${DETALLE_FALLA[@]:-}"; do [ -n "$l" ] && echo "FALLA $l"; done
  echo
  echo "$N_OK comprobaciones OK, $N_FALLA fallas, $N_BLOQ bloqueadas"
} | tee "$SALIDA"

rm -rf "$TMP"
echo
echo "evidencia: $SALIDA"

if [ "$N_FALLA" -gt 0 ]; then exit 1; fi
if [ "$N_BLOQ" -gt 0 ]; then exit 3; fi
exit 0
