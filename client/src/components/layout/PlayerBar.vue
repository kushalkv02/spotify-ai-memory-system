<script setup>
import { computed } from 'vue'
import { usePlayerStore } from '@/store/player'
import { useUserStore } from '@/store/user'

const playerStore = usePlayerStore()
const userStore = useUserStore()

const formatTime = (seconds = 0) => {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

const liked = computed(() =>
  playerStore.currentTrack ? userStore.isLiked(playerStore.currentTrack.id) : false
)

function onSeek(e) {
  const track = playerStore.currentTrack
  if (!track) return
  const pct = Number(e.target.value)
  playerStore.seekTo((pct / 100) * track.durationSeconds)
}

function onVolume(e) {
  playerStore.setVolume(Number(e.target.value) / 100)
}
</script>

<template>
  <footer class="playerbar" v-if="playerStore.currentTrack">
    <div class="playerbar__now">
      <img
        v-if="playerStore.currentTrack.coverUrl"
        :src="playerStore.currentTrack.coverUrl"
        :alt="playerStore.currentTrack.title"
        class="playerbar__cover"
      />
      <div v-else class="playerbar__cover playerbar__cover--placeholder" aria-hidden="true" />
      <div class="playerbar__meta">
        <p class="playerbar__title">{{ playerStore.currentTrack.title }}</p>
        <p class="playerbar__artist">{{ playerStore.currentTrack.artistName }}</p>
      </div>
      <button
        class="icon-btn playerbar__like"
        :class="{ 'playerbar__like--active': liked }"
        :aria-pressed="liked"
        aria-label="Like track"
        @click="userStore.toggleLike(playerStore.currentTrack)"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" :fill="liked ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="1.8">
          <path d="M12 21s-7.5-4.6-10-9.2C.5 8 2 4 6 4c2 0 3.6 1.2 6 4 2.4-2.8 4-4 6-4 4 0 5.5 4 4 7.8C19.5 16.4 12 21 12 21z"/>
        </svg>
      </button>
    </div>

    <div class="playerbar__center">
      <div class="playerbar__controls">
        <button class="icon-btn" :class="{ 'is-active': playerStore.shuffle }" aria-label="Shuffle" @click="playerStore.toggleShuffle">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M4 6h4l7 12h5M4 18h4l3-5"/><path d="m17 4 3 2-3 2M17 18l3 2-3 2"/></svg>
        </button>
        <button class="icon-btn" aria-label="Previous" :disabled="!playerStore.hasPrevious" @click="playerStore.previous">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M6 6h2v12H6zM20 6 9 12l11 6z"/></svg>
        </button>
        <button class="playerbar__play" :aria-label="playerStore.isPlaying ? 'Pause' : 'Play'" @click="playerStore.togglePlay">
          <svg v-if="playerStore.isPlaying" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><rect x="5" y="4" width="5" height="16" rx="1"/><rect x="14" y="4" width="5" height="16" rx="1"/></svg>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M7 4v16l14-8z"/></svg>
        </button>
        <button class="icon-btn" aria-label="Next" :disabled="!playerStore.hasNext" @click="playerStore.next()">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M16 6h2v12h-2zM4 6l11 6-11 6z"/></svg>
        </button>
        <button class="icon-btn" :class="{ 'is-active': playerStore.repeatMode !== 'off' }" aria-label="Repeat" @click="playerStore.cycleRepeat">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path d="M17 2l4 4-4 4"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><path d="M7 22l-4-4 4-4"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg>
          <span v-if="playerStore.repeatMode === 'one'" class="playerbar__repeat-badge">1</span>
        </button>
      </div>
      <div class="playerbar__scrubber">
        <span class="playerbar__time">{{ formatTime(playerStore.progressSeconds) }}</span>
        <input
          type="range"
          min="0"
          max="100"
          :value="playerStore.progressPct"
          @input="onSeek"
          class="playerbar__range"
          aria-label="Seek"
        />
        <span class="playerbar__time">{{ formatTime(playerStore.currentTrack.durationSeconds) }}</span>
      </div>
    </div>

    <div class="playerbar__volume">
      <button class="icon-btn" aria-label="Mute" @click="playerStore.toggleMute">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
          <path d="M5 9v6h4l5 4V5L9 9H5z"/>
          <path v-if="!playerStore.isMuted" d="M17.5 8.5a5 5 0 0 1 0 7"/>
        </svg>
      </button>
      <input
        type="range"
        min="0"
        max="100"
        :value="playerStore.isMuted ? 0 : playerStore.volume * 100"
        @input="onVolume"
        class="playerbar__range playerbar__range--small"
        aria-label="Volume"
      />
    </div>
  </footer>
</template>

<style scoped>
.playerbar {
  position: fixed;
  left: var(--sidebar-w);
  right: 0;
  bottom: 0;
  height: var(--playerbar-h);
  background: var(--bg-base);
  border-top: 1px solid var(--line-soft);
  display: grid;
  grid-template-columns: 1fr 2fr 1fr;
  align-items: center;
  padding: 0 20px;
  gap: 16px;
  z-index: 10;
}

.playerbar__now { display: flex; align-items: center; gap: 12px; min-width: 0; }
.playerbar__cover { width: 52px; height: 52px; border-radius: var(--radius-sm); object-fit: cover; }
.playerbar__cover--placeholder { background: linear-gradient(135deg, var(--accent-wash), var(--accent-2-wash)); }
.playerbar__meta { min-width: 0; }
.playerbar__title { margin: 0; font-size: 13.5px; font-weight: 600; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.playerbar__artist { margin: 2px 0 0; font-size: 12px; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.playerbar__like--active { color: var(--accent); }

.playerbar__center { display: flex; flex-direction: column; align-items: center; gap: 6px; min-width: 0; }
.playerbar__controls { display: flex; align-items: center; gap: 14px; }
.icon-btn.is-active { color: var(--accent); }
.icon-btn:disabled { opacity: 0.35; cursor: not-allowed; }

.playerbar__play {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--text-primary);
  color: var(--bg-void);
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.15s ease;
}
.playerbar__play:hover { transform: scale(1.05); }

.playerbar__repeat-badge {
  position: relative;
  top: -10px;
  left: -6px;
  font-size: 9px;
  font-weight: 800;
  color: var(--accent);
}

.playerbar__scrubber { display: flex; align-items: center; gap: 8px; width: 100%; max-width: 520px; }
.playerbar__time { font-size: 11px; color: var(--text-tertiary); min-width: 32px; text-align: center; }

.playerbar__range {
  flex: 1;
  appearance: none;
  height: 4px;
  border-radius: var(--radius-pill);
  background: var(--line);
  accent-color: var(--accent);
  cursor: pointer;
}
.playerbar__range--small { max-width: 100px; }

.playerbar__volume { display: flex; align-items: center; gap: 8px; justify-self: end; }

@media (max-width: 860px) {
  .playerbar { left: 0; grid-template-columns: 1fr; }
  .playerbar__volume { display: none; }
}
</style>
