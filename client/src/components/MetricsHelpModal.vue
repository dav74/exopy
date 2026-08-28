<script setup>
defineProps(["isDarkMode"]);
const emit = defineEmits(["close"]);

const sections = [
  {
    icon: "📊",
    color: "blue",
    title: "Progression",
    items: [
      { label: "XP", text: "Points d'expérience gagnés en réussissant des exercices. Chaque niveau rapporte plus (Vert : 10, Bleu : 20, Rouge : 40, Noir : 80), avec un bonus de +50 % si l'exercice est résolu sans aide de l'IA." },
      { label: "Complétion globale", text: "Nombre d'exercices réussis sur le total d'exercices disponibles." },
      { label: "Niveaux", text: "Répartition des exercices réussis par niveau de difficulté (Vert, Bleu, Rouge, Noir)." },
    ],
  },
  {
    icon: "⚡",
    color: "emerald",
    title: "Autonomie",
    items: [
      { label: "Réussite sans IA", text: "Pourcentage des exercices réussis sans avoir sollicité l'assistant IA sur cet exercice. Plus ce taux est élevé, plus l'élève progresse en autonomie." },
      { label: "Requêtes IA / exo", text: "Nombre moyen de sollicitations de l'IA par exercice tenté. Un chiffre bas traduit une plus grande autonomie." },
      { label: "Badges \"Déclic\"", text: "Nombre d'exercices où l'élève a demandé de l'aide à l'IA puis a réussi l'exercice : signe qu'un déclic utile a eu lieu grâce à cette aide." },
    ],
  },
  {
    icon: "✨",
    color: "rose",
    title: "Qualité",
    items: [
      { label: "Premier Essai (First Try)", text: "Pourcentage d'exercices réussis dès la toute première tentative, sans échec intermédiaire." },
      { label: "Persévérance", text: "Nombre moyen de tentatives nécessaires pour réussir un exercice (tentatives totales ÷ exercices réussis). Une valeur plus élevée montre que l'élève persiste face aux difficultés plutôt que d'abandonner." },
      { label: "Erreurs fréquentes", text: "Types d'erreurs les plus récurrentes rencontrées pendant les exercices." },
    ],
  },
  {
    icon: "🔥",
    color: "orange",
    title: "Engagement",
    items: [
      { label: "Série en cours", text: "Nombre de jours consécutifs avec au moins une activité." },
      { label: "Temps hebdo", text: "Temps de pratique estimé sur les 7 derniers jours." },
    ],
  },
];

const dotColor = {
  blue: "bg-blue-500",
  emerald: "bg-emerald-500",
  rose: "bg-rose-500",
  orange: "bg-orange-500",
};
const titleColor = {
  blue: "text-blue-500",
  emerald: "text-emerald-500",
  rose: "text-rose-500",
  orange: "text-orange-500",
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
          <h2 :class="['text-xl font-black tracking-tight', isDarkMode ? 'text-white' : 'text-zinc-900']">Comprendre mes statistiques</h2>
          <p :class="['text-xs font-medium mt-1', isDarkMode ? 'text-zinc-400' : 'text-zinc-500']">Le détail de chaque indicateur affiché dans le tableau de bord.</p>
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
