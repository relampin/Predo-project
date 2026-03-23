# Jarvis Assistant

Assistente local estilo Jarvis para Windows, escrito em Python e preparado para usar um LLM local via Ollama.

Agora com memoria persistente por historico JSON + memoria vetorial via Chroma.
Tambem com interface por voz usando Whisper e resposta falada por TTS local ou ElevenLabs.

## Requisitos

- Python 3.11+
- Windows
- Ollama instalado e em execucao
- Modelo local baixado, por exemplo: `ollama pull llama3.1:8b`
- Modelo de embeddings local baixado, por exemplo: `ollama pull nomic-embed-text`
- Microfone configurado no Windows para usar o modo voz

## Instalacao

```powershell
cd C:\Projetos\Predo project\jarvis-assistant
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m playwright install chromium
```

Para usar ElevenLabs, configure `elevenlabs_api_key` e `elevenlabs_voice_id` em [`C:\Projetos\Predo project\jarvis-assistant\config.py`](C:\Projetos\Predo project\jarvis-assistant\config.py).

## Execucao

```powershell
python main.py
```

Para abrir a interface grafica desktop:

```powershell
python gui.py
```

A interface grafica inclui:
- cards de status para modo, voz, memoria e navegador
- cockpit do navegador com abrir URL, pesquisar, voltar e recarregar
- painel de memoria com fatos lembrados e interacoes recentes

## Executavel

O build do executavel grafico fica em:

```text
dist\Jarvis\Jarvis.exe
```

Para gerar novamente:

```powershell
python -m PyInstaller --noconfirm --clean --windowed --name Jarvis gui.py
```

## Estrutura

- `main.py`: loop principal e confirmacoes de seguranca
- `gui.py`: interface grafica desktop com chat, voz e controles rapidos
- `assistant_runtime.py`: motor compartilhado entre terminal e GUI
- `brain.py`: interpretacao de linguagem natural com Ollama e fallback heuristico
- `actions.py`: integracao entre intents, arquivos, SO e navegador
- `browser.py`: controlador reutilizavel do Playwright
- `memory.py`: historico, fatos e memoria vetorial persistente com Chroma
- `voice.py`: captura de voz com Whisper e resposta falada via TTS
- `config.py`: configuracao central

## Comandos de exemplo

```text
Voce> abra o chrome
Jarvis> Abrindo chrome.

Voce> meu nome e Pedro
Jarvis> Posso abrir sites, pesquisar, clicar em botoes, preencher formularios, abrir programas, lembrar fatos seus e executar comandos. Me diga o que deseja fazer.

Voce> qual e meu nome?
Jarvis> Seu nome e Pedro.

Voce> /voz
Jarvis> Modo alterado para voice.

Pressione Enter para falar ou digite /texto, /misto ou sair:
Ouvindo...
Usuario fala: pesquise sobre placas de video
Jarvis fala: Pesquisa por 'sobre placas de video' aberta no navegador.

Pressione Enter para falar ou digite /texto, /misto ou sair:
Ouvindo...
Usuario fala: abra o chrome
Jarvis fala: Abrindo chrome.

Voce> pesquise sobre placas de video
Jarvis> Pesquisa por 'sobre placas de video' aberta no navegador.

Voce> entre no YouTube e abra o primeiro video
Jarvis> YouTube aberto e primeiro video iniciado.

Voce> clique no botao Inscrever-se
Jarvis> Clique realizado no botao 'Inscrever-se'.

Voce> preencha o campo input[name="search_query"] com placas RTX 5070
Jarvis> Campo 'input[name="search_query"]' preenchido.

Voce> crie um arquivo chamado teste.txt
Jarvis> Arquivo criado em C:\Projetos\Predo project\jarvis-assistant\workspace\teste.txt.

Voce> escreva no arquivo teste.txt: Ola, Jarvis.
Voce confirmou a escrita em 'teste.txt'? [s/N]: s
Jarvis> Texto salvo em C:\Projetos\Predo project\jarvis-assistant\workspace\teste.txt.

Voce> leia o arquivo teste.txt
Jarvis> Conteudo de C:\Projetos\Predo project\jarvis-assistant\workspace\teste.txt:
Ola, Jarvis.

Voce> execute o script example_hello.py
Voce confirmou a execucao do script 'example_hello.py'? [s/N]: s
Jarvis> Script example_hello.py executado com codigo 0.
Saida:
Jarvis online

Voce> execute este codigo
Cole o codigo Python abaixo. Finalize com uma linha contendo apenas FIM.
print("Jarvis online")
FIM
Voce confirmou a execucao de codigo Python local? [s/N]: s
Jarvis> Codigo Python executado com codigo 0.
Saida:
Jarvis online

Voce> mova o mouse para 400, 300
Jarvis> Mouse movido para (400, 300).

Voce> digite Ola mundo
Voce confirmou que o Jarvis pode digitar no foco atual? [s/N]: s
Jarvis> Texto digitado: Ola mundo
```

## Observacoes

- Comandos potencialmente perigosos pedem confirmacao antes da execucao.
- O assistente registra logs em tempo real no terminal.
- O navegador e controlado com Playwright e a sessao fica reutilizavel durante a execucao.
- O Jarvis salva historico em `data/memory.json` e memoria semantica em `data/chroma/`.
- Fatos como nome e preferencias podem ser lembrados em conversas futuras.
- O Jarvis aceita `/texto`, `/voz` e `/misto` para alternar o modo de entrada.
- A interface grafica usa o mesmo motor do terminal e mostra confirmacoes criticas por janela modal.
- No modo voz, o fluxo e: usuario fala -> Whisper transcreve -> Jarvis interpreta -> executa -> responde com voz.
- O TTS local usa `pyttsx3` por padrao. ElevenLabs e opcional.
- Arquivos relativos sao criados em `workspace/`.
- Scripts de exemplo e scripts gerados ficam em `scripts/`.
