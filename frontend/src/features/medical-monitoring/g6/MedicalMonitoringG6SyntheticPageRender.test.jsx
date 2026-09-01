import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import MedicalMonitoringG6SyntheticPage from "./MedicalMonitoringG6SyntheticPage.jsx";
import { loadCanonicalG6BundleForTest } from "./medicalMonitoringG6CanonicalTestFixture.mjs";

const bundle = loadCanonicalG6BundleForTest();

export const renders = {
  overview: renderToStaticMarkup(<MedicalMonitoringG6SyntheticPage bundle={bundle} />),
  journey: renderToStaticMarkup(<MedicalMonitoringG6SyntheticPage bundle={bundle} initialView="journey" />),
  loading: renderToStaticMarkup(<MedicalMonitoringG6SyntheticPage />),
};
