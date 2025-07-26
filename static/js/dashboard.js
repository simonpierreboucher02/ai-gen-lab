/**
 * AI Playground - JavaScript Principal
 * Gestion des interactions, streaming, thèmes et responsive design
 */

// Configuration globale
const DashboardConfig = {
    apiBaseUrl: '/api',
    streamTimeout: 300000, // 5 minutes
    pollInterval: 2000,
    toastDuration: 4000,
    animationDuration: 300
};

// State global de l'application
const AppState = {
    currentTheme: localStorage.getItem('theme') || 'light',
    activeStreams: new Map(),
    isLoading: false,
    currentPage: window.location.pathname
};

/**
 * =============================================================================
 * INITIALISATION ET UTILITAIRES
 * =============================================================================
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialiser le thème
    initializeTheme();
    
    // Initialiser les composants
    initializeComponents();
    
    // Initialiser les event listeners globaux
    initializeGlobalEvents();
    
    // Initialiser la page courante
    initializeCurrentPage();
    
    // Gérer le retry prompt depuis sessionStorage
    handleRetryPrompt();
    
    console.log('Dashboard AI Playground initialisé');
}

function initializeTheme() {
    document.documentElement.setAttribute('data-theme', AppState.currentTheme);
    
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', toggleTheme);
        updateThemeIcon();
    }
}

function toggleTheme() {
    AppState.currentTheme = AppState.currentTheme === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', AppState.currentTheme);
    localStorage.setItem('theme', AppState.currentTheme);
    updateThemeIcon();
    
    showToast(`Thème ${AppState.currentTheme === 'dark' ? 'sombre' : 'clair'} activé`, 'info');
}

function updateThemeIcon() {
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        const icon = themeToggle.querySelector('i');
        if (icon) {
            icon.className = AppState.currentTheme === 'dark' 
                ? 'fas fa-sun me-2' 
                : 'fas fa-moon me-2';
        }
    }
}

function initializeComponents() {
    // Initialiser Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialiser Bootstrap popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

function initializeGlobalEvents() {
    // Gestion du redimensionnement
    window.addEventListener('resize', debounce(handleResize, 250));
    
    // Gestion de la visibilité de la page
    document.addEventListener('visibilitychange', handleVisibilityChange);
    
    // Gestion des erreurs globales
    window.addEventListener('error', handleGlobalError);
    
    // Gestion des promesses rejetées
    window.addEventListener('unhandledrejection', handleUnhandledRejection);
}

function initializeCurrentPage() {
    const path = window.location.pathname;
    
    switch (path) {
        case '/dashboard':
            initializeDashboard();
            break;
        case '/generator':
            initializeGenerator();
            break;
        case '/history':
            initializeHistory();
            break;
    }
}

/**
 * =============================================================================
 * GESTION DES TOASTS ET NOTIFICATIONS
 * =============================================================================
 */

function showToast(message, type = 'info', duration = DashboardConfig.toastDuration) {
    // Créer le conteneur de toasts s'il n'existe pas
    let toastContainer = document.getElementById('toastContainer');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toastContainer';
        toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
        toastContainer.style.zIndex = '9999';
        document.body.appendChild(toastContainer);
    }
    
    const toastId = 'toast-' + Date.now();
    const iconMap = {
        success: 'fa-check-circle',
        error: 'fa-exclamation-triangle',
        warning: 'fa-exclamation-triangle',
        info: 'fa-info-circle'
    };
    
    const colorMap = {
        success: 'text-success',
        error: 'text-danger',
        warning: 'text-warning',
        info: 'text-info'
    };
    
    const toastHtml = `
        <div id="${toastId}" class="toast align-items-center border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body d-flex align-items-center">
                    <i class="fas ${iconMap[type]} ${colorMap[type]} me-2"></i>
                    ${message}
                </div>
                <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHtml);
    
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        delay: duration
    });
    
    toast.show();
    
    // Nettoyer après fermeture
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

/**
 * =============================================================================
 * GESTION DU LOADING
 * =============================================================================
 */

function showLoading(message = 'Chargement...') {
    AppState.isLoading = true;
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        const messageEl = overlay.querySelector('p');
        if (messageEl) {
            messageEl.textContent = message;
        }
        overlay.classList.remove('d-none');
    }
}

function hideLoading() {
    AppState.isLoading = false;
    const overlay = document.getElementById('loadingOverlay');
    if (overlay) {
        overlay.classList.add('d-none');
    }
}

/**
 * =============================================================================
 * DASHBOARD PAGE
 * =============================================================================
 */

function initializeDashboard() {
    // Auto-refresh des stats toutes les 30 secondes
    setInterval(refreshDashboardStats, 30000);
    
    // Initialiser le refresh des générations actives
    initializeActiveGenerationsRefresh();
}

function refreshDashboardStats() {
    if (AppState.isLoading) return;
    
    fetch(`${DashboardConfig.apiBaseUrl}/stats`)
        .then(response => response.json())
        .then(data => {
            if (!data.error) {
                updateStatsCards(data);
            }
        })
        .catch(error => {
            console.error('Erreur refresh stats:', error);
        });
}

function updateStatsCards(stats) {
    const elements = {
        total: document.querySelector('.stat-card-primary .stat-number'),
        completed: document.querySelector('.stat-card-success .stat-number'),
        generating: document.querySelector('.stat-card-warning .stat-number'),
        error: document.querySelector('.stat-card-danger .stat-number')
    };
    
    Object.keys(elements).forEach(key => {
        if (elements[key] && stats[key] !== undefined) {
            animateNumber(elements[key], parseInt(elements[key].textContent) || 0, stats[key]);
        }
    });
}

function animateNumber(element, from, to) {
    const duration = 1000;
    const steps = 20;
    const stepValue = (to - from) / steps;
    let current = from;
    let step = 0;
    
    const timer = setInterval(() => {
        step++;
        current += stepValue;
        
        if (step >= steps) {
            element.textContent = to;
            clearInterval(timer);
        } else {
            element.textContent = Math.round(current);
        }
    }, duration / steps);
}

function initializeActiveGenerationsRefresh() {
    const activeItems = document.querySelectorAll('.active-generation-item');
    
    if (activeItems.length > 0) {
        const refreshInterval = setInterval(() => {
            refreshActiveGenerations();
            
            // Arrêter le refresh si plus d'éléments actifs
            if (document.querySelectorAll('.active-generation-item').length === 0) {
                clearInterval(refreshInterval);
            }
        }, 5000);
    }
}

function refreshActiveGenerations() {
    const activeItems = document.querySelectorAll('.active-generation-item');
    
    activeItems.forEach(item => {
        const generationId = item.dataset.generationId;
        
        fetch(`${DashboardConfig.apiBaseUrl}/generation/${generationId}/status`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'completed' || data.status === 'error') {
                    // Recharger la page pour mettre à jour l'affichage
                    setTimeout(() => location.reload(), 1000);
                } else if (data.progress !== undefined) {
                    updateProgressBar(item, data.progress);
                }
            })
            .catch(error => console.error('Erreur refresh génération:', error));
    });
}

function updateProgressBar(container, progress) {
    const progressBar = container.querySelector('.progress-bar');
    if (progressBar) {
        const percentage = Math.round(progress * 100);
        progressBar.style.width = percentage + '%';
        progressBar.setAttribute('aria-valuenow', percentage);
        progressBar.textContent = percentage + '%';
    }
}

/**
 * =============================================================================
 * GENERATOR PAGE
 * =============================================================================
 */

function initializeGenerator() {
    const form = document.getElementById('generationForm');
    const promptTextarea = document.getElementById('prompt');
    const charCount = document.getElementById('charCount');
    
    if (form && promptTextarea && charCount) {
        // Compteur de caractères
        promptTextarea.addEventListener('input', function() {
            updateCharacterCount(this, charCount);
        });
        
        // Soumission du formulaire
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            startGeneration();
        });
        
        // Auto-save du prompt
        promptTextarea.addEventListener('input', debounce(() => {
            localStorage.setItem('draft_prompt', promptTextarea.value);
        }, 1000));
        
        // Restaurer le brouillon
        const draftPrompt = localStorage.getItem('draft_prompt');
        if (draftPrompt && !promptTextarea.value) {
            promptTextarea.value = draftPrompt;
            updateCharacterCount(promptTextarea, charCount);
        }
    }
}

function updateCharacterCount(textarea, counterElement) {
    const count = textarea.value.length;
    counterElement.textContent = count.toLocaleString();
    
    const parent = counterElement.parentElement;
    if (count > 50000) {
        parent.classList.add('text-danger');
        textarea.classList.add('is-invalid');
    } else if (count > 40000) {
        parent.classList.remove('text-danger');
        parent.classList.add('text-warning');
        textarea.classList.remove('is-invalid');
    } else {
        parent.classList.remove('text-danger', 'text-warning');
        textarea.classList.remove('is-invalid');
    }
}

function startGeneration() {
    // Vérifier s'il y a déjà une génération en cours
    if (AppState.isLoading || AppState.activeStreams.size > 0) {
        showToast('Une génération est déjà en cours', 'warning');
        return;
    }
    
    const prompt = document.getElementById('prompt').value.trim();
    
    if (!prompt) {
        showToast('Veuillez entrer un prompt', 'error');
        return;
    }
    
    if (prompt.length > 50000) {
        showToast('Le prompt est trop long (maximum 50,000 caractères)', 'error');
        return;
    }
    
    // Marquer comme en cours de chargement
    AppState.isLoading = true;
    
    // Désactiver le bouton et afficher le chargement
    const generateBtn = document.getElementById('generateBtn');
    setGenerationButtonState(generateBtn, 'loading');
    
    // Afficher la section résultats
    showResultsSection();
    
    const startTime = Date.now();
    
    // Lancer la génération
    fetch(`${DashboardConfig.apiBaseUrl}/generate`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            prompt: prompt,
            model: document.getElementById('model')?.value || 'claude-sonnet-4-20250514',
            temperature: parseFloat(document.getElementById('temperature')?.value || '1.0')
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status} ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        console.log('Génération créée:', data.generation_id);
        
        // Démarrer le streaming avec un petit délai pour éviter les conflits
        setTimeout(() => {
            startGenerationStreaming(data.generation_id, startTime);
        }, 100);
        
        // Supprimer le brouillon
        localStorage.removeItem('draft_prompt');
    })
    .catch(error => {
        console.error('Erreur génération:', error);
        let errorMessage = 'Erreur de communication avec le serveur';
        if (error.message) {
            errorMessage = error.message;
        }
        showToast(errorMessage, 'error');
        resetGenerationState();
    });
}

function setGenerationButtonState(button, state) {
    const states = {
        normal: {
            disabled: false,
            html: '<i class="fas fa-magic me-2"></i>Générer avec Claude AI'
        },
        loading: {
            disabled: true,
            html: '<i class="fas fa-spinner fa-spin me-2"></i>Génération...'
        }
    };
    
    if (states[state]) {
        button.disabled = states[state].disabled;
        button.innerHTML = states[state].html;
    }
}

function showResultsSection() {
    const resultsSection = document.getElementById('resultsSection');
    const progressSection = document.getElementById('progressSection');
    const resultContent = document.getElementById('resultContent');
    const resultInfo = document.getElementById('resultInfo');
    
    if (resultsSection) {
        resultsSection.style.display = 'block';
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    if (progressSection) progressSection.style.display = 'block';
    if (resultContent) {
        resultContent.textContent = ''; // Vider le contenu précédent
        resultContent.style.whiteSpace = 'pre-wrap'; // Préserver les espaces et sauts de ligne
        resultContent.style.wordWrap = 'break-word'; // Permettre la coupure des mots longs
    }
    if (resultInfo) resultInfo.style.display = 'none';
}

function startGenerationStreaming(generationId, startTime) {
    // Vérifier si un streaming existe déjà pour cet ID
    if (AppState.activeStreams.has(generationId)) {
        console.log('Streaming déjà actif pour:', generationId);
        return; // Éviter les doublons
    }
    
    console.log('Démarrage nouveau streaming pour:', generationId);
    const eventSource = new EventSource(`${DashboardConfig.apiBaseUrl}/generation/${generationId}/stream`);
    AppState.activeStreams.set(generationId, eventSource);
    
    let lastContentLength = 0;
    
    eventSource.onmessage = function(event) {
        try {
            console.log('Message streaming reçu:', event.data);
            const data = JSON.parse(event.data);
            
            if (data.error) {
                console.error('Erreur streaming:', data.error);
                handleStreamingError(data.error);
                eventSource.close();
                AppState.activeStreams.delete(generationId);
                resetGenerationState();
                return;
            }

            // Mise à jour du contenu en temps réel
            if (data.content || data.chunk) {
                const content = data.content || data.chunk;
                updateStreamingContent(content);
            }

            // Mise à jour de la progression
            if (data.progress !== undefined) {
                updateProgress(data.progress);
            }

            // Statut de génération
            if (data.status) {
                handleGenerationStatus(data.status, generationId, startTime);
            }
            
            // Si on reçoit directement un statut dans les données
            if (data.status === 'completed' || data.status === 'error') {
                handleGenerationStatus(data.status, generationId, startTime);
            }

        } catch (error) {
            console.error('Erreur parsing streaming:', error, 'Raw data:', event.data);
        }
    };

    eventSource.onerror = function(event) {
        console.error('Erreur EventSource:', event);
        eventSource.close();
        AppState.activeStreams.delete(generationId);
        handleStreamingError('Connexion streaming interrompue');
    };

    eventSource.onopen = function(event) {
        console.log('Connexion streaming établie pour:', generationId);
    };
}

function updateStreamingContent(content) {
    const resultContent = document.getElementById('resultContent');
    if (resultContent) {
        // Conserver le contenu existant et ajouter le nouveau
        const currentContent = resultContent.textContent || '';
        resultContent.textContent = currentContent + content;
        
        // Auto-scroll vers le bas
        resultContent.scrollTop = resultContent.scrollHeight;
        
        // Ajouter un effet visuel pour montrer l'ajout de contenu
        resultContent.style.backgroundColor = '#f8f9fa';
        setTimeout(() => {
            resultContent.style.backgroundColor = '';
        }, 100);
    }
}

function updateProgress(progress) {
    const progressBar = document.querySelector('#progressSection .progress-bar');
    const progressText = document.querySelector('#progressSection .progress-text');
    
    if (progressBar) {
        const percentage = Math.round(progress * 100);
        progressBar.style.width = Math.max(5, percentage) + '%';
        progressBar.setAttribute('aria-valuenow', percentage);
    }
    
    if (progressText) {
        progressText.textContent = `Progression: ${Math.round(progress * 100)}%`;
    }
}

function handleGenerationStatus(status, generationId, startTime) {
    if (status === 'completed') {
        console.log('Génération terminée:', generationId);
        
        // Finaliser l'interface
        const progressBar = document.querySelector('#progressSection .progress-bar');
        if (progressBar) progressBar.style.width = '100%';
        
        const progressText = document.querySelector('#progressSection .progress-text');
        if (progressText) progressText.textContent = 'Génération terminée avec succès';
        
        // Afficher les informations finales
        showGenerationInfo(generationId, startTime);
        
        // Nettoyer les streams
        if (AppState.activeStreams.has(generationId)) {
            const stream = AppState.activeStreams.get(generationId);
            if (stream) {
                stream.close();
            }
            AppState.activeStreams.delete(generationId);
            console.log('Stream fermé pour:', generationId);
        }
        
        resetGenerationState();
        loadDashboardStats();
        showToast('Génération terminée avec succès!', 'success');
        
    } else if (status === 'error') {
        console.error('Erreur de génération:', generationId);
        handleStreamingError('La génération a échoué');
        resetGenerationState();
    }
}

function handleStreamingError(errorMessage) {
    const resultContent = document.getElementById('resultContent');
    if (resultContent) {
        resultContent.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                ${errorMessage}
                <button class="btn btn-sm btn-outline-danger ms-2" onclick="location.reload()">
                    Recharger la page
                </button>
            </div>
        `;
    }
    showToast(errorMessage, 'error');
}

function showGenerationInfo(generationId, startTime) {
    const duration = ((Date.now() - startTime) / 1000).toFixed(1);
    const resultInfo = document.getElementById('resultInfo');
    
    if (resultInfo) {
        resultInfo.innerHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <span class="text-muted">
                    <i class="fas fa-clock me-1"></i>
                    Durée: ${duration}s
                </span>
                <div class="btn-group btn-group-sm">
                    <button class="btn btn-outline-primary" onclick="copyResult()">
                        <i class="fas fa-copy me-1"></i>Copier
                    </button>
                    <button class="btn btn-outline-success" onclick="newGeneration()">
                        <i class="fas fa-plus me-1"></i>Nouveau
                    </button>
                </div>
            </div>
        `;
        resultInfo.style.display = 'block';
    }
}

function resetGenerationState() {
    AppState.isLoading = false;
    
    const generateBtn = document.getElementById('generateBtn');
    if (generateBtn) {
        setGenerationButtonState(generateBtn, 'normal');
    }
    
    // Nettoyer tous les streams actifs en cas d'erreur
    AppState.activeStreams.forEach((stream, id) => {
        if (stream) {
            stream.close();
        }
    });
    AppState.activeStreams.clear();
}

function copyResult() {
    const resultContent = document.getElementById('resultContent');
    if (resultContent) {
        navigator.clipboard.writeText(resultContent.textContent)
            .then(() => showToast('Contenu copié!', 'success'))
            .catch(() => showToast('Erreur lors de la copie', 'error'));
    }
}

function newGeneration() {
    const promptTextarea = document.getElementById('prompt');
    if (promptTextarea) {
        promptTextarea.value = '';
        promptTextarea.focus();
    }
    
    const resultsSection = document.getElementById('resultsSection');
    if (resultsSection) {
        resultsSection.style.display = 'none';
    }
}

// Version modifiée de la fonction pour compatibilité
function startGenerationStreaming_old(generationId, startTime) {
    // Arrêter tout streaming existant
    if (AppState.activeStreams.has(generationId)) {
        AppState.activeStreams.get(generationId).close();
    }
    
    const eventSource = new EventSource(`${DashboardConfig.apiBaseUrl}/generation/${generationId}/stream`);
    AppState.activeStreams.set(generationId, eventSource);
    
    let lastContentLength = 0;
    
    eventSource.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            if (data.content) {
                appendGenerationContent(data.content);
                lastContentLength += data.content.length;
            }
            
            if (data.status) {
                updateGenerationProgress(data.status);
                
                if (data.status.status === 'completed') {
                    completeGeneration(data.status, startTime, generationId);
                } else if (data.status.status === 'error') {
                    handleGenerationError(data.status.error_message || 'Erreur inconnue', generationId);
                }
            }
            
        } catch (error) {
            console.error('Erreur parsing stream:', error);
        }
    };
    
    eventSource.onerror = function(event) {
        console.error('Erreur EventSource:', event);
        eventSource.close();
        AppState.activeStreams.delete(generationId);
        
        // Fallback: polling pour récupérer le résultat
        setTimeout(() => pollForGenerationResult(generationId, startTime), 2000);
    };
    
    // Timeout de sécurité
    setTimeout(() => {
        if (AppState.activeStreams.has(generationId)) {
            eventSource.close();
            AppState.activeStreams.delete(generationId);
            handleGenerationError('Timeout: La génération a pris trop de temps', generationId);
        }
    }, DashboardConfig.streamTimeout);
}

function appendGenerationContent(content) {
    const resultContent = document.getElementById('resultContent');
    if (!resultContent) return;
    
    // Convertir le markdown en HTML basique
    const htmlContent = content
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/^# (.*$)/gm, '<h1>$1</h1>')
        .replace(/^## (.*$)/gm, '<h2>$1</h2>')
        .replace(/^### (.*$)/gm, '<h3>$1</h3>');
    
    resultContent.innerHTML += htmlContent;
    
    // Scroll vers le bas avec animation fluide
    resultContent.scrollTop = resultContent.scrollHeight;
}

function updateGenerationProgress(status) {
    const progress = Math.round((status.progress || 0) * 100);
    const progressBar = document.querySelector('#progressSection .progress-bar');
    const progressPercentage = document.querySelector('.progress-percentage');
    
    if (progressBar) {
        progressBar.style.width = progress + '%';
        progressBar.setAttribute('aria-valuenow', progress);
        
        if (progress > 10) {
            progressBar.classList.remove('progress-bar-striped', 'progress-bar-animated');
        }
    }
    
    if (progressPercentage) {
        progressPercentage.textContent = progress + '%';
    }
}

function completeGeneration(status, startTime, generationId) {
    // Fermer le stream
    if (AppState.activeStreams.has(generationId)) {
        AppState.activeStreams.get(generationId).close();
        AppState.activeStreams.delete(generationId);
    }
    
    // Masquer la progression
    const progressSection = document.getElementById('progressSection');
    if (progressSection) progressSection.style.display = 'none';
    
    // Afficher les infos
    const duration = Math.round((Date.now() - startTime) / 1000);
    updateResultInfo(duration, status.token_count, status.model_used);
    
    // Réactiver le bouton
    resetGenerationState();
    
    // Sauvegarder l'ID pour les actions
    window.currentGenerationId = generationId;
    
    showToast('Génération terminée avec succès!', 'success');
}

function handleGenerationError(errorMessage, generationId) {
    // Fermer le stream
    if (AppState.activeStreams.has(generationId)) {
        AppState.activeStreams.get(generationId).close();
        AppState.activeStreams.delete(generationId);
    }
    
    const progressSection = document.getElementById('progressSection');
    const resultContent = document.getElementById('resultContent');
    
    if (progressSection) progressSection.style.display = 'none';
    
    if (resultContent) {
        resultContent.innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Erreur lors de la génération:</strong><br>
                ${errorMessage}
            </div>
        `;
    }
    
    resetGenerationState();
    showToast('Erreur lors de la génération', 'error');
}

function updateResultInfo(duration, tokenCount, modelUsed) {
    const elements = {
        duration: document.getElementById('duration'),
        tokenCount: document.getElementById('tokenCount'),
        modelUsed: document.getElementById('modelUsed'),
        resultInfo: document.getElementById('resultInfo')
    };
    
    if (elements.duration) elements.duration.textContent = duration + 's';
    if (elements.tokenCount) elements.tokenCount.textContent = (tokenCount || 0).toLocaleString();
    if (elements.modelUsed) elements.modelUsed.textContent = modelUsed || 'Claude Sonnet 4';
    if (elements.resultInfo) elements.resultInfo.style.display = 'block';
}

function resetGenerationState() {
    const generateBtn = document.getElementById('generateBtn');
    if (generateBtn) {
        setGenerationButtonState(generateBtn, 'normal');
    }
}

function pollForGenerationResult(generationId, startTime) {
    fetch(`${DashboardConfig.apiBaseUrl}/generation/${generationId}/status`)
        .then(response => response.json())
        .then(data => {
            if (data.status === 'completed') {
                const resultContent = document.getElementById('resultContent');
                if (resultContent) {
                    resultContent.innerHTML = data.response.replace(/\n/g, '<br>');
                }
                completeGeneration(data, startTime, generationId);
            } else if (data.status === 'error') {
                handleGenerationError(data.error_message || 'Erreur inconnue', generationId);
            } else if (data.status === 'generating') {
                // Continuer le polling
                setTimeout(() => pollForGenerationResult(generationId, startTime), DashboardConfig.pollInterval);
            }
        })
        .catch(error => {
            console.error('Erreur polling:', error);
            handleGenerationError('Erreur de communication avec le serveur', generationId);
        });
}

// Actions sur les résultats
function copyResult() {
    const resultContent = document.getElementById('resultContent');
    if (!resultContent) return;
    
    const text = resultContent.innerText || resultContent.textContent;
    
    navigator.clipboard.writeText(text).then(() => {
        showToast('Résultat copié dans le presse-papiers', 'success');
    }).catch(err => {
        console.error('Erreur copie:', err);
        showToast('Erreur lors de la copie', 'error');
    });
}

function downloadResult() {
    const generationId = window.currentGenerationId;
    if (!generationId) {
        showToast('Aucun résultat à télécharger', 'error');
        return;
    }
    
    fetch(`${DashboardConfig.apiBaseUrl}/generation/${generationId}`)
        .then(response => response.json())
        .then(data => {
            const content = `Prompt: ${data.prompt}\n\n---\n\nRéponse:\n${data.response}`;
            downloadTextFile(content, `claude_generation_${generationId}.txt`);
            showToast('Fichier téléchargé', 'success');
        })
        .catch(error => {
            console.error('Erreur téléchargement:', error);
            showToast('Erreur lors du téléchargement', 'error');
        });
}

/**
 * =============================================================================
 * HISTORY PAGE
 * =============================================================================
 */

function initializeHistory() {
    const searchInput = document.getElementById('searchInput');
    const statusFilter = document.getElementById('statusFilter');
    
    if (searchInput) {
        searchInput.addEventListener('input', debounce(filterHistory, 300));
    }
    
    if (statusFilter) {
        statusFilter.addEventListener('change', filterHistory);
    }
    
    // Animation d'entrée pour les cartes
    const cards = document.querySelectorAll('.history-card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('card-animate');
        }, index * 50);
    });
}

function filterHistory() {
    const searchInput = document.getElementById('searchInput');
    const statusFilter = document.getElementById('statusFilter');
    
    if (!searchInput || !statusFilter) return;
    
    const searchTerm = searchInput.value.toLowerCase();
    const statusValue = statusFilter.value;
    const cards = document.querySelectorAll('.history-card');
    
    let visibleCount = 0;
    
    cards.forEach(card => {
        const prompt = card.dataset.prompt || '';
        const response = card.dataset.response || '';
        const status = card.dataset.status || '';
        
        const matchesSearch = !searchTerm || 
                            prompt.includes(searchTerm) || 
                            response.includes(searchTerm);
        
        const matchesStatus = !statusValue || status === statusValue;
        
        if (matchesSearch && matchesStatus) {
            card.style.display = 'block';
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });
    
    // Afficher un message si aucun résultat
    toggleEmptyState(visibleCount === 0);
}

function toggleEmptyState(show) {
    let emptyState = document.getElementById('searchEmptyState');
    
    if (show && !emptyState) {
        emptyState = document.createElement('div');
        emptyState.id = 'searchEmptyState';
        emptyState.className = 'text-center py-5';
        emptyState.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-search text-muted"></i>
                <h5 class="mt-3">Aucun résultat trouvé</h5>
                <p class="text-muted">Essayez de modifier vos critères de recherche</p>
                <button class="btn btn-outline-secondary" onclick="clearFilters()">
                    <i class="fas fa-times me-1"></i>Effacer les filtres
                </button>
            </div>
        `;
        document.getElementById('historyGrid').parentNode.appendChild(emptyState);
    } else if (!show && emptyState) {
        emptyState.remove();
    }
}

function clearFilters() {
    const searchInput = document.getElementById('searchInput');
    const statusFilter = document.getElementById('statusFilter');
    
    if (searchInput) searchInput.value = '';
    if (statusFilter) statusFilter.value = '';
    
    filterHistory();
}

// Actions sur l'historique
function viewGeneration(generationId) {
    showLoading('Chargement des détails...');
    
    fetch(`${DashboardConfig.apiBaseUrl}/generation/${generationId}`)
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            
            displayGenerationModal(data);
        })
        .catch(error => {
            console.error('Erreur:', error);
            showToast('Erreur lors du chargement des détails', 'error');
        })
        .finally(() => {
            hideLoading();
        });
}

function displayGenerationModal(data) {
    window.currentModalGeneration = data;
    
    const modalContent = document.getElementById('modalContent');
    if (!modalContent) return;
    
    modalContent.innerHTML = `
        <div class="generation-details">
            <div class="mb-4">
                <h6 class="fw-bold text-primary">
                    <i class="fas fa-edit me-2"></i>Prompt:
                </h6>
                <div class="p-3 bg-light rounded">
                    ${escapeHtml(data.prompt).replace(/\n/g, '<br>')}
                </div>
            </div>
            
            ${data.status === 'completed' ? `
                <div class="mb-4">
                    <h6 class="fw-bold text-success">
                        <i class="fas fa-check-circle me-2"></i>Réponse:
                    </h6>
                    <div class="p-3 bg-light rounded result-content" style="max-height: 400px; overflow-y: auto;">
                        ${escapeHtml(data.response).replace(/\n/g, '<br>')}
                    </div>
                </div>
                
                <div class="row text-center">
                    <div class="col-md-4">
                        <div class="p-3 border rounded">
                            <i class="fas fa-coins text-warning mb-2"></i>
                            <div><strong>${(data.token_count || 0).toLocaleString()}</strong></div>
                            <small class="text-muted">Tokens</small>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="p-3 border rounded">
                            <i class="fas fa-robot text-info mb-2"></i>
                            <div><strong>${data.model_used || 'Claude Sonnet 4'}</strong></div>
                            <small class="text-muted">Modèle</small>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="p-3 border rounded">
                            <i class="fas fa-clock text-secondary mb-2"></i>
                            <div><strong>${formatDate(data.completed_at || data.timestamp)}</strong></div>
                            <small class="text-muted">Terminé</small>
                        </div>
                    </div>
                </div>
            ` : `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Erreur:</strong> ${escapeHtml(data.error_message || 'Erreur inconnue')}
                </div>
            `}
        </div>
    `;
    
    const modal = new bootstrap.Modal(document.getElementById('generationModal'));
    modal.show();
}

function copyGeneration(generationId) {
    fetch(`${DashboardConfig.apiBaseUrl}/generation/${generationId}`)
        .then(response => response.json())
        .then(data => {
            const text = data.status === 'completed' ? data.response : data.prompt;
            return navigator.clipboard.writeText(text);
        })
        .then(() => {
            showToast('Contenu copié dans le presse-papiers', 'success');
        })
        .catch(error => {
            console.error('Erreur:', error);
            showToast('Erreur lors de la copie', 'error');
        });
}

// Fonction d'exportation multi-format
async function exportGeneration(generationId, format) {
    try {
        // Afficher un indicateur de chargement
        const formatLabels = {
            'txt': 'TXT',
            'md': 'Markdown',
            'html': 'HTML',
            'json': 'JSON',
            'pdf': 'PDF'
        };
        
        showToast(`Préparation de l'export ${formatLabels[format]}...`, 'info');
        
        // Créer l'URL de téléchargement
        const downloadUrl = `/api/generation/${generationId}/export/${format}`;
        
        // Méthode robuste de téléchargement avec fetch
        const response = await fetch(downloadUrl);
        
        if (!response.ok) {
            throw new Error(`Erreur HTTP: ${response.status}`);
        }
        
        // Obtenir le blob du fichier
        const blob = await response.blob();
        
        // Créer l'URL du blob
        const blobUrl = window.URL.createObjectURL(blob);
        
        // Créer un lien de téléchargement
        const downloadLink = document.createElement('a');
        downloadLink.href = blobUrl;
        downloadLink.download = `generation_${generationId.substring(0, 8)}.${format}`;
        downloadLink.style.display = 'none';
        
        // Forcer le téléchargement avec attributs supplémentaires
        downloadLink.setAttribute('target', '_blank');
        downloadLink.setAttribute('rel', 'noopener noreferrer');
        
        document.body.appendChild(downloadLink);
        
        // Méthode de téléchargement robuste
        if (downloadLink.click) {
            downloadLink.click();
        } else {
            // Fallback pour navigateurs plus anciens
            const clickEvent = new MouseEvent('click', {
                view: window,
                bubbles: true,
                cancelable: false
            });
            downloadLink.dispatchEvent(clickEvent);
        }
        
        document.body.removeChild(downloadLink);
        
        // Nettoyer l'URL du blob
        setTimeout(() => {
            window.URL.revokeObjectURL(blobUrl);
        }, 1000);
        
        // Message de succès avec option alternative
        showToast(`Fichier ${formatLabels[format]} téléchargé !`, 'success');
        
        // Si le téléchargement automatique échoue, ouvrir dans un nouvel onglet
        setTimeout(() => {
            // Vérifier si le téléchargement a bien fonctionné en testant si le blob est encore accessible
            fetch(downloadUrl, { method: 'HEAD' })
                .then(response => {
                    if (response.ok) {
                        console.log('Téléchargement PDF configuré avec succès');
                    }
                })
                .catch(error => {
                    console.log('Fallback: ouverture en nouvel onglet');
                    window.open(downloadUrl, '_blank');
                });
        }, 2000);
        
    } catch (error) {
        console.error('Erreur export:', error);
        showToast(`Erreur lors de l'export ${format}: ${error.message}`, 'error');
    }
}

function downloadGeneration(generationId) {
    fetch(`${DashboardConfig.apiBaseUrl}/generation/${generationId}`)
        .then(response => response.json())
        .then(data => {
            const content = `Prompt: ${data.prompt}\n\n---\n\nRéponse:\n${data.response || 'Erreur: ' + (data.error_message || 'Inconnue')}`;
            downloadTextFile(content, `claude_generation_${generationId}.txt`);
            showToast('Fichier téléchargé', 'success');
        })
        .catch(error => {
            console.error('Erreur:', error);
            showToast('Erreur lors du téléchargement', 'error');
        });
}

function retryGeneration(prompt) {
    sessionStorage.setItem('retryPrompt', prompt);
    window.location.href = '/generator';
}

function copyModalContent() {
    const data = window.currentModalGeneration;
    if (!data) return;
    
    const text = data.status === 'completed' ? data.response : data.prompt;
    
    navigator.clipboard.writeText(text).then(() => {
        showToast('Contenu copié', 'success');
    }).catch(err => {
        console.error('Erreur copie modal:', err);
        showToast('Erreur lors de la copie', 'error');
    });
}

function downloadModalContent() {
    const data = window.currentModalGeneration;
    if (!data) return;
    
    const content = `Prompt: ${data.prompt}\n\n---\n\nRéponse:\n${data.response || 'Erreur: ' + (data.error_message || 'Inconnue')}`;
    downloadTextFile(content, `claude_generation_${data.id}.txt`);
    showToast('Fichier téléchargé', 'success');
}

/**
 * =============================================================================
 * FONCTIONS UTILITAIRES
 * =============================================================================
 */

function handleRetryPrompt() {
    const retryPrompt = sessionStorage.getItem('retryPrompt');
    if (retryPrompt && window.location.pathname === '/generator') {
        const promptTextarea = document.getElementById('prompt');
        if (promptTextarea) {
            promptTextarea.value = retryPrompt;
            const charCount = document.getElementById('charCount');
            if (charCount) {
                updateCharacterCount(promptTextarea, charCount);
            }
            promptTextarea.focus();
        }
        sessionStorage.removeItem('retryPrompt');
        showToast('Prompt restauré pour régénération', 'info');
    }
}

function downloadTextFile(content, filename) {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 1) return 'À l\'instant';
    if (diffMins < 60) return `Il y a ${diffMins}min`;
    if (diffHours < 24) return `Il y a ${diffHours}h`;
    if (diffDays < 7) return `Il y a ${diffDays}j`;
    
    return date.toLocaleDateString('fr-FR', {
        day: 'numeric',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Continuer une conversation depuis l'historique
function continueConversation(generationId) {
    if (!generationId) {
        showNotification('Erreur: ID de génération manquant', 'error');
        return;
    }
    
    // Rediriger vers le générateur avec le paramètre de continuation
    window.location.href = `/generator?continue=${generationId}`;
}

function handleResize() {
    // Ajuster la hauteur des éléments si nécessaire
    const resultContent = document.getElementById('resultContent');
    if (resultContent && window.innerWidth < 768) {
        resultContent.style.maxHeight = '250px';
    } else if (resultContent) {
        resultContent.style.maxHeight = '500px';
    }
}

function handleVisibilityChange() {
    if (document.hidden) {
        // Mettre en pause les streams actifs pour économiser la bande passante
        AppState.activeStreams.forEach(stream => {
            // Note: EventSource ne peut pas être mis en pause, mais on peut le noter
            console.log('Page cachée, stream actif détecté');
        });
    } else {
        // Reprendre les activités si nécessaire
        console.log('Page visible');
    }
}

function handleGlobalError(event) {
    console.error('Erreur globale:', event.error);
    showToast('Une erreur inattendue s\'est produite', 'error');
}

function handleUnhandledRejection(event) {
    console.error('Promesse rejetée:', event.reason);
    showToast('Erreur de communication avec le serveur', 'error');
}

// Nettoyage lors du déchargement de la page
window.addEventListener('beforeunload', function() {
    // Fermer tous les streams actifs
    AppState.activeStreams.forEach(stream => {
        stream.close();
    });
    AppState.activeStreams.clear();
});

// Exposer certaines fonctions globalement pour les templates
window.showToast = showToast;
window.showLoading = showLoading;
window.hideLoading = hideLoading;
window.copyResult = copyResult;
window.downloadResult = downloadResult;
window.viewGeneration = viewGeneration;
window.copyGeneration = copyGeneration;
window.downloadGeneration = downloadGeneration;
window.retryGeneration = retryGeneration;
window.copyModalContent = copyModalContent;
window.downloadModalContent = downloadModalContent;
window.clearFilters = clearFilters;
window.refreshStats = refreshDashboardStats;
window.shareGeneration = shareGeneration;

/**
 * =============================================================================
 * FONCTIONS DE PARTAGE
 * =============================================================================
 */

async function shareGeneration(generationId) {
    try {
        showToast('Génération du lien de partage...', 'info');
        
        const response = await fetch(`/api/share/${generationId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (data.status === 'success') {
            // Copier l'URL dans le presse-papiers
            if (navigator.clipboard) {
                try {
                    await navigator.clipboard.writeText(data.share_url);
                    showToast('Lien de partage copié dans le presse-papiers !', 'success');
                } catch (err) {
                    showShareModal(data.share_url);
                }
            } else {
                showShareModal(data.share_url);
            }
        } else {
            showToast('Erreur lors de la génération du lien de partage: ' + data.message, 'error');
        }
    } catch (error) {
        console.error('Erreur partage:', error);
        showToast('Erreur lors de la génération du lien de partage', 'error');
    }
}

function showShareModal(shareUrl) {
    // Créer une modal pour afficher l'URL si le clipboard API n'est pas disponible
    const modalHtml = `
        <div class="modal fade" id="shareModal" tabindex="-1" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-share-alt me-2"></i>Partager la génération
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <p class="mb-3">Copiez ce lien pour partager cette génération :</p>
                        <div class="input-group">
                            <input type="text" class="form-control" id="shareUrlInput" value="${shareUrl}" readonly>
                            <button class="btn btn-outline-primary" type="button" onclick="copyShareUrl()">
                                <i class="fas fa-copy"></i>
                            </button>
                        </div>
                        <div class="mt-3">
                            <small class="text-muted">
                                <i class="fas fa-info-circle me-1"></i>
                                Ce lien permet d'accéder à la génération sans authentification.
                            </small>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fermer</button>
                        <a href="${shareUrl}" target="_blank" class="btn btn-primary">
                            <i class="fas fa-external-link-alt me-1"></i>Ouvrir
                        </a>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Supprimer une modal existante si présente
    const existingModal = document.getElementById('shareModal');
    if (existingModal) {
        existingModal.remove();
    }
    
    // Ajouter la nouvelle modal
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Afficher la modal
    const modal = new bootstrap.Modal(document.getElementById('shareModal'));
    modal.show();
    
    // Sélectionner le texte
    document.getElementById('shareUrlInput').select();
}

function copyShareUrl() {
    const input = document.getElementById('shareUrlInput');
    input.select();
    document.execCommand('copy');
    showToast('Lien copié dans le presse-papiers !', 'success');
}

console.log('AI Playground JavaScript chargé et initialisé');

// Fonction pour initialiser les dropdowns imbriqués sur ordinateur
function initializeDropdownSubmenus() {
    // Pour les écrans desktop, activer les dropdowns au hover
    if (window.innerWidth > 768) {
        document.querySelectorAll('.dropdown-submenu').forEach(function(submenu) {
            submenu.addEventListener('mouseenter', function() {
                const submenuDropdown = this.querySelector('.dropdown-menu');
                if (submenuDropdown) {
                    // Positionner le sous-menu à gauche du menu principal
                    const rect = this.getBoundingClientRect();
                    const parentDropdown = this.closest('.dropdown-menu');
                    const parentRect = parentDropdown.getBoundingClientRect();
                    
                    submenuDropdown.style.position = 'fixed';
                    submenuDropdown.style.top = rect.top + 'px';
                    submenuDropdown.style.left = (parentRect.left - 200) + 'px'; // 200px est la largeur approximative du sous-menu
                    submenuDropdown.style.display = 'block';
                    submenuDropdown.style.zIndex = '1060';
                    submenuDropdown.style.minWidth = '180px';
                    
                    // Si le menu sort de l'écran à gauche, le mettre à droite
                    if (parentRect.left - 200 < 0) {
                        submenuDropdown.style.left = (parentRect.right + 5) + 'px';
                    }
                    
                    // Vérifier si le menu sort de l'écran en bas
                    const submenuRect = submenuDropdown.getBoundingClientRect();
                    if (submenuRect.bottom > window.innerHeight) {
                        submenuDropdown.style.top = (window.innerHeight - submenuRect.height - 10) + 'px';
                    }
                }
            });
            
            submenu.addEventListener('mouseleave', function() {
                const submenuDropdown = this.querySelector('.dropdown-menu');
                if (submenuDropdown) {
                    submenuDropdown.style.display = 'none';
                }
            });
        });
    } else {
        // Pour mobile, ajouter des gestionnaires de clic
        document.querySelectorAll('.dropdown-submenu > a').forEach(function(link) {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                const submenu = this.parentElement;
                const submenuDropdown = submenu.querySelector('.dropdown-menu');
                
                // Fermer les autres sous-menus
                document.querySelectorAll('.dropdown-submenu').forEach(function(otherSubmenu) {
                    if (otherSubmenu !== submenu) {
                        otherSubmenu.classList.remove('show');
                        const otherDropdown = otherSubmenu.querySelector('.dropdown-menu');
                        if (otherDropdown) {
                            otherDropdown.style.display = 'none';
                        }
                    }
                });
                
                // Toggle le sous-menu actuel
                submenu.classList.toggle('show');
                if (submenuDropdown) {
                    submenuDropdown.style.display = submenu.classList.contains('show') ? 'block' : 'none';
                }
            });
        });
    }
}

// Initialiser les dropdowns imbriqués
initializeDropdownSubmenus();

// Fonction pour copier le contenu d'une génération directement
function copyGenerationToClipboard(generationId) {
    fetch(`${DashboardConfig.apiBaseUrl}/generation/${generationId}`)
        .then(response => response.json())
        .then(data => {
            if (data.response) {
                navigator.clipboard.writeText(data.response).then(() => {
                    showToast('Contenu copié dans le presse-papiers !', 'success');
                }).catch(err => {
                    console.error('Erreur copie:', err);
                    showToast('Erreur lors de la copie', 'error');
                });
            }
        })
        .catch(error => {
            console.error('Erreur récupération:', error);
            showToast('Erreur lors de la récupération du contenu', 'error');
        });
}

// Fonction de suppression de génération
async function deleteGeneration(generationId) {
    if (!confirm('Êtes-vous sûr de vouloir supprimer cette génération ? Cette action est irréversible.')) {
        return;
    }
    
    try {
        const response = await fetch(`${DashboardConfig.apiBaseUrl}/generation/${generationId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showToast('Génération supprimée avec succès', 'success');
            
            // Animation de suppression
            const card = document.querySelector(`[data-generation-id="${generationId}"]`);
            if (card) {
                card.style.transition = 'all 0.3s ease';
                card.style.opacity = '0';
                card.style.transform = 'scale(0.9)';
                setTimeout(() => {
                    card.remove();
                }, 300);
            }
            
            // Rafraîchir l'historique si on est sur cette page
            if (window.location.pathname.includes('/history')) {
                setTimeout(() => location.reload(), 1000);
            }
        } else {
            showToast(`Erreur: ${data.error || 'Erreur inconnue'}`, 'error');
        }
    } catch (error) {
        console.error('Erreur suppression:', error);
        showToast('Erreur lors de la suppression', 'error');
    }
}
