#!/usr/bin/env bash
# Versão Linux de executar_tudo.bat

# Garante que o diretorio de trabalho seja o do script
cd "$(dirname "$0")" || exit 1

# Se os arquivos estiverem dentro da subpasta BancoDeDados, entra nela
if [ -d "BancoDeDados/scripts" ]; then
    cd "BancoDeDados" || exit 1
fi

pausar() {
    read -r -n 1 -s -p "$1" _
    echo
}

echo "==============================================================================="
echo "               PROJETO DE BANCO DE DADOS: RELACIONAL VS NOSQL"
echo "==============================================================================="
echo "Diretorio atual: $PWD"
echo
echo "Este script vai executar tudo de forma 100% automatica para voce:"
echo " 0. Baixar os dados brutos do MovieLens (data/raw/)"
echo " 1. Criar o Banco Relacional normalizado (SQLite / 3FN)"
echo " 2. Executar e exibir as Consultas SQL"
echo " 3. Gerar os Documentos para o NoSQL (MongoDB)"
echo " 4. Executar e exibir as Consultas NoSQL Documentais"
echo
pausar "Pressione qualquer tecla para comecar..."

PY=python3

etapa() {
    echo
    echo "-------------------------------------------------------------------------------"
    echo "$1"
    echo "-------------------------------------------------------------------------------"
}

etapa "[ETAPA 0 de 4] Baixando os dados brutos do MovieLens (se necessario)..."
if ! "$PY" scripts/download_data.py; then
    echo "[ERRO] Ocorreu uma falha no download dos dados. Verifique sua conexao."
    pausar "Pressione qualquer tecla para sair..."
    exit 1
fi

etapa "[ETAPA 1 de 4] Criando e populando o Banco Relacional (SQLite / 3FN)..."
if ! "$PY" scripts/load_relational.py; then
    echo "[ERRO] Ocorreu uma falha na etapa 1. Verifique se o Python esta instalado."
    pausar "Pressione qualquer tecla para sair..."
    exit 1
fi

etapa "[ETAPA 2 de 4] Executando as Consultas em SQL no Banco Relacional..."
"$PY" scripts/test_sql_queries.py

etapa "[ETAPA 3 de 4] Gerando os Documentos NoSQL (JSON Lines para MongoDB)..."
"$PY" scripts/transform.py

etapa "[ETAPA 4 de 4] Executando as Consultas Equivalentes no Modelo NoSQL..."
"$PY" scripts/test_nosql_queries.py

echo
echo "==============================================================================="
echo "                          EXECUCAO CONCLUIDA COM SUCESSO!"
echo "==============================================================================="
echo
echo "O seu relatorio completo para o trabalho esta pronto no arquivo:"
echo "  docs/analise.md"
echo
pausar "Pressione qualquer tecla para fechar esta janela..."
