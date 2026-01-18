const fs = require('fs');
const path = require('path');

const IDENTITY_CSS_DIR = path.resolve(__dirname, '../../../identity/css');
const DEST_DIR = path.resolve(__dirname, '../css');

const FILES_TO_COPY = [
    'dpd.css',
    'dpd-variables.css'
];

if (!fs.existsSync(DEST_DIR)) {
    fs.mkdirSync(DEST_DIR, { recursive: true });
    console.log(`Created directory: ${DEST_DIR}`);
}

FILES_TO_COPY.forEach(file => {
    const src = path.join(IDENTITY_CSS_DIR, file);
    const dest = path.join(DEST_DIR, file);

    try {
        if (!fs.existsSync(src)) {
            console.error(`Source file not found: ${src}`);
            process.exit(1);
        }
        fs.copyFileSync(src, dest);
        console.log(`Copied ${file} to ${DEST_DIR}`);
    } catch (err) {
        console.error(`Error copying ${file}:`, err);
        process.exit(1);
    }
});
