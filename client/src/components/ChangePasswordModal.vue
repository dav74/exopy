<script setup>
import { ref } from "vue";
import { API_URL } from "../config.js";

defineProps({
  closable: { type: Boolean, default: false },
});

const currentPassword = ref("");
const newPassword = ref("");
const confirmPassword = ref("");
const errorMsg = ref("");
const isLoading = ref(false);
const emit = defineEmits(["changed", "close"]);

async function handleSubmit() {
  errorMsg.value = "";

  if (newPassword.value.length < 6) {
    errorMsg.value = "Le nouveau mot de passe doit contenir au moins 6 caractères.";
    return;
  }
  if (newPassword.value !== confirmPassword.value) {
    errorMsg.value = "Les mots de passe ne correspondent pas.";
    return;
  }

  isLoading.value = true;
  try {
    const token = localStorage.getItem("access_token");
    const response = await fetch(`${API_URL}/auth/password`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        current_password: currentPassword.value,
        new_password: newPassword.value,
      }),
    });

    if (response.ok) {
      emit("changed");
    } else {
      const data = await response.json().catch(() => ({}));
      errorMsg.value = data.detail || "Erreur lors de la mise à jour du mot de passe.";
    }
  } catch (err) {
    console.error("Erreur lors du changement de mot de passe:", err);
    errorMsg.value = "Erreur réseau. Réessayez.";
  } finally {
    isLoading.value = false;
  }
}
</script>

<template>
  <div class="fixed inset-0 z-[200] flex items-center justify-center overflow-hidden">
    <div class="absolute inset-0 bg-black/70 backdrop-blur-sm"></div>

    <div class="relative z-10 w-full max-w-[440px] px-6">
      <div class="relative bg-zinc-900 p-10 rounded-[3rem] border border-white/10 shadow-2xl animate-in fade-in zoom-in slide-in-from-bottom-8 duration-500">
        <button
          v-if="closable"
          @click="emit('close')"
          class="absolute top-6 right-6 p-2 text-white/40 hover:text-white transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>

        <div class="text-center mb-8">
          <h1 class="text-xl font-black text-white uppercase tracking-widest">
            {{ closable ? "Modifier le mot de passe" : "Nouveau mot de passe requis" }}
          </h1>
          <p class="text-sm text-white/60 mt-3">
            {{ closable ? "Choisissez un nouveau mot de passe." : "Pour des raisons de sécurité, vous devez choisir un nouveau mot de passe avant de continuer." }}
          </p>
        </div>

        <form @submit.prevent="handleSubmit" class="space-y-5">
          <div class="space-y-3">
            <label class="block text-[10px] font-black text-white uppercase tracking-widest ml-1" for="current-password">
              Mot de passe actuel
            </label>
            <input
              v-model="currentPassword"
              id="current-password"
              type="password"
              class="w-full px-6 py-4 bg-white/5 border border-white/10 rounded-2xl text-white font-medium focus:outline-none focus:ring-1 focus:ring-white/30 focus:bg-white/10 transition-all placeholder:text-white/60"
              required
              placeholder="••••••••"
            />
          </div>

          <div class="space-y-3">
            <label class="block text-[10px] font-black text-white uppercase tracking-widest ml-1" for="new-password">
              Nouveau mot de passe
            </label>
            <input
              v-model="newPassword"
              id="new-password"
              type="password"
              class="w-full px-6 py-4 bg-white/5 border border-white/10 rounded-2xl text-white font-medium focus:outline-none focus:ring-1 focus:ring-white/30 focus:bg-white/10 transition-all placeholder:text-white/60"
              required
              placeholder="••••••••"
            />
          </div>

          <div class="space-y-3">
            <label class="block text-[10px] font-black text-white uppercase tracking-widest ml-1" for="confirm-password">
              Confirmer le mot de passe
            </label>
            <input
              v-model="confirmPassword"
              id="confirm-password"
              type="password"
              class="w-full px-6 py-4 bg-white/5 border border-white/10 rounded-2xl text-white font-medium focus:outline-none focus:ring-1 focus:ring-white/30 focus:bg-white/10 transition-all placeholder:text-white/60"
              required
              placeholder="••••••••"
            />
          </div>

          <div v-if="errorMsg" class="text-center">
            <span class="text-white text-[10px] font-black uppercase tracking-widest bg-red-500/20 text-red-300 px-4 py-1.5 rounded-full border border-red-500/30 inline-block">
              {{ errorMsg }}
            </span>
          </div>

          <button
            type="submit"
            :disabled="isLoading"
            class="w-full bg-white text-black py-4 rounded-2xl font-black text-xs uppercase tracking-[0.2em] shadow-xl hover:bg-zinc-200 hover:scale-[1.01] active:scale-[0.99] transition-all disabled:opacity-50 flex items-center justify-center gap-2"
          >
            <template v-if="isLoading">
              <div class="animate-spin h-4 w-4 border-2 border-black/30 border-t-black rounded-full"></div>
              <span>Mise à jour...</span>
            </template>
            <span v-else>Valider</span>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
