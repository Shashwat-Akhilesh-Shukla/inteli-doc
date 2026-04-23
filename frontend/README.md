# 🖥️ Intelligent Doc Navigator - Frontend
**Premium Glassmorphic UI for Agentic RAG**

The frontend of the Intelligent Documentation Navigator is a high-performance React application built with **Vite** and **TypeScript**. It features a modern, "glassmorphic" design language with real-time WebSocket streaming and interactive state tracking.

## ✨ UI Features

- **Live Thought Process:** A dedicated sidebar/dashboard that maps the backend agent's state machine (Routing → Retrieving → Evaluating → Generating) in real-time.
- **Asynchronous Token Streaming:** Responses are rendered word-by-word as they arrive from the LLM, providing a smooth, zero-latency feel.
- **Interactive Citations:** Hover over source chips to see exact document references and context snippets.
- **Glassmorphic Aesthetic:** Deep translucent backgrounds, subtle borders, and fluid micro-animations using pure CSS.

## 🚀 Getting Started

### Prerequisites
- Node.js `v20+`
- `npm` or `yarn`

### Installation

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Start the development server:**
   ```bash
   npm run dev
   ```

3. **Build for production:**
   ```bash
   npm run build
   ```

## 🏗️ Architecture

- **React 19:** Leveraging the latest features for UI state management.
- **Vite:** Blazing fast builds and Hot Module Replacement (HMR).
- **WebSockets:** Native HTML5 WebSocket API used for bi-directional streaming.
- **CSS Modules:** Scoped, maintainable styles with a focus on custom properties (CSS variables).

## 📂 Key Components

- `App.tsx`: Main layout and message orchestration.
- `useWebSocket.ts`: Custom hook for managing the socket lifecycle and message buffering.
- `ThoughtProcess/`: Components for visualizing the agentic loop phases.
- `ChatMessage/`: Renders LLM responses with markdown and citations.

## 🎨 Styling Philosophy

We avoid utility-first frameworks like Tailwind in favor of **Vanilla CSS** to achieve a highly bespoke, premium look. Global tokens are defined in `src/index.css`.

---

<sub>Part of the Intelligent Documentation Navigator ecosystem.</sub>
