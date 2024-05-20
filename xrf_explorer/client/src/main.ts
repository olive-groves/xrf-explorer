import { createApp } from "vue";
import "./assets/index.css";
import App from "./App.vue";
import { getConfig } from "./lib/config";

// Obtain configuration
const config = await getConfig();

createApp(App, { config: config }).mount("#app");
