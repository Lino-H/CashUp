/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_USER_API_URL: string
  readonly VITE_TRADING_API_URL: string
  readonly VITE_EXCHANGE_API_URL: string
  readonly VITE_ORDER_API_URL: string
  readonly VITE_MONITORING_API_URL: string
  readonly VITE_WS_URL: string
  readonly VITE_APP_NAME: string
  readonly VITE_APP_VERSION: string
  readonly VITE_APP_ENV: string
  readonly VITE_GATE_IO_API_KEY: string
  readonly VITE_GATE_IO_SECRET_KEY: string
  readonly VITE_JWT_SECRET_KEY: string
  readonly VITE_DEV_MODE: string
  readonly VITE_DEBUG: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}