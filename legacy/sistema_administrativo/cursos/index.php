<?php
/**
 * Cursos - Listado con búsqueda (Leer)
 */
declare(strict_types=1);

require_once __DIR__ . '/../includes/auth.php';
login_required();
require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../includes/functions.php';

$BASE        = '../';
$active_menu = 'cursos';
$page_title  = 'Gestión de Cursos';
require_once __DIR__ . '/../includes/header.php';

$q = trim((string) ($_GET['q'] ?? ''));

$sql = 'SELECT c.id, c.codigo, c.nombre, c.creditos, c.horas, c.estado,
               (SELECT COUNT(*) FROM matriculas m WHERE m.curso_id = c.id AND m.estado = "activa") AS matriculados
        FROM cursos c WHERE 1 = 1';
$params = [];

if ($q !== '') {
    $sql .= ' AND (c.codigo LIKE :q OR c.nombre LIKE :q)';
    $params[':q'] = '%' . $q . '%';
}

$sql .= ' ORDER BY c.codigo';
$stmt = db()->prepare($sql);
$stmt->execute($params);
$cursos = $stmt->fetchAll();
?>

<div class="card">
    <div class="card-header">
        <h5><i class="bi bi-book me-2 text-warning"></i>Listado de cursos</h5>
        <a href="create.php" class="btn btn-gold btn-sm">
            <i class="bi bi-plus-lg"></i> Nuevo curso
        </a>
    </div>
    <div class="card-body">
        <form method="get" action="index.php" class="row g-2 mb-3">
            <div class="col-md-8 col-lg-5">
                <div class="input-group">
                    <span class="input-group-text"><i class="bi bi-search"></i></span>
                    <input type="text" class="form-control" name="q" value="<?= e($q) ?>"
                           placeholder="Buscar por código o nombre del curso...">
                </div>
            </div>
            <div class="col-auto">
                <button type="submit" class="btn btn-primary">Buscar</button>
                <?php if ($q !== ''): ?>
                    <a href="index.php" class="btn btn-outline-secondary">Limpiar</a>
                <?php endif; ?>
            </div>
        </form>

        <?php if ($cursos): ?>
            <div class="table-responsive">
                <table class="table table-hover align-middle">
                    <thead>
                        <tr>
                            <th>Código</th>
                            <th>Nombre</th>
                            <th>Créditos</th>
                            <th>Horas</th>
                            <th>Matriculados</th>
                            <th>Estado</th>
                            <th class="text-end">Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($cursos as $c): ?>
                            <tr>
                                <td class="fw-semibold"><?= e($c['codigo']) ?></td>
                                <td><?= e($c['nombre']) ?></td>
                                <td><?= (int) $c['creditos'] ?></td>
                                <td><?= (int) $c['horas'] ?></td>
                                <td>
                                    <span class="badge text-bg-secondary"><?= (int) $c['matriculados'] ?></span>
                                </td>
                                <td>
                                    <span class="badge badge-<?= (int) $c['estado'] === 1 ? 'active' : 'inactive' ?>">
                                        <?= (int) $c['estado'] === 1 ? 'Activo' : 'Inactivo' ?>
                                    </span>
                                </td>
                                <td class="text-end text-nowrap">
                                    <a href="edit.php?id=<?= (int) $c['id'] ?>" class="btn btn-icon btn-outline-primary" title="Editar">
                                        <i class="bi bi-pencil"></i>
                                    </a>
                                    <form method="post" action="delete.php" class="d-inline"
                                          data-confirm="¿Eliminar el curso <?= e($c['nombre']) ?>? Se eliminarán también sus matrículas.">
                                        <?= csrf_field() ?>
                                        <input type="hidden" name="id" value="<?= (int) $c['id'] ?>">
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
            <p class="text-muted small mb-0"><?= count($cursos) ?> registro(s) encontrado(s).</p>
        <?php else: ?>
            <div class="alert alert-info mb-0">
                <i class="bi bi-info-circle"></i> No se encontraron cursos<?= $q !== '' ? ' para la búsqueda realizada' : ' registrados' ?>.
            </div>
        <?php endif; ?>
    </div>
</div>

<?php require_once __DIR__ . '/../includes/footer.php'; ?>
