import { renderLayerToggles, renderTranscript, renderDetails, renderStructureModal } from './components.js';
import { useStore } from './store.js';

document.addEventListener('DOMContentLoaded', () => {
    lucide.createIcons();


    renderLayerToggles();
    renderTranscript();
    renderDetails();


    document.addEventListener('click', (e) => {
        const isMarker = e.target.closest('.marker');
        const isPanel = e.target.closest('#right-panel');
        const isToggle = e.target.closest('.layer-btn');
        const isModal = e.target.closest('#structure-modal-content');
        const isModalBtn = e.target.closest('#open-structure');

        if (!isMarker && !isPanel && !isToggle && !isModal && !isModalBtn) {
            const currentSelected = useStore.getState().selectedMarkerId;
            if (currentSelected) {
                useStore.getState().selectMarker(null);
                renderDetails();
                renderTranscript();
            }
            useStore.getState().toggleStructureModal(false);
            renderStructureModal();
        }
    });


    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            useStore.getState().selectMarker(null);
            useStore.getState().toggleStructureModal(false);
            renderDetails();
            renderTranscript();
            renderStructureModal();
        }
    });


    document.getElementById('open-structure').onclick = () => {
        useStore.getState().toggleStructureModal(true);
        renderStructureModal();
    };

    document.getElementById('close-structure').onclick = () => {
        useStore.getState().toggleStructureModal(false);
        renderStructureModal();
    };
});
