/**
 * Webpack配置文件
 * Webpack Configuration File
 */

const path = require('path');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const ImageMinimizerPlugin = require('image-webpack-loader');
const TerserPlugin = require('terser-webpack-plugin');
const CompressionPlugin = require('compression-webpack-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const webpack = require('webpack');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = (env) => {
  const isProduction = env === 'production';

  return {
    mode: isProduction ? 'production' : 'development',
    devtool: isProduction ? 'source-map' : 'eval-source-map',
    entry: {
      main: './src/index.tsx',
      styles: './src/styles/optimized.css',
    },
    
    output: {
      path: path.resolve(__dirname, 'build'),
      filename: '[name].[contenthash].js',
      chunkFilename: '[name].[contenthash].chunk.js',
      publicPath: '/',
      assetModuleFilename: 'static/media/[name].[hash][ext]',
      clean: true,
    },
    
    resolve: {
      extensions: ['.ts', '.tsx', '.js', '.jsx'],
      alias: {
        '@': path.resolve(__dirname, 'src'),
        '@components': path.resolve(__dirname, 'src/components'),
        '@pages': path.resolve(__dirname, 'src/pages'),
        '@hooks': path.resolve(__dirname, 'src/hooks'),
        '@services': path.resolve(__dirname, 'src/services'),
        '@utils': path.resolve(__dirname, 'src/utils'),
        '@styles': path.resolve(__dirname, 'src/styles'),
      },
    },
    
    module: {
      rules: [
        // TypeScript文件处理
        {
          test: /\.(ts|tsx)$/,
          exclude: /node_modules/,
          use: {
            loader: 'babel-loader',
            options: {
              presets: [
                '@babel/preset-env',
                '@babel/preset-react',
                '@babel/preset-typescript',
              ],
              plugins: [
                '@babel/plugin-transform-runtime',
                '@babel/plugin-proposal-class-properties',
                '@babel/plugin-proposal-object-rest-spread',
              ],
            },
          },
        },
        
        // JavaScript文件处理
        {
          test: /\.js$/,
          exclude: /node_modules/,
          use: {
            loader: 'babel-loader',
            options: {
              presets: [
                '@babel/preset-env',
                '@babel/preset-react',
              ],
            },
          },
        },
        
        // CSS文件处理
        {
          test: /\.css$/,
          use: [
            isProduction ? MiniCssExtractPlugin.loader : 'style-loader',
            'css-loader',
            {
              loader: 'postcss-loader',
              options: {
                postcssOptions: {
                  plugins: [
                    'autoprefixer',
                    'cssnano',
                    [
                      'postcss-preset-env',
                      {
                        stage: 3,
                        features: {
                          'nesting-rules': true,
                          'custom-properties': true,
                          'custom-media-queries': true,
                        },
                      },
                    ],
                  ],
                },
              },
            },
          ],
          sideEffects: true,
        },
        
        // 图片文件处理
        {
          test: /\.(png|jpg|jpeg|gif|webp|avif|svg)$/,
          type: 'asset',
          generator: {
            filename: 'images/[name].[hash][ext]',
            publicPath: 'auto',
          },
          parser: {
            dataUrlCondition: {
              maxSize: 10 * 1024, // 10KB
            },
          },
        },
        
        // 字体文件处理
        {
          test: /\.(woff|woff2|eot|ttf|otf)$/,
          type: 'asset/resource',
          generator: {
            filename: 'fonts/[name].[hash][ext]',
          },
        },
        
        // 字体图标处理
        {
          test: /\.svg$/,
          include: /node_modules/,
          type: 'asset/resource',
          generator: {
            filename: 'icons/[name].[hash][ext]',
          },
        },
        
        // JSON文件处理
        {
          test: /\.json$/,
          type: 'asset/resource',
          generator: {
            filename: 'json/[name].[hash][ext]',
          },
        },
      ],
    },
    
    optimization: {
      minimize: isProduction,
      minimizer: [
        new CssMinimizerPlugin({
          minimizerOptions: {
            preset: [
              'default',
              {
                discardComments: {
                  removeAll: true,
                },
                normalizeWhitespace: false,
                mergeRules: true,
                discardDuplicates: true,
                mergeMedia: true,
                removeEmpty: true,
                normalizePositions: true,
                normalizeDisplayProperties: true,
                normalizeFontWeights: true,
                normalizeOrigin: true,
                normalizeString: true,
                normalizeTimingFunctions: true,
                normalizeRepeatStyle: true,
                normalizePositions: true,
                normalizeUnicode: true,
                normalizeUrl: true,
                normalizeString: true,
                normalizeDisplayProperties: true,
                normalizeFontWeights: true,
                normalizeOrigin: true,
                normalizeTimingFunctions: true,
                normalizeRepeatStyle: true,
                normalizePositions: true,
                normalizeUnicode: true,
                normalizeUrl: true,
              },
            ],
          },
        }),
        new TerserPlugin({
          terserOptions: {
            compress: {
              drop_console: isProduction,
              drop_debugger: isProduction,
              pure_funcs: ['console.log'],
            },
            output: {
              comments: false,
            },
          },
          parallel: true,
        }),
      ],
      
      splitChunks: {
        chunks: 'all',
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            chunks: 'all',
            priority: 10,
          },
          common: {
            name: 'common',
            minChunks: 2,
            chunks: 'initial',
            priority: 5,
          },
          styles: {
            name: 'css-styles',
            test: /\.(css|less|scss)$/,
            chunks: 'all',
            enforce: true,
          },
          images: {
            name: 'images',
            test: /\.(png|jpg|jpeg|gif|webp|avif|svg)$/,
            chunks: 'all',
            priority: -10,
          },
        },
      },
      
      runtimeChunk: {
        name: 'runtime',
      },
      
      moduleIds: isProduction ? 'deterministic' : 'named',
      chunkIds: isProduction ? 'deterministic' : 'named',
    },
    
    plugins: [
      // 生成HTML文件
      new HtmlWebpackPlugin({
        template: './public/index.html',
        filename: 'index.html',
        minify: isProduction ? {
          removeComments: true,
          collapseWhitespace: true,
          removeRedundantAttributes: true,
          useShortDoctype: true,
          removeEmptyAttributes: true,
          removeStyleLinkTypeAttributes: true,
          keepClosingSlash: true,
          minifyCSS: true,
          minifyJS: true,
        } : false,
      }),
      
      // 压缩插件
      ...(isProduction ? [
        new CompressionPlugin({
          algorithm: 'gzip',
          test: /\.(js|css|html|svg)$/,
          threshold: 10240,
          minRatio: 0.8,
        }),
      ] : []),
      
      // 提取CSS
      new MiniCssExtractPlugin({
        filename: 'css/[name].[contenthash].css',
        chunkFilename: 'css/[name].[contenthash].chunk.css',
        ignoreOrder: true,
      }),
      
      // 清理构建目录
      new CleanWebpackPlugin(),
      
      // 定义环境变量
      new webpack.DefinePlugin({
        'process.env.NODE_ENV': JSON.stringify(isProduction ? 'production' : 'development'),
        'process.env.VERSION': JSON.stringify(require('./package.json').version),
        'window.ENV': {
          REACT_APP_ENABLE_AUTH: JSON.stringify(process.env.REACT_APP_ENABLE_AUTH || (isProduction ? 'true' : 'false')),
          REACT_APP_API_URL: JSON.stringify('/api'),
          REACT_APP_TRADING_URL: JSON.stringify('/api/trading'),
          REACT_APP_STRATEGY_URL: JSON.stringify('/api/strategy'),
          REACT_APP_NOTIFICATION_URL: JSON.stringify('/api/notification'),
          REACT_APP_WS_BASE_URL: JSON.stringify(process.env.REACT_APP_WS_BASE_URL || ''),
          REACT_APP_WS_TRADING_URL: JSON.stringify(process.env.REACT_APP_WS_TRADING_URL || '/ws/trading'),
          REACT_APP_WS_NEWS_URL: JSON.stringify(process.env.REACT_APP_WS_NEWS_URL || '/ws/news'),
          REACT_APP_WS_STRATEGY_URL: JSON.stringify(process.env.REACT_APP_WS_STRATEGY_URL || '/ws/strategy'),
          REACT_APP_WS_NOTIFICATION_URL: JSON.stringify(process.env.REACT_APP_WS_NOTIFICATION_URL || '/ws/notification'),
        },
      }),
    ],
    
    devServer: {
      port: 3000,
      hot: true,
      open: true,
      compress: true,
      historyApiFallback: true,
      static: {
        directory: path.join(__dirname, 'public'),
      },
      onBeforeSetupMiddleware: (devServer) => {
        if (!devServer) {
          throw new Error('webpack-dev-server is not defined');
        }

        const http = require('http');
        const { createProxyMiddleware } = require('http-proxy-middleware');

        devServer.app.use('/api/core', createProxyMiddleware({
          target: 'http://localhost:8001',
          changeOrigin: true,
          pathRewrite: {
            '^/api/core': ''
          },
          secure: false,
        }));

        devServer.app.use('/api/trading', createProxyMiddleware({
          target: 'http://localhost:8002',
          changeOrigin: true,
          pathRewrite: {
            '^/api/trading': ''
          },
          secure: false,
        }));

        devServer.app.use('/api/strategy', createProxyMiddleware({
          target: 'http://localhost:8003',
          changeOrigin: true,
          pathRewrite: {
            '^/api/strategy': ''
          },
          secure: false,
        }));

        devServer.app.use('/api/notification', createProxyMiddleware({
          target: 'http://localhost:8004',
          changeOrigin: true,
          pathRewrite: {
            '^/api/notification': ''
          },
          secure: false,
        }));

        // WebSocket代理
        devServer.app.use('/ws/trading', createProxyMiddleware({
          target: 'http://localhost:8002',
          changeOrigin: true,
          ws: true,
          secure: false,
        }));

        devServer.app.use('/ws/news', createProxyMiddleware({
          target: 'http://localhost:8004',
          changeOrigin: true,
          ws: true,
          secure: false,
        }));

        devServer.app.use('/ws/strategy', createProxyMiddleware({
          target: 'http://localhost:8003',
          changeOrigin: true,
          ws: true,
          secure: false,
        }));

        devServer.app.use('/ws/notification', createProxyMiddleware({
          target: 'http://localhost:8004',
          changeOrigin: true,
          ws: true,
          secure: false,
        }));
      },
      proxy: {
        '/api/core': {
          target: 'http://localhost:8001',
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/api\/core/, ''),
        },
        '/api/trading': {
          target: 'http://localhost:8002',
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/api\/trading/, ''),
        },
        '/api/strategy': {
          target: 'http://localhost:8003',
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/api\/strategy/, ''),
        },
        '/api/notification': {
          target: 'http://localhost:8004',
          changeOrigin: true,
          secure: false,
          rewrite: (path) => path.replace(/^\/api\/notification/, ''),
        },
        '/api': {
          target: 'http://localhost:8001',
          changeOrigin: true,
          secure: false,
        },
      },
      headers: {
        'X-Content-Type-Options': 'nosniff',
        'X-Frame-Options': 'DENY',
        'X-XSS-Protection': '1; mode=block',
      },
    },
    
    performance: {
      hints: isProduction ? 'warning' : false,
      maxAssetSize: 244 * 1024, // 244KB
      maxEntrypointSize: 244 * 1024, // 244KB
      assetFilter: (assetFilename) => {
        return assetFilename.endsWith('.js');
      },
    },
    
    cache: {
      type: 'filesystem',
      buildDependencies: {
        config: [__filename],
      },
      name: isProduction ? 'production' : 'development',
    },
    
    stats: {
      colors: true,
      modules: false,
      chunks: false,
      chunkModules: false,
    },
  };
};