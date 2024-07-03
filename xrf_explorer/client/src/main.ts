// Import necessary modules
import { createApp } from "vue";
import "./assets/index.css";
import App from "./App.vue";
import { getConfig } from "./lib/config";

// Import global components
// Allows for the use of these components in any file without importing them
// For future development: sort these alphabetically and add new components as needed
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Slider } from "@/components/ui/slider";
import { Window } from "@/components/ui/window";

// Obtain configuration
export const config = await getConfig();

// Create the app
const app = createApp(App, { config: config });

// Register global components
// For future development: sort these alphabetically and add new components as needed
app.component("Button", Button);
app.component("Card", Card);
app.component("Checkbox", Checkbox);
app.component("Input", Input);
app.component("Label", Label);
app.component("Select", Select);
app.component("SelectContent", SelectContent);
app.component("SelectGroup", SelectGroup);
app.component("SelectItem", SelectItem);
app.component("SelectLabel", SelectLabel);
app.component("SelectTrigger", SelectTrigger);
app.component("SelectValue", SelectValue);
app.component("Separator", Separator);
app.component("Slider", Slider);
app.component("Window", Window);

// Mount the app
app.mount("#app");
