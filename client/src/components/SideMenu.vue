<script setup>
import { ref, onMounted } from "vue";
import { useExerciseStore } from "../stores/exerciseStore";
import { storeToRefs } from "pinia";
import { useThemeStore } from "../stores/themeStore";
import { API_URL } from "../config.js";

const exerciseStore = useExerciseStore();
const themeStore = useThemeStore();
const { selectedItemId, menuItems, isLoadingMenu } = storeToRefs(exerciseStore);
const { isDarkMode } = storeToRefs(themeStore);

const error = ref(null);
const emit = defineEmits(["select-item"]);

const handleItemClick = (item) => {
  emit("select-item", item.id);
};

onMounted(() => {
  exerciseStore.fetchMenuItems(API_URL);
});
</script>

<template>
  <aside 
    :class="['h-screen border-r flex flex-col shadow-xl transition-all duration-300 w-64', 
             isDarkMode ? 'bg-zinc-950 border-zinc-800/50' : 'bg-white border-zinc-200']"
  >
    <div class="flex flex-col h-full">
      <div class="flex-1 overflow-y-auto custom-scrollbar">
        <div v-if="isLoadingMenu" class="flex justify-center items-center py-8">
          <div
            class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"
          ></div>
        </div>
        <div v-else-if="error" class="text-red-500 text-center py-8 px-4">
          <p class="mb-4 text-sm font-medium">{{ error }}</p>
          <button
            @click="exerciseStore.fetchMenuItems(API_URL)"
            :class="['text-xs px-4 py-2 rounded-xl transition-colors font-bold uppercase tracking-widest border',
                     isDarkMode ? 'bg-zinc-800 hover:bg-zinc-700 text-zinc-300 border-zinc-700' : 'bg-zinc-100 hover:bg-zinc-200 text-zinc-600 border-zinc-200']"
          >
            Réessayer
          </button>
        </div>
        <nav v-else class="p-4">
          <ul class="space-y-1 pb-24">
            <li v-for="(item, index) in menuItems" :key="index">
              <button
                @click="handleItemClick(item)"
                class="w-full flex items-center justify-start p-2 rounded-xl transition-all duration-200 group relative overflow-hidden"
                :class="selectedItemId === item.id 
                  ? [isDarkMode ? 'bg-blue-600/10 text-blue-300 border-blue-500/20 shadow-blue-900/10' : 'bg-blue-50 text-blue-600 border-blue-100 shadow-sm'] 
                  : [isDarkMode ? 'text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-100' : 'text-zinc-500 hover:bg-zinc-100 hover:text-zinc-900', 'border border-transparent']"
              >
                <!-- Subtle indicator for selected item -->
                <div v-if="selectedItemId === item.id" class="absolute left-0 top-0 bottom-0 w-1 bg-blue-600 dark:bg-blue-500 rounded-r-full"></div>

                <div 
                  class="min-w-7 h-7 flex justify-center items-center rounded-md font-black text-[10px] shadow-sm transition-transform group-hover:scale-110"
                  :class="{
                    'bg-green-600 text-white': item.niveau == 1,
                    'bg-blue-600 text-white': item.niveau == 2,
                    'bg-red-600 text-white': item.niveau == 3,
                    'bg-zinc-950 text-white border border-white/20': item.niveau == 4
                  }"
                >
                  {{ index + 1 }}
                </div>
                <span class="truncate ml-3 text-sm font-bold tracking-tight min-w-0">{{ item.title }}</span>
                
                <!-- Completed indicator -->
                <div v-if="item.completed" class="ml-auto flex-shrink-0 pl-2">
                  <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 text-green-500" viewBox="0 0 20 20" fill="currentColor">
                    <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
                  </svg>
                </div>
              </button>
            </li>
          </ul>
        </nav>
      </div>
    </div>
  </aside>
</template>

<style>
/* Styles pour la barre de défilement */
.overflow-y-auto {
  scrollbar-width: thin;
  scrollbar-color: #3f3f46 transparent;
}

.overflow-y-auto::-webkit-scrollbar {
  width: 4px;
}

.overflow-y-auto::-webkit-scrollbar-track {
  background: transparent;
}

.overflow-y-auto::-webkit-scrollbar-thumb {
  background-color: #27272a;
  border-radius: 10px;
}

.overflow-y-auto::-webkit-scrollbar-thumb:hover {
  background-color: #3f3f46;
}
</style>
