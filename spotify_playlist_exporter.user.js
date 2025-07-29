// ==UserScript==
// @name         Spotify Playlist/Liked Songs Exporter
// @namespace    http://tampermonkey.net/
// @version      1.0
// @description  Export all song titles and artists from Spotify playlist or liked songs page to clipboard or .txt file
// @author       AI
// @match        https://open.spotify.com/*
// @grant        GM_setClipboard
// ==/UserScript==

(function() {
    'use strict';

    // Utility: sleep
    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    // Add export button to the page
    function addExportButton() {
        if (document.getElementById('export-songs-btn')) return;
        const header = document.querySelector('[data-testid="entityHeader"]') || document.querySelector('header');
        if (!header) return;
        const btn = document.createElement('button');
        btn.id = 'export-songs-btn';
        btn.textContent = 'Export Songs';
        btn.style.marginLeft = '16px';
        btn.style.padding = '8px 16px';
        btn.style.background = '#1db954';
        btn.style.color = '#fff';
        btn.style.border = 'none';
        btn.style.borderRadius = '20px';
        btn.style.cursor = 'pointer';
        btn.onclick = exportSongs;
        header.appendChild(btn);
    }

    // Scroll to load all songs
    async function scrollToLoadAllSongs() {
        // Try to find the main scrollable container
        let scrollContainer =
            document.querySelector('div[role="presentation"][tabindex="-1"]') ||
            document.querySelector('[data-testid="playlist-tracklist"]') ||
            document.querySelector('[data-testid="track-list"]');

        if (!scrollContainer) {
            alert("Could not find the scrollable container. Please make sure you're on a playlist or liked songs page.");
            return;
        }

        let lastCount = 0;
        let sameCountTimes = 0;
        for (let i = 0; i < 100; i++) {
            scrollContainer.scrollTo(0, scrollContainer.scrollHeight);
            await sleep(700);
            const rows = document.querySelectorAll('div[data-testid="tracklist-row"]');
            if (rows.length === lastCount) {
                sameCountTimes++;
                if (sameCountTimes > 3) break;
            } else {
                sameCountTimes = 0;
            }
            lastCount = rows.length;
        }
    }

    // Extract all song titles and artists (robust, using aria-colindex)
    function extractSongs() {
        // Find all rows by [data-testid="tracklist-row"]
        const rows = document.querySelectorAll('div[data-testid="tracklist-row"]');
        const songs = [];
        rows.forEach(row => {
            try {
                // Title
                const titleDiv = row.querySelector('div[aria-colindex="2"] div[dir="auto"]');
                const title = titleDiv ? titleDiv.textContent.trim() : '[Unknown Title]';
                // Artists
                const artistLinks = row.querySelectorAll('div[aria-colindex="3"] a');
                const artists = Array.from(artistLinks).map(a => a.textContent.trim()).join(', ');
                songs.push(`${title} - ${artists}`);
            } catch (e) {}
        });
        return songs;
    }

    // Export songs: scroll, extract, copy, and download
    async function exportSongs() {
        const btn = document.getElementById('export-songs-btn');
        btn.textContent = 'Exporting...';
        btn.disabled = true;
        await scrollToLoadAllSongs();
        const songs = extractSongs();
        if (songs.length === 0) {
            alert('No songs found! Make sure you are on a playlist or liked songs page.');
            btn.textContent = 'Export Songs';
            btn.disabled = false;
            return;
        }
        const text = songs.join('\n');
        // Copy to clipboard
        if (typeof GM_setClipboard !== 'undefined') {
            GM_setClipboard(text);
        } else {
            navigator.clipboard.writeText(text);
        }
        // Download as .txt file
        const blob = new Blob([text], {type: 'text/plain'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'spotify_songs.txt';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        alert(`Exported ${songs.length} songs!\nCopied to clipboard and downloaded as spotify_songs.txt`);
        btn.textContent = 'Export Songs';
        btn.disabled = false;
    }

    // Observe for header changes to add the button
    const observer = new MutationObserver(addExportButton);
    observer.observe(document.body, {childList: true, subtree: true});
    // Try to add button immediately
    addExportButton();
})(); 