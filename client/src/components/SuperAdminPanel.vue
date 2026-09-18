<script setup>
import { ref, computed, onMounted } from "vue";
import { API_URL } from "../config.js";
import { useThemeStore } from "../stores/themeStore";
import { useAuthStore } from "../stores/authStore";
import { storeToRefs } from "pinia";

const themeStore = useThemeStore();
const authStore = useAuthStore();
const { isDarkMode } = storeToRefs(themeStore);
const { toggleTheme } = themeStore;

const activeTab = ref("admins");

const llmSettings = ref({
  llm_provider: "openrouter",
  llm_model_openrouter: "",
  llm_model_albert: "",
  openrouter_key_configured: false,
  albert_key_configured: false,
  openrouter_key_source: null,
  albert_key_source: null,
  openrouter_key_hint: null,
  albert_key_hint: null,
  auto_active_provider: null,
});
const isLlmSettingsLoading = ref(false);
const isSavingLlmSettings = ref(false);
const openrouterApiKeyInput = ref("");
const albertApiKeyInput = ref("");
const clearOpenrouterKey = ref(false);
const clearAlbertKey = ref(false);

const keySourceLabel = (source) => source === "database" ? "enregistrée en base" : source === "environment" ? "variable d'environnement" : "";

const admins = ref([]);
const regularAdmins = computed(() => admins.value.filter(a => !a.is_super));
const isAdminsLoading = ref(false);
const isCreatingAdmin = ref(false);
const newAdminFormData = ref({ username: "", nom: "", prenom: "", etablissement: "", email: "" });
const isAddingAdmin = ref(false);
const isEditingAdmin = ref(false);
const editAdminFormData = ref({ id: null, username: "", nom: "", prenom: "", etablissement: "", email: "" });
const isSavingAdmin = ref(false);

const formatDate = (isoStr) => {
  if (!isoStr) return "—";
  const d = new Date(isoStr);
  return d.toLocaleDateString("fr-FR", { day: "numeric", month: "short", year: "numeric", hour: "2-digit", minute: "2-digit" });
};

const loadAdmins = async () => {
  isAdminsLoading.value = true;
  try {
    const token = localStorage.getItem("access_token");
    const res = await fetch(`${API_URL}/admin/admins`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (res.ok) {
      admins.value = await res.json();
    }
  } catch (err) {
    console.error(err.message);
  } finally {
    isAdminsLoading.value = false;
  }
};

const openCreateAdminForm = () => {
  isEditingAdmin.value = false;
  isCreatingAdmin.value = true;
  newAdminFormData.value = { username: "", nom: "", prenom: "", etablissement: "", email: "" };
};

const submitCreateAdminForm = async () => {
  if (!newAdminFormData.value.username || !newAdminFormData.value.nom || !newAdminFormData.value.prenom) {
    alert("L'identifiant, le nom et le prénom sont requis.");
    return;
  }
  isAddingAdmin.value = true;
  try {
    const token = localStorage.getItem("access_token");
    const res = await fetch(`${API_URL}/admin/admins`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify(newAdminFormData.value)
    });
    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Erreur");
    }
    alert("Admin créé avec succès !");
    isCreatingAdmin.value = false;
    loadAdmins();
  } catch (err) {
    alert(err.message);
  } finally {
    isAddingAdmin.value = false;
  }
};

const openEditAdminForm = (adm) => {
  isCreatingAdmin.value = false;
  isEditingAdmin.value = true;
  editAdminFormData.value = {
    id: adm.id,
    username: adm.username,
    nom: adm.nom || "",
    prenom: adm.prenom || "",
    etablissement: adm.etablissement || "",
    email: adm.email || "",
  };
};

const cancelEditAdmin = () => { isEditingAdmin.value = false; };

const submitEditAdminForm = async () => {
  if (!editAdminFormData.value.username || !editAdminFormData.value.nom || !editAdminFormData.value.prenom) {
    alert("L'identifiant, le nom et le prénom sont requis.");
    return;
  }
  isSavingAdmin.value = true;
  try {
    const token = localStorage.getItem("access_token");
    const res = await fetch(`${API_URL}/admin/admins/${editAdminFormData.value.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({
        username: editAdminFormData.value.username,
        nom: editAdminFormData.value.nom,
        prenom: editAdminFormData.value.prenom,
        etablissement: editAdminFormData.value.etablissement,
        email: editAdminFormData.value.email,
      })
    });
    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Erreur");
    }
    isEditingAdmin.value = false;
    loadAdmins();
  } catch (err) {
    alert(err.message);
  } finally {
    isSavingAdmin.value = false;
  }
};

const deleteAdmin = async (adminId) => {
  if (!confirm("Supprimer cet admin et tous ses élèves et exercices ?")) return;
  try {
    const token = localStorage.getItem("access_token");
    const res = await fetch(`${API_URL}/admin/admins/${adminId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Erreur");
    }
    alert("Admin supprimé.");
    loadAdmins();
  } catch (err) {
    alert(err.message);
  }
};

const resetAdminPassword = async (adminId) => {
  if (!confirm("Réinitialiser le mot de passe de cet admin ? Il redeviendra identique à son identifiant et devra être modifié à la prochaine connexion.")) return;
  try {
    const token = localStorage.getItem("access_token");
    const res = await fetch(`${API_URL}/admin/admins/reset-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ admin_id: adminId })
    });
    if (!res.ok) throw new Error("Erreur");
    alert("Mot de passe réinitialisé (identique à l'identifiant).");
  } catch (err) {
    alert(err.message);
  }
};

const loadLlmSettings = async () => {
  isLlmSettingsLoading.value = true;
  try {
    const token = localStorage.getItem("access_token");
    const res = await fetch(`${API_URL}/admin/settings/llm`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (res.ok) {
      llmSettings.value = await res.json();
    }
  } catch (err) {
    console.error(err.message);
  } finally {
    isLlmSettingsLoading.value = false;
  }
};

const submitLlmSettings = async () => {
  if (!llmSettings.value.llm_model_openrouter.trim() || !llmSettings.value.llm_model_albert.trim()) {
    alert("Le nom du modèle ne peut pas être vide.");
    return;
  }
  isSavingLlmSettings.value = true;
  try {
    const token = localStorage.getItem("access_token");
    const payload = {
      llm_provider: llmSettings.value.llm_provider,
      llm_model_openrouter: llmSettings.value.llm_model_openrouter,
      llm_model_albert: llmSettings.value.llm_model_albert,
    };
    if (clearOpenrouterKey.value) payload.openrouter_api_key = "";
    else if (openrouterApiKeyInput.value.trim()) payload.openrouter_api_key = openrouterApiKeyInput.value.trim();
    if (clearAlbertKey.value) payload.albert_api_key = "";
    else if (albertApiKeyInput.value.trim()) payload.albert_api_key = albertApiKeyInput.value.trim();

    const res = await fetch(`${API_URL}/admin/settings/llm`, {
      method: "PUT",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Erreur");
    }
    alert("Configuration IA mise à jour.");
    openrouterApiKeyInput.value = "";
    albertApiKeyInput.value = "";
    clearOpenrouterKey.value = false;
    clearAlbertKey.value = false;
    loadLlmSettings();
  } catch (err) {
    alert(err.message);
  } finally {
    isSavingLlmSettings.value = false;
  }
};

onMounted(() => {
  loadAdmins();
  loadLlmSettings();
});
</script>

<template>
  <div :class="['h-screen flex flex-col font-sans transition-colors duration-300', isDarkMode ? 'bg-zinc-950' : 'bg-white']">
    <header :class="['flex justify-between items-center px-6 py-2 z-10 backdrop-blur-md transition-colors', isDarkMode ? 'bg-zinc-900/80' : 'bg-white/80']">
      <div class="flex items-center gap-2">
        <img src="../assets/logo.png" alt="EXOPY" class="h-8 px-10 md:h-10 hover:scale-105 transition-transform" />
      </div>

      <div class="flex items-center gap-4">
        <button
          @click="toggleTheme"
          :class="['p-2 rounded-xl transition-all border shadow-sm', isDarkMode ? 'bg-zinc-800/50 text-zinc-400 hover:bg-zinc-700 border-zinc-700/50' : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200 border-zinc-200']"
          title="Changer le thème"
        >
          <svg v-if="isDarkMode" xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M17.293 13.293A8 8 0 016.707 2.707a8.001 8.001 0 1010.586 10.586z" />
          </svg>
          <svg v-else xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 2a1 1 0 011 1v1a1 1 0 11-2 0V3a1 1 0 011-1zm4 8a4 4 0 11-8 0 4 4 0 018 0zm-.464 4.95l.707.707a1 1 0 001.414-1.414l-.707-.707a1 1 0 00-1.414 1.414zm2.12-10.607a1 1 0 010 1.414l-.706.707a1 1 0 11-1.414-1.414l.707-.707a1 1 0 011.414 0zM17 11a1 1 0 100-2h-1a1 1 0 100 2h1zm-7 4a1 1 0 011 1v1a1 1 0 11-2 0v-1a1 1 0 011-1zM5.05 6.464A1 1 0 106.465 5.05l-.708-.707a1 1 0 00-1.414 1.414l.707.707zm1.414 8.486l-.707.707a1 1 0 01-1.414-1.414l.707-.707a1 1 0 011.414 1.414zM4 11a1 1 0 100-2H3a1 1 0 000 2h1z" clip-rule="evenodd" />
          </svg>
        </button>

        <button
          @click="authStore.logout"
          :class="['text-sm font-bold hover:text-red-500 transition-colors cursor-pointer p-2 rounded-lg', isDarkMode ? 'text-zinc-400 hover:text-red-400 hover:bg-zinc-800' : 'text-zinc-400 hover:bg-zinc-100']"
          title="Se déconnecter"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
        </button>
      </div>
    </header>

    <main class="flex-1 overflow-y-auto custom-scrollbar p-8">
      <div class="max-w-4xl mx-auto space-y-8">
        <nav class="flex gap-1 bg-zinc-200/50 dark:bg-zinc-950/50 p-1.5 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-inner w-fit">
          <button
            @click="activeTab = 'admins'"
            :class="activeTab === 'admins' ? 'bg-white dark:bg-zinc-800 text-blue-600 dark:text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-300'"
            class="px-6 py-2 rounded-xl text-xs font-black transition-all uppercase tracking-widest"
          >Gestion des admins</button>
          <button
            @click="activeTab = 'models'"
            :class="activeTab === 'models' ? 'bg-white dark:bg-zinc-800 text-blue-600 dark:text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-300'"
            class="px-6 py-2 rounded-xl text-xs font-black transition-all uppercase tracking-widest"
          >Gestion des modèles</button>
        </nav>

        <div v-if="activeTab === 'models'" class="bg-white dark:bg-zinc-800 rounded-[2rem] p-8 shadow-xl border border-zinc-100 dark:border-zinc-700 space-y-6">
          <div>
            <h2 class="text-xs font-black text-blue-600 dark:text-blue-400 uppercase tracking-widest mb-2">Configuration</h2>
            <h1 class="text-3xl font-black text-zinc-800 dark:text-white tracking-tight italic">Assistant IA</h1>
          </div>

          <div class="space-y-3">
            <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest ml-1">Fournisseur actif</label>
            <nav class="flex gap-1 bg-zinc-200/50 dark:bg-zinc-950/50 p-1.5 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-inner w-fit">
              <button
                @click="llmSettings.llm_provider = 'openrouter'"
                :class="llmSettings.llm_provider === 'openrouter' ? 'bg-white dark:bg-zinc-800 text-blue-600 dark:text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-300'"
                class="px-6 py-2 rounded-xl text-xs font-black transition-all uppercase tracking-widest"
              >OpenRouter</button>
              <button
                @click="llmSettings.llm_provider = 'albert'"
                :class="llmSettings.llm_provider === 'albert' ? 'bg-white dark:bg-zinc-800 text-blue-600 dark:text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-300'"
                class="px-6 py-2 rounded-xl text-xs font-black transition-all uppercase tracking-widest"
              >Albert API</button>
              <button
                @click="llmSettings.llm_provider = 'auto'"
                :class="llmSettings.llm_provider === 'auto' ? 'bg-white dark:bg-zinc-800 text-blue-600 dark:text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-300'"
                class="px-6 py-2 rounded-xl text-xs font-black transition-all uppercase tracking-widest"
              >Auto</button>
            </nav>
            <p v-if="llmSettings.llm_provider === 'auto'" class="text-xs text-zinc-500 dark:text-zinc-400 ml-1">
              Privilégie Albert API et bascule automatiquement sur OpenRouter en cas d'erreur
              (surcharge, indisponibilité...), puis revient sur Albert dès qu'il redevient disponible.
              <span v-if="llmSettings.auto_active_provider" class="font-bold">
                Actuellement : {{ llmSettings.auto_active_provider === 'albert' ? 'Albert API' : 'OpenRouter (secours)' }}.
              </span>
            </p>
          </div>

          <div v-if="(llmSettings.llm_provider === 'openrouter' || llmSettings.llm_provider === 'auto') && !llmSettings.openrouter_key_configured"
               class="text-xs text-amber-600 dark:text-amber-500 bg-amber-50 dark:bg-amber-500/5 border border-amber-200 dark:border-amber-500/20 rounded-xl p-4">
            Attention : la clé API OpenRouter n'est pas configurée sur le serveur. Les requêtes échoueront.
          </div>
          <div v-if="(llmSettings.llm_provider === 'albert' || llmSettings.llm_provider === 'auto') && !llmSettings.albert_key_configured"
               class="text-xs text-amber-600 dark:text-amber-500 bg-amber-50 dark:bg-amber-500/5 border border-amber-200 dark:border-amber-500/20 rounded-xl p-4">
            Attention : la clé API Albert n'est pas configurée sur le serveur. Les requêtes échoueront.
          </div>

          <div class="grid grid-cols-2 gap-6">
            <div class="space-y-3">
              <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest ml-1">Modèle OpenRouter</label>
              <input v-model="llmSettings.llm_model_openrouter" type="text" class="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-2xl p-4 text-zinc-800 dark:text-white font-bold focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-inner" placeholder="deepseek/deepseek-v4-flash">
            </div>
            <div class="space-y-3">
              <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest ml-1">Modèle Albert API</label>
              <input v-model="llmSettings.llm_model_albert" type="text" class="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-2xl p-4 text-zinc-800 dark:text-white font-bold focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-inner" placeholder="deepseek-v4-flash">
            </div>
          </div>
          <div class="text-xs text-zinc-500 dark:text-zinc-400 bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl p-4">
            Vérifiez l'identifiant exact du modèle Albert API dans la liste des modèles disponibles avant d'activer ce fournisseur : la documentation d'Albert ne garantit pas que "deepseek-v4-flash" soit la chaîne exacte attendue par l'API.
          </div>

          <div class="grid grid-cols-2 gap-6">
            <div class="space-y-3">
              <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest ml-1">Clé API OpenRouter</label>
              <input v-model="openrouterApiKeyInput" type="password" autocomplete="off"
                class="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-2xl p-4 text-zinc-800 dark:text-white font-bold focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-inner disabled:opacity-40"
                :disabled="clearOpenrouterKey"
                placeholder="laisser vide pour ne pas modifier">
              <div class="text-[11px] text-zinc-400 dark:text-zinc-500 ml-1">
                <span v-if="llmSettings.openrouter_key_configured">
                  Clé active : <span class="font-mono">{{ llmSettings.openrouter_key_hint }}</span> ({{ keySourceLabel(llmSettings.openrouter_key_source) }})
                </span>
                <span v-else>Aucune clé disponible pour ce fournisseur.</span>
                <label v-if="llmSettings.openrouter_key_source === 'database'" class="ml-2 inline-flex items-center gap-1 text-red-500 cursor-pointer">
                  <input type="checkbox" v-model="clearOpenrouterKey"> Supprimer la clé enregistrée
                </label>
              </div>
            </div>
            <div class="space-y-3">
              <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest ml-1">Clé API Albert</label>
              <input v-model="albertApiKeyInput" type="password" autocomplete="off"
                class="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-2xl p-4 text-zinc-800 dark:text-white font-bold focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-inner disabled:opacity-40"
                :disabled="clearAlbertKey"
                placeholder="laisser vide pour ne pas modifier">
              <div class="text-[11px] text-zinc-400 dark:text-zinc-500 ml-1">
                <span v-if="llmSettings.albert_key_configured">
                  Clé active : <span class="font-mono">{{ llmSettings.albert_key_hint }}</span> ({{ keySourceLabel(llmSettings.albert_key_source) }})
                </span>
                <span v-else>Aucune clé disponible pour ce fournisseur.</span>
                <label v-if="llmSettings.albert_key_source === 'database'" class="ml-2 inline-flex items-center gap-1 text-red-500 cursor-pointer">
                  <input type="checkbox" v-model="clearAlbertKey"> Supprimer la clé enregistrée
                </label>
              </div>
            </div>
          </div>
          <div class="text-xs text-zinc-500 dark:text-zinc-400 bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl p-4">
            Les clés saisies ici sont chiffrées avant d'être enregistrées en base et priment sur les variables d'environnement du serveur. Le changement de fournisseur est bloqué si aucune clé (base ou variable d'environnement) n'est disponible.
          </div>

          <div class="flex gap-4 pt-4 border-t border-zinc-100 dark:border-zinc-700">
            <button @click="submitLlmSettings" :disabled="isSavingLlmSettings" class="px-10 py-4 rounded-xl font-black text-[11px] text-white bg-blue-600 hover:bg-blue-500 transition-all shadow-xl shadow-blue-500/20 uppercase tracking-[0.2em] disabled:opacity-50">
              {{ isSavingLlmSettings ? 'Sauvegarde...' : 'Sauvegarder' }}
            </button>
          </div>
        </div>

        <template v-if="activeTab === 'admins'">
        <div class="flex justify-between items-end border-b border-zinc-200 dark:border-zinc-800 pb-6">
          <div>
            <h2 class="text-xs font-black text-blue-600 dark:text-blue-400 uppercase tracking-widest mb-2">Administration</h2>
            <h1 class="text-3xl font-black text-zinc-800 dark:text-white tracking-tight italic">Gestion des admins</h1>
          </div>
          <button @click="openCreateAdminForm" class="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-black text-[10px] uppercase tracking-widest transition-all shadow-xl shadow-blue-500/20">+ Nouvel admin</button>
        </div>

        <div v-if="isCreatingAdmin" class="bg-white dark:bg-zinc-800 rounded-[2rem] p-8 shadow-xl border border-zinc-100 dark:border-zinc-700 space-y-6 animate-in fade-in zoom-in-95 duration-500">
          <h3 class="text-sm font-black text-zinc-800 dark:text-white uppercase tracking-widest">Créer un admin</h3>
          <div class="grid grid-cols-2 gap-6">
            <div class="space-y-3">
              <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest ml-1">Identifiant</label>
              <input v-model="newAdminFormData.username" type="text" class="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-2xl p-4 text-zinc-800 dark:text-white font-bold focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-inner" placeholder="login admin">
            </div>
            <div class="space-y-3">
              <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest ml-1">Prénom</label>
              <input v-model="newAdminFormData.prenom" type="text" class="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-2xl p-4 text-zinc-800 dark:text-white font-bold focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-inner" placeholder="Jean">
            </div>
            <div class="space-y-3">
              <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest ml-1">Nom</label>
              <input v-model="newAdminFormData.nom" type="text" class="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-2xl p-4 text-zinc-800 dark:text-white font-bold focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-inner" placeholder="Dupont">
            </div>
            <div class="space-y-3">
              <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest ml-1">Établissement <span class="normal-case font-medium text-zinc-400">(optionnel)</span></label>
              <input v-model="newAdminFormData.etablissement" type="text" class="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-2xl p-4 text-zinc-800 dark:text-white font-bold focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-inner" placeholder="Lycée...">
            </div>
            <div class="space-y-3 col-span-2">
              <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest ml-1">Adresse email académique <span class="normal-case font-medium text-zinc-400">(optionnel)</span></label>
              <input v-model="newAdminFormData.email" type="email" class="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-2xl p-4 text-zinc-800 dark:text-white font-bold focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-inner" placeholder="prenom.nom@ac-academie.fr">
            </div>
          </div>
          <div class="text-xs text-zinc-500 dark:text-zinc-400 bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl p-4">
            Le mot de passe initial de l'admin sera automatiquement identique à son identifiant. Il devra le modifier à sa première connexion.
          </div>
          <div class="flex gap-4 pt-4 border-t border-zinc-100 dark:border-zinc-700">
            <button @click="isCreatingAdmin = false" class="px-8 py-4 rounded-xl font-black text-[10px] text-zinc-400 hover:text-red-500 transition-colors uppercase tracking-widest">Annuler</button>
            <button @click="submitCreateAdminForm" :disabled="isAddingAdmin" class="px-10 py-4 rounded-xl font-black text-[11px] text-white bg-blue-600 hover:bg-blue-500 transition-all shadow-xl shadow-blue-500/20 uppercase tracking-[0.2em] disabled:opacity-50">
              {{ isAddingAdmin ? 'Création...' : 'Créer' }}
            </button>
          </div>
        </div>

        <div v-if="isEditingAdmin" class="bg-white dark:bg-zinc-800 rounded-[2rem] p-8 shadow-xl border border-zinc-100 dark:border-zinc-700 space-y-6 animate-in fade-in zoom-in-95 duration-500">
          <h3 class="text-sm font-black text-zinc-800 dark:text-white uppercase tracking-widest">Modifier l'admin</h3>
          <div class="grid grid-cols-2 gap-6">
            <div class="space-y-3">
              <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest ml-1">Identifiant</label>
              <input v-model="editAdminFormData.username" type="text" class="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-2xl p-4 text-zinc-800 dark:text-white font-bold focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-inner" placeholder="login admin">
            </div>
            <div class="space-y-3">
              <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest ml-1">Prénom</label>
              <input v-model="editAdminFormData.prenom" type="text" class="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-2xl p-4 text-zinc-800 dark:text-white font-bold focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-inner" placeholder="Jean">
            </div>
            <div class="space-y-3">
              <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest ml-1">Nom</label>
              <input v-model="editAdminFormData.nom" type="text" class="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-2xl p-4 text-zinc-800 dark:text-white font-bold focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-inner" placeholder="Dupont">
            </div>
            <div class="space-y-3">
              <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest ml-1">Établissement <span class="normal-case font-medium text-zinc-400">(optionnel)</span></label>
              <input v-model="editAdminFormData.etablissement" type="text" class="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-2xl p-4 text-zinc-800 dark:text-white font-bold focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-inner" placeholder="Lycée...">
            </div>
            <div class="space-y-3 col-span-2">
              <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest ml-1">Adresse email académique <span class="normal-case font-medium text-zinc-400">(optionnel)</span></label>
              <input v-model="editAdminFormData.email" type="email" class="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-2xl p-4 text-zinc-800 dark:text-white font-bold focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-inner" placeholder="prenom.nom@ac-academie.fr">
            </div>
          </div>
          <div class="flex gap-4 pt-4 border-t border-zinc-100 dark:border-zinc-700">
            <button @click="cancelEditAdmin" class="px-8 py-4 rounded-xl font-black text-[10px] text-zinc-400 hover:text-red-500 transition-colors uppercase tracking-widest">Annuler</button>
            <button @click="submitEditAdminForm" :disabled="isSavingAdmin" class="px-10 py-4 rounded-xl font-black text-[11px] text-white bg-blue-600 hover:bg-blue-500 transition-all shadow-xl shadow-blue-500/20 uppercase tracking-[0.2em] disabled:opacity-50">
              {{ isSavingAdmin ? 'Sauvegarde...' : 'Sauvegarder' }}
            </button>
          </div>
        </div>

        <div v-if="isAdminsLoading" class="flex justify-center py-12"><div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div></div>
        <div v-else class="space-y-3">
          <div v-for="adm in regularAdmins" :key="adm.id" class="bg-white dark:bg-zinc-800 rounded-2xl p-6 shadow-sm border border-zinc-100 dark:border-zinc-700 group">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-2xl flex items-center justify-center font-black text-sm shadow-sm bg-blue-100 dark:bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-200 dark:border-blue-500/20">
                  {{ (adm.prenom || adm.username).substring(0, 2).toUpperCase() }}
                </div>
                <div>
                  <div class="flex items-center gap-3">
                    <span class="font-black text-zinc-800 dark:text-white tracking-tight">
                      {{ adm.nom }} {{ adm.prenom }}
                      <span v-if="!adm.prenom && !adm.nom">{{ adm.username }}</span>
                    </span>
                    <span v-if="adm.must_change_password" title="Doit encore changer son mot de passe" class="w-1.5 h-1.5 rounded-full bg-amber-500 flex-shrink-0"></span>
                  </div>
                  <div class="text-xs text-zinc-400 dark:text-zinc-500 font-bold flex items-center gap-2 flex-wrap">
                    <span>@{{ adm.username }}</span>
                    <span v-if="adm.etablissement">· {{ adm.etablissement }}</span>
                    <span>· {{ adm.nb_students }} élève{{ adm.nb_students !== 1 ? 's' : '' }}</span>
                  </div>
                  <div v-if="adm.email" class="text-[10px] text-zinc-400 dark:text-zinc-600 mt-0.5">{{ adm.email }}</div>
                </div>
              </div>
              <div class="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                <button @click="openEditAdminForm(adm)" class="px-4 py-2 text-[10px] font-black text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-500/5 border border-blue-200 dark:border-blue-500/20 rounded-xl uppercase tracking-widest hover:bg-blue-100 dark:hover:bg-blue-500/10 transition-all">Modifier</button>
                <button @click="resetAdminPassword(adm.id)" class="px-4 py-2 text-[10px] font-black text-amber-600 dark:text-amber-500 bg-amber-50 dark:bg-amber-500/5 border border-amber-200 dark:border-amber-500/20 rounded-xl uppercase tracking-widest hover:bg-amber-100 dark:hover:bg-amber-500/10 transition-all">Reset mdp</button>
                <button @click="deleteAdmin(adm.id)" class="px-4 py-2 text-[10px] font-black text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-500/5 border border-red-200 dark:border-red-500/20 rounded-xl uppercase tracking-widest hover:bg-red-100 dark:hover:bg-red-500/10 transition-all">Supprimer</button>
              </div>
            </div>
            <div class="mt-4 pt-4 border-t border-zinc-100 dark:border-zinc-700 grid grid-cols-4 gap-4">
              <div class="text-center">
                <div class="text-lg font-black text-zinc-800 dark:text-white">{{ adm.nb_exercises }}</div>
                <div class="text-[9px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest">Exercices</div>
              </div>
              <div class="text-center">
                <div class="text-lg font-black text-blue-600 dark:text-blue-400">{{ adm.nb_ai_requests }}</div>
                <div class="text-[9px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest">Requêtes IA</div>
              </div>
              <div class="text-center">
                <div class="text-lg font-black text-zinc-800 dark:text-white">{{ adm.nb_total_requests }}</div>
                <div class="text-[9px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest">Total événements</div>
              </div>
              <div class="text-center">
                <div class="text-sm font-black text-zinc-800 dark:text-white">{{ formatDate(adm.last_activity) }}</div>
                <div class="text-[9px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest">Dernière activité</div>
              </div>
            </div>
          </div>
          <div v-if="regularAdmins.length === 0" class="text-center py-12 text-zinc-400 text-sm italic">Aucun admin enregistré.</div>
        </div>
        </template>
      </div>
    </main>
  </div>
</template>
