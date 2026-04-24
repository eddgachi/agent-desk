import apiClient from './client'

export const simulationApi = {
  create(seed = null) {
    return apiClient.post('/api/v1/simulations', { seed })
  },

  get(simId) {
    return apiClient.get(`/api/v1/simulations/${simId}`)
  },

  tick(simId) {
    return apiClient.post(`/api/v1/simulations/${simId}/tick`)
  },

  reset(simId) {
    return apiClient.post(`/api/v1/simulations/${simId}/reset`)
  },

  startAuto(simId, interval = 0.5) {
    return apiClient.post(`/api/v1/simulations/${simId}/start`, null, { params: { interval } })
  },

  stopAuto(simId) {
    return apiClient.post(`/api/v1/simulations/${simId}/stop`)
  },
}
