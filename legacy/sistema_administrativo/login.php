<?php
/**
 * Login del sistema: autenticación con prepared statements
 * y verificación de contraseña encriptada (password_verify).
 */
declare(strict_types=1);

require_once __DIR__ . '/includes/auth.php';
require_once __DIR__ . '/includes/functions.php';
require_once __DIR__ . '/config/database.php';

// Si ya hay sesión, va directo al panel
if (is_logged_in()) {
    redirect('dashboard.php');
}

$error = '';
$oldUser = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    verify_csrf();

    $usuario = trim((string) ($_POST['nombre_usuario'] ?? ''));
    $clave   = (string) ($_POST['password'] ?? '');
    $oldUser = $usuario;

    if ($usuario === '' || $clave === '') {
        $error = 'Ingrese su usuario y contraseña.';
    } else {
        $stmt = db()->prepare(
            'SELECT id, nombre_usuario, email, password_hash, nombre_completo, rol, estado
             FROM usuarios
             WHERE nombre_usuario = :u1 OR email = :u2
             LIMIT 1'
        );
        $stmt->execute([':u1' => $usuario, ':u2' => $usuario]);
        $row = $stmt->fetch();

        if ($row && (int) $row['estado'] === 1 && password_verify($clave, $row['password_hash'])) {
            // Regenera el ID de sesión para prevenir fijación de sesión
            session_regenerate_id(true);

            $_SESSION['user'] = [
                'id'              => (int) $row['id'],
                'nombre_usuario'  => $row['nombre_usuario'],
                'email'           => $row['email'],
                'nombre_completo' => $row['nombre_completo'],
                'rol'             => $row['rol'],
            ];

            redirect('dashboard.php');
        }

        $error = 'Credenciales incorrectas o usuario inactivo.';
    }
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Iniciar sesión · <?= APP_NAME ?></title>
    <link rel="stylesheet" href="assets/vendor/bootstrap/css/bootstrap.min.css">
    <link rel="stylesheet" href="assets/vendor/bootstrap-icons/bootstrap-icons.min.css">
    <link rel="stylesheet" href="assets/css/style.css">
</head>
<body class="login-body">

    <div class="login-card">
        <div class="login-brand">
            <img src="assets/img/logo.png" alt="Logo de <?= APP_NAME ?>">
            <div class="brand-name">Instituto Privado</div>
            <div class="brand-sub">Horizonte</div>
        </div>

        <?php if ($error !== ''): ?>
            <div class="alert alert-danger py-2" role="alert">
                <i class="bi bi-exclamation-triangle"></i> <?= e($error) ?>
            </div>
        <?php endif; ?>

        <form method="post" action="login.php" autocomplete="off" novalidate>
            <?= csrf_field() ?>
            <div class="mb-3">
                <label for="nombre_usuario" class="form-label">Usuario o correo</label>
                <div class="input-group">
                    <span class="input-group-text"><i class="bi bi-person"></i></span>
                    <input type="text" class="form-control" id="nombre_usuario" name="nombre_usuario"
                           value="<?= e($oldUser) ?>" placeholder="admin" required autofocus>
                </div>
            </div>
            <div class="mb-4">
                <label for="password" class="form-label">Contraseña</label>
                <div class="input-group">
                    <span class="input-group-text"><i class="bi bi-lock"></i></span>
                    <input type="password" class="form-control" id="password" name="password"
                           placeholder="••••••••" required>
                </div>
            </div>
            <button type="submit" class="btn btn-primary w-100 py-2 fw-semibold">
                <i class="bi bi-box-arrow-in-right"></i> Ingresar al sistema
            </button>
        </form>

        <div class="login-foot">
            Sistema Administrativo Web · PHP, MySQL y Bootstrap
        </div>
    </div>

</body>
</html>
