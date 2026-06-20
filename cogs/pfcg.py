import discord
from discord.ext import commands
from discord.ui import Modal, View, Button
from sqlalchemy import select

from dbdata import AsyncSessionLocal, PremiumDataSuper, OptionsCommandsStyle
import functions as funcs

import logging
import re
import unicodedata
import asyncio
import time
import colorsys
import random
import os
from io import BytesIO
import io
from typing import List

from PIL import Image, ImageColor, ImageDraw, ImageFont
import requests


# =========================
# HELPERS
# =========================

def is_valid_hex(cor: str) -> bool:
    return re.match(r"^#[0-9A-Fa-f]{6}$", cor) is not None


def limpar_unicode(texto: str) -> str:
    texto = unicodedata.normalize("NFKC", texto)
    return ''.join(c for c in texto if c.isprintable())


FONTES_DISPONIVEIS = {
    "aquire": "fonts/Aquire-BW0ox.otf",
    "orbitron": "fonts/Orbitron-VariableFont_wght.ttf",
    "cyberpunk": "fonts/Cyberpunk.ttf",
    "blad": "fonts/BLADRMF_.TTF",
    "playfair": "fonts/PlayfairDisplay-VariableFont_wght.ttf",
    "quantico": "fonts/Quantico-Italic.ttf",
    "horrendo": "fonts/horrendo.ttf",
    "arial": "fonts/arial.ttf",
    "cinzel": "fonts/CinzelDecorative-Regular.ttf",
    "pf uniform": "fonts/pf_uniform.ttf",
    "monad": "fonts/Monad.otf",
    "morena": "fonts/Morena.otf",
    "astra": "fonts/Astra-6RGXq.otf",
    "alexana": "fonts/Alexana.ttf",
    "nordic": "fonts/Nordic.tff",
    "transformers": "fonts/Transformers.ttf",
    "optimus princeps": "fonts/Optimus_Princeps.ttf",
    "gyre termes": "fonts/tex-gyre-termes.italic.otf",
}


def caminho_da_fonte(nome_fonte: str) -> str:
    """Retorna o caminho do arquivo de fonte a partir do nome salvo pelo usuário."""
    if not nome_fonte:
        return FONTES_DISPONIVEIS["arial"]
    return FONTES_DISPONIVEIS.get(nome_fonte.lower(), FONTES_DISPONIVEIS["arial"])


# =========================
# SELECTS / VIEWS DE CONFIG DE ESTILO DE COMANDOS
# =========================

class SelectBalanceConfigs(discord.ui.Select):
    def __init__(self):
        options_saldo = [
            discord.SelectOption(
                label="Saldo com imagem.",
                description="O saldo vai ser mostrado numa imagem decorada.",
                value="SALDO_IMAGEM"
            ),
            discord.SelectOption(
                label="Saldo com embed.",
                description="Saldo vai ser mostrado em um embed decorado.",
                value="SALDO_EMBED"
            )
        ]

        super().__init__(
            placeholder="Escolha o modo do seu comando de saldo.",
            min_values=1,
            max_values=1,
            options=options_saldo,
        )

    async def callback(self, interaction: discord.Interaction):
        resultado = self.values[0]

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(OptionsCommandsStyle).filter_by(user_id=interaction.user.id)
            )
            userdb = result.scalars().first()

            if not userdb:
                userdb = OptionsCommandsStyle(user_id=interaction.user.id, command_option_1=resultado)
                session.add(userdb)
            else:
                userdb.command_option_1 = resultado

            await session.commit()

        if resultado == "SALDO_IMAGEM":
            await interaction.response.send_message("✅ Saldo com imagem definido!", ephemeral=True)
        else:
            await interaction.response.send_message("✅ Saldo com embed definido!", ephemeral=True)


class UserConfigsCommandsOptions(discord.ui.View):
    def __init__(self, ctx_author_id: int):
        super().__init__(timeout=120)
        self.ctx_author_id = ctx_author_id
        self.add_item(SelectBalanceConfigs())


# =========================
# SUPORTE / GRADIENTE DE EMBED / HELP
# =========================

class SuporteView(discord.ui.View):
    def __init__(self, timeout=100):
        super().__init__(timeout=timeout)

        self.add_item(discord.ui.Button(
            label="┃ Top.gg ",
            url="https://top.gg/bot/1367932530938089472",
            emoji="<:topgg:1406323879130955957>"
        ))
        self.add_item(discord.ui.Button(
            label="┃ Discord Bot List ",
            url="https://discordbotlist.com/bots/keith",
            emoji="<:discordbotlist:1406323822705119292>"
        ))
        self.add_item(discord.ui.Button(
            label="┃ Discord Bots ",
            url="https://discord.bots.gg/bots/1367932530938089472",
            emoji="<:botgg:1406323770238701638>"
        ))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if hasattr(self, "message"):
            await self.message.edit(view=self)


async def gradiente(embed, msg, view, duracao=100):
    hue = random.random()
    passo = 0.03
    inicio = time.time()

    while not view.is_finished() and (time.time() - inicio < duracao):
        r, g, b = colorsys.hsv_to_rgb(hue, 1, 1)
        embed.color = discord.Color.from_rgb(int(r * 255), int(g * 255), int(b * 255))
        await msg.edit(embed=embed)

        hue = (hue + passo) % 1
        await asyncio.sleep(0.3)


class HelpPaginator(View):
    def __init__(self, embeds: List[discord.Embed], timeout: float = 60.0):
        super().__init__(timeout=timeout)
        self.embeds = embeds
        self.current_page = 0
        self.max_page = len(embeds) - 1

        self.first_page = Button(label="⏮", style=discord.ButtonStyle.grey)
        self.prev_page = Button(label="◀", style=discord.ButtonStyle.grey)
        self.page_counter = Button(label=f"Página 1/{len(embeds)}", style=discord.ButtonStyle.grey, disabled=True)
        self.next_page = Button(label="▶", style=discord.ButtonStyle.grey)
        self.last_page = Button(label="⏭", style=discord.ButtonStyle.grey)

        self.add_item(self.first_page)
        self.add_item(self.prev_page)
        self.add_item(self.page_counter)
        self.add_item(self.next_page)
        self.add_item(self.last_page)

        self.update_buttons()

        self.first_page.callback = self.first_page_callback
        self.prev_page.callback = self.prev_page_callback
        self.next_page.callback = self.next_page_callback
        self.last_page.callback = self.last_page_callback

    def update_buttons(self):
        self.first_page.disabled = self.current_page == 0
        self.prev_page.disabled = self.current_page == 0
        self.next_page.disabled = self.current_page == self.max_page
        self.last_page.disabled = self.current_page == self.max_page
        self.page_counter.label = f"Página {self.current_page + 1}/{self.max_page + 1}"

    async def first_page_callback(self, interaction: discord.Interaction):
        self.current_page = 0
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    async def prev_page_callback(self, interaction: discord.Interaction):
        self.current_page -= 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    async def next_page_callback(self, interaction: discord.Interaction):
        self.current_page += 1
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)

    async def last_page_callback(self, interaction: discord.Interaction):
        self.current_page = self.max_page
        self.update_buttons()
        await interaction.response.edit_message(embed=self.embeds[self.current_page], view=self)


def create_help_embeds():
    categories = {
        "Diversão": [
            "8ball", "bombardeio",
            "globo", "ship", "vidente", "fate",
            "rank", "rankmdbs", "vote", "perdeutudo",
            "abraço", "beijar", "cafuné", "pesquisaranime", "niver", "niverlist",
            "futuroservidor", "tomatar"
        ],
        "Economia": [
            "acoes", "daily", "roletadiaria",
            "pay", "poupança", "sacar", "diario", "saldos", "rankmdbs",
            "duelo", "corrida", "roleta", "roletarussa", "flipcoin",
            "tiroaoalvo", "pescar", "bolsadepeixes", "blackjack"
        ],
        "Economia Parte 2": [
            "niquel", "adivinharcor", "roletarussaduo", "acertarcarta", "bombgame"
        ],
        "Perfil": [
            "avatar", "avatarservidor", "banner", "statusvip",
            "perfil", "pfp", "serverbanner", "email", "emaillist", "configs",
            "setfonte", "escolherpxtext", "pegarfundo", "premium", "premiumstats"
        ],
        "Casamento": [
            "casar", "casal", "divorciar"],
        "Moderação": [
            "ban", "mute", "limpar", "unban", "configurarcanal", "configurarcanalgoodbye",
            "serverconfigs", "displayconfigs", "/rrcreate", "setlog", "clearlog", "warn",
            "warnslist", "unwarn", "configurarcanallevelup"
        ],
        "Informação": [
            "botinfo", "help", "userinfo", "ping", "serverinfo", "xp",
            "convite", "suporte"
        ],
        "CorridasKeith": [
            "corrida", "corridasolo"
        ],
        "notificações": [
            "addnotif", "desativarnotif"
        ]
    }

    embeds = []
    for category, commands_list in categories.items():
        embed = discord.Embed(
            title=f"Comandos - {category}",
            description="\n".join(f"`{cmd}`" for cmd in commands_list),
            color=discord.Color.blue()
        )
        embed.set_footer(text="Use <help [comando] para mais informações")
        embeds.append(embed)

    return embeds


# =========================
# MODAIS — PERFIL
# =========================

class EditColorModal(discord.ui.Modal, title="Editar Cor"):
    color = discord.ui.TextInput(label="Hex (#FFAABB)", required=True, placeholder="#2F3136")

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        c = self.color.value.strip()
        if is_valid_hex(c):
            await funcs.save_config(self.user_id, color=c)
            await interaction.response.send_message("✅ Cor atualizada!", ephemeral=True)
        else:
            await interaction.response.send_message("⚠️ HEX inválido.", ephemeral=True)


class EditBioModal(discord.ui.Modal, title="Editar Bio"):
    bio = discord.ui.TextInput(label="Nova bio", style=discord.TextStyle.paragraph, required=True, max_length=200)
    extra = discord.ui.TextInput(label="Emoji extra (opcional)", required=False, max_length=10)

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        await funcs.save_config(
            self.user_id,
            bio=self.bio.value.strip(),
            extra_emoji=self.extra.value.strip(),
        )
        await interaction.response.send_message("✅ Bio atualizada!", ephemeral=True)


class EditSobreMimModal(discord.ui.Modal, title="Editar +Sobre Mim"):
    genero = discord.ui.TextInput(label="Gênero", required=False)
    sexualidade = discord.ui.TextInput(label="Sexualidade", required=False)
    idade_18 = discord.ui.TextInput(label="Você tem 18 anos ou mais? (sim/não)", required=True)
    pronomes = discord.ui.TextInput(label="Pronomes", required=False)
    texto_extra = discord.ui.TextInput(label="Texto extra da bio", style=discord.TextStyle.paragraph, required=False, max_length=200)

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        idade_input = self.idade_18.value.strip().lower()
        idade_bool = idade_input in ("sim", "s", "+18", "18", "maior")

        await funcs.save_sobre_mim(
            self.user_id,
            genero=self.genero.value.strip() or None,
            sexualidade=self.sexualidade.value.strip() or None,
            idade_18=idade_bool,
            pronomes=self.pronomes.value.strip() or None,
            texto_extra=self.texto_extra.value.strip() or None,
        )
        await interaction.response.send_message("✅ Sobre mim atualizado!", ephemeral=True)


class EditBotao(discord.ui.Modal, title="Cor do Botão +Sobre Mim"):
    botao_style = discord.ui.TextInput(
        label="Cor do botão (azul/cinza/verde/vermelho)",
        placeholder="*use letra minúscula*",
        required=True
    )

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        estilo = self.botao_style.value.strip().lower()
        if estilo not in ("azul", "cinza", "verde", "vermelho"):
            estilo = "azul"
        await funcs.save_sobre_mim(self.user_id, botao_style=estilo)
        await interaction.response.send_message(f"✅ Estilo do botão atualizado para `{estilo}`!", ephemeral=True)


class EditFaixaColorModal(discord.ui.Modal, title="Editar Cor da Faixa"):
    faixa_color = discord.ui.TextInput(label="Hex (#123456)", required=True, placeholder="#1E1E1E")

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        c = self.faixa_color.value.strip()
        if is_valid_hex(c):
            await funcs.save_config(self.user_id, perfil_faixa_color=c)
            await interaction.response.send_message("✅ Cor da faixa atualizada!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ HEX inválido.", ephemeral=True)


class EditLayoutModal(discord.ui.Modal, title="Editar Layout"):
    faixa = discord.ui.TextInput(label="Modelo de faixa? (xp/perfil/id)", placeholder="xp, perfil ou id", required=True)
    avatar = discord.ui.TextInput(label="Modelo de avatar? (xp/perfil)", placeholder="xp ou perfil", required=True)

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        f, a = self.faixa.value.lower().strip(), self.avatar.value.lower().strip()
        if f not in ("xp", "perfil", "id") or a not in ("xp", "perfil"):
            return await interaction.response.send_message("❌ Use apenas 'xp', 'perfil' ou 'id'.", ephemeral=True)
        await funcs.save_config(self.user_id, layout_faixa=f, layout_avatar=a)
        await interaction.response.send_message("✅ Layout atualizado com sucesso!", ephemeral=True)


class ModalTamanhoPerfil(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Escolha as configurações do seu perfil.")

        self.tamanho_P_ = discord.ui.TextInput(
            label="Escolha o tamanho do perfil.",
            placeholder="Ex: min 100, max: 1000"
        )
        self.curvatura_da_faixa = discord.ui.TextInput(
            label="Escolha a curvatura da faixa.",
            placeholder="Ex: 1, max: 4"
        )

        self.add_item(self.tamanho_P_)
        self.add_item(self.curvatura_da_faixa)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            tamanho_int = int(self.tamanho_P_.value)
            curvatura_faixa_int = int(self.curvatura_da_faixa.value)
        except ValueError:
            await interaction.response.send_message("Por favor, insira números válidos.", ephemeral=True)
            return

        if curvatura_faixa_int > 4:
            return await interaction.response.send_message("Não coloque uma curvatura acima de 4.", ephemeral=True)
        if tamanho_int > 1000:
            return await interaction.response.send_message("Não coloque um tamanho maior que mil.", ephemeral=True)
        if tamanho_int < 100:
            return await interaction.response.send_message("Não coloque um número menor que 100.", ephemeral=True)
        if curvatura_faixa_int < 1:
            return await interaction.response.send_message("Não coloque uma curvatura menor que 1.", ephemeral=True)

        await funcs.set_perfil_size(interaction.user.id, tamanho_int, curvatura_faixa_int)

        await interaction.response.send_message(
            f"Perfil configurado!\nTamanho: {tamanho_int}\nCurvatura: {curvatura_faixa_int}",
            ephemeral=True
        )


class ModalTranslucidez(discord.ui.Modal, title="Escolha a translucidez da faixa."):
    translucidez_faixa_new = discord.ui.TextInput(
        label="Digite a translucidez desejada.",
        placeholder="Ex: 10, max: 255",
        max_length=3
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            numero_translucidez = int(self.translucidez_faixa_new.value)
        except ValueError:
            return await interaction.response.send_message("Por favor, insira um número válido.", ephemeral=True)

        if not (0 <= numero_translucidez <= 255):
            return await interaction.response.send_message("Use um valor entre 0 e 255.", ephemeral=True)

        await funcs.set_translucidez_faixa(interaction.user.id, numero_translucidez)

        await interaction.response.send_message(
            "Translucidez configurada com sucesso, use <perfil para ver o resultado.",
            ephemeral=True
        )


class ModalForBorder(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Decida a cor e espessura da borda.")

        self.input_one = discord.ui.TextInput(label="Cor da borda.", placeholder="Ex: #000000 = Preto", max_length=7)
        self.input_two = discord.ui.TextInput(label="Decida o tamanho da borda.", placeholder='Ex: 4', max_length=2)
        self.add_item(self.input_one)
        self.add_item(self.input_two)

    async def on_submit(self, interaction: discord.Interaction):
        cor = self.input_one.value.strip()
        if not is_valid_hex(cor):
            return await interaction.response.send_message("❌ HEX inválido para a cor da borda.", ephemeral=True)

        try:
            tamanho = int(self.input_two.value)
        except ValueError:
            return await interaction.response.send_message("❌ Tamanho da borda inválido.", ephemeral=True)

        if tamanho > 10:
            return await interaction.response.send_message("Não coloque uma espessura maior que 10 na borda.", ephemeral=True)
        if tamanho < 0:
            return await interaction.response.send_message("Não coloque uma espessura negativa na borda.", ephemeral=True)

        await funcs.set_perfil_border(interaction.user.id, cor, tamanho)

        await interaction.response.send_message("✅ Alterações feitas com sucesso!", ephemeral=True)


# =========================
# MODAIS — XP
# =========================

class EditXPTextColorModal(discord.ui.Modal, title="Cor do Texto do XP"):
    cor = discord.ui.TextInput(label="Cor HEX do texto", placeholder="#FFFFFF", required=True)

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        c = self.cor.value.strip()
        if is_valid_hex(c):
            await funcs.save_config(self.user_id, xp_text_color=c)
            await interaction.response.send_message("✅ Cor do texto atualizada!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ HEX inválido.", ephemeral=True)


class EditXPBarColorModal(discord.ui.Modal, title="Cor da Barra de XP"):
    cor = discord.ui.TextInput(label="Cor HEX da barra de progresso", placeholder="#64B4FF", required=True)

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        c = self.cor.value.strip()
        if is_valid_hex(c):
            await funcs.save_config(self.user_id, xp_bar_color=c)
            await interaction.response.send_message("✅ Cor da barra de XP atualizada!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ HEX inválido.", ephemeral=True)


class EditFaixaXPColorModal(discord.ui.Modal, title="Editar Cor da Faixa"):
    faixa_color = discord.ui.TextInput(label="Hex (#123456)", required=True, placeholder="#1E1E1E")

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id

    async def on_submit(self, interaction: discord.Interaction):
        c = self.faixa_color.value.strip()
        if is_valid_hex(c):
            await funcs.save_config(self.user_id, faixa_color=c)
            await interaction.response.send_message("✅ Cor da faixa atualizada!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ HEX inválido.", ephemeral=True)


class EscolherPxDaFonteModal(Modal, title="Escolha o PX dos textos do seu perfil."):
    fonte_nome_px = discord.ui.TextInput(label="PX da do nome.", placeholder="EX: 30", max_length=2)
    fonte_bio_px = discord.ui.TextInput(label="PX da Bio.", placeholder="Ex: 40", max_length=2)
    fonte_xp_px = discord.ui.TextInput(label="PX do XP.", placeholder="Ex: 12", max_length=2)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            nome_px = int(self.fonte_nome_px.value)
            bio_px = int(self.fonte_bio_px.value)
            xp_px = int(self.fonte_xp_px.value)
        except ValueError:
            return await interaction.response.send_message(
                "Por favor, insira apenas números válidos para os tamanhos de fonte!",
                ephemeral=True
            )

        await funcs.set_font_sizes(interaction.user.id, nome_px, bio_px, xp_px)

        embed_px_font = discord.Embed(
            title="PX dos textos do perfil.",
            description=(
                f"* Seu nome no perfil agora tem: {nome_px}px\n"
                f"* Sua bio no perfil agora tem: {bio_px}px\n"
                f"* A descrição do XP agora tem: {xp_px}px"
            ),
            color=discord.Color.dark_blue()
        )
        embed_px_font.set_footer(text=f"Requisitado por {interaction.user.name}", icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message(embed=embed_px_font)


class EscolherFonteModal(Modal, title="Escolha sua fonte."):
    fonte = discord.ui.TextInput(label="Escolha uma fonte.", placeholder="Ex: Orbitron", max_length=20, required=True)

    async def on_submit(self, interaction: discord.Interaction):
        nome_fonte = self.fonte.value.strip()
        await funcs.set_fonte(interaction.user.id, nome_fonte)
        await interaction.response.send_message(f"Fonte `{nome_fonte}` adicionada com sucesso.", ephemeral=True)


class BotoesPaginamentoCatalogoFonts(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="Mostrar catálogo")
    async def botaofontecatalogoPoróximapage(self, interaction: discord.Interaction, button: discord.ui.Button):
        embedpage1 = discord.Embed(
            title="Catálogo de fontes.",
            description="Olá, aqui temos o catálogo.\n\n* Aquire.\n* Cyberpunk\n* Blad\n* Arial\n* Orbitron\n* Horrendo\n* playfair\n* cinzel\n* quantico",
            color=discord.Color.dark_blue()
        )
        embedpage1.set_footer(text=f"Requisitado por {interaction.user.name}")

        await interaction.response.send_message(embed=embedpage1, view=EnviarModalComBotao())

    @discord.ui.button(label="Escolher Px dos textos do perfil.", style=discord.ButtonStyle.grey)
    async def interaction_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EscolherPxDaFonteModal())


class EnviarModalComBotao(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="Escolher fonte.")
    async def enviarmodaldafonte(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EscolherFonteModal())


# =========================
# VIEWS — PLATAFORMA / PERFIL / XP
# =========================

class PlataformaView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction):
        return interaction.user.id == self.user_id

    @discord.ui.button(label="💻 PC", style=discord.ButtonStyle.primary)
    async def pc(self, interaction: discord.Interaction, button: discord.ui.Button):
        await funcs.set_plataforma(self.user_id, "desktop")
        await interaction.response.send_message(
            "✅ Plataforma definida como **PC**. Agora use `<perfil` novamente.",
            ephemeral=True
        )

    @discord.ui.button(label="📱 Celular", style=discord.ButtonStyle.secondary)
    async def mobile(self, interaction: discord.Interaction, button: discord.ui.Button):
        await funcs.set_plataforma(self.user_id, "mobile")
        await interaction.response.send_message(
            "✅ Plataforma definida como **Celular**. Agora use `<perfil` novamente.",
            ephemeral=True
        )


class PerfilConfigView(discord.ui.View):
    """View principal de configuração do <perfil. O botão de exibir/ocultar casamento é
    adicionado dinamicamente em `build`, pois depende de uma consulta assíncrona ao banco
    (e Views não podem fazer await dentro de __init__)."""

    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.add_item(self.EditarFundo())
        self.add_item(self.EditarCor())
        self.add_item(self.EditarBio())
        self.add_item(self.EditarSobreMim())
        self.add_item(self.EditarBotaoSobreMim())
        self.add_item(self.EditarFaixa())
        self.add_item(self.EditarLayout())
        self.add_item(self.ToggleBadges())
        self.add_item(self.ToggleXPBar())
        self.add_item(self.EscolherTamanhoPerfilDiscord())
        self.add_item(self.EscolherTranslucidezDaFaixaBUtton())
        self.add_item(self.BorderBUttonOpenModal())
        self.add_item(self.Resetar())

    @classmethod
    async def build(cls, user_id: int) -> "PerfilConfigView":
        view = cls(user_id)
        if await funcs.esta_casado(user_id):
            view.add_item(view.ToggleCasamento())
        return view

    async def validate(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Apenas você pode editar seu perfil.", ephemeral=True)
            return False
        return True

    class EditarFundo(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Editar Fundo", style=discord.ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            view = self.view
            if not await view.validate(interaction):
                return

            await interaction.response.send_message(
                "📸 Envie uma imagem para o fundo (você tem 60s)...", ephemeral=True
            )

            def check(m):
                return m.author.id == view.user_id and m.attachments

            try:
                msg = await interaction.client.wait_for("message", check=check, timeout=60)
            except asyncio.TimeoutError:
                return await interaction.followup.send("⏰ Tempo esgotado.", ephemeral=True)

            att = msg.attachments[0]
            url = att.url
            content_type = att.content_type

            allowed_types = ["image/png", "image/gif", "image/jpeg", "image/webp"]
            if content_type not in allowed_types:
                await interaction.followup.send(
                    "❌ Apenas imagens PNG, GIF, JPG ou WebP são aceitas.", ephemeral=True
                )
                return

            try:
                resp = requests.get(url, timeout=10)
                img_data = resp.content

                img = Image.open(BytesIO(img_data))
                actual_format = img.format.upper() if img.format else "UNKNOWN"

                os.makedirs("fundos", exist_ok=True)

                if actual_format == "GIF":
                    with open(f"fundos/{view.user_id}.gif", "wb") as fh:
                        fh.write(img_data)
                else:
                    if img.mode != "RGBA":
                        img = img.convert("RGBA")
                    img.save(f"fundos/{view.user_id}.png", "PNG")

                await funcs.save_config(view.user_id, background=url)
                await msg.delete()
                await interaction.followup.send("✅ Fundo salvo com sucesso!", ephemeral=True)

            except Exception as e:
                logging.warning(f"Erro ao salvar fundo: {e}")
                await interaction.followup.send("❌ Erro ao processar a imagem. Tente outra.", ephemeral=True)

    class EditarCor(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Editar Cor", style=discord.ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            if not await self.view.validate(interaction):
                return
            await interaction.response.send_modal(EditColorModal(self.view.user_id))

    class EditarBio(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Editar Bio", style=discord.ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            if not await self.view.validate(interaction):
                return
            await interaction.response.send_modal(EditBioModal(self.view.user_id))

    class EditarSobreMim(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Editar +Sobre Mim", style=discord.ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            if not await self.view.validate(interaction):
                return
            await interaction.response.send_modal(EditSobreMimModal(self.view.user_id))

    class EditarBotaoSobreMim(discord.ui.Button):
        def __init__(self):
            super().__init__(label="cor do Botão Sobre Mim", style=discord.ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            if not await self.view.validate(interaction):
                return
            await interaction.response.send_modal(EditBotao(self.view.user_id))

    class EditarFaixa(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Editar Faixa", style=discord.ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            if not await self.view.validate(interaction):
                return
            await interaction.response.send_modal(EditFaixaColorModal(self.view.user_id))

    class EditarLayout(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Layout (faixa/avatar/id)", style=discord.ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            if not await self.view.validate(interaction):
                return
            await interaction.response.send_modal(EditLayoutModal(self.view.user_id))

    class ToggleBadges(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Mostrar Badges (Sim/Não)", style=discord.ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            if not await self.view.validate(interaction):
                return
            cfg = await funcs.load_config(self.view.user_id)
            atual = cfg.get("mostrar_badges", True)
            await funcs.save_config(self.view.user_id, mostrar_badges=not atual)
            status = "✅ agora visíveis" if not atual else "🚫 agora ocultas"
            await interaction.response.send_message(f"🏅 Badges {status} no seu perfil.", ephemeral=True)

    class ToggleXPBar(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Mostrar barra XP no <perfil", style=discord.ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            if not await self.view.validate(interaction):
                return
            cfg = await funcs.load_config(self.view.user_id)
            atual = cfg.get("mostrar_xp_bar", False)
            await funcs.save_config(self.view.user_id, mostrar_xp_bar=not atual)
            status = "ativada ✅" if not atual else "desativada 🚫"
            await interaction.response.send_message(f"📊 Barra de XP no -perfil {status}.", ephemeral=True)

    class ToggleCasamento(discord.ui.Button):
        def __init__(self):
            super().__init__(label="💍 Exibir Casamento", style=discord.ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            if not await self.view.validate(interaction):
                return
            cfg = await funcs.load_config(self.view.user_id)
            layout = cfg.get("layout_faixa", "perfil")
            mostrar_xp = cfg.get("mostrar_xp_bar", False)

            if layout == "perfil" and mostrar_xp:
                await interaction.response.send_message(
                    "❌ Barra de xp e exibir casal não cabem no layout de faixa perfil juntos", ephemeral=True
                )
                return

            atual = cfg.get("mostrar_casamento", False)
            await funcs.save_config(self.view.user_id, mostrar_casamento=not atual)
            status = "agora visível 💖" if not atual else "oculto 🔕"
            await interaction.response.send_message(f"📘 Estado de casamento no perfil: {status}.", ephemeral=True)

    class Resetar(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Resetar", style=discord.ButtonStyle.danger)

        async def callback(self, interaction: discord.Interaction):
            if not await self.view.validate(interaction):
                return
            await funcs.save_config(
                self.view.user_id,
                background="",
                color="#2F3136",
                bio="Sem bio.",
                extra_emoji="",
                mostrar_badges=True,
            )
            await interaction.response.send_message("✅ Perfil resetado!", ephemeral=True)

    class EscolherTamanhoPerfilDiscord(discord.ui.Button):
        def __init__(self):
            super().__init__(style=discord.ButtonStyle.grey, label="Tamanho do Perfil e Curvatura da faixa.")

        async def callback(self, interaction: discord.Interaction):
            if not await self.view.validate(interaction):
                return
            await interaction.response.send_modal(ModalTamanhoPerfil())

    class EscolherTranslucidezDaFaixaBUtton(discord.ui.Button):
        def __init__(self):
            super().__init__(style=discord.ButtonStyle.grey, label="Translucidez da faixa.")

        async def callback(self, interaction: discord.Interaction):
            if not await self.view.validate(interaction):
                return
            await interaction.response.send_modal(ModalTranslucidez())

    class BorderBUttonOpenModal(discord.ui.Button):
        def __init__(self):
            super().__init__(style=discord.ButtonStyle.grey, label="Ajudar borda da faixa.")

        async def callback(self, interaction: discord.Interaction):
            if not await self.view.validate(interaction):
                return
            await interaction.response.send_modal(ModalForBorder())


class XPConfigView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.add_item(self.CorBarraXP())
        self.add_item(self.CorFaixaXP())
        self.add_item(self.CorTextoXP())
        self.add_item(self.TrocarFundoXP())

    async def validate(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ Apenas você pode editar suas configurações.", ephemeral=True)
            return False
        return True

    class CorBarraXP(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Cor da Barra de XP", style=discord.ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            if not await self.view.validate(interaction):
                return
            await interaction.response.send_modal(EditXPBarColorModal(self.view.user_id))

    class CorFaixaXP(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Cor da Faixa do XP", style=discord.ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            if not await self.view.validate(interaction):
                return
            await interaction.response.send_modal(EditFaixaXPColorModal(self.view.user_id))

    class CorTextoXP(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Cor do Texto do XP", style=discord.ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            if not await self.view.validate(interaction):
                return
            await interaction.response.send_modal(EditXPTextColorModal(self.view.user_id))

    class TrocarFundoXP(discord.ui.Button):
        def __init__(self):
            super().__init__(label="Fundo do XP", style=discord.ButtonStyle.secondary)

        async def callback(self, interaction: discord.Interaction):
            view = self.view
            if not await view.validate(interaction):
                return
            await interaction.response.send_message("📸 Envie uma imagem para o fundo do comando `-xp` (você tem 60s)...", ephemeral=True)

            def check(m):
                return m.author.id == view.user_id and m.attachments and m.attachments[0].content_type.startswith("image/")

            try:
                msg = await interaction.client.wait_for("message", check=check, timeout=60)
            except asyncio.TimeoutError:
                return await interaction.followup.send("⏰ Tempo esgotado.", ephemeral=True)

            att = msg.attachments[0]
            url = att.url
            try:
                resp = requests.get(url, timeout=10)
                img = Image.open(BytesIO(resp.content))
                img.verify()
                img = Image.open(BytesIO(resp.content)).convert("RGBA").resize((600, 240))

                os.makedirs("fundos_xp", exist_ok=True)
                img.save(f"fundos_xp/{view.user_id}.png", "PNG")
                await funcs.save_config(view.user_id, xp_background=url)
                await msg.delete()
                await interaction.followup.send("✅ Fundo do XP salvo com sucesso!", ephemeral=True)
            except Exception as e:
                logging.warning(f"Erro ao salvar fundo XP: {e}")
                await interaction.followup.send("❌ Imagem inválida. Tente outra.", ephemeral=True)


# =========================
# PREMIUM
# =========================

class ModalForModelProfile(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Escolha O modo do perfil")

        self.texinput_1 = discord.ui.TextInput(label="Modo", placeholder="Ex: GIF ou estatico", required=True, default="estatico")
        self.add_item(self.texinput_1)

    async def on_submit(self, interaction: discord.Interaction):
        modo = self.texinput_1.value.strip().lower()
        await funcs.set_perfil_model(interaction.user.id, modo)

        if modo == "gif":
            await interaction.response.send_message("✅ Modo gif foi ativado com sucesso.", ephemeral=True)
        elif modo == "estatico":
            await interaction.response.send_message("✅ Modo estatico foi ativado com sucesso.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Digitou certo? Nada foi ativado.", ephemeral=True)


class ModalGradientColors(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Deseja ativar o gradiente.")

        self.color1 = discord.ui.TextInput(label="Cor 1", placeholder="Ex: #FFFFFF", max_length=10, required=True)
        self.color2 = discord.ui.TextInput(label="Cor 2", placeholder="Ex: #FF234F", max_length=10, required=False)
        self.color3 = discord.ui.TextInput(label="Cor 3", placeholder="Ex: #FF176F", max_length=10, required=False, default="")
        self.color4 = discord.ui.TextInput(label="Cor 4", placeholder="Ex: #FFF987", max_length=10, required=False, default="")
        self.color5 = discord.ui.TextInput(label="Cor 5", placeholder="Ex: #FFFOII", max_length=10, required=False, default="")

        self.add_item(self.color1)
        self.add_item(self.color2)
        self.add_item(self.color3)
        self.add_item(self.color4)
        self.add_item(self.color5)

    async def on_submit(self, interaction: discord.Interaction):
        colors = []

        if self.color1.value.strip():
            colors.append(self.color1.value.strip())

        for color_input in (self.color2, self.color3, self.color4, self.color5):
            if color_input.value and color_input.value.strip():
                colors.append(color_input.value.strip())

        if not colors:
            await interaction.response.send_message("❌ É necessário fornecer pelo menos uma cor!", ephemeral=True)
            return

        try:
            await funcs.set_gradient_colors(interaction.user.id, colors)
            cores_formatadas = ", ".join(colors)
            await interaction.response.send_message(
                f"✅ Gradiente configurado com sucesso!\n**Cores:** {cores_formatadas}", ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao salvar as cores: {str(e)}", ephemeral=True)


class PremiumUserButtonsForCustomization(discord.ui.View):
    def __init__(self, ctx_author_id):
        super().__init__(timeout=120)
        self.ctx_author_id = ctx_author_id

    async def _eh_premium(self, user_id: int) -> bool:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(PremiumDataSuper).filter_by(user_id=user_id))
            return result.scalars().first() is not None

    @discord.ui.button(label="Mostrar catálogo de fontes Premium.", style=discord.ButtonStyle.grey, emoji='🈹')
    async def catalog_fonts(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx_author_id != interaction.user.id:
            return await interaction.response.send_message("Isso não é pra você, saia!", ephemeral=True)

        if not await self._eh_premium(interaction.user.id):
            return await interaction.response.send_message("Você não é Premium.", ephemeral=True)

        m = discord.Embed(
            title="Catálogo de Fontes.",
            description=(
                "- Andromeda.\n"
                "- Nordic.\n"
                "- Azonix.\n"
                "- Nebula.\n"
                "- Zector.\n"
                "- Meroona.\n"
            ),
            color=discord.Color.gold(),
            timestamp=discord.utils.utcnow()
        )

        m.set_thumbnail(url=interaction.user.display_avatar.url)
        m.set_footer(text=f'{interaction.user.name}', icon_url=interaction.user.display_avatar.url)

        view = discord.ui.View()
        button_ = discord.ui.Button(label="Escolher Fonte.", style=discord.ButtonStyle.grey)

        async def callback(inner_interaction: discord.Interaction):
            await inner_interaction.response.send_modal(EscolherFonteModal())

        button_.callback = callback
        view.add_item(button_)

        await interaction.response.send_message(embed=m, view=view, ephemeral=True)

    @discord.ui.button(label="Nome Gradiente", style=discord.ButtonStyle.grey, emoji='🔮')
    async def gradiente_select_text(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx_author_id != interaction.user.id:
            return await interaction.response.send_message("Isso não é pra você, saia!", ephemeral=True)

        if not await self._eh_premium(interaction.user.id):
            return await interaction.response.send_message("Você não é Premium.", ephemeral=True)

        await interaction.response.send_modal(ModalGradientColors())

    @discord.ui.button(label="GIFMODE", style=discord.ButtonStyle.red, emoji='📹')
    async def gifmode_for_p(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.ctx_author_id != interaction.user.id:
            return await interaction.response.send_message("Isso não é pra você, saia!", ephemeral=True)

        if not await self._eh_premium(interaction.user.id):
            return await interaction.response.send_message("Você não é Premium.", ephemeral=True)

        await interaction.response.send_modal(ModalForModelProfile())


# =========================
# COG PRINCIPAL
# =========================

class ConfigsForPerfilCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="configs", help="Configurações do usuario para o bot.", category="Geral")
    async def configs(self, ctx: commands.Context):
        view_perfil = await PerfilConfigView.build(ctx.author.id)
        view_xp = XPConfigView(ctx.author.id)

        view_configs = discord.ui.View()
        view_configs2 = discord.ui.View()
        view_configs4 = discord.ui.View()

        button_configs_profile = discord.ui.Button(label="Abrir", style=discord.ButtonStyle.grey, emoji='📼')
        button_configs_xp = discord.ui.Button(label="Abrir", style=discord.ButtonStyle.grey, emoji='🔮')
        button_commands_style_configs = discord.ui.Button(label="Abrir", style=discord.ButtonStyle.grey, emoji='🏮')

        embed_perfil = discord.Embed(
            title="🔧🌠 Suas configurações de perfil:",
            description="Botões de configurações que dizem respeito ao comando `<perfil`",
            color=discord.Color.blurple()
        )
        embed_xp = discord.Embed(
            title="🔧🌠 Suas configurações do <xp:",
            description="Botões de configurações que dizem respeito ao comando `<xp`",
            color=discord.Color.dark_teal()
        )
        embed_premium = discord.Embed(
            title="⚗️🌆 Configurações Premium.",
            description="Aqui você pode configurar coisa relacionadas ao <perfil e outros benefícios vip.",
            color=discord.Color.dark_purple()
        )
        embed_plat = discord.Embed(
            title="🔧🌠 Mude para sua plataforma atual:",
            description="Escolha a plataforma onde você está usando o Discord",
            color=discord.Color.dark_purple()
        )
        embed_style_commands = discord.Embed(
            title="💻📱 Modifique o estilo dos comandos!",
            description="Aqui você pode modificar o estilo de alguns comandos.",
            color=discord.Color.blurple()
        )

        async def call_profile(interaction: discord.Interaction):
            if interaction.user.id != ctx.author.id:
                return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)
            await interaction.response.send_message(embed=embed_perfil, view=view_perfil, ephemeral=True)

        async def call_xp(interaction: discord.Interaction):
            if interaction.user.id != ctx.author.id:
                return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)
            await interaction.response.send_message(embed=embed_xp, view=view_xp, ephemeral=True)

        async def call_premium(interaction: discord.Interaction):
            if interaction.user.id != ctx.author.id:
                return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)

            async with AsyncSessionLocal() as session:
                result = await session.execute(select(PremiumDataSuper).filter_by(user_id=ctx.author.id))
                userdb = result.scalars().first()
                if userdb:
                    await interaction.response.send_message(embed=embed_premium, view=PremiumUserButtonsForCustomization(ctx.author.id), ephemeral=True)
                else:
                    await interaction.response.send_message("❌ Você não é Premium!", ephemeral=True)

        async def call_style_commands(interaction: discord.Interaction):
            if interaction.user.id != ctx.author.id:
                return await interaction.response.send_message("❌ Somente o autor do comando pode clicar nesses botões!", ephemeral=True)
            await interaction.response.send_message(embed=embed_style_commands, view=UserConfigsCommandsOptions(ctx.author.id), ephemeral=True)

        button_configs_profile.callback = call_profile
        button_configs_xp.callback = call_xp
        button_commands_style_configs.callback = call_style_commands

        view_configs.add_item(button_configs_profile)
        view_configs2.add_item(button_configs_xp)
        view_configs4.add_item(button_commands_style_configs)

        embed_1 = discord.Embed(title="📼 Configurações do <perfil", description="Clique no botão para abrir elas.", color=discord.Color.purple(), timestamp=discord.utils.utcnow())
        embed_2 = discord.Embed(title="🔮 Configurações do <xp", description="Clique no botão para abrir elas.", color=discord.Color.purple(), timestamp=discord.utils.utcnow())
        embed_3 = discord.Embed(title="💎 Configurações do <perfil premium", description="Clique no botão para abrir elas.", color=discord.Color.purple(), timestamp=discord.utils.utcnow())
        embed_4 = discord.Embed(title="🏮 Configurações do estilo dos comandos.", description="Clique no botão para abrir elas.", color=discord.Color.purple(), timestamp=discord.utils.utcnow())

        await ctx.reply(embed=embed_1, view=view_configs)
        await ctx.send(embed=embed_2, view=view_configs2)
        await ctx.send(embed=embed_4, view=view_configs4)

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(PremiumDataSuper).filter_by(user_id=ctx.author.id))
            userdb = result.scalars().first()
            if userdb:
                view_configs3 = discord.ui.View()
                button_configs_vip = discord.ui.Button(label="Abrir", style=discord.ButtonStyle.blurple, emoji='💎')
                button_configs_vip.callback = call_premium
                view_configs3.add_item(button_configs_vip)
                await ctx.send(embed=embed_3, view=view_configs3)

        await ctx.send(embed=embed_plat, view=PlataformaView(ctx.author.id))

    @commands.command(name="xp", help="Mostra seu xp.")
    async def xp(self, ctx: commands.Context, membro: discord.Member = None):
        user = membro or ctx.author
        nome_visivel = limpar_unicode(user.display_name)

        nivel, xp_restante, xp_total = await funcs.calcular_nivel_e_xp(user.id, ctx.guild.id)
        xp_universal = await funcs.get_xp_universal(user.id)

        cfg = await funcs.load_config(user.id)
        cor_barra = cfg.get("xp_bar_color", "#64B4FF")
        cor_faixa = cfg.get("faixa_color", "#1E1E1E")
        cor_texto = cfg.get("xp_text_color", "#FFFFFF")

        largura, altura = 600, 240
        padding_x = 30
        avatar_tamanho = 96
        barra_largura = 300
        barra_altura = 20
        espacamento_vertical = 8
        faixa_radius = 30

        try:
            bg = Image.open(f'fundos_xp/{user.id}.png').convert('RGBA').resize((largura, altura))
        except Exception:
            try:
                bg = Image.open("assets/banner_bg.webp").convert("RGBA").resize((largura, altura))
            except Exception:
                bg = Image.new("RGBA", (largura, altura), (20, 20, 20, 255))

        draw = ImageDraw.Draw(bg)

        faixa_largura = largura - 40
        faixa_altura = altura - 40
        faixa_x = 20
        faixa_y = 20

        try:
            faixa_rgb = ImageColor.getrgb(cor_faixa)
        except Exception:
            faixa_rgb = (60, 60, 60)

        faixa_canvas = Image.new("RGBA", (faixa_largura, faixa_altura), (0, 0, 0, 0))
        faixa_cinza = Image.new("RGBA", (faixa_largura, faixa_altura), (*faixa_rgb, 150))
        faixa_mask = Image.new("L", (faixa_largura, faixa_altura), 0)
        ImageDraw.Draw(faixa_mask).rounded_rectangle((0, 0, faixa_largura, faixa_altura), radius=faixa_radius, fill=255)
        faixa_canvas.paste(faixa_cinza, (0, 0), faixa_mask)
        bg.alpha_composite(faixa_canvas, dest=(faixa_x, faixa_y))

        avatar_bytes = await user.display_avatar.read()
        avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA").resize((avatar_tamanho, avatar_tamanho))
        avatar_bg = Image.new("RGBA", (avatar_tamanho, avatar_tamanho), (30, 30, 30, 255))
        avatar_mask = Image.new("L", (avatar_tamanho, avatar_tamanho), 0)
        ImageDraw.Draw(avatar_mask).rounded_rectangle((0, 0, avatar_tamanho, avatar_tamanho), radius=20, fill=255)
        avatar_bg.paste(avatar, (0, 0), avatar_mask)
        avatar_y = faixa_y + (faixa_altura - avatar_tamanho) // 2
        bg.paste(avatar_bg, (padding_x, avatar_y), avatar_mask)

        fonte_nome_arquivo = await funcs.get_fonte(user.id)
        caminho_fonte = caminho_da_fonte(fonte_nome_arquivo)

        try:
            fonte_nome = ImageFont.truetype(caminho_fonte, 24)
            fonte_xp = ImageFont.truetype(caminho_fonte, 18)
        except Exception:
            fonte_nome = ImageFont.truetype(FONTES_DISPONIVEIS["arial"], 24)
            fonte_xp = ImageFont.truetype(FONTES_DISPONIVEIS["arial"], 18)

        info_x = padding_x + avatar_tamanho + 20
        centro_y = faixa_y + faixa_altura // 2

        draw.text((info_x, centro_y - barra_altura - espacamento_vertical - 20), nome_visivel, font=fonte_nome, fill=cor_texto)

        barra_x = info_x
        barra_y = centro_y - barra_altura // 2
        progresso = min(xp_restante / 1000, 1.0)
        barra_cheia = int(barra_largura * progresso)

        try:
            cor_rgb = ImageColor.getrgb(cor_barra)
        except Exception:
            cor_rgb = (100, 180, 255)

        barra_fundo = Image.new("RGBA", (barra_largura, barra_altura), (100, 100, 100, 180))
        fundo_mask = Image.new("L", (barra_largura, barra_altura), 0)
        ImageDraw.Draw(fundo_mask).rounded_rectangle((0, 0, barra_largura, barra_altura), radius=10, fill=255)
        bg.paste(barra_fundo, (barra_x, barra_y), fundo_mask)

        if barra_cheia > 0:
            preenchida = Image.new("RGBA", (barra_cheia, barra_altura), cor_rgb)
            preenchida_mask = Image.new("L", (barra_cheia, barra_altura), 0)
            ImageDraw.Draw(preenchida_mask).rounded_rectangle((0, 0, barra_cheia, barra_altura), radius=10, fill=255)
            bg.paste(preenchida, (barra_x, barra_y), preenchida_mask)

        draw.rounded_rectangle((barra_x, barra_y, barra_x + barra_largura, barra_y + barra_altura), radius=10, outline="white", width=2)
        draw.text((barra_x, barra_y + barra_altura + espacamento_vertical), f"Nível {nivel} • XP {xp_restante}/1000", font=fonte_xp, fill=cor_texto)
        draw.text((barra_x, barra_y + barra_altura + espacamento_vertical + 24), f"XP universal: {xp_universal}", font=fonte_xp, fill=cor_texto)

        buffer = io.BytesIO()
        bg.save(buffer, format="PNG")
        buffer.seek(0)
        await ctx.send(file=discord.File(buffer, filename="xp.png"))

    @commands.command(name="vote")
    async def vote(self, ctx):
        embed = discord.Embed(
            title="<:card:1406323715590848634>  Gostaria de dar uma ajudinha pro keith? ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ",
            description="Escolha abaixo um dos links para contribuir gratuitamente:",
            color=discord.Color.red()
        )
        view = SuporteView(timeout=100)
        msg = await ctx.reply(embed=embed, view=view)
        view.message = msg

        asyncio.create_task(gradiente(embed, msg, view, duracao=100))

    @commands.command(name="ajuda", aliases=["help"])
    async def help_command(self, ctx):
        embeds = create_help_embeds()
        view = HelpPaginator(embeds)
        await ctx.send(embed=embeds[0], view=view)


async def setup(bot):
    await bot.add_cog(ConfigsForPerfilCog(bot))
