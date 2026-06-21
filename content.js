// Content script - runs on Instagram and X pages
// Automatically detects the current profile username
function getUsername() {
    const url = window.location.href;
    
    // Instagram
    const igMatch = url.match(/instagram\.com\/([^/?]+)/);
    if (igMatch && igMatch[1]) {
        const excluded = ['p', 'explore', 'reels', 'stories', 'direct'];
        if (!excluded.includes(igMatch[1])) {
            return { username: igMatch[1], platform: 'instagram' };
        }
    }

    // X/Twitter
    const xMatch = url.match(/(?:x|twitter)\.com\/([^/?]+)/);
    if (xMatch && xMatch[1]) {
        const excluded = ['home', 'explore', 'notifications', 'messages', 'i', 'settings'];
        if (!excluded.includes(xMatch[1])) {
            return { username: xMatch[1], platform: 'x' };
        }
    }

    return null;
}

// Store detected username for popup to use
const detected = getUsername();
if (detected) {
    chrome.storage.local.set({
        detectedUsername: detected.username,
        detectedPlatform: detected.platform
    });
}