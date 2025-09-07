import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/optimized.css';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

// 初始化主题
const initTheme = () => {
  const savedTheme = localStorage.getItem('theme') || 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);
};

// 初始化主题
initTheme();

root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);