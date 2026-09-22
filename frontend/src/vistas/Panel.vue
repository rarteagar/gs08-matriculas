<script setup>
// Panel: los KPIs se cuentan desde las TRES listas (estudiantes, cursos y matrículas),
// que es el alcance final: no se usa /dashboard.
import { onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'
import { api } from '../api'

const estudiantes = ref([])
const cursos = ref([])
const matriculas = ref([])
const cargando = ref(true)
const error = ref('')

onMounted(async () => {
  try {
    const [alumnos, catalogo, inscripciones] = await Promise.all([
      api.estudiantes({ page_size: 100 }),
      api.cursos({ page_size: 100 }),
      api.matriculas({ page_size: 100 }),
    ])
    estudiantes.value = alumnos.estudiantes
    cursos.value = catalogo.cursos
    matriculas.value = inscripciones.matriculas
  } catch (fallo) {
    error.value = fallo.message
  } finally {
    cargando.value = false
  }
})
</script>

<template>
  <div>
    <h1 class="text-xl font-semibold text-slate-900">Panel</h1>
    <p class="text-sm text-slate-500">Los tres números salen de las listas de estudiantes, cursos y matrículas.</p>

    <p v-if="cargando" class="mt-6 text-sm text-slate-500">Cargando…</p>
    <p v-else-if="error" class="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{{ error }}</p>

    <template v-else>
      <div class="mt-5 grid gap-4 sm:grid-cols-3">
        <div class="tarjeta">
          <p class="text-xs font-semibold tracking-wide text-slate-500 uppercase">Estudiantes activos</p>
          <p class="mt-2 text-3xl font-semibold text-sky-700">{{ estudiantes.filter((e) => e.estado).length }}</p>
          <p class="mt-1 text-xs text-slate-500">de {{ estudiantes.length }} registrados</p>
        </div>
        <div class="tarjeta">
          <p class="text-xs font-semibold tracking-wide text-slate-500 uppercase">Cursos activos</p>
          <p class="mt-2 text-3xl font-semibold text-emerald-700">{{ cursos.filter((c) => c.estado).length }}</p>
          <p class="mt-1 text-xs text-slate-500">de {{ cursos.length }} registrados</p>
        </div>
        <div class="tarjeta">
          <p class="text-xs font-semibold tracking-wide text-slate-500 uppercase">Matrículas activas</p>
          <p class="mt-2 text-3xl font-semibold text-violet-700">
            {{ matriculas.filter((m) => m.estado === 'activa').length }}
          </p>
          <p class="mt-1 text-xs text-slate-500">de {{ matriculas.length }} registradas</p>
        </div>
      </div>

      <div class="tarjeta mt-6">
        <h2 class="text-sm font-semibold text-slate-900">Ir a</h2>
        <div class="mt-3 flex flex-wrap gap-3">
          <RouterLink class="boton-primario" :to="{ name: 'estudiantes' }">Estudiantes</RouterLink>
          <RouterLink class="boton-primario" :to="{ name: 'matriculas' }">Matrículas</RouterLink>
        </div>
      </div>
    </template>
  </div>
</template>
