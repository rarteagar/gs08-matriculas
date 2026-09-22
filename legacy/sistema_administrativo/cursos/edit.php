<?php
/**
 * Cursos - Editar registro (Actualizar)
 */
declare(strict_types=1);

require_once __DIR__ . '/../includes/auth.php';
login_required();
require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../includes/functions.php';

$BASE        = '../';
$active_menu = 'cursos';
$page_title  = 'Editar Curso';
require_once __DIR__ . '/../includes/header.php';

$id = (int) ($_GET['id'] ?? 0);
if ($id <= 0) {
    flash('danger', 'Identificador de curso no válido.');
    redirect('index.php');
}

$stmt = db()->prepare('SELECT * FROM cursos WHERE id = :id');
$stmt->execute([':id' => $id]);
$cur = $stmt->fetch();

if (!$cur) {
    flash('danger', 'El curso solicitado no existe.');
    redirect('index.php');
}

$errores = [];
$d = [
    'codigo'      => $cur['codigo'],
    'nombre'      => $cur['nombre'],
    'descripcion' => (string) $cur['descripcion'],
    'creditos'    => (string) $cur['creditos'],
    'horas'       => (string) $cur['horas'],
    'estado'      => (int) $cur['estado'],
];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    verify_csrf();

    $d = [
        'codigo'      => trim((string) ($_POST['codigo'] ?? '')),
        'nombre'      => trim((string) ($_POST['nombre'] ?? '')),
        'descripcion' => trim((string) ($_POST['descripcion'] ?? '')),
        'creditos'    => trim((string) ($_POST['creditos'] ?? '')),
        'horas'       => trim((string) ($_POST['horas'] ?? '')),
        'estado'      => isset($_POST['estado']) ? 1 : 0,
    ];

    if ($d['codigo'] === '') $errores[] = 'El código del curso es obligatorio.';
    if (mb_strlen($d['codigo']) > 20) $errores[] = 'El código no puede superar 20 caracteres.';
    if ($d['nombre'] === '') $errores[] = 'El nombre del curso es obligatorio.';
    if (!ctype_digit($d['creditos']) || (int) $d['creditos'] < 1 || (int) $d['creditos'] > 10) {
        $errores[] = 'Los créditos deben ser un número entre 1 y 10.';
    }
    if (!ctype_digit($d['horas']) || (int) $d['horas'] < 1) {
        $errores[] = 'Las horas deben ser un número entero positivo.';
    }

    if (!$errores) {
        try {
            $stmt = db()->prepare(
                'UPDATE cursos
                 SET codigo = :codigo, nombre = :nombre, descripcion = :descripcion,
                     creditos = :creditos, horas = :horas, estado = :estado
                 WHERE id = :id'
            );
            $stmt->execute([
                ':codigo'      => $d['codigo'],
                ':nombre'      => $d['nombre'],
                ':descripcion' => $d['descripcion'] !== '' ? $d['descripcion'] : null,
                ':creditos'    => (int) $d['creditos'],
                ':horas'       => (int) $d['horas'],
                ':estado'      => $d['estado'],
                ':id'          => $id,
            ]);

            flash('success', 'Curso actualizado correctamente.');
            redirect('index.php');
        } catch (PDOException $ex) {
            if ($ex->getCode() === '23000') {
                $errores[] = 'Ya existe otro curso con ese código.';
            } else {
                $errores[] = 'Error al actualizar el registro. Intente nuevamente.';
            }
        }
    }
}
?>

<div class="card">
    <div class="card-header">
        <h5><i class="bi bi-book-half me-2 text-warning"></i>Editar curso</h5>
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
                    <label class="form-label required">Código del curso</label>
                    <input type="text" class="form-control" name="codigo" maxlength="20"
                           value="<?= e($d['codigo']) ?>" required>
                </div>
                <div class="col-md-4">
                    <label class="form-label required">Créditos</label>
                    <input type="number" class="form-control" name="creditos" min="1" max="10"
                           value="<?= e($d['creditos']) ?>" required>
                </div>
                <div class="col-md-4">
                    <label class="form-label required">Horas</label>
                    <input type="number" class="form-control" name="horas" min="1"
                           value="<?= e($d['horas']) ?>" required>
                </div>
                <div class="col-12">
                    <label class="form-label required">Nombre del curso</label>
                    <input type="text" class="form-control" name="nombre" maxlength="100"
                           value="<?= e($d['nombre']) ?>" required>
                </div>
                <div class="col-12">
                    <label class="form-label">Descripción</label>
                    <textarea class="form-control" name="descripcion" rows="3"
                              maxlength="500"><?= e($d['descripcion']) ?></textarea>
                </div>
                <div class="col-12">
                    <div class="form-check form-switch">
                        <input class="form-check-input" type="checkbox" name="estado" id="estado"
                               value="1" <?= $d['estado'] === 1 ? 'checked' : '' ?>>
                        <label class="form-check-label" for="estado">Curso activo</label>
                    </div>
                </div>
            </div>
            <div class="mt-4 d-flex gap-2">
                <button type="submit" class="btn btn-primary px-4"><i class="bi bi-check-lg"></i> Actualizar curso</button>
                <a href="index.php" class="btn btn-outline-secondary">Cancelar</a>
            </div>
        </form>
    </div>
</div>

<?php require_once __DIR__ . '/../includes/footer.php'; ?>
