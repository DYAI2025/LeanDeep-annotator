import { useStore } from './store.js';
import { LAYERS, MOCK_TRANSCRIPT, MOCK_MARKERS, PROJECT_STRUCTURE } from './data_mock.js';

export function renderLayerToggles() {
    const container = document.getElementById('layer-toggles');
    const { activeLayers, toggleLayer } = useStore.getState();

    container.innerHTML = '';
    
    Object.entries(LAYERS).forEach(([key, info]) => {
        const btn = document.createElement('button');
        const isActive = activeLayers[key];
        btn.className = `layer-btn ${isActive ? 'active' : 'inactive'}`;
        btn.setAttribute('aria-pressed', isActive);
        btn.setAttribute('aria-label', `Toggle ${info.desc} Layer`);
        
        btn.innerHTML = `
            <div class="w-1.5 h-6 rounded-full" style="background-color: ${info.color}"></div>
            <div class="flex-1 text-left">
                <div class="leading-none mb-0.5">${key}</div>
                <div class="text-[10px] text-muted font-normal lowercase tracking-normal">${info.desc}</div>
            </div>
        `;
        
        btn.onclick = () => {
            toggleLayer(key);
            renderLayerToggles();
            renderTranscript();
        };
        
        container.appendChild(btn);
    });
}

export function renderTranscript() {
    const container = document.getElementById('transcript-container');
    const { activeLayers, selectedMarkerId } = useStore.getState();
    
    container.innerHTML = '';

    MOCK_TRANSCRIPT.forEach(msg => {
        const msgMarkers = MOCK_MARKERS.filter(m => m.msgId === msg.id && activeLayers[m.type]);
        const wrapper = document.createElement('div');
        wrapper.className = "mb-16 group relative transition-opacity duration-300";
        
        let htmlContent = msg.text;

        const sortedMarkers = [...msgMarkers].sort((a, b) => (b.end - b.start) - (a.end - a.start));
        
        sortedMarkers.forEach(m => {
            const snippet = msg.text.substring(m.start, m.end);
            const isSelected = selectedMarkerId === m.id;
            const cls = `marker marker-${m.type.toLowerCase()} ${isSelected ? 'marker-active' : ''}`;
            htmlContent = htmlContent.replace(snippet, `<span class="${cls}" tabindex="0" data-marker-id="${m.id}">${snippet}</span>`);
        });

        wrapper.innerHTML = `
            <div class="flex items-center gap-4 mb-5">
                <span class="text-[10px] font-mono font-bold uppercase tracking-[0.2em] text-muted">${msg.speaker}</span>
                <div class="h-[1px] flex-1 bg-border/40"></div>
                <span class="text-[10px] font-mono text-muted/60">14:20:05</span>
            </div>
            <div class="text-base font-medium leading-[1.5] text-secondary tracking-tight">
                ${htmlContent}
            </div>
        `;

        container.appendChild(wrapper);
    });

    document.querySelectorAll('.marker').forEach(el => {
        el.onclick = (e) => {
            e.stopPropagation();
            const id = el.getAttribute('data-marker-id');
            useStore.getState().selectMarker(id);
            renderDetails();
            renderTranscript();
        };
        el.onkeydown = (e) => { if (e.key === 'Enter') el.click(); };
    });
}

export function renderDetails() {
    const panel = document.getElementById('right-panel');
    const content = document.getElementById('detail-content');
    const { selectedMarkerId } = useStore.getState();

    if (!selectedMarkerId) {
        panel.classList.remove('open');
        return;
    }

    const marker = MOCK_MARKERS.find(m => m.id === selectedMarkerId);
    const layerInfo = LAYERS[marker.type];

    panel.classList.add('open');
    content.innerHTML = `
        <div class="p-10 flex flex-col h-full animate-fade-in">
            <div class="flex justify-between items-center mb-12">
                <div class="flex items-center gap-3">
                    <div class="w-2.5 h-2.5 rounded-full" style="background-color: ${layerInfo.color}"></div>
                    <span class="text-[11px] font-black uppercase tracking-widest">${marker.type}</span>
                    <span class="text-[10px] font-mono text-muted/50 ml-2">ID: ${marker.id}</span>
                </div>
                <button id="close-details" aria-label="Close details" class="p-2 hover:bg-black/5 rounded-full transition-all focus-ring">
                    <i data-lucide="x" class="w-5 h-5"></i>
                </button>
            </div>

            <div class="space-y-10">
                <header>
                    <h2 class="text-3xl font-extrabold tracking-tight mb-4 text-primary">${marker.label}</h2>
                    <p class="text-base text-muted leading-relaxed">${marker.description}</p>
                </header>

                <section class="bg-surface-elevated p-6 border-l-2 border-primary">
                    <h4 class="text-[10px] font-black uppercase tracking-widest text-muted mb-3">Psychological Finding</h4>
                    <p class="text-[14px] leading-relaxed font-medium">${marker.analysis}</p>
                </section>

                <section>
                    <div class="flex justify-between items-end mb-4">
                        <h4 class="text-[10px] font-black uppercase tracking-widest text-muted">Confidence</h4>
                        <span class="font-mono font-bold text-sm">${(marker.confidence * 100).toFixed(0)}%</span>
                    </div>
                    <div class="w-full h-[2px] bg-border rounded-full overflow-hidden">
                        <div class="h-full bg-primary transition-all duration-1000" style="width: ${marker.confidence * 100}%"></div>
                    </div>
                </section>

                <section class="pt-8 border-t border-border">
                    <h4 class="text-[10px] font-black uppercase tracking-widest text-accent-blue mb-4">Intervention Strategy</h4>
                    <div class="p-5 bg-accent-blue/[0.04] border border-accent-blue/10 rounded-sm">
                        <p class="text-[14px] leading-relaxed font-semibold text-accent-blue">
                            ${marker.intervention}
                        </p>
                    </div>
                </section>
            </div>
        </div>
    `;

    lucide.createIcons();
    document.getElementById('close-details').onclick = () => {
        useStore.getState().selectMarker(null);
        renderDetails();
        renderTranscript();
    };
}

export function renderStructureModal() {
    const modal = document.getElementById('structure-modal');
    const treeContainer = document.getElementById('structure-tree');
    const { isStructureModalOpen } = useStore.getState();

    if (!isStructureModalOpen) {
        modal.classList.add('hidden');
        return;
    }

    modal.classList.remove('hidden');
    
    const generateTreeHTML = (obj, depth = 0) => {
        let html = '<ul class="space-y-1">';
        for (const [key, value] of Object.entries(obj)) {
            const isFile = Array.isArray(value);
            html += `<li class="flex flex-col">
                <div class="flex items-center gap-2 py-1">
                    <i data-lucide="${isFile ? 'folder' : 'folder-open'}" class="w-3.5 h-3.5 text-muted"></i>
                    <span class="text-[13px] font-medium text-secondary">${key}</span>
                </div>
                <div class="pl-6 border-l border-border/50 ml-1.5">
                    ${isFile 
                        ? value.map(file => `
                            <div class="flex items-center gap-2 py-1">
                                <i data-lucide="file-text" class="w-3.5 h-3.5 text-accent-blue"></i>
                                <span class="text-[13px] font-mono text-primary/80">${file}</span>
                            </div>`).join('')
                        : generateTreeHTML(value, depth + 1)
                    }
                </div>
            </li>`;
        }
        html += '</ul>';
        return html;
    };

    treeContainer.innerHTML = generateTreeHTML(PROJECT_STRUCTURE);
    lucide.createIcons();
}
