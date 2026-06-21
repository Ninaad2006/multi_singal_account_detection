let currentPlatform = 'instagram';

// Try to auto-detect username from active tab
chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
    // Safety check - make sure tab and URL exist
    if (!tabs || tabs.length === 0 || !tabs[0] || !tabs[0].url) {
        return;
    }

    const url = tabs[0].url;
    let username = null;
    let platform = null;

    try {
        // Instagram: instagram.com/username
        const igMatch = url.match(/instagram\.com\/([^/?]+)/);
        if (igMatch && igMatch[1] && !['p', 'explore', 'reels', 'stories', 'direct'].includes(igMatch[1])) {
            username = igMatch[1];
            platform = 'instagram';
        }

        // X/Twitter: x.com/username or twitter.com/username
        const xMatch = url.match(/(?:x|twitter)\.com\/([^/?]+)/);
        if (xMatch && xMatch[1] && !['home', 'explore', 'notifications', 'messages', 'i', 'settings'].includes(xMatch[1])) {
            username = xMatch[1];
            platform = 'x';
        }

        if (username && platform) {
            document.getElementById('auto-detect').style.display = 'block';
            document.getElementById('detected-username').textContent = '@' + username;
            document.getElementById('username').value = username;
            setPlatform(platform);
            analyzeDetected();
        }
    } catch (e) {
        console.log('URL detection error:', e);
    }
});

function setPlatform(platform) {
    currentPlatform = platform;
    document.getElementById('btn-ig').className = 'platform-btn' + (platform === 'instagram' ? ' active-instagram' : '');
    document.getElementById('btn-x').className = 'platform-btn' + (platform === 'x' ? ' active-x' : '');
    chrome.storage.local.set({ platform: platform });
}

function analyzeDetected() {
    const username = document.getElementById('username').value.trim();
    if (username) analyze();
}

async function analyze() {
    const username = document.getElementById('username').value.trim();
    if (!username) { alert('Please enter a username!'); return; }

    document.getElementById('loading').style.display = 'block';
    document.getElementById('result').innerHTML = '';

    try {
        const response = await fetch('http://127.0.0.1:5004/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: username, platform: currentPlatform })
        });

        const result = await response.json();
        document.getElementById('loading').style.display = 'none';

        if (result.error) {
            document.getElementById('result').innerHTML =
                '<div class="result warning">⚠️ ' + result.error + '</div>';
            return;
        }

        const label = result.prediction === 'fake' ? 'Fake Account' : 'Real Account';
        const riskColor = result.risk_color || 'var(--gray-dark)';
        const riskScore = result.risk_score || 0;
        const spamScore = result.spam ? result.spam.spam_score : 0;
        const spamColor = spamScore >= 60 ? 'var(--red-card)' : spamScore >= 30 ? 'var(--yellow)' : 'var(--green)';
        const predictionClass = result.prediction === 'fake' ? 'fake' : (result.prediction === 'real' ? 'real' : 'warning');

        let profilePic = result.data.profile_pic_url ?
            `<img class="result-avatar" src="http://127.0.0.1:5004/proxy-image?url=${encodeURIComponent(result.data.profile_pic_url)}">`
            : '<div class="result-avatar" style="background:var(--gray);display:flex;align-items:center;justify-content:center;font-size:20px;">👤</div>';

        document.getElementById('result').innerHTML = `
            <div class="result-hero-card ${predictionClass}">
                ${profilePic}
                <div class="result-main">
                    <div class="result-verdict">${label}</div>
                    <div class="result-confidence">Confidence: ${result.confidence}%</div>
                </div>
            </div>
            <div class="details-card">
                <div class="section-title">Risk Analysis</div>
                <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;">
                    <span style="color:${riskColor};font-weight:700;">${result.risk_level || 'Unknown'}</span>
                    <span>${riskScore}/100</span>
                </div>
                <div class="meter-bar">
                    <div class="meter-fill" style="width:${riskScore}%;background:${riskColor};"></div>
                </div>

                <div class="section-title" style="margin-top:16px;">Profile Details</div>
                <p><span>👥 Followers</span> <b>${result.data.followers.toLocaleString()}</b></p>
                <p><span>➡️ Following</span> <b>${result.data.following.toLocaleString()}</b></p>
                <p><span>✔️ Verified</span> <b>${result.data.is_verified ? 'Yes ✅' : 'No ❌'}</b></p>
                <p><span>😊 Face</span> <b>${result.face.verdict}</b></p>
                <p><span>👥 Clone</span> <b>${result.clone ? result.clone.verdict : 'Not checked'}</b></p>

                <div class="section-title" style="margin-top:16px;">Spam Score</div>
                <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;">
                    <span>${result.spam ? result.spam.verdict : ''}</span>
                </div>
                <div class="meter-bar">
                    <div class="meter-fill" style="width:${spamScore}%;background:${spamColor};"></div>
                </div>
            </div>
        `;

    } catch (error) {
        document.getElementById('loading').style.display = 'none';
        document.getElementById('result').innerHTML =
            '<div class="result warning">⚠️ Cannot connect to app. Make sure your app is running at http://127.0.0.1:5004</div>';
    }
}

document.addEventListener('keypress', function (e) {
    if (e.key === 'Enter') analyze();
});

document.addEventListener('DOMContentLoaded', () => {
    const btnAnalyzeDetected = document.getElementById('btn-analyze-detected');
    if (btnAnalyzeDetected) {
        btnAnalyzeDetected.addEventListener('click', analyzeDetected);
    }
    
    const btnIg = document.getElementById('btn-ig');
    if (btnIg) {
        btnIg.addEventListener('click', () => setPlatform('instagram'));
    }
    
    const btnX = document.getElementById('btn-x');
    if (btnX) {
        btnX.addEventListener('click', () => setPlatform('x'));
    }
    
    const btnAnalyze = document.getElementById('btn-analyze');
    if (btnAnalyze) {
        btnAnalyze.addEventListener('click', analyze);
    }
});