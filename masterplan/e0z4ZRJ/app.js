import { api } from './api.js';


const state = {
  currentRoute: 'dashboard',
  activeLayers: { ATO: true, SEM: true, CLU: true, MEMA: true },
  selectedMarker: null,
  isSidebarOpen: true,
  isLoading: false,
  data: []
};

const routes = {
  dashboard: { title: 'Übersicht', icon: 'LayoutDashboard' },
  analyze: { title: 'Analyse', icon: 'Zap' },
  conversation: { title: 'Konversation', icon: 'MessageSquare' },
  persona: { title: 'Persona', icon: 'UserCircle' },
  developers: { title: 'Entwickler', icon: 'Code' }
};

const layerColors = {
  ATO: 'var(--color-ato)',
  SEM: 'var(--color-sem)',
  CLU: 'var(--color-clu)',
  MEMA: 'var(--color-mema)'
};

function render() {
  const root = document.getElementById('root');
  
  root.innerHTML = `
    <!-- Sidebar -->
    <aside class="w-64 glass-panel border-r border-slate-200 flex flex-col h-full z-30 transition-all duration-300">
      <div class="p-6">
        <div class="flex items-center gap-3 mb-10">
          <div class="w-10 h-10 rounded-xl bg-ato-gradient shadow-lg flex items-center justify-center text-white">
            <i data-lucide="layers" class="w-6 h-6"></i>
          </div>
          <span class="text-xl font-bold tracking-tight text-slate-800">LeanDeep</span>
        </div>

        <nav class="space-y-2">
          ${Object.entries(routes).map(([key, route]) => `
            <button onclick="window.navigateTo('${key}')" 
              class="w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-200 ${state.currentRoute === key ? 'neu-button text-slate-900 font-semibold' : 'text-slate-500 hover:text-slate-700'}">
              <i data-lucide="${route.icon}" class="w-5 h-5"></i>
              <span>${route.title}</span>
            </button>
          `).join('')}
        </nav>
      </div>

      <div class="mt-auto p-6 space-y-6">
        <div class="p-4 rounded-2xl neu-inset">
          <p class="text-[10px] uppercase tracking-wider text-slate-400 mb-3 font-bold">Layer Filter</p>
          <div class="space-y-2">
            ${['ATO', 'SEM', 'CLU', 'MEMA'].map(l => `
              <label class="flex items-center justify-between cursor-pointer group">
                <span class="text-sm font-medium text-slate-600 group-hover:text-slate-900 transition-colors">${l}</span>
                <input type="checkbox" ${state.activeLayers[l] ? 'checked' : ''} 
                  onchange="window.toggleLayer('${l}')"
                  class="w-4 h-4 rounded border-slate-300 text-slate-800 focus:ring-ato-500">
              </label>
            `).join('')}
          </div>
        </div>
        
        <div class="flex items-center gap-2 px-2">
          <div class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
          <span class="text-xs text-slate-400 font-medium tracking-wide">DSGVO Konform</span>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 flex flex-col h-full bg-[#F8FAFC] overflow-hidden relative">
      <!-- Topbar -->
      <header class="h-16 border-b border-slate-100 flex items-center justify-between px-8 bg-white/50 backdrop-blur-sm z-20">
        <div class="flex items-center gap-4">
          <span class="text-xs font-bold text-slate-300 uppercase tracking-widest">LeanDeep</span>
          <i data-lucide="chevron-right" class="w-4 h-4 text-slate-300"></i>
          <span class="text-sm font-medium text-slate-600">${routes[state.currentRoute].title}</span>
        </div>

        <div class="flex items-center gap-6">
          <div class="flex items-center gap-4 px-4 py-1.5 rounded-full bg-slate-50 border border-slate-100">
             <div class="flex items-center gap-1.5">
               <i data-lucide="shield-check" class="w-4 h-4 text-emerald-500"></i>
               <span class="text-[11px] font-bold text-slate-500">MADE IN GERMANY</span>
             </div>
             <div class="w-px h-3 bg-slate-200"></div>
             <span class="text-[11px] font-bold text-slate-500">SECURE CLOUD</span>
          </div>
          <button class="w-10 h-10 rounded-full neu-button flex items-center justify-center text-slate-600">
            <i data-lucide="bell" class="w-5 h-5"></i>
          </button>
        </div>
      </header>

      <!-- View Container -->
      <div id="content-area" class="flex-1 p-8 overflow-y-auto">
        ${renderCurrentRoute()}
      </div>
      
      <!-- Right Panel Slide-in -->
      <div id="right-panel" class="absolute top-0 right-0 h-full w-96 glass-panel border-l border-slate-200 shadow-2xl transition-transform duration-500 transform ${state.selectedMarker ? 'translate-x-0' : 'translate-x-full'} z-40 p-8">
        ${renderRightPanel()}
      </div>
    </main>
  `;

  lucide.createIcons();
  if (state.currentRoute === 'dashboard') {
     initDashboardCharts();
  }
}

function renderCurrentRoute() {
  switch(state.currentRoute) {
    case 'dashboard': return `
      <div class="max-w-6xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div class="col-span-2 p-8 rounded-3xl neu-flat space-y-6">
            <div class="flex items-center justify-between">
              <div>
                <h2 class="text-2xl font-bold text-slate-800">System Performance</h2>
                <p class="text-slate-400 text-sm font-medium mt-1">Echtzeit-Analyse der Layer-Aktivität</p>
              </div>
              <div class="flex gap-2">
                <button class="px-4 py-2 rounded-xl neu-button text-xs font-bold text-slate-600">HEUTE</button>
                <button class="px-4 py-2 rounded-xl neu-button text-xs font-bold text-slate-600">WOCHE</button>
              </div>
            </div>
            <div id="main-chart" class="h-64 w-full flex items-center justify-center text-slate-300 bg-slate-50/50 rounded-2xl border border-dashed border-slate-200">
              <span class="text-xs uppercase tracking-widest font-bold">Chart-Visualisierung wird geladen...</span>
            </div>
          </div>
          
          <div class="p-8 rounded-3xl neu-flat flex flex-col justify-between">
             <div class="space-y-2">
               <h3 class="text-lg font-bold text-slate-800">Aktive Marker</h3>
               <p class="text-slate-400 text-sm">Zuletzt erkannte Anomalien</p>
             </div>
             <div class="space-y-4 mt-6" id="marker-list">
               <!-- Markers loaded here -->
             </div>
          </div>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-4 gap-6">
          ${['ATO', 'SEM', 'CLU', 'MEMA'].map(l => `
            <div class="p-6 rounded-2xl neu-flat border-t-4" style="border-top-color: ${layerColors[l]}">
              <span class="text-xs font-bold text-slate-400 uppercase tracking-widest">${l} Layer</span>
              <div class="text-3xl font-black text-slate-800 mt-2">99.2%</div>
              <div class="text-[10px] text-green-500 font-bold mt-1">▲ 0.4% vs. Vormonat</div>
            </div>
          `).join('')}
        </div>
      </div>
    `;
    case 'analyze': return `
      <div class="max-w-4xl mx-auto text-center py-20 space-y-6">
        <div class="w-20 h-20 bg-slate-100 rounded-3xl mx-auto flex items-center justify-center neu-button">
          <i data-lucide="zap" class="w-10 h-10 text-violet-500"></i>
        </div>
        <h1 class="text-3xl font-bold text-slate-800">Deep Analysis Engine</h1>
        <p class="text-slate-500 max-w-lg mx-auto leading-relaxed">Verarbeiten Sie komplexe Datensätze mit unserer Layer-basierten Architektur. Keine Konfiguration nötig – Made in Germany.</p>
        <button class="px-8 py-4 bg-slate-900 text-white rounded-2xl font-bold shadow-xl hover:scale-105 transition-transform">Analyse Starten</button>
      </div>
    `;
    default: return `
      <div class="flex flex-col items-center justify-center h-full text-slate-400 space-y-4">
        <i data-lucide="construction" class="w-12 h-12"></i>
        <p class="font-medium">Diese Sektion wird aktuell für Sie vorbereitet.</p>
      </div>
    `;
  }
}

function renderRightPanel() {
  if (!state.selectedMarker) return '';
  const m = state.selectedMarker;
  return `
    <div class="h-full flex flex-col">
      <button onclick="window.closePanel()" class="self-end p-2 rounded-full neu-button mb-8">
        <i data-lucide="x" class="w-5 h-5"></i>
      </button>
      
      <div class="flex items-center gap-3 mb-6">
        <div class="w-12 h-12 rounded-2xl flex items-center justify-center text-white font-bold text-lg" style="background-color: ${layerColors[m.type]}">
          ${m.type[0]}
        </div>
        <div>
          <h3 class="font-bold text-xl text-slate-800">${m.label}</h3>
          <span class="text-xs font-bold px-2 py-0.5 rounded bg-slate-100 text-slate-500 uppercase">${m.type} Marker</span>
        </div>
      </div>

      <div class="space-y-6 flex-1">
        <div class="p-6 rounded-2xl neu-inset bg-white/50">
          <h4 class="text-xs font-bold text-slate-400 uppercase mb-2">Beschreibung</h4>
          <p class="text-sm text-slate-600 leading-relaxed">${m.desc}</p>
        </div>

        <div class="space-y-4">
          <h4 class="text-xs font-bold text-slate-400 uppercase">Metriken</h4>
          <div class="grid grid-cols-2 gap-4">
            <div class="p-4 rounded-xl neu-flat">
              <span class="text-[10px] text-slate-400 font-bold block uppercase">Latenz</span>
              <span class="text-lg font-bold text-slate-700">4.2ms</span>
            </div>
            <div class="p-4 rounded-xl neu-flat">
              <span class="text-[10px] text-slate-400 font-bold block uppercase">Confidence</span>
              <span class="text-lg font-bold text-slate-700">98%</span>
            </div>
          </div>
        </div>
      </div>

      <button class="w-full py-4 mt-auto rounded-2xl neu-button text-slate-800 font-bold border border-slate-100">
        Marker-Details exportieren
      </button>
    </div>
  `;
}


window.navigateTo = (route) => {
  state.currentRoute = route;
  state.selectedMarker = null;
  render();
};

window.toggleLayer = (layer) => {
  state.activeLayers[layer] = !state.activeLayers[layer];
  render();
};

window.openMarker = (id) => {
  api.getMarkers().then(markers => {
    state.selectedMarker = markers.find(m => m.id === id);
    render();
  });
};

window.closePanel = () => {
  state.selectedMarker = null;
  render();
};


async function initDashboardCharts() {
  const data = await api.getLayerData();
  const markers = await api.getMarkers();
  
  const markerContainer = document.getElementById('marker-list');
  if (markerContainer) {
    markerContainer.innerHTML = markers.map(m => `
      <div onclick="window.openMarker('${m.id}')" class="group flex items-center gap-4 p-3 rounded-2xl hover:bg-white cursor-pointer transition-all border border-transparent hover:border-slate-100 hover:shadow-sm">
        <div class="w-2 h-10 rounded-full" style="background-color: ${layerColors[m.type]}"></div>
        <div class="flex-1">
          <div class="text-sm font-bold text-slate-700">${m.label}</div>
          <div class="text-[10px] text-slate-400 uppercase tracking-tighter font-medium">${m.type} • VOR 2 MIN</div>
        </div>
        <i data-lucide="chevron-right" class="w-4 h-4 text-slate-200 group-hover:text-slate-400 transition-colors"></i>
      </div>
    `).join('');
    lucide.createIcons();
  }




  const chartEl = document.getElementById('main-chart');
  if (chartEl) {
    chartEl.innerHTML = `
      <svg viewBox="0 0 500 200" class="w-full h-full p-4">
        <defs>
          <linearGradient id="grad-ato" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="var(--color-ato)" stop-opacity="0.3"/><stop offset="100%" stop-color="var(--color-ato)" stop-opacity="0"/></linearGradient>
        </defs>
        <path d="M0,150 Q50,140 100,160 T200,120 T300,140 T400,100 T500,130 L500,200 L0,200 Z" fill="url(#grad-ato)" opacity="0.5"/>
        <path d="M0,150 Q50,140 100,160 T200,120 T300,140 T400,100 T500,130" stroke="var(--color-ato)" stroke-width="3" fill="none" />
        <path d="M0,180 Q100,170 200,185 T400,160 T500,175" stroke="var(--color-sem)" stroke-width="2" fill="none" stroke-dasharray="4" />
      </svg>
    `;
  }
}


render();
