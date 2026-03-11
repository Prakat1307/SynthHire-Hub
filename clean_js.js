const fs = require('fs');
const path = require('path');
const decomment = require('decomment');

function cleanFrontend(dir) {
    const files = fs.readdirSync(dir);
    for (const file of files) {
        const fullPath = path.join(dir, file);
        if (fullPath.includes('node_modules') || fullPath.includes('.next') || fullPath.includes('.git')) {
            continue;
        }
        if (fs.statSync(fullPath).isDirectory()) {
            cleanFrontend(fullPath);
        } else if (fullPath.endsWith('.js') || fullPath.endsWith('.ts') || fullPath.endsWith('.tsx') || fullPath.endsWith('.jsx') || fullPath.endsWith('.css')) {
            try {
                const code = fs.readFileSync(fullPath, 'utf8');
                const cleaned = decomment(code, {
                    safe: true,
                    space: true
                });
                if (cleaned !== code) {
                    fs.writeFileSync(fullPath, cleaned, 'utf8');
                    console.log(`Cleaned ${fullPath}`);
                }
            } catch (e) {
                console.log(`Failed to clean ${fullPath}: ${e.message}`);
            }
        }
    }
}

console.log("Starting JS/TS/CSS cleanup...");
cleanFrontend(path.resolve("d:/SynthHire-Interview-Platform/frontend"));
console.log("JS/TS/CSS cleanup done.");
