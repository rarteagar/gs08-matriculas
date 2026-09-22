<?php
/**
 * Matrículas - Eliminar registro (Eliminar)
 * Solo peticiones POST con token CSRF.
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
    $stmt = db()->prepare('DELETE FROM matriculas WHERE id = :id');
    $stmt->execute([':id' => $id]);
    flash('success', 'Matrícula eliminada correctamente.');
} else {
    flash('danger', 'Identificador de matrícula no válido.');
}

redirect('index.php');
