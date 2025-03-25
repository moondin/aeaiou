// aeaiou - AI Image Generator

// DOM Elements
const promptInput = document.getElementById('promptInput');
const generateButton = document.getElementById('generateButton');
const loadingIndicator = document.getElementById('loadingIndicator');
const resultContainer = document.getElementById('resultContainer');
const generatedImage = document.getElementById('generatedImage');
const downloadLink = document.getElementById('downloadLink');
const errorMessage = document.getElementById('errorMessage');

// Event Listeners
generateButton.addEventListener('click', generateImage);

// UI Helper Functions
function showLoading() {
    loadingIndicator.style.display = 'flex';
    resultContainer.style.display = 'none';
    hideError();
}

function hideLoading() {
    loadingIndicator.style.display = 'none';
}

function showResult(imageUrl) {
    resultContainer.style.display = 'block';
    generatedImage.src = imageUrl;
    downloadLink.href = imageUrl;
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
}

function hideError() {
    errorMessage.style.display = 'none';
}

// Image Generation using Replicate API (via Replicate hosted API proxy)
async function generateImage() {
    const prompt = promptInput.value.trim();
    
    if (!prompt) {
        showError('Please enter a prompt description.');
        return;
    }
    
    showLoading();
    
    try {
        // Using a third-party proxy service to handle API calls
        // In production, you should replace this with your own secure backend
        const response = await fetch('https://replicate-api-proxy.glitch.me/predictions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                prompt: prompt,
                model: "stability-ai/stable-diffusion:db21e94d2eda158a3bf169282768c2a61aabab93cbdd385669865480734c35ad"
            })
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || 'Failed to connect to the image generation API');
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // For demonstration purposes - normally we would poll the API
        // But this proxy should return the full result
        if (data.output && data.output.length > 0) {
            showResult(data.output[0]);
        } else {
            throw new Error('No image was generated');
        }
        
    } catch (error) {
        console.error('Error generating image:', error);
        showError(error.message || 'An error occurred while generating the image');
    } finally {
        hideLoading();
    }
}
