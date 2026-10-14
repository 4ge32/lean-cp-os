// mdBook's English tokenizer cannot find Japanese words embedded in a sentence.
// Keep its UI, result links, keyboard handling and Latin search. For Japanese
// queries, search the same generated section documents by normalized substring.
(() => {
    if (!window.elasticlunr) return;
    const originalSearch = window.elasticlunr.Index.prototype.search;
    const normalize = value => String(value || '').normalize('NFKC').toLowerCase();
    window.elasticlunr.Index.prototype.search = function (query, options) {
        if (!/[\u3040-\u30ff\u3400-\u9fff]/u.test(query)) {
            return originalSearch.call(this, query, options);
        }
        const terms = normalize(query).trim().split(/\s+/u).filter(Boolean);
        if (!terms.length) return [];
        return Object.entries(this.documentStore.docs).flatMap(([ref, doc]) => {
            const title = normalize(doc.title);
            const body = normalize(doc.body);
            const text = title + ' ' + body + ' ' + normalize(doc.breadcrumbs);
            if (!terms.every(term => text.includes(term))) return [];
            const score = terms.reduce((sum, term) => sum + (title.includes(term) ? 10 : 1), 0);
            return [{ref, score, doc}];
        }).sort((left, right) => right.score - left.score || Number(left.ref) - Number(right.ref));
    };
})();

// Give native mdBook controls Japanese labels without changing keyboard behavior.
document.addEventListener('DOMContentLoaded', () => {
    const controls = {
        'sidebar-toggle': '章の目次を開く・閉じる',
        'theme-toggle': '配色を選ぶ',
        'search-toggle': '本文を検索する',
        'searchbar': '本文を検索する',
    };
    for (const [id, label] of Object.entries(controls)) {
        const element = document.getElementById(id);
        if (element) {
            element.setAttribute('aria-label', label);
            element.setAttribute('title', label);
        }
    }
    const search = document.getElementById('searchbar');
    if (search) search.placeholder = '用語・関数名・章の内容を検索…';
    const metrics = document.getElementById('searchresults-header');
    if (metrics) {
        const translate = () => {
            const text = metrics.textContent;
            const found = text.match(/^(\d+) search results? for '([\s\S]*)':$/);
            const none = text.match(/^No search results for '([\s\S]*)'\.$/);
            if (found) metrics.textContent = `「${found[2]}」の検索結果：${found[1]}件`;
            else if (none) metrics.textContent = `「${none[1]}」に一致する項目はありません`;
        };
        new MutationObserver(translate).observe(metrics, {childList: true, characterData: true, subtree: true});
        translate();
    }
    document.querySelectorAll('a[rel~="prev"]').forEach(e => e.setAttribute('aria-label', '前の章へ'));
    document.querySelectorAll('a[rel~="next"]').forEach(e => e.setAttribute('aria-label', '次の章へ'));
});
