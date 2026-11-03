// EstateFlow CRM — Global Script

// ── Theme Toggle (runs before DOMContentLoaded) ──────────────
var html = document.documentElement;
function applyThemeIcons() {
    var moon = document.getElementById('theme-icon-moon');
    var sun  = document.getElementById('theme-icon-sun');
    if (html.classList.contains('dark')) {
        if (moon) moon.style.display = 'none';
        if (sun)  sun.style.display  = '';
    } else {
        if (moon) moon.style.display = '';
        if (sun)  sun.style.display  = 'none';
    }
}
applyThemeIcons();
var themeBtn = document.getElementById('theme-toggle-btn');
if (themeBtn) {
    themeBtn.addEventListener('click', function () {
        if (html.classList.contains('dark')) {
            html.classList.remove('dark');
            localStorage.setItem('color-theme', 'light');
        } else {
            html.classList.add('dark');
            localStorage.setItem('color-theme', 'dark');
        }
        applyThemeIcons();
    });
}

// ── DOM Ready ─────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function () {

    // Mobile Sidebar
    var sidebar         = document.getElementById('sidebar');
    var sidebarToggle   = document.getElementById('sidebar-toggle-btn');
    var sidebarClose    = document.getElementById('sidebar-close-btn');
    var sidebarBackdrop = document.getElementById('sidebar-backdrop');
    function openSidebar()  { if (sidebar && sidebarBackdrop) { sidebar.classList.remove('-translate-x-full'); sidebarBackdrop.classList.remove('hidden'); } }
    function closeSidebar() { if (sidebar && sidebarBackdrop) { sidebar.classList.add('-translate-x-full');    sidebarBackdrop.classList.add('hidden');    } }
    if (sidebarToggle)   sidebarToggle.addEventListener('click', openSidebar);
    if (sidebarClose)    sidebarClose.addEventListener('click', closeSidebar);
    if (sidebarBackdrop) sidebarBackdrop.addEventListener('click', closeSidebar);

    // Modals
    document.querySelectorAll('[data-modal-open]').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var m = document.getElementById(btn.getAttribute('data-modal-open'));
            if (m) { m.classList.remove('hidden'); m.classList.add('flex'); }
        });
    });
    document.querySelectorAll('[data-modal-close]').forEach(function(btn) {
        btn.addEventListener('click', function() {
            var tid = btn.getAttribute('data-modal-close');
            var m = tid ? document.getElementById(tid) : btn.closest('.modal-container');
            if (m) { m.classList.add('hidden'); m.classList.remove('flex'); }
        });
    });
    document.querySelectorAll('.modal-container').forEach(function(m) {
        m.addEventListener('click', function(e) {
            if (e.target === m) { m.classList.add('hidden'); m.classList.remove('flex'); }
        });
    });

    // Table search
    var gs = document.getElementById('global-search');
    if (gs) {
        gs.addEventListener('input', function(e) {
            var q = e.target.value.toLowerCase().trim();
            document.querySelectorAll('tbody tr').forEach(function(row) {
                if (row.querySelector('td[colspan]')) return;
                row.style.display = row.innerText.toLowerCase().includes(q) ? '' : 'none';
            });
        });
    }

    // ── AI CHAT WIDGET ────────────────────────────────────────
    var chatToggle   = document.getElementById('ai-chat-toggle');
    var chatPanel    = document.getElementById('ai-chat-panel');
    var chatMessages = document.getElementById('ai-chat-messages');
    var chatInput    = document.getElementById('ai-chat-input');
    var chatSend     = document.getElementById('ai-chat-send');
    var openIcon     = document.getElementById('ai-chat-open-icon');
    var closeIcon    = document.getElementById('ai-chat-close-icon');
    var chips        = document.querySelectorAll('.ai-chip');
    var suggestions  = document.getElementById('ai-suggestion-chips');

    if (!chatToggle || !chatPanel) return;

    var isOpen = false;

    chatToggle.addEventListener('click', function () {
        isOpen = !isOpen;
        chatPanel.style.display  = isOpen ? 'flex' : 'none';
        openIcon.style.display   = isOpen ? 'none' : '';
        closeIcon.style.display  = isOpen ? ''     : 'none';
        if (isOpen && chatInput) chatInput.focus();
    });

    chips.forEach(function(chip) {
        chip.addEventListener('click', function() {
            chatInput.value = chip.textContent.trim();
            sendMessage();
        });
    });

    if (chatSend) chatSend.addEventListener('click', sendMessage);
    if (chatInput) {
        chatInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
        });
    }

    function sendMessage() {
        var message = chatInput.value.trim();
        if (!message) return;
        appendMessage('user', message);
        chatInput.value = '';
        if (suggestions) suggestions.style.display = 'none';
        var typingId = appendTyping();
        fetch('/ai/chat/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        })
        .then(function(res) { return res.json(); })
        .then(function(data) {
            removeTyping(typingId);
            appendMessage('ai', data.reply || 'No response.');
        })
        .catch(function() {
            removeTyping(typingId);
            appendMessage('ai', '⚠️ Network error — make sure the server is running.');
        });
    }

    function appendMessage(role, text) {
        var isUser = role === 'user';
        var wrapper = document.createElement('div');
        wrapper.style.cssText = 'display:flex; gap:8px; align-items:flex-start;' + (isUser ? 'flex-direction:row-reverse;' : '');
        var avatar = document.createElement('div');
        avatar.style.cssText = 'width:28px; height:28px; border-radius:50%; display:flex; align-items:center; justify-content:center; flex-shrink:0;' + (isUser ? 'background:#2563eb;' : 'background:#dbeafe;');
        avatar.innerHTML = isUser
            ? '<i class="fa-solid fa-user" style="color:white; font-size:0.7rem;"></i>'
            : '<i class="fa-solid fa-robot" style="color:#2563eb; font-size:0.7rem;"></i>';
        var bubble = document.createElement('div');
        bubble.style.cssText = 'border-radius:12px; padding:10px 14px; font-size:0.8rem; max-width:85%; line-height:1.5;' + (isUser ? 'background:#2563eb; color:white; border-top-right-radius:2px;' : 'background:#f3f4f6; color:#374151; border-top-left-radius:2px;');
        bubble.innerHTML = renderMd(text);
        wrapper.appendChild(avatar);
        wrapper.appendChild(bubble);
        chatMessages.appendChild(wrapper);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function appendTyping() {
        var id = 'typing-' + Date.now();
        var wrapper = document.createElement('div');
        wrapper.id = id;
        wrapper.style.cssText = 'display:flex; gap:8px; align-items:flex-start;';
        wrapper.innerHTML = '<div style="width:28px;height:28px;border-radius:50%;background:#dbeafe;display:flex;align-items:center;justify-content:center;flex-shrink:0;"><i class="fa-solid fa-robot" style="color:#2563eb;font-size:0.7rem;"></i></div><div style="background:#f3f4f6;border-radius:12px;border-top-left-radius:2px;padding:10px 16px;display:flex;gap:5px;align-items:center;"><span style="width:7px;height:7px;border-radius:50%;background:#9ca3af;display:inline-block;animation:bounce 1s infinite 0ms;"></span><span style="width:7px;height:7px;border-radius:50%;background:#9ca3af;display:inline-block;animation:bounce 1s infinite 150ms;"></span><span style="width:7px;height:7px;border-radius:50%;background:#9ca3af;display:inline-block;animation:bounce 1s infinite 300ms;"></span></div>';
        chatMessages.appendChild(wrapper);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return id;
    }

    function removeTyping(id) { var el = document.getElementById(id); if (el) el.remove(); }

    function renderMd(text) {
        return text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
    }
});
