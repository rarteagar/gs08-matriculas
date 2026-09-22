<script setup>
// Matrículas: lista completa + formulario de alta y edición, con los selectores de
// estudiante y curso cargados desde sus listas (alcance final).
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'

const lista = ref([])
const estudiantes = ref([])
const cursos = ref([])
const cargando = ref(false)
const error = ref('')
const aviso = ref('')

const VACIO = { id: null, estudiante_id: '', curso_id: '', periodo: '2026-02', fecha_matricula: '' }
const formulario = reactive({ ...VACIO })

async function cargar() {
  cargando.value = true
  error.value = ''
  try {
    const [inscripciones, alumnos, catalogo] = await Promise.all([
      api.matriculas({ page_size: 100 }),
      api.estudiantes({ page_size: 100 }),
      api.cursos({ page_size: 100 }),
    ])
    lista.value = inscripciones.matriculas
    estudiantes.value = alumnos.estudiantes
    cursos.value = catalogo.cursos
  } catch (fallo) {
    error.value = fallo.message
  } finally {
    cargando.value = false
  }
}

function limpiar() {
  Object.assign(formulario, VACIO)
}

function editar(matricula) {
  Object.assign(formulario, {
    id: matricula.id,
    estudiante_id: matricula.estudiante_id,
    curso_id: matricula.curso_id,
    periodo: matricula.periodo,
    fecha_matricula: matricula.fecha_matricula,
  })
  aviso.value = ''
  window.scrollTo({ top: 0 })
}

async function guardar() {
  error.value = ''
  aviso.value = ''
  const cuerpo = {
    estudiante_id: Number(formulario.estudiante_id),
    curso_id: Number(formulario.curso_id),
    periodo: formulario.periodo,
    fecha_matricula: formulario.fecha_matricula,
  }
  try {
    if (formulario.id) {
      const actualizada = await api.editarMatricula(formulario.id, cuerpo)
      aviso.value = `Matrícula ${actualizada.id} actualizada.`
    } else {
      const creada = await api.crearMatricula(cuerpo)
      aviso.value = `Matrícula ${creada.id} registrada: ${creada.estudiante} en ${creada.curso} (${creada.periodo}).`
    }
    limpiar()
    await cargar()
  } catch (fallo) {
    error.value = fallo.message
  }
}

onMounted(cargar)
</script>

<template>
  <div>
    <h1 class="text-xl font-semibold text-slate-900">Matrículas</h1>
    <p class="text-sm text-slate-500">Un estudiante en un curso, en un periodo. Los selectores salen de las listas de estudiantes y cursos.</p>

    <div class="tarjeta mt-4">
      <h2 class="text-sm font-semibold text-slate-900">{{ formulario.id ? `Editar matrícula ${formulario.id}` : 'Nueva matrícula' }}</h2>
      <form class="mt-4 grid gap-4 md:grid-cols-4" @submit.prevent="guardar">
        <div class="md:col-span-2">
          <label class="etiqueta" for="estudiante">Estudiante</label>
          <select id="estudiante" v-model="formulario.estudiante_id" class="campo" required>
            <option value="" disabled>Selecciona un estudiante</option>
            <option v-for="e in estudiantes" :key="e.id" :value="e.id">{{ e.codigo }} · {{ e.nombre_completo }}</option>
          </select>
        </div>
        <div class="md:col-span-2">
          <label class="etiqueta" for="curso">Curso</label>
          <select id="curso" v-model="formulario.curso_id" class="campo" required>
            <option value="" disabled>Selecciona un curso</option>
            <option v-for="c in cursos" :key="c.id" :value="c.id">{{ c.codigo }} · {{ c.nombre }} ({{ c.creditos }} cr.)</option>
          </select>
        </div>
        <div>
          <label class="etiqueta" for="periodo">Periodo (AAAA-MM)</label>
          <input id="periodo" v-model="formulario.periodo" class="campo" placeholder="2026-02" required />
        </div>
        <div>
          <label class="etiqueta" for="fecha">Fecha de matrícula</label>
          <input id="fecha" v-model="formulario.fecha_matricula" type="date" class="campo" required />
        </div>
        <div class="flex items-end gap-2 md:col-span-2">
          <button class="boton-primario" type="submit">{{ formulario.id ? 'Guardar cambios' : 'Matricular' }}</button>
          <button v-if="formulario.id" class="boton-secundario" type="button" @click="limpiar">Cancelar</button>
        </div>
      </form>
    </div>

    <p v-if="error" class="mt-4 rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{{ error }}</p>
    <p v-if="aviso" class="mt-4 rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-800">{{ aviso }}</p>

    <div class="tarjeta mt-4 overflow-x-auto">
      <table class="tabla">
        <thead>
          <tr>
            <th>#</th>
            <th>Estudiante</th>
            <th>Curso</th>
            <th>Periodo</th>
            <th>Fecha</th>
            <th>Estado</th>
            <th class="text-right">Acción</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="matricula in lista" :key="matricula.id">
            <td class="text-slate-500">{{ matricula.id }}</td>
            <td>
              <span class="font-medium text-slate-700">{{ matricula.estudiante }}</span>
              <span class="block font-mono text-xs text-slate-400">{{ matricula.codigo_estudiante }}</span>
            </td>
            <td>
              {{ matricula.curso }}
              <span class="block text-xs text-slate-400">{{ matricula.codigo_curso }} · {{ matricula.creditos }} cr.</span>
            </td>
            <td>{{ matricula.periodo }}</td>
            <td>{{ matricula.fecha_matricula }}</td>
            <td>
              <span :class="matricula.estado === 'activa' ? 'insignia-activa' : 'insignia-retirado'">
                {{ matricula.estado === 'activa' ? 'Activa' : 'Retirado' }}
              </span>
            </td>
            <td class="text-right">
              <button class="boton-secundario px-3! py-1.5! text-xs!" @click="editar(matricula)">Editar</button>
            </td>
          </tr>
          <tr v-if="!lista.length">
            <td colspan="7" class="py-6 text-center text-slate-500">
              {{ cargando ? 'Cargando…' : 'No hay matrículas registradas.' }}
            </td>
          </tr>
        </tbody>
      </table>
      <p class="mt-3 text-sm text-slate-600">{{ lista.length }} matrícula(s)</p>
    </div>
  </div>
</template>
