<script setup>
import { ref } from "vue";
import { API_URL } from "../config.js";

const identifiant = ref("");
const mdp = ref("");
const isIncorrect = ref(false);
const isLoading = ref(false);
const emit = defineEmits(["idCorrect"]);

async function handleLogin() {
  isIncorrect.value = false;
  isLoading.value = true;
  try {
    const params = new URLSearchParams();
    params.append("username", identifiant.value);
    params.append("password", mdp.value);
    const response = await fetch(`${API_URL}/auth/login`, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
      body: params,
    });

    if (response.ok) {
      const data = await response.json();
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("username", identifiant.value);
      emit("idCorrect", identifiant.value);
    } else {
      isIncorrect.value = true;
    }
  } catch (err) {
    console.error("Erreur lors de la connexion:", err);
    isIncorrect.value = true;
  } finally {
    isLoading.value = false;
  }
}

async function handleGuestLogin() {
  isLoading.value = true;
  try {
    const response = await fetch(`${API_URL}/auth/login/guest`, {
      method: "POST",
    });

    if (response.ok) {
      const data = await response.json();
      localStorage.setItem("access_token", data.access_token);
      localStorage.setItem("username", "Invité");
      emit("idCorrect", "Invité");
    } else {
      console.error("Erreur lors de la connexion invité");
    }
  } catch (err) {
    console.error("Erreur réseau lors de la connexion invité:", err);
  } finally {
    isLoading.value = false;
  }
}
</script>
<template>
  <div class="fixed inset-0 flex items-center justify-center overflow-hidden">
    <!-- Background Layer with Image -->
    <div 
      class="absolute inset-0 bg-cover bg-center bg-no-repeat transition-transform duration-1000 scale-105"
      style="background-image: url('/src/assets/login_bg.png'); filter: grayscale(1) brightness(0.4);"
    ></div>
    
    <!-- Glassmorphic Login Card -->
    <div class="relative z-10 w-full max-w-[440px] px-6">
      <div 
        class="bg-black/60 backdrop-blur-3xl p-10 rounded-[3rem] border border-white/10 shadow-2xl animate-in fade-in zoom-in slide-in-from-bottom-8 duration-700"
      >
        <!-- Logo Section -->
        <div class="flex flex-col items-center mb-10">
          <img 
            src="../assets/logo.png" 
            alt="EXOPY" 
            class="w-56 mx-auto filter drop-shadow-[0_0_10px_rgba(255,255,255,0.1)] transform hover:scale-105 transition-transform duration-500" 
          />
        </div>

        <form @submit.prevent="handleLogin" class="space-y-6">
          <div class="space-y-3">
            <label class="block text-[10px] font-black text-white uppercase tracking-widest ml-1" for="identifiant">
              Identifiant
            </label>
            <div class="relative group">
              <input
                v-model="identifiant"
                id="identifiant"
                type="text"
                class="w-full px-6 py-4 bg-white/5 border border-white/10 rounded-2xl text-white font-medium focus:outline-none focus:ring-1 focus:ring-white/30 focus:bg-white/10 transition-all placeholder:text-white/60"
                required
                placeholder="votre login"
              />
            </div>
          </div>

          <div class="space-y-3">
            <label class="block text-[10px] font-black text-white uppercase tracking-widest ml-1" for="mdp">
              Mot de passe
            </label>
            <div class="relative group">
              <input
                v-model="mdp"
                id="mdp"
                type="password"
                class="w-full px-6 py-4 bg-white/5 border border-white/10 rounded-2xl text-white font-medium focus:outline-none focus:ring-1 focus:ring-white/30 focus:bg-white/10 transition-all placeholder:text-white/60"
                required
                placeholder="••••••••"
              />
            </div>
          </div>

          <div class="h-6 flex items-center justify-center">
            <Transition name="fade">
              <span v-if="isIncorrect" class="text-white text-[10px] font-black uppercase tracking-widest bg-white/10 px-4 py-1.5 rounded-full border border-white/20">
                ⚠️ Identifiants incorrects
              </span>
            </Transition>
          </div>

          <button
            type="submit"
            :disabled="isLoading"
            class="w-full bg-white text-black py-4 rounded-2xl font-black text-xs uppercase tracking-[0.2em] shadow-xl hover:bg-zinc-200 hover:scale-[1.01] active:scale-[0.99] transition-all disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <template v-if="isLoading">
              <div class="animate-spin h-4 w-4 border-2 border-black/30 border-t-black rounded-full"></div>
              <span>Connexion...</span>
            </template>
            <span v-else>Se connecter</span>
          </button>
          
          <div class="relative flex items-center py-2">
            <div class="flex-grow border-t border-white/10"></div>
            <span class="flex-shrink mx-4 text-white/20 text-[10px] font-black uppercase tracking-[0.3em]">ou</span>
            <div class="flex-grow border-t border-white/10"></div>
          </div>
          
          <button
            @click.prevent="handleGuestLogin"
            :disabled="isLoading"
            class="w-full bg-white/5 text-white/80 py-4 rounded-2xl font-bold text-[10px] uppercase tracking-[0.2em] border border-white/10 hover:bg-white/10 hover:text-white transition-all shadow-lg"
          >
            Continuer sans compte
          </button>
        </form>
      </div>
    </div>

    <!-- Footer Decoration -->
    <div class="absolute bottom-8 left-1/2 -translate-x-1/2 text-[10px] font-black text-white/30 uppercase tracking-[0.5em] pointer-events-none">
      Advanced Coding Environment
    </div>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(-5px);
}
</style>
