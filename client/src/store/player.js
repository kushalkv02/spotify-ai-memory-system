import { defineStore } from 'pinia'
import interactionService from '@/services/interactionService'

export const usePlayerStore = defineStore('player', {
  state: () => ({
    queue: [],
    queueIndex: -1,
    currentTrack: null,
    isPlaying: false,
    progressSeconds: 0,
    volume: 0.8,
    isMuted: false,
    shuffle: false,
    repeatMode: 'off', // 'off' | 'all' | 'one'
    _tickHandle: null,
    _playSource: null
  }),

  getters: {
    hasNext: (state) => state.queueIndex < state.queue.length - 1 || state.repeatMode !== 'off',
    hasPrevious: (state) => state.queueIndex > 0,
    progressPct: (state) => {
      if (!state.currentTrack?.durationSeconds) return 0
      return Math.min(100, (state.progressSeconds / state.currentTrack.durationSeconds) * 100)
    }
  },

  actions: {
    /** Replace the queue and start playing at `startIndex`. */
    playQueue(tracks, startIndex = 0, source = 'unknown') {
      this.queue = tracks
      this.queueIndex = startIndex
      this._playSource = source
      this._loadCurrent()
    },

    /** Play a single track immediately, queueing it alone. */
    playTrack(track, source = 'unknown') {
      this.playQueue([track], 0, source)
    },

    togglePlay() {
      if (!this.currentTrack) return
      this.isPlaying = !this.isPlaying
      this.isPlaying ? this._startTicking() : this._stopTicking()
    },

    pause() {
      this.isPlaying = false
      this._stopTicking()
    },

    next(auto = false) {
      const prevTrack = this.currentTrack
      if (auto && prevTrack) {
        interactionService.logSkip(prevTrack.id, { atSeconds: this.progressSeconds }).catch(() => {})
      }
      if (this.repeatMode === 'one' && auto) {
        this.progressSeconds = 0
        this._startTicking()
        return
      }
      if (this.queueIndex < this.queue.length - 1) {
        this.queueIndex += 1
        this._loadCurrent()
      } else if (this.repeatMode === 'all' && this.queue.length) {
        this.queueIndex = 0
        this._loadCurrent()
      } else {
        this.pause()
      }
    },

    previous() {
      if (this.progressSeconds > 3) {
        this.progressSeconds = 0
        return
      }
      if (this.queueIndex > 0) {
        this.queueIndex -= 1
        this._loadCurrent()
      }
    },

    seekTo(seconds) {
      this.progressSeconds = seconds
    },

    setVolume(value) {
      this.volume = value
      this.isMuted = value === 0
    },

    toggleMute() {
      this.isMuted = !this.isMuted
    },

    toggleShuffle() {
      this.shuffle = !this.shuffle
    },

    cycleRepeat() {
      this.repeatMode = { off: 'all', all: 'one', one: 'off' }[this.repeatMode]
    },

    _loadCurrent() {
      this.currentTrack = this.queue[this.queueIndex] || null
      this.progressSeconds = 0
      this.isPlaying = !!this.currentTrack
      if (this.currentTrack) {
        interactionService.logPlay(this.currentTrack.id, { source: this._playSource }).catch(() => {})
        this._startTicking()
      } else {
        this._stopTicking()
      }
    },

    _startTicking() {
      this._stopTicking()
      this._tickHandle = setInterval(() => {
        if (!this.currentTrack) return
        this.progressSeconds += 1
        if (this.progressSeconds >= this.currentTrack.durationSeconds) {
          this.next(true)
        }
      }, 1000)
    },

    _stopTicking() {
      if (this._tickHandle) {
        clearInterval(this._tickHandle)
        this._tickHandle = null
      }
    }
  }
})
