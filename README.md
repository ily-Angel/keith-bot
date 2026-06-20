# 🤖 Keith Bot - Discord Multifuncional

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![discord.py](https://img.shields.io/badge/discord.py-2.4.0-blue.svg)](https://github.com/Rapptz/discord.py)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> Um bot Discord completo e escalável com sistemas de economia, perfil personalizável, moderação e muito mais.

---

## 📋 Índice

- [Sobre o Projeto](#-sobre-o-projeto)
- [Funcionalidades](#-funcionalidades)
- [Tecnologias Utilizadas](#-tecnologias-utilizadas)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação e Configuração](#-instalação-e-configuração)
- [Comandos Principais](#-comandos-principais)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Contribuição](#-contribuição)
- [Licença](#-licença)
- [Contato](#-contato)

---

## 🚀 Sobre o Projeto

**Keith** é um bot para Discord desenvolvido em Python com foco em performance, escalabilidade e uma experiência rica para os usuários. Ele combina sistemas complexos de economia, customização de perfil com geração de imagens, moderação e funcionalidades sociais, tudo em uma arquitetura assíncrona e modular.

Este projeto foi desenvolvido como estudo e portfólio, demonstrando boas práticas de programação, uso de banco de dados assíncrono e integração com múltiplas APIs.

---

## ✨ Funcionalidades

### 💰 Sistema de Economia
- **Moeda Virtual (MDBs)**: Sistema completo de moeda com saldo, transferências e poupança.
- **Jogos de Azar**: Roleta, Blackjack, Coinflip, Caça-níquel, Roleta Russa, Adivinhe a Cor, BombGame e mais.
- **Sistema de Daily**: Recompensas diárias com bônus para usuários Premium.
- **Poupança**: Rendimento diário de 0.5% sobre o saldo poupado.
- **Ranking de MDBs**: Visualize os usuários mais ricos do servidor.

### 👤 Perfil Customizável
- **Personalização Completa**: Alterne entre diferentes layouts (perfil/xp), cores, fontes e tamanhos.
- **Fundos Dinâmicos**: Suporte a imagens estáticas (PNG) e animadas (GIF) como plano de fundo.
- **Nome com Gradiente** *(Premium)*: Cores degradê no nome do perfil.
- **Perfil Animado** *(Premium)*: Suporte a GIFs animados no perfil.
- **Sistema de Likes**: Curta e descurta perfis de outros usuários.
- **Bio Personalizável**: Adicione uma descrição e emojis extras.

### 💍 Sistema de Casamento
- **Pedido de Casamento**: Envie pedidos para outros usuários.
- **Status do Casal**: Visualize informações e estatísticas do relacionamento.
- **Divórcio**: Sistema de divórcio com confirmação.

### 📨 Sistema Interno de E-mail
- Envie mensagens privadas para outros usuários dentro do bot.
- Sistema de caixa de entrada com notificações de e-mails não lidos.

### 🛡️ Moderação
- **Comandos de Moderação**: Ban, Unban, Mute, Unmute, Limpar mensagens.
- **Sistema de Warns**: Aplique e remova advertências com embed personalizável.
- **Reaction Roles**: Crie mensagens com reações para auto-atribuição de cargos.
- **Logs de Auditoria**: Configure canais para monitorar ações.

### 🎨 Mensagens de Boas-Vindas e Despedida
- **Totalmente Customizável**: Alterne entre modos estático (PNG) e animado (GIF).
- **Personalização Visual**: Edite cores, fontes, tamanhos, transparência e layout.
- **Preview**: Visualize como a mensagem ficará antes de ativá-la.

### 🐟 Sistema de Pesca
- Colete diferentes espécies de peixes (água doce e salgada).
- Venda os peixes por MDBs.
- Sistema de inventário para gerenciar sua coleção.

### 🏆 Sistema de XP e Rankings
- Ganhe XP ao enviar mensagens.
- Sistema de níveis com barra de progresso visual.
- Ranking global e por servidor.

### 📊 Comandos de Informação
- `userinfo`, `serverinfo`, `botinfo`, `ping`, `avatar`, `banner`, `serverbanner`.

### 🎯 Comandos de Diversão
- `ship`, `8ball`, `beijo`, `abraço`, `cafuné`, `vidente`, `fate`, `perdeutudo`.

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Versão | Finalidade |
|------------|--------|------------|
| **Python** | 3.10+ | Linguagem principal |
| **discord.py** | 2.4.0 | Biblioteca para integração com Discord |
| **SQLAlchemy** | 2.0+ | ORM para banco de dados |
| **Pillow (PIL)** | 10.0+ | Geração e manipulação de imagens |
| **aiohttp** | 3.9+ | Requisições HTTP assíncronas |
| **python-dotenv** | 1.0+ | Gerenciamento de variáveis de ambiente |
| **psutil** | 5.9+ | Monitoramento de recursos do sistema |
| **requests** | 2.31+ | Requisições HTTP síncronas (em migração para aiohttp) |

---

## 📦 Pré-requisitos

Antes de começar, certifique-se de ter instalado:

- [Python 3.10+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/)
- [SQLite3](https://www.sqlite.org/) (já incluso no Python)
- Um [Token de Bot do Discord](https://discord.com/developers/applications)
- [SQLAlchemy](https://www.sqlalchemy.org/)

---

## ⭐ Diferenciais

- Perfis com suporte a GIFs animados
- Sistema interno de e-mail
- Sistema de casamento
- Sistema de pesca
- Welcome/Goodbye totalmente renderizados em imagem
- Arquitetura assíncrona com SQLAlchemy Async

---

## 📈 Projeto em Números

- +80 comandos
- +20 tabelas SQL
- Sistema de economia completo
- Sistema de XP
- Sistema de casamento
- Sistema de e-mail
- Sistema de pesca
- Geração dinâmica de imagens PNG e GIF