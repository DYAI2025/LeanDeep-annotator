
const create = window.zustand.default || window.zustand;

export const useStore = create((set) => ({
    activeLayers: {
        ATO: true,
        SEM: true,
        CLU: true,
        MEMA: true
    },
    selectedMarkerId: null,
    isStructureModalOpen: false,

    toggleLayer: (layerType) => set((state) => ({
        activeLayers: {
            ...state.activeLayers,
            [layerType]: !state.activeLayers[layerType]
        }
    })),

    selectMarker: (id) => set({ selectedMarkerId: id }),
    
    toggleStructureModal: (val) => set((state) => ({ 
        isStructureModalOpen: typeof val === 'boolean' ? val : !state.isStructureModalOpen 
    }))
}));
