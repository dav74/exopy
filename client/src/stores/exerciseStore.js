import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useExerciseStore = defineStore('exercise', () => {
  const selectedItemId = ref(null)
  const exercise = ref(null)
  const code = ref("")
  const resTest = ref("0")
  const testCode = ref([])
  const visibleTests = ref([])
  const menuItems = ref([])
  const isLoadingMenu = ref(false)
  const errorCode = ref("")
  
  const fetchMenuItems = async (API_URL) => {
    try {
      isLoadingMenu.value = true;
      const token = localStorage.getItem("access_token");
      if (!token) return;
      
      const response = await fetch(API_URL + "/title", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
      if (response.ok) {
        const data = await response.json();
        menuItems.value = data.title;
      }
    } catch (err) {
      console.error("Failed to fetch menu items", err);
    } finally {
      isLoadingMenu.value = false;
    }
  };
  
  function resetExerciseState() {
    selectedItemId.value = null;
    exercise.value = null;
    code.value = "";
    resTest.value = "0";
    testCode.value = [];
    visibleTests.value = [];
    errorCode.value = "";
  }

  function setExercise(data, id) {
    exercise.value = data
    selectedItemId.value = id
    // Restore locally saved code if it exists for this exercise
    const savedCode = localStorage.getItem(`draft_code_${id}`)
    code.value = savedCode ? savedCode : ""
    
    resTest.value = "0"
    testCode.value = []
    visibleTests.value = []
    errorCode.value = ""
  }

  function saveCodeLocally(newCode) {
    code.value = newCode;
    if (selectedItemId.value) {
        localStorage.setItem(`draft_code_${selectedItemId.value}`, newCode)
    }
  }

  return { 
    selectedItemId, 
    exercise, 
    code, 
    resTest, 
    testCode, 
    visibleTests, 
    errorCode, 
    resetExerciseState, 
    setExercise,
    saveCodeLocally,
    menuItems,
    isLoadingMenu,
    fetchMenuItems
  }
})
