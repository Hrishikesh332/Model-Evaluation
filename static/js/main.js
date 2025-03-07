document.addEventListener('DOMContentLoaded', function() {

  
 
    const suggestionCards = document.querySelectorAll('.suggestion-card');
    const messageInput = document.querySelector('.message-input');
    const apiStatus = document.querySelector('.api-status');
    const saveApiKeyBtn = document.getElementById('saveApiKey');
    const apiKeyInput = document.getElementById('apiKey');
    const sendButton = document.querySelector('.send-button');
    const projectSelect = document.getElementById('projectSelect');
    const createProjectBtn = document.getElementById('createProject');
    const projectNameInput = document.getElementById('projectName');
    const videoUploadInput = document.getElementById('videoUpload');
    const externalLink = document.getElementById('externalLink');
    const alertContainer = document.getElementById('alertContainer');
    const searchResults = document.getElementById('searchResults');
    const dropdownButton = document.querySelector('.btn.btn-light.border span');
    const leftPanel = document.querySelector('.col-lg-6.border-end');
    const rightPanel = document.querySelector('.col-lg-6.border-start');
    const modelSelector = document.querySelector('.form-select[aria-label="Performance filter"]');
    const techModelSelector = document.querySelector('.form-select[aria-label="Technical filter"]');

    const customSelect = document.querySelector('.custom-select');
    const customOptions = document.querySelector('.custom-options');

    if (customSelect && customOptions) {
        // Toggle custom dropdown when clicked
        customSelect.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            customOptions.style.display = customOptions.style.display === 'none' ? 'block' : 'none';
        });
        
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.custom-select-container')) {
                customOptions.style.display = 'none';
            }
        });
    }

    let videoSelectContainer = document.getElementById('videoSelectContainer');
    if (!videoSelectContainer) {
        videoSelectContainer = document.createElement('div');
        videoSelectContainer.id = 'videoSelectContainer';
        videoSelectContainer.className = 'dropdown-menu videoSelectMenu p-2';
        videoSelectContainer.innerHTML = `
            <div class="mb-2">
                <label class="form-label fw-bold mb-2">Select Video:</label>
                <select id="videoSelect" class="form-select"></select>
            </div>
        `;

        
        
        // Append to dropdown menu
        const dropdownMenu = document.querySelector('.dropdown-menu');
        if (dropdownMenu) {
            const hr = document.createElement('hr');
            hr.className = 'dropdown-divider';
            dropdownMenu.appendChild(hr);
            dropdownMenu.appendChild(videoSelectContainer);
        }
    }
    
    const videoSelect = document.getElementById('videoSelect');

    let isApiConnected = false;
    let selectedIndexId = null;
    let selectedVideoId = null;
    let isPublicVideo = false;
    let currentVideos = [];

    const savedApiKey = localStorage.getItem('apiKey');
    if (savedApiKey) {
        connectWithApiKey(savedApiKey);
    } else {
        // Load public indexes by default
        loadPublicIndexes();
    }

    if (saveApiKeyBtn) {
        saveApiKeyBtn.addEventListener('click', function() {
            const apiKey = apiKeyInput.value.trim();
            if (apiKey) {
                connectWithApiKey(apiKey);
            } else {
                showAlert('Please enter a valid API key', 'warning');
            }
        });
    }

    suggestionCards.forEach(card => {
        card.addEventListener('click', function() {
            if (!selectedVideoId) {
                showAlert('Please select a video first', 'warning');
                return;
            }
            messageInput.value = this.textContent.trim();
            messageInput.focus();
        });
    });

    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    if (videoSelect) {
        videoSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            if (selectedOption && selectedOption.value) {
                const videoId = selectedOption.value;
                const videoName = selectedOption.textContent;
                
                selectedVideoId = videoId;
                selectVideo(selectedIndexId, videoId, videoName, isPublicVideo);
            }
        });
    }

    if (projectSelect) {
        projectSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            if (selectedOption && selectedOption.value) {
                const indexName = selectedOption.textContent;
                const indexUrl = selectedOption.dataset.url;
                const indexId = selectedOption.value;
                
                if (dropdownButton) {
                    dropdownButton.textContent = indexName;
                }
                
                if (externalLink) {
                    externalLink.href = indexUrl || "#";
                }

                selectedIndexId = indexId;
                selectedVideoId = null;
                
                loadVideosForIndex(indexId);
            }
        });
    }

    if (createProjectBtn) {
        createProjectBtn.addEventListener('click', function() {
            const projectName = projectNameInput.value.trim();
            const videoFile = videoUploadInput.files[0];
            
            if (!projectName) {
                showAlert('Please enter a project name', 'warning');
                return;
            }
            
            if (!videoFile) {
                showAlert('Please select a video file', 'warning');
                return;
            }
            
            showAlert('Note: Project creation requires API access. Please connect your TwelveLabs API key.', 'info');

            setTimeout(() => {
                const modal = bootstrap.Modal.getInstance(document.getElementById('newProjectModal'));
                if (modal) modal.hide();
                
                projectNameInput.value = '';
                videoUploadInput.value = '';
            }, 2000);
        });
    }

    // Connect with API key
    function connectWithApiKey(apiKey) {
        if (saveApiKeyBtn) {
            saveApiKeyBtn.disabled = true;
            saveApiKeyBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Connecting...';
        }

        fetch('/api/connect', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                type: 'twelvelabs',
                api_key: apiKey
            })
        })
        .then(response => response.json())
        .then(data => {
            if (saveApiKeyBtn) {
                saveApiKeyBtn.disabled = false;
                saveApiKeyBtn.textContent = 'Connect';
            }

            if (data.status === 'success') {
                localStorage.setItem('apiKey', apiKey);
                updateApiStatus(true);
                isApiConnected = true;
                showAlert('API key connected successfully', 'success');

                if (data.indexes && data.indexes.length > 0) {
                    updateIndexesDropdown(data.indexes, false);
                } else {
                    showAlert('No indexes found in your account. Loading public indexes.', 'info');
                    loadPublicIndexes();
                }
                
                const modal = bootstrap.Modal.getInstance(document.getElementById('apiModal'));
                if (modal) modal.hide();
            } else {
                showAlert(data.message || 'Failed to connect API key', 'danger');
                loadPublicIndexes(); 
            }
        })
        .catch(error => {

            if (saveApiKeyBtn) {
                saveApiKeyBtn.disabled = false;
                saveApiKeyBtn.textContent = 'Connect';
            }

            console.error('Error connecting API:', error);
            showAlert('Error connecting to the server', 'danger');
            loadPublicIndexes();
        });
    }

    // Load public indexes
    function loadPublicIndexes() {
        fetch('/api/indexes')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success' && data.indexes) {
                    updateIndexesDropdown(data.indexes, true);
                    isPublicVideo = true;
                } else {
                    showAlert('Error loading indexes', 'danger');
                }
            })
            .catch(error => {
                console.error('Error loading public indexes:', error);
                showAlert('Error loading public indexes', 'danger');
            });
    }


    function updateIndexesDropdown(indexes, isPublic) {
        while (projectSelect.options.length > 0) {
            projectSelect.remove(0);
        }
        
        const defaultOption = document.createElement('option');
        defaultOption.value = "";
        defaultOption.textContent = "Select an index";
        defaultOption.disabled = true;
        defaultOption.selected = true;
        projectSelect.appendChild(defaultOption);
        
        indexes.forEach(index => {
            const option = document.createElement('option');
            option.value = index.id;
            option.textContent = index.name;
            option.dataset.url = index.url;
            projectSelect.appendChild(option);
        });
        
        // Select first index by default
        if (indexes.length > 0) {
            projectSelect.value = indexes[0].id;
            selectedIndexId = indexes[0].id;
            isPublicVideo = isPublic;
            
            // Update dropdown button text
            if (dropdownButton) {
                dropdownButton.textContent = indexes[0].name;
            }
            
            // Update external link
            if (externalLink) {
                externalLink.href = indexes[0].url || "#";
            }
            
            // Load videos for selected index
            loadVideosForIndex(indexes[0].id);
        }
    }

    
    // Load videos for an index
    function loadVideosForIndex(indexId) {
        // Update standard select dropdown
        while (videoSelect.options.length > 0) {
            videoSelect.remove(0);
        }
        
        const loadingOption = document.createElement('option');
        loadingOption.textContent = "Loading videos...";
        loadingOption.disabled = true;
        loadingOption.selected = true;
        videoSelect.appendChild(loadingOption);
        
        // Update custom dropdown UI
        const customSelectText = document.querySelector('.selected-text');
        if (customSelectText) {
            customSelectText.textContent = "Loading videos...";
        }
        
        const customOptions = document.querySelector('.custom-options');
        if (customOptions) {
            customOptions.innerHTML = '';
        }
    
        fetch(`/api/indexes/${indexId}/videos`)
            .then(response => response.json())
            .then(data => {
                // Clear loading options
                while (videoSelect.options.length > 0) {
                    videoSelect.remove(0);
                }
    
                if (data.status === 'success' && data.videos && data.videos.length > 0) {
                    // Store videos for reference
                    currentVideos = data.videos;
                    
                    // 1. Update standard select dropdown
                    data.videos.forEach(video => {
                        const option = document.createElement('option');
                        option.value = video.id;
                        option.textContent = video.name;
                        option.dataset.thumbnail = video.thumbnailUrl;
                        videoSelect.appendChild(option);
                    });
                    
                    // 2. Update custom dropdown UI
                    if (customOptions) {
                        customOptions.innerHTML = '';
                        
                        data.videos.forEach(video => {
                            const option = document.createElement('div');
                            option.className = 'custom-option';
                            option.dataset.value = video.id;
                            
                            option.innerHTML = `
                                <div class="d-flex align-items-center">
                                <img src="${video.thumbnailUrl}" alt="${video.name}" class="video-thumbnail-small me-2">
                                    <span>${video.name}</span>
                                </div>
                            `;
                            
                            option.addEventListener('click', function() {
                                // Update the custom select display
                                if (customSelectText) {
                                    customSelectText.innerHTML = `
                                        <div class="d-flex align-items-center">
                                            <img src="${video.thumbnailUrl}" alt="${video.name}" class="video-thumbnail-small me-2">
                                            <span>${video.name}</span>
                                        </div>
                                    `;
                                }
                                
                                // Hide the options
                                customOptions.style.display = 'none';
                                
                                // Select the video in the standard dropdown (for state management)
                                if (videoSelect) {
                                    videoSelect.value = video.id;
                                }
                                
                                // Call the selectVideo function
                                selectVideo(indexId, video.id, video.name, isPublicVideo);
                            });
                            
                            customOptions.appendChild(option);
                        });
                    }
                    
                    // Select first video by default
                    if (data.videos.length > 0) {
                        videoSelect.value = data.videos[0].id;
                        
                        // Also update custom dropdown display
                        if (customSelectText && data.videos[0].thumbnailUrl) {
                            customSelectText.innerHTML = `
                                <div class="d-flex align-items-center">
                                    <img src="${data.videos[0].thumbnailUrl}" alt="${data.videos[0].name}" class="video-thumbnail-small me-2">
                                    <span>${data.videos[0].name}</span>
                                </div>
                            `;
                        }
                        
                        selectVideo(indexId, data.videos[0].id, data.videos[0].name, isPublicVideo);
                    }
                } else {
                    // No videos found
                    const noVideosOption = document.createElement('option');
                    noVideosOption.textContent = "No videos found";
                    noVideosOption.disabled = true;
                    noVideosOption.selected = true;
                    videoSelect.appendChild(noVideosOption);
                    
                    if (customSelectText) {
                        customSelectText.textContent = "No videos found";
                    }
                    
                    showAlert('No videos found in this index', 'warning');
                }
            })
            .catch(error => {
                console.error('Error loading videos:', error);
                // Clear dropdowns and show error
                while (videoSelect.options.length > 0) {
                    videoSelect.remove(0);
                }
                
                const errorOption = document.createElement('option');
                errorOption.textContent = "Error loading videos";
                errorOption.disabled = true;
                errorOption.selected = true;
                videoSelect.appendChild(errorOption);
                
                if (customSelectText) {
                    customSelectText.textContent = "Error loading videos";
                }
                
                showAlert('Error loading videos for this index', 'danger');
            });
    }



    function selectVideo(indexId, videoId, videoName, isPublic) {
        if (videoSelect) {
            videoSelect.disabled = true;
        }

        if (messageInput) {
            messageInput.disabled = true;
            messageInput.placeholder = "Loading video...";
        }
        
        showAlert(`Selecting video: ${videoName}...`, 'info');
        
        fetch('/api/video/select', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                index_id: indexId,
                video_id: videoId
            })
        })
        .then(response => response.json())
        .then(data => {
            if (videoSelect) {
                videoSelect.disabled = false;
            }
            
            if (data.status === 'success') {
                isPublicVideo = isPublic;
                selectedVideoId = videoId;
                
                showAlert(`Video '${videoName}' selected successfully`, 'success');
                
                suggestionCards.forEach(card => {
                    card.classList.add('active');
                });
                
                if (messageInput) {
                    messageInput.disabled = false;
                    messageInput.placeholder = "Ask about this video...";
                }
                
                if (sendButton) {
                    sendButton.disabled = false;
                }
            } else {
                showAlert(data.message || 'Failed to select video', 'danger');
            }
        })
        .catch(error => {
            if (videoSelect) {
                videoSelect.disabled = false;
            }
            
            console.error('Error selecting video:', error);
            showAlert('Error selecting video', 'danger');
        });
    }


    function displayLoadingInPanel(panelId) {
        const panel = document.getElementById(panelId);
        if (!panel) return null;
        
        const loadingIndicator = document.createElement('div');
        loadingIndicator.className = 'card mb-3 loading-indicator';
        loadingIndicator.style.maxWidth = '100%';
        loadingIndicator.innerHTML = `
            <div class="card-body">
                <div class="d-flex">
                    <div class="spinner-grow spinner-grow-sm text-primary me-2" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <div>Analyzing...</div>
                </div>
            </div>
        `;
        
        panel.appendChild(loadingIndicator);
        return loadingIndicator;
    }
    

    function displayUserMessageInPanel(panelId, message) {
        const panel = document.getElementById(panelId);
        if (!panel) return;
    
        const messageEl = document.createElement('div');
        messageEl.className = 'card mb-3 ms-auto';
        messageEl.style.maxWidth = '80%';
        
        messageEl.innerHTML = `
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <strong class="text-primary">You</strong>
                    <small class="text-muted">${getCurrentTime()}</small>
                </div>
                <p class="card-text mb-0">${message}</p>
            </div>
        `;
        
        panel.appendChild(messageEl);
    }
    
    function replaceLoadingWithResponse(panelId, loadingElement, message, sourceName) {
        const panel = document.getElementById(panelId);
        if (!panel || !loadingElement) return;
        
        const messageEl = document.createElement('div');
        messageEl.className = 'card mb-3';
        messageEl.style.maxWidth = '100%';
        
        const formattedMessage = renderMarkdown(message);
        
        messageEl.innerHTML = `
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <strong class="text-success">${sourceName}</strong>
                    <small class="text-muted">${getCurrentTime()}</small>
                </div>
                <div class="card-text mb-0">${formattedMessage}</div>
            </div>
        `;
        
        if (loadingElement.parentNode === panel) {
            panel.replaceChild(messageEl, loadingElement);
        } else {
            panel.appendChild(messageEl);
        }
    }
    

    function formatErrorMessage(message) {
        if (message.startsWith('Error') || message.startsWith('ERROR')) {
            return `<div class="alert alert-danger">${message}</div>`;
        }
        return message;
    }

    function renderMarkdown(text) {
        if (!text) return '';
        
        // If the text contains HTML tags from formatErrorMessage, return it as-is
        if (text.includes('<div class="alert alert-danger">')) {
            return text;
        }
    
        // Otherwise, process it as normal markdown
        text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
        text = text.replace(/^### (.*?)$/gm, '<h5>$1</h5>');
        text = text.replace(/^## (.*?)$/gm, '<h4>$1</h4>');
        text = text.replace(/^# (.*?)$/gm, '<h3>$1</h3>');
        text = text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
        text = text.replace(/\n/g, '<br>');
    
        text = text.replace(/^\* (.*?)$/gm, '<li>$1</li>');
        text = text.replace(/^(\d+)\. (.*?)$/gm, '<li>$2</li>');
        
        text = text.replace(/(\d{1,2}:\d{2}(?::\d{2})?(?:-\d{1,2}:\d{2}(?::\d{2})?)?)/g, '<span class="badge bg-secondary">$1</span>');
        
        return text;
    }


    function sendMessage() {
        const message = messageInput.value.trim();
        if (!message) return;
        
        if (!selectedVideoId) {
            showAlert('Please select a video first', 'warning');
            return;
        }
    
        clearSuggestionsAndShowResults();
        
        // Display user message in the main chat area
        displayUserMessage(message);
        
        // Display user message in both left and right panels
        displayUserMessageInPanel('leftPanelResults', message);
        displayUserMessageInPanel('rightPanelResults', message);
        
        const selectedModel = modelSelector.value === '1' ? 'gpt4o' : 'gemini';
    
        // Add a temporary loading message in the main chat area
        const loadingMessage = displayBotMessage("Analyzing your request...", true);
        
        messageInput.disabled = true;
        sendButton.disabled = true;
        
        // Create loading indicators in each panel
        const leftPanelLoading = displayLoadingInPanel('leftPanelResults');
        const rightPanelLoading = displayLoadingInPanel('rightPanelResults');
        
        // Send query to server
        fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                query: message,
                model: selectedModel
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Remove the main loading message
            if (loadingMessage && loadingMessage.parentNode === searchResults) {
                searchResults.removeChild(loadingMessage);
            }
            
            messageInput.disabled = false;
            sendButton.disabled = false;
            messageInput.focus();
            
            // Handle API responses
            if (data.status === 'success' || data.status === 'partial') {
                // Process pegasus response
                if (data.responses.pegasus) {
                    let responseText = data.responses.pegasus;
                    
                    // Check if there was an error with Pegasus
                    if (data.errors && data.errors.pegasus) {
                        responseText = formatErrorMessage(responseText);
                    }
                    
                    replaceLoadingWithResponse('rightPanelResults', rightPanelLoading, responseText, 'Pegasus Model');
                }
                
                // Process the selected model response
                if (data.responses[selectedModel]) {
                    const modelName = selectedModel === 'gemini' ? 'Gemini Model' : 'GPT-4o Model';
                    let responseText = data.responses[selectedModel];
                    
                    // Check if there was an error with the selected model
                    if (data.errors && data.errors[selectedModel]) {
                        responseText = formatErrorMessage(responseText);
                    }
                    
                    replaceLoadingWithResponse('leftPanelResults', leftPanelLoading, responseText, modelName);
                }
                
                // Show status message
                let statusMessage = "Analysis complete. Check both panels for detailed results.";
                if (data.status === 'partial') {
                    statusMessage = "Analysis partially complete. Some models encountered errors.";
                }
                
                displayBotMessage(statusMessage);
            } else {
                // Handle complete failure
                const leftPanel = document.getElementById('leftPanelResults');
                const rightPanel = document.getElementById('rightPanelResults');
                
                if (leftPanel && leftPanelLoading && leftPanelLoading.parentNode === leftPanel) {
                    leftPanel.removeChild(leftPanelLoading);
                }
                
                if (rightPanel && rightPanelLoading && rightPanelLoading.parentNode === rightPanel) {
                    rightPanel.removeChild(rightPanelLoading);
                }
                
                showAlert(data.message || 'Failed to analyze video', 'danger');
                displayBotMessage("Sorry, I encountered an error while analyzing your request.");
            }
        })
        .catch(error => {
            console.error('Error sending message:', error);
            
            // Remove all loading indicators
            if (loadingMessage && loadingMessage.parentNode === searchResults) {
                searchResults.removeChild(loadingMessage);
            }
            
            const leftPanel = document.getElementById('leftPanelResults');
            const rightPanel = document.getElementById('rightPanelResults');
            
            if (leftPanel && leftPanelLoading && leftPanelLoading.parentNode === leftPanel) {
                leftPanel.removeChild(leftPanelLoading);
            }
            
            if (rightPanel && rightPanelLoading && rightPanelLoading.parentNode === rightPanel) {
                rightPanel.removeChild(rightPanelLoading);
            }
            
            messageInput.disabled = false;
            sendButton.disabled = false;
            
            showAlert('Error communicating with the server: ' + error.message, 'danger');
            displayBotMessage("Sorry, I encountered an error while analyzing your request. Please check the server logs for details.");
        });
        
        messageInput.value = '';
    }



    // Function to clear suggestions and show results panels
    function clearSuggestionsAndShowResults() {
        if (leftPanel) {
            const leftSuggestions = leftPanel.querySelectorAll('.suggestion-card');
            const leftTitle = leftPanel.querySelector('.section-title');
            const leftSelect = leftPanel.querySelector('.form-select');
            const leftHr = leftPanel.querySelector('hr');
            
            // Save title and select
            if (leftTitle && leftSelect) {
                leftPanel.innerHTML = '';
                
                const headerDiv = document.createElement('div');
                headerDiv.className = 'd-flex align-items-center gap-2 justify-content-between';
                headerDiv.appendChild(leftTitle);
                
                const selectDiv = document.createElement('div');
                selectDiv.appendChild(leftSelect);
                
                headerDiv.appendChild(selectDiv);
                leftPanel.appendChild(headerDiv);
                
                const newHr = document.createElement('hr');
                leftPanel.appendChild(newHr);
                
                const resultsDiv = document.createElement('div');
                resultsDiv.id = 'leftPanelResults';
                resultsDiv.className = 'panel-results';
                leftPanel.appendChild(resultsDiv);
            }
        }
        
        // Clear suggestions in right panel
        if (rightPanel) {
            const rightSuggestions = rightPanel.querySelectorAll('.suggestion-card');
            const rightTitle = rightPanel.querySelector('.section-title');
            const rightSelect = rightPanel.querySelector('.form-select');
            const rightHr = rightPanel.querySelector('hr');
            
            if (rightTitle && rightSelect) {
                rightPanel.innerHTML = '';
                
                const headerDiv = document.createElement('div');
                headerDiv.className = 'd-flex align-items-center gap-2 justify-content-between';
                headerDiv.appendChild(rightTitle);
                
                const selectDiv = document.createElement('div');
                selectDiv.appendChild(rightSelect);
                
                headerDiv.appendChild(selectDiv);
                rightPanel.appendChild(headerDiv);
                
                const newHr = document.createElement('hr');
                rightPanel.appendChild(newHr);
                
                const resultsDiv = document.createElement('div');
                resultsDiv.id = 'rightPanelResults';
                resultsDiv.className = 'panel-results';
                rightPanel.appendChild(resultsDiv);
            }
        }
    }


    function displayUserMessage(message) {
        if (!searchResults) return;

        const messageEl = document.createElement('div');
        messageEl.className = 'card mb-3 ms-auto';
        messageEl.style.maxWidth = '80%';
        
        messageEl.innerHTML = `
            <div class="card-body">
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <strong class="text-primary">You</strong>
                    <small class="text-muted">${getCurrentTime()}</small>
                </div>
                <p class="card-text mb-0">${message}</p>
            </div>
        `;
        
        searchResults.appendChild(messageEl);
        scrollToBottom();
    }

    function displayBotMessage(message, isLoading = false) {
        if (!searchResults) return;

        const messageEl = document.createElement('div');
        messageEl.className = 'card mb-3';
        messageEl.style.maxWidth = '80%';
        
        if (isLoading) {
            messageEl.innerHTML = `
                <div class="card-body">
                    <div class="d-flex">
                        <div class="spinner-grow spinner-grow-sm text-primary me-2" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                        <div>Model is analyzing...</div>
                    </div>
                </div>
            `;
        } else {
            messageEl.innerHTML = `
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <strong class="text-success">Model Eval</strong>
                        <small class="text-muted">${getCurrentTime()}</small>
                    </div>
                    <div class="card-text mb-0">${message}</div>
                </div>
            `;
        }
        
        searchResults.appendChild(messageEl);
        scrollToBottom();
        
        return messageEl;
    }

    function scrollToBottom() {
        if (searchResults) {
            const container = searchResults.parentElement;
            if (container) {
                container.scrollTop = container.scrollHeight;
            }
        }
    }

    function showAlert(message, type) {
        if (!alertContainer) return;
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        alertContainer.appendChild(alert);

        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => {
                if (alertContainer.contains(alert)) {
                    alertContainer.removeChild(alert);
                }
            }, 150);
        }, 5000);
    }

 
    function updateApiStatus(connected) {
        if (!apiStatus) return;
        
        if (connected) {
            apiStatus.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="me-1">
                    <path d="M12 2a10 10 0 0 1 10 10c0 5.523-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2z"/>
                    <path d="M12 6v6l4 2"/>
                </svg>
                API Key: Connected
            `;
            apiStatus.style.color = '#28a745';
        } else {
            apiStatus.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M12 2a10 10 0 0 1 10 10c0 5.523-4.477 10-10 10S2 17.523 2 12 6.477 2 12 2z"/>
                    <path d="M12 6v6l4 2"/>
                </svg>
                API Key: Not Connected
            `;
            apiStatus.style.color = '#6c757d';
        }
    }

    function getCurrentTime() {
        const now = new Date();
        let hours = now.getHours();
        const minutes = now.getMinutes().toString().padStart(2, '0');
        const ampm = hours >= 12 ? 'PM' : 'AM';
        
        hours = hours % 12;
        hours = hours ? hours : 12; 
        
        return `${hours}:${minutes} ${ampm}`;
    }

    function checkModelAvailability() {
        fetch('/api/models')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {

                    if (!data.models.gemini && !data.models.gpt4o) {
                        if (modelSelector) {
                            modelSelector.disabled = true;
                        }
                        showAlert('Additional AI models (Gemini, GPT-4o) are not available. Using Pegasus only.', 'info');
                    } else if (!data.models.gpt4o) {
                        // If GPT-4o is not available, disable that option
                        if (modelSelector && modelSelector.options[1]) {
                            modelSelector.options[1].disabled = true;
                        }
                    }
                }
            })
            .catch(error => {
                console.error('Error checking model availability:', error);
            });
    }

    // disable message input and button until video is selected
    if (messageInput) {
        messageInput.disabled = true;
        messageInput.placeholder = "Select a video first...";
    }
    
    if (sendButton) {
        sendButton.disabled = true;
    }

    checkModelAvailability();
});