<?php
/**
 * Autenticación y manejo de sesiones.
 */
declare(strict_types=1);

require_once __DIR__ . '/functions.php';

if (session_status() === PHP_SESSION_NONE) {
    session_start();
}

/** Devuelve el usuario autenticado o null. */
function current_user(): ?array
{
    return $_SESSION['user'] ?? null;
}

/** Indica si hay sesión iniciada. */
function is_logged_in(): bool
{
    return current_user() !== null;
}

/**
 * Protege páginas internas.
 * $loginUrl: ruta al login según la ubicación del archivo que llama
 * ('' desde la raíz, '../' desde una subcarpeta de módulo).
 */
function login_required(string $loginUrl = '../login.php'): void
{
    if (!is_logged_in()) {
        redirect($loginUrl);
    }
}
