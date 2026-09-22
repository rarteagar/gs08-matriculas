<script setup>
import { computed } from 'vue'
import { RouterLink, RouterView, useRouter } from 'vue-router'
import { cerrarSesion, token, usuarioGuardado } from './api'

const router = useRouter()
const usuario = usuarioGuardado()
const haySesion = computed(() => Boolean(token()))

const enlaces = [
  { nombre: 'panel', texto: 'Panel' },
  { nombre: 'estudiantes', texto: 'Estudiantes' },
  { nombre: 'matriculas', texto: 'Matrículas' },
]

function salir() {
  cerrarSesion()
  router.push({ name: 'login' })
}
</script>

<template>
  <div class="min-h-screen">
    <header v-if="haySesion" class="border-b border-slate-200 bg-white">
      <div class="mx-auto flex max-w-6xl flex-wrap items-center gap-4 px-5 py-3">
        <div class="mr-2">
          <p class="text-sm font-semibold text-slate-900">GS08 · Matrículas y Notas</p>
          <p class="text-xs text-slate-500">Sistema administrativo · Instituto Privado Horizonte</p>
        </div>
        <nav class="flex flex-1 flex-wrap gap-1">
          <RouterLink
            v-for="enlace in enlaces"
            :key="enlace.nombre"
            :to="{ name: enlace.nombre }"
            class="rounded-lg px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-100"
            active-class="bg-sky-50 text-sky-800"
          >
            {{ enlace.texto }}
          </RouterLink>
        </nav>
        <div class="flex items-center gap-3">
          <span class="text-xs text-slate-500">
            {{ usuario ? `${usuario.nombre_completo} (${usuario.rol})` : '' }}
          </span>
          <button class="boton-secundario" @click="salir">Cerrar sesión</button>
        </div>
      </div>
    </header>

    <main class="mx-auto max-w-6xl px-5 py-6">
      <RouterView />
    </main>
  </div>
</template>
