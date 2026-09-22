<?php
/**
 * Matrículas - Crear registro (Crear)
 * Un estudiante no puede repetir el mismo curso en el mismo periodo
 * (restricción UNIQUE de la base de datos).
 */
declare(strict_types=1);

require_once __DIR__ . '/../includes/auth.php';
login_required();
require_once __DIR__ . '/../config/database.php';
require_once __DIR__ . '/../includes/functions.php';

$BASE        = '../';
$active_menu = 'matriculas';
$page_title  = 'Nueva Matrícula';
require_once __DIR__ . '/../includes/header.php';

$errores = [];
$d = ['estudiante_id' => '', 'curso_id' => '', 'periodo' => '2026-02', 'fecha_matricula' => date('Y-m-d'), 'estado' => 'activa'];

// Listas para los selectores
$estudiantes = db()->query(
    'SELECT id, codigo, nombres, apellidos FROM estudiantes WHERE estado = 1 ORDER BY apellidos, nombres'
)->fetchAll();

$cursos = db()->query(
    'SELECT id, codigo, nombre FROM cursos WHERE estado = 1 ORDER BY codigo'
)->fetchAll();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    verify_csrf();

    $d = [
        'estudiante_id'    => (int) ($_POST['estudiante_id'] ?? 0),
        'curso_id'         => (int) ($_POST['curso_id'] ?? 0),
        'periodo'          => trim((string) ($_POST['periodo'] ?? '')),
        'fecha_matricula'  => trim((string) ($_POST['fecha_matricula'] ?? '')),
        'estado'           => (string) ($_POST['estado'] ?? 'activa'),
    ];

    if ($d['estudiante_id'] <= 0) $errores[] = 'Seleccione un estudiante.';
    if ($d['curso_id'] <= 0)      $errores[] = 'Seleccione un curso.';
    if (!preg_match('/^\d{4}-\d{2}$/', $d['periodo'])) {
        $errores[] = 'El periodo debe tener el formato AAAA-MM (ej. 2026-02).';
    }
    $f = explode('-', $d['fecha_matricula']);
    if (count($f) !== 3 || !checkdate((int) $f[1], (int) $f[2], (int) $f[0])) {
        $errores[] = 'La fecha de matrícula no es válida.';
    }
    if (!in_array($d['estado'], ['activa', 'retirado'], true)) $errores[] = 'El estado seleccionado no es válido.';

    if (!$errores) {
        try {
            $stmt = db()->prepare(
                'INSERT INTO matriculas (estudiante_id, curso_id, periodo, fecha_matricula, estado)
                 VALUES (:estudiante, :curso, :periodo, :fecha, :estado)'
            );
            $stmt->execute([
                ':estudiante' => $d['estudiante_id'],
                ':curso'      => $d['curso_id'],
                ':periodo'    => $d['periodo'],
                ':fecha'      => $d['fecha_matricula'],
                ':estado'     => $d['estado'],
            ]);

            flash('success', 'Matrícula registrada correctamente.');
            redirect('index.php');
        } catch (PDOException $ex) {
            if ($ex->getCode() === '23000') {
                $errores[] = 'Ese estudiante ya está matriculado en ese curso para el periodo indicado.';
            } else {
                $errores[] = 'Error al guardar la matrícula. Intente nuevamente.';
            }
        }
    }
}
?>

<div class="card">
    <div class="card-header">
        <h5><i class="bi bi-journal-plus me-2 text-warning"></i>Registrar nueva matrícula</h5>
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
                    <label class="form-label required">Estudiante</label>
                    <select class="form-select" name="estudiante_id" required>
                        <option value="">— Seleccione un estudiante —</option>
                        <?php foreach ($estudiantes as $est): ?>
                            <option value="<?= (int) $est['id'] ?>" <?= $d['estudiante_id'] === (int) $est['id'] ? 'selected' : '' ?>>
                                <?= e($est['apellidos'] . ', ' . $est['nombres'] . ' — ' . $est['codigo']) ?>
                            </option>
                        <?php endforeach; ?>
                    </select>
                </div>
                <div class="col-md-6">
                    <label class="form-label required">Curso</label>
                    <select class="form-select" name="curso_id" required>
                        <option value="">— Seleccione un curso —</option>
                        <?php foreach ($cursos as $cur): ?>
                            <option value="<?= (int) $cur['id'] ?>" <?= $d['curso_id'] === (int) $cur['id'] ? 'selected' : '' ?>>
                                <?= e($cur['codigo'] . ' — ' . $cur['nombre']) ?>
                            </option>
                        <?php endforeach; ?>
                    </select>
                </div>
                <div class="col-md-4">
                    <label class="form-label required">Periodo</label>
                    <input type="text" class="form-control" name="periodo" maxlength="7"
                           value="<?= e($d['periodo']) ?>" placeholder="2026-02" required>
                </div>
                <div class="col-md-4">
                    <label class="form-label required">Fecha de matrícula</label>
                    <input type="date" class="form-control" name="fecha_matricula"
                           value="<?= e($d['fecha_matricula']) ?>" required>
                </div>
                <div class="col-md-4">
                    <label class="form-label required">Estado</label>
                    <select class="form-select" name="estado">
                        <option value="activa"   <?= $d['estado'] === 'activa' ? 'selected' : '' ?>>Activa</option>
                        <option value="retirado" <?= $d['estado'] === 'retirado' ? 'selected' : '' ?>>Retirado</option>
                    </select>
                </div>
            </div>
            <div class="mt-4 d-flex gap-2">
                <button type="submit" class="btn btn-primary px-4"><i class="bi bi-check-lg"></i> Guardar matrícula</button>
                <a href="index.php" class="btn btn-outline-secondary">Cancelar</a>
            </div>
        </form>
    </div>
</div>

<?php require_once __DIR__ . '/../includes/footer.php'; ?>
