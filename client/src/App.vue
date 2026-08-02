<script setup>
import { onMounted } from 'vue'
import Sidebar from '@/components/layout/Sidebar.vue'
import TopBar from '@/components/layout/TopBar.vue'
import PlayerBar from '@/components/layout/PlayerBar.vue'
import ChatWidget from '@/components/chatbot/ChatWidget.vue'
import ChatToggleButton from '@/components/chatbot/ChatToggleButton.vue'
import { useUserStore } from '@/store/user'
import { usePlayerStore } from '@/store/player'

const userStore = useUserStore()
const playerStore = usePlayerStore()

onMounted(() => {
  if (userStore.isAuthenticated) {
    userStore.refreshProfile().catch(() => userStore.logout())
    userStore.fetchLibrary()
  }
})
</script>

<template>
  <router-view v-if="$route.meta.public" />
  <div v-else class="shell">
    <Sidebar />

    <div class="shell__main">
      <TopBar />
      <main class="shell__content">
        <router-view />
      </main>
    </div>

    <PlayerBar v-if="playerStore.currentTrack" />

    <ChatToggleButton />
    <ChatWidget />
  </div>
</template>

<style scoped>
.shell {
  display: grid;
  grid-template-columns: var(--sidebar-w) 1fr;
  height: 100vh;
  background: var(--bg-void);
}

.shell__main {
  display: flex;
  flex-direction: column;
  min-width: 0;
  height: 100vh;
}

.shell__content {
  flex: 1;
  overflow-y: auto;
  padding: 24px 32px calc(var(--playerbar-h) + 32px);
}

@media (max-width: 860px) {
  .shell {
    grid-template-columns: 1fr;
  }
}
</style>
