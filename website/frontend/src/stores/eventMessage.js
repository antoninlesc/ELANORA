import { defineStore } from 'pinia';
import { ref } from 'vue';

export const useEventMessageStore = defineStore('eventMessage', () => {
  const messages = ref([]);
  const counter = ref(0);

  const addMessage = (
    translationKey,
    type = 'info',
    duration = 5000,
    params = undefined
  ) => {
    const id = counter.value++;

    messages.value.push({
      id,
      translationKey,
      type,
      duration,
      show: false,
      params, // Pass params for interpolation
    });

    // Use requestAnimationFrame to ensure browser has completed rendering
    // before triggering the animation
    const showMessage = () => {
      const messageIndex = messages.value.findIndex((msg) => msg.id === id);
      if (messageIndex !== -1) {
        messages.value[messageIndex].show = true;
      }
    };

    // Wait for document ready state before showing the message
    if (document.readyState === 'complete') {
      // If document is already loaded, use next animation frame
      requestAnimationFrame(() => {
        // Additional delay for smoother animation
        setTimeout(showMessage, 50);
      });
    } else {
      // If document is still loading, wait for load event
      window.addEventListener(
        'load',
        () => {
          requestAnimationFrame(() => {
            setTimeout(showMessage, 50);
          });
        },
        { once: true }
      );
    }

    return id;
  };

  const removeMessage = (id) => {
    const index = messages.value.findIndex((msg) => msg.id === id);
    if (index !== -1) {
      // First set show to false to trigger fade-out animation
      messages.value[index].show = false;

      // Then after animation completes, remove the message
      setTimeout(() => {
        const currentIndex = messages.value.findIndex((msg) => msg.id === id);
        if (currentIndex !== -1) {
          messages.value.splice(currentIndex, 1);
        }
      }, 300); // Animation duration
    }
  };

  return {
    messages,
    addMessage,
    removeMessage,
  };
});