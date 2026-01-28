# LinkedIn Bot - Aplicativo Desktop

## Requisitos

- Node.js 18+
- Python 3.10+
- Chrome instalado

## Desenvolvimento

1. Instale as dependências do Electron:
```bash
cd electron
npm install
```

2. Inicie o backend (em um terminal):
```bash
cd ..
.\venv\Scripts\python.exe -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8002
```

3. Inicie o frontend (em outro terminal):
```bash
cd frontend
npm run dev
```

4. Inicie o Electron:
```bash
cd electron
npm run dev
```

## Build para Produção

### Windows
```bash
cd electron
npm run build:win
```

O instalador será gerado em `electron/dist/`.

### macOS
```bash
npm run build:mac
```

### Linux
```bash
npm run build:linux
```

## Estrutura

```
electron/
├── main.js          # Processo principal do Electron
├── preload.js       # Script de preload (segurança)
├── package.json     # Configuração do Electron
├── assets/          # Ícones do aplicativo
│   ├── icon.png     # Linux (512x512)
│   ├── icon.ico     # Windows
│   └── icon.icns    # macOS
└── dist/            # Builds gerados
```

## Notas Importantes

- O aplicativo empacota o backend Python e frontend Next.js
- O Chrome/Chromium é necessário no sistema do usuário para o bot funcionar
- As credenciais do LinkedIn são armazenadas localmente de forma criptografada
