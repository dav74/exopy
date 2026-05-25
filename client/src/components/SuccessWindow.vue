<script setup>
import { ref, nextTick } from "vue";
import MarkdownIt from "markdown-it";

const props = defineProps(["msg", "title", "assistantOn"]);
const markdown = new MarkdownIt();
const emit = defineEmits(["close"]);
const isVisible = ref(false);
const confetti = ref([]);

const showSuccess = () => {
  // Generate confetti first so they are ready
  confetti.value = Array.from({ length: 80 }).map(() => ({
    id: Math.random(),
    style: getRandomConfettiStyle()
  }));
  
  isVisible.value = true;
};

const hideSuccess = () => {
  isVisible.value = false;
  confetti.value = [];
  emit("close");
};

const getRandomConfettiStyle = () => {
  const colors = ["#60a5fa", "#34d399", "#fbbf24", "#f87171", "#a78bfa", "#f472b6"];
  const color = colors[Math.floor(Math.random() * colors.length)];
  
  const angle = Math.random() * Math.PI * 2;
  const velocity = 15 + Math.random() * 45;
  const size = 10 + Math.random() * 15;
  const duration = 2.5 + Math.random() * 2;
  const rotation = Math.random() * 360;

  return {
    "--color": color,
    "--size": `${size}px`,
    "--duration": `${duration}s`,
    "--tx": `${Math.cos(angle) * velocity * 15}px`,
    "--ty": `${Math.sin(angle) * velocity * 15 - 300}px`,
    "--rot": `${rotation + 1080}deg`
  };
};

defineExpose({
  showSuccess,
  hideSuccess,
});
</script>

<template>
  <Transition name="modal">
    <div
      v-if="isVisible"
      class="fixed inset-0 flex items-center justify-center z-[100] p-4 pointer-events-none"
    >
      <!-- Overlay flou (Glassmorphism backdrop) -->
      <div class="absolute inset-0 bg-black/60 backdrop-blur-md pointer-events-auto" @click="hideSuccess"></div>

      <!-- Teleport Confetti to body to be sure they are on top -->
      <Teleport to="body">
        <div v-if="isVisible && confetti.length > 0" class="confetti-container">
          <div
            v-for="p in confetti"
            :key="p.id"
            class="confetti-piece"
            :style="p.style"
          ></div>
        </div>
      </Teleport>

      <!-- Modal Card (Glassmorphism) -->
      <div
        class="relative bg-white/95 dark:bg-zinc-900/95 border border-white/20 dark:border-white/10 backdrop-blur-2xl p-10 md:p-14 rounded-[3rem] shadow-[0_40px_100px_rgba(0,0,0,0.3)] dark:shadow-[0_40px_100px_rgba(0,0,0,0.7)] max-w-2xl w-full z-50 overflow-hidden pointer-events-auto transition-colors duration-500"
      >
        <!-- Subtle gradient glow -->
        <div class="absolute -top-32 -left-32 w-64 h-64 bg-blue-600/20 dark:bg-blue-600/30 blur-[100px] rounded-full"></div>
        <div class="absolute -bottom-32 -right-32 w-64 h-64 bg-green-600/20 dark:bg-green-600/30 blur-[100px] rounded-full"></div>

        <div class="text-center relative">
          <!-- Animated Checkmark Icon -->
          <div class="w-24 h-24 mx-auto mb-10 relative">
            <div class="absolute inset-0 bg-green-500/20 rounded-full animate-ping opacity-30"></div>
            <div class="relative bg-gradient-to-tr from-green-600 to-green-400 rounded-full p-5 shadow-xl shadow-green-500/30 ring-8 ring-green-500/10">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="text-white drop-shadow-md w-full h-full"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="3"
                stroke-linecap="round"
                stroke-linejoin="round"
              >
                <polyline points="20 6 9 17 4 12" class="checkmark-draw"></polyline>
              </svg>
            </div>
          </div>

          <h2 class="text-4xl font-black mb-8 tracking-tighter bg-clip-text text-transparent bg-gradient-to-b from-zinc-800 to-zinc-500 dark:from-white dark:to-zinc-500 leading-tight italic">
            {{ props.title || "Félicitations !" }}
          </h2>

          <div class="overflow-y-auto max-h-[40vh] custom-scrollbar mb-10 px-4">
            <div
              class="text-zinc-700 dark:text-zinc-100 text-xl leading-relaxed text-center font-medium"
              v-if="props.msg"
              v-html="markdown.render(props.msg)"
            ></div>
            <div
              v-else-if="props.assistantOn"
              class="flex flex-col items-center justify-center py-8 gap-6"
            >
              <div class="premium-loader"></div>
              <span class="text-blue-600 dark:text-zinc-400 font-black animate-pulse tracking-[0.3em] text-[10px] uppercase">Analyse IA en cours...</span>
            </div>
            <div
              v-else
              class="text-zinc-400 dark:text-zinc-500 italic text-lg font-medium"
            >
              Excellent travail ! Vous avez brillamment résolu l'exercice.
            </div>
          </div>

          <button
            @click="hideSuccess"
            class="group relative inline-flex items-center justify-center px-12 py-5 font-black text-xs text-white transition-all duration-300 bg-blue-600 uppercase tracking-[0.2em] rounded-2xl focus:outline-none shadow-2xl shadow-blue-500/40 hover:bg-blue-500 hover:scale-105 active:scale-95 border border-blue-400/20"
          >
            Continuer l'aventure
          </button>
        </div>
      </div>
    </div>
  </Transition>
</template>

<style scoped>
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: #3f3f46 transparent;
}
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #3f3f46;
  border-radius: 10px;
}

/* Modal Transitions */
.modal-enter-active,
.modal-leave-active {
  transition: all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.modal-enter-from {
  opacity: 0;
  transform: scale(0.8) translateY(20px);
}

.modal-leave-to {
  opacity: 0;
  transform: scale(0.9) translateY(10px);
}

/* Checkmark Animation */
.checkmark-draw {
  stroke-dasharray: 40;
  stroke-dashoffset: 40;
  animation: draw 0.8s ease-out forwards 0.4s;
}

@keyframes draw {
  to {
    stroke-dashoffset: 0;
  }
}

/* Premium Loader */
.premium-loader {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(255, 255, 255, 0.1);
  border-left-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

:deep(p) {
  margin-bottom: 1rem;
}

:deep(strong) {
  color: #fbbf24;
}

:deep(code) {
  background: rgba(255, 255, 255, 0.1);
  padding: 0.2rem 0.4rem;
  border-radius: 0.4rem;
  font-family: monospace;
  color: #a78bfa;
}
</style>

<style>
/* Global Confetti Styles (outside scoped because of Teleport) */
.confetti-container {
  position: fixed;
  top: 50%;
  left: 50%;
  width: 1px;
  height: 1px;
  pointer-events: none;
  z-index: 9999;
}

.confetti-piece {
  position: absolute;
  width: var(--size);
  height: var(--size);
  background: var(--color);
  border-radius: 4px;
  opacity: 0;
  animation: explode var(--duration) cubic-bezier(0.1, 0.8, 0.3, 1) forwards;
  box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}

@keyframes explode {
  0% {
    transform: translate(0, 0) rotate(0deg);
    opacity: 1;
  }
  70% {
    opacity: 1;
  }
  100% {
    transform: translate(var(--tx), var(--ty)) rotate(var(--rot));
    opacity: 0;
  }
}
</style>

