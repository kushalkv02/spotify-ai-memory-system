<script setup>
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import interactionService from '@/services/interactionService'
import TrackList from '@/components/tracks/TrackList.vue'
import TrackCard from '@/components/tracks/TrackCard.vue'

const route = useRoute()
const router = useRouter()
const query = ref(route.query.q || '')
const loading = ref(false)
const error = ref(null)
const results = ref({ tracks: [], artists: [], albums: [] })
let debounceHandle = null

async function runSearch(q) {
  if (!q.trim()) {
    results.value = { tracks: [], artists: [], albums: [] }
    return
  }
  loading.value = true
  error.value = null
  try {
    results.value = await interactionService.search(q)
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

watch(query, (val) => {
  router.replace({ query: { ...route.query, q: val || undefined } })
  clearTimeout(debounceHandle)
  debounceHandle = setTimeout(() => runSearch(val), 350)
})

if (query.value) runSearch(query.value)
</script>

<template>
  <section class="search">
    <div class="search__bar">
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>
      <input v-model="query" type="search" placeholder="Search for songs, artists, albums" autofocus />
    </div>

    <p v-if="error" class="search__error">Search failed — {{ error }}.</p>
    <p v-if="loading" class="search__loading">Searching…</p>

    <template v-if="!loading && query">
      <section v-if="results.artists?.length" class="search__section">
        <h2>Artists</h2>
        <div class="search__artists">
          <router-link
            v-for="artist in results.artists"
            :key="artist.id"
            :to="`/artist/${artist.id}`"
            class="search__artist"
          >
            <div class="search__artist-avatar">
              <img v-if="artist.imageUrl" :src="artist.imageUrl" :alt="artist.name" />
            </div>
            <span>{{ artist.name }}</span>
          </router-link>
        </div>
      </section>

      <section v-if="results.albums?.length" class="search__section">
        <h2>Albums</h2>
        <div class="search__grid">
          <router-link v-for="album in results.albums" :key="album.id" :to="`/album/${album.id}`" class="search__album">
            <div class="search__album-art">
              <img v-if="album.coverUrl" :src="album.coverUrl" :alt="album.title" />
            </div>
            <p class="search__album-title">{{ album.title }}</p>
            <p class="search__album-artist">{{ album.artistName }}</p>
          </router-link>
        </div>
      </section>

      <section v-if="results.tracks?.length" class="search__section">
        <h2>Songs</h2>
        <TrackList :tracks="results.tracks" source="search" :show-header="false" />
      </section>

      <p
        v-if="!results.tracks?.length && !results.artists?.length && !results.albums?.length"
        class="search__empty"
      >
        No matches for "{{ query }}". Try a different spelling or an artist name.
      </p>
    </template>

    <p v-else-if="!loading && !query" class="search__empty">
      Start typing to search your catalog.
    </p>
  </section>
</template>

<style scoped>
.search__bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-radius: var(--radius-pill);
  background: var(--bg-raised);
  border: 1px solid var(--line);
  max-width: 480px;
  margin-bottom: 28px;
  color: var(--text-tertiary);
}
.search__bar input { flex: 1; background: transparent; border: none; outline: none; color: var(--text-primary); font-size: 14px; }

.search__section { margin-bottom: 30px; }
.search__section h2 { font-size: 18px; margin-bottom: 14px; }

.search__artists { display: flex; gap: 20px; flex-wrap: wrap; }
.search__artist { display: flex; flex-direction: column; align-items: center; gap: 8px; width: 120px; text-align: center; }
.search__artist-avatar { width: 100px; height: 100px; border-radius: 50%; background: var(--bg-panel); overflow: hidden; }
.search__artist-avatar img { width: 100%; height: 100%; object-fit: cover; }
.search__artist span { font-size: 12.5px; font-weight: 600; color: var(--text-primary); }

.search__grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 14px; }
.search__album { padding: 10px; border-radius: var(--radius-md); background: var(--bg-raised); }
.search__album:hover { background: var(--bg-hover); }
.search__album-art { aspect-ratio: 1; border-radius: var(--radius-sm); background: var(--bg-panel); overflow: hidden; margin-bottom: 8px; }
.search__album-art img { width: 100%; height: 100%; object-fit: cover; }
.search__album-title { margin: 0; font-size: 13px; font-weight: 600; color: var(--text-primary); }
.search__album-artist { margin: 3px 0 0; font-size: 12px; color: var(--text-secondary); }

.search__loading, .search__empty { color: var(--text-tertiary); font-size: 13.5px; padding: 16px 0; }
.search__error { color: #f2b8b8; font-size: 13.5px; }
</style>
