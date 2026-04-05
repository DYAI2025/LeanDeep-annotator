// i18n.js — Lightweight Deutsch ↔ Englisch Toggle
// Speichert Sprachpräferenz in LocalStorage

const translations = {
  de: {
    page_title: "LeanDeep LD5 - Communication Intelligence",
    nav_vision: "Vision",
    nav_engine: "Engine",
    nav_usecases: "Anwendungen",
    nav_benefits: "Vorteile",
    nav_cta: "Live-Demo anfragen",
    
    hero_tagline: "Jenseits der Worte",
    hero_title_pt1: "Die Tiefenstruktur der",
    hero_title_pt2: "Kommunikation",
    hero_title_pt3: "entschlüsseln",
    hero_description: "In einer Welt, die in Daten ertrinkt, bleibt die wichtigste Information oft unsichtbar: Die psychologische und semiotische Dynamik zwischen Menschen. LeanDeep LD5 ist Ihre High-End-Intelligence-Engine für das 'Wie' hinter dem 'Was'.",
    hero_detail: "Durch die Kombination von linguistischer Präzision, prosodischer Analyse (Stimmführung) und tiefenpsychologischen Algorithmen wandelt LD5 flüchtige Gespräche in messbare, objektive Daten um. Es ist nicht einfach nur ein Transkriptions-Tool – es ist ein Analyse-Instrument für menschliche Interaktion.",
    
    arch_title: "Das Vier-Ebenen-Modell",
    arch_description: "Diese Sektion visualisiert die fraktale Architektur von LD5. Sie zeigt, wie aus feinsten mikroskopischen Signalen schrittweise komplexe, psychologische Metamuster berechnet werden.",
    
    layer_ato_title: "ATO",
    layer_ato_subtitle: "Atomic Markers",
    layer_ato_desc: "Die kleinsten Bausteine. LD5 misst Pausen, Filler-Wörter ('ähm'), Wortwahl-Präferenzen und feine Tonhöhen-Schwankungen in Millisekunden.",
    
    layer_sem_title: "SEM",
    layer_sem_subtitle: "Semantic Markers",
    layer_sem_desc: "Bedeutungseinheiten und Intentionen. Erkennt das System Ironie? Ein aufrichtiges Lob? Eine versteckte Anschuldigung oder den Wunsch nach Nähe?",
    
    layer_clu_title: "CLU",
    layer_clu_subtitle: "Cluster Markers",
    layer_clu_desc: "Kombinationen, die emotionale Zustände definieren. Ein 'Widerstands-Cluster' entsteht z.B., wenn defensive Sprache auf abfallende Intonation trifft.",
    
    layer_mema_title: "MEMA",
    layer_mema_subtitle: "Meta-Patterns",
    layer_mema_desc: "Die Langzeit-DNA der Kommunikation. Hier werden komplexe Beziehungsdynamiken (nach Gottman) oder Entwicklungsstufen (Spiral Dynamics) objektiv sichtbar.",
    
    usecases_title: "Interaktive Anwendungsfälle",
    usecases_description: "Erleben Sie in dieser Sektion, wie LD5 in verschiedenen Domänen verborgene Dynamiken aufdeckt. Wählen Sie einen Anwendungsfall, um das Szenario, den LD5-Insight und die daraus resultierenden, datenbasierten Visualisierungen zu erkunden.",
    
    tab_therapy: "Psychotherapie",
    tab_hr: "HR & Leadership",
    tab_research: "Forschung",
    tab_sales: "B2B Sales",
    
    scenario_label: "Das Szenario",
    insight_label: "Der LD5-Insight",
    benefit_label: "Der Nutzen",
    
    benefits_title: "Warum LD5? (The Marketing Edge)",
    benefits_description: "Die Integration von Kommunikations-Intelligenz bietet fundamentale Vorteile gegenüber klassischen NLP- oder Transkriptionslösungen.",
    
    benefit1_title: "Objektivität statt Bias",
    benefit1_desc: "Menschen bewerten Kommunikation unbewusst basierend auf Sympathie und eigenen Mustern. LD5 bewertet strikt neutral, basierend auf über 1.500+ wissenschaftlich validierten semiotischen Markern.",
    
    benefit2_title: "Echtzeit-Fähigkeit",
    benefit2_desc: "Integrieren Sie LD5 nahtlos via API in Ihre bestehenden Systeme (Zoom, Microsoft Teams oder proprietäre Apps) für unmittelbare Live-Feedback-Loops während laufender Gespräche.",
    
    benefit3_title: "Grenzenlose Skalierbarkeit",
    benefit3_desc: "Analysieren Sie tausende Stunden von Gesprächen, Interviews oder Sales-Calls gleichzeitig. LD5 bietet bei jedem Datensatz dieselbe diagnostische Sorgfalt wie ein erfahrener psychologischer Experte.",
    
    benefit4_title: "Deep-Tech Integration",
    benefit4_desc: "Technologisch zukunftssicher: Basierend auf modernsten Large Language Models (wie Gemini 2.5 Flash), jedoch entscheidend veredelt und spezialisiert durch unser proprietäres tiefenpsychologisches Regelwerk.",
    
    footer_title: "Machen Sie Kommunikation sichtbar",
    footer_description: "LeanDeep LD5 ist das Mikroskop für die menschliche Interaktion. Ob es darum geht, Leben in der Therapie zu verbessern, die besten Talente im HR zu finden oder die Wissenschaft voranzutreiben – wir helfen Ihnen, die Wahrheit zwischen den Zeilen zu lesen.",
    footer_cta_title: "Wollen Sie die unsichtbaren Signale Ihrer Daten sehen?",
    footer_cta_button: "Kontaktieren Sie unser Sales-Team für eine Live-Demo",
    footer_rights: "All rights reserved."
  },
  
  en: {
    page_title: "LeanDeep LD5 - Communication Intelligence",
    nav_vision: "Vision",
    nav_engine: "Engine",
    nav_usecases: "Use Cases",
    nav_benefits: "Benefits",
    nav_cta: "Request Live Demo",
    
    hero_tagline: "Beyond the Words",
    hero_title_pt1: "Decrypt the Deep Structure of",
    hero_title_pt2: "Communication",
    hero_title_pt3: "",
    hero_description: "In a world drowning in data, the most critical information often remains invisible: the psychological and semiotic dynamics between people. LeanDeep LD5 is your high-end intelligence engine for the 'how' behind the 'what'.",
    hero_detail: "By combining linguistic precision, prosodic analysis (speech melody), and deep-psychological algorithms, LD5 transforms fleeting conversations into measurable, objective data. It's not just a transcription tool – it's an analytical instrument for human interaction.",
    
    arch_title: "The Four-Level Model",
    arch_description: "This section visualizes LD5's fractal architecture. It shows how, from the finest microscopic signals, complex psychological meta-patterns are progressively computed.",
    
    layer_ato_title: "ATO",
    layer_ato_subtitle: "Atomic Markers",
    layer_ato_desc: "The smallest building blocks. LD5 measures pauses, filler words ('um'), word choice preferences, and subtle pitch variations in milliseconds.",
    
    layer_sem_title: "SEM",
    layer_sem_subtitle: "Semantic Markers",
    layer_sem_desc: "Units of meaning and intent. Does the system detect irony? Genuine praise? Hidden accusation or a desire for closeness?",
    
    layer_clu_title: "CLU",
    layer_clu_subtitle: "Cluster Markers",
    layer_clu_desc: "Combinations that define emotional states. A 'resistance cluster' emerges, for example, when defensive language pairs with falling intonation.",
    
    layer_mema_title: "MEMA",
    layer_mema_subtitle: "Meta-Patterns",
    layer_mema_desc: "The long-term DNA of communication. Here, complex relationship dynamics (per Gottman) or developmental stages (Spiral Dynamics) become objectively visible.",
    
    usecases_title: "Interactive Use Cases",
    usecases_description: "Experience how LD5 uncovers hidden dynamics across various domains. Select a use case to explore the scenario, the LD5 insight, and resulting data-driven visualizations.",
    
    tab_therapy: "Psychotherapy",
    tab_hr: "HR & Leadership",
    tab_research: "Research",
    tab_sales: "B2B Sales",
    
    scenario_label: "The Scenario",
    insight_label: "The LD5 Insight",
    benefit_label: "The Value",
    
    benefits_title: "Why LD5?",
    benefits_description: "Integrating communication intelligence delivers fundamental advantages over classic NLP or transcription solutions.",
    
    benefit1_title: "Objectivity Over Bias",
    benefit1_desc: "People unconsciously rate communication through the lens of sympathy and personal patterns. LD5 evaluates purely neutrally, based on 1,500+ scientifically validated semiotic markers.",
    
    benefit2_title: "Real-Time Capability",
    benefit2_desc: "Integrate LD5 seamlessly via API into your existing systems (Zoom, Microsoft Teams, or proprietary apps) for immediate live feedback loops during ongoing conversations.",
    
    benefit3_title: "Limitless Scalability",
    benefit3_desc: "Analyze thousands of hours of conversations, interviews, or sales calls simultaneously. LD5 delivers the same diagnostic rigor at every dataset as an experienced psychological expert.",
    
    benefit4_title: "Deep-Tech Integration",
    benefit4_desc: "Future-proof technologically: Built on cutting-edge Large Language Models (like Gemini 2.5 Flash), yet decisively refined and specialized through our proprietary deep-psychological rule system.",
    
    footer_title: "Make Communication Visible",
    footer_description: "LeanDeep LD5 is the microscope for human interaction. Whether improving lives in therapy, finding top talent in HR, or advancing science – we help you read the truth between the lines.",
    footer_cta_title: "Want to see the invisible signals in your data?",
    footer_cta_button: "Contact our sales team for a live demo",
    footer_rights: "All rights reserved."
  }
};

// Detect current language from localStorage, default to 'de'
let currentLanguage = localStorage.getItem('leandeep-lang') || 'de';

// Apply translations on page load
function applyTranslations() {
  document.documentElement.lang = currentLanguage;
  
  document.querySelectorAll('[data-i18n-key]').forEach(el => {
    const key = el.getAttribute('data-i18n-key');
    const text = translations[currentLanguage][key];
    
    if (text) {
      if (el.tagName === 'TITLE') {
        el.textContent = text;
      } else if (el.hasAttribute('placeholder')) {
        el.placeholder = text;
      } else if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        el.value = text;
      } else {
        el.textContent = text;
      }
    }
  });
  
  // Update language toggle button
  const langBtn = document.getElementById('langToggle');
  if (langBtn) {
    langBtn.textContent = currentLanguage === 'de' ? 'EN' : 'DE';
  }
}

// Toggle language
function toggleLanguage() {
  currentLanguage = currentLanguage === 'de' ? 'en' : 'de';
  localStorage.setItem('leandeep-lang', currentLanguage);
  applyTranslations();
}

// Initialize on DOM ready
document.addEventListener('DOMContentLoaded', applyTranslations);
