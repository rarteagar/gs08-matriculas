<?php
/**
 * Dashboard: resumen del sistema con funciones agregadas COUNT()
 * y consultas con JOIN a través de la vista v_matriculas_detalle.
 */
declare(strict_types=1);

require_once __DIR__ . '/includes/auth.php';
login_required('login.php');
require_once __DIR__ . '/config/database.php';
require_once __DIR__ . '/includes/functions.php';

$BASE        = '';
$active_menu = 'dashboard';
$page_title  = 'Dashboard';
require_once __DIR__ . '/includes/header.php';

$pdo = db();

// Totales (funciones agregadas COUNT)
$totalEstudiantes = (int) $pdo->query('SELECT COUNT(*) FROM estudiantes WHERE estado = 1')->fetchColumn();
$totalCursos      = (int) $pdo->query('SELECT COUNT(*) FROM cursos WHERE estado = 1')->fetchColumn();
$totalMatriculas  = (int) $pdo->query("SELECT COUNT(*) FROM matriculas WHERE estado = 'activa'")->fetchColumn();
$totalUsuarios    = (int) $pdo->query('SELECT COUNT(*) FROM usuarios WHERE estado = 1')->fetchColumn();

// Matrículas activas por curso (JOIN a través de la vista)
$porCurso = $pdo->query(
    "SELECT curso, COUNT(*) AS total
     FROM v_matriculas_detalle
     WHERE estado_matricula = 'activa'
     GROUP BY curso
     ORDER BY total DESC
     LIMIT 5"
)->fetchAll();

$maxCurso = 1;
foreach ($porCurso as $row) {
    $maxCurso = max($maxCurso, (int) $row['total']);
}

// Últimos estudiantes registrados
$ultimos = $pdo->query(
    'SELECT codigo, nombres, apellidos, dni, email
     FROM estudiantes
     ORDER BY id DESC
     LIMIT 6'
)->fetchAll();
?>

<div class="row g-3">
    <div class="col-sm-6 col-xl-3">
        <a href="estudiantes/index.php" class="kpi-card kpi-navy d-flex">
            <div class="kpi-icon"><i class="bi bi-person-video3"></i></div>
            <div>
                <div class="kpi-value"><?= $totalEstudiantes ?></div>
                <div class="kpi-label">Estudiantes activos</div>
            </div>
        </a>
    </div>
    <div class="col-sm-6 col-xl-3">
        <a href="cursos/index.php" class="kpi-card kpi-gold d-flex">
            <div class="kpi-icon"><i class="bi bi-book"></i></div>
            <div>
                <div class="kpi-value"><?= $totalCursos ?></div>
                <div class="kpi-label">Cursos activos</div>
            </div>
        </a>
    </div>
    <div class="col-sm-6 col-xl-3">
        <a href="matriculas/index.php" class="kpi-card kpi-teal d-flex">
            <div class="kpi-icon"><i class="bi bi-journal-check"></i></div>
            <div>
                <div class="kpi-value"><?= $totalMatriculas ?></div>
                <div class="kpi-label">Matrículas activas</div>
            </div>
        </a>
    </div>
    <div class="col-sm-6 col-xl-3">
        <a href="usuarios/index.php" class="kpi-card kpi-plum d-flex">
            <div class="kpi-icon"><i class="bi bi-people"></i></div>
            <div>
                <div class="kpi-value"><?= $totalUsuarios ?></div>
                <div class="kpi-label">Usuarios del sistema</div>
            </div>
        </a>
    </div>
</div>

<div class="row g-3 mt-1">
    <div class="col-lg-6">
        <div class="card h-100">
            <div class="card-header">
                <h6><i class="bi bi-bar-chart me-2 text-warning"></i>Matrículas activas por curso</h6>
                <span class="text-muted small">Periodo 2026-02</span>
            </div>
            <div class="card-body">
                <?php if ($porCurso): ?>
                    <?php foreach ($porCurso as $row): ?>
                        <div class="mb-3">
                            <div class="d-flex justify-content-between small mb-1">
                                <span class="fw-semibold"><?= e($row['curso']) ?></span>
                                <span class="text-muted"><?= (int) $row['total'] ?> matrícula(s)</span>
                            </div>
                            <div class="bar-track">
                                <div class="bar-fill" style="width: <?= round(((int) $row['total'] / $maxCurso) * 100) ?>%"></div>
                            </div>
                        </div>
                    <?php endforeach; ?>
                <?php else: ?>
                    <p class="text-muted mb-0">Aún no hay matrículas registradas.</p>
                <?php endif; ?>
            </div>
        </div>
    </div>

    <div class="col-lg-6">
        <div class="card h-100">
            <div class="card-header">
                <h6><i class="bi bi-clock-history me-2 text-warning"></i>Últimos estudiantes registrados</h6>
                <a href="estudiantes/index.php" class="btn btn-sm btn-outline-primary">Ver todos</a>
            </div>
            <div class="card-body p-0">
                <table class="table table-hover align-middle mb-0">
                    <thead>
                        <tr>
                            <th>Código</th>
                            <th>Estudiante</th>
                            <th>DNI</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($ultimos as $est): ?>
                            <tr>
                                <td class="fw-semibold"><?= e($est['codigo']) ?></td>
                                <td><?= e($est['apellidos'] . ', ' . $est['nombres']) ?></td>
                                <td class="text-muted"><?= e($est['dni']) ?></td>
                            </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</div>

<?php require_once __DIR__ . '/includes/footer.php'; ?>
