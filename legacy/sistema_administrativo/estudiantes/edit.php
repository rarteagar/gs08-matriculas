<?php
/**
 * Estudiantes - Editar registro (Actualizar)
 */
declare(strict_types=1);

require_once __DIR__ . '/../includes/auth.php';
login_required();
require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../includes/functions.php';

$BASE        = '../';
$active_menu = 'estudiantes';
$page_title  = 'Editar Estudiante';
require_once __DIR__ . '/../includes/header.php';

$id = (int) ($_GET['id'] ?? 0);
if ($id <= 0) {
    flash('danger', 'Identificador de estudiante no válido.');
    redirect('index.php');
}

$stmt = db()->prepare('SELECT * FROM estudiantes WHERE id = :id');
$stmt->execute([':id' => $id]);
$est = $stmt->fetch();

if (!$est) {
    flash('danger', 'El estudiante solicitado no existe.');
    redirect('index.php');
}

$errores = [];
$d = [
    'codigo'           => $est['codigo'],
    'dni'              => $est['dni'],
    'nombres'          => $est['nombres'],
    'apellidos'        => $est['apellidos'],
    'email'            => (string) $est['email'],
    'telefono'         => (string) $est['telefono'],
    'fecha_nacimiento' => (string) $est['fecha_nacimiento'],
    'direccion'        => (string) $est['direccion'],
    'estado'           => (int) $est['estado'],
];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    verify_csrf();

    $d = [
        'codigo'           => trim((string) ($_POST['codigo'] ?? '')),
        'dni'              => trim((string) ($_POST['dni'] ?? '')),
        'nombres'          => trim((string) ($_POST['nombres'] ?? '')),
        'apellidos'        => trim((string) ($_POST['apellidos'] ?? '')),
        'email'            => trim((string) ($_POST['email'] ?? '')),
        'telefono'         => trim((string) ($_POST['telefono'] ?? '')),
        'fecha_nacimiento' => trim((string) ($_POST['fecha_nacimiento'] ?? '')),
        'direccion'        => trim((string) ($_POST['direccion'] ?? '')),
        'estado'           => isset($_POST['estado']) ? 1 : 0,
    ];

    if ($d['codigo'] === '')    $errores[] = 'El código es obligatorio.';
    if (mb_strlen($d['codigo']) > 20) $errores[] = 'El código no puede superar 20 caracteres.';
    if ($d['dni'] === '')       $errores[] = 'El DNI es obligatorio.';
    elseif (!preg_match('/^\d{8}$/', $d['dni'])) $errores[] = 'El DNI debe tener exactamente 8 dígitos.';
    if ($d['nombres'] === '')   $errores[] = 'Los nombres son obligatorios.';
    if ($d['apellidos'] === '') $errores[] = 'Los apellidos son obligatorios.';
    if ($d['email'] !== '' && !filter_var($d['email'], FILTER_VALIDATE_EMAIL)) {
        $errores[] = 'El correo electrónico no tiene un formato válido.';
    }
    if ($d['fecha_nacimiento'] !== '') {
        $f = explode('-', $d['fecha_nacimiento']);
        if (count($f) !== 3 || !checkdate((int) $f[1], (int) $f[2], (int) $f[0])) {
            $errores[] = 'La fecha de nacimiento no es válida.';
        }
    }

    if (!$errores) {
        try {
            $stmt = db()->prepare(
                'UPDATE estudiantes
                 SET codigo = :codigo, dni = :dni, nombres = :nombres, apellidos = :apellidos,
                     email = :email, telefono = :telefono, fecha_nacimiento = :fecha_nacimiento,
                     direccion = :direccion, estado = :estado
                 WHERE id = :id'
            );
            $stmt->execute([
                ':codigo'           => $d['codigo'],
                ':dni'              => $d['dni'],
                ':nombres'          => $d['nombres'],
                ':apellidos'        => $d['apellidos'],
                ':email'            => $d['email'] !== '' ? $d['email'] : null,
                ':telefono'         => $d['telefono'] !== '' ? $d['telefono'] : null,
                ':fecha_nacimiento' => $d['fecha_nacimiento'] !== '' ? $d['fecha_nacimiento'] : null,
                ':direccion'        => $d['direccion'] !== '' ? $d['direccion'] : null,
                ':estado'           => $d['estado'],
                ':id'               => $id,
            ]);

            flash('success', 'Estudiante actualizado correctamente.');
            redirect('index.php');
        } catch (PDOException $ex) {
            if ($ex->getCode() === '23000') {
                $errores[] = 'Ya existe otro estudiante con ese código o DNI.';
            } else {
                $errores[] = 'Error al actualizar el registro. Intente nuevamente.';
            }
        }
    }
}
?>

<div class="card">
    <div class="card-header">
        <h5><i class="bi bi-person-gear me-2 text-warning"></i>Editar estudiante</h5>
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

        <form method="post" action="edit.php?id=<?= $id ?>" novalidate>
            <?= csrf_field() ?>
            <div class="row g-3">
                <div class="col-md-4">
                    <label class="form-label required">Código de estudiante</label>
                    <input type="text" class="form-control" name="codigo" maxlength="20"
                           value="<?= e($d['codigo']) ?>" required>
                </div>
                <div class="col-md-4">
                    <label class="form-label required">DNI</label>
                    <input type="text" class="form-control" name="dni" maxlength="8" inputmode="numeric"
                           value="<?= e($d['dni']) ?>" required>
                </div>
                <div class="col-md-4">
                    <label class="form-label">Fecha de nacimiento</label>
                    <input type="date" class="form-control" name="fecha_nacimiento"
                           value="<?= e($d['fecha_nacimiento']) ?>">
                </div>
                <div class="col-md-6">
                    <label class="form-label required">Nombres</label>
                    <input type="text" class="form-control" name="nombres" maxlength="80"
                           value="<?= e($d['nombres']) ?>" required>
                </div>
                <div class="col-md-6">
                    <label class="form-label required">Apellidos</label>
                    <input type="text" class="form-control" name="apellidos" maxlength="80"
                           value="<?= e($d['apellidos']) ?>" required>
                </div>
                <div class="col-md-6">
                    <label class="form-label">Correo electrónico</label>
                    <input type="email" class="form-control" name="email" maxlength="100"
                           value="<?= e($d['email']) ?>">
                </div>
                <div class="col-md-6">
                    <label class="form-label">Teléfono</label>
                    <input type="text" class="form-control" name="telefono" maxlength="20"
                           value="<?= e($d['telefono']) ?>">
                </div>
                <div class="col-12">
                    <label class="form-label">Dirección</label>
                    <input type="text" class="form-control" name="direccion" maxlength="150"
                           value="<?= e($d['direccion']) ?>">
                </div>
                <div class="col-12">
                    <div class="form-check form-switch">
                        <input class="form-check-input" type="checkbox" name="estado" id="estado"
                               value="1" <?= $d['estado'] === 1 ? 'checked' : '' ?>>
                        <label class="form-check-label" for="estado">Estudiante activo</label>
                    </div>
                </div>
            </div>
            <div class="mt-4 d-flex gap-2">
                <button type="submit" class="btn btn-primary px-4"><i class="bi bi-check-lg"></i> Actualizar estudiante</button>
                <a href="index.php" class="btn btn-outline-secondary">Cancelar</a>
            </div>
        </form>
    </div>
</div>

<?php require_once __DIR__ . '/../includes/footer.php'; ?>
