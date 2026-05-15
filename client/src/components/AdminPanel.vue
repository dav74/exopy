<script setup>
import { ref, computed, onMounted, defineAsyncComponent } from "vue";
import { API_URL } from "../config.js";
import MarkdownIt from "markdown-it";
import DOMPurify from "dompurify";
import { useThemeStore } from "../stores/themeStore";
import { storeToRefs } from "pinia";

const themeStore = useThemeStore();
const { isDarkMode } = storeToRefs(themeStore);
const Dashboard = defineAsyncComponent(() => import("./Dashboard.vue"));

const markdown = new MarkdownIt();

const emit = defineEmits(["close"]);

// General state
const exercises = ref([]);
const isLoading = ref(true);
const isGenerating = ref(false);
const errorMsg = ref("");

// Tab state
const currentTab = ref("exercises"); // 'exercises' or 'users'

// User management state
const users = ref([]);
const userSearchQuery = ref("");
const selectedStudent = ref(null); // When viewing a dashboard
const isUsersLoading = ref(false);
const isEditingUser = ref(false);
const isCreatingUser = ref(false);
const userFormData = ref({
  username: "",
  nom: "",
  prenom: ""
});
const newUserFormData = ref({
  username: "",
  password: "",
  nom: "",
  prenom: ""
});
const isUpdatingUser = ref(false);
const isAddingUser = ref(false);
const isImportingUsers = ref(false);
const userCsvInput = ref(null);

// Form state
const isEditing = ref(false);
const showForm = ref(false);
const formData = ref({
  id: null,
  titre: "",
  niveau: "1",
  enonce: "",
  test: ""
});

const safeEnoncePreview = computed(() => {
  if (!formData.value.enonce) return "";
  return DOMPurify.sanitize(markdown.render(formData.value.enonce));
});

const loadExercises = async () => {
  isLoading.value = true;
  errorMsg.value = "";
  try {
    const token = localStorage.getItem("access_token");
    const res = await fetch(API_URL + "/title", {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Erreur de chargement");
    const data = await res.json();
    exercises.value = data.title;
  } catch (err) {
    errorMsg.value = err.message;
  } finally {
    isLoading.value = false;
  }
};

const loadUsers = async () => {
  isUsersLoading.value = true;
  try {
    const token = localStorage.getItem("access_token");
    const res = await fetch(`${API_URL}/admin/users`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Erreur lors du chargement des utilisateurs");
    users.value = await res.json();
  } catch (err) {
    console.error(err.message);
  } finally {
    isUsersLoading.value = false;
  }
};

const filteredUsers = computed(() => {
  if (!userSearchQuery.value) return users.value;
  const q = userSearchQuery.value.toLowerCase();
  return users.value.filter(u => 
    u.username.toLowerCase().includes(q) ||
    (u.nom && u.nom.toLowerCase().includes(q)) ||
    (u.prenom && u.prenom.toLowerCase().includes(q))
  );
});

const openUserEditForm = (user) => {
  isEditingUser.value = true;
  isCreatingUser.value = false;
  selectedStudent.value = null; // Close dashboard if open
  userFormData.value = {
    username: user.username,
    nom: user.nom || "",
    prenom: user.prenom || ""
  };
};

const openCreateUserForm = () => {
  isCreatingUser.value = true;
  isEditingUser.value = false;
  selectedStudent.value = null;
  newUserFormData.value = {
    username: "",
    password: "",
    nom: "",
    prenom: ""
  };
};

const cancelUserEdit = () => {
  isEditingUser.value = false;
};

const cancelUserCreate = () => {
  isCreatingUser.value = false;
};

const submitUserForm = async () => {
  isUpdatingUser.value = true;
  try {
    const token = localStorage.getItem("access_token");
    const res = await fetch(`${API_URL}/admin/users/${userFormData.value.username}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({
        nom: userFormData.value.nom,
        prenom: userFormData.value.prenom
      })
    });
    
    if (!res.ok) throw new Error("Erreur lors de la mise à jour");
    
    alert("Utilisateur mis à jour avec succès !");
    isEditingUser.value = false;
    loadUsers();
  } catch (err) {
    alert(err.message);
  } finally {
    isUpdatingUser.value = false;
  }
};

const submitCreateUserForm = async () => {
  if (!newUserFormData.value.username || !newUserFormData.value.password) {
    alert("L'identifiant et le mot de passe sont requis.");
    return;
  }

  isAddingUser.value = true;
  try {
    const token = localStorage.getItem("access_token");
    const res = await fetch(`${API_URL}/admin/users`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify(newUserFormData.value)
    });
    
    if (!res.ok) {
      const errorData = await res.json();
      throw new Error(errorData.detail || "Erreur lors de la création");
    }
    
    alert("Utilisateur créé avec succès !");
    isCreatingUser.value = false;
    loadUsers();
  } catch (err) {
    alert(err.message);
  } finally {
    isAddingUser.value = false;
  }
};

const viewUserDashboard = (username) => {
  isEditingUser.value = false;
  isCreatingUser.value = false;
  selectedStudent.value = users.value.find(u => u.username === username) || { username };
};

const resetUserPassword = async (username) => {
  const newPass = prompt(`Entrez le nouveau mot de passe pour ${username} :`);
  if (!newPass) return;

  try {
    const token = localStorage.getItem("access_token");
    const res = await fetch(`${API_URL}/admin/users/reset-password`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}` 
      },
      body: JSON.stringify({ username, new_password: newPass })
    });
    if (!res.ok) throw new Error("Erreur lors de la réinitialisation");
    alert(`Le mot de passe de ${username} a été réinitialisé.`);
  } catch (err) {
    alert(err.message);
  }
};

const triggerUserCSVInput = () => {
  if (userCsvInput.value) {
    userCsvInput.value.click();
  }
};

const handleUserCSVUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  if (!confirm("ATTENTION : L'importation d'un fichier CSV EFFACERA TOUS les utilisateurs existants et TOUT l'historique de leur progression. Êtes-vous sûr de vouloir continuer ?")) {
    event.target.value = ""; // Reset input
    return;
  }

  isImportingUsers.value = true;
  const token = localStorage.getItem("access_token");
  
  try {
    const formData = new FormData();
    formData.append("file", file);

    const res = await fetch(`${API_URL}/admin/users/import`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`
      },
      body: formData
    });

    if (!res.ok) {
      const errData = await res.json();
      throw new Error(errData.detail || "Erreur lors de l'importation");
    }

    const data = await res.json();
    alert(data.message);
    loadUsers(); // Refresh the list
  } catch (err) {
    alert("Erreur: " + err.message);
  } finally {
    isImportingUsers.value = false;
    event.target.value = ""; // Reset input
  }
};

const exportUsers = () => {
  if (users.value.length === 0) {
    alert("Aucun utilisateur à exporter.");
    return;
  }
  
  const header = "nom,prenom,login\n";
  const rows = users.value.map(u => 
    `"${u.nom || ''}","${u.prenom || ''}","${u.username}"`
  ).join("\n");
  
  const csvContent = header + rows;
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.setAttribute("href", url);
  link.setAttribute("download", "utilisateurs_exopy.csv");
  link.style.visibility = 'hidden';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const exportExercises = async () => {
  try {
    const token = localStorage.getItem("access_token");
    const res = await fetch(`${API_URL}/admin/exercises/export`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Erreur lors de l'exportation des exercices");
    const data = await res.json();
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "exercices_exopy.json";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch (err) {
    alert("Erreur d'exportation : " + err.message);
  }
};

onMounted(() => {
  loadExercises();
  loadUsers();
});

const resetForm = () => {
  formData.value = { id: null, titre: "", niveau: "1", enonce: "", test: "" };
  isEditing.value = false;
  showForm.value = false;
};

const openCreateForm = () => {
  resetForm();
  showForm.value = true;
};

const openEditForm = async (id) => {
  resetForm();
  try {
    const token = localStorage.getItem("access_token");
    const res = await fetch(API_URL + `/exercise/${id}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error("Erreur lors de la récupération");
    const data = await res.json();
    
    formData.value = {
      id: data.id,
      titre: data.title,
      niveau: String(data.niveau),
      enonce: data.enonce,
      test: data.test
    };
    isEditing.value = true;
    showForm.value = true;
  } catch (err) {
    alert("Impossible de charger l'exercice : " + err.message);
  }
};

const submitForm = async () => {
  const token = localStorage.getItem("access_token");
  const method = isEditing.value ? "PUT" : "POST";
  const url = isEditing.value 
    ? `${API_URL}/admin/exercise/${formData.value.id}` 
    : `${API_URL}/admin/exercise`;

  try {
    const res = await fetch(url, {
      method,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({
        titre: formData.value.titre,
        niveau: formData.value.niveau,
        enonce: formData.value.enonce,
        test: formData.value.test
      })
    });
    
    if (!res.ok) {
       const errData = await res.json();
       throw new Error(errData.detail || "Erreur lors de la sauvegarde.");
    }
    
    alert(`Exercice ${isEditing.value ? 'mis à jour' : 'créé'} avec succès !`);
    resetForm();
    loadExercises();
  } catch(err) {
    alert("Erreur: " + err.message);
  }
};

const generateWithAI = async () => {
  if (isGenerating.value) return;
  
  isGenerating.value = true;
  const token = localStorage.getItem("access_token");
  try {
    const res = await fetch(`${API_URL}/admin/exercises/generate`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`
      },
      body: JSON.stringify({
        difficulty: formData.value.niveau,
        existing_titles: exercises.value.map(ex => ex.title)
      })
    });
    
    if (!res.ok) throw new Error("Erreur lors de la génération par l'IA");
    const data = await res.json();
    
    if (data.error) throw new Error(data.error);

    formData.value.titre = data.titre || "";
    formData.value.enonce = data.enonce || "";
    formData.value.test = data.test || "";
    
    alert("Exercice généré par l'IA avec succès ! Vous pouvez maintenant le vérifier et le modifier.");
  } catch (err) {
    alert("Erreur IA: " + err.message);
  } finally {
    isGenerating.value = false;
  }
};

const deleteExercise = async (id) => {
  if (!confirm("Êtes-vous sûr de vouloir supprimer définitivement cet exercice ?")) return;
  
  const token = localStorage.getItem("access_token");
  try {
    const res = await fetch(`${API_URL}/admin/exercise/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` }
    });
    
    if (!res.ok) throw new Error("Erreur lors de la suppression");
    alert("Exercice supprimé.");
    loadExercises();
  } catch(err) {
    alert("Erreur: " + err.message);
  }
};

const draggedIndex = ref(null);

const onDragStart = (index) => {
  draggedIndex.value = index;
};

const onDragOver = (event) => {
  event.preventDefault();
};

const onDrop = async (event, index) => {
  if (draggedIndex.value === null || draggedIndex.value === index) return;
  
  const movedItem = exercises.value.splice(draggedIndex.value, 1)[0];
  exercises.value.splice(index, 0, movedItem);
  draggedIndex.value = null;

  // Persist the new order
  const token = localStorage.getItem("access_token");
  try {
    const res = await fetch(`${API_URL}/admin/exercises/reorder`, {
      method: "POST",
      headers: { 
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}` 
      },
      body: JSON.stringify({ ids: exercises.value.map(ex => ex.id) })
    });
    if (!res.ok) throw new Error("Erreur lors de la sauvegarde de l'ordre");
  } catch (err) {
    alert("Erreur: " + err.message);
    loadExercises(); // Rollback to server state
  }
};

const fileInput = ref(null);
const triggerFileInput = () => {
  if (fileInput.value) {
    fileInput.value.click();
  }
};

const handleFileUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = async (e) => {
    const text = e.target.result;
    let exercisesToImport = [];
    
    // Check if it's JSON
    if (text.trim().startsWith('[') || text.trim().startsWith('{')) {
      try {
        exercisesToImport = JSON.parse(text);
        if (!Array.isArray(exercisesToImport)) exercisesToImport = [exercisesToImport];
      } catch (err) {
        console.warn("Échec du parsing JSON, tentative de parsing texte classique.");
      }
    }
    
    if (exercisesToImport.length === 0) {
      exercisesToImport = parseExercisesFromText(text);
    }
    
    if (exercisesToImport.length === 0) {
      alert("Aucun exercice lisible trouvé dans le fichier.");
      return;
    }

    if (!confirm(`${exercisesToImport.length} exercices détectés. Voulez-vous les importer ?`)) {
      return;
    }

    const token = localStorage.getItem("access_token");
    let successCount = 0;
    
    for (const ex of exercisesToImport) {
      try {
        const res = await fetch(`${API_URL}/admin/exercise`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`
          },
          body: JSON.stringify(ex)
        });
        if (res.ok) successCount++;
      } catch (err) {
        console.error("Erreur d'import pour", ex.titre, err);
      }
    }
    
    alert(`Import terminé ! ${successCount}/${exercisesToImport.length} exercices ajoutés.`);
    loadExercises();
  };
  reader.readAsText(file);
};

function parseExercisesFromText(text) {
  if (text.includes(';;;')) {
    const results = [];
    const parts = text.split(';;;').map(p => p.trim()).filter(p => p !== "");
    for (let i = 0; i + 4 < parts.length; i += 5) {
      results.push({
        titre: parts[i],
        niveau: parts[i + 1],
        enonce: parts[i + 3],
        test: parts[i + 4]
      });
    }
    if (results.length > 0) return results;
  }

  const results = [];
  const blocks = text.split(/(?=### |^---$|^===+$)/m).map(b => b.trim()).filter(b => b.length > 5);

  blocks.forEach(block => {
    let titleStr = "Exercice Importé";
    let levelStr = "1";
    let enonceStr = "";
    let testStr = "";
    
    const lines = block.split('\n');
    const firstLine = lines[0].replace(/#|-|=/g, '').trim();
    if (firstLine.length > 3 && firstLine.length < 100) {
      titleStr = firstLine;
    }
    
    const lowerBlock = block.toLowerCase();
    const testIndex = Math.max(
      lowerBlock.lastIndexOf("test:"),
      lowerBlock.lastIndexOf("tests:"),
      lowerBlock.lastIndexOf("def test"),
      lowerBlock.lastIndexOf("try:\n"),
      lowerBlock.lastIndexOf("```python\ntry")
    );

    if (testIndex !== -1 && testIndex > 10) {
      enonceStr = block.substring(0, testIndex).replace(lines[0], '').trim();
      testStr = block.substring(testIndex).replace(/test:|tests:/i, '').trim();
    } else {
      enonceStr = block.replace(lines[0], '').trim();
      testStr = "c = \"\"\ntry:\n    # TODO: Ajouter des assertions ici\n    if True: \n        c += '1'\n    else:\n        c += '0'\nexcept:\n    c += '0'\"";
    }
    
    if (enonceStr.length < 5) enonceStr = "Veuillez écrire l'énoncé ici.";
    
    results.push({
      titre: titleStr,
      niveau: levelStr,
      enonce: enonceStr,
      test: testStr
    });
  });

  return results;
}
</script>

<template>
  <div class="fixed inset-0 bg-white dark:bg-zinc-900 z-[100] flex flex-col h-screen overflow-hidden text-zinc-800 dark:text-zinc-200 transition-colors duration-300">
    <!-- Header Admin -->
    <header class="bg-zinc-50 dark:bg-zinc-800 p-6 flex justify-between items-center shadow-sm">
      <div class="flex items-center gap-8">
        <div class="flex items-center gap-4">
          <div class="w-10 h-10 rounded-2xl bg-blue-600 flex items-center justify-center font-black text-white shadow-lg shadow-blue-500/20">
            A
          </div>
          <h1 class="text-xl font-black text-zinc-800 dark:text-white tracking-widest uppercase italic">Panel Admin</h1>
        </div>
        
        <!-- Tabs -->
        <nav class="flex gap-1 bg-zinc-200/50 dark:bg-zinc-950/50 p-1.5 rounded-2xl border border-zinc-200 dark:border-zinc-800 shadow-inner">
          <button 
            @click="currentTab = 'exercises'"
            :class="currentTab === 'exercises' ? 'bg-white dark:bg-zinc-800 text-blue-600 dark:text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-300'"
            class="px-6 py-2 rounded-xl text-xs font-black transition-all uppercase tracking-widest"
          >
            Exercices
          </button>
          <button 
            @click="currentTab = 'users'"
            :class="currentTab === 'users' ? 'bg-white dark:bg-zinc-800 text-blue-600 dark:text-white shadow-sm' : 'text-zinc-500 hover:text-zinc-800 dark:hover:text-zinc-300'"
            class="px-6 py-2 rounded-xl text-xs font-black transition-all uppercase tracking-widest"
          >
            Utilisateurs
          </button>
        </nav>
      </div>
      <button @click="$emit('close')" class="px-6 py-2 bg-zinc-100 dark:bg-zinc-700 hover:bg-zinc-200 dark:hover:bg-zinc-600 text-zinc-600 dark:text-white rounded-xl font-black text-xs uppercase tracking-widest transition-all border border-zinc-200 dark:border-zinc-600 shadow-sm">
        Quitter
      </button>
    </header>

    <div class="flex-1 flex overflow-hidden">
      <!-- TAB EXERCICES -->
      <template v-if="currentTab === 'exercises'">
        <!-- Liste des exercices (Sidebar) -->
        <aside class="w-80 flex-shrink-0 border-r border-zinc-200 dark:border-zinc-800 flex flex-col bg-zinc-50/50 dark:bg-zinc-800/50 transition-colors duration-300">
          <div class="p-6 border-b border-zinc-200 dark:border-zinc-800 flex justify-between items-center">
            <h2 class="font-black text-zinc-800 dark:text-zinc-100 uppercase tracking-widest text-xs">Vos Exercices</h2>
            <button @click="openCreateForm" class="p-2 bg-blue-600/10 hover:bg-blue-600/20 text-blue-600 dark:text-blue-400 rounded-xl transition-all shadow-sm border border-blue-600/20" title="Créer un exercice">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
              </svg>
            </button>
          </div>
          
          <div class="px-6 py-4 border-b border-zinc-100 dark:border-zinc-800/50 bg-white/50 dark:bg-transparent">
            <input type="file" ref="fileInput" accept=".txt" class="hidden" @change="handleFileUpload" />
            <button @click="triggerFileInput" class="w-full flex items-center justify-center gap-2 py-3 px-4 bg-white dark:bg-zinc-900 hover:bg-zinc-50 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-300 rounded-xl font-black transition-all border border-zinc-200 dark:border-zinc-700 text-[10px] text-center uppercase tracking-widest shadow-sm">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 inline" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM6.293 6.707a1 1 0 010-1.414l3-3a1 1 0 011.414 0l3 3a1 1 0 01-1.414 1.414L11 5.414V13a1 1 0 11-2 0V5.414L7.707 6.707a1 1 0 01-1.414 0z" clip-rule="evenodd" />
              </svg>
              Importer (.json, .txt)
            </button>
            <button @click="exportExercises" class="w-full mt-2 flex items-center justify-center gap-2 py-3 px-4 bg-white dark:bg-zinc-900 hover:bg-zinc-50 dark:hover:bg-zinc-800 text-zinc-600 dark:text-zinc-300 rounded-xl font-black transition-all border border-zinc-200 dark:border-zinc-700 text-[10px] text-center uppercase tracking-widest shadow-sm">
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 mr-1 inline" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M3 17a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM10 3a1 1 0 011 1v8.586l1.293-1.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 111.414-1.414L9 12.586V4a1 1 0 011-1z" clip-rule="evenodd" />
              </svg>
              Exporter (.json)
            </button>
          </div>

          <div class="flex-1 overflow-y-auto p-4 custom-scrollbar">
            <div v-if="isLoading" class="flex justify-center py-8">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
            <div v-else-if="errorMsg" class="text-red-500 text-xs py-4 text-center font-bold">{{ errorMsg }}</div>
            <ul v-else class="space-y-2">
               <li 
                  v-for="(ex, index) in exercises" 
                  :key="ex.id" 
                  draggable="true"
                  @dragstart="onDragStart(index)"
                  @dragover="onDragOver"
                  @drop="onDrop($event, index)"
                  class="flex items-center justify-between p-4 bg-transparent border border-transparent rounded-2xl hover:bg-white dark:hover:bg-zinc-800 hover:shadow-sm dark:hover:shadow-none hover:border-zinc-200 dark:hover:border-zinc-700 transition-all cursor-move group"
               >
                  <div class="flex items-center gap-4 flex-1 min-w-0 pr-4">
                    <div class="text-zinc-300 dark:text-zinc-600 group-hover:text-zinc-400">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                        <path fill-rule="evenodd" d="M3 5a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 10a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1zM3 15a1 1 0 011-1h12a1 1 0 110 2H4a1 1 0 01-1-1z" clip-rule="evenodd" />
                      </svg>
                    </div>
                    <div class="flex-1 min-w-0">
                      <p class="font-bold text-zinc-700 dark:text-zinc-200 truncate text-sm tracking-tight group-hover:text-zinc-900 dark:group-hover:text-white transition-colors">{{ ex.title.toUpperCase() }}</p>
                      <p class="text-[9px] text-zinc-400 dark:text-zinc-500 font-black uppercase tracking-widest mt-0.5">Niveau {{ ex.niveau }}</p>
                    </div>
                  </div>
                  <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button @click.stop="openEditForm(ex.id)" class="p-1.5 text-zinc-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                      </svg>
                    </button>
                    <button @click.stop="deleteExercise(ex.id)" class="p-1.5 text-zinc-400 hover:text-red-500 transition-colors">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
               </li>
            </ul>
          </div>
        </aside>

        <!-- Éditeur principal -->
        <main class="flex-1 bg-zinc-50 dark:bg-zinc-900/40 p-8 overflow-y-auto custom-scrollbar transition-colors duration-300">
          <div v-if="!showForm" class="h-full flex flex-col items-center justify-center text-zinc-400 dark:text-zinc-600 transition-opacity animate-in fade-in duration-700">
             <div class="w-24 h-24 rounded-[2.5rem] bg-white dark:bg-zinc-800 flex items-center justify-center mb-8 shadow-xl border border-zinc-100 dark:border-zinc-700/50">
               <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                 <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
               </svg>
             </div>
             <p class="text-[10px] font-black uppercase tracking-[0.4em] opacity-40 text-center">Gestionnaire d'exercices</p>
             <p class="text-xs opacity-60 mt-4 italic text-center max-w-xs font-medium">Sélectionnez un exercice pour commencer l'édition ou créez-en un nouveau</p>
          </div>
          
          <div v-else class="max-w-[1400px] px-8 mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
             <div class="flex justify-between items-end border-b border-zinc-200 dark:border-zinc-800 pb-6">
               <div>
                  <h2 class="text-xs font-black text-blue-600 dark:text-blue-400 uppercase tracking-widest mb-2">Configuration</h2>
                  <h1 class="text-3xl font-black text-zinc-800 dark:text-white px-0 tracking-tighter italic">
                    {{ isEditing ? 'Modifier l\'exercice' : 'Nouvel exercice' }}
                  </h1>
               </div>
               <div class="text-[10px] font-black text-zinc-400 dark:text-zinc-500 bg-white dark:bg-zinc-800 px-4 py-2 rounded-xl border border-zinc-200 dark:border-zinc-700 uppercase tracking-widest shadow-sm">
                 {{ isEditing ? 'ID: ' + formData.id : 'Mode Création' }}
               </div>
             </div>

             <!-- Titre & Niveau -->
             <div class="grid grid-cols-3 gap-8">
                <div class="col-span-2 space-y-3">
                  <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest ml-1">Titre de l'exercice</label>
                  <input v-model="formData.titre" type="text" class="w-full bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-2xl p-4 text-zinc-800 dark:text-white font-bold tracking-tight focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-sm" placeholder="Ex: Fibonacci Master">
                </div>
                <div class="space-y-3">
                  <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest ml-1">Difficulté</label>
                  <div class="relative">
                    <select v-model="formData.niveau" class="w-full bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-2xl p-4 text-zinc-800 dark:text-white font-bold focus:ring-2 focus:ring-blue-500 outline-none transition-all appearance-none cursor-pointer shadow-sm">
                      <option value="1">🟢 Très facile</option>
                      <option value="2">🔵 Facile</option>
                      <option value="3">🔴 Difficile</option>
                      <option value="4">⚫ Expert</option>
                    </select>
                    <div class="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-zinc-400">
                      <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
                      </svg>
                    </div>
                  </div>
                </div>
             </div>

             <!-- Énoncé Markdown -->
             <div class="space-y-3">
                <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest ml-1">Énoncé (Markdown)</label>
                <div class="grid grid-cols-2 gap-6 h-[400px]">
                   <textarea 
                      v-model="formData.enonce" 
                      class="w-full h-full bg-white dark:bg-zinc-800 border border-zinc-200 dark:border-zinc-700 rounded-[2rem] p-6 font-mono text-sm text-zinc-700 dark:text-zinc-300 focus:ring-2 focus:ring-blue-500 outline-none custom-scrollbar resize-none transition-all shadow-sm" 
                      placeholder="Décrivez l'exercice ici..."
                   ></textarea>
                   
                   <!-- Aperçu sécurisé -->
                   <div class="w-full h-full bg-white dark:bg-zinc-950/40 border border-zinc-200 dark:border-zinc-800 rounded-[2rem] p-6 overflow-y-auto custom-scrollbar prose dark:prose-invert prose-sm max-w-none shadow-inner">
                      <div v-if="!formData.enonce" class="text-zinc-400 italic text-xs flex items-center justify-center h-full font-medium">L'aperçu apparaîtra ici...</div>
                      <div v-else v-html="safeEnoncePreview"></div>
                   </div>
                </div>
             </div>

             <!-- Code des tests -->
             <div class="space-y-3">
                <div class="flex justify-between items-center ml-1">
                  <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest">Validation Python (Caché)</label>
                  <span class="text-[9px] text-emerald-600 dark:text-emerald-500 font-black uppercase tracking-widest opacity-80 italic">Ajoutez '1' à `c` pour valider</span>
                </div>
                <textarea 
                   v-model="formData.test" 
                   class="w-full h-48 bg-zinc-900 border border-zinc-800 rounded-[2rem] p-6 font-mono text-sm text-emerald-400 focus:ring-2 focus:ring-emerald-500/50 outline-none custom-scrollbar shadow-2xl"
                   placeholder="try:\n    assert solution() == expected\n    c.append('1')\nexcept:\n    c.append('0')"
                ></textarea>
             </div>
             
              <div class="flex justify-between items-center pt-8 border-t border-zinc-200 dark:border-zinc-800">
                <button 
                  @click="generateWithAI" 
                  :disabled="isGenerating"
                  class="flex items-center gap-3 px-8 py-4 rounded-2xl font-black text-[10px] uppercase tracking-[0.2em] text-amber-600 dark:text-amber-500 bg-amber-50 dark:bg-amber-500/5 border border-amber-200 dark:border-amber-500/20 hover:bg-amber-100 dark:hover:bg-amber-500/10 transition-all disabled:opacity-30 shadow-sm"
                >
                  <svg v-if="isGenerating" class="animate-spin h-4 w-4 text-amber-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  <span v-else class="text-lg">✨</span>
                  {{ isGenerating ? 'Magie en cours...' : 'Générer via IA' }}
                </button>
                
                <div class="flex gap-4">
                  <button @click="resetForm" class="px-8 py-4 rounded-2xl font-black text-[10px] text-zinc-400 hover:text-red-500 transition-colors uppercase tracking-widest">Annuler</button>
                  <button @click="submitForm" class="px-10 py-4 rounded-2xl font-black text-[11px] text-white bg-blue-600 hover:bg-blue-500 transition-all shadow-xl shadow-blue-500/20 uppercase tracking-[0.2em]">
                    {{ isEditing ? 'Sauvegarder' : 'Publier l\'exercice' }}
                  </button>
                </div>
              </div>
          </div>
        </main>
      </template>

      <!-- TAB UTILISATEURS -->
      <template v-else-if="currentTab === 'users'">
        <!-- Sidebar Utilisateurs -->
        <aside class="w-80 flex-shrink-0 border-r border-zinc-200 dark:border-zinc-800 flex flex-col bg-zinc-50/50 dark:bg-zinc-800/50 transition-colors duration-300">
          <div class="p-6 border-b border-zinc-200 dark:border-zinc-800">
            <h2 class="font-black text-zinc-800 dark:text-zinc-100 uppercase tracking-widest text-xs mb-4">Élèves</h2>
            <div class="relative mb-4">
              <input 
                v-model="userSearchQuery" 
                type="text" 
                placeholder="Rechercher..." 
                class="w-full bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl p-3 pl-10 text-sm focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-500 outline-none transition-all shadow-sm dark:shadow-none dark:text-white"
              >
              <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4 absolute left-3.5 top-3.5 text-zinc-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            
<div class="flex gap-2 mb-4">
  <button 
    @click="openCreateUserForm"
    class="flex-1 flex items-center justify-center gap-2 py-2.5 px-3 bg-blue-600 hover:bg-blue-500 text-white rounded-xl font-bold transition-all shadow-sm text-[10px] uppercase tracking-wider"
  >
    <svg xmlns="http://www.w3.org/2000/svg" class="h-3.5 w-3.5" viewBox="0 0 20 20" fill="currentColor">
      <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
    </svg>
    Ajouter
  </button>
  <input type="file" ref="userCsvInput" accept=".csv" class="hidden" @change="handleUserCSVUpload" />
  <button 
    @click="triggerUserCSVInput" 
    :disabled="isImportingUsers"
    class="flex-1 flex items-center justify-center gap-2 py-2.5 px-3 bg-white dark:bg-zinc-800 hover:bg-zinc-100 dark:hover:bg-zinc-700 text-zinc-600 dark:text-zinc-300 rounded-xl font-bold transition-all border border-zinc-200 dark:border-zinc-700 text-[10px] uppercase tracking-wider shadow-sm disabled:opacity-50"
  >
                <svg v-if="isImportingUsers" class="animate-spin h-3 w-3 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                <span v-else>Importer</span>
              </button>
              <button 
                @click="exportUsers"
                class="flex-1 flex items-center justify-center gap-2 py-2.5 px-3 bg-white dark:bg-zinc-800 hover:bg-zinc-100 dark:hover:bg-zinc-700 text-zinc-600 dark:text-zinc-300 rounded-xl font-bold transition-all border border-zinc-200 dark:border-zinc-700 text-[10px] uppercase tracking-wider shadow-sm"
              >
                Exporter
              </button>
            </div>
          </div>
          
          <div class="flex-1 overflow-y-auto p-4 custom-scrollbar">
            <div v-if="isUsersLoading" class="flex justify-center py-8">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>
            <ul v-else class="space-y-2">
              <li 
                v-for="user in filteredUsers" 
                :key="user.username"
                @click="viewUserDashboard(user.username)"
                :class="selectedStudent && selectedStudent.username === user.username 
                  ? 'bg-blue-600/10 border-blue-500/30' 
                  : 'bg-transparent border-transparent hover:bg-white dark:hover:bg-zinc-800/80 hover:shadow-sm'"
                class="p-3 rounded-2xl border transition-all cursor-pointer flex items-center justify-between group"
              >
                <div class="flex items-center gap-3 overflow-hidden">
                  <div 
                    class="w-9 h-9 rounded-xl flex-shrink-0 flex items-center justify-center text-xs font-black transition-all shadow-sm"
                    :class="selectedStudent && selectedStudent.username === user.username ? 'bg-blue-600 text-white' : 'bg-white dark:bg-zinc-900 text-zinc-400 border border-zinc-100 dark:border-zinc-700'"
                  >
                    {{ (user.prenom || user.username).substring(0, 2).toUpperCase() }}
                  </div>
                  <div class="flex flex-col min-w-0">
                    <span 
                      class="font-bold tracking-tight text-sm transition-colors truncate"
                      :class="selectedStudent && selectedStudent.username === user.username ? 'text-blue-600 dark:text-blue-400' : 'text-zinc-700 dark:text-zinc-300 group-hover:text-zinc-900 dark:group-hover:text-white'"
                    >
                      {{ user.nom }} {{ user.prenom }}
                      <span v-if="!user.prenom && !user.nom">{{ user.username }}</span>
                    </span>
                    <span class="text-[9px] text-zinc-400 dark:text-zinc-500 font-black uppercase tracking-widest truncate">@{{ user.username }}</span>
                  </div>
                </div>
                <div class="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button @click.stop="openUserEditForm(user)" class="p-1.5 text-zinc-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors">
                    <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                  </button>
                </div>
              </li>
            </ul>
          </div>
        </aside>

        <!-- Zone d'affichage (Dashboard ou Form) -->
        <main class="flex-1 bg-zinc-50 dark:bg-zinc-900/40 p-8 overflow-y-auto custom-scrollbar relative transition-colors duration-300">
          <!-- Create User Form -->
          <div v-if="isCreatingUser" class="max-w-4xl mx-auto space-y-8 bg-white dark:bg-zinc-800 p-10 rounded-[2.5rem] shadow-2xl border border-zinc-100 dark:border-zinc-700 transition-all animate-in fade-in zoom-in-95 duration-500">
            <div class="flex justify-between items-start border-b border-zinc-100 dark:border-zinc-700 pb-6">
               <div>
                 <h2 class="text-xs font-black text-blue-600 dark:text-blue-400 uppercase tracking-widest mb-2">Nouvel Élève</h2>
                 <h1 class="text-3xl font-black text-zinc-800 dark:text-white tracking-tight italic">Création Manuelle</h1>
               </div>
               <button @click="cancelUserCreate" class="p-2 text-zinc-400 hover:text-red-500 transition-colors bg-zinc-50 dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-700 shadow-sm">
                 <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                   <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                 </svg>
               </button>
            </div>

            <div class="grid grid-cols-2 gap-8">
              <div class="space-y-6">
                <div class="space-y-3">
                  <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest ml-1">Identifiant (login)</label>
                  <input v-model="newUserFormData.username" type="text" class="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-2xl p-4 text-zinc-800 dark:text-white font-bold focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-inner" placeholder="ex: jdupont">
                </div>
                <div class="space-y-3">
                  <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest ml-1">Mot de passe provisoire</label>
                  <input v-model="newUserFormData.password" type="password" class="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-2xl p-4 text-zinc-800 dark:text-white font-bold focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-inner" placeholder="••••••••">
                </div>
              </div>
              
              <div class="space-y-6">
                <div class="space-y-3">
                  <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest ml-1">Prénom</label>
                  <input v-model="newUserFormData.prenom" type="text" class="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-2xl p-4 text-zinc-800 dark:text-white font-bold focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-inner" placeholder="Jean">
                </div>
                <div class="space-y-3">
                  <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest ml-1">Nom</label>
                  <input v-model="newUserFormData.nom" type="text" class="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-2xl p-4 text-zinc-800 dark:text-white font-bold focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-inner" placeholder="Dupont">
                </div>
              </div>
            </div>

            <div class="flex justify-end gap-4 pt-8 border-t border-zinc-100 dark:border-zinc-700">
              <button @click="cancelUserCreate" class="px-8 py-4 rounded-xl font-black text-[10px] text-zinc-400 hover:text-red-500 transition-colors uppercase tracking-widest">Annuler</button>
              <button 
                @click="submitCreateUserForm" 
                :disabled="isAddingUser"
                class="px-10 py-4 rounded-xl font-black text-[11px] text-white bg-blue-600 hover:bg-blue-500 transition-all shadow-xl shadow-blue-500/20 uppercase tracking-[0.2em] flex items-center gap-3 disabled:opacity-50"
              >
                <svg v-if="isAddingUser" class="animate-spin h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Créer le compte
              </button>
            </div>
          </div>

          <!-- Edit User Form -->
          <div v-if="isEditingUser" class="max-w-4xl mx-auto space-y-8 bg-white dark:bg-zinc-800 p-10 rounded-[2.5rem] shadow-2xl border border-zinc-100 dark:border-zinc-700 transition-all duration-300">
            <div class="flex justify-between items-start border-b border-zinc-100 dark:border-zinc-700 pb-6">
               <div>
                 <h2 class="text-xs font-black text-blue-600 dark:text-blue-400 uppercase tracking-widest mb-2">Édition de Profil</h2>
                 <h1 class="text-3xl font-black text-zinc-800 dark:text-white tracking-tight italic">@{{ userFormData.username }}</h1>
               </div>
               <button @click="cancelUserEdit" class="p-2 text-zinc-400 hover:text-red-500 transition-colors bg-zinc-50 dark:bg-zinc-900 rounded-xl border border-zinc-100 dark:border-zinc-700 shadow-sm">
                 <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                   <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
                 </svg>
               </button>
            </div>

            <div class="space-y-8">
              <div class="grid grid-cols-2 gap-6">
                <div class="space-y-3">
                  <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest ml-1">Prénom</label>
                  <input v-model="userFormData.prenom" type="text" class="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-2xl p-4 text-zinc-800 dark:text-white font-bold focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-inner">
                </div>
                <div class="space-y-3">
                  <label class="block text-[10px] font-black text-zinc-400 dark:text-zinc-500 uppercase tracking-widest ml-1">Nom</label>
                  <input v-model="userFormData.nom" type="text" class="w-full bg-zinc-50 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-2xl p-4 text-zinc-800 dark:text-white font-bold focus:ring-2 focus:ring-blue-500 outline-none transition-all shadow-inner">
                </div>
              </div>

              <div class="pt-8 border-t border-zinc-100 dark:border-zinc-700 space-y-4">
                <button @click="resetUserPassword(userFormData.username)" class="w-full py-4 rounded-2xl font-black text-[10px] text-amber-600 dark:text-amber-500 bg-amber-50 dark:bg-amber-500/5 border border-amber-200 dark:border-amber-500/20 hover:bg-amber-100 dark:hover:bg-amber-500/10 transition-all uppercase tracking-widest shadow-sm">
                  Réinitialiser le mot de passe
                </button>
                <button @click="submitUserForm" :disabled="isUpdatingUser" class="w-full py-5 rounded-2xl font-black text-xs text-white bg-blue-600 hover:bg-blue-500 transition-all shadow-xl shadow-blue-500/20 uppercase tracking-[0.2em] disabled:opacity-50">
                  {{ isUpdatingUser ? 'Magie en cours...' : 'Sauvegarder les modifications' }}
                </button>
              </div>
            </div>
          </div>

          <!-- Empty State -->
          <div v-else-if="!selectedStudent" class="h-full flex flex-col items-center justify-center text-zinc-400 transition-opacity animate-in fade-in duration-700">
            <div class="w-24 h-24 rounded-[2.5rem] bg-white dark:bg-zinc-800 flex items-center justify-center mb-8 shadow-xl border border-zinc-100 dark:border-zinc-700/50">
               <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-blue-500 dark:text-blue-400 opacity-80" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                 <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
               </svg>
             </div>
             <p class="text-[10px] font-black uppercase tracking-[0.4em] opacity-40 text-center">Analyses des performances</p>
             <p class="text-xs opacity-60 mt-4 italic text-center max-w-xs font-medium">Sélectionnez un élève pour synchroniser ses données de progression et visualiser ses performances en temps réel</p>
          </div>
          
          <!-- Student Dashboard -->
          <div v-else class="h-full flex flex-col transition-all animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div class="flex justify-between items-end mb-8 pb-6 border-b border-zinc-200 dark:border-zinc-700">
              <div class="flex items-center gap-6">
                <div class="w-16 h-16 rounded-[1.5rem] bg-blue-600 flex items-center justify-center text-xl font-black text-white shadow-xl shadow-blue-500/20">
                  {{ (selectedStudent.prenom || selectedStudent.username).substring(0, 1).toUpperCase() }}
                </div>
                <div>
                  <h2 class="text-[10px] font-black text-blue-600 dark:text-blue-400 uppercase tracking-widest mb-1">Dossier Étudiant</h2>
                  <h1 class="text-3xl font-black text-zinc-800 dark:text-white px-0 tracking-tighter">
                    <template v-if="selectedStudent.prenom || selectedStudent.nom">
                      {{ selectedStudent.prenom }} {{ selectedStudent.nom }}
                    </template>
                    <template v-else>
                      {{ selectedStudent.username.toUpperCase() }}
                    </template>
                  </h1>
                </div>
              </div>
              <button @click="selectedStudent = null" class="px-5 py-2.5 text-[10px] font-black text-zinc-400 hover:text-white bg-white dark:bg-zinc-800 hover:bg-zinc-900 border border-zinc-200 dark:border-zinc-700 rounded-xl uppercase tracking-widest transition-all shadow-sm">
                Fermer
              </button>
            </div>
            
            <div class="flex-1 bg-white dark:bg-zinc-950/20 rounded-[3rem] border border-zinc-200 dark:border-zinc-800/50 p-4 lg:p-10 shadow-2xl relative overflow-hidden transition-colors duration-300">
              <div class="absolute -top-40 -right-40 w-80 h-80 bg-blue-500/10 dark:bg-blue-600/5 blur-[100px] rounded-full pointer-events-none"></div>
              <Dashboard :key="selectedStudent.username" :studentId="selectedStudent.username" />
            </div>
          </div>
        </main>
      </template>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: #3f3f46 transparent;
}
.custom-scrollbar::-webkit-scrollbar {
  width: 5px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #3f3f46;
  border-radius: 10px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background-color: #52525b;
}

/* Animations simples */
.v-enter-active, .v-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.v-enter-from, .v-leave-to {
  opacity: 0;
  transform: translateY(10px);
}
</style>
