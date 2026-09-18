<script setup>
defineProps(["isDarkMode"]);
const emit = defineEmits(["close"]);

const sections = [
  {
    icon: "🔬",
    color: "indigo",
    title: "Export recherche",
    items: [
      { label: "Données pseudonymisées", text: "Export des traces d'activité de la classe (tentatives, réussites, aide IA...) sous un identifiant pseudonymisé stable, utilisable pour une analyse externe ou une étude." },
      { label: "Consentement", text: "Seuls les élèves ayant donné leur consentement recherche (géré dans l'onglet Élèves) sont inclus dans l'export." },
      { label: "Choix des champs", text: "Le bouton \"Choisir les champs\" permet de sélectionner précisément les colonnes à inclure dans l'export (identifiant de l'exercice, statut, etc.)." },
      { label: "Données sensibles", text: "Le code écrit par l'élève et les réponses de l'assistant IA sont des champs à part, décochés par défaut : ils peuvent contenir des informations identifiantes (noms en commentaire) et sont à relire avant toute diffusion externe." },
    ],
  },
  {
    icon: "⚠️",
    color: "amber",
    title: "Alertes",
    items: [
      { label: "Bloqué·e 🧱", text: "L'élève a échoué au moins 3 fois sur un même exercice sans encore l'avoir réussi. Un signal pour proposer un coup de main." },
      { label: "Inactif·ve 💤", text: "L'élève n'a eu aucune activité depuis 7 jours ou plus." },
    ],
  },
  {
    icon: "🗺️",
    color: "blue",
    title: "Vue d'ensemble (heatmap)",
    intro: "Une ligne par élève, une colonne par exercice. Chaque case résume le statut de l'élève sur cet exercice ; cliquer sur un élève ouvre sa fiche détaillée.",
    items: [
      { label: "Réussi", text: "L'exercice a été validé en 4 tentatives ou moins." },
      { label: "Réussi (+ de 4 tentatives)", text: "L'exercice a été validé, mais après un nombre inhabituellement élevé d'essais : peut indiquer une difficulté persistante malgré la réussite finale." },
      { label: "En échec", text: "L'élève a tenté l'exercice mais ne l'a pas encore réussi." },
      { label: "Non commencé", text: "Aucune tentative enregistrée sur cet exercice." },
    ],
  },
  {
    icon: "📏",
    color: "indigo",
    title: "Étalonnage des exercices",
    intro: "Ces chiffres permettent de vérifier si le niveau affiché de l'exercice (Vert, Bleu, Rouge ou Noir) correspond bien à sa difficulté réelle du point de vue des élèves. Un taux de réussite très bas ou beaucoup de tentatives pour un exercice \"Vert\", par exemple, peut indiquer qu'il faudrait le reclasser à un niveau supérieur.",
    items: [
      { label: "Réussite", text: "Pourcentage d'élèves ayant tenté l'exercice qui l'ont réussi. Un taux très bas peut signaler un exercice trop difficile ou mal formulé." },
      { label: "Tentatives moy.", text: "Nombre moyen de tentatives (réussites + échecs) par élève ayant essayé l'exercice." },
      { label: "Aide IA moy.", text: "Nombre moyen de sollicitations de l'assistant IA par élève ayant essayé l'exercice." },
      { label: "Élèves ayant essayé", text: "Nombre d'élèves distincts ayant tenté l'exercice au moins une fois." },
    ],
  },
  {
    icon: "✨",
    color: "rose",
    title: "Erreurs fréquentes",
    intro: "Types d'erreurs les plus rencontrées par l'ensemble de la classe, tous exercices confondus. Utile pour repérer une notion à retravailler collectivement.",
    items: [],
  },
];

const titleColor = {
  indigo: "text-indigo-500",
  amber: "text-amber-500",
  blue: "text-blue-500",
  rose: "text-rose-500",
};
const dotColor = {
  indigo: "bg-indigo-500",
  amber: "bg-amber-500",
  blue: "bg-blue-500",
  rose: "bg-rose-500",
};
</script>

<template>
  <div class="fixed inset-0 z-[200] flex items-center justify-center overflow-hidden p-4">
    <div class="absolute inset-0 bg-black/70 backdrop-blur-sm" @click="emit('close')"></div>

    <div
      :class="['relative z-10 w-full max-w-2xl max-h-[85vh] rounded-[2.5rem] shadow-2xl border overflow-hidden animate-in fade-in zoom-in slide-in-from-bottom-8 duration-300', isDarkMode ? 'bg-zinc-900 border-zinc-800' : 'bg-white border-zinc-200']"
    >
      <div :class="['flex items-center justify-between px-8 py-6 border-b', isDarkMode ? 'border-zinc-800' : 'border-zinc-100']">
        <div>
          <h2 :class="['text-xl font-black tracking-tight', isDarkMode ? 'text-white' : 'text-zinc-900']">Comprendre les statistiques de classe</h2>
          <p :class="['text-xs font-medium mt-1', isDarkMode ? 'text-zinc-400' : 'text-zinc-500']">Le détail de chaque section de l'onglet Stat.</p>
        </div>
        <button
          @click="emit('close')"
          :class="['p-2.5 rounded-2xl transition-all hover:scale-110 shadow-sm flex-shrink-0', isDarkMode ? 'bg-zinc-800 text-zinc-400 hover:text-red-400' : 'bg-zinc-50 text-zinc-400 hover:text-red-500 border border-zinc-100']"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.5" d="M6 18L18 6M6 6l12 12" /></svg>
        </button>
      </div>

      <div class="px-8 py-6 overflow-y-auto max-h-[calc(85vh-100px)] custom-scrollbar space-y-8">
        <div v-for="section in sections" :key="section.title">
          <h3 :class="['text-lg font-bold tracking-tight flex items-center gap-2 mb-3', isDarkMode ? 'text-zinc-100' : 'text-zinc-800']">
            <span :class="titleColor[section.color]">{{ section.icon }}</span> {{ section.title }}
          </h3>
          <p v-if="section.intro" :class="['text-sm leading-relaxed italic mb-3', isDarkMode ? 'text-zinc-400' : 'text-zinc-500']">
            {{ section.intro }}
          </p>
          <div class="space-y-3">
            <div v-for="item in section.items" :key="item.label" class="flex gap-3">
              <span :class="['mt-1.5 h-1.5 w-1.5 rounded-full flex-shrink-0', dotColor[section.color]]"></span>
              <p :class="['text-sm leading-relaxed', isDarkMode ? 'text-zinc-300' : 'text-zinc-600']">
                <span :class="['font-bold', isDarkMode ? 'text-zinc-100' : 'text-zinc-800']">{{ item.label }} — </span>{{ item.text }}
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar {
  scrollbar-width: thin;
  scrollbar-color: #3f3f46 #f4f4f5;
}
.custom-scrollbar::-webkit-scrollbar {
  width: 8px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #d4d4d8;
  border-radius: 20px;
}
</style>
