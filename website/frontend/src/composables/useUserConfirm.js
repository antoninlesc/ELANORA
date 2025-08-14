import { h, render } from 'vue';
import UserConfirm from '@/components/common/UserConfirm.vue';

export function useUserConfirm() {
  return (options) => {
    return new Promise((resolve) => {
      const container = document.createElement('div');
      document.body.appendChild(container);

      const vnode = h(UserConfirm, {
        ...options,
        modelValue: true,
        onConfirm: () => {
          cleanup();
          resolve(true);
        },
        onCancel: () => {
          cleanup();
          resolve(false);
        },
        'onUpdate:modelValue': (v) => {
          if (!v) cleanup();
        },
      });

      function cleanup() {
        render(null, container);
        document.body.removeChild(container);
      }

      render(vnode, container);
    });
  };
}
