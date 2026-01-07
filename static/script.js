// DOM Elements
const menuBtn = document.querySelector('.menu-btn');
const uploadCard = document.getElementById('uploadCard');
const historyCard = document.getElementById('historyCard');
const guideCard = document.getElementById('guideCard');
const uploadSection = document.getElementById('uploadSection');
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const previewSection = document.getElementById('previewSection');
const imagePreview = document.getElementById('imagePreview');
const cancelBtn = document.getElementById('cancelBtn');
const analyzeBtn = document.getElementById('analyzeBtn');
const loading = document.getElementById('loading');
const resultsSection = document.getElementById('resultsSection');
const resultContent = document.getElementById('resultContent');
const newScanBtn = document.getElementById('newScanBtn');

let selectedFile = null;

// Logging helper
function log(...args) {
    if (console && console.debug) console.debug('[App]', ...args);
}

// Menu Button Handler
menuBtn.addEventListener('click', () => {
    menuBtn.classList.toggle('active');
    log('Menu toggled');
});

// Event Listeners
uploadCard.addEventListener('click', () => {
    uploadArea.scrollIntoView({ behavior: 'smooth' });
    log('Upload card clicked');
});

historyCard.addEventListener('click', () => {
    alert('History feature coming soon!');
});

guideCard.addEventListener('click', () => {
    showGuidelines();
});

uploadArea.addEventListener('click', () => {
    fileInput.click();
});

// Drag and drop handlers
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = 'var(--primary-dark)';
    uploadArea.style.background = 'var(--surface)';
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.style.borderColor = 'var(--primary-color)';
    uploadArea.style.background = 'var(--white)';
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.style.borderColor = 'var(--primary-color)';
    uploadArea.style.background = 'var(--white)';
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

cancelBtn.addEventListener('click', () => {
    resetUpload();
});

analyzeBtn.addEventListener('click', () => {
    analyzeScan();
});

newScanBtn.addEventListener('click', () => {
    resetAll();
});

// Functions
function handleFileSelect(file) {
    log('File selected', file.name, file.type, file.size);
    if (!file.type.startsWith('image/')) {
        alert('Please select an image file');
        return;
    }

    if (file.size > 10 * 1024 * 1024) {
        alert('File size must be less than 10MB');
        return;
    }

    selectedFile = file;
    
    const reader = new FileReader();
    reader.onload = (e) => {
        imagePreview.src = e.target.result;
        uploadArea.style.display = 'none';
        previewSection.style.display = 'block';
        log('Preview displayed');
    };
    reader.readAsDataURL(file);
}

function resetUpload() {
    selectedFile = null;
    fileInput.value = '';
    imagePreview.src = '';
    previewSection.style.display = 'none';
    uploadArea.style.display = 'block';
    log('Upload reset');
}

function resetAll() {
    resetUpload();
    uploadSection.style.display = 'block';
    resultsSection.style.display = 'none';
    document.querySelector('.welcome-section').style.display = 'block';
    document.querySelector('.action-cards').style.display = 'grid';
    log('Reset to start');
}

async function analyzeScan() {
    if (!selectedFile) {
        alert('Please select an image first');
        return;
    }

    // Scroll to top, show loading
    window.scrollTo({ top: 0, behavior: 'smooth' });
    previewSection.style.display = 'none';
    loading.style.display = 'block';

    const formData = new FormData();
    formData.append('image', selectedFile);

    try {
        log('Uploading image for analysis', selectedFile.name);
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        log('Server response', data);

        // Hide loading
        loading.style.display = 'none';

        if (data.status === 'success' && data.analysis) {
            displayResults(data.analysis);
        } else {
            alert('Error: ' + (data.error || 'Analysis failed'));
            previewSection.style.display = 'block';
        }
    } catch (error) {
        console.error('Error:', error);
        loading.style.display = 'none';
        alert('An error occurred while analyzing the image');
        previewSection.style.display = 'block';
    }
}

function displayResults(analysis) {
    const confidencePct = (analysis.confidence * 100).toFixed(1);
    const label = analysis.diagnosis || analysis.top_label || `Class ${analysis.top_index}`;

    resultContent.innerHTML = `
        <div class="result-item">
            <div class="result-label">Result</div>
            <div class="result-value">${label}</div>
        </div>
        <div class="result-item">
            <div class="result-label">Confidence</div>
            <div class="result-value">${confidencePct}%</div>
        </div>
    `;

    resultsSection.style.display = 'block';
    log('Displayed results', analysis.top_index, label, analysis.confidence);
}

function showGuidelines() {
    const guidelines = `
📋 Guidelines for Accurate Skin Scan:

1. Lighting: Use natural, bright lighting
2. Distance: Hold camera 6-8 inches away
3. Focus: Ensure the area is clearly visible
4. Background: Use a plain, neutral background
5. Angle: Take photos straight-on, not at an angle
6. Quality: Use high resolution images

⚠️ Important: This tool is for screening purposes only. 
Always consult a healthcare professional for medical advice.
    `;
    
    alert(guidelines);
}

// Smooth scroll behavior
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth'
            });
        }
    });
});
