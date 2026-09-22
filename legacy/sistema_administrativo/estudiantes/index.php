<?php
/**
 * Estudiantes - Listado con búsqueda (Leer)
 */
declare(strict_types=1);

require_once __DIR__ . '/../includes/auth.php';
login_required();
require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../includes/functions.php';

$BASE        = '../';
$active_menu = 'estudiantes';
$page_title  = 'Gestión de Estudiantes';
require_once __DIR__ . '/../includes/header.php';

$q = trim((string) ($_GET['q'] ?? ''));

$sql = 'SELECT id, codigo, dni, nombres, apellidos, email, telefono, estado
        FROM estudiantes WHERE 1 = 1';
$params = [];

if ($q !== '') {
    $sql .= ' AND (codigo LIKE :q OR dni LIKE :q OR nombres LIKE :q OR apellidos LIKE :q)';
    $params[':q'] = '%' . $q . '%';
}

$sql .= ' ORDER BY apellidos, nombres';
$stmt = db()->prepare($sql);
$stmt->execute($params);
$estudiantes = $stmt->fetchAll();
?>

<div class="card">
    <div class="card-header">
        <h5><i class="bi bi-person-video3 me-2 text-warning"></i>Listado de estudiantes</h5>
        <a href="create.php" class="btn btn-gold btn-sm">
            <i class="bi bi-plus-lg"></i> Nuevo estudiante
        </a>
    </div>
    <div class="card-body">
        <form method="get" action="index.php" class="row g-2 mb-3">
            <div class="col-md-8 col-lg-5">
                <div class="input-group">
                    <span class="input-group-text"><i class="bi bi-search"></i></span>
                    <input type="text" class="form-control" name="q" value="<?= e($q) ?>"
                           placeholder="Buscar por código, DNI, nombres o apellidos...">
                </div>
            </div>
            <div class="col-auto">
                <button type="submit" class="btn btn-primary">Buscar</button>
                <?php if ($q !== ''): ?>
                    <a href="index.php" class="btn btn-outline-secondary">Limpiar</a>
                <?php endif; ?>
            </div>
        </form>

        <?php if ($estudiantes): ?>
            <div class="table-responsive">
                <table class="table table-hover align-middle">
                    <thead>
                        <tr>
                            <th>Código</th>
                            <th>Apellidos y nombres</th>
                            <th>DNI</th>
                            <th>Correo</th>
                            <th>Teléfono</th>
                            <th>Estado</th>
                            <th class="text-end">Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($estudiantes as $e): ?>
                            <tr>
                                <td class="fw-semibold"><?= e($e['codigo']) ?></td>
                                <td><?= e($e['apellidos'] . ', ' . $e['nombres']) ?></td>
                                <td><?= e($e['dni']) ?></td>
                                <td><?= e($e['email'] ?? '—') ?></td>
                                <td><?= e($e['telefono'] ?? '—') ?></td>
                                <td>
                                    <span class="badge badge-<?= (int) $e['estado'] === 1 ? 'active' : 'inactive' ?>">
                                        <?= (int) $e['estado'] === 1 ? 'Activo' : 'Inactivo' ?>
                                    </span>
                                </td>
                                <td class="text-end text-nowrap">
                                    <a href="edit.php?id=<?= (int) $e['id'] ?>" class="btn btn-icon btn-outline-primary" title="Editar">
                                        <i class="bi bi-pencil"></i>
                                    </a>
                                    <form method="post" action="delete.php" class="d-inline"
                                          data-confirm="¿Eliminar al estudiante <?= e($e['apellidos'] . ', ' . $e['nombres']) ?>? Se eliminarán también sus matrículas.">
                                        <?= csrf_field() ?>
                                        <input type="hidden" name="id" value="<?= (int) $e['id'] ?>">
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
            <p class="text-muted small mb-0"><?= count($estudiantes) ?> registro(s) encontrado(s).</p>
        <?php else: ?>
            <div class="alert alert-info mb-0">
                <i class="bi bi-info-circle"></i> No se encontraron estudiantes<?= $q !== '' ? ' para la búsqueda realizada' : ' registrados' ?>.
            </div>
        <?php endif; ?>
    </div>
</div>

<?php require_once __DIR__ . '/../includes/footer.php'; ?>
