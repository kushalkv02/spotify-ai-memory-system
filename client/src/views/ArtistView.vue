<script setup>
import { ref, watch, onMounted, computed } from 'vue'
import interactionService from '@/services/interactionService'
import { usePlayerStore } from '@/store/player'
import { useUserStore } from '@/store/user'
import TrackList from '@/components/tracks/TrackList.vue'

const props = defineProps({ id: { type: String, required: true } })
const playerStore = usePlayerStore()
const userStore = useUserStore()

const loading = ref(true)
const error = ref(null)
const artist = ref(null)

async function load(id) {
  loading.value = true
  error.value = null
  try {
    artist.value = await interactionService.getArtist(id)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

onMounted(() => load(props.id))
watch(() => props.id, load)

const following = computed(() => (artist.value ? userStore.isFollowing(artist.value.id) : false))

function playTop() {
  if (artist.value?.topTracks?.length) {
    playerStore.playQueue(artist.value.topTracks, 0, `artist-${props.id}`)
  }
}
</script>

<template>
  <section class="artist">
    <p v-if="loading" class="artist__loading">Loading artist…</p>
    <p v-else-if="error" class="artist__error">Couldn't load this artist — {{ error }}.</p>

    <template v-else-if="artist">
      <header class="artist__header">
        <div class="artist__avatar">
          <img v-if="artist.imageUrl" :src="artist.imageUrl" :alt="artist.name" />
        </div>
        <div class="artist__info">
          <span class="eyebrow">Artist</span>
          <h1>{{ artist.name }}</h1>
          <p v-if="artist.monthlyListeners" class="artist__stats">
            {{ artist.monthlyListeners.toLocaleString() }} monthly listeners
          </p>
        </div>
      </header>

      <div class="artist__actions">
        <button class="btn-pill" :disabled="!artist.topTracks?.length" @click="playTop">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M7 4v16l14-8z"/></svg>
          Play
        </button>
        <button class="btn-ghost" :class="{ 'artist__following': following }" @click="userStore.toggleFollow(artist)">
          {{ following ? 'Following' : 'Follow' }}
        </button>
      </div>

      <section v-if="artist.topTracks?.length" class="artist__section">
        <h2>Popular</h2>
        <TrackList :tracks="artist.topTracks" :source="`artist-${id}`" :show-header="false" :show-album="false" />
      </section>

      <section v-if="artist.albums?.length" class="artist__section">
        <h2>Albums</h2>
        <div class="artist__grid">
          <router-link v-for="album in artist.albums" :key="album.id" :to="`/album/${album.id}`" class="artist__album">
            <div class="artist__album-art">
              <img v-if="album.coverUrl" :src="album.coverUrl" :alt="album.title" />
            </div>
            <p class="artist__album-title">{{ album.title }}</p>
            <p class="artist__album-year">{{ album.releaseYear }}</p>
          </router-link>
        </div>
      </section>
    </template>
  </section>
</template>

<style scoped>
.artist__header { display: flex; gap: 24px; align-items: flex-end; margin-bottom: 20px; }
.artist__avatar { width: 176px; height: 176px; border-radius: 50%; background: linear-gradient(135deg, var(--accent-wash), var(--accent-2-wash)); box-shadow: var(--shadow-panel); overflow: hidden; flex-shrink: 0; }
.artist__avatar img { width: 100%; height: 100%; object-fit: cover; }
.artist__info h1 { font-size: 42px; margin: 8px 0 10px; }
.artist__stats { margin: 0; color: var(--text-secondary); font-size: 13px; }

.artist__actions { display: flex; gap: 12px; margin-bottom: 26px; }
.artist__following { border-color: var(--accent); color: var(--accent); }

.artist__section { margin-bottom: 30px; }
.artist__section h2 { font-size: 18px; margin-bottom: 14px; }

.artist__grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 14px; }
.artist__album { padding: 10px; border-radius: var(--radius-md); background: var(--bg-raised); }
.artist__album:hover { background: var(--bg-hover); }
.artist__album-art { aspect-ratio: 1; border-radius: var(--radius-sm); background: var(--bg-panel); overflow: hidden; margin-bottom: 8px; }
.artist__album-art img { width: 100%; height: 100%; object-fit: cover; }
.artist__album-title { margin: 0; font-size: 13px; font-weight: 600; color: var(--text-primary); }
.artist__album-year { margin: 3px 0 0; font-size: 12px; color: var(--text-tertiary); }

.artist__loading, .artist__error { color: var(--text-tertiary); font-size: 13.5px; }
.artist__error { color: #f2b8b8; }

@media (max-width: 600px) {
  .artist__header { flex-direction: column; align-items: flex-start; }
}
</style>
