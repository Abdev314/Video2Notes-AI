import { createRouter, createWebHistory } from 'vue-router'
import Home from '@/pages/Home.vue'
import AIStatus from '@/pages/AIStatusPanel.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home
    },
    {
      path: '/ai-status',
      name: 'ai-status',
      component: AIStatus
    },
  ]
})

export default router