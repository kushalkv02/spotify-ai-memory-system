import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/auth', name: 'auth', component: () => import('@/views/AuthView.vue'), meta: { public: true } },
  {
    path: '/',
    name: 'home',
    component: () => import('@/views/HomeView.vue')
  },
  {
    path: '/search',
    name: 'search',
    component: () => import('@/views/SearchView.vue')
  },
  {
    path: '/library',
    name: 'library',
    component: () => import('@/views/LibraryView.vue')
  },
  {
    path: '/playlist/:id',
    name: 'playlist',
    component: () => import('@/views/PlaylistView.vue'),
    props: true
  },
  {
    path: '/album/:id',
    name: 'album',
    component: () => import('@/views/AlbumView.vue'),
    props: true
  },
  {
    path: '/artist/:id',
    name: 'artist',
    component: () => import('@/views/ArtistView.vue'),
    props: true
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

router.beforeEach((to) => {
  if (!to.meta.public && !localStorage.getItem('reverie:token')) return { name: 'auth' }
  if (to.name === 'auth' && localStorage.getItem('reverie:token')) return { name: 'home' }
})

export default router
