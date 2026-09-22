<?php
/**
 * Usuarios - Listado (Leer)
 */
declare(strict_types=1);

require_once __DIR__ . '/../includes/auth.php';
login_required();
require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../includes/functions.php';

$BASE        = '../';
$active_menu = 'usuarios';
$page_title  = 'Gestión de Usuarios';
require_once __DIR__ . '/../includes/header.php';

$q = trim((string) ($_GET['q'] ?? ''));

$sql = 'SELECT id, nombre_usuario, email, nombre_completo, rol, estado, creado_en
        FROM usuarios WHERE 1 = 1';
$params = [];

if ($q !== '') {
    $sql .= ' AND (nombre_usuario LIKE :q OR email LIKE :q OR nombre_completo LIKE :q)';
    $params[':q'] = '%' . $q . '%';
}

$sql .= ' ORDER BY nombre_completo';
$stmt = db()->prepare($sql);
$stmt->execute($params);
$usuarios = $stmt->fetchAll();

$yo = (int) (current_user()['id'] ?? 0);
?>

<div class="card">
    <div class="card-header">
        <h5><i class="bi bi-people me-2 text-warning"></i>Listado de usuarios</h5>
        <a href="create.php" class="btn btn-gold btn-sm">
            <i class="bi bi-plus-lg"></i> Nuevo usuario
        </a>
    </div>
    <div class="card-body">
        <form method="get" action="index.php" class="row g-2 mb-3">
            <div class="col-md-8 col-lg-5">
                <div class="input-group">
                    <span class="input-group-text"><i class="bi bi-search"></i></span>
                    <input type="text" class="form-control" name="q" value="<?= e($q) ?>"
                           placeholder="Buscar por usuario, correo o nombre...">
                </div>
            </div>
            <div class="col-auto">
                <button type="submit" class="btn btn-primary">Buscar</button>
                <?php if ($q !== ''): ?>
                    <a href="index.php" class="btn btn-outline-secondary">Limpiar</a>
                <?php endif; ?>
            </div>
        </form>

        <?php if ($usuarios): ?>
            <div class="table-responsive">
                <table class="table table-hover align-middle">
                    <thead>
                        <tr>
                            <th>Usuario</th>
                            <th>Nombre completo</th>
                            <th>Correo</th>
                            <th>Rol</th>
                            <th>Estado</th>
                            <th class="text-end">Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($usuarios as $u): ?>
                            <tr>
                                <td class="fw-semibold">
                                    <?= e($u['nombre_usuario']) ?>
                                    <?php if ((int) $u['id'] === $yo): ?>
                                        <span class="badge text-bg-info ms-1">Tú</span>
                                    <?php endif; ?>
                                </td>
                                <td><?= e($u['nombre_completo']) ?></td>
                                <td><?= e($u['email']) ?></td>
                                <td>
                                    <span class="badge <?= $u['rol'] === 'admin' ? 'text-bg-warning' : 'text-bg-secondary' ?>">
                                        <?= e(ucfirst($u['rol'])) ?>
                                    </span>
                                </td>
                                <td>
                                    <span class="badge badge-<?= (int) $u['estado'] === 1 ? 'active' : 'inactive' ?>">
                                        <?= (int) $u['estado'] === 1 ? 'Activo' : 'Inactivo' ?>
                                    </span>
                                </td>
                                <td class="text-end text-nowrap">
                                    <a href="edit.php?id=<?= (int) $u['id'] ?>" class="btn btn-icon btn-outline-primary" title="Editar">
                                        <i class="bi bi-pencil"></i>
                                    </a>
                                    <?php if ((int) $u['id'] !== $yo): ?>
                                        <form method="post" action="delete.php" class="d-inline"
                                              data-confirm="¿Eliminar al usuario <?= e($u['nombre_usuario']) ?>?">
                                            <?= csrf_field() ?>
                                            <input type="hidden" name="id" value="<?= (int) $u['id'] ?>">
                                            <button type="submit" class="btn btn-icon btn-outline-danger" title="Eliminar">
                                                <i class="bi bi-trash"></i>
                                            </button>
                                        </form>
                                    <?php endif; ?>
                                </td>
                            </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
            <p class="text-muted small mb-0"><?= count($usuarios) ?> registro(s) encontrado(s). No puedes eliminar tu propia cuenta.</p>
        <?php else: ?>
            <div class="alert alert-info mb-0">
                <i class="bi bi-info-circle"></i> No se encontraron usuarios.
            </div>
        <?php endif; ?>
    </div>
</div>

<?php require_once __DIR__ . '/../includes/footer.php'; ?>
