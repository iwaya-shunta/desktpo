let selectedFileBase64 = null, selectedMimeType = null;
    const chatHistory = document.getElementById('chat-history');

    // 時計・ニュース・天気
    setInterval(() => { document.getElementById('clock').innerText = new Date().toLocaleTimeString('ja-JP', {hour:'2-digit', minute:'2-digit'}); }, 1000);
    fetch(`https://api.rss2json.com/v1/api.json?rss_url=https://news.google.com/rss?hl=ja&gl=JP&ceid=JP:ja`)
        .then(r=>r.json())
        .then(d=>document.getElementById('news-container').innerHTML = d.items.slice(0, 10).map(i => `<div class="news-item"><a href="${i.link}" target="_blank" class="news-link">${i.title}</a></div>`).join(''));

    fetch(`https://api.open-meteo.com/v1/forecast?latitude=34.3796&longitude=132.4026&current_weather=true`)
        .then(r=>r.json())
        .then(d=>document.getElementById('weather').innerText = `${Math.round(d.current_weather.temperature)}°C`);

    // タブ切り替え
    window.switchTab = function(t, e) {
        document.querySelectorAll('.panel').forEach(p => { p.style.display = 'none'; p.classList.remove('active-panel'); });
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        const target = document.getElementById(t + '-panel');
        if (target) { target.style.display = 'flex'; target.classList.add('active-panel'); }
        if (e) e.currentTarget.classList.add('active');
    };
    if (window.innerWidth <= 768) switchTab('chat');

    // コピーボタン
    function addCopyButtons(container) {
        container.querySelectorAll('pre').forEach((pre) => {
            const code = pre.querySelector('code');
            if (!code || pre.querySelector('.copy-btn')) return;
            const button = document.createElement('button');
            button.innerText = 'Copy';
            button.className = 'copy-btn';
            button.onclick = () => {
                navigator.clipboard.writeText(code.innerText).then(() => {
                    button.innerText = 'Copied!';
                    setTimeout(() => button.innerText = 'Copy', 2000);
                });
            };
            pre.appendChild(button);
        });
    }

    function addMessageToUI(role, text) {
        const hist = document.getElementById('chat-history');
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
        hist.appendChild(bubble);
        hist.scrollTop = hist.scrollHeight;
        return bubble;
    }

    async function loadHistory() {
    try {
        const response = await fetch('/history');
        if (!response.ok) return;

        const history = await response.json();
        const chatHistoryElement = document.getElementById('chat-history');

        // 🚀 重要：一度画面をクリアしてから、取得した履歴を 1 つずつ追加する
        chatHistoryElement.innerHTML = '';

        history.forEach(msg => {
            // role が 'user' か 'assistant' かで判定
            addMessageToUI(msg.role, msg.content);
        });

        // 最後に一番下までスクロール
        chatHistoryElement.scrollTop = chatHistoryElement.scrollHeight;
    } catch (error) {
        console.error("履歴の読み込み中にエラーが発生しました:", error);
    }
}

// 🚀 ページが読み込まれたら履歴を取得する
document.addEventListener('DOMContentLoaded', loadHistory);

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

    async function ask() {
        const input = document.getElementById('geminiInput');
        const text = input.value.trim();
        const model = document.querySelector('input[name="modelSelect"]:checked').value;
        if (!text && !selectedFileBase64) return;

        const f64 = selectedFileBase64; const mime = selectedMimeType;
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
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ message: text, image: f64, mime_type: mime, model: model })
            });
            const data = await res.json();

            // 🚀 信号があれば Windows プロトコルを呼び出し
            if (data.launch_url) {
                console.log("Launching:", data.launch_url);
                window.location.href = data.launch_url;
            }

            await runTypewriter(resTxtElement, data.response, data.voice_url);
        } catch (e) {
            resTxtElement.innerText = "エラーになっちゃった...";
        }
    }

    // スクロールボタンのロジック
    let scrollInterval = null;
    function startScroll(amount) {
        chatHistory.scrollBy({ top: amount, behavior: 'auto' });
        scrollInterval = setInterval(() => { chatHistory.scrollBy({ top: amount, behavior: 'auto' }); }, 30);
    }
    function stopScroll() { if (scrollInterval) { clearInterval(scrollInterval); scrollInterval = null; } }
    
    // 音声認識
    const rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    rec.lang = 'ja-JP';
    document.getElementById('micBtn').onclick = () => { rec.start(); document.body.classList.add('recording'); };
    rec.onresult = (e) => { document.getElementById('geminiInput').value = e.results[0][0].transcript; ask(); };
    rec.onend = () => { document.body.classList.remove('recording'); };

    // 各種ボタン・キーイベント
    document.getElementById('sendBtn').onclick = ask;
    document.getElementById('geminiInput').onkeydown = (e) => { if(e.key==='Enter') ask(); };
    document.getElementById('fileBtn').onclick = () => document.getElementById('fileInput').click();
    document.getElementById('fileInput').onchange = (e) => {
        const f = e.target.files[0]; if (!f) return;
        const r = new FileReader(); r.onload = (e) => {
            selectedFileBase64 = e.target.result.split(',')[1]; selectedMimeType = f.type;
            document.getElementById('preview-container').innerHTML = `<img src="${e.target.result}" style="max-height:80px; border-radius:10px;">`;
            document.getElementById('preview-container').style.display = 'block';
        }; r.readAsDataURL(f);
    };

    // スマホ用スワイプ遷移
    let touchStartX = 0; let touchEndX = 0;
    const tabs = ['news', 'chat', 'calendar'];
    window.addEventListener('touchstart', e => { touchStartX = e.changedTouches[0].screenX; }, false);
    window.addEventListener('touchend', e => { touchEndX = e.changedTouches[0].screenX; handleSwipe(); }, false);
    function handleSwipe() {
        const distance = touchEndX - touchStartX;
        const currentTab = document.querySelector('.nav-item.active').innerText.includes('ニュース') ? 'news' :
                           document.querySelector('.nav-item.active').innerText.includes('チャット') ? 'chat' : 'calendar';
        const currentIndex = tabs.indexOf(currentTab);
        if (distance > 70 && currentIndex > 0) switchTab(tabs[currentIndex - 1]);
        else if (distance < -70 && currentIndex < 2) switchTab(tabs[currentIndex + 1]);
    }

    // PWAサービスワーカー登録
    if ('serviceWorker' in navigator) {
        window.addEventListener('load', () => {
            navigator.serviceWorker.register('/service-worker.js')
                .then(reg => console.log('SW Registered'))
                .catch(err => console.log('SW Registration Failed', err));
        });
    }