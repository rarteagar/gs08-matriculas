<?php
/**
 * Cursos - Eliminar registro (Eliminar)
 * Solo se aceptan peticiones POST (con token CSRF).
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

if ($id > 0) {
    $stmt = db()->prepare('DELETE FROM cursos WHERE id = :id');
    $stmt->execute([':id' => $id]);

    flash('success', 'Curso eliminado correctamente (sus matrículas también, por integridad referencial).');
} else {
    flash('danger', 'Identificador de curso no válido.');
}

redirect('index.php');
