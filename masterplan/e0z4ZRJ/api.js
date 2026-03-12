
export const api = {
  getLayerData: async () => {

    await new Promise(resolve => setTimeout(resolve, 800));
    return [
      { name: 'Jan', ato: 400, sem: 240, clu: 200, mema: 150 },
      { name: 'Feb', ato: 300, sem: 139, clu: 221, mema: 200 },
      { name: 'Mär', ato: 200, sem: 980, clu: 229, mema: 210 },
      { name: 'Apr', ato: 278, sem: 390, clu: 200, mema: 180 },
      { name: 'Mai', ato: 189, sem: 480, clu: 218, mema: 250 },
    ];
  },
  
  getMarkers: async () => {
    return [
      { id: 'm1', label: 'Integritäts-Check', type: 'ATO', status: 'active', desc: 'Prüfung der Datenkonsistenz über alle Knoten.' },
      { id: 'm2', label: 'Semantischer Fokus', type: 'SEM', status: 'warning', desc: 'Abweichung in der Kontext-Zuordnung erkannt.' },
      { id: 'm3', label: 'Cluster-Validierung', type: 'CLU', status: 'active', desc: 'Optimierung der Gruppierungs-Vektoren.' },
      { id: 'm4', label: 'Memory-Sync', type: 'MEMA', status: 'idle', desc: 'Synchronisation der Langzeit-Speicher-Module.' },
    ];
  }
};
