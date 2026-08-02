<script setup>
import { usePlayerStore } from '@/store/player'

const props = defineProps({
  message: { type: Object, required: true }
})

const playerStore = usePlayerStore()

function playRef(track) {
  playerStore.playTrack(track, 'chat')
}
</script>

<template>
  <div class="chat-message" :class="`chat-message--${message.role}`">
    <div class="chat-message__bubble" :class="{ 'chat-message__bubble--error': message.isError }">
      <span v-if="message.pending" class="chat-message__typing" aria-label="Assistant is typing">
        <span></span><span></span><span></span>
      </span>
      <p v-else class="chat-message__text">{{ message.content }}</p>

      <div v-if="message.trackRefs?.length" class="chat-message__refs">
        <button
          v-for="track in message.trackRefs"
          :key="track.id"
          class="chat-message__ref"
          @click="playRef(track)"
        >
          <span class="chat-message__ref-art" aria-hidden="true">
            <img v-if="track.coverUrl" :src="track.coverUrl" :alt="track.title" />
          </span>
          <span class="chat-message__ref-meta">
            <span class="chat-message__ref-title">{{ track.title }}</span>
            <span class="chat-message__ref-artist">{{ track.artistName }}</span>
          </span>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M7 4v16l14-8z"/></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chat-message { display: flex; }
.chat-message--user { justify-content: flex-end; }
.chat-message--assistant { justify-content: flex-start; }

.chat-message__bubble {
  max-width: 84%;
  padding: 10px 13px;
  border-radius: var(--radius-md);
  font-size: 13.5px;
  line-height: 1.5;
}
.chat-message--user .chat-message__bubble { background: var(--accent-wash); color: var(--text-primary); border-bottom-right-radius: 4px; }
.chat-message--assistant .chat-message__bubble { background: var(--bg-raised); color: var(--text-primary); border-bottom-left-radius: 4px; }
.chat-message__bubble--error { background: rgba(224, 90, 90, 0.12); color: #f2b8b8; }

.chat-message__text { margin: 0; white-space: pre-wrap; }

.chat-message__typing { display: inline-flex; gap: 4px; padding: 4px 2px; }
.chat-message__typing span {
  width: 6px; height: 6px; border-radius: 50%;
  background: var(--text-tertiary);
  animation: chat-typing 1.1s infinite ease-in-out;
}
.chat-message__typing span:nth-child(2) { animation-delay: 0.15s; }
.chat-message__typing span:nth-child(3) { animation-delay: 0.3s; }
@keyframes chat-typing {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.5; }
  30% { transform: translateY(-3px); opacity: 1; }
}

.chat-message__refs { margin-top: 8px; display: flex; flex-direction: column; gap: 6px; }
.chat-message__ref {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px;
  border-radius: var(--radius-sm);
  background: var(--bg-panel);
  border: 1px solid var(--line-soft);
  text-align: left;
  color: var(--text-primary);
  transition: border-color 0.15s ease;
}
.chat-message__ref:hover { border-color: var(--accent-dim); }
.chat-message__ref-art { width: 30px; height: 30px; border-radius: 4px; overflow: hidden; background: linear-gradient(135deg, var(--accent-wash), var(--accent-2-wash)); flex-shrink: 0; }
.chat-message__ref-art img { width: 100%; height: 100%; object-fit: cover; }
.chat-message__ref-meta { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.chat-message__ref-title { font-size: 12.5px; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.chat-message__ref-artist { font-size: 11.5px; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
</style>
