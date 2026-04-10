const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');

const app = express();
const PORT = 5174;
const SCRIPT_PATH = '/Users/a12/projects/tts/대본.txt';

app.use(cors());
app.use(express.json());

app.post('/api/sync', (req, res) => {
    const { content } = req.body;
    if (!content) {
        return res.status(400).json({ error: 'No content provided' });
    }

    try {
        fs.writeFileSync(SCRIPT_PATH, content, 'utf8');
        console.log(`✅ Synced to: ${SCRIPT_PATH}`);
        res.json({ success: true, path: SCRIPT_PATH });
    } catch (error) {
        console.error('❌ Sync Error:', error);
        res.status(500).json({ error: 'Failed to write to file' });
    }
});

app.listen(PORT, () => {
    console.log(`🚀 PromptBox Bridge running at http://localhost:${PORT}`);
});
