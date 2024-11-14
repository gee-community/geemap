// Karma configuration file, see link for more information
// https://karma-runner.github.io/1.0/config/configuration-file.html
process.env.CHROME_BIN = require('puppeteer').executablePath();

// test/karma.conf.js
module.exports = config => {
  config.set({
    frameworks: ['jasmine', 'webpack'],
    basePath: '',
    type: 'module',
    files: [
      {pattern: 'js/*.ts', type:'module'},
      {pattern: 'tests/*.spec.ts', type:'module'},
    ],
    exclude: [],
    client: {
      clearContext: false, // leave Jasmine Spec Runner output visible in browser
    },
    preprocessors: {
      '**/*.ts': ['webpack'],
    },
    webpack: {
      mode: 'development',
      devtool: 'inline-source-map',
      module: {
        rules: [
          {
            test: /\.ts$/,
            loader: "ts-loader",
            exclude: /node_modules/,
            options: {
              configFile: "tsconfig.webpack.json"
            }
          },
        ],
      },
      resolve: {
        extensions: ['.ts'],
      },
      stats: {
          colors: true,
          modules: true,
          reasons: true,
          errorDetails: true
      },
    },
    reporters: ['spec', 'progress', 'kjhtml'],
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