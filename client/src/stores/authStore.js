import { defineStore } from 'pinia'
import { ref } from 'vue'
import { validateToken } from '../utils/auth.js'

export const useAuthStore = defineStore('auth', () => {
  const id_user = ref('')
  const userFullInfo = ref({ nom: '', prenom: '' })
  const assistantIsOn = ref(false)
  const isAdmin = ref(false)

  function setUserId(user) {
    id_user.value = user
    isAdmin.value = false;
    const token = localStorage.getItem("access_token");
    if (token) {
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        if (payload.role === 'admin') {
           isAdmin.value = true;
        }
      } catch(e) {}
    }
    userFullInfo.value = { nom: '', prenom: '' }
  }

  function setUserFullInfo(info) {
    userFullInfo.value = info
  }

  function setAssistantStatus(status) {
    assistantIsOn.value = !!status
  }

  function logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("username");
    id_user.value = "";
    window.location.reload();
  }

  function checkSavedAuth() {
    const savedUser = localStorage.getItem("username");
    const token = localStorage.getItem("access_token");
    if (savedUser && validateToken()) {
      id_user.value = savedUser;
      try {
        const payload = JSON.parse(atob(token.split('.')[1]));
        if (payload.role === 'admin') {
           isAdmin.value = true;
        }
      } catch(e) {}
    } else if (savedUser) {
      // Token exists but is expired/invalid
      logout()
    }
  }

  return { id_user, userFullInfo, assistantIsOn, isAdmin, setUserId, setUserFullInfo, setAssistantStatus, logout, checkSavedAuth }
})
