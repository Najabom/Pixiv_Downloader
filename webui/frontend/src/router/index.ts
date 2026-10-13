import { createRouter, createWebHistory } from 'vue-router'
import DashboardView from '../views/DashboardView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/', name: 'dashboard', component: DashboardView },
    { path: '/works', name: 'works', component: () => import('../views/WorksView.vue') },
    {
      path: '/works/:name',
      name: 'work-detail',
      component: () => import('../views/WorkDetailView.vue'),
    },
    { path: '/gallery', name: 'gallery', component: () => import('../views/GalleryView.vue') },
    { path: '/logs', name: 'logs', component: () => import('../views/LogsView.vue') },
    { path: '/settings', name: 'settings', component: () => import('../views/SettingsView.vue') },
  ],
})

export default router
