import { defineStore } from 'pinia'
import interactionService from '@/services/interactionService'
import authService from '@/services/authService'
import { useChatStore } from './chat'
import { usePlayerStore } from './player'

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
    error: null,
    _sessionMarker: 0
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

    resetAccountState() {
      this._sessionMarker += 1
      this.likedTrackIds = new Set()
      this.followedArtistIds = new Set()
      this.library = { playlists: [], likedTracks: [], followedArtists: [] }
      this.avatarUrl = ''
      this.loading = false
      this.error = null
      useChatStore().resetSession()
      usePlayerStore().resetSession()
    },

    async login(credentials) {
      const result = await authService.login(credentials)
      this.resetAccountState()
      this.setAccount(result.user, result.token)
      await this.fetchLibrary()
    },

    async signup(account) {
      const result = await authService.signup(account)
      this.resetAccountState()
      this.setAccount(result.user, result.token)
      await this.fetchLibrary()
    },

    async refreshProfile() {
      const sessionMarker = this._sessionMarker
      const user = await authService.me()
      if (sessionMarker !== this._sessionMarker || !this.isAuthenticated) return
      this.setAccount(user)
    },

    logout() {
      this.resetAccountState()
      ;['reverie:token', 'reverie:userId', 'reverie:login', 'reverie:email', 'reverie:displayName', 'reverie:createdAt'].forEach((key) => localStorage.removeItem(key))
      this.id = ''
      this.loginName = ''
      this.email = ''
      this.displayName = ''
      this.createdAt = ''
    },

    async fetchLibrary() {
      const sessionMarker = this._sessionMarker
      this.loading = true
      this.error = null
      try {
        const data = await interactionService.getLibrary()
        if (sessionMarker !== this._sessionMarker) return
        this.library = data
        this.likedTrackIds = new Set((data.likedTracks || []).map((t) => t.id))
        this.followedArtistIds = new Set((data.followedArtists || []).map((a) => a.id))
        if (data.avatarUrl) this.avatarUrl = data.avatarUrl
      } catch (err) {
        if (sessionMarker !== this._sessionMarker) return
        this.error = err.message
      } finally {
        if (sessionMarker === this._sessionMarker) this.loading = false
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
