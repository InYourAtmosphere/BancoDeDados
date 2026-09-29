@echo off
chcp 65001 > nul
title Projeto Banco de Dados - Execucao Completa

:: Garante que o diretorio de trabalho seja o do script
cd /d "%~dp0"

:: Se os arquivos estiverem dentro da subpasta BancoDeDados, entra nela
if exist "BancoDeDados\scripts" (
    cd "BancoDeDados"
)

echo ===============================================================================
echo                PROJETO DE BANCO DE DADOS: RELACIONAL VS NOSQL
echo ===============================================================================
echo Diretorio atual: %CD%
echo.
echo Este script vai executar tudo de forma 100%% automatica para voce:
echo  1. Criar o Banco Relacional normalizado (SQLite / 3FN)
echo  2. Executar e exibir as Consultas SQL
echo  3. Gerar os Documentos para o NoSQL (MongoDB)
echo  4. Executar e exibir as Consultas NoSQL Documentais
echo.
echo Pressione qualquer tecla para comecar...
pause > nul

echo.
echo -------------------------------------------------------------------------------
echo [ETAPA 1 de 4] Criando e populando o Banco Relacional (SQLite / 3FN)...
echo -------------------------------------------------------------------------------
python scripts/load_relational.py
if %ERRORLEVEL% NEQ 0 (
    echo [ERRO] Ocorreu uma falha na etapa 1. Verifique se o Python esta instalado.
    pause
    exit /b
)

echo.
echo -------------------------------------------------------------------------------
echo [ETAPA 2 de 4] Executando as Consultas em SQL no Banco Relacional...
echo -------------------------------------------------------------------------------
python scripts/test_sql_queries.py

echo.
echo -------------------------------------------------------------------------------
echo [ETAPA 3 de 4] Gerando os Documentos NoSQL (JSON Lines para MongoDB)...
echo -------------------------------------------------------------------------------
python scripts/transform.py

echo.
echo -------------------------------------------------------------------------------
echo [ETAPA 4 de 4] Executando as Consultas Equivalentes no Modelo NoSQL...
echo -------------------------------------------------------------------------------
python scripts/test_nosql_queries.py

echo.
echo ===============================================================================
echo                           EXECUCAO CONCLUIDA COM SUCESSO!
echo ===============================================================================
echo.
echo O seu relatorio completo para o trabalho esta pronto no arquivo:
echo   docs\analise.md
echo.
echo Pressione qualquer tecla para fechar esta janela...
pause > nul
