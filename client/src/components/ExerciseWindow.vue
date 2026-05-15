<script setup>
import { computed } from "vue";
import MarkdownIt from "markdown-it";
import DOMPurify from "dompurify";
import { useThemeStore } from "../stores/themeStore";
import { storeToRefs } from "pinia";

const props = defineProps(["exercise", "isLoading", "error"]);
const themeStore = useThemeStore();
const { isDarkMode } = storeToRefs(themeStore);

const markdown = new MarkdownIt();

const safeEnonce = computed(() => {
  if (!props.exercise || !props.exercise.enonce) return "";
  const rawHtml = markdown.render(props.exercise.enonce);
  return DOMPurify.sanitize(rawHtml);
});
</script>

<template>
  <div :class="['w-full h-full flex flex-col overflow-hidden border transition-all duration-300 rounded-2xl', isDarkMode ? 'bg-zinc-950 border-zinc-800' : 'bg-white border-zinc-200']">
    <div
      v-if="isLoading"
      :class="['flex flex-col gap-4 p-8 w-full h-full', isDarkMode ? 'bg-zinc-950' : 'bg-white']"
    >
      <div :class="['h-8 rounded animate-pulse w-1/3 mb-4', isDarkMode ? 'bg-zinc-800' : 'bg-zinc-100']"></div>
      <div :class="['h-4 rounded animate-pulse w-full', isDarkMode ? 'bg-zinc-800' : 'bg-zinc-100']"></div>
      <div :class="['h-4 rounded animate-pulse w-5/6', isDarkMode ? 'bg-zinc-800' : 'bg-zinc-100']"></div>
      <div :class="['h-4 rounded animate-pulse w-4/6', isDarkMode ? 'bg-zinc-800' : 'bg-zinc-100']"></div>
    </div>

    <div
      v-else-if="error"
      :class="['flex items-center justify-center p-8 h-full text-red-500 transition-colors', isDarkMode ? 'bg-red-900/10' : 'bg-red-50']"
    >
      <div class="text-center">
        <svg xmlns="http://www.w3.org/2000/svg" class="h-12 w-12 mx-auto mb-3 opacity-80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        <p class="font-bold tracking-tight">{{ error }}</p>
      </div>
    </div>

    <div
      v-else-if="exercise"
      :class="['p-8 h-full overflow-y-auto custom-scrollbar transition-colors', isDarkMode ? 'bg-zinc-950' : 'bg-white']"
    >
      <div :class="['flex items-center gap-4 mb-6 border-b pb-5', isDarkMode ? 'border-zinc-800' : 'border-zinc-100']">
        <h2 :class="['text-2xl font-black tracking-tight', isDarkMode ? 'text-white' : 'text-zinc-800']">
           {{ props.exercise.title ? props.exercise.title.toUpperCase() : "" }}
        </h2>
        <span :class="['px-3 py-1 text-xs font-black rounded-lg border uppercase tracking-widest', isDarkMode ? 'bg-zinc-800 border-zinc-700 text-zinc-300' : 'bg-zinc-100 border-zinc-200 text-zinc-600']">
           Niveau {{ props.exercise.level || props.exercise.niveau || '...' }}
        </span>
      </div>
      <div :class="['prose prose-sm max-w-none transition-all duration-300', isDarkMode ? 'prose-invert' : '']">
        <div
          v-if="props.exercise.enonce"
          :class="[isDarkMode ? 'text-zinc-300' : 'text-zinc-600']"
          v-html="safeEnonce"
        />
      </div>
    </div>

    <div
      v-else
      :class="['p-8 h-full overflow-y-auto custom-scrollbar flex flex-col max-w-3xl mx-auto transition-colors', isDarkMode ? 'bg-zinc-950' : 'bg-white']"
    >
      <div :class="['my-auto space-y-6 text-lg leading-relaxed', isDarkMode ? 'text-zinc-300' : 'text-zinc-600']">
        <p class="text-justify font-medium">
          EXOPY va vous permettre d'améliorer vos compétences en programmation Python. 
        </p>

        <div :class="['p-6 rounded-2xl border shadow-sm transition-colors', isDarkMode ? 'bg-zinc-900/40 border-zinc-700/60 shadow-inner' : 'bg-zinc-50 border-zinc-200']">
          <h3 :class="['font-black mb-4 uppercase tracking-widest text-sm text-center md:text-left', isDarkMode ? 'text-white' : 'text-zinc-800']">Comment ça marche ?</h3>
          <ul class="space-y-3 text-base font-medium">
            <li class="flex items-center gap-3">
              <span class="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px] font-black">1</span>
              <span>Sélectionnez un exercice dans le menu latéral.</span>
            </li>
            <li class="flex items-center gap-3">
              <span class="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px] font-black">2</span>
              <span>Utilisez l'éditeur de code pour saisir votre solution.</span>
            </li>
            <li class="flex items-center gap-3">
              <span class="w-6 h-6 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px] font-black">3</span>
              <span class="flex items-center gap-2">
                Consultez l'assistant 
                <div :class="['p-1 rounded-full border', isDarkMode ? 'bg-zinc-800 border-zinc-600' : 'bg-white border-zinc-200']">
                  <img src="/assistant.png" alt="logo" class="w-5 h-5" />
                </div>
                pour obtenir de l'aide interactive.
              </span>
            </li>
          </ul>
        </div>

        <div class="pt-4">
          <p :class="['mb-5 text-center font-black uppercase tracking-[0.3em] text-[10px]', isDarkMode ? 'text-zinc-500' : 'text-zinc-400']">LÉGENDE DES NIVEAUX</p>
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
            <div :class="['flex flex-col items-center p-3 rounded-xl border shadow-sm', isDarkMode ? 'bg-zinc-800 border-zinc-700' : 'bg-white border-zinc-100']">
              <div class="bg-green-600 w-3 h-3 rounded-full mb-2"></div>
              <span class="font-bold uppercase tracking-widest text-[9px]">Très facile</span>
            </div>
            <div :class="['flex flex-col items-center p-3 rounded-xl border shadow-sm', isDarkMode ? 'bg-zinc-800 border-zinc-700' : 'bg-white border-zinc-100']">
              <div class="bg-blue-600 w-3 h-3 rounded-full mb-2"></div>
              <span class="font-bold uppercase tracking-widest text-[9px]">Intermédiaire</span>
            </div>
            <div :class="['flex flex-col items-center p-3 rounded-xl border shadow-sm', isDarkMode ? 'bg-zinc-800 border-zinc-700' : 'bg-white border-zinc-100']">
              <div class="bg-red-600 w-3 h-3 rounded-full mb-2"></div>
              <span class="font-bold uppercase tracking-widest text-[9px]">Avancé</span>
            </div>
            <div :class="['flex flex-col items-center p-3 rounded-xl border shadow-sm', isDarkMode ? 'bg-zinc-800 border-zinc-700' : 'bg-white border-zinc-100']">
              <div class="bg-black w-3 h-3 rounded-full mb-2"></div>
              <span class="font-bold uppercase tracking-widest text-[9px]">Expert</span>
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
