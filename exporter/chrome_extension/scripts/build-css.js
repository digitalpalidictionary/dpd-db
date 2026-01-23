const fs = require('fs');
const path = require('path');

const IDENTITY_CSS_DIR = path.resolve(__dirname, '../../../identity/css');
const DEST_DIR = path.resolve(__dirname, '../css');
const SCOPE_ID = '#dict-panel-25445';

const FILES_TO_PROCESS = [
    'dpd.css',
    'dpd-variables.css'
];

/**
 * Scopes CSS by prefixing selectors with SCOPE_ID.
 * Handles comma-separated selectors and basic @rules.
 */
function scopeCSS(css, scope) {
    // 1. Handle :root and body - they become the scope itself
    css = css.replace(/:root/g, scope);
    css = css.replace(/\bbody\b/g, scope);

    // 2. Process blocks
    // This is a simplified parser that handles flat CSS structure
    const blocks = css.split('}');
    const processedBlocks = blocks.map(block => {
        const parts = block.split('{');
        if (parts.length !== 2) return block;

        const selectorList = parts[0];
        const content = parts[1];

        // Skip @rules like @keyframes, @media (simplified)
        if (selectorList.trim().startsWith('@')) {
            return block; 
        }

        const scopedSelectors = selectorList.split(',')
            .map(selector => {
                const s = selector.trim();
                if (!s) return s;
                // If the selector is already the scope, don't prefix
                if (s === scope || s.startsWith(scope + ' ') || s.startsWith(scope + '.')) {
                    return s;
                }
                return `${scope} ${s}`;
            })
            .join(', ');

        return `${scopedSelectors} {${content}`;
    });

    return processedBlocks.join('}\n');
}

if (!fs.existsSync(DEST_DIR)) {
    fs.mkdirSync(DEST_DIR, { recursive: true });
    console.log(`Created directory: ${DEST_DIR}`);
}

FILES_TO_PROCESS.forEach(file => {
    const src = path.join(IDENTITY_CSS_DIR, file);
    const dest = path.join(DEST_DIR, file);

    try {
        if (!fs.existsSync(src)) {
            console.error(`Source file not found: ${src}`);
            process.exit(1);
        }
        
        const originalCss = fs.readFileSync(src, 'utf8');
        const scopedCss = scopeCSS(originalCss, SCOPE_ID);
        
        fs.writeFileSync(dest, scopedCss);
        console.log(`Scoped and copied ${file} to ${DEST_DIR}`);
    } catch (err) {
        console.error(`Error processing ${file}:`, err);
        process.exit(1);
    }
});
