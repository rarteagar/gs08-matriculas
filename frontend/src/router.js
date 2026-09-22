import { createRouter, createWebHistory } from 'vue-router'
import { token } from './api'
import Login from './vistas/Login.vue'
import Panel from './vistas/Panel.vue'
import Estudiantes from './vistas/Estudiantes.vue'
import Matriculas from './vistas/Matriculas.vue'

const rutas = [
  { path: '/login', name: 'login', component: Login, meta: { publica: true } },
  { path: '/', name: 'panel', component: Panel },
  { path: '/estudiantes', name: 'estudiantes', component: Estudiantes },
  { path: '/matriculas', name: 'matriculas', component: Matriculas },
  { path: '/:ruta(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes: rutas,
})

// Sin token no se entra a ninguna pantalla (y con token no se vuelve al login).
router.beforeEach((destino) => {
  const haySesion = Boolean(token())
  if (!haySesion && !destino.meta.publica) return { name: 'login' }
  if (haySesion && destino.name === 'login') return { name: 'panel' }
  return true
})

export default router
