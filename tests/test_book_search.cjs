// Exercise the real generated mdBook index and its bundled search engine.
// No package installation or browser is needed: node tests/test_book_search.cjs build/book
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const directory = process.argv[2] || 'build/book';
const context = {console, search: {}, document: {addEventListener() {}}};
context.window = context;
vm.createContext(context);
for (const file of ['elasticlunr.min.js', 'docs/book/assets/enhancements.js', 'searchindex.js']) {
    vm.runInContext(fs.readFileSync(path.join(directory, file), 'utf8'), context, {filename: file});
}
const index = context.elasticlunr.Index.load(context.search.index);
for (const query of ['起動上限', 'タスク', '証明', 'ChainTask', '起動上限 ChainTask', '起動上限　ＣｈａｉｎＴａｓｋ']) {
    const results = index.search(query, context.search.search_options);
    assert(results.length > 0, `No results for ${query}`);
    for (const result of results) {
        assert(context.search.doc_urls[Number(result.ref)], `No page link for ${query}`);
        assert.equal(typeof result.doc.body, 'string', `No result teaser for ${query}`);
        assert.equal(typeof result.doc.breadcrumbs, 'string', `No result title for ${query}`);
    }
    console.log(`PASS search: ${query} (${results.length} sections)`);
}
assert.equal(index.search('存在しない検索語zz987654321').length, 0);
console.log('PASS search: no results for an absent term');
