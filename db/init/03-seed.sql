-- ============================================================
-- GS08 - Matriculas y Notas | 03-seed.sql
-- Datos iniciales (mismos registros que el seed del legacy)
-- Autor: @analista | Sprint 0
--
-- Contenido: 1 usuario admin, 12 estudiantes, 7 cursos, 24 matriculas (23 activas + 1 retirada).
-- Se cargan con id explicito para que el numero de matricula del estudiante 1 sea
-- siempre 1 en todas las maquinas (comodidad para @qa y para los ejemplos del informe).
-- Al final se sincronizan las secuencias IDENTITY: sin ese setval, el primer INSERT
-- del API intentaria reusar id=1 y chocaria con la clave primaria.
--
-- Usuario de demo: admin / Admin123!   (hash bcrypt del legacy, verificado con pgcrypto)
-- Se puede re-ejecutar sin duplicar: ON CONFLICT DO NOTHING.
-- ============================================================

-- ------------------------------------------------------------
-- Usuario administrador
-- ------------------------------------------------------------
INSERT INTO usuarios (id, nombre_usuario, email, password_hash, nombre_completo, rol, estado) VALUES
(1, 'admin', 'admin@horizonte.edu.pe',
 '$2y$10$Tzgm/meEuR9o/nxq1ocKBu01ncP.pbnMay7a1aqWsuwXA4Q9Y9nzu',
 'Administrador del Sistema', 'admin', true)
ON CONFLICT DO NOTHING;

-- ------------------------------------------------------------
-- Estudiantes (12)
-- ------------------------------------------------------------
INSERT INTO estudiantes (id, codigo, dni, nombres, apellidos, email, telefono, fecha_nacimiento, direccion) VALUES
( 1, 'E20260001', '45123456', 'Carlos Alberto',    'Ramírez Torres',     'cramirez@correo.pe',   '987654321', '2005-03-14', 'Av. Los Laureles 245, Lima'),
( 2, 'E20260002', '46234567', 'María Fernanda',    'Quispe Huamán',      'mquispe@correo.pe',    '986543210', '2006-07-22', 'Jr. Puno 118, Lima'),
( 3, 'E20260003', '47345678', 'Luis Enrique',      'Gutiérrez Salas',    'lgutierrez@correo.pe', '985432109', '2004-11-30', 'Calle Los Olivos 87, Callao'),
( 4, 'E20260004', '48456789', 'Ana Lucía',         'Vargas Mendoza',     'avargas@correo.pe',    '984321098', '2005-01-09', 'Av. Grau 456, Lima'),
( 5, 'E20260005', '49567890', 'Diego Antonio',     'Flores Chávez',      'dflores@correo.pe',    '983210987', '2006-05-18', 'Jr. Amazonas 332, Lima'),
( 6, 'E20260006', '50678901', 'Valeria Sofía',     'Paredes Rojas',      'vparedes@correo.pe',   '982109876', '2004-09-25', 'Av. Arequipa 1780, Lima'),
( 7, 'E20260007', '51789012', 'Jorge Luis',        'Castillo Neyra',     'jcastillo@correo.pe',  '981098765', '2005-12-03', 'Calle Los Pinos 51, Miraflores'),
( 8, 'E20260008', '52890123', 'Camila Andrea',     'Ríos Delgado',       'crios@correo.pe',      '980987654', '2006-02-27', 'Jr. Chiclayo 220, Lima'),
( 9, 'E20260009', '53901234', 'Miguel Ángel',      'Herrera Palacios',   'mherrera@correo.pe',   '979876543', '2004-06-11', 'Av. Universitaria 3120, Lima'),
(10, 'E20260010', '54012345', 'Nicole Alessandra', 'Torres Vega',        'ntorres@correo.pe',    '978765432', '2005-08-19', 'Calle El Sol 96, San Miguel'),
(11, 'E20260011', '55123456', 'Renato Gabriel',    'Salazar Meza',       'rsalazar@correo.pe',   '977654321', '2006-04-07', 'Jr. Cusco 154, Lima'),
(12, 'E20260012', '56234567', 'Fiorella Milagros', 'Cárdenas Ruiz',      'fcardenas@correo.pe',  '976543210', '2005-10-15', 'Av. La Marina 2890, Lima')
ON CONFLICT DO NOTHING;

-- ------------------------------------------------------------
-- Cursos (7)
-- ------------------------------------------------------------
INSERT INTO cursos (id, codigo, nombre, descripcion, creditos, horas) VALUES
(1, 'C101', 'Matemática Básica',             'Fundamentos de aritmética, álgebra y geometría aplicada.', 4, 64),
(2, 'C102', 'Comunicación Efectiva',         'Redacción académica, expresión oral y comprensión lectora.', 3, 48),
(3, 'C201', 'Programación Web III',          'Desarrollo de aplicaciones web con PHP, MySQL y Bootstrap.', 4, 64),
(4, 'C202', 'Base de Datos II',              'Diseño y administración de bases de datos relacionales.', 3, 48),
(5, 'C203', 'Inglés Técnico',                'Inglés orientado al ámbito profesional y técnico.', 2, 32),
(6, 'C204', 'Estadística Aplicada',          'Estadística descriptiva e inferencial para la toma de decisiones.', 3, 48),
(7, 'C205', 'Fundamentos de Administración', 'Principios de gestión, organización y liderazgo.', 3, 48)
ON CONFLICT DO NOTHING;

-- ------------------------------------------------------------
-- Matriculas (24, periodo 2026-02) — 1 retirada (estudiante 7 / curso 4)
-- ------------------------------------------------------------
INSERT INTO matriculas (id, estudiante_id, curso_id, periodo, fecha_matricula, estado) VALUES
( 1,  1, 1, '2026-02', '2026-08-03', 'activa'),
( 2,  1, 2, '2026-02', '2026-08-03', 'activa'),
( 3,  2, 1, '2026-02', '2026-08-04', 'activa'),
( 4,  2, 3, '2026-02', '2026-08-04', 'activa'),
( 5,  3, 3, '2026-02', '2026-08-05', 'activa'),
( 6,  3, 4, '2026-02', '2026-08-05', 'activa'),
( 7,  4, 2, '2026-02', '2026-08-06', 'activa'),
( 8,  4, 5, '2026-02', '2026-08-06', 'activa'),
( 9,  5, 1, '2026-02', '2026-08-07', 'activa'),
(10,  5, 6, '2026-02', '2026-08-07', 'activa'),
(11,  6, 3, '2026-02', '2026-08-07', 'activa'),
(12,  6, 7, '2026-02', '2026-08-07', 'activa'),
(13,  7, 4, '2026-02', '2026-08-10', 'retirado'),
(14,  7, 5, '2026-02', '2026-08-10', 'activa'),
(15,  8, 2, '2026-02', '2026-08-11', 'activa'),
(16,  8, 6, '2026-02', '2026-08-11', 'activa'),
(17,  9, 1, '2026-02', '2026-08-12', 'activa'),
(18,  9, 7, '2026-02', '2026-08-12', 'activa'),
(19, 10, 3, '2026-02', '2026-08-13', 'activa'),
(20, 10, 5, '2026-02', '2026-08-13', 'activa'),
(21, 11, 2, '2026-02', '2026-08-14', 'activa'),
(22, 11, 4, '2026-02', '2026-08-14', 'activa'),
(23, 12, 1, '2026-02', '2026-08-17', 'activa'),
(24, 12, 6, '2026-02', '2026-08-17', 'activa')
ON CONFLICT DO NOTHING;

-- ------------------------------------------------------------
-- Sincronizar secuencias IDENTITY con los ids cargados
-- ------------------------------------------------------------
SELECT setval(pg_get_serial_sequence('usuarios',   'id'), (SELECT max(id) FROM usuarios));
SELECT setval(pg_get_serial_sequence('estudiantes','id'), (SELECT max(id) FROM estudiantes));
SELECT setval(pg_get_serial_sequence('cursos',     'id'), (SELECT max(id) FROM cursos));
SELECT setval(pg_get_serial_sequence('matriculas', 'id'), (SELECT max(id) FROM matriculas));

-- Reiniciar la estadistica del planificador (los INSERT masivos la dejan desfasada)
ANALYZE usuarios;
ANALYZE estudiantes;
ANALYZE cursos;
ANALYZE matriculas;
