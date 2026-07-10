import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import AppLayout from '../layout/AppLayout.vue'
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'
import ProjectsView from '../views/ProjectsView.vue'
import WorkspaceView from '../views/WorkspaceView.vue'
import ImportView from '../views/ImportView.vue'
import RunsView from '../views/RunsView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: LoginView, meta: { public: true } },
    {
      path: '/',
      component: AppLayout,
      children: [
        { path: '', name: 'dashboard', component: DashboardView },
        { path: 'projects', name: 'projects', component: ProjectsView },
        { path: 'workspace', name: 'workspace', component: WorkspaceView },
        { path: 'import', name: 'import', component: ImportView },
        { path: 'runs', name: 'runs', component: RunsView },
      ],
    },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (!to.meta.public && !auth.isAuthenticated) return '/login'
  if (to.path === '/login' && auth.isAuthenticated) return '/'
})

export default router
