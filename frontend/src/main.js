import { createStandaloneApplication } from './standalone/application.js';
import { describeError } from './standalone/errors.js';
import sentinelAdapter from './sentinel_adapter.js';
import { initAiBot } from './ui/aiBot.js';

const application = createStandaloneApplication({
  googleApiKey: import.meta.env.GOOGLE_MAPS_API_KEY,
  cesiumToken: import.meta.env.CESIUM_ION_TOKEN,
  allowQaRegistration: import.meta.env.DEV,
});

application.start().then((components) => {
  if (components && components.scene && components.scene.viewer) {
    sentinelAdapter.setViewer(components.scene.viewer);
    window._cesiumViewer = components.scene.viewer;
  }
  window._gevComponents = components;
  if (components?.scene?.viewer && components?.controls?.styleManager) {
    initAiBot({
      viewer: components.scene.viewer,
      styleManager: components.controls.styleManager,
      dataManager: components.data?.dataManager,
      placeSearch: components.controls.styleManager?.placeSearch,
      scene: components.scene,
    });
  }
}).catch((error) => {
  console.error("God's Eye View initialization failed:", error);
  const loaderStatus = document.querySelector('#loading-screen .loader-status');
  if (loaderStatus) {
    loaderStatus.textContent = `Error: ${describeError(error)}`;
    loaderStatus.style.color = '#ff4444';
  }
});

export { application, sentinelAdapter };

