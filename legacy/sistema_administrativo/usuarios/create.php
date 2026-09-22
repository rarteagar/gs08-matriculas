<?php
/**
 * Usuarios - Crear registro (Crear)
 * La contraseña se encripta con password_hash().
 */
declare(strict_types=1);

require_once __DIR__ . '/../includes/auth.php';
login_required();
require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../includes/functions.php';

$BASE        = '../';
$active_menu = 'usuarios';
$page_title  = 'Nuevo Usuario';
require_once __DIR__ . '/../includes/header.php';

$errores = [];
$d = ['nombre_usuario' => '', 'email' => '', 'nombre_completo' => '', 'rol' => 'admin'];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    verify_csrf();

    $d = [
        'nombre_usuario'  => trim((string) ($_POST['nombre_usuario'] ?? '')),
        'email'           => trim((string) ($_POST['email'] ?? '')),
        'nombre_completo' => trim((string) ($_POST['nombre_completo'] ?? '')),
        'rol'             => (string) ($_POST['rol'] ?? 'admin'),
        'password'        => (string) ($_POST['password'] ?? ''),
        'password2'       => (string) ($_POST['password2'] ?? ''),
    ];

    if ($d['nombre_usuario'] === '') $errores[] = 'El nombre de usuario es obligatorio.';
    elseif (!preg_match('/^[a-zA-Z0-9_\.]{3,50}$/', $d['nombre_usuario'])) {
        $errores[] = 'El usuario debe tener entre 3 y 50 caracteres (letras, números, punto o guion bajo).';
    }
    if ($d['email'] === '') $errores[] = 'El correo electrónico es obligatorio.';
    elseif (!filter_var($d['email'], FILTER_VALIDATE_EMAIL)) $errores[] = 'El correo no tiene un formato válido.';
    if ($d['nombre_completo'] === '') $errores[] = 'El nombre completo es obligatorio.';
    if (!in_array($d['rol'], ['admin', 'asistente'], true)) $errores[] = 'El rol seleccionado no es válido.';
    if (strlen($d['password']) < 8) $errores[] = 'La contraseña debe tener al menos 8 caracteres.';
    if ($d['password'] !== $d['password2']) $errores[] = 'La confirmación de contraseña no coincide.';

    if (!$errores) {
        try {
            $stmt = db()->prepare(
                'INSERT INTO usuarios (nombre_usuario, email, password_hash, nombre_completo, rol)
                 VALUES (:u, :email, :pass, :nombre, :rol)'
            );
            $stmt->execute([
                ':u'      => $d['nombre_usuario'],
                ':email'  => $d['email'],
                ':pass'   => password_hash($d['password'], PASSWORD_DEFAULT),
                ':nombre' => $d['nombre_completo'],
                ':rol'    => $d['rol'],
            ]);

            flash('success', 'Usuario creado correctamente. La contraseña fue encriptada con password_hash().');
            redirect('index.php');
        } catch (PDOException $ex) {
            if ($ex->getCode() === '23000') {
                $errores[] = 'Ya existe un usuario con ese nombre de usuario o correo.';
            } else {
                $errores[] = 'Error al guardar el registro. Intente nuevamente.';
            }
        }
    }
}
?>

<div class="card">
    <div class="card-header">
        <h5><i class="bi bi-person-plus me-2 text-warning"></i>Registrar nuevo usuario</h5>
        <a href="index.php" class="btn btn-outline-secondary btn-sm"><i class="bi bi-arrow-left"></i> Volver</a>
    </div>
    <div class="card-body">
        <?php if ($errores): ?>
            <div class="alert alert-danger">
                <ul class="mb-0">
                    <?php foreach ($errores as $err): ?><li><?= e($err) ?></li><?php endforeach; ?>
                </ul>
            </div>
        <?php endif; ?>

        <form method="post" action="create.php" novalidate>
            <?= csrf_field() ?>
            <div class="row g-3">
                <div class="col-md-6">
                    <label class="form-label required">Nombre de usuario</label>
                    <input type="text" class="form-control" name="nombre_usuario" maxlength="50"
                           value="<?= e($d['nombre_usuario']) ?>" placeholder="ej. jperez" required>
                </div>
                <div class="col-md-6">
                    <label class="form-label required">Correo electrónico</label>
                    <input type="email" class="form-control" name="email" maxlength="100"
                           value="<?= e($d['email']) ?>" required>
                </div>
                <div class="col-md-6">
                    <label class="form-label required">Nombre completo</label>
                    <input type="text" class="form-control" name="nombre_completo" maxlength="100"
                           value="<?= e($d['nombre_completo']) ?>" required>
                </div>
                <div class="col-md-6">
                    <label class="form-label required">Rol</label>
                    <select class="form-select" name="rol">
                        <option value="admin"     <?= $d['rol'] === 'admin' ? 'selected' : '' ?>>Administrador</option>
                        <option value="asistente" <?= $d['rol'] === 'asistente' ? 'selected' : '' ?>>Asistente</option>
                    </select>
                </div>
                <div class="col-md-6">
                    <label class="form-label required">Contraseña (mín. 8 caracteres)</label>
                    <input type="password" class="form-control" name="password" autocomplete="new-password" required>
                </div>
                <div class="col-md-6">
                    <label class="form-label required">Confirmar contraseña</label>
                    <input type="password" class="form-control" name="password2" autocomplete="new-password" required>
                </div>
            </div>
            <div class="mt-4 d-flex gap-2">
                <button type="submit" class="btn btn-primary px-4"><i class="bi bi-check-lg"></i> Crear usuario</button>
                <a href="index.php" class="btn btn-outline-secondary">Cancelar</a>
            </div>
        </form>
    </div>
</div>

<?php require_once __DIR__ . '/../includes/footer.php'; ?>
