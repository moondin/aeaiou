const express = require('express');
const fetch = require('node-fetch');
const path = require('path');
const fs = require('fs');
require('dotenv').config(); // Add dotenv support
const app = express();
const PORT = process.env.PORT || 3000;

// API key from environment variable
const REPLICATE_API_TOKEN = process.env.REPLICATE_API_TOKEN;

// Middleware
app.use(express.json());
app.use(express.static(path.join(__dirname, '/')));

// API endpoint to handle image generation
app.post('/api/generate', async (req, res) => {
    try {
        const { prompt } = req.body;
        
        // Call Replicate API
        const response = await fetch('https://api.replicate.com/v1/predictions', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Token ${REPLICATE_API_TOKEN}`
            },
            body: JSON.stringify({
                version: "stability-ai/stable-diffusion:db21e94d2eda158a3bf169282768c2a61aabab93cbdd385669865480734c35ad",
                input: { prompt }
            })
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'API request failed');
        }
        
        const prediction = await response.json();
        res.json({ id: prediction.id });
        
    } catch (error) {
        console.error('Error:', error);
        res.status(500).json({ error: error.message });
    }
});

// Endpoint to check prediction status
app.get('/api/prediction/:id', async (req, res) => {
    try {
        const { id } = req.params;
        
        const response = await fetch(`https://api.replicate.com/v1/predictions/${id}`, {
            headers: {
                'Authorization': `Token ${REPLICATE_API_TOKEN}`
            }
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Status check failed');
        }
        
        const prediction = await response.json();
        res.json(prediction);
        
    } catch (error) {
        console.error('Error:', error);
        res.status(500).json({ error: error.message });
    }
});

// Serve the main HTML file
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// Start the server
app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
