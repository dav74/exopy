<script setup>
import { ref, computed } from "vue";
import { useThemeStore } from "../stores/themeStore";
import { storeToRefs } from "pinia";

const props = defineProps({
  points: { type: Array, required: true }, // [{ label, value, hasActivity }]
  color: { type: String, default: "blue" }, // 'blue' | 'emerald' | 'amber'
  unit: { type: String, default: "" },
});

const themeStore = useThemeStore();
const { isDarkMode } = storeToRefs(themeStore);

const hoveredIndex = ref(null);

const colorClasses = {
  blue: "bg-blue-500",
  emerald: "bg-emerald-500",
  amber: "bg-amber-500",
};
const barColor = computed(() => colorClasses[props.color] || colorClasses.blue);

const computedMax = computed(() => Math.max(...props.points.map((p) => p.value), 1));

const heightPct = (p) => {
  if (!p.hasActivity) return 4;
  return Math.max((p.value / computedMax.value) * 100, 6);
};
</script>

<template>
  <div class="relative">
    <div class="flex items-end gap-1.5 h-16">
      <div
        v-for="(p, i) in points"
        :key="i"
        class="flex-1 flex flex-col items-center justify-end h-full relative"
        @mouseenter="hoveredIndex = i"
        @mouseleave="hoveredIndex = null"
      >
        <div
          v-if="hoveredIndex === i"
          :class="['absolute -top-7 left-1/2 -translate-x-1/2 px-2 py-1 rounded-lg text-[10px] font-black whitespace-nowrap shadow-lg z-10', isDarkMode ? 'bg-zinc-700 text-white' : 'bg-zinc-800 text-white']"
        >
          {{ p.hasActivity ? `${p.value}${unit}` : "—" }}
        </div>
        <div
          class="w-full rounded-t-md transition-all duration-300 cursor-default"
          :class="[!p.hasActivity ? (isDarkMode ? 'bg-zinc-800' : 'bg-zinc-200') : barColor, hoveredIndex === i ? 'opacity-100' : 'opacity-80']"
          :style="{ height: heightPct(p) + '%' }"
        ></div>
      </div>
    </div>
    <div class="flex gap-1.5 mt-1.5">
      <span
        v-for="(p, i) in points"
        :key="'l' + i"
        :class="['flex-1 text-center text-[8px] font-black uppercase tracking-wider', isDarkMode ? 'text-zinc-600' : 'text-zinc-400']"
      >{{ p.label }}</span>
    </div>
  </div>
</template>
