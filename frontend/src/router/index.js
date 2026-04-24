import { createRouter, createWebHistory } from 'vue-router'
import AboutView from '../views/AboutView.vue'
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
  {
    path: '/about',
    name: 'About',
    component: AboutView,
  },
]

export default createRouter({
  history: createWebHistory(),
  routes,
})
