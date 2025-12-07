// Global realtime + unread badge
(function () {
    const metaUser = document.querySelector('meta[name="current-user-id"]');
    if (!metaUser) return;
    window.currentUserId = Number(metaUser.content);
    if (Number.isNaN(window.currentUserId)) return;

    const badge = document.getElementById("unread-badge");
    const socket = window.letstalkSocket || io();
    window.letstalkSocket = socket;

    const ensureNotificationPermission = async () => {
        if (!("Notification" in window)) return;
        if (Notification.permission === "default") {
            try {
                await Notification.requestPermission();
            } catch (_) {
                /* ignore */
            }
        }
    };

    const setBadge = (count) => {
        if (!badge) return;
        if (count > 0) {
            badge.textContent = count;
            badge.classList.remove("hidden");
        } else {
            badge.classList.add("hidden");
            badge.textContent = "";
        }
    };

    const fetchUnread = async () => {
        try {
            const res = await fetch("/api/unread_count");
            if (!res.ok) return;
            const data = await res.json();
            setBadge(data.count || 0);
        } catch (e) {
            console.warn("unread fetch failed", e);
        }
    };

    socket.on("connect", () => {
        socket.emit("join", { user_id: window.currentUserId });
        fetchUnread();
        ensureNotificationPermission();
    });

    socket.on("unread", (payload) => {
        setBadge(payload.count || 0);
    });

    socket.on("message", (msg) => {
        if (msg.receiver_id === window.currentUserId) {
            fetchUnread();
            showBrowserNotification(msg);
        }
    });

    fetchUnread();
})();

// Chat screen realtime
(function () {
    const chatEl = document.querySelector("#chat");
    if (!chatEl) return;

    const otherId = window.letstalkOtherId;
    const socket = window.letstalkSocket || io();
    window.letstalkSocket = socket;
    const form = document.querySelector("#chat-form");
    const input = form ? form.querySelector("input[name='content']") : null;

    const showBrowserNotification = (msg) => {
        if (!("Notification" in window)) return;
        if (document.hasFocus()) return; // avoid double notice when active
        if (Notification.permission !== "granted") return;
        const title = msg.sender_name ? `${msg.sender_name} messaged you` : "New message";
        const body = msg.content;
        try {
            new Notification(title, { body });
        } catch (e) {
            /* ignore failures */
        }
    };

    const escapeHtml = (str) =>
        str.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

    const addMessage = (m) => {
        if (chatEl.querySelector(`[data-id="${m.id}"]`)) return;
        const div = document.createElement("div");
        div.className = "message " + (m.sender_id === window.currentUserId ? "outgoing" : "incoming");
        div.dataset.id = m.id;
        div.innerHTML = `
            <div class="body">${escapeHtml(m.content)}</div>
            <div class="meta">
                ${new Date(m.created_at).toLocaleTimeString([], {hour: "2-digit", minute: "2-digit"})}
                ${m.sender_id === window.currentUserId ? `<span class="ticks ${m.seen_at ? "seen" : ""}" data-id="${m.id}">✔✔</span>` : ""}
            </div>
        `;
        chatEl.appendChild(div);
        chatEl.scrollTop = chatEl.scrollHeight;
        if (m.sender_id !== window.currentUserId) {
            showPopup(`New message from user #${m.sender_id}: ${m.content.slice(0, 80)}`);
            showBrowserNotification(m);
            markSeen();
        }
    };

    const showPopup = (text) => {
        const el = document.createElement("div");
        el.className = "popup";
        el.textContent = text;
        document.body.appendChild(el);
        setTimeout(() => el.remove(), 2500);
    };

    const updateSeenTicks = (messageIds) => {
        messageIds.forEach((id) => {
            const tick = chatEl.querySelector(`.ticks[data-id="${id}"]`);
            if (tick) tick.classList.add("seen");
        });
    };

    const fetchMessages = async () => {
        const res = await fetch(`/api/messages/${otherId}`);
        if (!res.ok) return;
        const data = await res.json();
        chatEl.innerHTML = "";
        data.forEach(addMessage);
        chatEl.scrollTop = chatEl.scrollHeight;
        await markSeen();
    };

    const markSeen = async () => {
        await fetch(`/api/messages/${otherId}/seen`, { method: "POST" });
    };

    socket.on("seen", (payload) => {
        if (payload.by === otherId) {
            updateSeenTicks(payload.message_ids || []);
        }
    });

    socket.on("message", (msg) => {
        const participants = [msg.sender_id, msg.receiver_id];
        if (!participants.includes(otherId)) return;
        addMessage(msg);
    });

    if (form && input) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            const text = input.value.trim();
            if (!text) return;
            input.value = "";
            try {
                const res = await fetch(`/chat/${otherId}/send`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ content: text }),
                });
                if (res.ok) {
                    const msg = await res.json();
                    addMessage(msg);
                }
            } catch (err) {
                console.warn("send failed", err);
            }
        });
    }

    fetchMessages();
})();