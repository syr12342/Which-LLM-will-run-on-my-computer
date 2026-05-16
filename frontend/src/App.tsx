// Main App Component

import React, { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Calculator from './components/Calculator';
import './App.css';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="app">
        <header className="app-header">
          <h1>🚀 LLM Router & Matching Platform</h1>
          <p className="subtitle">
            Calculate VRAM requirements and find compatible hardware for Large Language Models
          </p>
        </header>
        
        <main className="app-main">
          <Calculator />
        </main>
        
        <footer className="app-footer">
          <p>Production-ready LLM Hardware Matching System</p>
        </footer>
      </div>
    </QueryClientProvider>
  );
}

export default App;
