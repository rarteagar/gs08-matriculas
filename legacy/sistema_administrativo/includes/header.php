<?php
/**
 * Cabecera del panel: sidebar + topbar + apertura de contenido.
 * Variables opcionales: $BASE ('', '../'), $active_menu, $page_title.
 */
declare(strict_types=1);

require_once __DIR__ . '/auth.php';
require_once __DIR__ . '/functions.php';
require_once __DIR__ . '/../config/database.php';

$BASE        = $BASE ?? '';
$active_menu = $active_menu ?? '';
$page_title  = $page_title ?? 'Panel de Control';
$user        = current_user();

$menu = [
    'dashboard' => ['dashboard.php',            'bi-speedometer2', 'Dashboard'],
    'usuarios'  => ['usuarios/index.php',       'bi-people',       'Usuarios'],
    'estudiantes' => ['estudiantes/index.php',  'bi-person-video3','Estudiantes'],
    'cursos'    => ['cursos/index.php',         'bi-book',         'Cursos'],
    'matriculas' => ['matriculas/index.php',    'bi-journal-check','Matrículas'],
];
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title><?= e($page_title) ?> · <?= APP_NAME ?></title>
    <link rel="stylesheet" href="<?= $BASE ?>assets/vendor/bootstrap/css/bootstrap.min.css">
    <link rel="stylesheet" href="<?= $BASE ?>assets/vendor/bootstrap-icons/bootstrap-icons.min.css">
    <link rel="stylesheet" href="<?= $BASE ?>assets/css/style.css">
</head>
<body>

<!-- Barra lateral -->
<aside class="sidebar" id="sidebar">
    <div class="sidebar-brand">
        <img src="<?= $BASE ?>assets/img/logo.png" alt="Logo de <?= APP_NAME ?>" class="brand-logo">
        <div class="brand-text">
            <span class="brand-name">Instituto Privado</span>
            <span class="brand-sub">Horizonte</span>
        </div>
    </div>

    <nav class="sidebar-nav">
        <?php foreach ($menu as $key => $item): ?>
            <a href="<?= $BASE . $item[0] ?>"
               class="nav-item <?= $active_menu === $key ? 'active' : '' ?>">
                <i class="bi <?= $item[1] ?>"></i><span><?= $item[2] ?></span>
            </a>
        <?php endforeach; ?>
    </nav>

    <div class="sidebar-footer">
        <div class="user-chip">
            <i class="bi bi-person-circle"></i>
            <div class="user-chip-text">
                <span class="user-name"><?= e($user['nombre_completo'] ?? 'Usuario') ?></span>
                <span class="user-role"><?= e(ucfirst($user['rol'] ?? '')) ?></span>
            </div>
        </div>
        <a href="<?= $BASE ?>logout.php" class="btn-logout">
            <i class="bi bi-box-arrow-right"></i> Cerrar sesión
        </a>
    </div>
</aside>
<div class="sidebar-backdrop" id="sidebarBackdrop"></div>

<!-- Contenido principal -->
<div class="main">
    <header class="topbar">
        <button class="btn btn-toggle" id="btnToggleSidebar" aria-label="Abrir menú">
            <i class="bi bi-list"></i>
        </button>
        <h1 class="page-title"><?= e($page_title) ?></h1>
    </header>

    <main class="content">
        <?php if ($flash = get_flash()): ?>
            <div class="alert alert-<?= e($flash['type']) ?> alert-dismissible fade show" role="alert">
                <i class="bi <?= $flash['type'] === 'success' ? 'bi-check-circle' : ($flash['type'] === 'danger' ? 'bi-exclamation-triangle' : 'bi-info-circle') ?>"></i>
                <?= e($flash['message']) ?>
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Cerrar"></button>
            </div>
        <?php endif; ?>
