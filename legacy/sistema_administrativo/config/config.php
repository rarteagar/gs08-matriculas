<?php
/**
 * Configuración general del sistema
 * Instituto Privado Horizonte - Sistema Administrativo Web
 */
declare(strict_types=1);

define('APP_NAME', 'Instituto Privado Horizonte');
define('APP_SHORT', 'IPH');

// Entorno: 'dev' muestra errores en pantalla; 'prod' los oculta y registra en log
define('APP_ENV', 'dev');
if (APP_ENV === 'dev') {
    error_reporting(E_ALL);
    ini_set('display_errors', '1');
} else {
    error_reporting(E_ALL);
    ini_set('display_errors', '0');
    ini_set('log_errors', '1');
}

// Base de datos (MySQL Laragon: root sin contraseña)
define('DB_HOST', '127.0.0.1');
define('DB_NAME', 'sistema_administrativo');
define('DB_USER', 'root');
define('DB_PASS', '');
define('DB_CHARSET', 'utf8mb4');
