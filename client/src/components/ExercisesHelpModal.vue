<script setup>
defineProps(["isDarkMode"]);
const emit = defineEmits(["close"]);

const sections = [
  {
    icon: "➕",
    color: "blue",
    title: "Ajouter un exercice",
    items: [
      { label: "Formulaire manuel", text: "Le bouton \"+\" en haut de la liste ouvre un formulaire vierge : titre, niveau (Vert, Bleu, Rouge, Noir), énoncé et code de validation Python caché." },
      { label: "Génération via IA", text: "Depuis le formulaire, le bouton \"Générer via IA\" propose automatiquement un énoncé et un test de validation à partir d'un sujet, à relire et ajuster avant publication." },
      { label: "Niveau", text: "Le niveau choisi ici est celui affiché aux élèves. La section \"Étalonnage des exercices\" de l'onglet Stat permet ensuite de vérifier qu'il correspond bien à la difficulté réellement observée." },
    ],
  },
  {
    icon: "📥",
    color: "indigo",
    title: "Importer (.json)",
    intro: "Permet d'ajouter plusieurs exercices d'un coup à partir d'un fichier, sans toucher aux exercices déjà présents.",
    items: [
      { label: "Format", text: "Un fichier JSON contenant un objet exercice ou un tableau d'objets, chacun avec les champs titre, niveau, enonce et test." },
      { label: "Format texte (secours)", text: "Un fichier texte structuré (un exercice par bloc, titre en en-tête suivi de l'énoncé et d'un bloc de test) est aussi accepté si le JSON n'est pas reconnu." },
      { label: "Ajout, pas remplacement", text: "Contrairement à l'import des élèves, les exercices importés s'ajoutent à la liste existante : rien n'est supprimé." },
    ],
  },
  {
    icon: "📤",
    color: "indigo",
    title: "Exporter (.json)",
    items: [
      { label: "Contenu", text: "Télécharge tous les exercices actuels au format JSON : pratique pour une sauvegarde, un partage entre enseignants, ou une réimportation après modification." },
    ],
  },
];

const titleColor = {
  blue: "text-blue-500",
  indigo: "text-indigo-500",
};
const dotColor = {
  blue: "bg-blue-500",
  indigo: "bg-indigo-500",
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
          <h2 :class="['text-xl font-black tracking-tight', isDarkMode ? 'text-white' : 'text-zinc-900']">Gérer les exercices</h2>
          <p :class="['text-xs font-medium mt-1', isDarkMode ? 'text-zinc-400' : 'text-zinc-500']">Ajout, import et export des exercices.</p>
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
