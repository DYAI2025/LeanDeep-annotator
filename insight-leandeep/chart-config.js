// chart-config.js — Chart Data for all Use Cases

const chartColors = {
    teal: 'rgba(15, 118, 110, 1)',
    tealBg: 'rgba(15, 118, 110, 0.2)',
    amber: 'rgba(217, 119, 6, 1)',
    amberBg: 'rgba(217, 119, 6, 0.2)',
    slate: 'rgba(71, 85, 105, 1)',
    slateBg: 'rgba(71, 85, 105, 0.2)',
    emerald: 'rgba(5, 150, 105, 1)'
};

const useCaseData = {
    therapy: {
        title_de: "Präzision in der Empathie",
        title_en: "Precision in Empathy",
        subtitle_de: "Objektiver Co-Pilot für Therapeuten",
        subtitle_en: "Objective Co-Pilot for Therapists",
        scenario_de: 'Ein Paar in der 5. Sitzung. Verbal behaupten beide Fortschritte ("Wir streiten weniger, alles ist ruhiger").',
        scenario_en: 'A couple in their 5th session. Verbally, both claim progress ("We fight less, everything is calmer").',
        insight_de: 'Die Analyse zeigt eine dramatische Zunahme des Metamusters <code class="bg-teal-100 text-teal-800 px-1 rounded text-xs font-mono">MEMA_WITHDRAWAL_PURSUIT_DYNAMIC</code> (Rückzug-Verfolgung). Während die Worte friedlich sind, sinkt die <code class="bg-teal-100 text-teal-800 px-1 rounded text-xs font-mono">ATO_POSITIVE_RESONANCE</code> stetig ab.',
        insight_en: 'Analysis reveals dramatic increase in the meta-pattern <code class="bg-teal-100 text-teal-800 px-1 rounded text-xs font-mono">MEMA_WITHDRAWAL_PURSUIT_DYNAMIC</code>. While words are peaceful, <code class="bg-teal-100 text-teal-800 px-1 rounded text-xs font-mono">ATO_POSITIVE_RESONANCE</code> declines steadily.',
        benefit_de: "Der Therapeut kann gezielt die non-verbale Distanzierung ansprechen, bevor es zum erneuten Rückfall kommt. LD5 ermöglicht messbare Erfolgsquoten durch den objektiven Vergleich von Sitzung 1 und 10.",
        benefit_en: "The therapist can directly address non-verbal distancing before relapse occurs. LD5 enables measurable success rates through objective session-to-session comparison.",
        chartTitle_de: "Dynamik-Divergenz über 10 Sitzungen",
        chartTitle_en: "Dynamics Divergence Over 10 Sessions",
        config: {
            type: 'line',
            data: {
                labels: ['S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'S10'],
                datasets: [
                    {
                        label: 'Verbal Consensus / Verbaler Konsens',
                        data: [30, 40, 45, 60, 80, 85, 85, 90, 95, 95],
                        borderColor: chartColors.slate,
                        borderDash: [5, 5],
                        tension: 0.4
                    },
                    {
                        label: 'Withdrawal Pattern (MEMA)',
                        data: [80, 75, 60, 65, 85, 90, 95, 95, 98, 99],
                        borderColor: chartColors.amber,
                        backgroundColor: chartColors.amberBg,
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'Positive Resonance (ATO)',
                        data: [20, 35, 50, 45, 30, 25, 20, 15, 10, 5],
                        borderColor: chartColors.teal,
                        backgroundColor: chartColors.tealBg,
                        fill: true,
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' },
                    tooltip: { mode: 'index', intersect: false }
                },
                scales: {
                    y: { beginAtZero: true, max: 100 }
                }
            }
        }
    },
    hr: {
        title_de: "Soft Skills objektivieren",
        title_en: "Objectifying Soft Skills",
        subtitle_de: "Vom Bauchgefühl zum Data-Driven Recruiting",
        subtitle_en: "From Gut Feeling to Data-Driven Recruiting",
        scenario_de: 'Führungskräfte-Assessment. Ein Kandidat wirkt im Interview extrem souverän und charismatisch.',
        scenario_en: 'Executive Assessment. A candidate appears extremely confident and charismatic in the interview.',
        insight_de: 'Die Engine erkennt ein hohes Maß an <code class="bg-teal-100 text-teal-800 px-1 rounded text-xs font-mono">ATO_CORPORATE_DOUBLESPEAK</code> kombiniert mit einer sehr geringen <code class="bg-teal-100 text-teal-800 px-1 rounded text-xs font-mono">SEM_VALIDATION</code> gegenüber dem Interviewer.',
        insight_en: 'Engine detects high <code class="bg-teal-100 text-teal-800 px-1 rounded text-xs font-mono">ATO_CORPORATE_DOUBLESPEAK</code> combined with very low <code class="bg-teal-100 text-teal-800 px-1 rounded text-xs font-mono">SEM_VALIDATION</code> toward the interviewer.',
        benefit_de: 'HR erkennt frühzeitig narzisstische Tendenzen oder mangelnde Authentizität, die durch Charme verdeckt würden. Teams können auf "Rapport-Synchronität" analysiert werden.',
        benefit_en: 'HR detects narcissistic tendencies or lack of authenticity early, which charm would otherwise conceal. Teams can be analyzed for "rapport synchrony."',
        chartTitle_de: "Verstecktes Kandidaten-Profil vs. Benchmark",
        chartTitle_en: "Hidden Candidate Profile vs. Benchmark",
        config: {
            type: 'radar',
            data: {
                labels: ['Authenticity / Authentizität', 'Empathy (SEM_VALIDATION)', 'Corporate Doublespeak', 'Superiority (CLU)', 'Resilience / Resilienz'],
                datasets: [
                    {
                        label: 'Candidate X / Kandidat X',
                        data: [30, 20, 95, 90, 60],
                        backgroundColor: chartColors.amberBg,
                        borderColor: chartColors.amber,
                        pointBackgroundColor: chartColors.amber
                    },
                    {
                        label: 'Ideal Profile / Idealprofil (Benchmark)',
                        data: [80, 85, 30, 40, 80],
                        backgroundColor: chartColors.tealBg,
                        borderColor: chartColors.teal,
                        pointBackgroundColor: chartColors.teal
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                elements: { line: { borderWidth: 3 } },
                scales: { r: { angleLines: { display: true }, suggestedMin: 0, suggestedMax: 100 } }
            }
        }
    },
    research: {
        title_de: "Qualität in Quantität wandeln",
        title_en: "Converting Quality to Quantity",
        subtitle_de: "Automatisierte linguistische Kodierung in Skalierung",
        subtitle_en: "Automated Linguistic Coding at Scale",
        scenario_de: 'Eine Studie über die sprachlichen Marker von Depressionen bei Jugendlichen in sozialen Medien oder Video-Interviews.',
        scenario_en: 'A study on linguistic markers of depression in adolescents across social media or video interviews.',
        insight_de: 'Automatischer Scan von 1.000 Stunden Videomaterial identifiziert hochsignifikante Cluster von <code class="bg-teal-100 text-teal-800 px-1 rounded text-xs font-mono">ATO_DEPRESSION_SELF_FOCUS</code> und <code class="bg-teal-100 text-teal-800 px-1 rounded text-xs font-mono">ATO_TEMPORAL_ABSOLUTIZER</code>.',
        insight_en: 'Automated scan of 1,000 hours identifies highly significant clusters of <code class="bg-teal-100 text-teal-800 px-1 rounded text-xs font-mono">ATO_DEPRESSION_SELF_FOCUS</code> and <code class="bg-teal-100 text-teal-800 px-1 rounded text-xs font-mono">ATO_TEMPORAL_ABSOLUTIZER</code>.',
        benefit_de: 'Was früher durch menschliche Rater Jahre dauerte, erledigt LD5 in Stunden mit einer Konsistenz (Inter-Rater-Reliability), die den menschlichen Standard weit übertrifft.',
        benefit_en: 'What once took years of human rating, LD5 completes in hours with inter-rater reliability far exceeding human standards.',
        chartTitle_de: "Marker-Frequenz in Datensätzen (n=10.000)",
        chartTitle_en: "Marker Frequency in Datasets (n=10,000)",
        config: {
            type: 'bar',
            data: {
                labels: ['Self-Focus (ATO)', 'Temporal Absolutes (ATO)', 'Negative Cognition', 'Isolation Vocabulary', 'Affect Flatness'],
                datasets: [{
                    label: 'Clinical Cohort / Klinische Kohorte',
                    data: [85, 78, 92, 65, 70],
                    backgroundColor: chartColors.amber
                },
                {
                    label: 'Control Group / Kontrollgruppe',
                    data: [25, 35, 20, 15, 10],
                    backgroundColor: chartColors.teal
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'top' } },
                scales: { y: { beginAtZero: true } }
            }
        }
    },
    sales: {
        title_de: "Die Wahrheit zwischen den Zeilen",
        title_en: "The Truth Between the Lines",
        subtitle_de: "Predictive Analytics in High-Stakes Verhandlungen",
        subtitle_en: "Predictive Analytics in High-Stakes Negotiations",
        scenario_de: 'Ein Verkaufsgespräch für ein Millionenprojekt. Nach der Preisnennung sagt der Kunde: "Das klingt sehr interessant, wir prüfen das in Ruhe."',
        scenario_en: 'A million-dollar sales call. After pricing, the prospect says: "That sounds interesting, we\'ll review it carefully."',
        insight_de: 'LD5 erkennt simultan <code class="bg-teal-100 text-teal-800 px-1 rounded text-xs font-mono">SEM_UNCERTAINTY_PROSODY</code> (hohe Unsicherheit in der Mikrostimmführung) und klassifiziert die Aussage als <code class="bg-teal-100 text-teal-800 px-1 rounded text-xs font-mono">CLU_SOFT_REJECTION_PATTERN</code>.',
        insight_en: 'LD5 detects <code class="bg-teal-100 text-teal-800 px-1 rounded text-xs font-mono">SEM_UNCERTAINTY_PROSODY</code> (micro-pitch uncertainty) and classifies it as <code class="bg-teal-100 text-teal-800 px-1 rounded text-xs font-mono">CLU_SOFT_REJECTION_PATTERN</code>.',
        benefit_de: 'Das Sales-Team weiß sofort, dass sie nicht "abwarten" dürfen, sondern den versteckten Einwand proaktiv adressieren müssen.',
        benefit_en: 'Sales team knows immediately they must address hidden objections, not wait for a callback.',
        chartTitle_de: "Deal Probability vs. Hidden Uncertainty",
        chartTitle_en: "Deal Probability vs. Hidden Uncertainty",
        config: {
            type: 'line',
            data: {
                labels: ['Min 5', 'Min 15', 'Min 30', 'Min 45 (Pitch)', 'Min 50 (Price)', 'Min 55 (Response)', 'Min 60 (Close)'],
                datasets: [
                    {
                        label: 'CRM Sales Probability',
                        data: [30, 40, 60, 85, 85, 90, 90],
                        borderColor: chartColors.slate,
                        borderDash: [5, 5],
                        fill: false,
                        tension: 0.1
                    },
                    {
                        label: 'Uncertainty Prosody (SEM)',
                        data: [10, 15, 12, 10, 85, 95, 88],
                        borderColor: chartColors.amber,
                        backgroundColor: chartColors.amberBg,
                        fill: true,
                        tension: 0.4
                    },
                    {
                        label: 'Soft Rejection Cluster (CLU)',
                        data: [0, 0, 0, 0, 20, 85, 95],
                        borderColor: chartColors.emerald,
                        backgroundColor: chartColors.emerald,
                        type: 'bar',
                        barPercentage: 0.3
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { tooltip: { mode: 'index', intersect: false } },
                scales: { y: { beginAtZero: true, max: 100 } }
            }
        }
    }
};
