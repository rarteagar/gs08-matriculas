/* ============================================================
   Instituto Privado Horizonte - Scripts del panel
   ============================================================ */
document.addEventListener('DOMContentLoaded', function () {
    'use strict';

    // ---- Sidebar responsive ----
    var sidebar = document.getElementById('sidebar');
    var backdrop = document.getElementById('sidebarBackdrop');
    var btnToggle = document.getElementById('btnToggleSidebar');

    function openSidebar() {
        if (!sidebar) return;
        sidebar.classList.add('open');
        if (backdrop) backdrop.classList.add('show');
    }
    function closeSidebar() {
        if (!sidebar) return;
        sidebar.classList.remove('open');
        if (backdrop) backdrop.classList.remove('show');
    }

    if (btnToggle) btnToggle.addEventListener('click', openSidebar);
    if (backdrop) backdrop.addEventListener('click', closeSidebar);

    // ---- Confirmación de eliminación ----
    // Todo botón con data-confirm pide confirmación antes de enviar su formulario.
    document.querySelectorAll('form[data-confirm]').forEach(function (form) {
        form.addEventListener('submit', function (ev) {
            var msg = form.getAttribute('data-confirm');
            if (!window.confirm(msg)) {
                ev.preventDefault();
            }
        });
    });
});
