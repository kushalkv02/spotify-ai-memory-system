import { defineStore } from 'pinia'
import interactionService from '@/services/interactionService'
import authService from '@/services/authService'

export const useUserStore = defineStore('user', {
  state: () => ({
    id: localStorage.getItem('reverie:userId') || '',
    loginName: localStorage.getItem('reverie:login') || '',
    email: localStorage.getItem('reverie:email') || '',
    createdAt: localStorage.getItem('reverie:createdAt') || '',
    displayName: localStorage.getItem('reverie:displayName') || '',
    avatarUrl: '',
    likedTrackIds: new Set(),
    followedArtistIds: new Set(),
    library: { playlists: [], likedTracks: [], followedArtists: [] },
    loading: false,
    error: null
  }),

  getters: {
    isAuthenticated: () => Boolean(localStorage.getItem('reverie:token')),
    isLiked: (state) => (trackId) => state.likedTrackIds.has(trackId),
    isFollowing: (state) => (artistId) => state.followedArtistIds.has(artistId)
  },

  actions: {
    setAccount(user, token) {
      if (token) localStorage.setItem('reverie:token', token)
      this.id = user.id
      this.loginName = user.login
      this.email = user.email
      this.displayName = user.displayName
      this.createdAt = user.createdAt || ''
      localStorage.setItem('reverie:userId', user.id)
      localStorage.setItem('reverie:login', user.login)
      localStorage.setItem('reverie:email', user.email)
      localStorage.setItem('reverie:displayName', user.displayName)
      localStorage.setItem('reverie:createdAt', user.createdAt || '')
    },

    async login(credentials) {
      const result = await authService.login(credentials)
      this.setAccount(result.user, result.token)
    },

    async signup(account) {
      const result = await authService.signup(account)
      this.setAccount(result.user, result.token)
    },

    async refreshProfile() {
      const user = await authService.me()
      this.setAccount(user)
    },

    logout() {
      ;['reverie:token', 'reverie:userId', 'reverie:login', 'reverie:email', 'reverie:displayName', 'reverie:createdAt'].forEach((key) => localStorage.removeItem(key))
      this.id = ''
      this.loginName = ''
      this.email = ''
      this.displayName = ''
      this.createdAt = ''
      this.library = { playlists: [], likedTracks: [], followedArtists: [] }
    },

    async fetchLibrary() {
      this.loading = true
      this.error = null
      try {
        const data = await interactionService.getLibrary()
        this.library = data
        this.likedTrackIds = new Set((data.likedTracks || []).map((t) => t.id))
        this.followedArtistIds = new Set((data.followedArtists || []).map((a) => a.id))
        if (data.avatarUrl) this.avatarUrl = data.avatarUrl
      } catch (err) {
        this.error = err.message
      } finally {
        this.loading = false
      }
    },

    async toggleLike(track) {
      const wasLiked = this.likedTrackIds.has(track.id)
      // optimistic update
      if (wasLiked) {
        this.likedTrackIds.delete(track.id)
        this.library.likedTracks = this.library.likedTracks.filter((t) => t.id !== track.id)
      } else {
        this.likedTrackIds.add(track.id)
        this.library.likedTracks = [track, ...this.library.likedTracks]
      }
      try {
        if (wasLiked) await interactionService.unlikeSong(track.id)
        else await interactionService.likeSong(track.id)
      } catch (err) {
        // revert on failure
        if (wasLiked) this.likedTrackIds.add(track.id)
        else this.likedTrackIds.delete(track.id)
        this.error = err.message
      }
    },

    async toggleFollow(artist) {
      const wasFollowing = this.followedArtistIds.has(artist.id)
      if (wasFollowing) this.followedArtistIds.delete(artist.id)
      else this.followedArtistIds.add(artist.id)
      try {
        if (wasFollowing) await interactionService.unfollowArtist(artist.id)
        else await interactionService.followArtist(artist.id)
      } catch (err) {
        if (wasFollowing) this.followedArtistIds.add(artist.id)
        else this.followedArtistIds.delete(artist.id)
        this.error = err.message
      }
    }
  }
})
