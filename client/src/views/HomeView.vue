<script setup>
import { ref, onMounted } from 'vue'
import interactionService from '@/services/interactionService'
import TrackCard from '@/components/tracks/TrackCard.vue'
import TrackList from '@/components/tracks/TrackList.vue'
import { useUserStore } from '@/store/user'

const userStore = useUserStore()
const loading = ref(true)
const error = ref(null)
const feed = ref({ recommended: [], recentlyPlayed: [], forYouGenres: [] })
const artists = ref([])

async function load() {
  loading.value = true
  error.value = null
  try {
    const [homeFeed, featuredArtists] = await Promise.all([
      interactionService.getHomeFeed(),
      interactionService.getArtists()
    ])
    feed.value = homeFeed
    artists.value = featuredArtists
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
  }
}

onMounted(load)

const greeting = () => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 18) return 'Good afternoon'
  return 'Good evening'
}
</script>

<template>
  <section class="home">
    <header class="home__header">
      <span class="eyebrow">{{ greeting() }}</span>
      <h1>Welcome back{{ userStore.displayName ? `, ${userStore.displayName}` : '' }}</h1>
      <p class="home__subhead">
        Recommendations below adapt to what you tell the chat and what you actually play.
      </p>
    </header>

    <p v-if="error" class="home__error">
      Couldn't load your feed — {{ error }}. Check that the backend API is running.
    </p>

    <template v-if="!loading && !error">
      <section v-if="feed.recommended?.length" class="home__section">
        <h2>Made for you</h2>
        <div class="home__grid">
          <TrackCard
            v-for="track in feed.recommended"
            :key="track.id"
            :track="track"
            :queue="feed.recommended"
            source="home-recommended"
          />
        </div>
      </section>

      <section v-if="artists.length" class="home__section">
        <h2>Artists to follow</h2>
        <div class="home__artists">
          <article v-for="artist in artists" :key="artist.id" class="home__artist">
            <router-link :to="`/artist/${artist.id}`" class="home__artist-link">
              <span class="home__artist-avatar">{{ artist.name.charAt(0) }}</span>
              <span>{{ artist.name }}</span>
            </router-link>
            <button class="btn-ghost home__follow" :class="{ 'home__following': userStore.isFollowing(artist.id) }" @click="userStore.toggleFollow(artist)">
              {{ userStore.isFollowing(artist.id) ? 'Following' : 'Follow' }}
            </button>
          </article>
        </div>
      </section>

      <section v-if="feed.recentlyPlayed?.length" class="home__section">
        <h2>Jump back in</h2>
        <TrackList :tracks="feed.recentlyPlayed" source="home-recent" :show-header="false" />
      </section>

      <section
        v-for="genreShelf in feed.forYouGenres"
        :key="genreShelf.genre"
        class="home__section"
      >
        <h2>{{ genreShelf.genre }}</h2>
        <div class="home__grid">
          <TrackCard
            v-for="track in genreShelf.tracks"
            :key="track.id"
            :track="track"
            :queue="genreShelf.tracks"
            :source="`home-${genreShelf.genre}`"
          />
        </div>
      </section>

      <p
        v-if="!feed.recommended?.length && !feed.recentlyPlayed?.length && !feed.forYouGenres?.length"
        class="home__empty"
      >
        Play a few tracks or tell the assistant what you like, and your home feed will fill in.
      </p>
    </template>

    <p v-if="loading" class="home__loading">Loading your feed…</p>
  </section>
</template>

<style scoped>
.home__header { margin-bottom: 28px; }
.home__header h1 { font-size: 28px; margin: 6px 0 6px; }
.home__subhead { margin: 0; color: var(--text-secondary); font-size: 13.5px; max-width: 520px; }

.home__section { margin-bottom: 32px; }
.home__section h2 { font-size: 19px; margin-bottom: 14px; }

.home__grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: 14px;
}
.home__artists { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 14px; }
.home__artist { display: grid; gap: 10px; padding: 14px; border: 1px solid var(--line-soft); border-radius: var(--radius-md); background: var(--bg-raised); }
.home__artist-link { display: grid; justify-items: center; gap: 8px; color: var(--text-primary); font-weight: 700; font-size: 13px; text-align: center; }
.home__artist-avatar { display: grid; place-items: center; width: 64px; height: 64px; border-radius: 50%; background: var(--accent-2-wash); color: var(--accent-strong); font-family: var(--font-display); font-size: 24px; }
.home__follow { justify-content: center; padding: 7px 12px; }
.home__following { color: var(--accent); border-color: var(--accent); }

.home__loading, .home__empty { color: var(--text-tertiary); font-size: 13.5px; padding: 24px 0; }
.home__error { color: #f2b8b8; font-size: 13.5px; background: rgba(224,90,90,0.1); padding: 12px 14px; border-radius: var(--radius-md); }
</style>
