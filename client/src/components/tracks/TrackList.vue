<script setup>
import TrackRow from './TrackRow.vue'

const props = defineProps({
  tracks: { type: Array, required: true },
  source: { type: String, default: 'list' },
  showAlbum: { type: Boolean, default: true },
  showHeader: { type: Boolean, default: true },
  emptyMessage: { type: String, default: 'Nothing here yet.' }
})
</script>

<template>
  <div class="track-list">
    <div v-if="showHeader && tracks.length" class="track-list__header">
      <span>#</span>
      <span>Title</span>
      <span v-if="showAlbum">Album</span>
      <span></span>
      <span class="track-list__header-duration">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 3"/></svg>
      </span>
    </div>

    <TrackRow
      v-for="(track, index) in tracks"
      :key="track.id"
      :track="track"
      :index="index"
      :queue="tracks"
      :source="source"
      :show-album="showAlbum"
    />

    <p v-if="!tracks.length" class="track-list__empty">{{ emptyMessage }}</p>
  </div>
</template>

<style scoped>
.track-list { display: flex; flex-direction: column; }

.track-list__header {
  display: grid;
  grid-template-columns: 32px 1fr 200px 32px 48px;
  gap: 14px;
  padding: 0 12px 8px;
  border-bottom: 1px solid var(--line-soft);
  margin-bottom: 8px;
  color: var(--text-tertiary);
  font-size: 11px;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.track-list__header-duration { display: flex; justify-content: flex-end; }

.track-list__empty {
  color: var(--text-tertiary);
  font-size: 13px;
  padding: 24px 12px;
  text-align: center;
}

@media (max-width: 720px) {
  .track-list__header { grid-template-columns: 28px 1fr 32px 40px; }
}
</style>
