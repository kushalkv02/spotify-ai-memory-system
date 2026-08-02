<script setup>
import { ref, watch, onMounted } from 'vue'
import interactionService from '@/services/interactionService'
import { usePlayerStore } from '@/store/player'
import TrackList from '@/components/tracks/TrackList.vue'

const props = defineProps({ id: { type: String, required: true } })
const playerStore = usePlayerStore()

const loading = ref(true)
const error = ref(null)
const playlist = ref(null)

async function load(id) {
  loading.value = true
  error.value = null
  try {
    playlist.value = await interactionService.getPlaylist(id)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

onMounted(() => load(props.id))
watch(() => props.id, load)

function playAll() {
  if (playlist.value?.tracks?.length) {
    playerStore.playQueue(playlist.value.tracks, 0, `playlist-${props.id}`)
  }
}
</script>

<template>
  <section class="playlist">
    <p v-if="loading" class="playlist__loading">Loading playlist…</p>
    <p v-else-if="error" class="playlist__error">Couldn't load this playlist — {{ error }}.</p>

    <template v-else-if="playlist">
      <header class="playlist__header">
        <div class="playlist__cover">
          <img v-if="playlist.coverUrl" :src="playlist.coverUrl" :alt="playlist.name" />
        </div>
        <div class="playlist__info">
          <span class="eyebrow">Playlist</span>
          <h1>{{ playlist.name }}</h1>
          <p v-if="playlist.description" class="playlist__description">{{ playlist.description }}</p>
          <p class="playlist__stats">{{ playlist.tracks?.length || 0 }} songs</p>
        </div>
      </header>

      <button class="btn-pill playlist__play-all" :disabled="!playlist.tracks?.length" @click="playAll">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M7 4v16l14-8z"/></svg>
        Play
      </button>

      <TrackList :tracks="playlist.tracks || []" :source="`playlist-${id}`" />
    </template>
  </section>
</template>

<style scoped>
.playlist__header { display: flex; gap: 24px; align-items: flex-end; margin-bottom: 22px; }
.playlist__cover { width: 176px; height: 176px; border-radius: var(--radius-md); background: linear-gradient(135deg, var(--accent-wash), var(--accent-2-wash)); box-shadow: var(--shadow-panel); overflow: hidden; flex-shrink: 0; }
.playlist__cover img { width: 100%; height: 100%; object-fit: cover; }
.playlist__info h1 { font-size: 38px; margin: 8px 0 12px; }
.playlist__description { margin: 0 0 8px; color: var(--text-secondary); font-size: 13.5px; max-width: 520px; }
.playlist__stats { margin: 0; color: var(--text-tertiary); font-size: 12.5px; }

.playlist__play-all { margin-bottom: 20px; }
.playlist__loading, .playlist__error { color: var(--text-tertiary); font-size: 13.5px; }
.playlist__error { color: #f2b8b8; }

@media (max-width: 600px) {
  .playlist__header { flex-direction: column; align-items: flex-start; }
}
</style>
