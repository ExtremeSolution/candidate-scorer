let currentStep = 0;
let thinkingMessages = [
    "Extracting candidate name and contact information...",
    "Analyzing education background and certifications...",
    "Parsing work experience and job progression...",
    "Identifying technical skills and competencies...",
    "Evaluating soft skills and leadership qualities...",
    "Cross-referencing job requirements with candidate profile...",
    "Loading company culture and values framework...",
    "Assessing industry experience and domain knowledge...",
    "Calculating skills match percentage...",
    "Evaluating culture fit based on company profile...",
    "Analyzing geographic and remote work preferences...",
    "Determining growth stage compatibility...",
    "Generating personalized interview questions...",
    "Compiling strengths and potential concerns...",
    "Finalizing recommendation and scoring..."
];

document.getElementById('analyzeForm').onsubmit = async function(e) {
    e.preventDefault();
    
    // Show loading and hide results
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';
    
    // Disable submit button
    const submitBtn = document.getElementById('submitBtn');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Analyzing...';
    
    // Reset progress steps
    resetProgressSteps();
    
    // Start progress animation
    startProgressAnimation();
    
    // Start thinking stream after 2 seconds
    setTimeout(() => {
        startThinkingStream();
    }, 2000);
    
    const formData = new FormData(this);
    
    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        // Complete all steps quickly
        completeAllSteps();
        
        // Show final thinking message
        addThinkingMessage("Analysis complete! Generating results...");
        
        setTimeout(() => {
            document.getElementById('loading').style.display = 'none';
            document.getElementById('results').style.display = 'block';
            
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.textContent = 'Analyze Candidate';
            
            if (data.success) {
                document.getElementById('resultContent').innerHTML = formatResults(data);
            } else {
                document.getElementById('resultContent').innerHTML = 
                    `<div class="error">Error: ${data.error}</div>`;
            }
        }, 1000);
        
    } catch (error) {
        completeAllSteps();
        addThinkingMessage("Error occurred during analysis.");
        
        setTimeout(() => {
            document.getElementById('loading').style.display = 'none';
            
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.textContent = 'Analyze Candidate';
            
            document.getElementById('resultContent').innerHTML = 
                `<div class="error">Error: ${error.message}</div>`;
            document.getElementById('results').style.display = 'block';
        }, 1000);
    }
};

function resetProgressSteps() {
    currentStep = 0;
    for (let i = 1; i <= 5; i++) {
        const step = document.getElementById(`step${i}`);
        step.className = 'step';
    }
    
    // Hide thinking stream
    document.getElementById('thinkingStream').style.display = 'none';
    document.getElementById('streamContent').innerHTML = '';
}

function startProgressAnimation() {
    const stepDuration = 3000; // 3 seconds per step
    
    function activateNextStep() {
        if (currentStep < 5) {
            currentStep++;
            
            // Mark previous step as completed
            if (currentStep > 1) {
                document.getElementById(`step${currentStep - 1}`).className = 'step completed';
            }
            
            // Mark current step as active
            document.getElementById(`step${currentStep}`).className = 'step active';
            
            // Continue to next step
            setTimeout(activateNextStep, stepDuration);
        }
    }
    
    // Start first step
    setTimeout(activateNextStep, 500);
}

function startThinkingStream() {
    document.getElementById('thinkingStream').style.display = 'block';
    let messageIndex = 0;
    
    function addNextMessage() {
        if (messageIndex < thinkingMessages.length) {
            addThinkingMessage(thinkingMessages[messageIndex]);
            messageIndex++;
            
            // Random delay between 1-3 seconds
            const delay = Math.random() * 2000 + 1000;
            setTimeout(addNextMessage, delay);
        }
    }
    
    addNextMessage();
}

function addThinkingMessage(message) {
    const streamContent = document.getElementById('streamContent');
    streamContent.innerHTML += message + '\n';
    
    // Auto-scroll to bottom
    streamContent.parentNode.scrollTop = streamContent.parentNode.scrollHeight;
}

function completeAllSteps() {
    // Mark all steps as completed
    for (let i = 1; i <= 5; i++) {
        document.getElementById(`step${i}`).className = 'step completed';
    }
}

function sanitizeHTML(str) {
    const temp = document.createElement('div');
    temp.textContent = str;
    return temp.innerHTML;
}

function formatResults(data) {
    try {
        // Data is already parsed JSON from the backend
        const resume = data.resume_analysis;
        const scoring = data.scoring;
        const enhanced = data.enhanced_analysis;
        const companyInfo = data.company_summary;
        
        let result = `
            <div class="result-header">
                <div class="candidate-info">
                    <h3 class="candidate-name">👤 ${sanitizeHTML(resume.name || 'Unknown Candidate')}</h3>
                    <div class="candidate-contact">
                        ${resume.email ? `<span class="contact-item">📧 ${sanitizeHTML(resume.email)}</span>` : ''}
                        ${resume.phone ? `<span class="contact-item">📱 ${sanitizeHTML(resume.phone)}</span>` : ''}
                        ${resume.experience_years ? `<span class="contact-item">⏰ ${sanitizeHTML(resume.experience_years)} years experience</span>` : ''}
                    </div>
                </div>
                <div class="score">Overall Score: ${sanitizeHTML(scoring.overall_score)}/10</div>
            </div>
            
            <div class="recommendation-badge ${sanitizeHTML(scoring.recommendation?.toLowerCase().replace(' ', '-')) || 'unknown'}">
                <strong>${getRecommendationIcon(scoring.recommendation)} ${sanitizeHTML(scoring.recommendation || 'Unknown')}</strong>
            </div>
            
            <div class="analysis-type">
                ${enhanced ? '<span class="enhanced-badge">✅ Enhanced Analysis with Company Context</span>' : '<span class="basic-badge">⚠️ Basic Analysis (No Company Context)</span>'}
            </div>
        `;
        
        // Company Summary (if enhanced analysis)
        if (enhanced && companyInfo) {
            result += `
                <div class="info-card company-context">
                    <h4 class="card-title">🏢 Company Context</h4>
                    <div class="company-grid">
                        <div class="company-item">
                            <span class="label">Industry:</span>
                            <span class="value">${sanitizeHTML(companyInfo.industry)}</span>
                        </div>
                        <div class="company-item">
                            <span class="label">Company Stage:</span>
                            <span class="value">${sanitizeHTML(companyInfo.stage)}</span>
                        </div>
                        <div class="company-item">
                            <span class="label">Work Environment:</span>
                            <span class="value">${sanitizeHTML(companyInfo.culture)}</span>
                        </div>
                        <div class="company-item">
                            <span class="label">Mission:</span>
                            <span class="value">${sanitizeHTML(companyInfo.mission)}</span>
                        </div>
                    </div>
                </div>
            `;
        }
        
        // Score Breakdown with visual bars
        result += `
            <div class="info-card score-breakdown">
                <h4 class="card-title">📊 Score Breakdown</h4>
                <div class="scores-grid">
                    ${createScoreBar('Skills Match', scoring.skills_match, '🎯')}
                    ${createScoreBar('Experience Match', scoring.experience_match, '💼')}
                    ${createScoreBar('Culture Fit', scoring.culture_fit, '🤝')}
        `;
        
        // Enhanced scoring dimensions (if available)
        if (enhanced) {
            if (scoring.industry_fit) result += createScoreBar('Industry Fit', scoring.industry_fit, '🏭');
            if (scoring.geographic_fit) result += createScoreBar('Geographic Fit', scoring.geographic_fit, '🌍');
            if (scoring.growth_stage_fit) result += createScoreBar('Growth Stage Fit', scoring.growth_stage_fit, '📈');
            if (scoring.values_alignment) result += createScoreBar('Values Alignment', scoring.values_alignment, '⭐');
        }
        result += `
                </div>
            </div>
        `;
        
        // Candidate Profile
        result += `
            <div class="info-card candidate-profile">
                <h4 class="card-title">👨‍💻 Candidate Profile</h4>
                <div class="profile-grid">
                    <div class="profile-item">
                        <span class="label">Experience Level:</span>
                        <span class="value">${sanitizeHTML(resume.experience_level || 'Not specified')}</span>
                    </div>
                    <div class="profile-item full-width">
                        <span class="label">Key Skills:</span>
                        <div class="skills-tags">
                            ${Array.isArray(resume.skills) ? resume.skills.map(skill => `<span class="skill-tag">${sanitizeHTML(skill)}</span>`).join('') : `<span class="skill-tag">${sanitizeHTML(resume.skills || 'Not found')}</span>`}
                        </div>
                    </div>
                    <div class="profile-item full-width">
                        <span class="label">Summary:</span>
                        <span class="value summary-text">${sanitizeHTML(resume.summary || 'Not available')}</span>
                    </div>
                </div>
            </div>
        `;
        
        // Assessment
        result += `
            <div class="info-card assessment">
                <h4 class="card-title">📝 Assessment</h4>
                <div class="assessment-grid">
                    <div class="assessment-section strengths">
                        <h5 class="section-title">✅ Strengths</h5>
                        <ul class="assessment-list">
                            ${Array.isArray(scoring.strengths) ? scoring.strengths.map(item => `<li>${sanitizeHTML(item)}</li>`).join('') : `<li>${sanitizeHTML(scoring.strengths || 'None specified')}</li>`}
                        </ul>
                    </div>
                    <div class="assessment-section concerns">
                        <h5 class="section-title">⚠️ Concerns</h5>
                        <ul class="assessment-list">
                            ${Array.isArray(scoring.concerns) ? scoring.concerns.map(item => `<li>${sanitizeHTML(item)}</li>`).join('') : `<li>${sanitizeHTML(scoring.concerns || 'None specified')}</li>`}
                        </ul>
                    </div>
                    <div class="assessment-section interview">
                        <h5 class="section-title">💬 Interview Focus</h5>
                        <ul class="assessment-list">
                            ${Array.isArray(scoring.interview_focus) ? scoring.interview_focus.map(item => `<li>${sanitizeHTML(item)}</li>`).join('') : `<li>${sanitizeHTML(scoring.interview_focus || 'General discussion')}</li>`}
                        </ul>
                    </div>
        `;
        
        // Enhanced assessment fields (if available)
        if (enhanced) {
            if (scoring.company_fit_highlights && Array.isArray(scoring.company_fit_highlights) && scoring.company_fit_highlights.length > 0) {
                result += `
                    <div class="assessment-section highlights">
                        <h5 class="section-title">🎯 Company Fit Highlights</h5>
                        <ul class="assessment-list">
                            ${scoring.company_fit_highlights.map(item => `<li>${sanitizeHTML(item)}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }
            if (scoring.potential_challenges && Array.isArray(scoring.potential_challenges) && scoring.potential_challenges.length > 0) {
                result += `
                    <div class="assessment-section challenges">
                        <h5 class="section-title">🚧 Potential Challenges</h5>
                        <ul class="assessment-list">
                            ${scoring.potential_challenges.map(item => `<li>${sanitizeHTML(item)}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }
            if (scoring.onboarding_considerations && Array.isArray(scoring.onboarding_considerations) && scoring.onboarding_considerations.length > 0) {
                result += `
                    <div class="assessment-section onboarding">
                        <h5 class="section-title">🚀 Onboarding Considerations</h5>
                        <ul class="assessment-list">
                            ${scoring.onboarding_considerations.map(item => `<li>${sanitizeHTML(item)}</li>`).join('')}
                        </ul>
                    </div>
                `;
            }
        }
        
        result += `
                </div>
            </div>
        `;
        
        // Rationale
        result += `
            <div class="info-card rationale">
                <h4 class="card-title">🧠 AI Rationale</h4>
                <p class="rationale-text">${sanitizeHTML(scoring.rationale || 'Not provided')}</p>
            </div>
        `;
        
        // Job Description Preview
        result += `
            <div class="info-card job-preview">
                <h4 class="card-title">📋 Job Description Preview</h4>
                <div class="job-content">${sanitizeHTML(data.jd_preview)}</div>
            </div>
        `;
        
        return result;
    } catch (e) {
        return `<div class="error">Error displaying results: ${sanitizeHTML(e.message)}</div>`;
    }
}

function createScoreBar(label, score, icon) {
    const percentage = (score / 10) * 100;
    const colorClass = score >= 8 ? 'excellent' : score >= 6 ? 'good' : score >= 4 ? 'fair' : 'poor';
    
    return `
        <div class="score-item">
            <div class="score-label">
                <span class="score-icon">${icon}</span>
                <span class="score-name">${label}</span>
                <span class="score-value">${score}/10</span>
            </div>
            <div class="score-bar">
                <div class="score-fill ${colorClass}" style="width: ${percentage}%"></div>
            </div>
        </div>
    `;
}

function getRecommendationIcon(recommendation) {
    if (!recommendation) return '❓';
    const rec = recommendation.toLowerCase();
    if (rec.includes('strong')) return '🎯';
    if (rec.includes('moderate')) return '⚖️';
    if (rec.includes('weak')) return '⚠️';
    return '📋';
}
