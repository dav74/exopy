<script setup>
import { ref, onMounted, computed } from "vue";
import { useThemeStore } from "../stores/themeStore";
import { storeToRefs } from "pinia";
import { API_URL } from "../config.js";

const props = defineProps(["studentId"]);
const themeStore = useThemeStore();
const { isDarkMode } = storeToRefs(themeStore);

const stats = ref(null);
const isLoading = ref(true);
const error = ref(null);

const fetchMetrics = async () => {
  isLoading.value = true;
  try {
    const token = localStorage.getItem('access_token');
    const response = await fetch(`${API_URL}/api/metrics/${props.studentId}`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    if (!response.ok) throw new Error('Erreur lors de la récupération des métriques');
    stats.value = await response.json();
  } catch (err) {
    error.value = err.message;
  } finally {
    isLoading.value = false;
  }
};

onMounted(fetchMetrics);

const getLevelColor = (level) => {
  const colors = {
    'Vert': 'text-green-500 bg-green-500/10 border-green-500/20',
    'Bleu': 'text-blue-500 bg-blue-500/10 border-blue-500/20',
    'Rouge': 'text-red-500 bg-red-500/10 border-red-500/20',
    'Noir': 'text-white bg-zinc-950 border-white/20'
  };
  return colors[level] || 'text-zinc-500 bg-zinc-500/10 border-zinc-500/20';
};
</script>

<template>
  <div class="space-y-6 text-zinc-900 dark:text-white p-2 transition-colors duration-300">
    <div v-if="isLoading" class="flex justify-center items-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
    </div>

    <div v-else-if="error" class="bg-red-500/10 dark:bg-red-500/20 border border-red-500/50 p-4 rounded-xl text-red-600 dark:text-red-400">
      {{ error }}
    </div>

    <div v-else-if="stats" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 xl:gap-6">
      
      <!-- Section Progression -->
      <div :class="['border p-8 rounded-[2rem] shadow-sm transition-all group', isDarkMode ? 'bg-zinc-900/50 border-zinc-800 dark:shadow-xl hover:shadow-blue-500/5' : 'bg-white border-zinc-200 hover:shadow-blue-500/5']">
        <div class="flex justify-between items-start mb-6">
          <h3 class="text-xl font-bold tracking-tight text-zinc-800 dark:text-zinc-100 flex items-center gap-2">
            <span class="text-blue-500">📊</span> Progression
          </h3>
          <div class="bg-blue-600/10 dark:bg-blue-600/20 text-blue-600 dark:text-blue-400 px-3 py-1 rounded-full text-sm font-bold border border-blue-500/30">
            {{ stats.progression.xp }} XP
          </div>
        </div>
        
        <div class="mb-6">
          <div class="flex justify-between text-sm mb-2">
            <span class="text-zinc-500 dark:text-zinc-400 font-medium">Complétion Globale</span>
            <span class="text-zinc-800 dark:text-zinc-200 font-bold">{{ stats.progression.total_completion }} / {{ stats.progression.total_exercises }}</span>
          </div>
          <div :class="['w-full rounded-full h-3 overflow-hidden border shadow-inner', isDarkMode ? 'bg-zinc-800 border-zinc-700' : 'bg-zinc-100 border-zinc-200']">
            <div 
              class="bg-gradient-to-r from-blue-600 to-indigo-500 h-full transition-all duration-1000 ease-out shadow-[0_0_10px_rgba(59,130,246,0.3)]" 
              :style="{ width: (stats.progression.total_completion / stats.progression.total_exercises * 100) + '%' }"
            ></div>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-4">
          <div v-for="(count, level) in stats.progression.levels" :key="level" 
               class="p-3 rounded-xl border flex flex-col items-center justify-center transition-transform hover:scale-105"
               :class="getLevelColor(level)">
            <span class="text-xs font-bold uppercase tracking-wider mb-1">{{ level }}</span>
            <span class="text-2xl font-black">{{ count }}</span>
          </div>
        </div>
      </div>

      <!-- Section Autonomie -->
      <div :class="['border p-8 rounded-[2rem] shadow-sm transition-all group', isDarkMode ? 'bg-zinc-900/50 border-zinc-800 dark:shadow-xl hover:shadow-emerald-500/5' : 'bg-white border-zinc-200 hover:shadow-emerald-500/5']">
        <h3 :class="['text-xl font-bold tracking-tight flex items-center gap-2 mb-6', isDarkMode ? 'text-zinc-100' : 'text-zinc-800']">
          <span class="text-emerald-500">⚡</span> Autonomie
        </h3>
        
        <div class="space-y-6">
          <div class="flex items-center gap-4">
            <div :class="['w-16 h-16 rounded-2xl border flex items-center justify-center text-2xl shadow-sm transition-colors', isDarkMode ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-emerald-50/50 border-emerald-100/50']">
              🎯
            </div>
            <div>
              <p :class="['text-sm font-medium', isDarkMode ? 'text-zinc-400' : 'text-zinc-500']">Réussite sans IA</p>
              <p :class="['text-2xl font-black', isDarkMode ? 'text-white' : 'text-zinc-900']">{{ stats.autonomie.success_rate_no_ai }}%</p>
            </div>
          </div>

          <div class="flex items-center gap-4">
            <div :class="['w-16 h-16 rounded-2xl border flex items-center justify-center text-2xl shadow-sm transition-colors', isDarkMode ? 'bg-amber-500/10 border-amber-500/20' : 'bg-amber-50/50 border-amber-100/50']">
              🤖
            </div>
            <div>
              <p :class="['text-sm font-medium', isDarkMode ? 'text-zinc-400' : 'text-zinc-500']">Requêtes IA / exo</p>
              <p :class="['text-2xl font-black', isDarkMode ? 'text-white' : 'text-zinc-900']">{{ stats.autonomie.avg_ai_requests }}</p>
            </div>
          </div>

          <div :class="['p-4 border rounded-2xl flex items-center justify-between transition-colors', isDarkMode ? 'bg-indigo-500/10 border-indigo-500/20' : 'bg-indigo-50/50 border-indigo-100/50']">
            <div class="flex items-center gap-3">
              <span class="text-3xl">💡</span>
              <div>
                <p :class="['text-[10px] font-black uppercase tracking-widest', isDarkMode ? 'text-indigo-400' : 'text-indigo-600']">Badges "Déclic"</p>
                <p :class="['text-[10px] font-medium leading-tight', isDarkMode ? 'text-zinc-400' : 'text-zinc-500']">Réussite rapide après IA</p>
              </div>
            </div>
            <span :class="['text-3xl font-black', isDarkMode ? 'text-white' : 'text-indigo-600']">{{ stats.autonomie.badges_declic }}</span>
          </div>
        </div>
      </div>

      <!-- Section Qualité de Code -->
      <div :class="['border p-8 rounded-[2rem] shadow-sm transition-all group', isDarkMode ? 'bg-zinc-900/50 border-zinc-800 shadow-xl hover:shadow-rose-500/5' : 'bg-white border-zinc-200 hover:shadow-rose-500/5']">
        <h3 :class="['text-xl font-bold tracking-tight flex items-center gap-2 mb-6', isDarkMode ? 'text-zinc-100' : 'text-zinc-800']">
          <span class="text-rose-500">✨</span> Qualité
        </h3>

        <div class="grid grid-cols-2 gap-4 mb-6">
          <div :class="['p-4 rounded-xl border shadow-sm transition-colors', isDarkMode ? 'bg-zinc-800/50 border-zinc-700/50' : 'bg-zinc-50 border-zinc-100']">
            <p :class="['text-[10px] font-black uppercase mb-1 tracking-widest', isDarkMode ? 'text-zinc-400' : 'text-zinc-500']">First Try</p>
            <p :class="['text-2xl font-black', isDarkMode ? 'text-rose-400' : 'text-rose-600']">{{ stats.qualite.first_try_rate }}%</p>
          </div>
          <div :class="['p-4 rounded-xl border shadow-sm transition-colors', isDarkMode ? 'bg-zinc-800/50 border-zinc-700/50' : 'bg-zinc-50 border-zinc-100']">
            <p :class="['text-[10px] font-black uppercase mb-1 tracking-widest', isDarkMode ? 'text-zinc-400' : 'text-zinc-500']">Persévérance</p>
            <p :class="['text-2xl font-black', isDarkMode ? 'text-rose-400' : 'text-rose-600']">{{ stats.qualite.perseverance_index }}</p>
          </div>
        </div>

        <div class="space-y-3">
          <p :class="['text-[10px] font-black uppercase tracking-widest mb-2 ml-1', isDarkMode ? 'text-zinc-500' : 'text-zinc-400']">Erreurs fréquentes</p>
          <div v-for="err in stats.qualite.common_errors" :key="err.type" 
               :class="['flex items-center justify-between p-2.5 rounded-xl border shadow-sm transition-all', isDarkMode ? 'bg-zinc-800/30 border-zinc-800 hover:bg-zinc-800' : 'bg-zinc-50 border-zinc-100 hover:bg-white']">
            <span :class="['text-xs font-mono', isDarkMode ? 'text-zinc-300' : 'text-zinc-600']">{{ err.type }}</span>
            <span :class="['px-2 py-0.5 rounded-lg text-[10px] font-black', isDarkMode ? 'bg-zinc-700 text-zinc-100' : 'bg-zinc-200 text-zinc-700']">{{ err.count }}</span>
          </div>
        </div>
      </div>

      <!-- Section Engagement -->
      <div :class="['border p-6 rounded-2xl shadow-sm transition-all group', isDarkMode ? 'bg-zinc-900/50 border-zinc-800 shadow-xl hover:shadow-orange-500/5' : 'bg-white border-zinc-200 hover:shadow-orange-500/5']">
        <h3 :class="['text-xl font-bold tracking-tight flex items-center gap-2 mb-6', isDarkMode ? 'text-zinc-100' : 'text-zinc-800']">
          <span class="text-orange-500">🔥</span> Engagement
        </h3>

        <div class="flex flex-col items-center justify-center py-6 bg-gradient-to-b from-orange-500/5 to-transparent rounded-[2rem] border border-orange-500/10 mb-6 shadow-inner">
          <div class="text-5xl mb-3">🔥</div>
          <div :class="['text-4xl font-black tracking-tighter', isDarkMode ? 'text-white' : 'text-orange-600']">{{ stats.engagement.streak }} JOURS</div>
          <div :class="['text-[10px] font-black uppercase tracking-[0.2em] mt-1', isDarkMode ? 'text-orange-500' : 'text-orange-400']">Série en cours</div>
        </div>

        <div :class="['flex justify-between items-center p-5 rounded-2xl border shadow-sm', isDarkMode ? 'bg-zinc-800/50 border-zinc-700/50' : 'bg-zinc-50 border-zinc-100']">
          <div class="min-w-0">
            <p :class="['text-[10px] font-black uppercase tracking-widest mb-1', isDarkMode ? 'text-zinc-400' : 'text-zinc-500']">Temps hebdo</p>
            <p :class="['text-lg font-black truncate italic', isDarkMode ? 'text-zinc-100' : 'text-zinc-800']">{{ Math.floor(stats.engagement.weekly_practice_time / 60) }}h {{ stats.engagement.weekly_practice_time % 60 }}min</p>
          </div>
          <div class="text-orange-500 dark:text-orange-400 flex-shrink-0 ml-4">
             <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<style scoped>
/* Animations subtiles */
.group:hover {
  transform: translateY(-2px);
}
</style>
