import apiClient from './apiClient'

export default {
  signup(payload) {
    return apiClient.post('/auth/signup', payload).then((response) => response.data)
  },
  login(payload) {
    return apiClient.post('/auth/login', payload).then((response) => response.data)
  },
  me() {
    return apiClient.get('/auth/me').then((response) => response.data.user)
  }
}
