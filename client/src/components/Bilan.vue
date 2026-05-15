<script setup>
import Dashboard from './Dashboard.vue';
import { useAuthStore } from '../stores/authStore';
import { storeToRefs } from 'pinia';
import { useThemeStore } from "../stores/themeStore";

const themeStore = useThemeStore();
const { isDarkMode } = storeToRefs(themeStore);

const props = defineProps(['user_name'])
const emit = defineEmits(["close"]);
const authStore = useAuthStore();
const { userFullInfo } = storeToRefs(authStore);
</script>

<template>
  <div :class="['relative w-full max-w-[1600px] max-h-[90vh] rounded-[2.5rem] shadow-2xl overflow-hidden border transition-all duration-300', isDarkMode ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200']">
    <!-- Header with User Profile -->
    <div :class="['px-10 py-8 border-b transition-colors', isDarkMode ? 'bg-zinc-900 border-zinc-800' : 'bg-slate-50 border-zinc-100']">
      <div class="flex items-center justify-between gap-6">
        <div class="flex items-center gap-6">
          <div :class="['w-16 h-16 rounded-3xl flex items-center justify-center text-xl font-black shadow-lg transition-colors', isDarkMode ? 'bg-zinc-800 text-white shadow-black/20 text-zinc-300' : 'bg-white text-zinc-900 shadow-zinc-200/50']">
            {{ (userFullInfo.prenom || props.user_name).substring(0, 2).toUpperCase() }}
          </div>
          <div>
            <h2 :class="['text-2xl font-black tracking-tighter italic', isDarkMode ? 'text-white' : 'text-zinc-900']">{{ userFullInfo.prenom }} {{ userFullInfo.nom }}</h2>
            <p :class="['text-xs font-black uppercase tracking-[0.2em]', isDarkMode ? 'text-zinc-500' : 'text-zinc-400']">{{ props.user_name }} • ÉLÈVE</p>
          </div>
        </div>
        <button @click="emit('close')" :class="['p-3 rounded-2xl transition-all hover:scale-110 shadow-lg', isDarkMode ? 'bg-zinc-800 text-zinc-400 hover:text-red-400' : 'bg-white text-zinc-400 hover:text-red-500 border border-zinc-100 shadow-zinc-200/50']">
          <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Dashboard Content -->
    <div :class="['p-10 overflow-y-auto max-h-[calc(90vh-140px)] custom-scrollbar transition-colors relative', isDarkMode ? 'bg-zinc-900' : 'bg-white']">
      <Dashboard :isDarkMode="isDarkMode" :studentId="props.user_name" />
      
      <!-- Guest Restriction Overlay -->
      <div 
        v-if="props.user_name === 'Invité'" 
        class="absolute inset-0 z-10 flex items-center justify-center p-6 md:p-12 animate-in fade-in duration-500"
      >
        <div class="absolute inset-0 bg-white/40 dark:bg-zinc-950/40 backdrop-blur-md"></div>
        
        <div :class="['relative max-w-md w-full p-8 md:p-10 rounded-[2.5rem] shadow-2xl border text-center transform transition-all hover:scale-[1.02] duration-300', 
                    isDarkMode ? 'bg-zinc-900/90 border-white/10 shadow-black/50' : 'bg-white/90 border-zinc-200 shadow-zinc-200']">
          
          <div class="mb-8 relative">
            <div class="absolute inset-0 bg-blue-500/20 rounded-full animate-pulse blur-xl"></div>
            <div :class="['relative w-20 h-20 mx-auto rounded-3xl flex items-center justify-center text-4xl shadow-lg', 
                       isDarkMode ? 'bg-zinc-800 text-blue-400' : 'bg-blue-50 text-blue-600']">
              🔒
            </div>
          </div>

          <h3 :class="['text-2xl font-black mb-4 tracking-tighter italic', isDarkMode ? 'text-white' : 'text-zinc-900']">
            Dashboard limité
          </h3>
          
          <p :class="['text-sm leading-relaxed mb-8', isDarkMode ? 'text-zinc-400' : 'text-zinc-500']">
            Le dashboard est réservé aux élèves inscrits. Connectez-vous avec votre compte pour suivre votre progression, gagner de l'XP et consulter vos statistiques d'apprentissage.
          </p>

          <button 
            @click="authStore.logout"
            class="w-full py-4 rounded-2xl bg-blue-600 hover:bg-blue-500 text-white font-black text-xs uppercase tracking-[0.2em] shadow-xl shadow-blue-500/25 transition-all active:scale-95"
          >
            Se connecter
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: #3f3f46 #f4f4f5;
}
.dark .custom-scrollbar {
  scrollbar-color: #3f3f46 #09090b;
}
.custom-scrollbar::-webkit-scrollbar {
  width: 8px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #f4f4f5;
}
.dark .custom-scrollbar::-webkit-scrollbar-track {
  background: #09090b;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #d4d4d8;
  border-radius: 20px;
}
.dark .custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #3f3f46;
}
</style>

<style scoped>
</style>