import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import "./theme"; // Initialize theme early to prevent flash

createApp(App).use(router).mount("#app");
