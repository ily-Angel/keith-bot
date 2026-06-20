# msg_init_system.py - Versão otimizada
import discord
from discord.ext import commands
from sqlalchemy import select
from datetime import datetime
import asyncio
from io import BytesIO
import aiohttp
import unicodedata

from dbdata_server import AsyncSessionServerConfigs, DataForExtrasForGoodbyeMessage, DataForExtrasForWelcomeMessage, DataForGoodbyeMessage, BancoDeDadosParaMensagemDeBemVindoPersonalizada, ChatForMessageUperLevelXp
from dbdata import DataForGuildWarns, AsyncSessionLocal
from functionspillow import limpar_unicode, caminho_da_fonte, FONTES_DISPONIVEIS

# =========================
# FUNÇÕES DE IMAGEM (IMPORTADAS DO Keith.py)
# =========================

async def pegar_avatar_pillow(user: discord.User | discord.Member, tamanho: int = 128):
    """Importado do Keith.py para evitar duplicação"""
    from Keith import pegar_avatar_pillow as _pegar
    return await _pegar(user, tamanho)

async def gerar_gif_personalizado(*args, **kwargs):
    from Keith import gerar_gif_personalizado as _gerar
    return await _gerar(*args, **kwargs)

async def gerar_gif_personalizado_layout2(*args, **kwargs):
    from Keith import gerar_gif_personalizado_layout2 as _gerar
    return await _gerar(*args, **kwargs)

async def gerar_imagem_personalizada(*args, **kwargs):
    from Keith import gerar_imagem_personalizada as _gerar
    return await _gerar(*args, **kwargs)

async def gerar_imagem_personalizado_layout2(*args, **kwargs):
    from Keith import gerar_imagem_personalizado_layout2 as _gerar
    return await _gerar(*args, **kwargs)

# =========================
# MODAIS
# =========================

class ModalModeMessageInicial(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Modo da mensagem inicial.")
        self.modo = discord.ui.TextInput(
            label="Escolha o Modo da mensagem incial.",
            placeholder="Ex: IMAGEMODE/GIFMODE",
            max_length=9
        )
        self.add_item(self.modo)

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("Este comando só pode ser usado em servidores.", ephemeral=True)

        if self.modo.value not in ["GIFMODE", "IMAGEMODE"]:
            return await interaction.response.send_message("Coloque um modo válido.", ephemeral=True)

        async with AsyncSessionServerConfigs() as session:
            result = await session.execute(select(BancoDeDadosParaMensagemDeBemVindoPersonalizada).filter_by(guild_id=interaction.guild.id))
            guild_db = result.scalars().first()

            if not guild_db:
                guild_db = BancoDeDadosParaMensagemDeBemVindoPersonalizada(guild_id=interaction.guild.id, MODO=self.modo.value)
                session.add(guild_db)
            else:
                guild_db.MODO = self.modo.value

            await session.commit()
            await interaction.response.send_message("Modo salvo com sucesso!", ephemeral=True)

class ModalEscolherFonteMessageInicial(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Fonte da mensagem inicial.")
        self.fonte = discord.ui.TextInput(
            label="Fonte da mensagem inicial.",
            placeholder="Ex: Orbitron"
        )
        self.add_item(self.fonte)

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("Este comando só pode ser usado em servidores.", ephemeral=True)

        async with AsyncSessionServerConfigs() as session:
            result = await session.execute(select(BancoDeDadosParaMensagemDeBemVindoPersonalizada).filter_by(guild_id=interaction.guild.id))
            guild_db = result.scalars().first()

            if not guild_db:
                guild_db = BancoDeDadosParaMensagemDeBemVindoPersonalizada(guild_id=interaction.guild.id, font_message=self.fonte.value)
                session.add(guild_db)
            else:
                guild_db.font_message = self.fonte.value

            await session.commit()
            await interaction.response.send_message("Fonte configurada com sucesso!", ephemeral=True)

class ModalColorAndTransparencia(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Definições da faixa.")
        self.cor = discord.ui.TextInput(label="Coloque a cor, tem que ser Hexadecimal.", placeholder="Ex: #000000")
        self.transparencia = discord.ui.TextInput(label="Coloque a transparência.", placeholder="Ex: 1, max: 255")
        self.add_item(self.cor)
        self.add_item(self.transparencia)

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("Este comando só pode ser usado em servidores.", ephemeral=True)

        try:
            transparencia_int = int(self.transparencia.value)
        except ValueError:
            return await interaction.response.send_message("Transparência inválida.", ephemeral=True)

        async with AsyncSessionServerConfigs() as session:
            result = await session.execute(select(BancoDeDadosParaMensagemDeBemVindoPersonalizada).filter_by(guild_id=interaction.guild.id))
            guild_db = result.scalars().first()

            if not guild_db:
                guild_db = BancoDeDadosParaMensagemDeBemVindoPersonalizada(
                    guild_id=interaction.guild.id,
                    translucidez_faixa=transparencia_int,
                    cor_faixa=self.cor.value
                )
                session.add(guild_db)
            else:
                guild_db.translucidez_faixa = transparencia_int
                guild_db.cor_faixa = self.cor.value

            await session.commit()
            await interaction.response.send_message("Cor e transparência editadas com sucesso!", ephemeral=True)

class ModalTextSecond(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Definições do texto secundário.")
        self.text = discord.ui.TextInput(
            label="Escolha o texto secundário.",
            placeholder="Ex: Seja bem vindo ao servidor.",
            max_length=80
        )
        self.add_item(self.text)

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("Este comando só pode ser usado em servidores.", ephemeral=True)

        async with AsyncSessionServerConfigs() as session:
            result = await session.execute(select(BancoDeDadosParaMensagemDeBemVindoPersonalizada).filter_by(guild_id=interaction.guild.id))
            guild_db = result.scalars().first()

            if not guild_db:
                guild_db = BancoDeDadosParaMensagemDeBemVindoPersonalizada(guild_id=interaction.guild.id, text_content2=self.text.value)
                session.add(guild_db)
            else:
                guild_db.text_content2 = self.text.value

            await session.commit()
            await interaction.response.send_message("Texto definido com sucesso!", ephemeral=True)

class ModalTextColorsInicial(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Definições de cores dos textos.")
        self.text1 = discord.ui.TextInput(label="Escolha a cor do texto principal.", placeholder="Ex: #000000", max_length=7)
        self.text2 = discord.ui.TextInput(label="Escolha a cor do texto secundário.", placeholder="Ex: #000000", max_length=7)
        self.add_item(self.text1)
        self.add_item(self.text2)

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("Este comando só pode ser usado em servidores.", ephemeral=True)

        async with AsyncSessionServerConfigs() as session:
            result = await session.execute(select(BancoDeDadosParaMensagemDeBemVindoPersonalizada).filter_by(guild_id=interaction.guild.id))
            guild_db = result.scalars().first()

            if not guild_db:
                guild_db = BancoDeDadosParaMensagemDeBemVindoPersonalizada(
                    guild_id=interaction.guild.id,
                    cor_text1=self.text1.value,
                    cor_text2=self.text2.value
                )
                session.add(guild_db)
            else:
                guild_db.cor_text1 = self.text1.value
                guild_db.cor_text2 = self.text2.value

            await session.commit()
            await interaction.response.send_message("Cores dos textos definidas com sucesso!", ephemeral=True)

class ModalConfigsEmbedForWarn(discord.ui.Modal):
    def __init__(self):
        super().__init__(title='Configurações de Embed.')
        self.option1 = discord.ui.TextInput(label="Escolha o titulo do seu Embed.", required=True, placeholder="Ex: Usuário burro foi punido!", max_length=40)
        self.option2 = discord.ui.TextInput(label="Configure o recado do Embed.", placeholder="Ex: O que custa seguir as regras? É fácil.", required=True, max_length=120)
        self.option3 = discord.ui.TextInput(label="Escolha uma cor para seu Embed.", placeholder="#000000 = Preto", required=True, max_length=8)
        self.add_item(self.option1)
        self.add_item(self.option2)
        self.add_item(self.option3)

    async def on_submit(self, interaction: discord.Interaction):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(DataForGuildWarns).filter_by(guild_id=interaction.guild.id))
            guild = result.scalars().first()
            if not guild:
                guild = DataForGuildWarns(guild_id=interaction.guild.id)
                session.add(guild)
            guild.title = self.option1.value
            guild.recado = self.option2.value
            guild.cor_embed = self.option3.value
            await session.commit()

        await interaction.response.send_message("Configurações definidas com sucesso!")

class ModalConfigsTamanhoELargura(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Escolha o tamanho e a largura da imagem.")
        self.largura = discord.ui.TextInput(label="Defina a largura da imagem.", placeholder="Ex: 650", max_length=4)
        self.altura = discord.ui.TextInput(label="Defina a altura da imagem.", placeholder="Ex: 350", max_length=4)
        self.add_item(self.largura)
        self.add_item(self.altura)

    async def on_submit(self, interaction: discord.Interaction):
        if not interaction.guild:
            return await interaction.response.send_message("Este comando só pode ser usado em servidores.", ephemeral=True)

        try:
            largura = int(self.largura.value)
            altura = int(self.altura.value)
        except ValueError:
            return await interaction.response.send_message("Valores inválidos.", ephemeral=True)

        async with AsyncSessionServerConfigs() as session:
            result = await session.execute(select(BancoDeDadosParaMensagemDeBemVindoPersonalizada).filter_by(guild_id=interaction.guild.id))
            guild_db = result.scalars().first()

            if not guild_db:
                guild_db = BancoDeDadosParaMensagemDeBemVindoPersonalizada(
                    guild_id=interaction.guild.id,
                    tamanho_da_imagem=altura,
                    largura_da_imagem=largura
                )
                session.add(guild_db)
            else:
                guild_db.largura_da_imagem = largura
                guild_db.tamanho_da_imagem = altura

            await session.commit()
            await interaction.response.send_message("Altura e largura definidos com sucesso!", ephemeral=True)

class ModalTamanhoDaFonte(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Escolha o tamanho e a largura da imagem.")
        self.text1_size = discord.ui.TextInput(label="Defina o tamanho do texto principal.", placeholder="Ex: 40", max_length=2)
        self.text2_size = discord.ui.TextInput(label="Defina o tamanho do texto secundário.", placeholder="Ex: 20", max_length=2)
        self.add_item(self.text2_size)
        self.add_item(self.text1_size)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            text_size1 = int(self.text1_size.value)
            text_size2 = int(self.text2_size.value)
        except ValueError:
            return await interaction.response.send_message("Valores inválidos.", ephemeral=True)

        async with AsyncSessionServerConfigs() as session:
            result = await session.execute(select(BancoDeDadosParaMensagemDeBemVindoPersonalizada).filter_by(guild_id=interaction.guild.id))
            guilddb = result.scalars().first()
            if not guilddb:
                guilddb = BancoDeDadosParaMensagemDeBemVindoPersonalizada(guild_id=interaction.guild.id)
                session.add(guilddb)
            guilddb.size_text1 = text_size1
            guilddb.size_text2 = text_size2
            await session.commit()

        await interaction.response.send_message("Tamanho dos textos definido com sucesso!", ephemeral=True)

class ModalTrocarLayoutMessage(discord.ui.Modal):
    def __init__(self, title="Trocar Layout"):
        super().__init__(title=title)
        self.layout = discord.ui.TextInput(label="Trocar Layout. (Base/Perfil)", placeholder="Ex: perfil", max_length=10, required=True)
        self.add_item(self.layout)

    async def on_submit(self, interaction: discord.Interaction):
        async with AsyncSessionServerConfigs() as session:
            result = await session.execute(select(BancoDeDadosParaMensagemDeBemVindoPersonalizada).filter_by(guild_id=interaction.guild.id))
            guild_db = result.scalars().first()
            if not guild_db:
                guild_db = BancoDeDadosParaMensagemDeBemVindoPersonalizada(guild_id=interaction.guild.id)
                session.add(guild_db)
            guild_db.cor_embed = self.layout.value
            await session.commit()
            await interaction.response.send_message("Layout definido com sucesso.", ephemeral=True)

# =========================
# VIEWS
# =========================

class ButtonsForConfigsEmbedWarn(discord.ui.View):
    def __init__(self, ctx_author_id):
        super().__init__(timeout=120)
        self.ctxid = ctx_author_id

    @discord.ui.button(label="Configurar Embed.", style=discord.ButtonStyle.grey, emoji='🛠')
    async def configs_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctxid != interaction.user.id:
            return await interaction.response.send_message("Somente o usuário que usou o comando pode interagir com os botões❌.", ephemeral=True)
        await interaction.response.send_modal(ModalConfigsEmbedForWarn())

class BaseMessageConfigView(discord.ui.View):
    """View base para configurações de mensagem (Welcome e Goodbye)"""
    def __init__(self, ctx_author_id, is_goodbye=False):
        super().__init__(timeout=120)
        self.ctx_author_id = ctx_author_id
        self.is_goodbye = is_goodbye
        self._setup_buttons()

    def _setup_buttons(self):
        suffix = "Goodbye" if self.is_goodbye else ""
        self.add_item(self._create_button("Escolher Modo. (GIFMODE/IMAGEMODE)", self._get_modal_class("ModalModeMessageInicial", suffix)))
        self.add_item(self._create_button("Escolher fonte.", self._get_modal_class("ModalEscolherFonteMessageInicial", suffix)))
        self.add_item(self._create_button("Cor e Translucidez da faixa.", self._get_modal_class("ModalColorAndTransparencia", suffix)))
        self.add_item(self._create_button("Escolha o texto secundário.", self._get_modal_class("ModalTextSecond", suffix)))
        self.add_item(self._create_button("Escolher cor do texto principal e secundário.", self._get_modal_class("ModalTextColorsInicial", suffix)))
        self.add_item(self._create_button("Largura e Altura da imagem.", self._get_modal_class("ModalConfigsTamanhoELargura", suffix)))
        self.add_item(self._create_button("Escolher tamanho dos textos.", self._get_modal_class("ModalTamanhoDaFonte", suffix)))
        self.add_item(self._create_button("Trocar Layout.", self._get_modal_class("ModalTrocarLayoutMessage", suffix)))
        self.add_item(self._create_button("Preview da imagem.", self._preview_image))
        self.add_item(self._create_button("Enviar Imagem", self._send_image))
        self.add_item(self._create_button("Resetar tudo.", self._reset_configs))

    def _create_button(self, label, callback):
        button = discord.ui.Button(label=label, style=discord.ButtonStyle.grey)
        button.callback = callback
        return button

    def _get_modal_class(self, base_name, suffix):
        # Retorna a classe do modal apropriada (com ou sem suffix)
        if suffix:
            return getattr(self, f"{base_name}{suffix}", None)
        return getattr(self, base_name, None)

    async def _preview_image(self, interaction: discord.Interaction):
        # Implementação do preview (será sobrescrita)
        pass

    async def _send_image(self, interaction: discord.Interaction):
        # Implementação do envio de imagem (será sobrescrita)
        pass

    async def _reset_configs(self, interaction: discord.Interaction):
        # Implementação do reset (será sobrescrita)
        pass

# =========================
# VIEWS DE CONFIGURAÇÃO DE EMBED
# =========================

class ViewConfigsEmbed(discord.ui.View):
    def __init__(self, ctx_author_id, is_goodbye=False):
        super().__init__(timeout=120)
        self.ctx_author_id = ctx_author_id
        self.is_goodbye = is_goodbye
        suffix = "Goodbye" if is_goodbye else ""
        
        self.add_item(self._create_button("Editar titúlo, descrição, cor, footer e thumb do Embed.", self._get_modal_class("Modal2ConfiguraçõesDeEmbedTitulo", suffix)))
        self.add_item(self._create_button("Imagem dentro ou fora do Embed? (SIM/NÃO)", self._get_modal_class("Modal2ModoForEmbedBy", suffix)))
        self.add_item(self._create_button("Ativar Embed junto da imagem? (SIM/NÃO)", self._get_modal_class("Modal2ModoForEmbedByImage", suffix)))

    def _create_button(self, label, callback):
        button = discord.ui.Button(label=label, style=discord.ButtonStyle.grey)
        button.callback = callback
        return button

    def _get_modal_class(self, base_name, suffix):
        if suffix:
            return getattr(self, f"{base_name}{suffix}", None)
        return getattr(self, base_name, None)

class ButtonsForOpenConfigs(discord.ui.View):
    def __init__(self, ctx_author_id):
        super().__init__(timeout=120)
        self.ctxid = ctx_author_id

    @discord.ui.button(label="Abrir", style=discord.ButtonStyle.grey)
    async def buttonforopenconfigs1(self, interaction: discord.Interaction, button: discord.ui.Button):
        m = discord.Embed(
            title="Configurações da mensagem de bem vindo🌌.",
            description="Configure a sua mensagem de bem vindo da forma que você desejar🪄!",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=m, view=WelecomeMessageConfigsView(self.ctxid), ephemeral=True)

class ButtonForOpenConfigs2(discord.ui.View):
    def __init__(self, ctx_author_id):
        super().__init__(timeout=120)
        self.ctxid = ctx_author_id

    @discord.ui.button(label="Abrir", style=discord.ButtonStyle.grey)
    async def buttonforopenconfigs1(self, interaction: discord.Interaction, button: discord.ui.Button):
        m = discord.Embed(
            title="Configurações do embed da mensagem de bem vindo🌌.",
            description="Configure o seu embed de bem vindo da forma que você desejar🪄!",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=m, view=ViewConfigsEmbedForMessageWelcome(self.ctxid), ephemeral=True)

class ButtonForOpenConfigs3(discord.ui.View):
    def __init__(self, ctx_author_id):
        super().__init__(timeout=120)
        self.ctxid = ctx_author_id

    @discord.ui.button(label="Abrir", style=discord.ButtonStyle.grey)
    async def buttonforopenconfigs1(self, interaction: discord.Interaction, button: discord.ui.Button):
        m = discord.Embed(
            title="Configurações da mensagem de saída🌇.",
            description="Configure a sua mensagem de saída da forma que você desejar🪄!",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=m, view=GoodbyeMessageViewConfigs(self.ctxid), ephemeral=True)

class ButtonForOpenConfigs4(discord.ui.View):
    def __init__(self, ctx_author_id):
        super().__init__(timeout=120)
        self.ctxid = ctx_author_id

    @discord.ui.button(label="Abrir", style=discord.ButtonStyle.grey)
    async def buttonforopenconfigs1(self, interaction: discord.Interaction, button: discord.ui.Button):
        m = discord.Embed(
            title="Configurações do embed da mensagem de saída🌇.",
            description="Configure o seu embed da mensagem de saída da forma que você desejar🪄!",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow()
        )
        await interaction.response.send_message(embed=m, view=ViewConfigsEmbedForMessageGoodbye(self.ctxid), ephemeral=True)

class ButtonHelpForWelcomeAndGoodbyeMessageConfigs(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="Informações e Ajuda", style=discord.ButtonStyle.green)
    async def buttonforhelp(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed_info_message_ = discord.Embed(
            title="🏗Configurações da mensagem de bem vindo e tchau.🏭",
            description="Aqui você tem todas as opções de configurações da mensagem de bem vindo e tchau.",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow()
        )
        embed_info_message_.add_field(name="🛣Canal onde a mensagem será enviada.🛣", value="Para definir isso, você precisa usar o comando <configurarcanal [canal]", inline=True)
        embed_info_message_.add_field(name="🧬Configuração das cores.⚗️", value="Todas as cores são configuraveis através de cor hexadecimal.\nEx: #000000 = Preto.", inline=True)
        embed_info_message_.add_field(name="🖋Escolher Fontes.✒️", value="O catálogo de fontes está disponível no <configs, usando esse comando, irá aparecer uma série de botões, um deles foi feito para a configuração de fontes do perfil, e lá tem o catálogo disponível.", inline=True)
        embed_info_message_.add_field(name="📐Tamanho da imagem.📏", value="A altura e Largura tem que ser as mesmas da imagem que você enivou, ou em escala semelhante, mas não pode passar dos 1000x1000, caso a imagem passe isso, é recomendado colocar uma escala semelhante, como 500x500.", inline=True)
        embed_info_message_.add_field(name="🎥Modos de imagem disponível.📸", value="Temos dois modos de imagem disponpivel, .gif e .png, sempre envie nesses formatos, e escolha qual modo você prefere, gif ou imagem estática (vulgo .png).", inline=True)
        embed_info_message_.add_field(name="🏭Como posso ver uma preview da mensagem?📡", value="Basta usar <preview mensagem inicial, com esse comando, você poderá ver como iŕa ficar sua mensagem de boas vindas e mensagem de saída.", inline=True)
        embed_info_message_.add_field(name="📱Como configurar o canais?📱", value="Use <configurarcanal [canal] para configurar o canal onde a mensagem de entrada será enviada, e use <configurarcanalgoodbye para configurar o canal onde a mensagem de saída será enviada.", inline=True)
        await interaction.response.send_message(embed=embed_info_message_, ephemeral=True)

# =========================
# VIEWS DE CONFIGURAÇÃO - WELCOME E GOODBYE
# =========================

class WelecomeMessageConfigsView(discord.ui.View):
    def __init__(self, ctx_author_id):
        super().__init__(timeout=120)
        self.ctx_author_id = ctx_author_id
        self._add_buttons(False)

    def _add_buttons(self, is_goodbye):
        buttons = [
            ("Escolher Modo. (GIFMODE/IMAGEMODE)", ModalModeMessageInicial),
            ("Escolher fonte.", ModalEscolherFonteMessageInicial),
            ("Cor e Translucidez da faixa.", ModalColorAndTransparencia),
            ("Escolha o texto secundário.", ModalTextSecond),
            ("Escolher cor do texto principal e secundário.", ModalTextColorsInicial),
            ("Largura e Altura da imagem.", ModalConfigsTamanhoELargura),
            ("Escolher tamanho dos textos.", ModalTamanhoDaFonte),
            ("Trocar Layout.", ModalTrocarLayoutMessage),
        ]
        for label, modal_class in buttons:
            self.add_item(self._create_button(label, modal_class))
        
        self.add_item(self._create_preview_button(is_goodbye))
        self.add_item(self._create_send_image_button(is_goodbye))
        self.add_item(self._create_reset_button(is_goodbye))

    def _create_button(self, label, modal_class):
        button = discord.ui.Button(label=label, style=discord.ButtonStyle.grey)
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.ctx_author_id:
                return await interaction.response.send_message("Somente o autor do comando pode interagir com esses botões.", ephemeral=True)
            await interaction.response.send_modal(modal_class())
        button.callback = callback
        return button

    def _create_preview_button(self, is_goodbye):
        button = discord.ui.Button(label="Preview da imagem.", style=discord.ButtonStyle.grey)
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.ctx_author_id:
                return await interaction.response.send_message("Somente o autor do comando pode interagir com esses botões.", ephemeral=True)
            await self._preview_image(interaction, is_goodbye)
        button.callback = callback
        return button

    def _create_send_image_button(self, is_goodbye):
        button = discord.ui.Button(label="Enviar Imagem", style=discord.ButtonStyle.grey)
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.ctx_author_id:
                return await interaction.response.send_message("Somente o autor do comando pode interagir com esses botões.", ephemeral=True)
            await self._send_image(interaction, is_goodbye)
        button.callback = callback
        return button

    def _create_reset_button(self, is_goodbye):
        button = discord.ui.Button(label="Resetar tudo.", style=discord.ButtonStyle.red)
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.ctx_author_id:
                return await interaction.response.send_message("Somente o autor do comando pode interagir com esses botões.", ephemeral=True)
            await self._reset_configs(interaction, is_goodbye)
        button.callback = callback
        return button

    async def _preview_image(self, interaction: discord.Interaction, is_goodbye: bool):
        await interaction.response.defer(ephemeral=True)
        
        db_class = DataForGoodbyeMessage if is_goodbye else BancoDeDadosParaMensagemDeBemVindoPersonalizada
        folder = "fundos_msg_goodbye" if is_goodbye else "fundos_msg"
        
        async with AsyncSessionServerConfigs() as session:
            result = await session.execute(select(db_class).filter_by(guild_id=interaction.guild.id))
            guild_db = result.scalars().first()
            if not guild_db:
                return await interaction.followup.send("Você não tem nenhuma imagem disponível.", ephemeral=True)

            member = interaction.user
            avatar_path = await pegar_avatar_pillow(member)
            
            caminho_fonte = caminho_da_fonte(guild_db.font_message or "arial")
            mode = guild_db.MODO or "estatico"
            layout = guild_db.cor_embed or "base"
            
            fundo_path = f'{folder}/{interaction.guild.id}.{"gif" if mode.lower() == "gifmode" else "png"}'

            if mode.lower() == 'gifmode':
                if layout.lower() == "base":
                    img = await gerar_gif_personalizado(
                        fundo_path=fundo_path, avatar_path=avatar_path,
                        texto_nome=limpar_unicode(member.display_name),
                        texto_sub=guild_db.text_content2 or ("Até logo!" if is_goodbye else "Bem vindo ao servidor."),
                        translucidez_faixa=guild_db.translucidez_faixa or 160,
                        cor_faixa=guild_db.cor_faixa or (100, 180, 255),
                        fonte_caminho=caminho_fonte,
                        tamanho_nome=guild_db.size_text1 or 40,
                        tamanho_sub=guild_db.size_text2 or 25,
                        imagem_altura=guild_db.tamanho_da_imagem or 380,
                        largura_imagem=guild_db.largura_da_imagem or 650,
                        text_color=guild_db.cor_text1 or "#ffffff",
                        color_text2=guild_db.cor_text2 or "#000000"
                    )
                    file_ = discord.File(img, filename="Preview.gif")
                else:
                    img = await gerar_gif_personalizado_layout2(
                        fundo_path=fundo_path, avatar_path=avatar_path,
                        texto_nome=limpar_unicode(member.display_name),
                        texto_sub=guild_db.text_content2 or ("Até logo!" if is_goodbye else "Bem vindo ao servidor."),
                        translucidez_faixa=guild_db.translucidez_faixa or 160,
                        cor_faixa=guild_db.cor_faixa or (100, 180, 255),
                        fonte_caminho=caminho_fonte,
                        tamanho_nome=guild_db.size_text1 or 40,
                        tamanho_sub=guild_db.size_text2 or 25,
                        imagem_altura=guild_db.tamanho_da_imagem or 380,
                        largura_imagem=guild_db.largura_da_imagem or 650,
                        text_color=guild_db.cor_text1 or "#ffffff",
                        text_cololr2=guild_db.cor_text2 or "#000000"
                    )
                    file_ = discord.File(img, filename="Preview.gif")
            else:
                if layout.lower() == "base":
                    img = await gerar_imagem_personalizada(
                        fundo_path=fundo_path, avatar_path=avatar_path,
                        texto_nome=limpar_unicode(member.display_name),
                        texto_sub=guild_db.text_content2 or ("Até logo!" if is_goodbye else "Bem vindo ao servidor."),
                        translucidez_faixa=guild_db.translucidez_faixa or 160,
                        cor_faixa=guild_db.cor_faixa or (100, 180, 255),
                        fonte_caminho=caminho_fonte,
                        tamanho_nome=guild_db.size_text1 or 40,
                        tamanho_sub=guild_db.size_text2 or 25,
                        imagem_altura=guild_db.tamanho_da_imagem or 380,
                        largura_imagem=guild_db.largura_da_imagem or 650,
                        color_text=guild_db.cor_text1 or "#000000",
                        color_text2=guild_db.cor_text2 or "#000000"
                    )
                    file_ = discord.File(img, filename="Preview.png")
                else:
                    img = await gerar_imagem_personalizado_layout2(
                        fundo_path=fundo_path, avatar_path=avatar_path,
                        texto_nome=limpar_unicode(member.display_name),
                        texto_sub=guild_db.text_content2 or ("Até logo!" if is_goodbye else "Bem vindo ao servidor."),
                        translucidez_faixa=guild_db.translucidez_faixa or 160,
                        cor_faixa=guild_db.cor_faixa or (100, 180, 255),
                        fonte_caminho=caminho_fonte,
                        tamanho_nome=guild_db.size_text1 or 40,
                        tamanho_sub=guild_db.size_text2 or 25,
                        imagem_altura=guild_db.tamanho_da_imagem or 380,
                        largura_imagem=guild_db.largura_da_imagem or 650,
                        text_color=guild_db.cor_text1 or "#ffffff",
                        text_cololr2=guild_db.cor_text2 or "#000000"
                    )
                    file_ = discord.File(img, filename="Preview.png")

            await interaction.followup.send(content=f"Aqui está sua preview {interaction.user.mention}", file=file_, ephemeral=True)

    async def _send_image(self, interaction: discord.Interaction, is_goodbye: bool):
        await interaction.response.defer(ephemeral=True)
        await interaction.followup.send("Você tem **60 segundos** para enviar uma imagem `.png` ou `.gif` neste canal!", ephemeral=True)

        def check(msg: discord.Message):
            if msg.author != interaction.user or msg.channel != interaction.channel:
                return False
            if not msg.attachments:
                return False
            att = msg.attachments[0]
            if att.content_type and att.content_type in ("image/png", "image/gif"):
                return True
            return att.filename.lower().endswith((".png", ".gif"))

        try:
            msg = await interaction.client.wait_for("message", check=check, timeout=60.0)
            attachment = msg.attachments[0]
            ext = attachment.filename.split(".")[-1].lower()
            folder = "fundos_msg_goodbye" if is_goodbye else "fundos_msg"
            file_path = f"{folder}/{interaction.guild.id}.{ext}"
            await attachment.save(file_path)
            await interaction.followup.send(f"✅ Imagem recebida e salva como `{interaction.guild.id}.{ext}`", ephemeral=True)
        except asyncio.TimeoutError:
            await interaction.followup.send("⏰ Tempo esgotado! Envie apenas `.png` ou `.gif`.", ephemeral=True)

    async def _reset_configs(self, interaction: discord.Interaction, is_goodbye: bool):
        db_class = DataForGoodbyeMessage if is_goodbye else BancoDeDadosParaMensagemDeBemVindoPersonalizada
        async with AsyncSessionServerConfigs() as session:
            result = await session.execute(select(db_class).filter_by(guild_id=interaction.guild.id))
            guild_db = result.scalars().first()
            if guild_db:
                await session.delete(guild_db)
                await session.commit()
        await interaction.response.send_message("Configurações resetadas com sucesso!", ephemeral=True)

class GoodbyeMessageViewConfigs(WelecomeMessageConfigsView):
    def __init__(self, ctx_author_id):
        super().__init__(ctx_author_id)
        # Sobrescreve para usar Goodbye
        self._add_buttons(True)

# =========================
# VIEWS DE CONFIGURAÇÃO DE EMBED - WELCOME E GOODBYE
# =========================

class ViewConfigsEmbedForMessageWelcome(ViewConfigsEmbed):
    def __init__(self, ctx_author_id):
        super().__init__(ctx_author_id, False)

class ViewConfigsEmbedForMessageGoodbye(ViewConfigsEmbed):
    def __init__(self, ctx_author_id):
        super().__init__(ctx_author_id, True)

# =========================
# MODAIS DE EMBED - VERSÕES COM SUFFIX
# =========================

class Modal2ConfiguraçõesDeEmbedTitulo(ViewConfigsEmbed._modal_base):
    pass

# =========================
# COG PRINCIPAL
# =========================

class InitialSystemMessage(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @commands.command(name="serverconfigs", aliases=["svconfigs", "configuraçõesdeservidor"])
    @commands.has_permissions(manage_channels=True)
    async def serverconfigs(self, ctx: commands.Context, *args):
        termo = ' '.join(args[:2])

        if termo == '':
            embed = discord.Embed(title="📜 Opções de Configurações.", color=discord.Color.dark_grey(), timestamp=discord.utils.utcnow())
            embed.add_field(name="📨 Mensagem inicial.", value="📪 Ao digitar `<serverconfigs mensagem inicial`, você abre as configurações de mensagem de entrada e saída.", inline=True)
            embed.add_field(name="⚠️ Warn Configs", value="🛑 Ao digitar `<serverconfigs warnconfigs`, você abre as configurações do comando de warn.", inline=True)
            embed.set_footer(text=ctx.author.name, icon_url=ctx.author.avatar.url)
            embed.set_thumbnail(url=ctx.guild.icon.url)
            return await ctx.reply(embed=embed)

        if termo == 'warnconfigs':
            m = discord.Embed(
                title="🌌🛠 Configurações do Embed de warn.",
                description="Aqui você pode editar as configurações do seu embed de warn 🔮.",
                color=discord.Color.blurple(),
                timestamp=discord.utils.utcnow()
            )
            m.set_thumbnail(url=ctx.guild.icon.url)
            m.set_footer(text=ctx.guild.name, icon_url=ctx.guild.icon.url)
            await ctx.reply(embed=m, view=ButtonsForConfigsEmbedWarn(ctx.author.id))
            return

        if termo == "mensagem inicial":
            embed_separador_2 = discord.Embed(title="🛠🌌Configurações da mensagem de entrada.", color=discord.Color.blurple(), timestamp=discord.utils.utcnow())
            embed_separador = discord.Embed(title="🛠🌌Configurações da mensagem de saída.", color=discord.Color.blurple(), timestamp=discord.utils.utcnow())
            embed_separador_embed = discord.Embed(title="🛠🌌Configurações de embed de saída.", description="Aqui você pode editar o seu embed de saída!", color=discord.Color.blurple(), timestamp=discord.utils.utcnow())
            embed_info_embed_for_welcome_message = discord.Embed(title="🛠🌌Definições do embed de entrada.", description="Aqui você pode editar seu embed!", color=discord.Color.blurple(), timestamp=discord.utils.utcnow())
            embed_help = discord.Embed(title="🛠🏕Deseja abrir o menu de ajuda?", description="Ele irá mostrar uma série de informações que ajudarão você a configurar sua mensagem de saída e bem vindo.", color=discord.Color.green(), timestamp=discord.utils.utcnow())

            await ctx.send(embed=embed_separador_2, view=ButtonsForOpenConfigs(ctx.author.id))
            await ctx.send(embed=embed_info_embed_for_welcome_message, view=ButtonForOpenConfigs2(ctx.author.id))
            await ctx.send(embed=embed_separador, view=ButtonForOpenConfigs3(ctx.author.id))
            await ctx.send(embed=embed_separador_embed, view=ButtonForOpenConfigs4(ctx.author.id))
            await ctx.send(embed=embed_help, view=ButtonHelpForWelcomeAndGoodbyeMessageConfigs())
            return

        embed_info = discord.Embed(
            title="🛠Configurações de servidor.🔌",
            description="Ajuste as configurações de seu servidor aqui.",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow()
        )
        embed_info.set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url)
        embed_info.set_thumbnail(url=ctx.guild.icon.url)
        await ctx.send(embed=embed_info)

    @commands.command(name="configurarcanalgoodbye")
    @commands.has_permissions(manage_channels=True)
    async def configurarcanalgoodbye(self, ctx, channel: discord.TextChannel):
        async with AsyncSessionServerConfigs() as session:
            result = await session.execute(select(DataForGoodbyeMessage).filter_by(guild_id=ctx.guild.id))
            guilddb = result.scalars().first()
            if not guilddb:
                guilddb = DataForGoodbyeMessage(guild_id=ctx.guild.id)
                session.add(guilddb)
            guilddb.canal_bem_vindo = channel.id
            await session.commit()
        await ctx.reply(f"Canal configurado como {channel.mention}")

    @commands.command(name="displayconfigs")
    @commands.has_permissions(manage_guild=True)
    async def displayconfigs(self, ctx: commands.Context, *args):
        termo = ' '.join(args[:2])
        if termo == '':
            return await ctx.reply("Você pode olhar diversas configurações do servidor com esse comando. \n\n* <displayconfigs mensagem inicial: Você pode olhar as configurações da mensagem de bem vindo e adeus.")

        if termo == "mensagem inicial":
            # Buscar configurações de Welcome
            async with AsyncSessionServerConfigs() as session:
                result = await session.execute(select(BancoDeDadosParaMensagemDeBemVindoPersonalizada).filter_by(guild_id=ctx.guild.id))
                guild_db = result.scalars().first()
                if not guild_db:
                    guild_db = BancoDeDadosParaMensagemDeBemVindoPersonalizada(guild_id=ctx.guild.id)
                    session.add(guild_db)
                result2 = await session.execute(select(DataForExtrasForWelcomeMessage).filter_by(guild_id=ctx.guild.id))
                embed_guild = result2.scalars().first()
                if not embed_guild:
                    embed_guild = DataForExtrasForWelcomeMessage(guild_id=ctx.guild.id)
                    session.add(embed_guild)

            # Buscar configurações de Goodbye
            async with AsyncSessionServerConfigs() as session:
                result = await session.execute(select(DataForGoodbyeMessage).filter_by(guild_id=ctx.guild.id))
                guild_db2 = result.scalars().first()
                if not guild_db2:
                    guild_db2 = DataForGoodbyeMessage(guild_id=ctx.guild.id)
                    session.add(guild_db2)
                result2 = await session.execute(select(DataForExtrasForGoodbyeMessage).filter_by(guild_id=ctx.guild.id))
                embed_guild2 = result2.scalars().first()
                if not embed_guild2:
                    embed_guild2 = DataForExtrasForGoodbyeMessage(guild_id=ctx.guild.id)
                    session.add(embed_guild2)

            canal = ctx.guild.get_channel(guild_db.canal_bem_vindo)
            canal_ = canal.mention if canal else "Não configurado"
            canal2 = ctx.guild.get_channel(guild_db2.canal_bem_vindo)
            canal2_ = canal2.mention if canal2 else "Não configurado"

            embed_display = discord.Embed(
                title="Configurações da mensagem de boas vindas e adeus.",
                description=(
                    f"* Configurações da Mensagem de Bem vindo.\n\n"
                    f"Modo: {guild_db.MODO or 'Não configurado'}\n"
                    f"Largura: {guild_db.largura_da_imagem or 650} e Altura: {guild_db.tamanho_da_imagem or 380}\n"
                    f"canal: {canal_}\n"
                    f"Transparência: {guild_db.translucidez_faixa or 160} e Cor: {guild_db.cor_faixa or 'Não configurado'}\n"
                    f"Cor do texto 1: {guild_db.cor_text1 or 'Não configurado'} e Cor do texto 2: {guild_db.cor_text2 or 'Não configurado'}\n"
                    f"Fonte do texto: {guild_db.font_message or 'arial'}\n"
                    f"Tamanho do texto 1: {guild_db.size_text1 or 40} e Tamanho do texto 2: {guild_db.size_text2 or 25}\n"
                    f"Texto 2: {guild_db.text_content2 or 'Não configurado'}\n"
                    f"* Configurações de Embed da mensagem de Bem vindo.\n\n"
                    f"Ativado?: {embed_guild.embed_true_false or 'Não configurado'}\n"
                    f"Titulo: {embed_guild.title_for_embed or 'Não configurado'}\n"
                    f"Descrição: {embed_guild.text_for_embed or 'Não configurado'}\n"
                    f"Footer do Embed: {embed_guild.footer_for_embed or 'Não configurado'}\n"
                    f"Cor do Embed: {embed_guild.color_for_embed or 'Não configurado'}\n"
                    f"Imagem Dentro do Embed?: {embed_guild.imagem_enter_embed or 'Não configurado'}\n\n"
                    f"* Configurações da mensagem de Adeus.\n\n"
                    f"Modo: {guild_db2.MODO or 'Não configurado'}\n"
                    f"Largura: {guild_db2.largura_da_imagem or 650} e Altura: {guild_db2.tamanho_da_imagem or 380}\n"
                    f"canal: {canal2_}\n"
                    f"Transparência: {guild_db2.translucidez_faixa or 160} e Cor: {guild_db2.cor_faixa or 'Não configurado'}\n"
                    f"Cor do texto 1: {guild_db2.cor_text1 or 'Não configurado'} e Cor do texto 2: {guild_db2.cor_text2 or 'Não configurado'}\n"
                    f"Fonte do texto: {guild_db2.font_message or 'arial'}\n"
                    f"Tamanho do texto 1: {guild_db2.size_text1 or 40} e Tamanho do texto 2: {guild_db2.size_text2 or 25}\n"
                    f"Texto 2: {guild_db2.text_content2 or 'Não configurado'}\n"
                    f"* Configurações do Embed da mensagem de Adeus\n\n."
                    f"Ativado?: {embed_guild2.embed_true_false or 'Não configurado'}\n"
                    f"Titulo: {embed_guild2.title_for_embed or 'Não configurado'}\n"
                    f"Descrição: {embed_guild2.text_for_embed or 'Não configurado'}\n"
                    f"Footer do Embed: {embed_guild2.footer_for_embed or 'Não configurado'}\n"
                    f"Cor do Embed: {embed_guild2.color_for_embed or 'Não configurado'}\n"
                    f"Imagem Dentro do Embed?: {embed_guild2.imagem_enter_embed or 'Não configurado'}\n\n"
                ),
                color=discord.Color.dark_blue(),
                timestamp=discord.utils.utcnow()
            ).set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url)

            await ctx.send(embed=embed_display)

    @commands.command(name="configurarcanallevelup", aliases=["cfglp"])
    @commands.has_permissions(manage_channels=True)
    async def config_set_channel_level_up(self, ctx: commands.Context, channel: discord.TextChannel):
        async with AsyncSessionServerConfigs() as session:
            result = await session.execute(select(ChatForMessageUperLevelXp).filter_by(guild_id=ctx.guild.id))
            userdb = result.scalars().first()
            if not userdb:
                userdb = ChatForMessageUperLevelXp(guild_id=ctx.guild.id, chat_id=channel.id)
                session.add(userdb)
            await session.commit()
        await ctx.reply("✅ Canal configurado com sucesso!")

async def setup(bot):
    await bot.add_cog(InitialSystemMessage(bot))