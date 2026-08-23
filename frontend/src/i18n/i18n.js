import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import sq from "./locales/sq.json";
import en from "./locales/en.json";
import de from "./locales/de.json";

const savedLanguage = localStorage.getItem("tavora_language");

const supportedLanguages = ["sq", "en", "de"];

const initialLanguage = supportedLanguages.includes(savedLanguage)
  ? savedLanguage
  : "en";

i18n
  .use(initReactI18next)
  .init({
    resources: {
      sq: {
        translation: sq,
      },
      en: {
        translation: en,
      },
      de: {
        translation: de,
      },
    },

    lng: initialLanguage,

    fallbackLng: "en",

    supportedLngs: supportedLanguages,

    load: "languageOnly",

    interpolation: {
      escapeValue: false,
    },
  });

export default i18n;