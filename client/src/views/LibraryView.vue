<script setup>
import { onMounted } from 'vue'
import { useUserStore } from '@/store/user'
import TrackList from '@/components/tracks/TrackList.vue'

const userStore = useUserStore()

onMounted(() => {
  if (!userStore.library.likedTracks.length) userStore.fetchLibrary()
})
</script>

<template>
  <section class="library">
    <header class="library__header">
      <h1>Your library</h1>
      <p class="library__subhead">Liked songs, playlists, and artists you follow.</p>
    </header>

    <p v-if="userStore.error" class="library__error">Couldn't load your library — {{ userStore.error }}.</p>
    <p v-if="userStore.loading" class="library__loading">Loading…</p>

    <template v-if="!userStore.loading">
      <section class="library__section">
        <h2>Playlists</h2>
        <div class="library__grid" v-if="userStore.library.playlists?.length">
          <router-link
            v-for="playlist in userStore.library.playlists"
            :key="playlist.id"
            :to="`/playlist/${playlist.id}`"
            class="library__card"
          >
            <div class="library__card-art">
              <img v-if="playlist.coverUrl" :src="playlist.coverUrl" :alt="playlist.name" />
            </div>
            <p class="library__card-title">{{ playlist.name }}</p>
            <p class="library__card-subtitle">{{ playlist.trackCount || 0 }} tracks</p>
          </router-link>
        </div>
        <p v-else class="library__empty">Playlists you create or save will show up here.</p>
      </section>

      <section class="library__section">
        <h2>Followed artists</h2>
        <div class="library__grid" v-if="userStore.library.followedArtists?.length">
          <router-link
            v-for="artist in userStore.library.followedArtists"
            :key="artist.id"
            :to="`/artist/${artist.id}`"
            class="library__card library__card--round"
          >
            <div class="library__card-art library__card-art--round">
              <img v-if="artist.imageUrl" :src="artist.imageUrl" :alt="artist.name" />
            </div>
            <p class="library__card-title">{{ artist.name }}</p>
          </router-link>
        </div>
        <p v-else class="library__empty">Follow artists from the chat or their profile page.</p>
      </section>

      <section class="library__section">
        <h2>Liked songs</h2>
        <TrackList
          :tracks="userStore.library.likedTracks"
          source="library-liked"
          :show-header="false"
          empty-message="Songs you like will be saved here."
        />
      </section>
    </template>
  </section>
</template>

<style scoped>
.library__header { margin-bottom: 24px; }
.library__header h1 { font-size: 26px; margin-bottom: 6px; }
.library__subhead { margin: 0; color: var(--text-secondary); font-size: 13.5px; }

.library__section { margin-bottom: 30px; }
.library__section h2 { font-size: 17px; margin-bottom: 14px; }

.library__grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 14px; }
.library__card { padding: 12px; border-radius: var(--radius-md); background: var(--bg-raised); }
.library__card:hover { background: var(--bg-hover); }
.library__card-art { aspect-ratio: 1; border-radius: var(--radius-sm); background: var(--bg-panel); overflow: hidden; margin-bottom: 10px; }
.library__card-art--round { border-radius: 50%; }
.library__card-art img { width: 100%; height: 100%; object-fit: cover; }
.library__card--round { text-align: center; }
.library__card-title { margin: 0; font-size: 13px; font-weight: 600; color: var(--text-primary); }
.library__card-subtitle { margin: 3px 0 0; font-size: 12px; color: var(--text-secondary); }

.library__empty, .library__loading { color: var(--text-tertiary); font-size: 13.5px; padding: 8px 0 16px; }
.library__error { color: #f2b8b8; font-size: 13.5px; }
</style>
