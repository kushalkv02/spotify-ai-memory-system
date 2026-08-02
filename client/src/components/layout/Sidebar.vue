<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '@/store/user'

const route = useRoute()
const userStore = useUserStore()

const navLinks = [
  { to: '/', label: 'Home', icon: 'home' },
  { to: '/search', label: 'Search', icon: 'search' },
  { to: '/library', label: 'Your library', icon: 'library' }
]

const isActive = (path) => computed(() => route.path === path).value
</script>

<template>
  <aside class="sidebar">
    <div class="sidebar__brand">
      <span class="sidebar__mark" aria-hidden="true">
        <svg width="20" height="20" viewBox="0 0 32 32">
          <path d="M9 20c4-2 10-2.5 14 0" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" fill="none"/>
          <path d="M9 16c5-2.5 11-2.5 15 0.5" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" fill="none" opacity="0.75"/>
          <path d="M9 12c4-2 9-2 12 1" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" fill="none" opacity="0.5"/>
        </svg>
      </span>
      <span class="sidebar__name">Reverie</span>
    </div>

    <nav class="sidebar__nav">
      <router-link
        v-for="link in navLinks"
        :key="link.to"
        :to="link.to"
        class="sidebar__link"
        :class="{ 'sidebar__link--active': isActive(link.to) }"
      >
        <span class="sidebar__icon" v-html="icons[link.icon]" />
        {{ link.label }}
      </router-link>
    </nav>

    <div class="sidebar__divider" />

    <div class="sidebar__section">
      <span class="eyebrow">Playlists</span>
      <ul class="sidebar__playlists">
        <li v-for="playlist in userStore.library.playlists" :key="playlist.id">
          <router-link :to="`/playlist/${playlist.id}`" class="sidebar__playlist-link">
            {{ playlist.name }}
          </router-link>
        </li>
        <li v-if="!userStore.library.playlists.length" class="sidebar__empty">
          Playlists you save will show up here.
        </li>
      </ul>
    </div>
  </aside>
</template>

<script>
const icons = {
  home: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 11.5 12 4l8 7.5"/><path d="M6 10v9h5v-5h2v5h5v-9"/></svg>',
  search: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
  library: '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><rect x="4" y="4" width="4" height="16" rx="1"/><rect x="10" y="7" width="4" height="13" rx="1"/><rect x="16" y="10" width="4" height="10" rx="1"/></svg>'
}
export default { data: () => ({ icons }) }
</script>

<style scoped>
.sidebar {
  background: var(--bg-base);
  border-right: 1px solid var(--line-soft);
  padding: 20px 12px;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow-y: auto;
}

.sidebar__brand {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 12px 20px;
  color: var(--accent);
}

.sidebar__name {
  font-family: var(--font-display);
  font-size: 19px;
  font-weight: 700;
  color: var(--text-primary);
}

.sidebar__nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sidebar__link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 14px;
  transition: background 0.15s ease, color 0.15s ease;
}

.sidebar__link:hover { color: var(--text-primary); background: var(--bg-hover); }
.sidebar__link--active { color: var(--text-primary); background: var(--bg-raised); }
.sidebar__icon { display: inline-flex; }

.sidebar__divider {
  height: 1px;
  background: var(--line-soft);
  margin: 16px 8px;
}

.sidebar__section {
  padding: 0 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-height: 0;
  overflow-y: auto;
}

.sidebar__playlists {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.sidebar__playlist-link {
  display: block;
  padding: 7px 4px;
  color: var(--text-secondary);
  font-size: 13.5px;
  border-radius: var(--radius-sm);
}
.sidebar__playlist-link:hover { color: var(--text-primary); }

.sidebar__empty {
  color: var(--text-tertiary);
  font-size: 12.5px;
  line-height: 1.5;
  padding: 4px;
}

@media (max-width: 860px) {
  .sidebar { display: none; }
}
</style>
