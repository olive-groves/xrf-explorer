#!/usr/bin/env node
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

// ========= CONFIGURATION =========
const frontendDirs = [
    './xrf_explorer/client/src/components/image-viewer', 
    './xrf_explorer/client/src/components/menus', 
    './xrf_explorer/client/src/components/workspace',
    './xrf_explorer/client/src/lib',
    './xrf_explorer/client/src/windows'
]; // all frontend folders containing .vue files
const backendDirs = ['./xrf_explorer/server']; // all backend folders containing .py files
const tmpDir = './.simian-temp'; // temporary folder for extracted code

// Files to exclude (regex patterns)
const excludePatterns = [
    /__init__\.py$/,  // exclude all __init__.py files
    /index\.ts$/      // exclude all index.ts files
];
// =================================

// Prepare temp folder
if (!fs.existsSync(tmpDir)) fs.mkdirSync(tmpDir, { recursive: true });
fs.readdirSync(tmpDir).forEach(f => fs.unlinkSync(path.join(tmpDir, f)));

// Utility function to check if a file should be excluded
function isExcluded(file) {
    return excludePatterns.some(pattern => pattern.test(file));
}

// Extract TypeScript code from Vue files
function extractTS(filePath) {
    const content = fs.readFileSync(filePath, 'utf8');
    const matches = content.match(/<script\s+lang=["']ts["'][^>]*>([\s\S]*?)<\/script>/gi);
    if (!matches) return null;
    return matches.map(m => {
        const inner = m.match(/<script\s+lang=["']ts["'][^>]*>([\s\S]*?)<\/script>/i);
        return inner ? inner[1] : '';
    }).join('\n\n');
}

// Recursively process directories for Vue files
function processVueDir(dir) {
    fs.readdirSync(dir).forEach(file => {
        const fullPath = path.join(dir, file);
        if (fs.statSync(fullPath).isDirectory()) return processVueDir(fullPath);
        
        // Skip excluded files
        if (isExcluded(file)) return;

        if (file.endsWith('.vue')) {
            const tsCode = extractTS(fullPath);
            if (tsCode) {
                const outFile = path.join(tmpDir, file.replace('.vue', '.ts'));
                fs.writeFileSync(outFile, tsCode, 'utf8');
            }
        }
    });
}

// Recursively process directories for Python files
function processPythonDir(dir) {
    fs.readdirSync(dir).forEach(file => {
        const fullPath = path.join(dir, file);
        if (fs.statSync(fullPath).isDirectory()) return processPythonDir(fullPath);
        
        // Skip excluded files
        if (isExcluded(file)) return;
        
        if (file.endsWith('.py')) {
            const destFile = path.join(tmpDir, path.basename(file));
            fs.copyFileSync(fullPath, destFile);
        }
    });
}

// Run Simian
function runSimian() {
    console.log('Running Simian on all extracted TS and Python code...');
    try {
        execSync(`java -jar simian.jar -includes="*.ts,*.py" ${tmpDir}`, { stdio: 'inherit' });
    } catch (err) {
        // Simian returns non-zero if duplicates are found
    }
}

// Clean up temp folder
function cleanUp() {
    fs.readdirSync(tmpDir).forEach(f => fs.unlinkSync(path.join(tmpDir, f)));
    fs.rmdirSync(tmpDir);
}

// ===== EXECUTION =====
frontendDirs.forEach(dir => processVueDir(dir));
backendDirs.forEach(dir => processPythonDir(dir));
runSimian();
cleanUp();
console.log('Done!');
