<script setup>
import { ref, watch, onMounted } from 'vue'
import interactionService from '@/services/interactionService'
import { usePlayerStore } from '@/store/player'
import TrackList from '@/components/tracks/TrackList.vue'

const props = defineProps({ id: { type: String, required: true } })
const playerStore = usePlayerStore()

const loading = ref(true)
const error = ref(null)
const album = ref(null)

async function load(id) {
  loading.value = true
  error.value = null
  try {
    album.value = await interactionService.getAlbum(id)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

onMounted(() => load(props.id))
watch(() => props.id, load)

function playAll() {
  if (album.value?.tracks?.length) {
    playerStore.playQueue(album.value.tracks, 0, `album-${props.id}`)
  }
}
</script>

<template>
  <section class="album">
    <p v-if="loading" class="album__loading">Loading album…</p>
    <p v-else-if="error" class="album__error">Couldn't load this album — {{ error }}.</p>

    <template v-else-if="album">
      <header class="album__header">
        <div class="album__cover">
          <img v-if="album.coverUrl" :src="album.coverUrl" :alt="album.title" />
        </div>
        <div class="album__info">
          <span class="eyebrow">Album</span>
          <h1>{{ album.title }}</h1>
          <router-link :to="`/artist/${album.artistId}`" class="album__artist-link">{{ album.artistName }}</router-link>
          <p class="album__stats">{{ album.releaseYear }} · {{ album.tracks?.length || 0 }} songs</p>
        </div>
      </header>

      <button class="btn-pill album__play-all" :disabled="!album.tracks?.length" @click="playAll">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M7 4v16l14-8z"/></svg>
        Play
      </button>

      <TrackList :tracks="album.tracks || []" :source="`album-${id}`" :show-album="false" />
    </template>
  </section>
</template>

<style scoped>
.album__header { display: flex; gap: 24px; align-items: flex-end; margin-bottom: 22px; }
.album__cover { width: 176px; height: 176px; border-radius: var(--radius-md); background: linear-gradient(135deg, var(--accent-wash), var(--accent-2-wash)); box-shadow: var(--shadow-panel); overflow: hidden; flex-shrink: 0; }
.album__cover img { width: 100%; height: 100%; object-fit: cover; }
.album__info h1 { font-size: 38px; margin: 8px 0 10px; }
.album__artist-link { font-size: 14px; font-weight: 700; color: var(--text-primary); }
.album__artist-link:hover { text-decoration: underline; }
.album__stats { margin: 8px 0 0; color: var(--text-tertiary); font-size: 12.5px; }

.album__play-all { margin-bottom: 20px; }
.album__loading, .album__error { color: var(--text-tertiary); font-size: 13.5px; }
.album__error { color: #f2b8b8; }

@media (max-width: 600px) {
  .album__header { flex-direction: column; align-items: flex-start; }
}
</style>
