const sharp = require('sharp');
const path = require('path');
const fs = require('fs');

const SOURCE_FILE = path.resolve(__dirname, '../../../identity/logo/dpd-logo.svg');
const DEST_DIR = path.resolve(__dirname, '../images');
const SIZES = [16, 32, 64, 128];

if (!fs.existsSync(SOURCE_FILE)) {
    console.error(`Source file not found: ${SOURCE_FILE}`);
    process.exit(1);
}

if (!fs.existsSync(DEST_DIR)) {
    fs.mkdirSync(DEST_DIR, { recursive: true });
}

async function generateIcons() {
    console.log(`Generating icons from ${SOURCE_FILE}...`);
    
    for (const size of SIZES) {
        const destFile = path.join(DEST_DIR, `dpd-logo_${size}.png`);
        try {
            await sharp(SOURCE_FILE)
                .resize(size, size)
                .png()
                .toFile(destFile);
            console.log(`Generated ${destFile}`);
        } catch (error) {
            console.error(`Error generating ${size}x${size} icon:`, error);
            process.exit(1);
        }
    }
}

generateIcons();
