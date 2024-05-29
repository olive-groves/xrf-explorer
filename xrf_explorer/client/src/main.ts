import { createApp } from "vue";
import "./assets/index.css";
import App from "./App.vue";
import { getConfig } from "./lib/config";

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
const config = await getConfig();

const app = createApp(App, { config: config });

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

app.mount("#app");
