/// <reference types="vite/client" />

// Augment the ImportMetaEnv interface from vite/client
declare global {
  interface ImportMetaEnv {
    readonly VITE_API_URL?: string
    // Add more env variables here as needed
  }
}

declare module '*.png' {
    const content: string;
    export default content;
}

declare module '*.jpg' {
    const content: string;
    export default content;
}

declare module '*.svg' {
    const content: string;
    export default content;
}

export {}
