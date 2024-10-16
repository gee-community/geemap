// Karma configuration file, see link for more information
// https://karma-runner.github.io/1.0/config/configuration-file.html

process.env.CHROME_BIN = require('puppeteer').executablePath();

module.exports = function (config) {
  config.set({
    basePath: '',
    frameworks: [
      'jasmine',
      'karma-typescript',
    ],
    files: [
        { pattern: 'tests/**/*.spec.ts', watched: true }
    ],
    preprocessors: {
        "**/*.ts": "karma-typescript",
    },
    plugins: [
      'karma-jasmine',
      'karma-chrome-launcher',
      'karma-jasmine-html-reporter',
      'karma-typescript',
    ],
    client: {
      clearContext: false, // leave Jasmine Spec Runner output visible in browser
      jasmine: {
        "helpers": ["./node_modules/jasmine-expect/index.js"],
        "stopSpecOnExpectationFailure": false,
        "random": true
      }
    },
    karmaTypescriptConfig: {
      tsconfig: './tsconfig.json'
    },
    reporters: ['progress', 'kjhtml'],
    port: 9876,
    colors: true,
    logLevel: config.LOG_INFO,
    autoWatch: true,
    browsers: ['Chrome'],
    singleRun: false,
    restartOnFileChange: true,
    customLaunchers: {
      ChromeHeadlessNoSandbox: {
        base: 'ChromeHeadless',
        flags: ['--no-sandbox'],
      },
    },
  });
};