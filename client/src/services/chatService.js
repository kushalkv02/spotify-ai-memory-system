import apiClient from './apiClient'

// Talks to the AI memory chatbot backend. Kept intentionally thin —
// the store owns conversation state, this module just performs the
// network calls.
export default {
  /**
   * Send a user message to the assistant and get its reply back.
   * @param {string} content
   * @param {Array<{role: string, content: string}>} [context] recent turns, optional if backend is stateless per-request
   */
  async sendMessage(content, context = []) {
    const { data } = await apiClient.post('/chat/messages', { content, context })
    return data // { id, role: 'assistant', content, quickReplies?, trackRefs? }
  },

  async getHistory(limit = 50) {
    const { data } = await apiClient.get('/chat/messages', { params: { limit } })
    return data.messages ?? data
  },

  /** Contextual preference chips, e.g. "More like this" / "Skip genre" */
  async getQuickReplies() {
    const { data } = await apiClient.get('/chat/quick-replies')
    return data.suggestions ?? data
  },

  async clearHistory() {
    await apiClient.delete('/chat/messages')
  }
}
