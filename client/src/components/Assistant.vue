<script setup>
import { ref, computed } from "vue";
import MarkdownIt from "markdown-it";
import DOMPurify from "dompurify";
import { useThemeStore } from "../stores/themeStore";
import { storeToRefs } from "pinia";

const themeStore = useThemeStore();
const { isDarkMode } = storeToRefs(themeStore);

const markdown = new MarkdownIt();
const emit = defineEmits(["isAssistant"]);
const props = defineProps(["msg", "isLoading", "disabled", "active"]);

const toggleAssistant = () => {
  if (props.disabled) return;
  emit("isAssistant", !props.active);
};

const safeRenderedMsg = computed(() => {
  if (!props.msg) return "";
  const rawHtml = markdown.render(props.msg);
  return DOMPurify.sanitize(rawHtml);
});
</script>

<template>
  <div :class="['flex flex-col w-full rounded-2xl p-5 shadow-xl border transition-colors duration-300', isDarkMode ? 'bg-zinc-800/80 border-zinc-700/50' : 'bg-white border-zinc-200']">
    <div :class="['flex items-center gap-4 mb-4 border-b pb-3', isDarkMode ? 'border-zinc-700' : 'border-zinc-100']">
      <img
        src="/assistant.png"
        alt="assistant"
        class="w-8 h-8 md:w-10 md:h-10 transition-all duration-300 transform hover:scale-110 shadow-sm rounded-full"
        :class="
          props.disabled
            ? 'cursor-not-allowed opacity-30 grayscale'
            : 'hover:cursor-pointer'
        "
        @click="toggleAssistant"
      />
      <h2 :class="['font-black tracking-widest text-sm uppercase', isDarkMode ? 'text-zinc-100' : 'text-zinc-800']">ASSISTANT</h2>
      <div v-if="props.active" :class="['ml-auto flex items-center gap-2 text-[10px] font-black px-3 py-1 rounded-full border uppercase', isDarkMode ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-emerald-500/10 text-emerald-600 border-emerald-500/10']">
        <div class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></div>
        Activé
      </div>
    </div>
    
    <div class="flex-1 overflow-hidden flex flex-col relative">
      <transition
        enter-active-class="transition-opacity duration-300"
        enter-from-class="opacity-0"
        enter-to-class="opacity-100"
        leave-active-class="transition-opacity duration-300"
        leave-from-class="opacity-100"
        leave-to-class="opacity-0"
      >
        <div v-show="props.active || props.isLoading" class="flex-1 overflow-y-auto custom-scrollbar relative">
          
          <!-- LLM Loading Skeleton -->
          <div
            v-if="props.isLoading"
            :class="['flex flex-col gap-3 py-4', isDarkMode ? 'text-zinc-300' : 'text-zinc-600']"
          >
             <div class="flex items-center gap-3 mb-2">
                <div class="loader flex-shrink-0"></div>
                <span class="animate-pulse font-medium">Je réfléchis à votre programme...</span>
             </div>
             <div :class="['h-4 rounded animate-pulse w-3/4', isDarkMode ? 'bg-zinc-700' : 'bg-zinc-100']"></div>
             <div :class="['h-4 rounded animate-pulse w-full', isDarkMode ? 'bg-zinc-700' : 'bg-zinc-100']"></div>
             <div :class="['h-4 rounded animate-pulse w-5/6', isDarkMode ? 'bg-zinc-700' : 'bg-zinc-100']"></div>
          </div>
          
          <!-- Message Content -->
          <div
            v-else-if="props.msg"
            :class="['prose prose-sm max-w-none py-2 leading-relaxed font-medium', isDarkMode ? 'prose-invert text-zinc-300' : 'text-zinc-600']"
            v-html="safeRenderedMsg"
          />
        </div>
      </transition>
      
      <!-- Placeholder when Assistant is disabled but panel visible -->
      <div v-if="!props.active && !props.isLoading" :class="['absolute inset-0 flex items-center justify-center text-sm italic py-8 text-center px-6 leading-relaxed select-none', isDarkMode ? 'text-zinc-500' : 'text-zinc-400']">
        <span v-if="props.disabled">L'assistant IA n'est pas disponible pour ce compte.</span>
        <span v-else class="max-w-[200px]">Cliquez sur l'icône pour m'activer et obtenir de l'aide !</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: #d4d4d8 transparent;
}
.dark .custom-scrollbar {
  scrollbar-color: #3f3f46 transparent;
}

.custom-scrollbar::-webkit-scrollbar {
  width: 4px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #e4e4e7;
  border-radius: 10px;
}
.dark .custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #27272a;
}

.loader {
  width: 20px;
  height: 20px;
  border: 2px solid #e2e8f0;
  border-top: 2px solid #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}
.dark .loader {
  border-color: #1e293b;
  border-top-color: #60a5fa;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

:deep(.prose) {
  color: #52525b;
}
.dark :deep(.prose) {
  color: #d1d5db;
}

:deep(.prose code) {
  background-color: #f4f4f5;
  padding: 0.2rem 0.4rem;
  border-radius: 0.25rem;
  font-size: 0.875em;
  color: #2563eb;
  font-weight: 700;
}
.dark :deep(.prose code) {
  background-color: #27272a;
  color: #93c5fd;
}

:deep(.prose pre) {
  background-color: #fafafa;
  border: 1px solid #e4e4e7;
  padding: 1rem;
  border-radius: 0.75rem;
  overflow-x: auto;
}
.dark :deep(.prose pre) {
  background-color: #18181b;
  border-color: #27272a;
}
</style>
