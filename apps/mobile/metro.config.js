// Learn more https://docs.expo.io/guides/customizing-metro
const { getDefaultConfig } = require('expo/metro-config');
const path = require('path');
const fs = require('fs');

const projectRoot = __dirname;
const monorepoRoot = path.resolve(projectRoot, '../..');

const config = getDefaultConfig(projectRoot);

// 1. Watch all files within the monorepo workspace
config.watchFolders = [monorepoRoot];

// 2. Let Metro know where to resolve packages and in what order
const nodeModulesPaths = [path.resolve(projectRoot, 'node_modules')];
const rootNodeModules = path.resolve(monorepoRoot, 'node_modules');
if (fs.existsSync(rootNodeModules)) {
  nodeModulesPaths.push(rootNodeModules);
}
config.resolver.nodeModulesPaths = nodeModulesPaths;

// 3. Monorepo workspace package aliases
const contractsDir = path.resolve(monorepoRoot, 'packages/contracts');
config.resolver.extraNodeModules = {
  '@msgi-one/contracts': contractsDir,
  '@msgi/contracts': contractsDir,
};

module.exports = config;
