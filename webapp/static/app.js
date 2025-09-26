(function () {
    const config = window.APP_CONFIG || {};

    const searchInput = document.getElementById('search-input');
    const searchResults = document.getElementById('search-results');
    const selectedTickerDisplay = document.getElementById('selected-ticker-display');
    const runButton = document.getElementById('run-button');
    const riskSelect = document.getElementById('risk-select');
    const periodSelect = document.getElementById('period-select');
    const freqSelect = document.getElementById('freq-select');

    const statusPanel = document.getElementById('status');
    const resultsPanel = document.getElementById('results');
    const analystOutput = document.getElementById('analyst-output');
    const strategistOutput = document.getElementById('strategist-output');
    const traderChart = document.getElementById('trader-chart');
    const traderStatsList = document.getElementById('trader-stats');
    const returnsChart = document.getElementById('returns-chart');
    const returnsEmpty = document.getElementById('returns-empty');

    const HIDDEN_CLASS = 'hidden';
    const MUTED_CLASS = 'muted';
    const MIN_QUERY_LENGTH = 2;

    const state = {
        selectedTicker: null,
        selectedLabel: null,
        currentQuery: '',
        searchAbortController: null,
        runAbortController: null,
    };

    const searchCache = new Map();

    function setStatus(kind, message) {
        statusPanel.classList.remove(HIDDEN_CLASS, 'status--error', 'status--success', 'status--info');
        if (!message) {
            statusPanel.classList.add(HIDDEN_CLASS);
            statusPanel.textContent = '';
            return;
        }

        if (kind === 'error') {
            statusPanel.classList.add('status--error');
        } else if (kind === 'success') {
            statusPanel.classList.add('status--success');
        } else {
            statusPanel.classList.add('status--info');
        }
        statusPanel.textContent = message;
    }

    function clearResultsList(message) {
        searchResults.innerHTML = '';
        if (message) {
            const li = document.createElement('li');
            li.className = MUTED_CLASS;
            li.textContent = message;
            searchResults.appendChild(li);
            searchResults.classList.remove(HIDDEN_CLASS);
        } else {
            searchResults.classList.add(HIDDEN_CLASS);
        }
    }

    function setSelectedTicker(symbol, label) {
        state.selectedTicker = symbol;
        state.selectedLabel = label;

        if (symbol && label) {
            selectedTickerDisplay.textContent = `Selected: ${label}`;
            selectedTickerDisplay.classList.remove(HIDDEN_CLASS);
            runButton.removeAttribute('disabled');
            searchInput.dataset.justSelected = 'true';
        } else {
            selectedTickerDisplay.textContent = '';
            selectedTickerDisplay.classList.add(HIDDEN_CLASS);
            runButton.setAttribute('disabled', 'disabled');
            delete searchInput.dataset.justSelected;
        }
    }

    function buildSuggestionItem(item) {
        const { label, symbol, logo } = item;
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'search-result';
        button.dataset.symbol = symbol;
        button.dataset.label = label;
        button.addEventListener('click', () => {
            setSelectedTicker(symbol, label);
            searchInput.value = label;
            clearResultsList();
        });

        if (logo) {
            const img = document.createElement('img');
            img.className = 'search-result__logo';
            img.src = logo;
            img.alt = `${symbol} logo`;
            button.appendChild(img);
        }

        const span = document.createElement('span');
        span.className = 'search-result__label';
        span.textContent = label;
        button.appendChild(span);

        const li = document.createElement('li');
        li.appendChild(button);
        return li;
    }

    function renderSearchResults(items) {
        searchResults.innerHTML = '';
        if (!items.length) {
            clearResultsList('No matches found.');
            return;
        }
        const fragment = document.createDocumentFragment();
        items.forEach((item) => {
            fragment.appendChild(buildSuggestionItem(item));
        });
        searchResults.appendChild(fragment);
        searchResults.classList.remove(HIDDEN_CLASS);
    }

    function abortOngoingSearch() {
        if (state.searchAbortController) {
            state.searchAbortController.abort();
            state.searchAbortController = null;
        }
    }

    function getCachedResults(cacheKey) {
        if (searchCache.has(cacheKey)) {
            return searchCache.get(cacheKey);
        }
        for (let i = cacheKey.length; i >= MIN_QUERY_LENGTH; i -= 1) {
            const prefix = cacheKey.slice(0, i);
            if (searchCache.has(prefix)) {
                return searchCache.get(prefix);
            }
        }
        return null;
    }

    let debounceTimer = null;
    function handleSearchInput(event) {
        const query = event.target.value.trim();
        const cacheKey = query.toLowerCase();
        state.currentQuery = cacheKey;
        delete searchInput.dataset.justSelected;

        if (query !== state.selectedLabel) {
            setSelectedTicker(null, null);
        }

        abortOngoingSearch();
        if (debounceTimer) {
            window.clearTimeout(debounceTimer);
        }

        if (query.length < MIN_QUERY_LENGTH) {
            clearResultsList(query ? 'Keep typing to see matches (2+ characters).' : '');
            return;
        }

        const cached = getCachedResults(cacheKey);
        if (cached) {
            renderSearchResults(cached);
        }

        debounceTimer = window.setTimeout(async () => {
            const controller = new AbortController();
            state.searchAbortController = controller;
            if (!cached) {
                clearResultsList('Searching…');
            }
            try {
                const response = await fetch(`${config.searchEndpoint}?q=${encodeURIComponent(query)}`, {
                    method: 'GET',
                    signal: controller.signal,
                    headers: {
                        'Accept': 'application/json',
                    },
                });

                if (!response.ok) {
                    throw new Error(`Search failed (${response.status})`);
                }

                const data = await response.json();
                if (state.currentQuery !== cacheKey) {
                    return;
                }
                const results = Array.isArray(data) ? data : [];
                searchCache.set(cacheKey, results);
                renderSearchResults(results);
            } catch (error) {
                if (error.name === 'AbortError') {
                    return;
                }
                clearResultsList('Search is unavailable right now.');
                console.error('Search error', error);
            } finally {
                state.searchAbortController = null;
            }
        }, 110);
    }

    function renderTextBlock(container, text) {
        container.innerHTML = '';
        if (!text) {
            container.classList.add(MUTED_CLASS);
            container.textContent = 'No output provided.';
            return;
        }
        container.classList.remove(MUTED_CLASS);
        const paragraphs = String(text).trim().split(/\n\n+/);
        const fragment = document.createDocumentFragment();
        paragraphs.forEach((para) => {
            const paragraphNode = document.createElement('p');
            const lines = para.split('\n');
            lines.forEach((line, index) => {
                if (index > 0) {
                    paragraphNode.appendChild(document.createElement('br'));
                }
                paragraphNode.appendChild(document.createTextNode(line));
            });
            fragment.appendChild(paragraphNode);
        });
        container.appendChild(fragment);
    }

    function renderStats(stats) {
        traderStatsList.innerHTML = '';
        if (!stats || typeof stats !== 'object') {
            const item = document.createElement('li');
            item.className = MUTED_CLASS;
            item.textContent = 'No stats available.';
            traderStatsList.appendChild(item);
            return;
        }

        const fragment = document.createDocumentFragment();
        Object.entries(stats).forEach(([label, value]) => {
            const item = document.createElement('li');
            const labelSpan = document.createElement('span');
            labelSpan.className = 'stat-label';
            labelSpan.textContent = label;
            const valueSpan = document.createElement('span');
            valueSpan.className = 'stat-value';
            valueSpan.textContent = typeof value === 'number' ? value.toFixed(4) : String(value);
            item.appendChild(labelSpan);
            item.appendChild(valueSpan);
            fragment.appendChild(item);
        });
        traderStatsList.appendChild(fragment);
    }

    function toggleLoading(isLoading) {
        if (isLoading) {
            runButton.setAttribute('disabled', 'disabled');
            runButton.dataset.originalLabel = runButton.dataset.originalLabel || runButton.textContent;
            runButton.textContent = 'Running…';
        } else {
            runButton.textContent = runButton.dataset.originalLabel || 'Launch Intelligence';
            if (state.selectedTicker) {
                runButton.removeAttribute('disabled');
            }
        }
    }

    function abortOngoingRun() {
        if (state.runAbortController) {
            state.runAbortController.abort();
            state.runAbortController = null;
        }
    }

    async function handleRunAgents() {
        if (!state.selectedTicker) {
            return;
        }

        abortOngoingRun();
        const controller = new AbortController();
        state.runAbortController = controller;

        setStatus('info', `Running intelligence suite for ${state.selectedLabel || state.selectedTicker}…`);
        resultsPanel.classList.add(HIDDEN_CLASS);
        toggleLoading(true);

        try {
            const response = await fetch(config.runEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                },
                signal: controller.signal,
                body: JSON.stringify({
                    ticker: state.selectedTicker,
                    risk: riskSelect.value,
                    period: periodSelect.value,
                    freq: freqSelect.value,
                }),
            });

            if (!response.ok) {
                const payload = await response.json().catch(() => ({}));
                const message = payload.error || `Request failed (${response.status})`;
                throw new Error(message);
            }

            const data = await response.json();
            renderTextBlock(analystOutput, data.summary);
            renderTextBlock(strategistOutput, data.strategy);
            renderStats(data.traderStats);

            if (data.traderChart) {
                traderChart.src = data.traderChart;
                traderChart.classList.remove(HIDDEN_CLASS);
                traderChart.removeAttribute('aria-hidden');
            } else {
                traderChart.classList.add(HIDDEN_CLASS);
                traderChart.setAttribute('aria-hidden', 'true');
            }

            if (data.returnsChart) {
                returnsChart.src = data.returnsChart;
                returnsChart.classList.remove(HIDDEN_CLASS);
                returnsChart.removeAttribute('aria-hidden');
                returnsEmpty.classList.add(HIDDEN_CLASS);
            } else {
                returnsChart.classList.add(HIDDEN_CLASS);
                returnsChart.setAttribute('aria-hidden', 'true');
                returnsEmpty.classList.remove(HIDDEN_CLASS);
            }

            resultsPanel.classList.remove(HIDDEN_CLASS);
            setStatus('success', 'Analysis complete. Review the insights below.');
        } catch (error) {
            if (error.name === 'AbortError') {
                setStatus('info', 'Previous analysis cancelled.');
            } else {
                console.error('Run error', error);
                setStatus('error', error.message || 'Failed to run agents.');
            }
        } finally {
            toggleLoading(false);
            state.runAbortController = null;
        }
    }

    function handleDocumentClick(event) {
        if (!searchResults.contains(event.target) && event.target !== searchInput) {
            searchResults.classList.add(HIDDEN_CLASS);
        }
    }

    searchInput.addEventListener('input', handleSearchInput);
    searchInput.addEventListener('focus', () => {
        if (searchInput.dataset.justSelected === 'true') {
            searchInput.select();
            delete searchInput.dataset.justSelected;
        }
        if (searchResults.children.length > 0) {
            searchResults.classList.remove(HIDDEN_CLASS);
        }
    });
    document.addEventListener('click', handleDocumentClick);
    runButton.addEventListener('click', handleRunAgents);
})();
