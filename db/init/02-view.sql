-- ============================================================
-- GS08 - Matriculas y Notas | 02-view.sql
-- Vista de matriculas con estudiante y curso (JOIN)
-- Autor: @analista | Sprint 0
--
-- Equivale a la vista v_matriculas_detalle del legacy (MySQL), que ya usaban
-- dashboard.php, matriculas/index.php y el filtro de busqueda del listado.
-- CREATE OR REPLACE: se puede re-ejecutar sin borrar la vista.
-- ============================================================

CREATE OR REPLACE VIEW v_matriculas_detalle AS
SELECT
    m.id                      AS matricula_id,
    m.periodo                 AS periodo,
    m.fecha_matricula         AS fecha_matricula,
    m.estado                  AS estado_matricula,
    e.id                      AS estudiante_id,
    e.codigo                  AS codigo_estudiante,
    e.dni                     AS dni,
    e.apellidos               AS apellidos_estudiante,
    e.nombres                 AS nombres_estudiante,
    (e.apellidos || ', ' || e.nombres) AS estudiante,
    e.email                   AS email_estudiante,
    c.id                      AS curso_id,
    c.codigo                  AS codigo_curso,
    c.nombre                  AS curso,
    c.creditos                AS creditos,
    c.horas                   AS horas
FROM matriculas m
INNER JOIN estudiantes e ON e.id = m.estudiante_id
INNER JOIN cursos c      ON c.id = m.curso_id;

COMMENT ON VIEW v_matriculas_detalle IS
    'Matriculas con datos del estudiante y del curso. Origen: legacy v_matriculas_detalle + columnas apellidos/nombres/email/horas para que el SPA ordene sin volver a consultar.';
