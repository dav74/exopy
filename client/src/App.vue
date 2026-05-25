<script setup>
import SideMenu from "./components/SideMenu.vue";
import ExerciseWindow from "./components/ExerciseWindow.vue";
import Code from "./components/Code.vue";
import Assistant from "./components/Assistant.vue";
import SuccessWindow from "./components/SuccessWindow.vue";
import Connexion from "./components/Connexion.vue";
import Bilan from "./components/Bilan.vue";
import AdminPanel from "./components/AdminPanel.vue";
import { ref, onMounted, onUnmounted, nextTick } from "vue";
import { useAuthStore } from "./stores/authStore";
import { useExerciseStore } from "./stores/exerciseStore";
import { useThemeStore } from "./stores/themeStore";
import { storeToRefs } from "pinia";
import { API_URL } from "./config.js";

const authStore = useAuthStore();
const exerciseStore = useExerciseStore();
const themeStore = useThemeStore();

const { id_user, userFullInfo, assistantIsOn, isAdmin, aiEnabled } = storeToRefs(authStore);
const { selectedItemId, exercise, code, resTest, testCode, visibleTests, errorCode } = storeToRefs(exerciseStore);
const { isDarkMode } = storeToRefs(themeStore);
const { toggleTheme } = themeStore;

const isLoading = ref(false);
const error = ref(null);
const msgAI = ref(
  "Vous devez choisir un exercice avant que je puisse vous aider.",
);
const codePlusTest = ref("");
const bilanAI = ref("");
let pyodide = null;
let successWindowRef = ref(null);
const showBilan = ref(false);
const showAdmin = ref(false);
const isAssistantLoading = ref(false);
const exerciseStartTime = ref(null);

const pythonOutput = ref([]);
const terminalRef = ref(null);

const uuidv4 = () => {
  return "10000000-1000-4000-8000-100000000000".replace(/[018]/g, (c) =>
    (
      +c ^
      (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (+c / 4)))
    ).toString(16),
  );
};

const session_id = uuidv4();

const logEvent = async (status, errorType = null) => {
  if (!selectedItemId.value) return;
  
  let duration = null;
  if (exerciseStartTime.value) {
    duration = Math.floor((Date.now() - exerciseStartTime.value) / 1000);
    // Re-initialize for the next sequence (e.g., failure -> reflection -> next attempt)
    exerciseStartTime.value = Date.now();
  }

  try {
    const token = localStorage.getItem("access_token");
    await fetch(API_URL + "/api/metrics/log", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        exercise_id: selectedItemId.value,
        status: status,
        error_type: errorType,
        session_id: session_id,
        duration: duration
      }),
    });
  } catch (err) {
    console.error("Failed to log metric event", err);
  }
};

const handleMenuItemSelect = async (id) => {
  isLoading.value = true;
  error.value = null;
  msgAI.value =
    "Vous devez exécuter votre programme avant que je puisse vous aider.";
  codePlusTest.value = "";
  pythonOutput.value = [];
  try {
    const token = localStorage.getItem("access_token");
    const response = await fetch(API_URL + `/exercise/${id}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    if (!response.ok) {
      if (response.status === 401) {
        authStore.logout();
      }
      throw new Error("Erreur lors de la récupération de l'exercice");
    }
    const data = await response.json();
    exerciseStore.setExercise(data, id);
    exerciseStartTime.value = Date.now();
  } catch (err) {
    error.value = err.message;
    exerciseStore.resetExerciseState();
  } finally {
    isLoading.value = false;
  }
};
const fetchProfile = async () => {
  if (id_user.value === "") return;
  try {
    const token = localStorage.getItem("access_token");
    const response = await fetch(API_URL + "/auth/me", {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (response.ok) {
      const data = await response.json();
      authStore.setUserFullInfo(data);
    }
  } catch (err) {
    console.error("Failed to fetch profile", err);
  }
};

onMounted(async () => {
  window.printPythonStorage = (text) => {
      pythonOutput.value.push(text);
      nextTick(() => {
          if (terminalRef.value) {
              terminalRef.value.scrollTop = terminalRef.value.scrollHeight;
          }
      });
  };

  pyodide = await loadPyodide({
    stdout: (msg) => { window.printPythonStorage(msg); },
    stderr: (msg) => { window.printPythonStorage(`[Erreur] ${msg}`); }
  });
  authStore.checkSavedAuth();
  fetchProfile();
});

const addTestWithDelay = (test, index) => {
  setTimeout(() => {
    visibleTests.value.push(test);
    if (index === testCode.value.length - 1) {
      if (resTest.value == "2") {
        setTimeout(() => {
          successWindowRef.value.showSuccess();
        }, 1000);
      }
    }
  }, index * 1000);
};

const callAssistant = async () => {
  if (!aiEnabled.value) {
    if (resTest.value == "2") {
      bilanAI.value = "";
      msgAI.value = "Vous pouvez choisir un autre exercice";
    } else {
      msgAI.value = "L'assistant IA n'est pas configuré sur ce serveur.";
    }
    isAssistantLoading.value = false;
    return;
  }
  
  msgAI.value = "";
  bilanAI.value = "";

  if (!assistantIsOn.value) {
    isAssistantLoading.value = false;
    return;
  }

  isAssistantLoading.value = true;
  try {
    const token = localStorage.getItem("access_token");
    const callAI = await fetch(API_URL + "/request", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({
        session: session_id,
        enonce: exercise.value.enonce,
        code: code.value,
        res_test: resTest.value,
        is_assistant: assistantIsOn.value,
      }),
    });
    if (!callAI.ok) {
      if (callAI.status === 401) {
        authStore.logout();
      } else if (callAI.status === 403) {
        if (resTest.value == "2") {
          bilanAI.value = "";
          msgAI.value = "Vous pouvez choisir un autre exercice";
        } else {
          msgAI.value = "L'assistant IA est désactivé par votre administrateur.";
        }
        isAssistantLoading.value = false;
        return;
      }
    }
    const data = await callAI.json();
    if (resTest.value == "2") {
      msgAI.value = "Vous pouvez choisir un autre exercice";
      bilanAI.value = data.response;
    } else {
      msgAI.value = data.response;
    }
  } catch (error) {
    msgAI.value =
      "Je suis désolé, mais suite à une erreur interne, je ne suis pas en mesure de t'aider pour le moment";
  } finally {
    isAssistantLoading.value = false;
  }
  logEvent("ai_request");
};

const handleCodeUpdate = async (co) => {
  exerciseStore.saveCodeLocally(co);
  testCode.value = [];
  errorCode.value = "";
  visibleTests.value = [];
  pythonOutput.value = [];
  codePlusTest.value = co + "\n\n" + exercise.value.test;
  try {
    await pyodide.runPythonAsync(codePlusTest.value);
    let val = await pyodide.globals.get("c");
    
    if (val === undefined) {
        throw new Error("La variable de test 'c' n'a pas été trouvée dans l'exécution.");
    }
    
    // Convertir en JS si c'est un PyProxy (ex: une liste au lieu d'une string)
    if (val && typeof val.toJs === 'function') {
        const jsVal = val.toJs();
        testCode.value = Array.isArray(jsVal) ? jsVal : String(jsVal).split("");
    } else {
        testCode.value = String(val).split("");
    }

    if (testCode.value.every((t) => t === "1") && testCode.value.length > 0) {
      resTest.value = "2";
    } else {
      resTest.value = "1";
    }
    callAssistant();
    testCode.value.forEach((test, index) => {
      addTestWithDelay(test, index);
    });
    if (resTest.value === "2") {
      await logEvent("success");
      exerciseStore.fetchMenuItems(API_URL);
    } else {
      logEvent("failure");
    }
  } catch (err) {
    resTest.value = "0";
    callAssistant();
    const errStr = err.toString();
    let eType = "Error";
    if (errStr.includes("SyntaxError")) eType = "SyntaxError";
    else if (errStr.includes("IndexError")) eType = "IndexError";
    else if (errStr.includes("NameError")) eType = "NameError";
    else if (errStr.includes("TypeError")) eType = "TypeError";
    
    logEvent("failure", eType);

    if (errStr.includes('File "<exec>",')) {
        errorCode.value = errStr.split('File "<exec>",')[1];
    } else {
        errorCode.value = errStr;
    }
  }
};

const openBilan = () => { showBilan.value = true; };
const closeBilan = () => { showBilan.value = false; };

const connect_id = (user) => {
  authStore.setUserId(user);
  fetchProfile();
};

const assitant = (v) => {
  authStore.setAssistantStatus(v);
};
</script>

<template>
  <div :class="['h-screen flex flex-col font-sans transition-colors duration-300', isDarkMode ? 'bg-zinc-950' : 'bg-white']">
    <!-- Top Header Bar -->
    <header v-if="id_user !== ''" :class="['flex justify-between items-center px-6 py-2 z-10 backdrop-blur-md transition-colors', isDarkMode ? 'bg-zinc-900/80' : 'bg-white/80']">
      <div class="flex items-center gap-2">
        <img src="./assets/logo.png" alt="EXOPY" class="h-8 px-10 md:h-10 hover:scale-105 transition-transform" />
      </div>
      
      <div class="flex items-center gap-4">
        <button
          v-if="isAdmin"
          @click="showAdmin = true"
          class="flex items-center gap-2 px-4 py-1.5 bg-blue-600/20 text-blue-400 hover:bg-blue-600/40 rounded-full transition-all text-sm font-bold border border-blue-500/30 mr-2 shadow-sm"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836 1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z" clip-rule="evenodd" />
          </svg>
          Panel admin
        </button>
        
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

        <div :class="['h-6 w-[1px] mx-1', isDarkMode ? 'bg-zinc-700' : 'bg-zinc-200']"></div>

        <span
          @click="openBilan"
          :class="['font-medium hover:text-blue-500 dark:hover:text-blue-400 transition-colors hover:cursor-pointer flex items-center gap-2 px-2', isDarkMode ? 'text-zinc-200' : 'text-zinc-600']"
        >
          <div :class="['w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold border', isDarkMode ? 'bg-zinc-700 text-zinc-300 border-zinc-600' : 'bg-zinc-100 text-zinc-500 border-zinc-200']">
            {{ (userFullInfo.prenom || id_user).substring(0, 2).toUpperCase() }}
          </div>
          {{ userFullInfo.prenom }} {{ userFullInfo.nom }}
          <span v-if="!userFullInfo.prenom && !userFullInfo.nom">{{ id_user }}</span>
        </span>

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

    <div v-if="id_user !== ''" class="flex flex-1 overflow-hidden">
      <SideMenu @select-item="handleMenuItemSelect" />
      
      <!-- Main Content Layout with Flex -->
      <main class="flex-1 flex flex-col lg:flex-row px-4 gap-6 overflow-hidden">
        
        <!-- Left Column: Exercise & Assistant -->
        <div class="flex-1 flex flex-col min-w-0 max-w-2xl gap-2 h-full">
          <ExerciseWindow
            class="flex-[2] min-h-0"
            :exercise="exercise"
            :is-loading="isLoading"
            :error="error"
          />
          <Assistant
            class="flex-[1] min-h-0"
            :msg="msgAI"
            :is-loading="isAssistantLoading"
            :disabled="!aiEnabled"
            :active="assistantIsOn"
            @isAssistant="assitant"
          />
        </div>
        
        <!-- Right Column: Code Editor & Tests -->
        <div class="flex-1 flex flex-col h-full overflow-hidden">
          <div class="flex justify-between items-center mb-4">
             <h1 :class="['text-xl font-black tracking-widest uppercase italic', isDarkMode ? 'text-white' : 'text-zinc-800']">
               Éditeur de code
             </h1>
          </div>
          
          <Code
            class="flex-[2] flex flex-col min-h-[300px]"
            @send-code="handleCodeUpdate"
            :exercise="exercise"
          />
          
          <!-- Test Feedback Section -->
          <div :class="['mt-4 flex flex-col rounded-[1.5rem] p-4 min-h-[80px] custom-scrollbar overflow-x-auto w-full border transition-colors shadow-inner', isDarkMode ? 'bg-zinc-950 border-black' : 'bg-white border-zinc-200 shadow-sm']">
            
            <div
              v-if="visibleTests.length > 0"
              class="flex flex-wrap gap-5 items-center"
            >
              <div v-for="(test, index) in visibleTests" :key="index">
                <img class="w-10 h-10 transform hover:scale-125 transition-transform duration-300" v-if="test == '1'" src="/ok.png" alt="Succès test" />
                <img class="w-10 h-10 transform hover:scale-125 transition-transform duration-300" v-if="test == '0'" src="/ko.png" alt="Échec test" />
              </div>
            </div>

            <div v-else-if="!pythonOutput.length && !errorCode" :class="['flex items-center justify-center h-full italic text-sm', isDarkMode ? 'text-zinc-600' : 'text-zinc-400']">
              En attente de l'exécution...
            </div>
            
            <div
              v-if="errorCode"
              class="flex items-start mt-2 bg-red-900/20 p-4 rounded-xl border border-red-500/30 error-container"
            >
              <img class="w-8 h-8 mr-4 flex-shrink-0 mt-1" src="/erreur.png" alt="Erreur" />
              <pre class="text-red-400 text-xs whitespace-pre-wrap font-mono leading-relaxed">{{ errorCode }}</pre>
            </div>
          </div>

          <!-- Python Console Section -->
          <div :class="['mt-4 flex flex-col flex-1 min-h-[140px] max-h-[220px] rounded-[1.5rem] border overflow-hidden relative shadow-inner transition-colors', isDarkMode ? 'bg-zinc-950 border-black' : 'bg-zinc-50 border-zinc-200 shadow-inner']">
            <div :class="['text-[10px] font-black tracking-[0.3em] py-2 px-6 border-b flex items-center justify-between uppercase', isDarkMode ? 'bg-zinc-900/50 text-zinc-500 border-black' : 'bg-zinc-100 text-zinc-400 border-zinc-200']">
              <span>CONSOLE OUTPUT</span>
            </div>
            
            <div ref="terminalRef" :class="['p-4 overflow-y-auto custom-scrollbar flex-1 transition-colors', isDarkMode ? 'bg-zinc-950' : 'bg-zinc-50']">
              <div v-if="pythonOutput.length > 0" :class="['font-mono text-sm whitespace-pre-wrap leading-relaxed transition-colors', isDarkMode ? 'text-emerald-400' : 'text-emerald-600']">
                 <div v-for="(line, idx) in pythonOutput" :key="idx" class="mb-1">{{ line }}</div>
              </div>
            </div>
          </div>

        </div>
      </main>
    </div>
    
    <!-- Admin Panel Overlay -->
    <AdminPanel 
      v-if="showAdmin" 
      @close="showAdmin = false" 
    />

    <!-- Overlays -->
    <SuccessWindow
      ref="successWindowRef"
      :msg="bilanAI"
      :assistant-on="assistantIsOn"
    />

    <div
      v-if="id_user === ''"
      class="fixed inset-0 z-[100]"
    >
      <Connexion @idCorrect="connect_id" />
    </div>
    
    <div
      v-if="showBilan"
      class="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-6 md:p-10"
    >
      <Bilan :user_name="id_user" @close="closeBilan" />
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: #4b5563 #374151;
}
.custom-scrollbar::-webkit-scrollbar {
  width: 8px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: #27272a;
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #52525b;
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: #71717a;
}

.error-container {
  opacity: 0;
  animation: fadeInError 0.4s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

@keyframes fadeInError {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
