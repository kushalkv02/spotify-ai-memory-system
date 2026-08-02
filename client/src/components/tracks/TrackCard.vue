<script setup>
import { computed } from 'vue'
import { usePlayerStore } from '@/store/player'
import { useUserStore } from '@/store/user'

const props = defineProps({
  track: { type: Object, required: true },
  queue: { type: Array, default: null }, // optional: play within a larger context
  source: { type: String, default: 'card' }
})

const playerStore = usePlayerStore()
const userStore = useUserStore()

const isCurrentlyPlaying = computed(
  () => playerStore.currentTrack?.id === props.track.id && playerStore.isPlaying
)
const liked = computed(() => userStore.isLiked(props.track.id))

function handlePlay() {
  if (playerStore.currentTrack?.id === props.track.id) {
    playerStore.togglePlay()
    return
  }
  const queue = props.queue?.length ? props.queue : [props.track]
  const startIndex = queue.findIndex((t) => t.id === props.track.id)
  playerStore.playQueue(queue, startIndex === -1 ? 0 : startIndex, props.source)
}
</script>

<template>
  <div class="track-card" role="group">
    <button class="track-card__play-area" :aria-label="`Play ${track.title}`" @click="handlePlay">
    <div class="track-card__art">
      <img v-if="track.coverUrl" :src="track.coverUrl" :alt="track.title" />
      <div v-else class="track-card__art-fallback" aria-hidden="true" />
      <span class="track-card__play" :class="{ 'track-card__play--visible': isCurrentlyPlaying }">
        <svg v-if="isCurrentlyPlaying" width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><rect x="5" y="4" width="5" height="16" rx="1"/><rect x="14" y="4" width="5" height="16" rx="1"/></svg>
        <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="currentColor"><path d="M7 4v16l14-8z"/></svg>
      </span>
    </div>
    <p class="track-card__title">{{ track.title }}</p>
    <p class="track-card__subtitle">{{ track.artistName }}</p>
    </button>
    <button class="track-card__like" :class="{ 'track-card__like--active': liked }" :aria-label="liked ? `Unlike ${track.title}` : `Like ${track.title}`" :aria-pressed="liked" @click="userStore.toggleLike(track)">
      <svg width="15" height="15" viewBox="0 0 24 24" :fill="liked ? 'currentColor' : 'none'" stroke="currentColor" stroke-width="1.8"><path d="M12 21s-7.5-4.6-10-9.2C.5 8 2 4 6 4c2 0 3.6 1.2 6 4 2.4-2.8 4-4 6-4 4 0 5.5 4 4 7.8C19.5 16.4 12 21 12 21z"/></svg>
    </button>
  </div>
</template>

<style scoped>
.track-card {
  position: relative;
  width: 100%;
  text-align: left;
  padding: 12px;
  border-radius: var(--radius-md);
  background: var(--bg-raised);
  border: 1px solid transparent;
  transition: background 0.15s ease, border-color 0.15s ease, transform 0.15s ease;
}
.track-card__play-area { display: block; width: 100%; padding: 0; text-align: left; }
.track-card:hover { background: var(--bg-hover); border-color: var(--line); transform: translateY(-2px); }

.track-card__art {
  position: relative;
  aspect-ratio: 1;
  border-radius: var(--radius-sm);
  overflow: hidden;
  margin-bottom: 10px;
  background: var(--bg-panel);
}
.track-card__art img { width: 100%; height: 100%; object-fit: cover; display: block; }
.track-card__art-fallback { width: 100%; height: 100%; background: linear-gradient(135deg, var(--accent-wash), var(--accent-2-wash)); }

.track-card__play {
  position: absolute;
  right: 8px;
  bottom: 8px;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--accent);
  color: #1a1305;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transform: translateY(6px);
  transition: opacity 0.15s ease, transform 0.15s ease;
  box-shadow: var(--shadow-soft);
}
.track-card:hover .track-card__play,
.track-card__play--visible { opacity: 1; transform: translateY(0); }

.track-card__title {
  margin: 0;
  font-size: 13.5px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.track-card__subtitle {
  margin: 3px 0 0;
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.track-card__like { position: absolute; right: 10px; bottom: 10px; width: 28px; height: 28px; display: grid; place-items: center; border-radius: 50%; color: var(--text-secondary); opacity: 0; transition: opacity 0.15s ease, color 0.15s ease; }
.track-card:hover .track-card__like, .track-card__like--active { opacity: 1; }
.track-card__like--active { color: var(--accent); }
</style>
