// Translation system for Zeitgesteuerte Nachrichten
// Supports German (de) and English (en) with extensibility for more languages

const translations = {
  de: {
    // Navigation & Tabs
    "nav.create": "Erstellen",
    "nav.scheduled": "Geplant", 
    "nav.delivered": "Ausgeliefert",
    "nav.subscription": "Abo",
    "nav.admin": "Admin",
    "nav.referral": "Einladungen",
    
    // Authentication
    "auth.login": "Anmelden",
    "auth.register": "Registrieren", 
    "auth.logout": "Abmelden",
    "auth.email": "E-Mail",
    "auth.password": "Passwort",
    "auth.name": "Name",
    "auth.confirmPassword": "Passwort bestätigen",
    "auth.loginButton": "Jetzt anmelden",
    "auth.registerButton": "Konto erstellen",
    "auth.switchToRegister": "Noch kein Konto? Registrieren",
    "auth.switchToLogin": "Bereits ein Konto? Anmelden",
    "auth.referralCode": "Referral-Code (optional)",
    "auth.referralBonus": "🎁 5 Bonus-Nachrichten bei Registrierung mit Referral-Code!",
    
    // App Title & Description
    "app.title": "Zeitgesteuerte Nachrichten",
    "app.subtitle": "Planen Sie Ihre Nachrichten für die perfekte Zeit",
    "app.description": "Erstellen, planen und verwalten Sie Ihre Nachrichten mit KI-Unterstützung und erweiterten Funktionen.",
    
    // Message Creation
    "create.title": "Nachricht erstellen",
    "create.messageTitle": "Titel",
    "create.messageContent": "Nachricht",
    "create.scheduledTime": "Lieferzeitpunkt",
    "create.titlePlaceholder": "Gib deiner Nachricht einen Titel...",
    "create.contentPlaceholder": "Schreibe deine Nachricht hier... oder nutze den AI-Assistenten oben!",
    "create.submitButton": "📅 Nachricht planen",
    "create.submitting": "⏳ Wird erstellt...",
    "create.recurring": "Wiederkehrende Nachricht",
    "create.recurringInterval": "Wiederholungsintervall",
    "create.recurringDaily": "Täglich",
    "create.recurringWeekly": "Wöchentlich", 
    "create.recurringMonthly": "Monatlich",
    "create.recurringNotice": "Wiederkehrende Nachrichten sind nur für Premium- und Business-Abonnenten verfügbar.",
    
    // AI Assistant
    "ai.assistant": "AI-Assistent",
    "ai.suggestions": "Vorschläge für Sie:",
    "ai.customPrompt": "Eigenen Prompt eingeben...",
    "ai.generate": "Generieren",
    "ai.improve": "Verbessern",
    "ai.correct": "Korrigieren",
    "ai.generating": "KI generiert...",
    "ai.enhancing": "KI verbessert...",
    
    // Messages Lists
    "scheduled.title": "Geplante Nachrichten",
    "scheduled.empty": "Keine geplanten Nachrichten vorhanden.",
    "scheduled.createFirst": "Erste Nachricht erstellen",
    "scheduled.dueSoon": "Diese Nachricht wird bald ausgeliefert!",
    "delivered.title": "Ausgelieferte Nachrichten", 
    "delivered.empty": "Noch keine Nachrichten ausgeliefert.",
    "delivered.scheduledAt": "Geplant:",
    "delivered.deliveredAt": "Ausgeliefert:",
    
    // Subscription Plans
    "plans.current": "Ihr aktuelles Abo",
    "plans.free": "Kostenlos",
    "plans.premium": "Premium", 
    "plans.business": "Business",
    "plans.month": "/Monat",
    "plans.unlimited": "Unbegrenzt",
    "plans.upgrade": "Auf {plan} upgraden",
    "plans.features": "Ihre Features:",
    "plans.messagesUsed": "Nachrichten diesen Monat:",
    "plans.welcomePremium": "Willkommen im Premium-Club!",
    
    // Subscription Features
    "features.basicMessages": "5 Nachrichten pro Monat",
    "features.basicFunctions": "Basis-Funktionen",
    "features.unlimitedMessages": "Unbegrenzte Nachrichten",
    "features.recurringMessages": "Wiederkehrende Nachrichten", 
    "features.advancedTime": "Erweiterte Zeitoptionen",
    "features.exportImport": "Export/Import",
    "features.analytics": "Analytics Dashboard",
    "features.apiAccess": "API-Zugang",
    "features.prioritySupport": "Priority Support",
    "features.premiumAll": "Alles aus Premium",
    
    // Admin Dashboard
    "admin.title": "Admin Dashboard",
    "admin.stats": "Statistiken",
    "admin.totalUsers": "Benutzer Gesamt",
    "admin.monthlyRevenue": "Monatserlös", 
    "admin.availableBalance": "Verfügbares Guthaben",
    "admin.premiumUsers": "Premium Kunden",
    "admin.loadingStats": "Lade Statistiken...",
    
    // Advanced Analytics
    "analytics.title": "Erweiterte Analytik",
    "analytics.export": "JSON Export", 
    "analytics.refresh": "Aktualisieren",
    "analytics.loading": "Lade erweiterte Analytik...",
    "analytics.overview": "Übersicht",
    "analytics.users": "Benutzer",
    "analytics.messages": "Nachrichten", 
    "analytics.revenue": "Umsatz",
    "analytics.ai": "KI-Nutzung",
    "analytics.conversionRate": "Konversionsrate",
    "analytics.userRetention": "Nutzerretention",
    "analytics.avgRevenue": "Durchschn. Umsatz/User",
    "analytics.aiAdoption": "KI-Adoption",
    
    // Payout System
    "payout.title": "Bank-Auszahlung",
    "payout.totalRevenue": "Gesamteinnahmen",
    "payout.availableBalance": "Verfügbar für Auszahlung", 
    "payout.pendingPayouts": "Ausstehende Auszahlungen",
    "payout.amount": "Auszahlungsbetrag in €",
    "payout.request": "Auszahlung anfordern",
    "payout.processing": "Wird bearbeitet...",
    "payout.minimum": "Mindestbetrag: €10.00 • Bearbeitungszeit: 1-3 Werktage",
    
    // Referral System
    "referral.title": "Freunde einladen & Belohnungen erhalten",
    "referral.invitedFriends": "Eingeladene Freunde",
    "referral.bonusMessages": "Bonus-Nachrichten", 
    "referral.yourCode": "Ihr Referral-Code",
    "referral.copyLink": "Link kopieren",
    "referral.linkCopied": "Link kopiert!",
    "referral.howItWorks": "So funktioniert es",
    "referral.step1": "Teilen Sie Ihren persönlichen Referral-Link",
    "referral.step2": "Freunde registrieren sich über Ihren Link", 
    "referral.step3": "Sie erhalten 5 Bonus-Nachrichten pro Einladung",
    
    // Common Actions
    "action.delete": "Löschen",
    "action.edit": "Bearbeiten", 
    "action.save": "Speichern",
    "action.cancel": "Abbrechen",
    "action.copy": "Kopieren",
    "action.loading": "Lädt...",
    "action.refresh": "Aktualisieren",
    "action.export": "Exportieren",
    
    // Time & Dates
    "time.daily": "Täglich",
    "time.weekly": "Wöchentlich",
    "time.monthly": "Monatlich", 
    "time.scheduled": "Geplant",
    "time.delivered": "Ausgeliefert",
    "time.created": "Erstellt",
    
    // Messages & Notifications
    "message.limitReached": "Nachrichtenlimit erreicht",
    "message.upgradeRequired": "Sie haben Ihr monatliches Limit von {limit} Nachrichten erreicht. Upgraden Sie auf Premium für unbegrenzte Nachrichten.",
    "message.deleteSuccess": "Nachricht erfolgreich gelöscht",
    "message.createSuccess": "Nachricht erfolgreich erstellt",
    "message.error": "Ein Fehler ist aufgetreten",
    
    // Language Switcher
    "lang.german": "Deutsch",
    "lang.english": "English",
    "lang.switch": "Sprache wechseln"
  },
  
  en: {
    // Navigation & Tabs
    "nav.create": "Create",
    "nav.scheduled": "Scheduled",
    "nav.delivered": "Delivered", 
    "nav.subscription": "Subscription",
    "nav.admin": "Admin",
    "nav.referral": "Referrals",
    
    // Authentication
    "auth.login": "Login",
    "auth.register": "Register",
    "auth.logout": "Logout", 
    "auth.email": "Email",
    "auth.password": "Password",
    "auth.name": "Name",
    "auth.confirmPassword": "Confirm Password",
    "auth.loginButton": "Sign In",
    "auth.registerButton": "Create Account",
    "auth.switchToRegister": "Don't have an account? Register",
    "auth.switchToLogin": "Already have an account? Sign In",
    "auth.referralCode": "Referral Code (optional)",
    "auth.referralBonus": "🎁 Get 5 bonus messages when registering with a referral code!",
    
    // App Title & Description
    "app.title": "Scheduled Messages",
    "app.subtitle": "Schedule your messages for the perfect time", 
    "app.description": "Create, schedule and manage your messages with AI support and advanced features.",
    
    // Message Creation
    "create.title": "Create Message",
    "create.messageTitle": "Title",
    "create.messageContent": "Message",
    "create.scheduledTime": "Delivery Time", 
    "create.titlePlaceholder": "Give your message a title...",
    "create.contentPlaceholder": "Write your message here... or use the AI assistant above!",
    "create.submitButton": "📅 Schedule Message",
    "create.submitting": "⏳ Creating...",
    "create.recurring": "Recurring Message",
    "create.recurringInterval": "Repeat Interval",
    "create.recurringDaily": "Daily",
    "create.recurringWeekly": "Weekly",
    "create.recurringMonthly": "Monthly",
    "create.recurringNotice": "Recurring messages are only available for Premium and Business subscribers.",
    
    // AI Assistant
    "ai.assistant": "AI Assistant",
    "ai.suggestions": "Suggestions for you:",
    "ai.customPrompt": "Enter custom prompt...", 
    "ai.generate": "Generate",
    "ai.improve": "Improve", 
    "ai.correct": "Correct",
    "ai.generating": "AI generating...",
    "ai.enhancing": "AI enhancing...",
    
    // Messages Lists
    "scheduled.title": "Scheduled Messages",
    "scheduled.empty": "No scheduled messages available.",
    "scheduled.createFirst": "Create first message", 
    "scheduled.dueSoon": "This message will be delivered soon!",
    "delivered.title": "Delivered Messages",
    "delivered.empty": "No messages delivered yet.",
    "delivered.scheduledAt": "Scheduled:",
    "delivered.deliveredAt": "Delivered:",
    
    // Subscription Plans
    "plans.current": "Your current subscription",
    "plans.free": "Free",
    "plans.premium": "Premium",
    "plans.business": "Business",
    "plans.month": "/month",
    "plans.unlimited": "Unlimited", 
    "plans.upgrade": "Upgrade to {plan}",
    "plans.features": "Your features:",
    "plans.messagesUsed": "Messages this month:",
    "plans.welcomePremium": "Welcome to Premium Club!",
    
    // Subscription Features
    "features.basicMessages": "5 messages per month",
    "features.basicFunctions": "Basic functions",
    "features.unlimitedMessages": "Unlimited messages",
    "features.recurringMessages": "Recurring messages",
    "features.advancedTime": "Advanced time options", 
    "features.exportImport": "Export/Import",
    "features.analytics": "Analytics Dashboard",
    "features.apiAccess": "API Access",
    "features.prioritySupport": "Priority Support",
    "features.premiumAll": "Everything from Premium",
    
    // Admin Dashboard
    "admin.title": "Admin Dashboard",
    "admin.stats": "Statistics", 
    "admin.totalUsers": "Total Users",
    "admin.monthlyRevenue": "Monthly Revenue",
    "admin.availableBalance": "Available Balance", 
    "admin.premiumUsers": "Premium Customers",
    "admin.loadingStats": "Loading statistics...",
    
    // Advanced Analytics
    "analytics.title": "Advanced Analytics",
    "analytics.export": "JSON Export",
    "analytics.refresh": "Refresh", 
    "analytics.loading": "Loading advanced analytics...",
    "analytics.overview": "Overview",
    "analytics.users": "Users",
    "analytics.messages": "Messages",
    "analytics.revenue": "Revenue",
    "analytics.ai": "AI Usage",
    "analytics.conversionRate": "Conversion Rate",
    "analytics.userRetention": "User Retention", 
    "analytics.avgRevenue": "Avg. Revenue/User",
    "analytics.aiAdoption": "AI Adoption",
    
    // Payout System
    "payout.title": "Bank Payout",
    "payout.totalRevenue": "Total Revenue",
    "payout.availableBalance": "Available for Payout",
    "payout.pendingPayouts": "Pending Payouts",
    "payout.amount": "Payout amount in €", 
    "payout.request": "Request Payout",
    "payout.processing": "Processing...",
    "payout.minimum": "Minimum amount: €10.00 • Processing time: 1-3 business days",
    
    // Referral System
    "referral.title": "Invite Friends & Get Rewards",
    "referral.invitedFriends": "Invited Friends",
    "referral.bonusMessages": "Bonus Messages",
    "referral.yourCode": "Your Referral Code",
    "referral.copyLink": "Copy Link", 
    "referral.linkCopied": "Link copied!",
    "referral.howItWorks": "How it works",
    "referral.step1": "Share your personal referral link",
    "referral.step2": "Friends register using your link",
    "referral.step3": "You get 5 bonus messages per referral",
    
    // Common Actions
    "action.delete": "Delete",
    "action.edit": "Edit",
    "action.save": "Save", 
    "action.cancel": "Cancel",
    "action.copy": "Copy",
    "action.loading": "Loading...",
    "action.refresh": "Refresh",
    "action.export": "Export",
    
    // Time & Dates
    "time.daily": "Daily",
    "time.weekly": "Weekly",
    "time.monthly": "Monthly",
    "time.scheduled": "Scheduled", 
    "time.delivered": "Delivered",
    "time.created": "Created",
    
    // Messages & Notifications
    "message.limitReached": "Message limit reached",
    "message.upgradeRequired": "You have reached your monthly limit of {limit} messages. Upgrade to Premium for unlimited messages.",
    "message.deleteSuccess": "Message deleted successfully", 
    "message.createSuccess": "Message created successfully",
    "message.error": "An error occurred",
    
    // Language Switcher
    "lang.german": "Deutsch",
    "lang.english": "English",
    "lang.switch": "Switch Language"
  }
};

// Translation hook
export const useTranslation = (language = 'de') => {
  const t = (key, params = {}) => {
    let translation = translations[language]?.[key] || translations['de']?.[key] || key;
    
    // Replace parameters in translation
    Object.keys(params).forEach(param => {
      translation = translation.replace(`{${param}}`, params[param]);
    });
    
    return translation;
  };
  
  return { t };
};

// Language context
import { createContext, useContext } from 'react';

export const LanguageContext = createContext({
  language: 'de',
  setLanguage: () => {},
  t: () => {}
});

export const useLanguage = () => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};

export default translations;