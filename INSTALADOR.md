# Como Criar o Instalador .exe do Legis Beta

---

## PASSO 1 — Compilar o executável

No terminal do PyCharm (ou PowerShell dentro da pasta Legis):
```
build_windows.bat
```
Aguarde 3–5 minutos. O executável será gerado em `dist\Legis\Legis.exe`.

---

## PASSO 2 — Instalar o Inno Setup

Baixe gratuitamente:
→ https://jrsoftware.org/isdl.php

Durante a instalação marque **"Install Inno Setup Preprocessor"**.

---

## PASSO 3 — Gerar o instalador

1. Abra o **Inno Setup**
2. Clique em **File → Open** e abra `legis_setup.iss`
3. Pressione **F9** (Build → Compile)
4. O instalador será gerado em:
```
Output\Legis_Beta_Setup.exe
```

---

## RESULTADO FINAL

O `Legis_Beta_Setup.exe` instala o sistema com:
- ✅ Ícone personalizado (Themis dourada)
- ✅ Atalho na Área de Trabalho
- ✅ Atalho no Menu Iniciar
- ✅ Aparece no "Adicionar ou remover programas"
- ✅ Abre automaticamente após instalar
- ✅ Funciona sem Python instalado
- ✅ Windows 10 ou superior

---

## Para atualizar versões futuras

Atualize `#define MyAppVersion "1.0"` no `legis_setup.iss` e repita os passos.
