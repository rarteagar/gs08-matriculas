<?php
/**
 * Usuarios - Eliminar registro (Eliminar)
 * Solo peticiones POST con token CSRF. No permite eliminarse a sí mismo.
 */
declare(strict_types=1);

require_once __DIR__ . '/../includes/auth.php';
login_required();
require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../includes/functions.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    redirect('index.php');
}

verify_csrf();

$id = (int) ($_POST['id'] ?? 0);

if ($id <= 0) {
    flash('danger', 'Identificador de usuario no válido.');
} elseif ($id === (int) (current_user()['id'] ?? 0)) {
    flash('danger', 'No puedes eliminar tu propia cuenta.');
} else {
    $stmt = db()->prepare('DELETE FROM usuarios WHERE id = :id');
    $stmt->execute([':id' => $id]);
    flash('success', 'Usuario eliminado correctamente.');
}

redirect('index.php');
