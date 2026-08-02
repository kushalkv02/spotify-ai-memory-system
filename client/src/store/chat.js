import { defineStore } from 'pinia'
import chatService from '@/services/chatService'

let idCounter = 0
const nextId = () => `local-${Date.now()}-${idCounter++}`

export const useChatStore = defineStore('chat', {
  state: () => ({
    isOpen: false,
    messages: [], // { id, role: 'user' | 'assistant', content, trackRefs?, pending? }
    quickReplies: [],
    isSending: false,
    isLoadingHistory: false,
    error: null,
    hasLoadedHistory: false
  }),

  getters: {
    unreadCount: (state) =>
      state.isOpen ? 0 : state.messages.filter((m) => m.role === 'assistant' && m.unread).length
  },

  actions: {
    open() {
      this.isOpen = true
      this.messages.forEach((m) => (m.unread = false))
      if (!this.hasLoadedHistory) this.loadHistory()
      if (!this.quickReplies.length) this.loadQuickReplies()
    },

    close() {
      this.isOpen = false
    },

    toggle() {
      this.isOpen ? this.close() : this.open()
    },

    async loadHistory() {
      this.isLoadingHistory = true
      try {
        const history = await chatService.getHistory()
        if (history?.length) {
          this.messages = history
        } else if (!this.messages.length) {
          this._seedGreeting()
        }
        this.hasLoadedHistory = true
      } catch (err) {
        this.error = err.message
        if (!this.messages.length) this._seedGreeting()
      } finally {
        this.isLoadingHistory = false
      }
    },

    async loadQuickReplies() {
      try {
        this.quickReplies = await chatService.getQuickReplies()
      } catch {
        this.quickReplies = [
          { id: 'more-like-this', label: 'More like this' },
          { id: 'change-mood', label: 'Change the mood' },
          { id: 'less-of-genre', label: 'Less of this genre' }
        ]
      }
    },

    async sendMessage(content) {
      const trimmed = content.trim()
      if (!trimmed || this.isSending) return

      const userMessage = { id: nextId(), role: 'user', content: trimmed }
      this.messages.push(userMessage)

      const pendingId = nextId()
      this.messages.push({ id: pendingId, role: 'assistant', content: '', pending: true })

      this.isSending = true
      this.error = null
      try {
        const recentContext = this.messages
          .filter((m) => !m.pending)
          .slice(-10)
          .map((m) => ({ role: m.role, content: m.content }))

        const reply = await chatService.sendMessage(trimmed, recentContext)
        const idx = this.messages.findIndex((m) => m.id === pendingId)
        if (idx !== -1) {
          this.messages[idx] = {
            id: reply.id || nextId(),
            role: 'assistant',
            content: reply.content,
            trackRefs: reply.trackRefs || [],
            unread: !this.isOpen
          }
        }
        if (reply.quickReplies?.length) this.quickReplies = reply.quickReplies
      } catch (err) {
        this.error = err.message
        const idx = this.messages.findIndex((m) => m.id === pendingId)
        if (idx !== -1) {
          this.messages[idx] = {
            id: pendingId,
            role: 'assistant',
            content: "I couldn't reach your memory service just now. Try again in a moment.",
            isError: true
          }
        }
      } finally {
        this.isSending = false
      }
    },

    sendQuickReply(reply) {
      this.sendMessage(reply.label || reply.prompt || reply.id)
    },

    _seedGreeting() {
      this.messages = [
        {
          id: nextId(),
          role: 'assistant',
          content:
            "Hey — I'm keeping track of what you play and skip so I can shape better recommendations. Tell me what you're in the mood for."
        }
      ]
    }
  }
})
