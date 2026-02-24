// === Perp DEX Airdrop Tracker - Main Application ===

class AirdropTracker {
    constructor() {
        this.protocols = [];
        this.chains = [];
        this.activeChain = 'all';
        this.activePotential = 'all';
        this.activeToken = 'all';
        this.searchQuery = '';
        this.settings = this.loadSettings();
        this.tweetCache = {};
        this.init();
    }

    async init() {
        await this.loadData();
        this.renderChainFilters();
        this.renderProtocols();
        this.updateStats();
        this.bindEvents();
    }

    // === Data Loading ===
    async loadData() {
        try {
            const response = await fetch('./data/protocols.json');
            const data = await response.json();
            this.protocols = data.protocols;
            this.chains = data.chains;
            this.lastUpdated = data.lastUpdated;
        } catch (err) {
            console.error('Failed to load protocol data:', err);
            this.showToast('データの読み込みに失敗しました', 'error');
        }
    }

    // === Settings ===
    loadSettings() {
        try {
            const saved = localStorage.getItem('airdrop_tracker_settings');
            return saved ? JSON.parse(saved) : { bearerToken: '', proxyUrl: '' };
        } catch {
            return { bearerToken: '', proxyUrl: '' };
        }
    }

    saveSettings() {
        const bearerToken = document.getElementById('bearerToken').value;
        const proxyUrl = document.getElementById('proxyUrl').value;
        this.settings = { bearerToken, proxyUrl };
        localStorage.setItem('airdrop_tracker_settings', JSON.stringify(this.settings));
        this.toggleSettingsPanel(false);
        this.showToast('設定を保存しました', 'success');
    }

    // === Rendering ===
    renderChainFilters() {
        const container = document.getElementById('chainFilters');
        const usedChainIds = new Set();
        this.protocols.forEach(p => {
            if (p.chains) {
                p.chains.forEach(c => usedChainIds.add(c));
            } else {
                usedChainIds.add(p.chain);
            }
        });

        let html = '<button class="chain-btn active" data-chain="all">全て</button>';
        this.chains
            .filter(c => usedChainIds.has(c.id))
            .forEach(chain => {
                html += `<button class="chain-btn" data-chain="${chain.id}">${chain.name}</button>`;
            });
        container.innerHTML = html;
    }

    renderProtocols() {
        const grid = document.getElementById('protocolGrid');
        const filtered = this.getFilteredProtocols();

        if (filtered.length === 0) {
            grid.innerHTML = `
                <div class="no-results">
                    <h3>該当するプロトコルが見つかりません</h3>
                    <p>フィルター条件を変更してください</p>
                </div>`;
            return;
        }

        grid.innerHTML = filtered.map(p => this.renderCard(p)).join('');
    }

    renderCard(protocol) {
        const chainBadges = (protocol.chains || [protocol.chain])
            .map(c => {
                const chain = this.chains.find(ch => ch.id === c);
                const name = chain ? chain.name : c;
                return `<span class="card-chain chain-${c}">${name}</span>`;
            }).join(' ');

        const potentialLabels = {
            confirmed: '確定',
            very_high: '非常に高い',
            high: '高い',
            medium: '中程度',
            low: '低い'
        };

        const criteriaHtml = protocol.criteria
            .map(c => `<span class="criteria-item">${c}</span>`)
            .join('');

        const twitterLinks = (protocol.twitter || [])
            .map(handle => `<a href="https://x.com/${handle.replace('@', '')}" target="_blank" rel="noopener noreferrer">${handle}</a>`)
            .join(' ');

        return `
        <div class="protocol-card potential-${protocol.airdropPotential}" data-id="${protocol.id}">
            <div class="card-header">
                <div class="card-title-area">
                    <div class="card-title">
                        ${protocol.website
                            ? `<a href="${protocol.website}" target="_blank" rel="noopener noreferrer">${protocol.name}</a>`
                            : protocol.name
                        }
                    </div>
                    <div>${chainBadges}</div>
                </div>
                <div class="card-badges">
                    <span class="badge badge-potential badge-${protocol.airdropPotential}">
                        ${potentialLabels[protocol.airdropPotential] || protocol.airdropPotential}
                    </span>
                    <span class="badge ${protocol.hasToken ? 'badge-token-yes' : 'badge-token-no'}">
                        ${protocol.hasToken ? `Token: ${protocol.tokenName}` : 'Token未発行'}
                    </span>
                </div>
            </div>
            <p class="card-description">${protocol.description}</p>
            <p class="card-description" style="color: var(--accent-cyan); font-size: 0.8rem;">
                ${protocol.airdropStatus}
            </p>
            <div class="card-criteria">
                <h4>エアドロップ対象基準</h4>
                <div class="criteria-list">${criteriaHtml}</div>
            </div>
            ${protocol.notes ? `<p class="card-description" style="font-style: italic; font-size: 0.8rem;">📝 ${protocol.notes}</p>` : ''}
            <div class="card-meta">
                <span class="card-tvl">TVL: ${protocol.tvl || 'N/A'}</span>
                <div class="card-twitter">${twitterLinks}</div>
            </div>
            <div class="card-actions">
                <button class="btn btn-secondary" onclick="app.searchTweets('${protocol.id}')">
                    𝕏 ツイート検索
                </button>
                <button class="btn btn-secondary" onclick="app.openXSearch('${protocol.xSearchQuery || protocol.name}')">
                    𝕏 で検索
                </button>
            </div>
        </div>`;
    }

    // === Filtering ===
    getFilteredProtocols() {
        return this.protocols.filter(p => {
            // Chain filter
            if (this.activeChain !== 'all') {
                const chains = p.chains || [p.chain];
                if (!chains.includes(this.activeChain)) return false;
            }

            // Potential filter
            if (this.activePotential !== 'all' && p.airdropPotential !== this.activePotential) {
                return false;
            }

            // Token filter
            if (this.activeToken !== 'all') {
                if (this.activeToken === 'no' && p.hasToken) return false;
                if (this.activeToken === 'yes' && !p.hasToken) return false;
            }

            // Search filter
            if (this.searchQuery) {
                const q = this.searchQuery.toLowerCase();
                const searchable = [
                    p.name,
                    p.description,
                    p.tokenName || '',
                    ...(p.chains || [p.chain])
                ].join(' ').toLowerCase();
                if (!searchable.includes(q)) return false;
            }

            return true;
        });
    }

    // === Stats ===
    updateStats() {
        const filtered = this.getFilteredProtocols();
        const allChains = new Set();
        filtered.forEach(p => {
            (p.chains || [p.chain]).forEach(c => allChains.add(c));
        });

        document.getElementById('totalProtocols').textContent = filtered.length;
        document.getElementById('totalChains').textContent = allChains.size;
        document.getElementById('highPotential').textContent =
            filtered.filter(p => ['confirmed', 'very_high', 'high'].includes(p.airdropPotential)).length;
        document.getElementById('lastUpdated').textContent = this.lastUpdated || '-';
    }

    // === X (Twitter) API Integration ===
    async searchTweets(protocolId) {
        const protocol = this.protocols.find(p => p.id === protocolId);
        if (!protocol) return;

        if (!this.settings.bearerToken) {
            this.showToast('X API Bearer Tokenを設定してください', 'error');
            this.toggleSettingsPanel(true);
            return;
        }

        this.showModal(protocol.name + ' - 最新ツイート');

        // Check cache (5 min)
        const cacheKey = protocolId;
        const cached = this.tweetCache[cacheKey];
        if (cached && Date.now() - cached.timestamp < 5 * 60 * 1000) {
            this.renderTweets(cached.data);
            return;
        }

        try {
            const query = encodeURIComponent(protocol.xSearchQuery || protocol.name + ' airdrop');
            const baseUrl = 'https://api.twitter.com/2/tweets/search/recent';
            const params = `?query=${query}&max_results=10&tweet.fields=created_at,public_metrics,author_id&expansions=author_id&user.fields=name,username`;
            const url = this.settings.proxyUrl
                ? `${this.settings.proxyUrl}/${baseUrl}${params}`
                : `${baseUrl}${params}`;

            const response = await fetch(url, {
                headers: {
                    'Authorization': `Bearer ${this.settings.bearerToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.status} ${response.statusText}`);
            }

            const data = await response.json();

            // Cache result
            this.tweetCache[cacheKey] = { data, timestamp: Date.now() };

            this.renderTweets(data);
        } catch (err) {
            console.error('Tweet fetch error:', err);
            const modalBody = document.getElementById('modalBody');
            modalBody.innerHTML = `
                <div class="no-results">
                    <h3>ツイートの取得に失敗しました</h3>
                    <p>${err.message}</p>
                    <p style="margin-top: 12px; font-size: 0.85rem; color: var(--text-muted);">
                        ヒント: ブラウザから直接X APIを呼ぶ場合はCORSプロキシが必要です。<br>
                        または、Pythonスクレイパー (scraper/twitter_scraper.py) を使ってローカルでデータを取得してください。
                    </p>
                </div>`;
        }
    }

    renderTweets(data) {
        const modalBody = document.getElementById('modalBody');

        if (!data.data || data.data.length === 0) {
            modalBody.innerHTML = '<div class="no-results"><h3>ツイートが見つかりませんでした</h3></div>';
            return;
        }

        const users = {};
        if (data.includes && data.includes.users) {
            data.includes.users.forEach(u => { users[u.id] = u; });
        }

        const tweetsHtml = data.data.map(tweet => {
            const user = users[tweet.author_id] || { name: 'Unknown', username: 'unknown' };
            const metrics = tweet.public_metrics || {};
            const date = tweet.created_at
                ? new Date(tweet.created_at).toLocaleString('ja-JP')
                : '';

            return `
            <div class="tweet-card">
                <div class="tweet-header">
                    <a class="tweet-author" href="https://x.com/${user.username}" target="_blank" rel="noopener noreferrer">
                        ${user.name} @${user.username}
                    </a>
                    <span class="tweet-date">${date}</span>
                </div>
                <p class="tweet-text">${this.linkifyText(tweet.text)}</p>
                <div class="tweet-metrics">
                    <span>&#x2764; ${metrics.like_count || 0}</span>
                    <span>&#x1F501; ${metrics.retweet_count || 0}</span>
                    <span>&#x1F4AC; ${metrics.reply_count || 0}</span>
                </div>
            </div>`;
        }).join('');

        modalBody.innerHTML = tweetsHtml;
    }

    openXSearch(query) {
        const url = `https://x.com/search?q=${encodeURIComponent(query)}&src=typed_query&f=live`;
        window.open(url, '_blank', 'noopener,noreferrer');
    }

    async fetchAllTweets() {
        if (!this.settings.bearerToken) {
            this.showToast('X API Bearer Tokenを設定してください', 'error');
            this.toggleSettingsPanel(true);
            return;
        }

        const noTokenProtocols = this.protocols.filter(p => !p.hasToken);
        this.showToast(`${noTokenProtocols.length}件のプロトコルのツイートを取得中...`, 'info');

        let success = 0;
        let failed = 0;

        for (const protocol of noTokenProtocols) {
            try {
                const query = encodeURIComponent(protocol.xSearchQuery || protocol.name + ' airdrop');
                const baseUrl = 'https://api.twitter.com/2/tweets/search/recent';
                const params = `?query=${query}&max_results=10&tweet.fields=created_at,public_metrics,author_id&expansions=author_id&user.fields=name,username`;
                const url = this.settings.proxyUrl
                    ? `${this.settings.proxyUrl}/${baseUrl}${params}`
                    : `${baseUrl}${params}`;

                const response = await fetch(url, {
                    headers: {
                        'Authorization': `Bearer ${this.settings.bearerToken}`,
                        'Content-Type': 'application/json'
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    this.tweetCache[protocol.id] = { data, timestamp: Date.now() };
                    success++;
                } else {
                    failed++;
                }

                // Rate limit: wait 1 second between requests
                await new Promise(resolve => setTimeout(resolve, 1000));
            } catch {
                failed++;
            }
        }

        this.showToast(`取得完了: ${success}件成功, ${failed}件失敗`, success > 0 ? 'success' : 'error');
    }

    // === UI Helpers ===
    linkifyText(text) {
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(
                /(https?:\/\/[^\s]+)/g,
                '<a href="$1" target="_blank" rel="noopener noreferrer" style="color: var(--accent-blue);">$1</a>'
            )
            .replace(
                /@(\w+)/g,
                '<a href="https://x.com/$1" target="_blank" rel="noopener noreferrer" style="color: var(--accent-blue);">@$1</a>'
            )
            .replace(
                /\$([A-Z]+)/g,
                '<span style="color: var(--accent-green); font-weight: 600;">$$1</span>'
            );
    }

    showModal(title) {
        const modal = document.getElementById('tweetModal');
        document.getElementById('modalTitle').textContent = title;
        document.getElementById('modalBody').innerHTML = '<div class="loading">ツイートを読み込み中...</div>';
        modal.classList.remove('hidden');
    }

    closeModal() {
        document.getElementById('tweetModal').classList.add('hidden');
    }

    toggleSettingsPanel(show) {
        const panel = document.getElementById('settingsPanel');
        if (show === undefined) {
            panel.classList.toggle('hidden');
        } else {
            panel.classList.toggle('hidden', !show);
        }

        if (!panel.classList.contains('hidden')) {
            document.getElementById('bearerToken').value = this.settings.bearerToken || '';
            document.getElementById('proxyUrl').value = this.settings.proxyUrl || '';
        }
    }

    showToast(message, type = 'info') {
        const container = document.getElementById('toastContainer');
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    }

    // === Event Binding ===
    bindEvents() {
        // Chain filters
        document.getElementById('chainFilters').addEventListener('click', (e) => {
            if (e.target.classList.contains('chain-btn')) {
                document.querySelectorAll('.chain-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
                this.activeChain = e.target.dataset.chain;
                this.renderProtocols();
                this.updateStats();
            }
        });

        // Potential filter
        document.getElementById('potentialFilter').addEventListener('change', (e) => {
            this.activePotential = e.target.value;
            this.renderProtocols();
            this.updateStats();
        });

        // Token filter
        document.getElementById('tokenFilter').addEventListener('change', (e) => {
            this.activeToken = e.target.value;
            this.renderProtocols();
            this.updateStats();
        });

        // Search
        document.getElementById('searchInput').addEventListener('input', (e) => {
            this.searchQuery = e.target.value;
            this.renderProtocols();
            this.updateStats();
        });

        // Settings
        document.getElementById('toggleSettings').addEventListener('click', () => {
            this.toggleSettingsPanel();
        });

        document.getElementById('saveSettings').addEventListener('click', () => {
            this.saveSettings();
        });

        document.getElementById('cancelSettings').addEventListener('click', () => {
            this.toggleSettingsPanel(false);
        });

        // Refresh tweets
        document.getElementById('refreshTweets').addEventListener('click', () => {
            this.fetchAllTweets();
        });

        // Modal close
        document.querySelector('.modal-close').addEventListener('click', () => {
            this.closeModal();
        });

        document.querySelector('.modal-overlay').addEventListener('click', () => {
            this.closeModal();
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
    }
}

// Initialize app
const app = new AirdropTracker();
