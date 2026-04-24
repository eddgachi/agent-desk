import { createRouter, createWebHistory } from 'vue-router'
import OfficeView from '../views/OfficeView.vue'

const routes = [
  {
    path: '/',
    redirect: '/office',
  },
  {
    path: '/office',
    name: 'Office',
    component: OfficeView,
  },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
