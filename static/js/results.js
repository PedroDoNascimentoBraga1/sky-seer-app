document.addEventListener('DOMContentLoaded', () => {
    const modalOverlay = document.getElementById('history-modal-overlay');
    if (!modalOverlay) return;

    const modalTitle = document.getElementById('modal-title');
    const modalTableHead = document.getElementById('modal-table-head');
    const modalTableBody = document.getElementById('modal-table-body');
    const closeModalBtn = document.getElementById('modal-close-btn');
    const openModalButtons = document.querySelectorAll('.toggle-history-btn');

    openModalButtons.forEach(button => {
        button.addEventListener('click', () => {
            try {
                const title = button.dataset.title;
                const headers = JSON.parse(button.dataset.headers);
                const history = JSON.parse(button.dataset.history);

                modalTitle.textContent = `Histórico: ${title}`;
                modalTableHead.innerHTML = `<tr><th>${headers[0]}</th><th>${headers[1]}</th></tr>`;
                modalTableBody.innerHTML = '';
                
                history.reverse().forEach(record => {
                    const row = document.createElement('tr');
                    row.innerHTML = `<td>${record.year}</td><td>${record.value}</td>`;
                    modalTableBody.appendChild(row);
                });

                modalOverlay.classList.add('active');

            } catch (error) {
                // Se um erro acontecer, esta parte nos ajuda a descobrir o porquê
                console.error("--- ERRO AO PROCESSAR DADOS DO HISTÓRICO ---");
                console.error("Erro:", error);
                console.error("Dados dos Cabeçalhos (Headers):", button.dataset.headers);
                console.error("Dados do Histórico (History):", button.dataset.history);
                alert("Ocorreu um erro ao tentar exibir o histórico. Verifique o console do navegador para mais detalhes (F12).");
            }
        });
    });

    const closeModal = () => {
        modalOverlay.classList.remove('active');
    };

    closeModalBtn.addEventListener('click', closeModal);
    modalOverlay.addEventListener('click', (event) => {
        if (event.target === modalOverlay) {
            closeModal();
        }
    });
});