import { defineStore } from 'pinia';
import { ref, watch } from 'vue';

export const useThemeStore = defineStore('theme', () => {
  const isDarkMode = ref(localStorage.getItem('theme') !== 'light');

  const toggleTheme = () => {
    isDarkMode.value = !isDarkMode.value;
    localStorage.setItem('theme', isDarkMode.value ? 'dark' : 'light');
    updateTheme();
  };

  const updateTheme = () => {
    if (isDarkMode.value) {
      document.documentElement.classList.add('dark');
      document.body.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
      document.body.classList.remove('dark');
    }
  };

  // Initialize theme
  updateTheme();

  return {
    isDarkMode,
    toggleTheme,
    updateTheme
  };
});
