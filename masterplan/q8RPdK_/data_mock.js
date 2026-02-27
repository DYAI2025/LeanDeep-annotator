export const LAYERS = {
    ATO: { color: '#F26B63', desc: 'Atomic Markers', pattern: 'solid' },
    SEM: { color: '#7C6FF2', desc: 'Semantic Context', pattern: 'dashed' },
    CLU: { color: '#3FBCC1', desc: 'Behavioral Clusters', pattern: 'dotted' },
    MEMA: { color: '#F2B35C', desc: 'Meta-Diagnostics', pattern: 'double' }
};

export const MOCK_TRANSCRIPT = [
    { id: 'm1', speaker: 'Client', text: 'Ich fühle mich in letzter Zeit oft missverstanden, besonders wenn ich versuche, meine Grenzen klar zu kommunizieren.' },
    { id: 'm2', speaker: 'Analyst', text: 'Können Sie ein konkretes Beispiel nennen, in dem dieser Kommunikationsabbruch stattgefunden hat?' }
];

export const MOCK_MARKERS = [
    {
        id: 'ann_001',
        msgId: 'm1',
        type: 'ATO',
        start: 45,
        end: 58,
        label: 'Grenzen klar',
        description: 'Selbstbehauptungs-Marker mit defensiver Tonalität.',
        analysis: 'Der Proband zeigt eine Diskrepanz zwischen verbaler Intention und paraverbalem Rückzug.',
        confidence: 0.92,
        intervention: 'Spiegeln der Ambivalenz zwischen Wortwahl und Körpersprache.'
    },
    {
        id: 'ann_002',
        msgId: 'm1',
        type: 'MEMA',
        start: 14,
        end: 28,
        label: 'missverstanden',
        description: 'Kern-Ruptur in der Beziehungsdynamik.',
        analysis: 'Wiederkehrendes Motiv der Isolation. Hinweis auf tiefsitzende Bindungsunsicherheit.',
        confidence: 0.85,
        intervention: 'Validierung des emotionalen Erlebens vor der kognitiven Umstrukturierung.'
    }
];

export const PROJECT_STRUCTURE = {
    "src/": {
        "components/": {
            "analysis/": ["MarkerCard.ts", "MarkerList.ts", "TranscriptView.ts"],
            "layout/": ["TopBar.ts", "LeftSidebar.ts", "RightPanel.ts"]
        },
        "lib/": ["api.ts", "layers.ts", "chat-parser.ts"],
        "context/": ["AppContext.tsx"]
    }
};
