@echo off
REM ============================================================
REM  ABRIR O ESCUDO FEMININO (com a Lia) -- basta dar dois cliques.
REM  1. baixa a versao mais nova do GitHub (se nao der, segue assim mesmo)
REM  2. liga o painel numa janela minimizada (nao feche essa janela)
REM  3. espera o painel ficar pronto e abre o navegador
REM  Para fechar o painel: feche a janela "Escudo Feminino - painel".
REM ============================================================
title Escudo Feminino - abrindo a Lia
cd /d "%~dp0"

echo Atualizando o Escudo Feminino...
git pull --quiet 2>nul || echo Nao deu para atualizar agora - abrindo a versao deste computador.

REM Sem curl (Windows antigo): liga o painel, espera 10 s e abre.
where curl >nul 2>nul || goto sem_curl

REM Se o painel ja estiver aberto, so abre o navegador de novo.
curl -s -o nul http://localhost:8600/_stcore/health && goto abrir

echo Ligando o painel...
start "Escudo Feminino - painel" /min cmd /k py -m streamlit run dashboard\app.py --server.port 8600 --server.headless true

set /a tentativas=0
:esperar
set /a tentativas+=1
curl -s -o nul http://localhost:8600/_stcore/health && goto abrir
if %tentativas% geq 60 goto demorou
timeout /t 1 /nobreak >nul
goto esperar

:abrir
start "" http://localhost:8600
exit

:sem_curl
echo Ligando o painel...
start "Escudo Feminino - painel" /min cmd /k py -m streamlit run dashboard\app.py --server.port 8600 --server.headless true
timeout /t 10 /nobreak >nul
goto abrir

:demorou
echo.
echo O painel demorou mais de 1 minuto para ligar.
echo Abra a janela "Escudo Feminino - painel" na barra de tarefas para ver a mensagem de erro.
pause
