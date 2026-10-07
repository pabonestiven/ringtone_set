document.addEventListener('DOMContentLoaded', () => {
    console.log("Audio Architect UI V3 Inicializada");

    // --- TOAST NOTIFICATIONS ---
    const toastContainer = document.getElementById('toast-container');
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        
        let icon = 'ℹ️';
        if(type === 'success') icon = '✅';
        if(type === 'error') icon = '❌';
        if(type === 'warning') icon = '⚠️';

        toast.innerHTML = `<span>${icon}</span><span style="flex:1;">${message}</span>`;
        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    }

    // --- TAB NAVIGATION ---
    const navButtons = document.querySelectorAll('#sidebarNav button');
    const tabContents = document.querySelectorAll('.tab-content');

    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            navButtons.forEach(b => b.classList.remove('active'));
            tabContents.forEach(t => t.classList.remove('active'));

            btn.classList.add('active');
            document.getElementById(btn.dataset.target).classList.add('active');
            
            // Guardar en localStorage
            localStorage.setItem('activeTab', btn.dataset.target);
        });
    });
    
    // Restaurar tab activo al recargar
    const savedTab = localStorage.getItem('activeTab');
    if (savedTab) {
        const targetBtn = Array.from(navButtons).find(b => b.dataset.target === savedTab);
        if (targetBtn) targetBtn.click();
    }

    // --- PROFILES MANAGER ---
    let currentProfiles = [];
    const profileSelect = document.getElementById('profileSelect');
    
    // Inputs
    const pName = document.getElementById('profName');
    const pAtToken = document.getElementById('profAtToken');
    const pAtBase = document.getElementById('profAtBase');
    const pAtTable = document.getElementById('profAtTable');
    const pBwToken = document.getElementById('profBwToken');
    const pBwTable = document.getElementById('profBwTable');
    
    // Nuevos campos Inyección
    const pTargetFolder = document.getElementById('profTargetFolder');
    const pColAudio = document.getElementById('profColAudio');
    const pColArtist = document.getElementById('profColArtist');
    const pColTitle = document.getElementById('profColTitle');
    const pColIcon = document.getElementById('profColIcon');
    
    const profileEditor = document.getElementById('profileEditor');

    function loadProfiles() {
        fetch('/api/profiles')
            .then(r => r.json())
            .then(data => {
                currentProfiles = data;
                profileSelect.innerHTML = '<option value="">-- Selecciona un perfil --</option>';
                data.forEach(p => {
                    const opt = document.createElement('option');
                    opt.value = p.id;
                    opt.textContent = p.name || 'Sin Nombre';
                    profileSelect.appendChild(opt);
                });
            })
            .catch(e => showToast("Error cargando perfiles: " + e, 'error'));
    }

    profileSelect.addEventListener('change', () => {
        const id = profileSelect.value;
        if (!id) {
            profileEditor.style.opacity = '0.5';
            profileEditor.style.pointerEvents = 'none';
            clearProfileForm();
            return;
        }
        const p = currentProfiles.find(x => x.id === id);
        if (p) {
            profileEditor.style.opacity = '1';
            profileEditor.style.pointerEvents = 'auto';
            pName.value = p.name;
            pAtToken.value = p.airtable_token;
            pAtBase.value = p.airtable_base_id;
            pAtTable.value = p.airtable_table_id;
            pBwToken.value = p.baserow_token;
            pBwTable.value = p.baserow_table_id;
            
            pTargetFolder.value = p.target_folder || "base";
            pColAudio.value = p.col_audio || "Ringtone";
            pColArtist.value = p.col_artist || "Subtitle";
            pColTitle.value = p.col_title || "Title";
            pColIcon.value = p.col_icon || "Icon";
        }
    });

    document.getElementById('newProfileBtn').addEventListener('click', () => {
        profileSelect.value = "";
        clearProfileForm();
        profileEditor.style.opacity = '1';
        profileEditor.style.pointerEvents = 'auto';
        pName.focus();
    });

    document.getElementById('deleteProfileBtn').addEventListener('click', () => {
        const id = profileSelect.value;
        if (!id) return;
        if (confirm("¿Estás seguro de que quieres borrar este perfil?")) {
            fetch(`/api/profiles/${id}`, { method: 'DELETE' })
                .then(r => r.json())
                .then(d => {
                    showToast("Perfil borrado", "success");
                    loadProfiles();
                    clearProfileForm();
                    profileEditor.style.opacity = '0.5';
                    profileEditor.style.pointerEvents = 'none';
                });
        }
    });

    document.getElementById('saveProfileBtn').addEventListener('click', () => {
        const payload = {
            name: pName.value.trim(),
            airtable_token: pAtToken.value.trim(),
            airtable_base_id: pAtBase.value.trim(),
            airtable_table_id: pAtTable.value.trim(),
            baserow_token: pBwToken.value.trim(),
            baserow_table_id: pBwTable.value.trim(),
            target_folder: pTargetFolder.value.trim() || "base",
            col_audio: pColAudio.value.trim() || "Ringtone",
            col_artist: pColArtist.value.trim() || "Subtitle",
            col_title: pColTitle.value.trim() || "Title",
            col_icon: pColIcon.value.trim() || "Icon"
        };
        const id = profileSelect.value;
        if (id) payload.id = id;

        if (!payload.name) {
            showToast("Debes darle un nombre al perfil.", "warning");
            return;
        }

        fetch('/api/profiles', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(r => r.json())
        .then(data => {
            showToast("Perfil guardado correctamente", "success");
            loadProfiles();
            setTimeout(() => { profileSelect.value = data.id; }, 200);
        })
        .catch(e => showToast("Error guardando perfil: " + e, "error"));
    });

    function clearProfileForm() {
        pName.value = "";
        pAtToken.value = "";
        pAtBase.value = "";
        pAtTable.value = "";
        pBwToken.value = "";
        pBwTable.value = "";
        pTargetFolder.value = "base";
        pColAudio.value = "Ringtone";
        pColArtist.value = "Subtitle";
        pColTitle.value = "Title";
        pColIcon.value = "Icon";
    }

    loadProfiles();

    // --- RUN EXTERNAL SCRIPTS ---
    let activeScripts = {}; // consoleElemId -> { taskId, pollInterval }

    function executeScript(scriptName, consoleElemId, extraData = {}) {
        const consoleEl = document.getElementById(consoleElemId);
        consoleEl.textContent = "Iniciando script...\n";
        
        let cancelBtnId = consoleElemId === 'syncConsole' ? 'cancelSyncBtn' : 'cancelToolsBtn';
        const cancelBtn = document.getElementById(cancelBtnId);
        if (cancelBtn) cancelBtn.style.display = 'block';
        
        const payload = {
            script: scriptName,
            profile_id: profileSelect.value,
            ...extraData
        };

        fetch('/api/run_script', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        })
        .then(r => r.json())
        .then(data => {
            if (data.error) {
                showToast(data.error, "error");
                consoleEl.textContent += "\nError: " + data.error;
                if (cancelBtn) cancelBtn.style.display = 'none';
            } else if (data.status === 'started') {
                const taskId = data.task_id;
                
                const interval = setInterval(() => {
                    fetch('/api/script_status/' + taskId)
                    .then(r => r.json())
                    .then(statusData => {
                        if (statusData.error) return;
                        
                        consoleEl.textContent = statusData.logs.join("\n");
                        consoleEl.scrollTop = consoleEl.scrollHeight;
                        
                        if (statusData.status === 'completed' || statusData.status === 'error' || statusData.status === 'cancelled') {
                            clearInterval(interval);
                            delete activeScripts[consoleElemId];
                            if (cancelBtn) cancelBtn.style.display = 'none';
                            
                            if (statusData.status === 'completed') {
                                showToast("Operación finalizada con éxito", "success");
                            } else if (statusData.status === 'error') {
                                showToast("El script terminó con errores. Revisa la consola.", "warning");
                            } else {
                                showToast("Operación cancelada", "info");
                            }
                        }
                    });
                }, 1000);
                
                activeScripts[consoleElemId] = { taskId: taskId, pollInterval: interval };
            }
        })
        .catch(e => {
            showToast("Error de conexión al servidor", "error");
            consoleEl.textContent += "\nExcepción: " + e;
            if (cancelBtn) cancelBtn.style.display = 'none';
        });
    }

    function cancelActiveScript(consoleElemId) {
        if (activeScripts[consoleElemId]) {
            const taskId = activeScripts[consoleElemId].taskId;
            fetch('/api/cancel_script/' + taskId, {method: 'POST'})
            .then(() => {
                showToast("Cancelando...", "warning");
            });
        }
    }

    document.getElementById('cancelSyncBtn')?.addEventListener('click', () => cancelActiveScript('syncConsole'));
    document.getElementById('cancelToolsBtn')?.addEventListener('click', () => cancelActiveScript('toolsConsole'));


    document.getElementById('runAirtableBtn').addEventListener('click', () => {
        executeScript("airtable", "syncConsole");
    });
    
    document.getElementById('runBaserowBtn').addEventListener('click', () => {
        executeScript("baserow", "syncConsole");
    });


    document.getElementById('runGithubBtn').addEventListener('click', () => {
        executeScript("subir_github", "toolsConsole");
    });



    // --- FILE EXPLORER LOGIC ---
    function loadFolders() {
        const folderSelect = document.getElementById('folderSelectExp');
        if (!folderSelect) return;
        fetch('/api/folders')
            .then(r => r.json())
            .then(data => {
                if(data.folders) {
                    folderSelect.innerHTML = '<option value="">-- Selecciona la Carpeta --</option>';
                    data.folders.forEach(f => {
                        const opt = document.createElement('option');
                        opt.value = f;
                        opt.textContent = f;
                        folderSelect.appendChild(opt);
                    });
                }
            })
            .catch(e => showToast("Error cargando carpetas: " + e, 'error'));
    }
    loadFolders();

    const openFolderBtn = document.getElementById('openFolderBtn');
    if (openFolderBtn) {
        openFolderBtn.addEventListener('click', () => {
            const folder = document.getElementById('folderSelectExp').value;
            if (!folder) return showToast("Selecciona una carpeta primero.", "warning");
            
            fetch('/api/open_folder', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ folder: folder })
            })
            .then(r => r.json())
            .then(data => {
                if (data.error) showToast(data.error, "error");
                else showToast("Carpeta abierta en el explorador.", "success");
            })
            .catch(e => showToast("Error al abrir la carpeta: " + e, "error"));
        });
    }

    // --- YOUTUBE DOWNLOADER LOGIC ---
    const tasksList = document.getElementById('tasksList');
    const template = document.getElementById('taskTemplate');
    const ytConsole = document.getElementById('ytConsole');
    
    function updateQueueCount() {
        const count = tasksList.querySelectorAll('.task-card').length;
        document.getElementById('queueTitle').textContent = `Cola de Tareas (${count})`;
        
        const emptyState = document.getElementById('emptyTasksState');
        if (emptyState) {
            if (count === 0) {
                emptyState.style.display = 'block';
                tasksList.style.display = 'none';
            } else {
                emptyState.style.display = 'none';
                tasksList.style.display = 'block';
            }
        }
    }

    function addTask(data = {}) {
        const node = template.content.cloneNode(true);
        const card = node.querySelector('.task-card');
        
        card.querySelector('.task-url').value = data.url || '';
        if(data.artist) card.querySelector('.task-artist').value = data.artist;
        if(data.title) card.querySelector('.task-title').value = data.title;
        
        if (data.start) card.querySelector('.task-start-m').value = data.start;
        if (data.duration) card.querySelector('.task-dur-m').value = data.duration;
        if (data.speed) card.querySelector('.task-speed').value = data.speed;
        
        // Ranges
        const pitch = card.querySelector('.task-pitch');
        const bass = card.querySelector('.task-bass');
        const pan = card.querySelector('.task-pan');
        
        const updateVal = (input, spanClass) => {
            input.addEventListener('input', (e) => {
                card.querySelector(spanClass).textContent = e.target.value;
            });
        };
        updateVal(pitch, '.val-pitch');
        updateVal(bass, '.val-bass');
        updateVal(pan, '.val-pan');

        if (data.pitch !== undefined) { pitch.value = data.pitch; card.querySelector('.val-pitch').textContent = data.pitch; }
        if (data.bass !== undefined) { bass.value = data.bass; card.querySelector('.val-bass').textContent = data.bass; }
        if (data.pan !== undefined) { pan.value = data.pan; card.querySelector('.val-pan').textContent = data.pan; }
        if (data.fade_in !== undefined) card.querySelector('.task-fade-in').value = data.fade_in;
        if (data.fade_out !== undefined) card.querySelector('.task-fade-out').value = data.fade_out;
        if (data.pan_dinamico !== undefined) card.querySelector('.task-pan-dinamico').checked = data.pan_dinamico;

        card.querySelector('.remove-task').addEventListener('click', () => {
            card.remove();
            updateQueueCount();
        });

        // Advanced Settings Toggle
        const toggleBtn = card.querySelector('.toggle-advanced-btn');
        if (toggleBtn) {
            const advancedContent = card.querySelector('.advanced-settings-content');
            const toggleIcon = card.querySelector('.toggle-icon');
            
            toggleBtn.addEventListener('click', () => {
                if (advancedContent.style.display === 'none') {
                    advancedContent.style.display = 'block';
                    toggleIcon.style.transform = 'rotate(-180deg)';
                } else {
                    advancedContent.style.display = 'none';
                    toggleIcon.style.transform = 'rotate(0deg)';
                }
            });
        }

        // Preview Logic
        const prevBtn = card.querySelector('.preview-btn');
        const audioEl = card.querySelector('.task-audio');
        let lastPayloadStr = null;

        prevBtn.addEventListener('click', async () => {
            const url = card.querySelector('.task-url').value.trim();
            if(!url) return showToast("Falta la URL de YouTube", "warning");

            const payload = {
                url,
                start: card.querySelector('.task-start-m').value,
                duration: card.querySelector('.task-dur-m').value,
                speed: parseFloat(card.querySelector('.task-speed').value),
                pitch: parseFloat(card.querySelector('.task-pitch').value),
                bass: parseFloat(card.querySelector('.task-bass').value),
                pan: parseFloat(card.querySelector('.task-pan').value),
                pan_dinamico: card.querySelector('.task-pan-dinamico').checked,
                fade_in: parseInt(card.querySelector('.task-fade-in').value),
                fade_out: parseInt(card.querySelector('.task-fade-out').value)
            };

            const payloadStr = JSON.stringify(payload);
            if (lastPayloadStr === payloadStr && audioEl.src) {
                showToast("Esta previa ya está generada y actualizada. Reproduciendo...", "info");
                audioEl.play();
                return;
            }

            const originalText = prevBtn.textContent;
            prevBtn.textContent = '⏳ Cargando...';
            prevBtn.disabled = true;

            try {
                const res = await fetch('/api/preview', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: payloadStr
                });
                const responseData = await res.json();
                if(responseData.error) throw new Error(responseData.error);
                
                audioEl.src = responseData.preview_url + "?t=" + Date.now();
                audioEl.style.display = 'block';
                audioEl.play();
                lastPayloadStr = payloadStr;
                showToast("Nueva previa generada y lista.", "success");
            } catch(e) {
                showToast("Error generando previa: " + e.message, "error");
            } finally {
                prevBtn.textContent = '🎧 Regenerar Previa';
                prevBtn.disabled = false;
            }
        });

        tasksList.appendChild(card);
        updateQueueCount();
    }

    document.getElementById('addUrlBtn').addEventListener('click', () => addTask());
    document.getElementById('clearTasksBtn').addEventListener('click', () => {
        tasksList.innerHTML = '';
        addTask();
    });

    document.getElementById('bulkUploadFile').addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = function(event) {
            try {
                const data = JSON.parse(event.target.result);
                tasksList.innerHTML = '';
                data.forEach(item => addTask(item));
                showToast(`✅ JSON cargado (${data.length} canciones)`, "success");
            } catch (error) {
                showToast("Error parseando JSON", "error");
            }
            e.target.value = "";
        };
        reader.readAsText(file);
    });

    const pasteJsonToggleBtn = document.getElementById('pasteJsonToggleBtn');
    const pasteJsonBlock = document.getElementById('pasteJsonBlock');
    if (pasteJsonToggleBtn) {
        pasteJsonToggleBtn.addEventListener('click', () => {
            pasteJsonBlock.style.display = pasteJsonBlock.style.display === 'none' ? 'block' : 'none';
        });
    }

    document.getElementById('loadPastedJsonBtn').addEventListener('click', () => {
        const text = document.getElementById('pasteJsonInput').value.trim();
        if (!text) return showToast("Pega un JSON primero", "warning");
        try {
            const data = JSON.parse(text);
            if (Array.isArray(data)) {
                tasksList.innerHTML = '';
                data.forEach(item => addTask(item));
                showToast(`✅ Tareas cargadas desde el portapapeles (${data.length})`, "success");
                pasteJsonBlock.style.display = 'none';
            } else {
                throw new Error("El JSON debe ser una lista/array []");
            }
        } catch (error) {
            showToast("Error parseando JSON: " + error.message, "error");
        }
    });

    // Start Process
    let pollInterval = null;
    document.getElementById('startProcessBtn').addEventListener('click', async () => {
        const folder = document.getElementById('folderName').value.trim();
        if (!folder) return showToast("Ingresa la carpeta de destino.", "warning");

        const cards = document.querySelectorAll('.task-card');
        const tasks = [];
        let valid = true;

        cards.forEach(card => {
            const url = card.querySelector('.task-url').value.trim();
            if (!url) return;
            tasks.push({
                url,
                artist: card.querySelector('.task-artist').value.trim(),
                title: card.querySelector('.task-title').value.trim(),
                start: card.querySelector('.task-start-m').value,
                duration: card.querySelector('.task-dur-m').value,
                speed: parseFloat(card.querySelector('.task-speed').value),
                pitch: parseFloat(card.querySelector('.task-pitch').value),
                bass: parseFloat(card.querySelector('.task-bass').value),
                pan: parseFloat(card.querySelector('.task-pan').value),
                pan_dinamico: card.querySelector('.task-pan-dinamico').checked,
                fade_in: parseInt(card.querySelector('.task-fade-in').value),
                fade_out: parseInt(card.querySelector('.task-fade-out').value)
            });
        });

        if (tasks.length === 0) return showToast("Agrega al menos una URL válida.", "warning");

        try {
            ytConsole.textContent = "Iniciando...\n";
            document.getElementById('startProcessBtn').style.display = 'none';
            document.getElementById('cancelProcessBtn').style.display = 'block';

            const forceOverwrite = document.getElementById('forceOverwrite').checked;

            const res = await fetch('/api/process', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ folder, tasks, force_overwrite: forceOverwrite })
            });

            if (!res.ok) {
                const data = await res.json();
                throw new Error(data.error || "Error al iniciar");
            }

            pollInterval = setInterval(pollStatus, 1000);
            showToast("Procesamiento iniciado", "info");
        } catch (e) {
            showToast(e.message, "error");
            document.getElementById('startProcessBtn').style.display = 'block';
            document.getElementById('cancelProcessBtn').style.display = 'none';
        }
    });

    document.getElementById('cancelProcessBtn').addEventListener('click', () => {
        fetch('/api/cancel', {method:'POST'}).then(() => {
            showToast("Cancelación solicitada, esperando que termine la tarea actual...", "warning");
        });
    });

    function pollStatus() {
        fetch('/api/status')
        .then(r => r.json())
        .then(data => {
            ytConsole.textContent = data.logs.join("\n");
            ytConsole.scrollTop = ytConsole.scrollHeight;

            if (!data.is_processing) {
                clearInterval(pollInterval);
                document.getElementById('startProcessBtn').style.display = 'block';
                document.getElementById('cancelProcessBtn').style.display = 'none';
                
                if (data.failed_items && data.failed_items.length > 0) {
                    showToast(`Proceso finalizado. ${data.failed_items.length} tareas fallaron.`, "warning");
                } else {
                    showToast("¡Proceso finalizado con éxito!", "success");
                }
            }
        });
    }


    addTask(); // Init first empty task
    // Inicializar estado visual
    updateQueueCount();
});
