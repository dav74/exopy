<script setup>
import { ref, computed } from "vue";

const props = defineProps({
  isDarkMode: { type: Boolean, default: false },
  selectedFields: { type: Array, default: () => [] },
  showAdminField: { type: Boolean, default: false },
});
const emit = defineEmits(["close", "apply"]);

const local = ref(new Set(props.selectedFields));

const isChecked = (key) => local.value.has(key);
const toggle = (key) => {
  const next = new Set(local.value);
  if (next.has(key)) next.delete(key);
  else next.add(key);
  local.value = next;
};

const adminField = { key: "admin", label: "Identifiant de l'enseignant (admin)" };

const progressFields = [
  { key: "exercise_id", label: "Identifiant de l'exercice" },
  { key: "exercise_titre", label: "Titre de l'exercice" },
  { key: "niveau", label: "Niveau de difficulté" },
  { key: "status", label: "Statut (réussite / échec)" },
  { key: "error_type", label: "Type d'erreur Python" },
  { key: "duration", label: "Durée depuis la dernière action" },
  { key: "ai_used", label: "Assistant IA sollicité (oui/non)" },
  { key: "ai_disabled", label: "Assistant IA désactivé par le prof (oui/non)" },
  { key: "niveau_eleve", label: "Niveau scolaire de l'élève (Terminale/Première)" },
];

const visibleProgressFields = computed(() => props.showAdminField ? [adminField, ...progressFields] : progressFields);

const sensitiveFields = [
  { key: "code", label: "Code proposé par l'élève" },
  { key: "ai_response", label: "Réponse de l'assistant IA", hint: "Vide si l'assistant n'a pas été sollicité pour cette tentative." },
];

const apply = () => {
  emit("apply", Array.from(local.value));
  emit("close");
};
</script>

<template>
  <div class="fixed inset-0 z-[200] flex items-center justify-center overflow-hidden p-4">
    <div class="absolute inset-0 bg-black/70 backdrop-blur-sm" @click="emit('close')"></div>

    <div
      :class="['relative z-10 w-full max-w-2xl max-h-[85vh] rounded-[2.5rem] shadow-2xl border overflow-hidden animate-in fade-in zoom-in slide-in-from-bottom-8 duration-300 flex flex-col', isDarkMode ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200']"
    >
      <div :class="['flex items-center justify-between px-8 py-6 border-b flex-shrink-0', isDarkMode ? 'border-zinc-800' : 'border-zinc-100']">
        <div>
          <h2 :class="['text-xl font-black tracking-tight', isDarkMode ? 'text-white' : 'text-zinc-900']">Choisir les champs à exporter</h2>
          <p :class="['text-xs font-medium mt-1', isDarkMode ? 'text-zinc-400' : 'text-zinc-500']">Ces champs seront inclus dans le prochain export.</p>
        </div>
        <button
          @click="emit('close')"
          :class="['p-2.5 rounded-2xl transition-all hover:scale-110 shadow-sm flex-shrink-0', isDarkMode ? 'bg-zinc-800 text-zinc-400 hover:text-red-400' : 'bg-zinc-50 text-zinc-400 hover:text-red-500 border border-zinc-100']"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
      </div>

      <div class="px-8 py-6 overflow-y-auto custom-scrollbar space-y-8 flex-1">
        <div>
          <h3 :class="['text-sm font-black uppercase tracking-widest mb-3', isDarkMode ? 'text-zinc-300' : 'text-zinc-600']">Toujours inclus</h3>
          <div class="space-y-2">
            <div v-for="f in [{ label: 'Identifiant pseudonymisé de l\'élève' }, { label: 'Date et heure exactes' }]" :key="f.label"
                 :class="['flex items-center justify-between gap-4 p-3 rounded-xl border', isDarkMode ? 'bg-zinc-800/50 border-zinc-800' : 'bg-zinc-50 border-zinc-100']">
              <span :class="['text-sm font-medium', isDarkMode ? 'text-zinc-400' : 'text-zinc-500']">{{ f.label }}</span>
              <span :class="['text-[9px] font-black uppercase tracking-widest px-2 py-1 rounded-full', isDarkMode ? 'bg-zinc-700 text-zinc-400' : 'bg-zinc-200 text-zinc-500']">Toujours</span>
            </div>
          </div>
        </div>

        <div>
          <h3 :class="['text-sm font-black uppercase tracking-widest mb-1', isDarkMode ? 'text-zinc-300' : 'text-zinc-600']">Tentatives de soumission</h3>
          <p :class="['text-[11px] font-mono mb-3', isDarkMode ? 'text-zinc-600' : 'text-zinc-400']">→ fichier progress_events.csv</p>
          <div class="space-y-2">
            <div v-for="f in visibleProgressFields" :key="f.key"
                 :class="['flex items-center justify-between gap-4 p-3 rounded-xl border cursor-pointer transition-colors', isDarkMode ? 'bg-zinc-800/50 border-zinc-800 hover:bg-zinc-800' : 'bg-zinc-50 border-zinc-100 hover:bg-zinc-100']"
                 @click="toggle(f.key)">
              <div>
                <span :class="['text-sm font-bold', isDarkMode ? 'text-zinc-200' : 'text-zinc-700']">{{ f.label }}</span>
                <p v-if="f.hint" :class="['text-[11px] mt-0.5', isDarkMode ? 'text-zinc-500' : 'text-zinc-400']">{{ f.hint }}</p>
              </div>
              <div class="relative inline-flex items-center cursor-pointer flex-shrink-0" @click.stop="toggle(f.key)">
                <input type="checkbox" :checked="isChecked(f.key)" class="sr-only peer" tabindex="-1">
                <div class="w-11 h-6 bg-zinc-200 dark:bg-zinc-700 rounded-full peer peer-checked:bg-blue-600 transition-colors"></div>
                <div class="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
              </div>
            </div>
          </div>
        </div>

        <div>
          <h3 class="text-sm font-black uppercase tracking-widest mb-3 text-amber-500">⚠️ Données sensibles (texte brut)</h3>
          <p :class="['text-xs leading-relaxed mb-3', isDarkMode ? 'text-zinc-400' : 'text-zinc-500']">
            Le code écrit par l'élève et les réponses de l'assistant peuvent contenir des noms ou d'autres informations identifiantes en commentaire. À relire avant toute diffusion externe.
          </p>
          <div class="space-y-2">
            <div v-for="f in sensitiveFields" :key="f.key"
                 :class="['flex items-center justify-between gap-4 p-3 rounded-xl border cursor-pointer transition-colors', isDarkMode ? 'bg-amber-500/5 border-amber-500/20 hover:bg-amber-500/10' : 'bg-amber-50 border-amber-200 hover:bg-amber-100']"
                 @click="toggle(f.key)">
              <div>
                <span :class="['text-sm font-bold', isDarkMode ? 'text-zinc-200' : 'text-zinc-700']">{{ f.label }}</span>
                <p v-if="f.hint" :class="['text-[11px] mt-0.5', isDarkMode ? 'text-zinc-500' : 'text-zinc-400']">{{ f.hint }}</p>
              </div>
              <div class="relative inline-flex items-center cursor-pointer flex-shrink-0" @click.stop="toggle(f.key)">
                <input type="checkbox" :checked="isChecked(f.key)" class="sr-only peer" tabindex="-1">
                <div class="w-11 h-6 bg-zinc-200 dark:bg-zinc-700 rounded-full peer peer-checked:bg-amber-500 transition-colors"></div>
                <div class="absolute left-1 top-1 w-4 h-4 bg-white rounded-full transition-transform peer-checked:translate-x-5"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div :class="['px-8 py-6 border-t flex-shrink-0', isDarkMode ? 'border-zinc-800' : 'border-zinc-100']">
        <button
          @click="apply"
          class="w-full py-4 rounded-2xl font-black text-xs text-white bg-blue-600 hover:bg-blue-500 transition-all shadow-xl shadow-blue-500/20 uppercase tracking-[0.2em]"
        >
          Appliquer
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: #3f3f46 #f4f4f5;
}
.custom-scrollbar::-webkit-scrollbar {
  width: 8px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #d4d4d8;
  border-radius: 20px;
}
</style>
