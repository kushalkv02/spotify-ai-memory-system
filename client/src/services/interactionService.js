import apiClient from './apiClient'

// Every listening signal that should feed the AI memory system funnels
// through here: plays, skips, likes, follows. Keeping these as fire-and
// -forget-friendly calls means the player UI never has to block on them.
export default {
  async logPlay(trackId, { source } = {}) {
    const { data } = await apiClient.post('/interactions/play', { trackId, source })
    return data
  },

  async logSkip(trackId, { atSeconds } = {}) {
    const { data } = await apiClient.post('/interactions/skip', { trackId, atSeconds })
    return data
  },

  async toggleLike(trackId) {
    const { data } = await apiClient.post('/interactions/like', { trackId })
    return data // { trackId, liked: true }
  },

  async likeSong(trackId) {
    const { data } = await apiClient.post('/interactions/likes', { trackId })
    return data
  },

  async unlikeSong(trackId) {
    const { data } = await apiClient.delete(`/interactions/likes/${trackId}`)
    return data
  },

  async toggleFollowArtist(artistId) {
    const { data } = await apiClient.post('/interactions/follow', { artistId })
    return data // { artistId, following: true }
  },

  async followArtist(artistId) {
    const { data } = await apiClient.post('/interactions/follows', { artistId })
    return data
  },

  async unfollowArtist(artistId) {
    const { data } = await apiClient.delete(`/interactions/follows/${artistId}`)
    return data
  },

  async getRecommendations(params = {}) {
    const { data } = await apiClient.get('/recommendations', { params })
    return data.tracks ?? data
  },

  async getArtists() {
    const { data } = await apiClient.get('/artists')
    return data.artists
  },

  async getHomeFeed() {
    const { data } = await apiClient.get('/tracks/feed')
    return data
  },

  async search(query) {
    const { data } = await apiClient.get('/tracks/search', { params: { q: query } })
    return data
  },

  async getLibrary() {
    const { data } = await apiClient.get('/library')
    return data
  },

  async getPlaylist(id) {
    const { data } = await apiClient.get(`/playlists/${id}`)
    return data
  },

  async getAlbum(id) {
    const { data } = await apiClient.get(`/albums/${id}`)
    return data
  },

  async getArtist(id) {
    const { data } = await apiClient.get(`/artists/${id}`)
    return data
  }
}
