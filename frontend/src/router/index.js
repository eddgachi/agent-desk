import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import SimulationView from '../views/SimulationView.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
  },
  {
    path: '/simulation',
    name: 'Simulation',
    component: SimulationView,
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
