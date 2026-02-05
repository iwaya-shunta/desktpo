// desktpo.js

let selectedFileBase64 = null, selectedMimeType = null;
const chatHistory = document.getElementById('chat-history');

// --- 初期化処理 ---
document.addEventListener('DOMContentLoaded', () => {
    loadHistory();
    initClock();
    fetchNews();
    fetchWeather();
    initEventListeners();
});

// --- 時計 ---
function initClock() {
    setInterval(() => {
        document.getElementById('clock').innerText = new Date().toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
    }, 1000);
}

// --- ニュース取得 ---
function fetchNews() {
    fetch(`https://api.rss2json.com/v1/api.json?rss_url=https://news.google.com/rss?hl=ja&gl=JP&ceid=JP:ja`)
        .then(r => r.json())
        .then(d => {
            document.getElementById('news-container').innerHTML = d.items.slice(0, 10).map(i =>
                `<div class="news-item"><a href="${i.link}" target="_blank" class="news-link">${i.title}</a></div>`
            ).join('');
        });
}

// --- 天気取得 ---
function fetchWeather() {
    fetch(`https://api.open-meteo.com/v1/forecast?latitude=34.3796&longitude=132.4026&current_weather=true`)
        .then(r => r.json())
        .then(d => document.getElementById('weather').innerText = `${Math.round(d.current_weather.temperature)}°C`);
}

// --- チャットUI関連 ---
function addMessageToUI(role, text) {
    const bubble = document.createElement('div');
    const displayRole = role === 'assistant' ? 'gemini' : 'user';
    bubble.className = `message ${displayRole} show`;

    if (displayRole === 'gemini') {
        const content = marked.parse(text);
        bubble.innerHTML = `<div class="ai-avatar">L</div><div class="res-txt">${content}</div>`;
        addCopyButtons(bubble);
    } else {
        bubble.innerText = text;
    }
    chatHistory.appendChild(bubble);
    chatHistory.scrollTop = chatHistory.scrollHeight;
    return bubble;
}

async function ask() {
    const input = document.getElementById('geminiInput');
    const text = input.value.trim();
    const model = document.querySelector('input[name="modelSelect"]:checked').value;
    if (!text && !selectedFileBase64) return;

    const f64 = selectedFileBase64;
    const mime = selectedMimeType;
    selectedFileBase64 = null;
    document.getElementById('preview-container').style.display = 'none';

    if (f64) {
        chatHistory.innerHTML += `<div class="message user show" style="background:transparent; padding:0; align-self:flex-end;"><img src="data:${mime};base64,${f64}" style="max-height:280px; border-radius:15px;"></div>`;
    }
    if (text) addMessageToUI('user', text);
    input.value = '';

    const bubble = addMessageToUI('assistant', '...');
    const resTxtElement = bubble.querySelector('.res-txt');

    try {
        const res = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: text, image: f64, mime_type: mime, model: model })
        });
        const data = await res.json();

        // 🚀 起動信号の処理（修正版ロジックを採用）
        if (data.launch_url) {
            window.location.href = data.launch_url;
            data.response = "了解だよ！アプリを起動するね。";
        }

        await runTypewriter(resTxtElement, data.response, data.voice_url);
    } catch (e) { resTxtElement.innerText = "エラーになっちゃった..."; }
}

// --- タイピング演出 ---
async function runTypewriter(el, fullTxt, url) {
    const displayTxt = fullTxt.replace(/\(.*\)/g, '').replace(/（.*）/g, '');
    let i = 0; el.innerHTML = "";
    const audio = new Audio(url);
    const av = el.parentElement.parentElement.querySelector('.ai-avatar');
    audio.onplay = () => av.classList.add('speaking-icon');
    audio.onended = () => av.classList.remove('speaking-icon');
    audio.play();
    return new Promise(res => {
        function type() {
            if (i < displayTxt.length) {
                el.innerText += displayTxt.charAt(i); i++;
                setTimeout(type, 30);
            } else {
                el.innerHTML = marked.parse(displayTxt);
                addCopyButtons(el);
                res();
            }
            chatHistory.scrollTop = chatHistory.scrollHeight;
        }
        type();
    });
}

// --- イベントリスナー ---
function initEventListeners() {
    document.getElementById('sendBtn').onclick = ask;
    document.getElementById('geminiInput').onkeydown = (e) => { if (e.key === 'Enter') ask(); };
    document.getElementById('reloadBtn').onclick = () => location.reload();

    // タブ切り替え
    document.getElementById('nav-news').onclick = (e) => switchTab('news', e);
    document.getElementById('nav-chat').onclick = (e) => switchTab('chat', e);
    document.getElementById('nav-calendar').onclick = (e) => switchTab('calendar', e);
}

// 既存の履歴取得やその他の関数もここに移動...
window.switchTab = function(t, e) {
    document.querySelectorAll('.panel').forEach(p => { p.style.display = 'none'; p.classList.remove('active-panel'); });
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    const target = document.getElementById(t + '-panel');
    if (target) { target.style.display = 'flex'; target.classList.add('active-panel'); }
    if (e) e.currentTarget.classList.add('active');
};