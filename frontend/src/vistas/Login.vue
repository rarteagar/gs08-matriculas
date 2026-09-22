<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { api, guardarSesion } from '../api'

const router = useRouter()
const usuario = ref('')
const password = ref('')
const error = ref('')
const cargando = ref(false)

async function entrar() {
  error.value = ''
  cargando.value = true
  try {
    const datos = await api.login(usuario.value, password.value)
    guardarSesion(datos)
    router.push({ name: 'panel' })
  } catch (fallo) {
    error.value = fallo.message
  } finally {
    cargando.value = false
  }
}
</script>

<template>
  <div class="mx-auto mt-10 max-w-md">
    <div class="tarjeta">
      <h1 class="text-lg font-semibold text-slate-900">Iniciar sesión</h1>
      <p class="mt-1 text-sm text-slate-500">Entra con tu nombre de usuario o tu email institucional.</p>

      <form class="mt-5 space-y-4" @submit.prevent="entrar">
        <div>
          <label class="etiqueta" for="usuario">Usuario o email</label>
          <input id="usuario" v-model="usuario" class="campo" autocomplete="username" required />
        </div>
        <div>
          <label class="etiqueta" for="password">Contraseña</label>
          <input id="password" v-model="password" type="password" class="campo" autocomplete="current-password" required />
        </div>

        <p v-if="error" class="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-700">{{ error }}</p>

        <button class="boton-primario w-full" type="submit" :disabled="cargando">
          {{ cargando ? 'Entrando…' : 'Entrar' }}
        </button>
      </form>
    </div>
  </div>
</template>
