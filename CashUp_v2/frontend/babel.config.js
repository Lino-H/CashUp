module.exports = {
  presets: [
    [
      '@babel/preset-env',
      {
        targets: {
          browsers: ['last 2 versions', 'not dead'],
        },
        useBuiltIns: 'usage',
        corejs: 3,
      },
    ],
    '@babel/preset-react',
  ],
  plugins: [
    '@babel/plugin-proposal-class-properties',
    '@babel/plugin-proposal-object-rest-spread',
  ],
  env: {
    test: {
      presets: [
        '@babel/preset-env',
        '@babel/preset-react',
      ],
    },
  },
};