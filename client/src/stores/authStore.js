import { defineStore } from 'pinia'
import { ref } from 'vue'
import { validateToken } from '../utils/auth.js'

export const useAuthStore = defineStore('auth', () => {
  const id_user = ref('')
  const userFullInfo = ref({ nom: '', prenom: '' })
  const assistantIsOn = ref(false)
  const isAdmin = ref(false)
  const isSuperAdmin = ref(false)
  const aiEnabled = ref(false)

  function _decodeRole() {
    isAdmin.value = false
    isSuperAdmin.value = false
    const token = localStorage.getItem("access_token")
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]))
        if (payload.role === 'superadmin') {
          isAdmin.value = true
          isSuperAdmin.value = true
        } else if (payload.role === 'admin') {
          isAdmin.value = true
        }
      } catch(e) {}
    }
  }

  function setUserId(user) {
    id_user.value = user
    _decodeRole()
    userFullInfo.value = { nom: '', prenom: '' }
    aiEnabled.value = false
  }

  function setUserFullInfo(info) {
    userFullInfo.value = info
    if (info.ai_enabled !== undefined) {
      aiEnabled.value = !!info.ai_enabled
    }
  }

  function setAssistantStatus(status) {
    assistantIsOn.value = !!status
  }

  function logout() {
    localStorage.removeItem("access_token")
    localStorage.removeItem("username")
    id_user.value = ""
    window.location.reload()
  }

  function checkSavedAuth() {
    const savedUser = localStorage.getItem("username")
    const token = localStorage.getItem("access_token")
    if (savedUser && validateToken()) {
      id_user.value = savedUser
      _decodeRole()
    } else if (savedUser) {
      logout()
    }
  }

  return { id_user, userFullInfo, assistantIsOn, isAdmin, isSuperAdmin, aiEnabled, setUserId, setUserFullInfo, setAssistantStatus, logout, checkSavedAuth }
})
