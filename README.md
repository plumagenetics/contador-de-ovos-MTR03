# Contador MTR03 — Instalador Windows

Este projeto contém os arquivos necessários para **empacotar e distribuir**
o aplicativo **Contador MTR03 — Produção de Ovos** como um **instalador Windows (.exe)**,
utilizando **Inno Setup**.

O aplicativo é desenvolvido em **Python + Streamlit**, porém o **usuário final não precisa**
instalar Python, bibliotecas ou executar comandos técnicos.

---

## 📦 O que o instalador faz

Ao executar o instalador, o sistema:

- Instala o aplicativo sem exigir permissões de administrador
- Copia todos os arquivos necessários (código + ambiente Python)
- Cria atalho no **Menu Iniciar**
- (Opcional) Cria atalho na **Área de Trabalho**
- Abre o navegador automaticamente ao iniciar o app

---

## 📁 Estrutura obrigatória do projeto

Antes de gerar o instalador, a estrutura **deve ser exatamente esta**:

```text
contador-de-ovos-MTR03/
│
├── run.bat
├── icone.ico
├── requirements.txt
│
├── .venv/
│   └── Scripts/
│       └── activate.bat
│
└── app/
    ├── app.py
    ├── launcher.py
    └── src/
        ├── pdf_reader.py
        ├── interval_logic.py
        └── excel_export.py

⚠️ Importante

A pasta do ambiente virtual precisa se chamar .venv exatamente com esse nome.

▶️ Arquivo de inicialização (run.bat)

O run.bat é o ponto de entrada do aplicativo e deve estar na raiz do projeto:
@echo off
setlocal

cd /d "%~dp0"

call "%~dp0.venv\Scripts\activate.bat"
python "%~dp0app\launcher.py"

endlocal

🧰 Ferramentas necessárias (somente para quem gera o instalador)

Na máquina de build (desenvolvedor):
Python (para criar o .venv)
Inno Setup Compiler (gratuito)

➡️ O usuário final não precisa de nenhuma dessas ferramentas.

📝 Script do instalador (.iss)

O arquivo Contador_MTR03.iss é o script do Inno Setup responsável por:
Copiar todos os arquivos do app
Criar atalhos
Definir ícone
Gerar o instalador final

Exemplos de caminhos no .iss
Source: "C:\Build_Contador_MTR03\Contador_MTR03_App\*"
SetupIconFile=C:\Build_Contador_MTR03\Contador_MTR03_App\icone.ico
OutputDir=C:\Build_Contador_MTR03\Output

Ajuste os caminhos conforme o local real do projeto na sua máquina.

🏗️ Como gerar o instalador

Abra o Inno Setup Compiler
Abra o arquivo Contador_MTR03.iss
Clique em Compile
Aguarde a mensagem Compile successful

O instalador será gerado em:
C:\Build_Contador_MTR03\Output\
Instalador_Contador_MTR03.exe

🧪 Como testar o instalador

Execute Instalador_Contador_MTR03.exe
Conclua a instalação
Abra o aplicativo pelo atalho Contador MTR03
➡️ O navegador deve abrir automaticamente com o sistema funcionando.

🛠️ Solução de problemas

O aplicativo não abre
Verifique se a pasta .venv foi copiada corretamente
Confirme que o run.bat está na raiz da pasta instalada
Confira se o antivírus não bloqueou arquivos .pyd

Porta ocupada / erro 404
O launcher.py seleciona portas automaticamente
Não abra manualmente localhost:8501
Utilize apenas o atalho criado pelo instalador

🔒 Permissões e segurança

O instalador não exige privilégios de administrador
O app é instalado em: %APPDATA%\Contador MTR03\

📌 Observações finais

Este modelo de instalação é robusto e reproduzível
Atualizações futuras podem ser feitas gerando um novo instalador
O uso de .venv garante consistência entre diferentes máquinas

