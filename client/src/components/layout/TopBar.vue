<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/store/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const query = ref(route.query.q || '')
const profileOpen = ref(false)

function submitSearch() {
  if (!query.value.trim()) return
  router.push({ path: '/search', query: { q: query.value.trim() } })
}

const initial = () => (userStore.displayName || 'L').charAt(0).toUpperCase()
function logout() {
  userStore.logout()
  router.replace('/auth')
}
</script>

<template>
  <header class="topbar">
    <div class="topbar__nav">
      <button class="icon-btn" aria-label="Go back" @click="router.back()">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m15 18-6-6 6-6"/></svg>
      </button>
      <button class="icon-btn" aria-label="Go forward" @click="router.forward()">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 18 6-6-6-6"/></svg>
      </button>
    </div>

    <form class="topbar__search" @submit.prevent="submitSearch">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
      <input
        v-model="query"
        type="search"
        placeholder="What do you want to hear?"
        aria-label="Search tracks, artists, albums"
      />
    </form>

    <div class="profile-wrap">
    <button class="topbar__user" aria-haspopup="dialog" :aria-expanded="profileOpen" @click="profileOpen = !profileOpen">
      <span class="topbar__avatar" aria-hidden="true">{{ initial() }}</span>
      <span class="topbar__name">{{ userStore.displayName }}</span>
    </button>
    <section v-if="profileOpen" class="profile-popover" role="dialog" aria-label="Profile information">
      <span class="eyebrow">Your profile</span>
      <strong>{{ userStore.displayName }}</strong>
      <span>@{{ userStore.loginName }}</span>
      <span>{{ userStore.email }}</span>
      <small v-if="userStore.createdAt">Member since {{ new Date(userStore.createdAt).toLocaleDateString() }}</small>
      <button class="profile-logout" @click="logout">Log out</button>
    </section>
    </div>
  </header>
</template>

<style scoped>
.topbar {
  height: var(--topbar-h);
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 28px;
  background: linear-gradient(var(--bg-raised), var(--bg-base));
  border-bottom: 1px solid var(--line-soft);
  position: sticky;
  top: 0;
  z-index: 5;
}

.topbar__nav { display: flex; gap: 4px; }

.topbar__search {
  flex: 1;
  max-width: 420px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: var(--radius-pill);
  background: var(--bg-raised);
  border: 1px solid var(--line);
  color: var(--text-tertiary);
}

.topbar__search input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-size: 13.5px;
}
.topbar__search input::placeholder { color: var(--text-tertiary); }

.profile-wrap { position: relative; margin-left: auto; }
.topbar__user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 4px 12px 4px 4px;
  border-radius: var(--radius-pill);
  background: var(--bg-raised);
  border: 1px solid var(--line-soft);
}

.profile-popover { position: absolute; right: 0; top: calc(100% + 10px); z-index: 10; width: 245px; display: grid; gap: 7px; padding: 18px; border: 1px solid var(--line); border-radius: var(--radius-md); background: var(--bg-raised); box-shadow: var(--shadow-panel); color: var(--text-secondary); }
.profile-popover strong { color: var(--text-primary); font-size: 16px; }
.profile-popover small { margin-top: 4px; color: var(--text-tertiary); }
.profile-logout { margin-top: 8px; padding: 8px 10px; border-radius: var(--radius-sm); background: var(--bg-hover); color: var(--text-primary); text-align: left; font-weight: 700; }

.topbar__avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--accent-wash);
  color: var(--accent);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 12px;
}

.topbar__name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}
</style>
