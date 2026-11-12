import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { I18nProvider } from "../shared/i18n/I18nProvider";
import { App } from "./App";
import "./styles.css";

const root = document.getElementById("root");
if (root === null) throw new Error("index.html has no #root element");

createRoot(root).render(
  <StrictMode>
    <I18nProvider>
      <App />
    </I18nProvider>
  </StrictMode>,
);
