<script setup>
import { ref, onMounted, computed } from "vue";
import { useThemeStore } from "../stores/themeStore";
import { storeToRefs } from "pinia";
import { API_URL } from "../config.js";
import ClassStatsHelpModal from "./ClassStatsHelpModal.vue";
import ExportFieldsModal from "./ExportFieldsModal.vue";

const emit = defineEmits(["select-student"]);

const themeStore = useThemeStore();
const { isDarkMode } = storeToRefs(themeStore);

const data = ref(null);
const isLoading = ref(true);
const error = ref(null);
const showHelp = ref(false);

const fetchClassMetrics = async () => {
  isLoading.value = true;
  try {
    const token = localStorage.getItem("access_token");
    const response = await fetch(`${API_URL}/api/metrics/class`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) throw new Error("Erreur lors de la récupération des statistiques");
    data.value = await response.json();
  } catch (err) {
    error.value = err.message;
  } finally {
    isLoading.value = false;
  }
};

onMounted(fetchClassMetrics);

defineExpose({ refresh: fetchClassMetrics });

const exportFormat = ref("csv");
const isExporting = ref(false);
const showFieldsModal = ref(false);
const selectedExportFields = ref([
  "exercise_id", "exercise_titre", "niveau", "status", "error_type",
  "duration", "ai_used",
]);

const exportResearchData = async () => {
  isExporting.value = true;
  try {
    const token = localStorage.getItem("access_token");
    const params = new URLSearchParams({ format: exportFormat.value });
    selectedExportFields.value.forEach((f) => params.append("fields", f));
    const response = await fetch(`${API_URL}/api/research/export?${params.toString()}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
      const err = await response.json().catch(() => ({}));
      throw new Error(err.detail || "Erreur lors de l'export");
    }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = exportFormat.value === "json" ? "exopy_research_export.json" : "exopy_research_export.zip";
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  } catch (err) {
    alert(err.message);
  } finally {
    isExporting.value = false;
  }
};

const stuckAlerts = computed(() => (data.value?.alerts || []).filter(a => a.type === "stuck"));
const inactiveAlerts = computed(() => (data.value?.alerts || []).filter(a => a.type === "inactive"));

const cellClass = (status) => {
  if (status === "success") return "bg-emerald-500";
  if (status === "success_hard") return "bg-orange-500";
  if (status === "failure") return "bg-rose-500";
  return isDarkMode.value ? "bg-zinc-800" : "bg-zinc-200";
};

const niveauLabel = (n) => ({ 1: "Vert", 2: "Bleu", 3: "Rouge", 4: "Noir" }[n] || n);

const hoveredCell = ref(null);
const cellKey = (username, exId) => `${username}-${exId}`;
</script>

<template>
  <div class="space-y-6 text-zinc-900 dark:text-white p-2 transition-colors duration-300">
    <div v-if="isLoading" class="flex justify-center items-center h-64">
      <div class="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
    </div>

    <div v-else-if="error" class="bg-red-500/10 dark:bg-red-500/20 border border-red-500/50 p-4 rounded-xl text-red-600 dark:text-red-400">
      {{ error }}
    </div>

    <div v-if="data" class="flex justify-end">
      <button
        @click="showHelp = true"
        :class="['flex items-center gap-2 px-4 py-2 rounded-full text-[10px] font-black uppercase tracking-widest border shadow-sm transition-all hover:scale-105', isDarkMode ? 'bg-zinc-900/50 border-zinc-800 text-zinc-300 hover:text-white' : 'bg-white border-zinc-200 text-zinc-500 hover:text-zinc-800']"
      >
        <span :class="['flex items-center justify-center w-4 h-4 rounded-full text-[10px] font-black', isDarkMode ? 'bg-blue-500/20 text-blue-400' : 'bg-blue-500/10 text-blue-600']">?</span>
        Comprendre ces statistiques
      </button>
    </div>

    <ClassStatsHelpModal v-if="showHelp" :isDarkMode="isDarkMode" @close="showHelp = false" />

    <div v-if="data" class="space-y-6">

      <!-- Recherche -->
      <div :class="['border p-6 rounded-[2rem] shadow-sm transition-all', isDarkMode ? 'bg-zinc-900/50 border-zinc-800' : 'bg-white border-zinc-200']">
        <h3 :class="['text-xl font-bold tracking-tight flex items-center gap-2 mb-4', isDarkMode ? 'text-zinc-100' : 'text-zinc-800']">
          <span class="text-indigo-500">🔬</span> Export recherche (données pseudonymisées)
        </h3>
        <div class="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p :class="['text-sm font-bold', isDarkMode ? 'text-zinc-200' : 'text-zinc-700']">
              {{ data.consent_summary.given }} / {{ data.consent_summary.total }} élève(s) avec consentement recherche valide
            </p>
            <p :class="['text-xs mt-1', isDarkMode ? 'text-zinc-500' : 'text-zinc-400']">
              Seuls les élèves consentants sont inclus, sous identifiant pseudonymisé stable. Gérez le consentement dans l'onglet Élèves.
            </p>
          </div>
          <div class="flex items-center gap-2">
            <button
              @click="showFieldsModal = true"
              :class="['text-xs font-bold rounded-xl border px-3 py-2 transition-all', isDarkMode ? 'bg-zinc-800 border-zinc-700 text-zinc-300 hover:bg-zinc-700' : 'bg-white border-zinc-200 text-zinc-600 hover:bg-zinc-50']"
            >
              Choisir les champs ({{ selectedExportFields.length }})
            </button>
            <select v-model="exportFormat" :class="['text-xs font-bold rounded-xl border px-3 py-2', isDarkMode ? 'bg-zinc-800 border-zinc-700 text-zinc-200' : 'bg-white border-zinc-200 text-zinc-700']">
              <option value="csv">CSV (.zip)</option>
              <option value="json">JSON</option>
            </select>
            <button
              @click="exportResearchData"
              :disabled="isExporting || !data.consent_summary.given"
              class="px-5 py-2 rounded-xl text-xs font-black uppercase tracking-widest text-white bg-indigo-600 hover:bg-indigo-500 transition-all shadow-sm disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {{ isExporting ? 'Export...' : 'Exporter' }}
            </button>
          </div>
        </div>
      </div>

      <ExportFieldsModal
        v-if="showFieldsModal"
        :isDarkMode="isDarkMode"
        :selectedFields="selectedExportFields"
        @close="showFieldsModal = false"
        @apply="(fields) => selectedExportFields = fields"
      />

      <!-- Alertes -->
      <div :class="['border p-6 rounded-[2rem] shadow-sm transition-all', isDarkMode ? 'bg-zinc-900/50 border-zinc-800' : 'bg-white border-zinc-200']">
        <h3 :class="['text-xl font-bold tracking-tight flex items-center gap-2 mb-4', isDarkMode ? 'text-zinc-100' : 'text-zinc-800']">
          <span class="text-amber-500">⚠️</span> Alertes
        </h3>

        <div v-if="!stuckAlerts.length && !inactiveAlerts.length" :class="['text-sm italic', isDarkMode ? 'text-zinc-500' : 'text-zinc-400']">
          Aucune alerte : les élèves progressent normalement.
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
          <div v-for="(a, i) in stuckAlerts" :key="'stuck-'+i"
               class="flex items-center gap-3 p-3 rounded-xl border border-rose-500/30 bg-rose-500/10">
            <span class="text-xl">🧱</span>
            <div class="min-w-0">
              <p class="text-sm font-bold truncate">{{ a.username }}</p>
              <p class="text-xs text-rose-500 dark:text-rose-400 truncate">Bloqué·e sur « {{ a.exercise_title }} » ({{ a.attempts }} échecs)</p>
            </div>
          </div>

          <div v-for="(a, i) in inactiveAlerts" :key="'inactive-'+i"
               class="flex items-center gap-3 p-3 rounded-xl border border-amber-500/30 bg-amber-500/10">
            <span class="text-xl">💤</span>
            <div class="min-w-0">
              <p class="text-sm font-bold truncate">{{ a.username }}</p>
              <p class="text-xs text-amber-600 dark:text-amber-400 truncate">Inactif·ve depuis {{ a.days }} jours</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Heatmap -->
      <div :class="['border p-6 rounded-[2rem] shadow-sm transition-all overflow-hidden', isDarkMode ? 'bg-zinc-900/50 border-zinc-800' : 'bg-white border-zinc-200']">
        <h3 :class="['text-xl font-bold tracking-tight flex items-center gap-2 mb-4', isDarkMode ? 'text-zinc-100' : 'text-zinc-800']">
          <span class="text-blue-500">🗺️</span> Vue d'ensemble
        </h3>

        <div v-if="!data.students.length" :class="['text-sm italic', isDarkMode ? 'text-zinc-500' : 'text-zinc-400']">
          Aucun élève.
        </div>

        <div v-else class="overflow-x-auto custom-scrollbar">
          <table class="border-separate" style="border-spacing: 4px;">
            <thead>
              <tr>
                <th :class="['sticky left-0 z-10 text-left text-xs font-black uppercase tracking-widest pr-4 pb-2', isDarkMode ? 'text-zinc-400 bg-zinc-900/50' : 'text-zinc-500 bg-white']">Élève</th>
                <th v-for="ex in data.exercises" :key="ex.id" class="pb-2"></th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="s in data.students" :key="s.username">
                <td :class="['sticky left-0 z-10 text-sm font-bold pr-4 whitespace-nowrap cursor-pointer hover:text-blue-500', isDarkMode ? 'text-zinc-200 bg-zinc-900/50' : 'text-zinc-700 bg-white']"
                    @click="emit('select-student', s.username)">
                  {{ s.prenom || s.nom ? `${s.prenom} ${s.nom}` : s.username }}
                </td>
                <td v-for="ex in data.exercises" :key="ex.id">
                  <div
                    class="relative"
                    @mouseenter="hoveredCell = cellKey(s.username, ex.id)"
                    @mouseleave="hoveredCell = null"
                  >
                    <div
                      v-if="hoveredCell === cellKey(s.username, ex.id)"
                      :class="['absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 px-2 py-1 rounded-lg text-[10px] font-black whitespace-nowrap shadow-lg z-20 pointer-events-none', isDarkMode ? 'bg-zinc-700 text-white' : 'bg-zinc-800 text-white']"
                    >
                      {{ ex.titre }}
                    </div>
                    <div
                      class="w-5 h-5 rounded-md transition-transform hover:scale-125"
                      :class="cellClass(data.heatmap[s.username]?.[ex.id])"
                    ></div>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <div class="flex items-center gap-4 mt-4 text-xs">
          <div class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-emerald-500 inline-block"></span> Réussi</div>
          <div class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-orange-500 inline-block"></span> Réussi (+ de 4 tentatives)</div>
          <div class="flex items-center gap-1.5"><span class="w-3 h-3 rounded bg-rose-500 inline-block"></span> En échec</div>
          <div class="flex items-center gap-1.5"><span :class="['w-3 h-3 rounded inline-block', isDarkMode ? 'bg-zinc-800' : 'bg-zinc-200']"></span> Non commencé</div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Étalonnage des exercices -->
        <div :class="['border p-6 rounded-[2rem] shadow-sm transition-all', isDarkMode ? 'bg-zinc-900/50 border-zinc-800' : 'bg-white border-zinc-200']">
          <h3 :class="['text-xl font-bold tracking-tight flex items-center gap-2 mb-4', isDarkMode ? 'text-zinc-100' : 'text-zinc-800']">
            <span class="text-indigo-500">📏</span> Étalonnage des exercices
          </h3>
          <div class="space-y-2 max-h-96 overflow-y-auto custom-scrollbar pr-2">
            <div v-for="ex in data.exercise_stats" :key="ex.exercise_id"
                 :class="['p-3 rounded-xl border', isDarkMode ? 'bg-zinc-800/40 border-zinc-700/50' : 'bg-zinc-50 border-zinc-100']">
              <div class="flex justify-between items-center mb-1">
                <span class="text-sm font-bold truncate">{{ ex.titre }}</span>
                <span :class="['text-[10px] font-black uppercase px-2 py-0.5 rounded-full', isDarkMode ? 'bg-zinc-700 text-zinc-300' : 'bg-zinc-200 text-zinc-600']">{{ niveauLabel(ex.niveau) }}</span>
              </div>
              <div class="flex flex-wrap gap-x-4 gap-y-1 text-xs">
                <span :class="isDarkMode ? 'text-zinc-400' : 'text-zinc-500'">Réussite : <b :class="ex.success_rate < 40 ? 'text-rose-500' : 'text-emerald-500'">{{ ex.success_rate }}%</b></span>
                <span :class="isDarkMode ? 'text-zinc-400' : 'text-zinc-500'">Tentatives moy. : <b>{{ ex.avg_attempts }}</b></span>
                <span :class="isDarkMode ? 'text-zinc-400' : 'text-zinc-500'">Aide IA moy. : <b>{{ ex.avg_ai_requests }}</b></span>
                <span :class="isDarkMode ? 'text-zinc-400' : 'text-zinc-500'">Élèves ayant essayé : <b>{{ ex.nb_attempters }}</b></span>
              </div>
            </div>
          </div>
        </div>

        <!-- Erreurs fréquentes -->
        <div :class="['border p-6 rounded-[2rem] shadow-sm transition-all', isDarkMode ? 'bg-zinc-900/50 border-zinc-800' : 'bg-white border-zinc-200']">
          <h3 :class="['text-xl font-bold tracking-tight flex items-center gap-2 mb-4', isDarkMode ? 'text-zinc-100' : 'text-zinc-800']">
            <span class="text-rose-500">✨</span> Erreurs fréquentes
          </h3>
          <div v-if="!data.error_distribution.length" :class="['text-sm italic', isDarkMode ? 'text-zinc-500' : 'text-zinc-400']">
            Pas encore assez de données.
          </div>
          <div class="space-y-2">
            <div v-for="err in data.error_distribution" :key="err.type"
                 :class="['flex items-center justify-between p-2.5 rounded-xl border shadow-sm', isDarkMode ? 'bg-zinc-800/30 border-zinc-800' : 'bg-zinc-50 border-zinc-100']">
              <span :class="['text-xs font-mono', isDarkMode ? 'text-zinc-300' : 'text-zinc-600']">{{ err.type }}</span>
              <span :class="['px-2 py-0.5 rounded-lg text-[10px] font-black', isDarkMode ? 'bg-zinc-700 text-zinc-100' : 'bg-zinc-200 text-zinc-700']">{{ err.count }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: #525252 transparent;
}
.custom-scrollbar::-webkit-scrollbar {
  height: 6px;
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #525252;
  border-radius: 3px;
}
</style>
