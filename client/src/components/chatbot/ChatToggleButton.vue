<script setup>
import { useChatStore } from '@/store/chat'

const chatStore = useChatStore()
</script>

<template>
  <button
    v-if="!chatStore.isOpen"
    class="chat-toggle"
    aria-label="Open memory assistant"
    @click="chatStore.open()"
  >
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
      <path d="M21 12a8 8 0 1 1-3.2-6.4" />
      <path d="M21 4v5h-5" />
    </svg>
    <span v-if="chatStore.unreadCount" class="chat-toggle__badge">{{ chatStore.unreadCount }}</span>
  </button>
</template>

<style scoped>
.chat-toggle {
  position: fixed;
  right: 28px;
  bottom: calc(var(--playerbar-h) + 24px);
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: var(--accent);
  color: #1a1305;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: var(--shadow-panel);
  z-index: 20;
  transition: transform 0.15s ease, background 0.15s ease;
}
.chat-toggle:hover { transform: translateY(-2px) scale(1.03); background: var(--accent-strong); }

.chat-toggle__badge {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 18px;
  height: 18px;
  padding: 0 4px;
  border-radius: var(--radius-pill);
  background: var(--accent-2);
  color: #fff;
  font-size: 10.5px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 860px) {
  .chat-toggle { bottom: calc(var(--playerbar-h) + 16px); right: 16px; }
}
</style>
