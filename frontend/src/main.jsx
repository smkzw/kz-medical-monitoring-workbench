import React from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App.jsx";
import { G6SyntheticWorkbench } from "./features/medical-monitoring/g6/MedicalMonitoringG6SyntheticPage.jsx";
import { isG6SyntheticRoute } from "./features/medical-monitoring/g6/medicalMonitoringG6Route.mjs";
import { installApiContractFetch } from "./runtimeReadiness.js";
import "./styles.css";

installApiContractFetch(window);

const Root = isG6SyntheticRoute(typeof window === "undefined" ? null : window.location)
  ? G6SyntheticWorkbench
  : App;

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <Root />
  </React.StrictMode>,
);
