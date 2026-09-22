<script setup>
// Estudiantes: lista completa + formulario de alta y edición (alcance final).
import { onMounted, reactive, ref } from 'vue'
import { api } from '../api'

const VACIO = {
  id: null,
  codigo: '',
  dni: '',
  nombres: '',
  apellidos: '',
  email: '',
  telefono: '',
  fecha_nacimiento: '',
  direccion: '',
  estado: true,
}

const lista = ref([])
const cargando = ref(false)
const error = ref('')
const aviso = ref('')
const formulario = reactive({ ...VACIO })

async function cargar() {
  cargando.value = true
  error.value = ''
  try {
    const datos = await api.estudiantes({ page_size: 100 })
    lista.value = datos.estudiantes
  } catch (fallo) {
    error.value = fallo.message
  } finally {
    cargando.value = false
  }
}

function limpiar() {
  Object.assign(formulario, VACIO)
}

function editar(estudiante) {
  Object.assign(formulario, {
    id: estudiante.id,
    codigo: estudiante.codigo,
    dni: estudiante.dni,
    nombres: estudiante.nombres,
    apellidos: estudiante.apellidos,
    email: estudiante.email || '',
    telefono: estudiante.telefono || '',
    fecha_nacimiento: estudiante.fecha_nacimiento || '',
    direccion: estudiante.direccion || '',
    estado: estudiante.estado,
  })
  aviso.value = ''
  window.scrollTo({ top: 0 })
}

function cuerpo() {
  return {
    codigo: formulario.codigo.trim(),
    dni: formulario.dni.trim(),
    nombres: formulario.nombres.trim(),
    apellidos: formulario.apellidos.trim(),
    email: formulario.email.trim() || null,
    telefono: formulario.telefono.trim() || null,
    fecha_nacimiento: formulario.fecha_nacimiento || null,
    direccion: formulario.direccion.trim() || null,
    estado: formulario.estado,
  }
}

async function guardar() {
  error.value = ''
  aviso.value = ''
  try {
    if (formulario.id) {
      await api.editarEstudiante(formulario.id, cuerpo())
      aviso.value = `Estudiante ${formulario.codigo} actualizado.`
    } else {
      await api.crearEstudiante(cuerpo())
      aviso.value = `Estudiante ${formulario.codigo} registrado.`
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
    <h1 class="text-xl font-semibold text-slate-900">Estudiantes</h1>
    <p class="text-sm text-slate-500">Lista del sistema y formulario de alta y edición.</p>

    <div class="tarjeta mt-4">
      <h2 class="text-sm font-semibold text-slate-900">
        {{ formulario.id ? `Editar ${formulario.codigo}` : 'Nuevo estudiante' }}
      </h2>
      <form class="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3" @submit.prevent="guardar">
        <div>
          <label class="etiqueta" for="codigo">Código</label>
          <input id="codigo" v-model="formulario.codigo" class="campo" required maxlength="20" />
        </div>
        <div>
          <label class="etiqueta" for="dni">DNI (8 dígitos)</label>
          <input id="dni" v-model="formulario.dni" class="campo" required maxlength="8" />
        </div>
        <div>
          <label class="etiqueta" for="nombres">Nombres</label>
          <input id="nombres" v-model="formulario.nombres" class="campo" required />
        </div>
        <div>
          <label class="etiqueta" for="apellidos">Apellidos</label>
          <input id="apellidos" v-model="formulario.apellidos" class="campo" required />
        </div>
        <div>
          <label class="etiqueta" for="email">Email (opcional)</label>
          <input id="email" v-model="formulario.email" class="campo" />
        </div>
        <div>
          <label class="etiqueta" for="telefono">Teléfono (opcional)</label>
          <input id="telefono" v-model="formulario.telefono" class="campo" />
        </div>
        <div>
          <label class="etiqueta" for="nacimiento">Fecha de nacimiento (opcional)</label>
          <input id="nacimiento" v-model="formulario.fecha_nacimiento" type="date" class="campo" />
        </div>
        <div>
          <label class="etiqueta" for="direccion">Dirección (opcional)</label>
          <input id="direccion" v-model="formulario.direccion" class="campo" />
        </div>
        <div class="flex items-end gap-4">
          <label class="flex items-center gap-2 text-sm text-slate-700">
            <input v-model="formulario.estado" type="checkbox" class="h-4 w-4" />
            Activo
          </label>
        </div>
        <div class="flex items-end gap-2 sm:col-span-2 lg:col-span-3">
          <button class="boton-primario" type="submit">{{ formulario.id ? 'Guardar cambios' : 'Registrar' }}</button>
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
            <th>Código</th>
            <th>DNI</th>
            <th>Apellidos y nombres</th>
            <th>Email</th>
            <th>Estado</th>
            <th class="text-right">Acción</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="estudiante in lista" :key="estudiante.id">
            <td class="font-mono text-xs">{{ estudiante.codigo }}</td>
            <td class="font-mono text-xs">{{ estudiante.dni }}</td>
            <td class="font-medium text-slate-700">{{ estudiante.nombre_completo }}</td>
            <td class="text-slate-500">{{ estudiante.email || '—' }}</td>
            <td>
              <span :class="estudiante.estado ? 'insignia-activa' : 'insignia-inactivo'">
                {{ estudiante.estado ? 'Activo' : 'Inactivo' }}
              </span>
            </td>
            <td class="text-right">
              <button class="boton-secundario px-3! py-1.5! text-xs!" @click="editar(estudiante)">Editar</button>
            </td>
          </tr>
          <tr v-if="!lista.length">
            <td colspan="6" class="py-6 text-center text-slate-500">
              {{ cargando ? 'Cargando…' : 'No hay estudiantes registrados.' }}
            </td>
          </tr>
        </tbody>
      </table>
      <p class="mt-3 text-sm text-slate-600">{{ lista.length }} estudiante(s)</p>
    </div>
  </div>
</template>
