<script setup>
import { ref } from "vue";
import CodeMirror from "vue-codemirror6";
import { python } from "@codemirror/lang-python";
import { keymap, EditorView } from "@codemirror/view";
import { indentWithTab } from "@codemirror/commands";
import { oneDark } from "@codemirror/theme-one-dark";
import { useThemeStore } from "../stores/themeStore";
import { storeToRefs } from "pinia";
import { computed } from "vue";

const props = defineProps(["exercise"]);
const emit = defineEmits(["sendCode"]);
const code = ref("");
const isdisabled = ref(false);
const isFullscreen = ref(false);

import { watch } from "vue";
watch(
  () => props.exercise,
  () => {
    code.value = "";
  },
);

const themeStore = useThemeStore();
const { isDarkMode } = storeToRefs(themeStore);

const tabConfig = keymap.of([indentWithTab]);

const editorExtensions = computed(() => {
  const exts = [tabConfig, python(), EditorView.lineWrapping];
  if (isDarkMode.value) {
    exts.push(oneDark);
  }
  return exts;
});

const updateCode = () => {
  isdisabled.value = true;
  emit("sendCode", code.value);
  setTimeout(() => {
    isdisabled.value = false;
  }, 8000);
};

const toggleFullscreen = () => {
  isFullscreen.value = !isFullscreen.value;
};
</script>

<template>
  <div>
    <div :class="['w-full h-80 overflow-hidden rounded-2xl border transition-all shadow-inner', isDarkMode ? 'bg-zinc-900 border-zinc-950/50' : 'bg-[#f8f8f8] border-zinc-200']">
      <CodeMirror
        v-model="code"
        :lang="python()"
        :basic="true"
        :extensions="editorExtensions"
      />
    </div>
    <div class="flex items-start w-full ml-10 mt-4">
      <div class="flex-1 flex justify-start">
        <button
          v-if="exercise"
          :disabled="isdisabled"
          class="px-8 py-2.5 rounded-xl font-black text-xs uppercase tracking-widest transition-all duration-300 shadow-lg"
          :class="isdisabled 
            ? 'bg-zinc-200 dark:bg-zinc-800 text-zinc-400 dark:text-zinc-600 cursor-not-allowed' 
            : 'bg-blue-600 hover:bg-blue-500 text-white shadow-blue-500/20 hover:shadow-blue-500/40 hover:-translate-y-0.5 active:translate-y-0 hover:cursor-pointer'"
          @click="updateCode"
        >
          Envoyer
        </button>
        <button
          v-if="exercise"
          @click="toggleFullscreen"
          class="ml-6 text-zinc-400 dark:text-zinc-500 hover:text-blue-600 dark:hover:text-blue-400 transition-all hover:scale-110 hover:cursor-pointer p-2 rounded-xl bg-white dark:bg-transparent shadow-sm dark:shadow-none border border-zinc-100 dark:border-transparent"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-6 w-6"
            viewBox="0 0 20 20"
            fill="currentColor"
          >
            <path
              fill-rule="evenodd"
              d="M3 4a1 1 0 011-1h4a1 1 0 010 2H6.414l2.293 2.293a1 1 0 11-1.414 1.414L5 6.414V8a1 1 0 01-2 0V4zm9 1a1 1 0 010-2h4a1 1 0 011 1v4a1 1 0 01-2 0V6.414l-2.293 2.293a1 1 0 11-1.414-1.414L13.586 5H12zm-9 7a1 1 0 012 0v1.586l2.293-2.293a1 1 0 111.414 1.414L6.414 15H8a1 1 0 010 2H4a1 1 0 01-1-1v-4zm13-1a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 010-2h1.586l-2.293-2.293a1 1 0 111.414-1.414L15 13.586V12a1 1 0 011-1z"
              clip-rule="evenodd"
            />
          </svg>
        </button>
      </div>
    </div>
    <div
      v-if="isFullscreen"
      :class="['fixed inset-0 z-[100] w-full h-screen flex flex-col p-8 transition-colors duration-300', isDarkMode ? 'bg-zinc-900' : 'bg-slate-50']"
    >
      <div class="flex justify-between items-center mb-10">
        <button
          @click="toggleFullscreen"
          :class="['p-3 rounded-2xl transition-all hover:scale-110 shadow-lg', isDarkMode ? 'bg-zinc-800 text-zinc-400 hover:text-red-400' : 'bg-white text-zinc-400 hover:text-red-500 border border-zinc-100']"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-8 w-8" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>
      <div :class="['flex-1 overflow-hidden rounded-[2.5rem] border shadow-2xl', isDarkMode ? 'bg-zinc-950 border-black shadow-black/40' : 'bg-white border-zinc-200 shadow-zinc-300/50']">
        <CodeMirror
          v-model="code"
          :lang="python()"
          :basic="true"
          :extensions="editorExtensions"
          :style="{ fontSize: '24px', height: '100%' }"
        />
      </div>
    </div>
  </div>
</template>

<style scoped>
:deep(.cm-editor) {
  height: 100%;
  font-family: monospace;
}
</style>
