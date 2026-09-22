<?php
/**
 * Matrículas - Listado (Leer)
 * Consulta a través de la vista v_matriculas_detalle (JOIN estudiantes + cursos).
 */
declare(strict_types=1);

require_once __DIR__ . '/../includes/auth.php';
login_required();
require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../includes/functions.php';

$BASE        = '../';
$active_menu = 'matriculas';
$page_title  = 'Gestión de Matrículas';
require_once __DIR__ . '/../includes/header.php';

$q        = trim((string) ($_GET['q'] ?? ''));
$periodo  = trim((string) ($_GET['periodo'] ?? ''));

$sql = 'SELECT matricula_id, periodo, fecha_matricula, estado_matricula,
               codigo_estudiante, estudiante, codigo_curso, curso, creditos
        FROM v_matriculas_detalle WHERE 1 = 1';
$params = [];

if ($q !== '') {
    $sql .= ' AND (estudiante LIKE :q OR curso LIKE :q OR codigo_estudiante LIKE :q OR codigo_curso LIKE :q)';
    $params[':q'] = '%' . $q . '%';
}
if ($periodo !== '') {
    $sql .= ' AND periodo = :periodo';
    $params[':periodo'] = $periodo;
}

$sql .= ' ORDER BY fecha_matricula DESC, estudiante';
$stmt = db()->prepare($sql);
$stmt->execute($params);
$matriculas = $stmt->fetchAll();

// Períodos disponibles para el filtro
$periodos = db()->query('SELECT DISTINCT periodo FROM matriculas ORDER BY periodo DESC')->fetchAll();
?>

<div class="card">
    <div class="card-header">
        <h5><i class="bi bi-journal-check me-2 text-warning"></i>Listado de matrículas</h5>
        <a href="create.php" class="btn btn-gold btn-sm">
            <i class="bi bi-plus-lg"></i> Nueva matrícula
        </a>
    </div>
    <div class="card-body">
        <form method="get" action="index.php" class="row g-2 mb-3">
            <div class="col-md-6 col-lg-5">
                <div class="input-group">
                    <span class="input-group-text"><i class="bi bi-search"></i></span>
                    <input type="text" class="form-control" name="q" value="<?= e($q) ?>"
                           placeholder="Buscar por estudiante, curso o código...">
                </div>
            </div>
            <div class="col-auto">
                <select class="form-select" name="periodo" onchange="this.form.submit()">
                    <option value="">Todos los periodos</option>
                    <?php foreach ($periodos as $p): ?>
                        <option value="<?= e($p['periodo']) ?>" <?= $periodo === $p['periodo'] ? 'selected' : '' ?>>
                            <?= e($p['periodo']) ?>
                        </option>
                    <?php endforeach; ?>
                </select>
            </div>
            <div class="col-auto">
                <button type="submit" class="btn btn-primary">Filtrar</button>
                <?php if ($q !== '' || $periodo !== ''): ?>
                    <a href="index.php" class="btn btn-outline-secondary">Limpiar</a>
                <?php endif; ?>
            </div>
        </form>

        <?php if ($matriculas): ?>
            <div class="table-responsive">
                <table class="table table-hover align-middle">
                    <thead>
                        <tr>
                            <th>Estudiante</th>
                            <th>Curso</th>
                            <th>Créd.</th>
                            <th>Periodo</th>
                            <th>Fecha</th>
                            <th>Estado</th>
                            <th class="text-end">Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($matriculas as $m): ?>
                            <tr>
                                <td>
                                    <span class="fw-semibold"><?= e($m['estudiante']) ?></span><br>
                                    <small class="text-muted"><?= e($m['codigo_estudiante']) ?></small>
                                </td>
                                <td>
                                    <?= e($m['curso']) ?><br>
                                    <small class="text-muted"><?= e($m['codigo_curso']) ?></small>
                                </td>
                                <td><?= (int) $m['creditos'] ?></td>
                                <td><span class="badge text-bg-dark"><?= e($m['periodo']) ?></span></td>
                                <td><?= date('d/m/Y', strtotime($m['fecha_matricula'])) ?></td>
                                <td>
                                    <span class="badge badge-<?= $m['estado_matricula'] === 'activa' ? 'active' : 'retirado' ?>">
                                        <?= e(ucfirst($m['estado_matricula'])) ?>
                                    </span>
                                </td>
                                <td class="text-end text-nowrap">
                                    <a href="edit.php?id=<?= (int) $m['matricula_id'] ?>" class="btn btn-icon btn-outline-primary" title="Editar">
                                        <i class="bi bi-pencil"></i>
                                    </a>
                                    <form method="post" action="delete.php" class="d-inline"
                                          data-confirm="¿Eliminar la matrícula de <?= e($m['estudiante']) ?> en <?= e($m['curso']) ?>?">
                                        <?= csrf_field() ?>
                                        <input type="hidden" name="id" value="<?= (int) $m['matricula_id'] ?>">
                                        <button type="submit" class="btn btn-icon btn-outline-danger" title="Eliminar">
                                            <i class="bi bi-trash"></i>
                                        </button>
                                    </form>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
            <p class="text-muted small mb-0"><?= count($matriculas) ?> registro(s) encontrado(s). Datos provenientes de la vista <code>v_matriculas_detalle</code> (JOIN estudiantes + cursos).</p>
        <?php else: ?>
            <div class="alert alert-info mb-0">
                <i class="bi bi-info-circle"></i> No se encontraron matrículas para los filtros aplicados.
            </div>
        <?php endif; ?>
    </div>
</div>

<?php require_once __DIR__ . '/../includes/footer.php'; ?>
