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

    const sampleProjects = [
        { id: "project1", name: "Hybe_New", url: "https://playground.twelvelabs.io/indexes/67900e1181c61d781369699f" },
        { id: "project2", name: "Talent Show", url: "https://playground.twelvelabs.io/indexes/12345" },
        { id: "project3", name: "Music Videos", url: "https://playground.twelvelabs.io/indexes/67890" }
    ];

    function initializeProjects() {
        while (projectSelect.options.length > 0) {
            projectSelect.remove(0);
        }
        
        const defaultOption = document.createElement('option');
        defaultOption.value = "";
        defaultOption.textContent = "Select a project";
        defaultOption.disabled = true;
        defaultOption.selected = true;
        projectSelect.appendChild(defaultOption);
        
        sampleProjects.forEach(project => {
            const option = document.createElement('option');
            option.value = project.id;
            option.textContent = project.name;
            option.dataset.url = project.url;
            projectSelect.appendChild(option);
        });

        if (sampleProjects.length > 0) {
            projectSelect.value = sampleProjects[0].id;
            updateExternalLink(sampleProjects[0].url);
            
            if (dropdownButton) {
                dropdownButton.textContent = sampleProjects[0].name;
            }
        }
    }

    initializeProjects();

    projectSelect.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        const projectName = selectedOption.textContent;
        const projectUrl = selectedOption.dataset.url;
 
        if (dropdownButton) {
            dropdownButton.textContent = projectName;
        }
 
        updateExternalLink(projectUrl);
    });

    function updateExternalLink(url) {
        if (externalLink) {
            externalLink.href = url || "#";
        }
    }


    suggestionCards.forEach(card => {
        card.addEventListener('click', function() {
            messageInput.value = this.textContent.trim();
            messageInput.focus();
        });
    });

    if (saveApiKeyBtn) {
        saveApiKeyBtn.addEventListener('click', function() {
            const apiKey = apiKeyInput.value.trim();
            if (apiKey) {
                localStorage.setItem('apiKey', apiKey);
                updateApiStatus(true);
                bootstrap.Modal.getInstance(document.getElementById('apiModal')).hide();
                showAlert('API key connected successfully', 'success');
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
            

            showAlert(`Creating project "${projectName}" with video "${videoFile.name}"...`, 'info');

            setTimeout(() => {
                bootstrap.Modal.getInstance(document.getElementById('newProjectModal')).hide();
                
                projectNameInput.value = '';
                videoUploadInput.value = '';
     
                const newProject = {
                    id: `project${Date.now()}`,
                    name: projectName,
                    url: "#"
                };
                
                sampleProjects.push(newProject);
     
                const option = document.createElement('option');
                option.value = newProject.id;
                option.textContent = newProject.name;
                option.dataset.url = newProject.url;
                projectSelect.appendChild(option);
                
        
                projectSelect.value = newProject.id;
        
                if (dropdownButton) {
                    dropdownButton.textContent = newProject.name;
                }
                
                showAlert(`Project "${projectName}" created successfully!`, 'success');
            }, 1500);
        });
    }


    sendButton.addEventListener('click', sendMessage);
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    function sendMessage() {
        const message = messageInput.value.trim();
        if (message) {
            displayUserMessage(message);
          
            setTimeout(() => {
                let response;
                
                if (message.toLowerCase().includes('choreography') || message.toLowerCase().includes('dance')) {
                    response = "I found several synchronized choreography clips from your videos. Here are the top results with timestamps:<br><br>1. 01:24 - 01:53: Group formation change with synchronized arm movements<br>2. 03:12 - 03:42: Mirror dance sequence with perfect timing<br>3. 05:17 - 05:46: Complex synchronized footwork pattern";
                } else if (message.toLowerCase().includes('lighting') || message.toLowerCase().includes('transition')) {
                    response = "I found these notable lighting transitions in your videos:<br><br>1. 02:15 - 02:25: Dramatic shift from cool blue to warm amber<br>2. 04:37 - 04:50: Spotlight effect that gradually expands to full stage lighting<br>3. 07:12 - 07:30: Strobe effect transitioning to soft backlighting";
                } else if (message.toLowerCase().includes('iphone') || message.toLowerCase().includes('camera') || message.toLowerCase().includes('setting')) {
                    response = "I detected these video settings across your uploads:<br><br>1. Main performance: Professional camera setup, 4K resolution, 24fps with shallow depth of field<br>2. Behind the scenes: iPhone 13 Pro footage, 1080p at 60fps<br>3. Interview segments: Canon DSLR with standard 35mm lens, natural lighting setup";
                } else if (message.toLowerCase().includes('rap') || message.toLowerCase().includes('verse')) {
                    response = "I found these memorable rap verses in your videos:<br><br>1. 01:45 - 02:12: Fast-paced verse with complex rhyme patterns<br>2. 04:23 - 04:56: Verse with distinctive flow changes and vocal effects<br>3. 06:32 - 07:01: Emotional delivery with standout wordplay";
                } else if (message.toLowerCase().includes('performance') || message.toLowerCase().includes('standout') || message.toLowerCase().includes('moment')) {
                    response = "These standout performance moments were identified:<br><br>1. 02:34 - 02:52: High-energy dance break with audience reaction<br>2. 05:12 - 05:38: Powerful vocal high note with dramatic staging<br>3. 07:45 - 08:10: Intimate acoustic segment with emotional delivery";
                } else {
                    response = "I've analyzed your video content and can help find specific moments. Try asking me to find choreography sequences, lighting effects, technical details, or standout performances.";
                }
                
                displayBotMessage(response);
                messageInput.value = '';
            }, 1000);
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


    function displayBotMessage(message) {
        if (!searchResults) return;
 
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'card mb-3';
        typingIndicator.style.maxWidth = '80%';
        typingIndicator.innerHTML = `
            <div class="card-body">
                <div class="d-flex">
                    <div class="spinner-grow spinner-grow-sm text-primary me-2" role="status">
                        <span class="visually-hidden">Loading...</span>
                    </div>
                    <div>Jockey is typing...</div>
                </div>
            </div>
        `;
        
        searchResults.appendChild(typingIndicator);
        scrollToBottom();
        
        // Replace typing indicator with actual message after a delay
        setTimeout(() => {
            // Create message element
            const messageEl = document.createElement('div');
            messageEl.className = 'card mb-3';
            messageEl.style.maxWidth = '80%';
            
            messageEl.innerHTML = `
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <strong class="text-success">Jockey</strong>
                        <small class="text-muted">${getCurrentTime()}</small>
                    </div>
                    <div class="card-text mb-0">${message}</div>
                </div>
            `;
            
            // Replace typing indicator with actual message
            searchResults.replaceChild(messageEl, typingIndicator);
            scrollToBottom();
        }, 1000);
    }

    // Function to get current time
    function getCurrentTime() {
        const now = new Date();
        let hours = now.getHours();
        const minutes = now.getMinutes().toString().padStart(2, '0');
        const ampm = hours >= 12 ? 'PM' : 'AM';
        
        hours = hours % 12;
        hours = hours ? hours : 12; // Convert 0 to 12
        
        return `${hours}:${minutes} ${ampm}`;
    }

    // Function to scroll chat to bottom
    function scrollToBottom() {
        const container = searchResults.parentElement;
        container.scrollTop = container.scrollHeight;
    }

    // Function to show alerts
    function showAlert(message, type) {
        if (!alertContainer) return;
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        alertContainer.appendChild(alert);
        
        // Auto dismiss after 5 seconds
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => {
                if (alertContainer.contains(alert)) {
                    alertContainer.removeChild(alert);
                }
            }, 150);
        }, 5000);
    }

    // Function to update API status display
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


    if (searchResults) {
        searchResults.style.minHeight = '300px';
        searchResults.style.maxHeight = '500px';
        searchResults.style.overflowY = 'auto';
        searchResults.style.padding = '1rem';
        searchResults.style.marginBottom = '2rem';  
    }

    const savedApiKey = localStorage.getItem('apiKey');
    if (savedApiKey) {
        updateApiStatus(true);
    }

});