import React, { createContext, useCallback, useContext, useMemo, useState } from 'react';

const DEFAULT_LANGUAGE = 'en';

const translations = {
  en: {
    appTitle: 'AI Workfinder',
    navDashboard: 'Dashboard',
    navProfile: 'Profile',
    navApplications: 'Applications',
    logout: 'Logout',
    loading: 'Loading...',
    loginTitle: 'Login',
    loginButton: 'Login',
    loggingIn: 'Logging in...',
    registerTitle: 'Register',
    registerButton: 'Register',
    registering: 'Registering...',
    emailPlaceholder: 'Email',
    passwordPlaceholder: 'Password',
    repeatPasswordPlaceholder: 'Repeat password',
    noAccount: 'No account?',
    haveAccount: 'Already have an account?',
    registerLink: 'Register',
    loginLink: 'Login',
    errorInvalidCredentials: 'Invalid email or password',
    errorPasswordsMismatch: 'Passwords do not match',
    errorRegistrationFailed: 'Registration failed',
    dashboardTitle: 'Dashboard',
    jobPreferencesTitle: 'Job preferences',
    jobPreferencesEmpty: 'No job preferences set yet. Go to Profile and add them.',
    searchJobsTitle: 'Search jobs',
    specializationLabel: 'Specialization',
    specializationPlaceholder: 'python, javascript, devops, ai...',
    experienceLabel: 'Experience level',
    experienceAny: 'Any',
    experienceJunior: 'Junior',
    experienceMid: 'Mid',
    experienceSenior: 'Senior',
    experienceCLevel: 'C-level',
    locationLabel: 'Location',
    locationPlaceholder: 'warszawa, krakow, all-locations',
    resultsLimitLabel: 'Results limit',
    maxApplicationsLabel: 'Max applications',
    fullNameLabel: 'Full name',
    fullNamePlaceholder: 'Full name',
    resumeLabel: 'Resume',
    resumeNotUploaded: 'Not uploaded',
    statusLabel: 'Status',
    statusIdle: 'Not started',
    statusRunning: 'Running',
    statusFinished: 'Finished',
    statusFailed: 'Failed',
    statsJobsFound: 'Jobs found: {{jobs}} | One-click jobs: {{oneClick}}',
    statsApplied: 'Applied: {{applied}} / {{attempted}} (successful / attempted)',
    lastError: 'Last error: {{error}}',
    startSearch: 'Start search',
    searchInProgress: 'Search in progress...',
    agentStreamTitle: 'Agent stream',
    streamDisconnected: 'Stream disconnected',
    noStreamMessages: 'No stream messages yet.',
    errorSpecializationRequired: 'Specialization is required.',
    errorFullNameRequired: 'Full name is required.',
    errorResumeMissing: 'Please upload your resume in Profile first.',
    errorLimit: 'Limit must be between 1 and 100.',
    errorMaxApply: 'Max apply must be between 1 and 100.',
    errorStartSearch: 'Failed to start search',
    jobsTitle: 'Jobs',
    loadingJobs: 'Loading jobs...',
    errorLoadJobs: 'Failed to load jobs',
    noJobs: 'No jobs found yet. Start a search.',
    sourceLabel: 'Source',
    relevanceLabel: 'Relevance',
    statusApplied: 'Applied',
    statusNotApplied: 'Not applied',
    openJobPosting: 'Open job posting',
    profileTitle: 'Profile',
    loadingProfile: 'Loading profile...',
    errorLoadProfile: 'Failed to load profile',
    errorUpdateProfile: 'Failed to update profile',
    profileUpdated: 'Profile updated',
    errorGmailConnect: 'Failed to start Gmail connection',
    basicInfoTitle: 'Basic information',
    namePlaceholder: 'Name',
    phonePlaceholder: 'Phone',
    preferencesLabel: 'Job preferences (English, free text)',
    saveProfile: 'Save profile',
    saving: 'Saving...',
    resumeTitle: 'Resume',
    currentFileLabel: 'Current file',
    errorUploadResume: 'Failed to upload resume',
    resumeUploaded: 'Resume uploaded',
    applicationsTitle: 'Applications',
    loadingApplications: 'Loading applications...',
    errorLoadApplications: 'Failed to load applications',
    noApplications: 'No applications yet.',
    sentAtLabel: 'Sent at',
    toLabel: 'To',
    languageLabel: 'Language',
  },
  pl: {
    appTitle: 'AI Workfinder',
    navDashboard: 'Panel',
    navProfile: 'Profil',
    navApplications: 'Aplikacje',
    logout: 'Wyloguj',
    loading: 'Ładowanie...',
    loginTitle: 'Logowanie',
    loginButton: 'Zaloguj',
    loggingIn: 'Logowanie...',
    registerTitle: 'Rejestracja',
    registerButton: 'Zarejestruj',
    registering: 'Rejestracja...',
    emailPlaceholder: 'Email',
    passwordPlaceholder: 'Hasło',
    repeatPasswordPlaceholder: 'Powtórz hasło',
    noAccount: 'Nie masz konta?',
    haveAccount: 'Masz już konto?',
    registerLink: 'Zarejestruj się',
    loginLink: 'Zaloguj się',
    errorInvalidCredentials: 'Nieprawidłowy email lub hasło',
    errorPasswordsMismatch: 'Hasła nie są takie same',
    errorRegistrationFailed: 'Rejestracja nie powiodła się',
    dashboardTitle: 'Panel',
    jobPreferencesTitle: 'Preferencje pracy',
    jobPreferencesEmpty: 'Brak preferencji. Przejdź do Profilu i dodaj je.',
    searchJobsTitle: 'Szukaj ofert',
    specializationLabel: 'Specjalizacja',
    specializationPlaceholder: 'python, javascript, devops, ai...',
    experienceLabel: 'Poziom doświadczenia',
    experienceAny: 'Dowolny',
    experienceJunior: 'Junior',
    experienceMid: 'Mid',
    experienceSenior: 'Senior',
    experienceCLevel: 'C-level',
    locationLabel: 'Lokalizacja',
    locationPlaceholder: 'warszawa, krakow, all-locations',
    resultsLimitLabel: 'Limit wyników',
    maxApplicationsLabel: 'Maks. aplikacji',
    fullNameLabel: 'Imię i nazwisko',
    fullNamePlaceholder: 'Imię i nazwisko',
    resumeLabel: 'CV',
    resumeNotUploaded: 'Brak pliku',
    statusLabel: 'Status',
    statusIdle: 'Nie uruchomiono',
    statusRunning: 'W trakcie',
    statusFinished: 'Zakończono',
    statusFailed: 'Błąd',
    statsJobsFound: 'Znalezione: {{jobs}} | 1-click: {{oneClick}}',
    statsApplied: 'Aplikacje: {{applied}} / {{attempted}} (udane / próby)',
    lastError: 'Ostatni błąd: {{error}}',
    startSearch: 'Rozpocznij wyszukiwanie',
    searchInProgress: 'Wyszukiwanie w toku...',
    agentStreamTitle: 'Log agenta',
    streamDisconnected: 'Połączenie zerwane',
    noStreamMessages: 'Brak komunikatów.',
    errorSpecializationRequired: 'Specjalizacja jest wymagana.',
    errorFullNameRequired: 'Imię i nazwisko są wymagane.',
    errorResumeMissing: 'Najpierw dodaj CV w Profilu.',
    errorLimit: 'Limit musi być w zakresie 1-100.',
    errorMaxApply: 'Maks. aplikacji musi być w zakresie 1-100.',
    errorStartSearch: 'Nie udało się uruchomić wyszukiwania',
    jobsTitle: 'Oferty',
    loadingJobs: 'Ładowanie ofert...',
    errorLoadJobs: 'Nie udało się wczytać ofert',
    noJobs: 'Brak ofert. Uruchom wyszukiwanie.',
    sourceLabel: 'Źródło',
    relevanceLabel: 'Dopasowanie',
    statusApplied: 'Aplikacja wysłana',
    statusNotApplied: 'Nie wysłano',
    openJobPosting: 'Otwórz ofertę',
    profileTitle: 'Profil',
    loadingProfile: 'Ładowanie profilu...',
    errorLoadProfile: 'Nie udało się wczytać profilu',
    errorUpdateProfile: 'Nie udało się zapisać profilu',
    profileUpdated: 'Profil zapisany',
    errorGmailConnect: 'Nie udało się rozpocząć połączenia z Gmail',
    basicInfoTitle: 'Podstawowe informacje',
    namePlaceholder: 'Imię',
    phonePlaceholder: 'Telefon',
    preferencesLabel: 'Preferencje (po angielsku, tekst dowolny)',
    saveProfile: 'Zapisz profil',
    saving: 'Zapisywanie...',
    resumeTitle: 'CV',
    currentFileLabel: 'Aktualny plik',
    errorUploadResume: 'Nie udało się wysłać CV',
    resumeUploaded: 'CV wysłane',
    applicationsTitle: 'Aplikacje',
    loadingApplications: 'Ładowanie aplikacji...',
    errorLoadApplications: 'Nie udało się wczytać aplikacji',
    noApplications: 'Brak aplikacji.',
    sentAtLabel: 'Wysłano',
    toLabel: 'Do',
    languageLabel: 'Język',
  },
};

const LanguageContext = createContext({
  language: DEFAULT_LANGUAGE,
  setLanguage: () => {},
  t: (key, params) => key,
});

const interpolate = (template, params) => {
  if (!params) return template;
  return template.replace(/\{\{(\w+)\}\}/g, (match, key) => {
    if (params[key] === undefined || params[key] === null) {
      return '';
    }
    return String(params[key]);
  });
};

export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(() => {
    const stored = localStorage.getItem('language');
    return stored === 'en' || stored === 'pl' ? stored : DEFAULT_LANGUAGE;
  });

  const setLanguage = useCallback((nextLanguage) => {
    setLanguageState(nextLanguage);
    localStorage.setItem('language', nextLanguage);
  }, []);

  const t = useCallback(
    (key, params) => {
      const dictionary = translations[language] || translations[DEFAULT_LANGUAGE];
      const fallback = translations[DEFAULT_LANGUAGE];
      const value = dictionary[key] || fallback[key] || key;
      return interpolate(value, params);
    },
    [language]
  );

  const value = useMemo(
    () => ({
      language,
      setLanguage,
      t,
    }),
    [language, setLanguage, t]
  );

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useI18n() {
  return useContext(LanguageContext);
}
