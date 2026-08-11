<script setup>
import { computed } from 'vue'
import { usePlayerStore } from '@/store/player'
import { useUserStore } from '@/store/user'

const props = defineProps({
  track: { type: Object, required: true },
  index: { type: Number, default: null },
  queue: { type: Array, default: null },
  source: { type: String, default: 'row' },
  showAlbum: { type: Boolean, default: true }
})

const playerStore = usePlayerStore()
const userStore = useUserStore()

const isCurrent = computed(() => playerStore.currentTrack?.id === props.track.id)
const liked = computed(() => userStore.isLiked(props.track.id))

const formatTime = (seconds = 0) => {
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${String(s).padStart(2, '0')}`
}

function handlePlay() {
  if (isCurrent.value) {
    playerStore.togglePlay()
    return
  }
  const queue = props.queue?.length ? props.queue : [props.track]
  const startIndex = queue.findIndex((t) => t.id === props.track.id)
  playerStore.playQueue(queue, startIndex === -1 ? 0 : startIndex, props.source)
}
</script>

<template>
  <div class="track-row" :class="{ 'track-row--active': isCurrent }" @dblclick="handlePlay">
    <button class="track-row__play-index" @click="handlePlay" :aria-label="isCurrent && playerStore.isPlaying ? 'Pause' : 'Play'">
      <span v-if="index !== null && !(isCurrent && playerStore.isPlaying)" class="track-row__index">{{ index + 1 }}</span>
      <svg v-else-if="isCurrent && playerStore.isPlaying" width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><rect x="5" y="4" width="5" height="16" rx="1"/><rect x="14" y="4" width="5" height="16" rx="1"/></svg>
      <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M7 4v16l14-8z"/></svg>
    </button>

    <div class="track-row__main">
      <img v-if="track.coverUrl" :src="track.coverUrl" :alt="track.title" class="track-row__cover" />
      <div v-else class="track-row__cover track-row__cover--placeholder" aria-hidden="true" />
      <div class="track-row__meta">
        <p class="track-row__title">{{ track.title }}</p>
        <p class="track-row__artist">{{ track.artistName }}<span v-if="track.genre"> · {{ track.genre }}</span></p>
      </div>
    </div>

    <span v-if="showAlbum" class="track-row__album">{{ track.albumName }}</span>

    <button
      class="icon-btn track-row__like"
      :class="{ 'track-row__like--active': liked }"
      :aria-pressed="liked"
      :aria-label="liked ? `Unlike ${track.title}` : `Like ${track.title}`"
      @click="userStore.toggleLike(track)"
    >
      <svg width="15" height="15" viewBox="0 0 24 24" :fill="liked ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="1.8">
        <path d="M12 21s-7.5-4.6-10-9.2C.5 8 2 4 6 4c2 0 3.6 1.2 6 4 2.4-2.8 4-4 6-4 4 0 5.5 4 4 7.8C19.5 16.4 12 21 12 21z"/>
      </svg>
    </button>

    <span class="track-row__duration">{{ formatTime(track.durationSeconds) }}</span>
  </div>
</template>

<style scoped>
.track-row {
  display: grid;
  grid-template-columns: 32px 1fr 200px 32px 48px;
  align-items: center;
  gap: 14px;
  padding: 8px 12px;
  border-radius: var(--radius-sm);
}
.track-row:hover { background: var(--bg-hover); }
.track-row--active .track-row__title { color: var(--accent); }

.track-row__play-index {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-primary);
}
.track-row__index { color: var(--text-tertiary); font-size: 13px; }
.track-row__play-index:hover .track-row__index { display: none; }

.track-row__main { display: flex; align-items: center; gap: 12px; min-width: 0; }
.track-row__cover { width: 40px; height: 40px; border-radius: 4px; object-fit: cover; }
.track-row__cover--placeholder { background: linear-gradient(135deg, var(--accent-wash), var(--accent-2-wash)); }
.track-row__meta { min-width: 0; }
.track-row__title { margin: 0; font-size: 13.5px; font-weight: 600; color: var(--text-primary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.track-row__artist { margin: 2px 0 0; font-size: 12px; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.track-row__album { font-size: 12.5px; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

.track-row__like { opacity: 0; }
.track-row:hover .track-row__like,
.track-row__like--active { opacity: 1; }
.track-row__like--active { color: var(--accent); }

.track-row__duration { font-size: 12.5px; color: var(--text-tertiary); text-align: right; }

@media (max-width: 720px) {
  .track-row { grid-template-columns: 28px 1fr 32px 40px; }
  .track-row__album { display: none; }
}
</style>
