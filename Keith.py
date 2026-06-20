import discord
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv
from dbdata import Base, UserMDBs, AsyncSessionLocal, init_db, XpGlobal, UserXP, ChannelLogsConfiguration, DataForWarns, DataForGuildWarns, OptionsCommandsStyle
from datetime import datetime 
import psutil
from sqlalchemy import select
import logging
import platform
from discord.ui import Modal, View, Button
from discord.ext.commands import when_mentioned_or
from PIL import Image, ImageDraw, ImageColor, ImageFilter, ImageFont
from io import BytesIO
import aiohttp
from sqlalchemy import String, Integer, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from discord.ext import tasks
from typing import List
import math
from dbdata_server import AsyncSessionServerConfigs, DataForExtrasForGoodbyeMessage, DataForExtrasForWelcomeMessage, DataForGoodbyeMessage, BancoDeDadosParaMensagemDeBemVindoPersonalizada, init_db_server, ChatForMessageUperLevelXp
from datetime import datetime, date
from functionspillow import desenhar_layout_perfil, desenhar_layout_perfil_gif, desenhar_layout_xp, desenhar_layout_xp_gif, limpar_unicode, caminho_da_fonte, FONTES_DISPONIVEIS, FONTE_PADRAO
from database_sql import init_db_editor
import functions as funcs
from functions import verificar_premium
logging.basicConfig(level=logging.INFO)

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True
intents.typing = True
intents.presences = False
intents.reactions = True

TOKEN = os.getenv('TOKEN')

bot = commands.Bot(
    command_prefix=when_mentioned_or('<'),
    case_insensitive=True,
    intents=intents,
    help_command=None
)

# =========================
# FUNÇÕES DE IMAGEM (WELCOME/GIF)
# =========================

from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageColor, ImageSequence

async def pegar_avatar_pillow(user: discord.User | discord.Member, tamanho: int = 128) -> Image.Image:
    avatar_url = user.display_avatar.with_format('png').with_size(tamanho)
    async with aiohttp.ClientSession() as session:
        async with session.get(str(avatar_url)) as resp:
            if resp.status != 200:
                raise Exception(f"Não foi possível baixar o avatar ({resp.status})")
            avatar_bytes = await resp.read()
    return Image.open(BytesIO(avatar_bytes)).convert("RGBA")

async def gerar_gif_personalizado_layout2(
    fundo_path, avatar_path, texto_nome="The Love Marcos", texto_sub="Bem vindo ao servidor.",
    translucidez_faixa=160, cor_faixa=(100, 180, 255), fonte_caminho='fonts/arial.ttf',
    tamanho_nome=40, tamanho_sub=25, imagem_altura=380, largura_imagem=650,
    text_color='#ffffff', text_cololr2='#000000'
):
    escala = 0.84
    largura_total, altura_total = int(800 * escala), int(imagem_altura * escala)
    avatar_tamanho = int(128 * escala)
    faixa_largura = int(900 * 0.95 * escala)
    faixa_altura = int((imagem_altura / 2) * escala)
    faixa_y = int((imagem_altura * 0.56) * escala - 10)
    raio = int(faixa_altura * 0.15)

    mask = Image.new("L", (avatar_tamanho, avatar_tamanho), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, *mask.size), fill=255)
    avatar_final = Image.new("RGBA", (avatar_tamanho, avatar_tamanho))
    avatar_src = avatar_path.convert("RGBA").resize((avatar_tamanho, avatar_tamanho))
    avatar_final.paste(avatar_src, (0, 0), mask)

    try:
        font_nome = ImageFont.truetype(fonte_caminho, int(tamanho_nome * escala))
        font_bio = ImageFont.truetype(fonte_caminho, int(tamanho_sub * escala))
    except:
        fonte_caminho = "fonts/arial.ttf"
        font_nome = ImageFont.truetype(fonte_caminho, int(tamanho_nome * escala))
        font_bio = ImageFont.truetype(fonte_caminho, int(tamanho_sub * escala))

    frames = []
    bg = Image.open(fundo_path)

    for frame in ImageSequence.Iterator(bg):
        frame = frame.convert("RGBA").resize((largura_total, altura_total))

        try:
            faixa_rgb = ImageColor.getrgb(cor_faixa)
        except:
            faixa_rgb = (30, 30, 30)

        faixa_solid = Image.new("RGBA", (faixa_largura, faixa_altura), faixa_rgb + (255,))
        faixa_transp = Image.new("RGBA", (faixa_largura, faixa_altura), faixa_rgb + (0,))
        alpha = translucidez_faixa / 255.0
        faixa_final = Image.blend(faixa_transp, faixa_solid, alpha)

        mask_faixa = Image.new("L", (faixa_largura, faixa_altura), 255)
        draw_mask = ImageDraw.Draw(mask_faixa)
        draw_mask.rectangle((0, 0, faixa_largura - raio, faixa_altura), fill=255)
        draw_mask.pieslice((faixa_largura - 2*raio, 0, faixa_largura, 2*raio), 270, 360, fill=0)
        draw_mask.pieslice((faixa_largura - 2*raio, faixa_altura - 2*raio, faixa_largura, faixa_altura), 0, 90, fill=0)
        draw_mask.rectangle((faixa_largura - raio, raio, faixa_largura, faixa_altura - raio), fill=0)

        faixa_r, faixa_g, faixa_b, faixa_a = faixa_final.split()
        faixa_a = Image.composite(faixa_a, mask_faixa, mask_faixa)
        faixa_final = Image.merge("RGBA", (faixa_r, faixa_g, faixa_b, faixa_a))

        frame.paste(faixa_final, (0, faixa_y), faixa_final)

        avatar_x = 20
        avatar_y = faixa_y + (faixa_altura - avatar_tamanho)//2
        frame.paste(avatar_final, (avatar_x, avatar_y), avatar_final)

        draw_text = ImageDraw.Draw(frame)
        text_x = avatar_x + avatar_tamanho + 15
        draw_text.text((text_x, faixa_y + int(22 * escala)), texto_nome, font=font_nome, fill=ImageColor.getrgb(text_color))
        draw_text.text((text_x, faixa_y + int(72 * escala)), texto_sub, font=font_bio, fill=ImageColor.getrgb(text_cololr2))

        frames.append(frame)

    buffer = BytesIO()
    frames[0].save(buffer, format="GIF", save_all=True, append_images=frames[1:],
                   loop=0, duration=bg.info.get("duration", 100), disposal=2)
    buffer.seek(0)
    return buffer

async def gerar_gif_personalizado(
    fundo_path, avatar_path, texto_nome="The Love Marcos", texto_sub="Bem vindo ao servidor.",
    translucidez_faixa=160, cor_faixa=(100,180,255), fonte_caminho='fonts/arial.ttf',
    tamanho_nome=40, tamanho_sub=25, imagem_altura=380, largura_imagem=650,
    text_color='#ffffff', color_text2='#000000'
):
    at_1 = int(imagem_altura * 0.05)
    at_2 = int(imagem_altura * 0.33)
    at_3 = int(imagem_altura * 0.39)
    at_4 = int(imagem_altura * 0.08)
    cor_text = ImageColor.getrgb(text_color)
    cor_text2 = ImageColor.getrgb(color_text2)

    raio = at_4
    avatar_tamanho = at_2
    faixa_w = largura_imagem
    faixa_h = at_3
    faixa_x = at_1
    faixa_y = at_1

    cor_faixa_rgb = ImageColor.getrgb(cor_faixa)

    if isinstance(avatar_path, Image.Image):
        avatar_img = avatar_path.convert("RGBA")
    else:
        avatar_img = Image.open(avatar_path).convert("RGBA")

    fonte_nome = ImageFont.truetype(fonte_caminho, tamanho_nome)
    fonte_sub = ImageFont.truetype(fonte_caminho, tamanho_sub)

    frames = []
    fundo_gif = Image.open(fundo_path)
    fator_blend = translucidez_faixa / 255.0

    for frame in ImageSequence.Iterator(fundo_gif):
        frame = frame.convert("RGBA").resize((largura_imagem, imagem_altura), Image.Resampling.LANCZOS)

        regiao_fundo = frame.crop((faixa_x, faixa_y, faixa_x + faixa_w, faixa_y + faixa_h))
        faixa_solid = Image.new("RGBA", (faixa_w, faixa_h), cor_faixa_rgb + (255,))
        faixa_blendada = Image.blend(regiao_fundo, faixa_solid, fator_blend)

        mask = Image.new("L", (faixa_w, faixa_h), 0)
        draw_mask = ImageDraw.Draw(mask)
        draw_mask.rounded_rectangle((0, 0, faixa_w, faixa_h), radius=raio, fill=255)

        regiao_final = Image.composite(faixa_blendada, regiao_fundo, mask)
        frame.paste(regiao_final, (faixa_x, faixa_y))

        avatar_resized = avatar_img.resize((avatar_tamanho, avatar_tamanho), Image.Resampling.LANCZOS)
        mask_avatar = Image.new("L", (avatar_tamanho, avatar_tamanho), 0)
        ImageDraw.Draw(mask_avatar).ellipse((0, 0, avatar_tamanho, avatar_tamanho), fill=255)
        avatar_x = faixa_x + 30
        avatar_y = faixa_y + (faixa_h - avatar_tamanho) // 2
        frame.paste(avatar_resized, (avatar_x, avatar_y), mask_avatar)

        draw = ImageDraw.Draw(frame)
        texto_x = avatar_x + avatar_tamanho + 20
        draw.text((texto_x, faixa_y + 40), texto_nome, font=fonte_nome, fill=cor_text)
        draw.text((texto_x, faixa_y + 90), texto_sub, font=fonte_sub, fill=cor_text2)

        frame = frame.convert("P", palette=Image.ADAPTIVE, dither=Image.FLOYDSTEINBERG)
        frames.append(frame)

    buffer = BytesIO()
    frames[0].save(buffer, format="GIF", save_all=True, append_images=frames[1:],
                   optimize=False, duration=fundo_gif.info.get('duration', 100), loop=0)
    buffer.seek(0)
    return buffer

async def gerar_imagem_personalizado_layout2(
    fundo_path, avatar_path, texto_nome="The Love Marcos", texto_sub="Bem vindo ao servidor.",
    translucidez_faixa=160, cor_faixa=(100,180,255), fonte_caminho='fonts/arial.ttf',
    tamanho_nome=40, tamanho_sub=25, imagem_altura=380, largura_imagem=650,
    text_color='#ffffff', text_cololr2='#000000'
):
    escala = 0.84
    largura_total, altura_total = int(800 * escala), int(imagem_altura * escala)
    avatar_tamanho = int(128 * escala)
    faixa_largura = int(900 * 0.95 * escala)
    faixa_altura = int(imagem_altura / 2 * escala)
    faixa_y = int(imagem_altura * 0.56 * escala - 10)
    raio = int(faixa_altura * 0.15)

    try:
        bg = Image.open(fundo_path).convert("RGBA").resize((largura_total, altura_total))
    except:
        try:
            bg = Image.open("assets/default_bg.png").convert("RGBA").resize((largura_total, altura_total))
        except:
            raise Exception("Erro ao tentar carregar fundo.")

    mask = Image.new("L", (avatar_tamanho, avatar_tamanho), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, avatar_tamanho, avatar_tamanho), fill=255)
    avatar_final = Image.new("RGBA", (avatar_tamanho, avatar_tamanho))
    avatar_src = avatar_path.convert("RGBA").resize((avatar_tamanho, avatar_tamanho))
    avatar_final.paste(avatar_src, (0, 0), mask)

    try:
        faixa_rgb = ImageColor.getrgb(cor_faixa)
    except:
        faixa_rgb = (30, 30, 30)

    faixa_solid = Image.new("RGBA", (faixa_largura, faixa_altura), faixa_rgb + (255,))
    faixa_transp = Image.new("RGBA", (faixa_largura, faixa_altura), faixa_rgb + (0,))
    alpha = translucidez_faixa / 255.0
    faixa_final = Image.blend(faixa_transp, faixa_solid, alpha)

    mask_faixa = Image.new("L", (faixa_largura, faixa_altura), 255)
    draw_mask = ImageDraw.Draw(mask_faixa)
    draw_mask.rectangle((0, 0, faixa_largura - raio, faixa_altura), fill=255)
    draw_mask.pieslice((faixa_largura - 2*raio, 0, faixa_largura, 2*raio), 270, 360, fill=0)
    draw_mask.pieslice((faixa_largura - 2*raio, faixa_altura - 2*raio, faixa_largura, faixa_altura), 0, 90, fill=0)
    draw_mask.rectangle((faixa_largura - raio, raio, faixa_largura, faixa_altura - raio), fill=0)

    r, g, b, a = faixa_final.split()
    a = Image.composite(a, mask_faixa, mask_faixa)
    faixa_final = Image.merge("RGBA", (r, g, b, a))

    bg.paste(faixa_final, (0, faixa_y), faixa_final)

    avatar_x = 20
    avatar_y = faixa_y + (faixa_altura - avatar_tamanho)//2
    bg.paste(avatar_final, (avatar_x, avatar_y), avatar_final)

    try:
        font_nome = ImageFont.truetype(fonte_caminho, int(tamanho_nome * escala))
        font_bio = ImageFont.truetype(fonte_caminho, int(tamanho_sub * escala))
    except:
        font_nome = ImageFont.truetype("fonts/arial.ttf", int(tamanho_nome * escala))
        font_bio = ImageFont.truetype("fonts/arial.ttf", int(tamanho_sub * escala))

    draw = ImageDraw.Draw(bg)
    text_x = avatar_x + avatar_tamanho + 15
    draw.text((text_x, faixa_y + int(22 * escala)), texto_nome, font=font_nome, fill=ImageColor.getrgb(text_color))
    draw.text((text_x, faixa_y + int(72 * escala)), texto_sub, font=font_bio, fill=ImageColor.getrgb(text_cololr2))

    buffer = BytesIO()
    bg.save(buffer, "PNG")
    buffer.seek(0)
    return buffer

async def gerar_imagem_personalizada(
    fundo_path, avatar_path, texto_nome="The Love Marcos", texto_sub="Bem vindo ao servidor.",
    translucidez_faixa=160, cor_faixa=(100,180,255), fonte_caminho='fonts/arial.ttf',
    tamanho_nome=40, tamanho_sub=25, imagem_altura=380, largura_imagem=650,
    color_text='#000000', color_text2='#000000'
):
    at_1 = int(imagem_altura * 0.05)
    at_2 = int(imagem_altura * 0.33)
    at_3 = int(imagem_altura * 0.39)
    at_4 = int(imagem_altura * 0.08)
    cor_faixa = ImageColor.getrgb(cor_faixa)
    cor_texto = ImageColor.getrgb(color_text)
    cor_texto2 = ImageColor.getrgb(color_text2)

    raio = at_4
    avatar_tamanho = at_2
    faixa_w = largura_imagem
    faixa_h = at_3
    faixa_x = at_1
    faixa_y = at_1

    fundo = Image.open(fundo_path).convert("RGBA").resize((largura_imagem, imagem_altura))

    if isinstance(avatar_path, Image.Image):
        avatar_img = avatar_path.convert("RGBA")
    else:
        avatar_img = Image.open(avatar_path).convert("RGBA")

    fonte_nome = ImageFont.truetype(fonte_caminho, tamanho_nome)
    fonte_sub = ImageFont.truetype(fonte_caminho, tamanho_sub)

    faixa = Image.new("RGBA", (faixa_w, faixa_h), (*cor_faixa, translucidez_faixa))
    mask = Image.new("L", (faixa_w, faixa_h), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.rectangle((raio, 0, faixa_w, faixa_h), fill=translucidez_faixa)
    draw_mask.pieslice((0, 0, raio*2, raio*2), 180, 270, fill=translucidez_faixa)
    draw_mask.pieslice((0, faixa_h - raio*2, raio*2, faixa_h), 90, 180, fill=translucidez_faixa)
    draw_mask.rectangle((0, raio, raio, faixa_h - raio), fill=translucidez_faixa)
    faixa.putalpha(mask)
    fundo.alpha_composite(faixa, dest=(faixa_x, faixa_y))

    avatar_resized = avatar_img.resize((avatar_tamanho, avatar_tamanho))
    mask_avatar = Image.new("L", (avatar_tamanho, avatar_tamanho), 0)
    ImageDraw.Draw(mask_avatar).ellipse((0, 0, avatar_tamanho, avatar_tamanho), fill=255)
    avatar_x = faixa_x + 30
    avatar_y = faixa_y + (faixa_h - avatar_tamanho) // 2
    fundo.paste(avatar_resized, (avatar_x, avatar_y), mask_avatar)

    draw = ImageDraw.Draw(fundo)
    texto_x = avatar_x + avatar_tamanho + 20
    draw.text((texto_x, faixa_y + 40), texto_nome, font=fonte_nome, fill=cor_texto)
    draw.text((texto_x, faixa_y + 90), texto_sub, font=fonte_sub, fill=cor_texto2)

    buffer = BytesIO()
    fundo.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer

# =========================
# BOTÕES E VIEWS DO PERFIL
# =========================

class DarLikeButton(discord.ui.Button):
    def __init__(self, alvo: discord.Member, autor: discord.Member, mobile=False):
        super().__init__(label=None if mobile else "Like", emoji="👍🏻", style=discord.ButtonStyle.primary)
        self.alvo = alvo
        self.autor = autor

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.autor.id:
            return await interaction.response.send_message("❌ Apenas o autor do comando pode interagir.", ephemeral=True)

        if not await funcs.pode_dar_like(self.alvo.id, self.autor.id):
            return await interaction.response.send_message("⏳ Você já deu like nesse perfil recentemente. Tente novamente em 1h.", ephemeral=True)

        await funcs.registrar_like(self.alvo.id, self.autor.id)
        await interaction.response.send_message(f"👍 Você deu like em {self.alvo.display_name}!", ephemeral=True)

class DarDislikeButton(discord.ui.Button):
    def __init__(self, alvo: discord.Member, autor: discord.Member, mobile=False):
        super().__init__(label=None if mobile else "Dislike", emoji="👎🏻", style=discord.ButtonStyle.danger)
        self.alvo = alvo
        self.autor = autor

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.autor.id:
            return await interaction.response.send_message("❌ Apenas o autor pode interagir.", ephemeral=True)

        total_likes = await funcs.get_likes(self.alvo.id)
        if total_likes <= 0:
            return await interaction.response.send_message("⚠️ Este perfil já está com 0 likes.", ephemeral=True)

        await funcs.remover_like(self.alvo.id)
        await interaction.response.send_message(f"👎 Você removeu 1 like de {self.alvo.display_name}.", ephemeral=True)

class ShowSobreMimButton(discord.ui.Button):
    def __init__(self, user: discord.User, estilo='primary'):
        self.user = user
        estilo_mapa = {"azul": discord.ButtonStyle.primary, "cinza": discord.ButtonStyle.secondary,
                      "verde": discord.ButtonStyle.success, "vermelho": discord.ButtonStyle.danger}
        super().__init__(label="📂Sobre Mim", style=estilo_mapa.get(estilo, discord.ButtonStyle.primary))

    async def callback(self, interaction: discord.Interaction):
        perfil = await funcs.load_sobre_mim(self.user.id)
        likes = await funcs.get_likes(self.user.id)
        
        if not perfil:
            return await interaction.response.send_message("❌ Ainda não configurado!", ephemeral=True)

        idade_texto = "🔞 +18" if perfil.get('idade_18') else "🧒 -18"
        embed = discord.Embed(title="📁 Sobre Mim", color=discord.Color.blue())
        embed.add_field(name="🧬 Gênero", value=perfil.get('genero') or "—", inline=True)
        embed.add_field(name="💖 Sexualidade", value=perfil.get('sexualidade') or "—", inline=True)
        embed.add_field(name="📅 Idade", value=idade_texto, inline=True)
        embed.add_field(name="📌 Pronomes", value=perfil.get('pronomes') or "—", inline=False)
        if perfil.get('texto_extra'):
            embed.add_field(name="📝 Recado", value=perfil['texto_extra'], inline=False)
        embed.add_field(name="👍 Likes recebidos", value=str(likes), inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)

# =========================
# PERFIL VIEW (CORRIGIDO - ASSÍNCRONO)
# =========================

class PerfilView(discord.ui.View):
    def __init__(self, target_user: discord.Member, viewer: discord.Member, sobre_mim: dict = None, plataforma: str = None):
        super().__init__(timeout=120)
        self.user = target_user
        self.viewer = viewer
        
        if plataforma == "mobile":
            self.add_item(DarLikeButton(target_user, viewer, mobile=True))
            self.add_item(DarDislikeButton(target_user, viewer, mobile=True))
            if sobre_mim:
                estilo = sobre_mim.get("botao_style", "azul")
                self.add_item(ShowSobreMimButton(target_user, estilo))
        else:
            self.add_item(DarLikeButton(target_user, viewer))
            self.add_item(DarDislikeButton(target_user, viewer))
            if sobre_mim:
                estilo = sobre_mim.get("botao_style", "azul")
                self.add_item(ShowSobreMimButton(target_user, estilo))

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        try:
            await self.message.edit(view=self)
        except discord.NotFound:
            pass
        
# =========================
# BOTÕES DE PLATAFORMA
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
        await interaction.response.send_message("✅ Plataforma definida como **PC**. Agora use `<perfil` novamente.", ephemeral=True)

    @discord.ui.button(label="📱 Celular", style=discord.ButtonStyle.secondary)
    async def mobile(self, interaction: discord.Interaction, button: discord.ui.Button):
        await funcs.set_plataforma(self.user_id, "mobile")
        await interaction.response.send_message("✅ Plataforma definida como **Celular**. Agora use `<perfil` novamente.", ephemeral=True)

# =========================
# COMANDO PERFIL CONFIGS
# =========================

@bot.command(name="perfilconfigs")
async def perfildisplayconfigs(ctx: commands.Context, user_: discord.User = None):
    author = user_ or ctx.author
    
    font_sizes = await funcs.get_font_sizes(author.id)
    cfg = await funcs.load_config(author.id)
    fonte_nome = await funcs.get_fonte(author.id)
    
    m = discord.Embed(
        title="Configurações do seu <perfil e <xp",
        description=(
            f"- Sua bio do perfil: {cfg.get('bio', '???')}\n"
            f"- A cor do seu nome no perfil: {cfg.get('color', '???')}\n"
            f"- Layout do perfil: {cfg.get('layout_faixa', '???')}\n"
            f"- Layout do avatar: {cfg.get('layout_avatar', '???')}\n"
            f"- Cor da faixa: {cfg.get('perfil_faixa_color', '???')}\n"
            f"- Plataforma: {cfg.get('plataforma', '???')}\n"
            f"- Fonte: {fonte_nome}\n"
            f"- Tamanho da fonte do nome: {font_sizes.font_nome_px}\n"
            f"- Tamanho da fonte da bio: {font_sizes.font_bio_px}\n"
            f"- Tamanho da fonte do xp: {font_sizes.font_xp_px}\n"
            f"**Configs <xp**\n"
            f"- Cor da barra de xp: {cfg.get('xp_bar_color', '???')}\n"
            f"- Cor da faixa: {cfg.get('faixa_color', '???')}\n"
            f"- Cor do texto xp: {cfg.get('xp_text_color', '???')}"
        ),
        timestamp=discord.utils.utcnow(),
        color=discord.Color.blurple()
    )
    m.set_thumbnail(url=author.avatar.url)
    m.set_footer(text=author.name, icon_url=author.avatar.url)
    await ctx.reply(embed=m)

@bot.tree.command(name="perfilconfigs")
async def perfildisplayconfigs_slash(interaction: discord.Interaction, user_: discord.User = None):
    author = user_ or interaction.user
    
    font_sizes = await funcs.get_font_sizes(author.id)
    cfg = await funcs.load_config(author.id)
    fonte_nome = await funcs.get_fonte(author.id)
    
    m = discord.Embed(
        title="Configurações do seu <perfil e <xp",
        description=(
            f"- Sua bio do perfil: {cfg.get('bio', '???')}\n"
            f"- A cor do seu nome no perfil: {cfg.get('color', '???')}\n"
            f"- Layout do perfil: {cfg.get('layout_faixa', '???')}\n"
            f"- Layout do avatar: {cfg.get('layout_avatar', '???')}\n"
            f"- Cor da faixa: {cfg.get('perfil_faixa_color', '???')}\n"
            f"- Plataforma: {cfg.get('plataforma', '???')}\n"
            f"- Fonte: {fonte_nome}\n"
            f"- Tamanho da fonte do nome: {font_sizes.font_nome_px}\n"
            f"- Tamanho da fonte da bio: {font_sizes.font_bio_px}\n"
            f"- Tamanho da fonte do xp: {font_sizes.font_xp_px}\n"
            f"**Configs <xp**\n"
            f"- Cor da barra de xp: {cfg.get('xp_bar_color', '???')}\n"
            f"- Cor da faixa: {cfg.get('faixa_color', '???')}\n"
            f"- Cor do texto xp: {cfg.get('xp_text_color', '???')}"
        ),
        timestamp=discord.utils.utcnow(),
        color=discord.Color.blurple()
    )
    m.set_thumbnail(url=author.avatar.url)
    m.set_footer(text=author.name, icon_url=author.avatar.url)
    await interaction.response.send_message(embed=m)

# =========================
# COMANDO PERFIL
# =========================

@bot.command(name="perfil", help="Seu perfil.", category="Geral")
async def perfil(ctx, member: discord.Member = None):
    embed_loading = discord.Embed(description="⚠️ Aguarde, gerando imagem do perfil...", color=discord.Color.orange())
    loading_msg = await ctx.send(embed=embed_loading)

    try:
        user = member or ctx.author
        plataforma = await funcs.get_plataforma(user.id)

        if plataforma is None:
            embed = discord.Embed(
                title="📱 Em qual dispositivo você está?",
                description="Escolha abaixo para ajustar melhor os botões do seu perfil.\nUse `-perfil` novamente após escolher.",
                color=discord.Color.blurple()
            )
            view = PlataformaView(user.id)
            await loading_msg.edit(embed=embed, view=view)
            return

        cfg = await funcs.load_config(user.id)
        nome_visivel = limpar_unicode(user.display_name)
        bio = cfg.get('bio', 'Sem bio.')

        nivel, restante_xp, total_xp = await funcs.calcular_nivel_e_xp(user.id, ctx.guild.id)
        xp_universal = await funcs.get_xp_universal(user.id)
        xp_info = (nivel, restante_xp, total_xp, xp_universal)

        avatar_bytes = await user.display_avatar.read()
        avatar_img = Image.open(BytesIO(avatar_bytes)).convert("RGBA")

        parceiro_id = await funcs.buscar_id_de_casamento(user.id)
        parceiro = None
        if parceiro_id:
            parceiro = bot.get_user(parceiro_id) or await bot.fetch_user(parceiro_id)

        badge_imgs = []
        if ctx.guild.id == 1307698839263772803 and cfg.get("mostrar_badges", True):
            try:
                premium_badge = "badges/premium_badge.png"
                is_premium = await verificar_premium(user.id)
                if is_premium:
                    img_pb = Image.open(premium_badge).convert("RGBA").resize((38, 38))
                    badge_imgs.append(gerar_badge_com_fundo(img_pb))
            except Exception as e:
                logging.warning(f"Erro carregando badge: {e}")

        fonte_nome = await funcs.get_fonte(user.id)
        perfil_model = await funcs.get_perfil_model(user.id)
        layout_faixa = cfg.get("layout_faixa", "perfil").lower()
        is_premium = await verificar_premium(user.id)

        await loading_msg.edit(embed=discord.Embed(description="🖼️ Processando imagem...", color=discord.Color.blue()))

        if perfil_model == "gif":
            if layout_faixa == "xp":
                buffer = await desenhar_layout_xp_gif(user, cfg, nome_visivel, bio, avatar_img, xp_info, badge_imgs, parceiro, fonte_nome)
            else:
                buffer = await desenhar_layout_perfil_gif(user, cfg, nome_visivel, bio, avatar_img, xp_info, badge_imgs, parceiro, fonte_nome, user.id)
        else:
            if layout_faixa == "xp":
                buffer = await desenhar_layout_xp(user, cfg, nome_visivel, bio, avatar_img, xp_info, badge_imgs, parceiro, fonte_nome)
            else:
                buffer = await desenhar_layout_perfil(user, cfg, nome_visivel, bio, avatar_img, xp_info, badge_imgs, parceiro, fonte_nome, user.id)

        sobre_mim = await funcs.load_sobre_mim(user.id)
        
        await loading_msg.delete()
        
        view = PerfilView(user, user, sobre_mim, plataforma)
        filename = "perfil.gif" if (perfil_model == "gif" and is_premium) else "perfil.png"
        msg = await ctx.send(file=discord.File(buffer, filename=filename), view=view)
        view.message = msg

        async with AsyncSessionLocal() as session:
            from dbdata import Email
            result = await session.execute(select(Email).filter_by(destinatario_id=user.id, lido=False))
            count = len(result.scalars().all())

        if count > 0 and user.id == ctx.author.id:
            embed_email = discord.Embed(
                title="📩 Você tem correspondência!",
                description="Clique no botão abaixo para ler seus e-mails.",
                color=discord.Color.blue()
            )
            await ctx.send(embed=embed_email, view=AbrirEmailView(user.id))

    except Exception as e:
        logging.error(f"Erro no comando perfil: {e}")
        await loading_msg.edit(
            embed=discord.Embed(
                description=f"❌ Ocorreu um erro ao gerar o perfil: {str(e)}",
                color=discord.Color.red()
            ),
            view=None
        )

@bot.tree.command(name="perfil", description="Use para ver seu perfil.")
async def perfil_slash(interaction: discord.Interaction, member: discord.User = None):
    await interaction.response.defer()
    
    try:
        user = member or interaction.user
        plataforma = await funcs.get_plataforma(user.id)

        if plataforma is None:
            await interaction.followup.send("Você não tem uma plataforma selecionada, use <configs para mudar isso.")
            return

        cfg = await funcs.load_config(user.id)
        nome_visivel = limpar_unicode(user.display_name)
        bio = cfg.get('bio', 'Sem bio.')

        nivel, restante_xp, total_xp = await funcs.calcular_nivel_e_xp(user.id, interaction.guild.id)
        xp_universal = await funcs.get_xp_universal(user.id)
        xp_info = (nivel, restante_xp, total_xp, xp_universal)

        avatar_bytes = await user.display_avatar.read()
        avatar_img = Image.open(BytesIO(avatar_bytes)).convert("RGBA")

        parceiro_id = await funcs.buscar_id_de_casamento(user.id)
        parceiro = None
        if parceiro_id:
            parceiro = bot.get_user(parceiro_id) or await bot.fetch_user(parceiro_id)

        badge_imgs = []
        if interaction.guild and interaction.guild.id == 1307698839263772803 and cfg.get("mostrar_badges", True):
            try:
                premium_badge = "badges/premium_badge.png"
                is_premium = await verificar_premium(user.id)
                if is_premium:
                    img_pb = Image.open(premium_badge).convert("RGBA").resize((38, 38))
                    badge_imgs.append(gerar_badge_com_fundo(img_pb))
            except Exception as e:
                logging.warning(f"Erro carregando badge: {e}")

        fonte_nome = await funcs.get_fonte(user.id)
        perfil_model = await funcs.get_perfil_model(user.id)
        layout_faixa = cfg.get("layout_faixa", "perfil").lower()
        is_premium = await verificar_premium(user.id)

        # Gerar imagem
        if perfil_model == "gif":
            if layout_faixa == "xp":
                buffer = await desenhar_layout_xp_gif(user, cfg, nome_visivel, bio, avatar_img, xp_info, badge_imgs, parceiro, fonte_nome)
            else:
                buffer = await desenhar_layout_perfil_gif(user, cfg, nome_visivel, bio, avatar_img, xp_info, badge_imgs, parceiro, fonte_nome, user.id)
        else:
            if layout_faixa == "xp":
                buffer = await desenhar_layout_xp(user, cfg, nome_visivel, bio, avatar_img, xp_info, badge_imgs, parceiro, fonte_nome)
            else:
                buffer = await desenhar_layout_perfil(user, cfg, nome_visivel, bio, avatar_img, xp_info, badge_imgs, parceiro, fonte_nome, user.id)

        sobre_mim = await funcs.load_sobre_mim(user.id)
        view = PerfilView(user, user, sobre_mim, plataforma)
        filename = "perfil.gif" if (perfil_model == "gif" and is_premium) else "perfil.png"
        msg = await interaction.followup.send(file=discord.File(buffer, filename=filename), view=view)
        view.message = msg

    except Exception as e:
        logging.error(f"Erro no comando perfil (slash): {e}")
        await interaction.followup.send(f"❌ Ocorreu um erro ao gerar o perfil: {str(e)}")
                
def gerar_badge_com_fundo(im: Image.Image, size: int = 32, bg_color=(47, 49, 54)) -> Image.Image:
    base = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    mask = Image.new("L", (size, size), 0)
    d = ImageDraw.Draw(mask)
    d.rounded_rectangle((0, 0, size, size), radius=8, fill=255)
    fundo = Image.new("RGBA", (size, size), bg_color)
    fundo.putalpha(mask)
    im = im.resize((size - 6, size - 6), Image.Resampling.LANCZOS)
    base.paste(fundo, (0, 0), fundo)
    base.paste(im, (3, 3), im)
    return base

# =========================
# COMANDO PERFIL (FONTE E PX)
# =========================

class EscolherPxDaFonteModal(Modal, title="Escolha o PX dos textos do seu perfil."):
    fonte_nome_px = discord.ui.TextInput(label="PX do nome.", placeholder="EX: 30", max_length=2)
    fonte_bio_px = discord.ui.TextInput(label="PX da Bio.", placeholder="Ex: 40", max_length=2)
    fonte_xp_px = discord.ui.TextInput(label="PX do XP.", placeholder="Ex: 12", max_length=2)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            nome_px = int(self.fonte_nome_px.value)
            bio_px = int(self.fonte_bio_px.value)
            xp_px = int(self.fonte_xp_px.value)
        except ValueError:
            return await interaction.response.send_message("Por favor, insira apenas números válidos!", ephemeral=True)

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
        await funcs.set_fonte(interaction.user.id, self.fonte.value)
        await interaction.response.send_message(f"Fonte {self.fonte.value} adicionada com sucesso.", ephemeral=True)

class ButtonPxFontPerfilCommand(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="Escolher Px dos textos do perfil.", style=discord.ButtonStyle.grey)
    async def interaction_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EscolherPxDaFonteModal())

class EnviarModalComBotao(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="Escolher fonte.")
    async def enviarmodaldafonte(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EscolherFonteModal())

class BotoesPaginamentoCatalogoFonts(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=120)

    @discord.ui.button(label="Mostrar catálogo")
    async def botaofontecatalogo(self, interaction: discord.Interaction, button: discord.ui.Button):
        embedpage1 = discord.Embed(
            title="Catálogo de fontes.",
            description="Olá, aqui temos o catálogo.\n\n* Aquire.\n* Cyberpunk\n* Blad\n* Arial\n* Orbitron\n* Horrendo\n* Playfair\n* Cinzel\n* Quantico\n* Monad\n* PF Uniform\n* Morena\n* Astra\n* Alexana\n* Gyre Termes\n**Escolha uma fonte e use o comando `<setfonte` para definir a sua fonte.**",
            color=discord.Color.dark_blue()
        )
        embedpage1.set_footer(text=f"Requisitado por {interaction.user.name}")
        await interaction.response.send_message(embed=embedpage1, view=EnviarModalComBotao())

    @discord.ui.button(label="Escolher Px dos textos do perfil.", style=discord.ButtonStyle.grey)
    async def interaction_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(EscolherPxDaFonteModal())

@bot.command(name="escolherpxtext", aliases=["ept"])
async def escolherpxfontecommand(ctx: commands.Context):
    embed = discord.Embed(
        title="Pixels do texto do perfil.",
        description="Escolha quantos pixels você deseja que cada texto do comando de perfil tenha.",
        color=discord.Color.dark_blue()
    )
    embed.set_thumbnail(url=ctx.author.display_avatar.url)
    embed.set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url)
    embed.timestamp = discord.utils.utcnow()
    await ctx.reply(embed=embed, view=ButtonPxFontPerfilCommand())

@bot.command(name="setfonte")
async def selecionarfonte(ctx: commands.Context):
    m = discord.Embed(
        title="Catálogo de fontes.",
        description="Temos mais de 15 fontes disponíveis, de diversos estilos diferentes.\nClique no botão para abrir o catálogo de Fontes do Keith!",
        color=discord.Color.dark_blue(),
        timestamp=discord.utils.utcnow()
    )
    m.set_thumbnail(url=ctx.author.avatar.url)
    m.set_footer(text=ctx.author.name, icon_url=ctx.author.avatar.url)
    await ctx.reply(embed=m, view=BotoesPaginamentoCatalogoFonts())

# =========================
# COMANDOS DE LIMPEZA E INFO
# =========================

@bot.command(name="limpar3", aliases=["clean3", "clear3"])
@commands.is_owner()
async def limpar(ctx, quantidade: int):
    if quantidade < 1 or quantidade > 500:
        await ctx.send("❌ Escolha um número entre 1 e 500!", delete_after=5)
        return
    deleted = await ctx.channel.purge(limit=quantidade + 1)
    await ctx.send(f"✅ {len(deleted) - 1} mensagens foram apagadas!", delete_after=5)

@bot.command(name='servidores')
@commands.is_owner()
async def list_servers(ctx):
    guilds = bot.guilds
    if not guilds:
        await ctx.send("O bot não está em nenhum servidor.")
        return
    
    embed = discord.Embed(title=f"Servidores onde estou presente ({len(guilds)})", color=discord.Color.blue())
    for guild in guilds:
        owner = guild.owner if hasattr(guild, 'owner') else "Não disponível"
        embed.add_field(name=guild.name, value=f"ID: {guild.id}\nMembros: {guild.member_count}\nDono: {owner}", inline=False)
    await ctx.send(embed=embed)

# =========================
# COMANDO BOTINFO
# =========================

@bot.command(name="botinfo", aliases=["infobot"])
async def botinfo(ctx: commands.Context):
    owner = (await bot.application_info()).owner
    guilds = len(bot.guilds)
    users = sum(guild.member_count for guild in bot.guilds if guild.member_count is not None)
    commands_count = len(bot.commands) + len(bot.tree.get_commands())
    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent

    embed = discord.Embed(title=f"🤖 Informações do {bot.user.name}", color=discord.Color.blue(), timestamp=datetime.now())
    embed.set_thumbnail(url=bot.user.avatar.url)
    embed.add_field(name="👑 Dono", value=f"`{owner}`", inline=True)
    embed.add_field(name="📅 Criado em", value=f"`{bot.user.created_at.strftime('%d/%m/%Y')}`", inline=True)
    embed.add_field(name="🏓 Latência", value=f"`{round(bot.latency * 1000)}ms`", inline=True)
    embed.add_field(name="🌍 Servidores", value=f"`{guilds}`", inline=True)
    embed.add_field(name="📜 Comandos", value=f"{commands_count}", inline=True)
    embed.add_field(name="👥 Usuários", value=f"`{users}`", inline=True)
    embed.add_field(name="💻 CPU", value=f"`{cpu_usage}%`", inline=True)
    embed.add_field(name="🧠 RAM", value=f"`{ram_usage}%`", inline=True)
    embed.add_field(name="🐍 Python", value=f"`{platform.python_version()}`", inline=True)
    embed.add_field(name="🔗 Links", value="[Convite](https://discord.com/oauth2/authorize?client_id=1367932530938089472&permissions=8&integration_type=0&scope=bot) | [Suporte](https://discord.gg/t63Xf2PSFh)", inline=False)
    embed.set_footer(text=f"Solicitado por {ctx.author.display_name}", icon_url=ctx.author.display_avatar.url)
    await ctx.reply(embed=embed)

@bot.tree.command(name="botinfo")
async def botinfo_slash(interaction: discord.Interaction):
    owner = (await bot.application_info()).owner
    guilds = len(bot.guilds)
    users = sum(guild.member_count for guild in bot.guilds if guild.member_count is not None)
    commands_count = len(bot.commands) + len(bot.tree.get_commands())
    cpu_usage = psutil.cpu_percent()
    ram_usage = psutil.virtual_memory().percent

    embed = discord.Embed(title=f"🤖 Informações do {bot.user.name}", color=discord.Color.blue(), timestamp=datetime.now())
    embed.set_thumbnail(url=bot.user.avatar.url)
    embed.add_field(name="👑 Dono", value=f"`{owner}`", inline=True)
    embed.add_field(name="📅 Criado em", value=f"`{bot.user.created_at.strftime('%d/%m/%Y')}`", inline=True)
    embed.add_field(name="🏓 Latência", value=f"`{round(bot.latency * 1000)}ms`", inline=True)
    embed.add_field(name="🌍 Servidores", value=f"`{guilds}`", inline=True)
    embed.add_field(name="📜 Comandos", value=f"{commands_count}", inline=True)
    embed.add_field(name="👥 Usuários", value=f"`{users}`", inline=True)
    embed.add_field(name="💻 CPU", value=f"`{cpu_usage}%`", inline=True)
    embed.add_field(name="🧠 RAM", value=f"`{ram_usage}%`", inline=True)
    embed.add_field(name="🐍 Python", value=f"`{platform.python_version()}`", inline=True)
    embed.add_field(name="🔗 Links", value="[Convite](https://discord.com/oauth2/authorize?client_id=1367932530938089472&permissions=8&integration_type=0&scope=bot) | [Suporte](https://discord.gg/t63Xf2PSFh)", inline=False)
    embed.set_footer(text=f"{interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

# =========================
# E-MAIL
# =========================

class EmailModal(discord.ui.Modal, title="📨 Escreva seu E-Mail"):
    destinatario_id = discord.ui.TextInput(label="ID do destinatário", placeholder="Ex: 123456789012345678", required=True)
    titulo = discord.ui.TextInput(label="Título do e-mail", placeholder="Assunto", required=True, max_length=100)
    conteudo = discord.ui.TextInput(label="Conteúdo", style=discord.TextStyle.paragraph, required=True, max_length=1000)

    def __init__(self, autor_id: int):
        super().__init__()
        self.autor_id = autor_id

    async def on_submit(self, interaction: discord.Interaction):
        from dbdata import Email
        try:
            destinatario_id = int(self.destinatario_id.value.strip())
            titulo = self.titulo.value.strip()
            conteudo = self.conteudo.value.strip()
            
            async with AsyncSessionLocal() as session:
                email = Email(
                    remetente_id=self.autor_id,
                    destinatario_id=destinatario_id,
                    titulo=titulo,
                    conteudo=conteudo,
                    data_envio=datetime.utcnow().isoformat()
                )
                session.add(email)
                await session.commit()
            
            await interaction.response.send_message("✅ E-Mail enviado com sucesso!", ephemeral=True)
        except Exception as e:
            logging.error(f"Erro ao enviar e-mail: {e}")
            await interaction.response.send_message("❌ Ocorreu um erro ao enviar o e-mail.", ephemeral=True)

class EmailSendView(discord.ui.View):
    def __init__(self, autor_id: int):
        super().__init__(timeout=120)
        self.autor_id = autor_id

    @discord.ui.button(label="Enviar E-Mail 📧", style=discord.ButtonStyle.primary)
    async def enviar_email(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.autor_id:
            return await interaction.response.send_message("❌ Apenas quem usou o comando pode enviar o e-mail.", ephemeral=True)
        await interaction.response.send_modal(EmailModal(self.autor_id))

class AbrirEmailView(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id

    @discord.ui.button(label="Abrir E-Mails 📧", style=discord.ButtonStyle.primary)
    async def abrir(self, interaction: discord.Interaction, button: discord.ui.Button):
        from dbdata import Email
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Apenas o destinatário pode abrir seus e-mails.", ephemeral=True)

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(Email).filter_by(destinatario_id=self.user_id, lido=False)
            )
            emails = result.scalars().all()
            
            for email in emails:
                email.lido = True
            await session.commit()

        await interaction.message.delete()

        if not emails:
            return await interaction.response.send_message("📭 Você não tem e-mails não lidos.", ephemeral=True)

        description = ""
        for email in emails:
            remetente = interaction.client.get_user(email.remetente_id)
            if not remetente:
                try:
                    remetente = await interaction.client.fetch_user(email.remetente_id)
                except:
                    remetente = None
            nome = remetente.display_name if remetente else f"ID: {email.remetente_id}"
            description += f"**📨 {email.titulo}**\n{email.conteudo}\n*Enviado por **{nome}** em `{email.data_envio}`*\n\n"

        embed = discord.Embed(title="📬 Seus E-Mails", description=description.strip(), color=discord.Color.blue())
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name="email", help="Enviar um e-mail para outro usuário.", category="Utilidade")
async def email(ctx: commands.Context):
    embed = discord.Embed(title="📧 Envio de E-Mail", description="O que deseja mandar e pra quem?", color=discord.Color.blue())
    view = EmailSendView(ctx.author.id)
    await ctx.send(embed=embed, view=view)

# =========================
# CASAMENTO
# =========================

def gerar_imagem_pedido(avatar1: Image.Image, avatar2: Image.Image, amor_path="assets/amor.png") -> BytesIO:
    size = (256, 256)
    avatar1 = avatar1.resize(size).convert("RGBA")
    avatar2 = avatar2.resize(size).convert("RGBA")

    total_width = size[0] * 2
    height = size[1]
    base = Image.new("RGBA", (total_width, height), (255, 255, 255, 0))

    base.paste(avatar1, (0, 0), avatar1)
    base.paste(avatar2, (size[0], 0), avatar2)

    amor = Image.open(amor_path).convert("RGBA")
    max_width = int(total_width * 0.27)
    scale = max_width / amor.width
    new_size = (int(amor.width * scale), int(amor.height * scale))
    amor = amor.resize(new_size)

    pos_x = (total_width - new_size[0]) // 2
    pos_y = (height - new_size[1]) // 2
    base.paste(amor, (pos_x, pos_y), amor)

    buf = BytesIO()
    base.save(buf, format="PNG")
    buf.seek(0)
    return buf

class ConfirmarDivorcioView(View):
    def __init__(self, autor_id, parceiro_id):
        super().__init__(timeout=60)
        self.autor_id = autor_id
        self.parceiro_id = parceiro_id
        self.confirmado = False

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.autor_id:
            await interaction.response.send_message("❌ Somente quem iniciou o divórcio pode confirmar.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Sim", style=discord.ButtonStyle.gray)
    async def confirmar(self, interaction: discord.Interaction, button: Button):
        if self.confirmado:
            return
        self.confirmado = True

        await funcs.desfazer_casamento(self.autor_id, self.parceiro_id)
        await interaction.response.edit_message(content="Divórcio realizado com sucesso. 🥀", embed=None, view=None)

class PedidoCasamentoView(View):
    def __init__(self, autor, alvo, mensagem_inicial, imagem_file):
        super().__init__(timeout=300)
        self.autor = autor
        self.alvo = alvo
        self.mensagem_inicial = mensagem_inicial
        self.mensagem_de_botao = None
        self.imagem_file = imagem_file
        self.respondido = False

    def set_mensagem_de_botao(self, mensagem):
        self.mensagem_de_botao = mensagem

    async def interaction_check(self, interaction: discord.Interaction):
        if interaction.user.id != self.alvo.id:
            await interaction.response.send_message("❌ Este pedido não é para você.", ephemeral=True)
            return False
        return True

    async def on_timeout(self):
        if self.respondido or not self.mensagem_de_botao:
            return
        try:
            await self.mensagem_de_botao.edit(view=None)
        except Exception as e:
            logging.error(f"[Erro ao renovar View]: {e}")

    @discord.ui.button(label="Aceitar 💐", style=discord.ButtonStyle.success)
    async def aceitar(self, interaction: discord.Interaction, button: Button):
        if self.respondido:
            return
        self.respondido = True

        await funcs.criar_casamento(self.autor.id, self.alvo.id)

        texto_publico = f"{self.alvo.mention} aceitou o pedido de {self.autor.mention}! 💞💍🎉"
        await self.mensagem_inicial.channel.send(texto_publico)

        embed = discord.Embed(title=f"{self.alvo.display_name} aceitou o pedido! 💋💍🎊", color=discord.Color.magenta())
        await self.autor.send(embed=embed)
        await interaction.response.send_message("💖 Você aceitou! Felicidades ao casal!", ephemeral=True)

    @discord.ui.button(label="Recusar 🥀", style=discord.ButtonStyle.danger)
    async def recusar(self, interaction: discord.Interaction, button: Button):
        if self.respondido:
            return
        self.respondido = True

        embed_editado = self.mensagem_inicial.embeds[0]
        embed_editado.description = "Infelizmente não foi dessa vez 🥀"
        embed_editado.set_image(url=None)
        await self.mensagem_inicial.edit(embed=embed_editado, attachments=[])
        await interaction.response.send_message("🚫 Você recusou o pedido de casamento.", ephemeral=True)

class CasalStatsView(View):
    def __init__(self, casal_ids, data_casamento):
        super().__init__(timeout=None)
        self.casal_ids = casal_ids
        self.data_casamento = data_casamento

    @discord.ui.button(label="Estatísticas 💌", style=discord.ButtonStyle.red)
    async def estatisticas(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id not in self.casal_ids:
            return await interaction.response.send_message("❌ Somente o casal pode ver essas estatísticas.", ephemeral=True)

        inicio = datetime.fromisoformat(self.data_casamento)
        agora = datetime.now()
        duracao = agora - inicio
        dias = duracao.days
        horas = duracao.seconds // 3600

        data_formatada = inicio.strftime("%d de %B de %Y")
        casamentos = await funcs.listar_casamentos_ordenados_por_data()
        casal_pos = 1 + next((i for i, c in enumerate(casamentos) 
                             if sorted(self.casal_ids) == sorted([c.user_id_1, c.user_id_2])), -1)
        total = len(casamentos)

        embed = discord.Embed(title="💖 Estatísticas do Casamento", color=discord.Color.red())
        embed.add_field(name="⏳ Tempo de casamento", value=f"{dias} dias, {horas} horas", inline=False)
        embed.add_field(name="📅 Desde", value=data_formatada, inline=True)
        embed.add_field(name="🏆 Ranking", value=f"#{casal_pos} de {total} casais", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.command(name="casar")
async def casar(ctx, membro: discord.Member = None):
    if not membro or membro.bot:
        return await ctx.send("❌ Você deve mencionar um usuário válido (e não um bot).")
    if membro.id == ctx.author.id:
        return await ctx.send("❌ Você não pode se casar consigo mesmo! Seu narcisista.")

    if await funcs.esta_casado(ctx.author.id) or await funcs.esta_casado(membro.id):
        return await ctx.send("❌ Um de vocês já está em um casamento. Monogamia por aqui!")

    avatar1_bytes = await ctx.author.display_avatar.read()
    avatar2_bytes = await membro.display_avatar.read()
    avatar1 = Image.open(BytesIO(avatar1_bytes))
    avatar2 = Image.open(BytesIO(avatar2_bytes))
    img_buffer = gerar_imagem_pedido(avatar1, avatar2)
    img_file = discord.File(img_buffer, filename="casamento.png")

    embed_envio = discord.Embed(description=f"💌 Pedido enviado... Será se {membro.mention} vai aceitar?", color=discord.Color.red())
    embed_envio.set_image(url="attachment://casamento.png")
    msg = await ctx.send(embed=embed_envio, file=img_file)

    embed_pedido = discord.Embed(title="💍 Você recebeu um pedido de casamento!", 
                                description=f"{ctx.author.mention} quer se casar com você, aceita?", color=discord.Color.blurple())
    embed_pedido.set_thumbnail(url="attachment://cs.png")
    thumb = discord.File("assets/cs.png", filename="cs.png")

    view = PedidoCasamentoView(ctx.author, membro, msg, img_file)

    try:
        mensagem_botao = await membro.send(embed=embed_pedido, file=thumb, view=view)
    except discord.Forbidden:
        await ctx.send("⚠️ Não consegui enviar o pedido por DM. Enviando aqui mesmo.")
        mensagem_botao = await ctx.send(embed=embed_pedido, file=thumb, view=view)

    view.set_mensagem_de_botao(mensagem_botao)

@bot.command(name="divorciar")
async def divorciar(ctx):
    parceiro_id = await funcs.buscar_id_de_casamento(ctx.author.id)
    if not parceiro_id:
        return await ctx.send("❌ Você não está casado.")

    try:
        parceiro = await ctx.guild.fetch_member(parceiro_id)
    except:
        return await ctx.send("⚠️ Não consegui localizar seu parceiro atual.")

    embed = discord.Embed(description=f"Tem certeza que deseja se divorciar de {parceiro.mention}? 🥀", color=discord.Color.dark_theme())
    view = ConfirmarDivorcioView(ctx.author.id, parceiro_id)
    await ctx.send(embed=embed, view=view)

@bot.command(name="casal")
async def casal(ctx, membro: discord.Member = None):
    alvo = membro or ctx.author
    parceiro_id = await funcs.buscar_id_de_casamento(alvo.id)
    
    if not parceiro_id:
        return await ctx.send("❌ Este usuário não está casado.")

    try:
        parceiro = await ctx.guild.fetch_member(parceiro_id)
    except:
        return await ctx.send("⚠️ Não consegui localizar o outro membro do casal.")

    titulo = f"❤️ {alvo.display_name} é casado com {parceiro.display_name} ❤️" if membro else f"❤️ Você é casado com {parceiro.display_name} ❤️"

    avatar1_bytes = await alvo.display_avatar.read()
    avatar2_bytes = await parceiro.display_avatar.read()
    avatar1 = Image.open(BytesIO(avatar1_bytes))
    avatar2 = Image.open(BytesIO(avatar2_bytes))

    buffer = gerar_imagem_pedido(avatar1, avatar2)
    buffer.name = "casal.png"
    arquivo = discord.File(buffer, filename="casal.png")

    embed = discord.Embed(title=titulo, color=discord.Color.red())
    embed.set_image(url="attachment://casal.png")

    # Obter data do casamento
    async with AsyncSessionLocal() as session:
        from dbdata import Casamento
        ids = sorted([alvo.id, parceiro.id])
        result = await session.execute(
            select(Casamento).filter_by(user_id_1=ids[0], user_id_2=ids[1])
        )
        casamento = result.scalars().first()
        data_casamento = casamento.data.isoformat() if casamento else datetime.utcnow().isoformat()

    view = CasalStatsView(casal_ids=[alvo.id, parceiro.id], data_casamento=data_casamento)
    await ctx.send(embed=embed, file=arquivo, view=view)

# =========================
# LOGS E CONFIGURAÇÕES DE CANAL
# =========================

async def set_log_channel_db(guild_id: int, channel_id: int):
    async with AsyncSessionLocal() as session:
        result = await session.get(ChannelLogsConfiguration, guild_id)
        if result is None:
            cfg = ChannelLogsConfiguration(guild_id=guild_id, channel_id=channel_id)
            session.add(cfg)
        else:
            result.channel_id = channel_id
        await session.commit()

async def get_log_channel_id_db(guild_id: int) -> int | None:
    async with AsyncSessionLocal() as session:
        result = await session.get(ChannelLogsConfiguration, guild_id)
        if result:
            return int(result.channel_id)
    return None

def make_basic_embed(title: str, description: str = None, color: discord.Color = discord.Color.dark_gold()):
    return discord.Embed(title=title, description=description or "", color=color, timestamp=datetime.utcnow())

async def send_log(guild: discord.Guild, embed: discord.Embed, file: discord.File | None = None):
    channel_id = await get_log_channel_id_db(guild.id)
    if not channel_id:
        return
    channel = guild.get_channel(channel_id) or await bot.fetch_channel(channel_id)
    if channel is None:
        return
    try:
        if file:
            await channel.send(embed=embed, file=file)
        else:
            await channel.send(embed=embed)
    except Exception:
        pass

@bot.command(name="setlog", help="!setlog #canal -> Define o canal de logs deste servidor")
@commands.has_guild_permissions(administrator=True)
async def setlog(ctx: commands.Context, channel: discord.TextChannel):
    await set_log_channel_db(ctx.guild.id, channel.id)
    await ctx.reply(f"✅ Canal de logs configurado para {channel.mention}")

@bot.command(name="clearlog", help="!clearlog -> Remove a configuração de logs")
@commands.has_guild_permissions(administrator=True)
async def clearlog(ctx: commands.Context):
    async with AsyncSessionLocal() as session:
        cfg = await session.get(ChannelLogsConfiguration, ctx.guild.id)
        if cfg:
            await session.delete(cfg)
            await session.commit()
            await ctx.reply("✅ Configuração de logs removida.")
        else:
            await ctx.reply("❌ Nenhuma configuração de logs encontrada.")

@bot.command(name="configurarcanal")
@commands.has_permissions(manage_channels=True)
async def configurarcanal(ctx, channel: discord.TextChannel):
    async with AsyncSessionServerConfigs() as session:
        result = await session.execute(select(BancoDeDadosParaMensagemDeBemVindoPersonalizada).filter_by(guild_id=ctx.guild.id))
        guilddb = result.scalars().first()
        if not guilddb:
            guilddb = BancoDeDadosParaMensagemDeBemVindoPersonalizada(guild_id=ctx.guild.id)
            session.add(guilddb)
        guilddb.canal_bem_vindo = channel.id
        await session.commit()
    await ctx.reply(f"Canal configurado como {channel.mention}")

# =========================
# WELCOME / GOODBYE (ON_MEMBER_JOIN/REMOVE)
# =========================

@bot.event
async def on_member_join(member: discord.Member):
    async with AsyncSessionServerConfigs() as session:
        result = await session.execute(select(BancoDeDadosParaMensagemDeBemVindoPersonalizada).filter_by(guild_id=member.guild.id))
        guild_db = result.scalars().first()
        if not guild_db:
            guild_db = BancoDeDadosParaMensagemDeBemVindoPersonalizada(guild_id=member.guild.id)
            session.add(guild_db)
        result2 = await session.execute(select(DataForExtrasForWelcomeMessage).filter_by(guild_id=member.guild.id))
        embed_guild = result2.scalars().first()
        if not embed_guild:
            embed_guild = DataForExtrasForWelcomeMessage(guild_id=member.guild.id)
            session.add(embed_guild)

    mode = guild_db.MODO or "estatico"
    cor_faixa = guild_db.cor_faixa or (100, 180, 255)
    cor_text1 = guild_db.cor_text1 or "#ffffff"
    cor_text2 = guild_db.cor_text2 or "#000000"
    tamanho_da_imagem = guild_db.tamanho_da_imagem or 380
    largura = guild_db.largura_da_imagem or 650
    text1 = limpar_unicode(member.display_name)
    text2 = guild_db.text_content2 or "Bem vindo ao servidor."
    size_text1 = guild_db.size_text1 or 40
    size_text2 = guild_db.size_text2 or 25
    fonte = guild_db.font_message or "arial"
    translucidez = guild_db.translucidez_faixa or 160
    canal = guild_db.canal_bem_vindo
    avatar_path = await pegar_avatar_pillow(member)
    layout = guild_db.cor_embed or "base"

    caminho_fonte = caminho_da_fonte(fonte)

    if mode.lower() == 'gifmode':
        fundo_path = f'fundos_msg/{member.guild.id}.gif'
        if layout.lower() == "base":
            img = await gerar_gif_personalizado(
                fundo_path=fundo_path, avatar_path=avatar_path,
                texto_nome=text1, texto_sub=text2, translucidez_faixa=translucidez,
                cor_faixa=cor_faixa, fonte_caminho=caminho_fonte,
                tamanho_nome=size_text1, tamanho_sub=size_text2,
                imagem_altura=tamanho_da_imagem, largura_imagem=largura,
                text_color=cor_text1, color_text2=cor_text2
            )
            file_ = discord.File(img, filename="WelcomeMessage.gif")
        else:
            img = await gerar_gif_personalizado_layout2(
                fundo_path=fundo_path, avatar_path=avatar_path,
                texto_nome=text1, texto_sub=text2, translucidez_faixa=translucidez,
                cor_faixa=cor_faixa, fonte_caminho=caminho_fonte,
                tamanho_nome=size_text1, tamanho_sub=size_text2,
                imagem_altura=tamanho_da_imagem, largura_imagem=largura,
                text_color=cor_text1, text_cololr2=cor_text2
            )
            file_ = discord.File(img, filename="WelcomeMessage.gif")
    else:
        fundo_path = f'fundos_msg/{member.guild.id}.png'
        if layout == "base":
            img = await gerar_imagem_personalizada(
                fundo_path=fundo_path, avatar_path=avatar_path,
                texto_nome=text1, texto_sub=text2, translucidez_faixa=translucidez,
                cor_faixa=cor_faixa, fonte_caminho=caminho_fonte,
                tamanho_nome=size_text1, tamanho_sub=size_text2,
                imagem_altura=tamanho_da_imagem, color_text=cor_text1, color_text2=cor_text2
            )
            file_ = discord.File(img, filename='WelcomeMessage.png')
        else:
            img = await gerar_imagem_personalizado_layout2(
                fundo_path=fundo_path, avatar_path=avatar_path,
                texto_nome=text1, texto_sub=text2, translucidez_faixa=translucidez,
                cor_faixa=cor_faixa, fonte_caminho=caminho_fonte,
                tamanho_nome=size_text1, tamanho_sub=size_text2,
                imagem_altura=tamanho_da_imagem, text_color=cor_text1, text_cololr2=cor_text2
            )
            file_ = discord.File(img, filename="WelcomeMessage.png")

    channel = member.guild.get_channel(canal)
    if channel:
        await channel.send(member.mention, file=file_)

@bot.event
async def on_member_remove(member: discord.Member):
    async with AsyncSessionServerConfigs() as session:
        result = await session.execute(select(DataForGoodbyeMessage).filter_by(guild_id=member.guild.id))
        guild_db = result.scalars().first()
        if not guild_db:
            guild_db = DataForGoodbyeMessage(guild_id=member.guild.id)
            session.add(guild_db)
        result2 = await session.execute(select(DataForExtrasForGoodbyeMessage).filter_by(guild_id=member.guild.id))
        embed_guild = result2.scalars().first()
        if not embed_guild:
            embed_guild = DataForExtrasForGoodbyeMessage(guild_id=member.guild.id)
            session.add(embed_guild)

    mode = guild_db.MODO or "estatico"
    cor_faixa = guild_db.cor_faixa or (100, 180, 255)
    cor_text1 = guild_db.cor_text1 or "#ffffff"
    cor_text2 = guild_db.cor_text2 or "#000000"
    tamanho_da_imagem = guild_db.tamanho_da_imagem or 380
    largura = guild_db.largura_da_imagem or 650
    text1 = limpar_unicode(member.display_name)
    text2 = guild_db.text_content2 or "Até logo!"
    size_text1 = guild_db.size_text1 or 40
    size_text2 = guild_db.size_text2 or 25
    fonte = guild_db.font_message or "arial"
    translucidez = guild_db.translucidez_faixa or 160
    canal = guild_db.canal_bem_vindo
    avatar_path = await pegar_avatar_pillow(member)
    layout = guild_db.cor_embed or "base"

    caminho_fonte = caminho_da_fonte(fonte)

    if mode.lower() == 'gifmode':
        fundo_path = f'fundos_msg_goodbye/{member.guild.id}.gif'
        if layout.lower() == "base":
            img = await gerar_gif_personalizado(
                fundo_path=fundo_path, avatar_path=avatar_path,
                texto_nome=text1, texto_sub=text2, translucidez_faixa=translucidez,
                cor_faixa=cor_faixa, fonte_caminho=caminho_fonte,
                tamanho_nome=size_text1, tamanho_sub=size_text2,
                imagem_altura=tamanho_da_imagem, largura_imagem=largura,
                text_color=cor_text1, color_text2=cor_text2
            )
            file_ = discord.File(img, filename="GoodbyeMessage.gif")
        else:
            img = await gerar_gif_personalizado_layout2(
                fundo_path=fundo_path, avatar_path=avatar_path,
                texto_nome=text1, texto_sub=text2, translucidez_faixa=translucidez,
                cor_faixa=cor_faixa, fonte_caminho=caminho_fonte,
                tamanho_nome=size_text1, tamanho_sub=size_text2,
                imagem_altura=tamanho_da_imagem, largura_imagem=largura,
                text_color=cor_text1, text_cololr2=cor_text2
            )
            file_ = discord.File(img, filename="GoodbyeMessage.gif")
    else:
        fundo_path = f'fundos_msg_goodbye/{member.guild.id}.png'
        if layout == "base":
            img = await gerar_imagem_personalizada(
                fundo_path=fundo_path, avatar_path=avatar_path,
                texto_nome=text1, texto_sub=text2, translucidez_faixa=translucidez,
                cor_faixa=cor_faixa, fonte_caminho=caminho_fonte,
                tamanho_nome=size_text1, tamanho_sub=size_text2,
                imagem_altura=tamanho_da_imagem, color_text=cor_text1, color_text2=cor_text2
            )
            file_ = discord.File(img, filename='GoodbyeMessage.png')
        else:
            img = await gerar_imagem_personalizado_layout2(
                fundo_path=fundo_path, avatar_path=avatar_path,
                texto_nome=text1, texto_sub=text2, translucidez_faixa=translucidez,
                cor_faixa=cor_faixa, fonte_caminho=caminho_fonte,
                tamanho_nome=size_text1, tamanho_sub=size_text2,
                imagem_altura=tamanho_da_imagem, text_color=cor_text1, text_cololr2=cor_text2
            )
            file_ = discord.File(img, filename="GoodbyeMessage.png")

    channel = member.guild.get_channel(canal)
    if channel:
        await channel.send(file=file_)

# =========================
# USERINFO
# =========================

@bot.command(name="userinfo", aliases=["infouser"])
async def infouser(ctx: commands.Context, usuario_1: discord.Member = None):
    usuario_1 = usuario_1 or ctx.author

    userdbxp = await funcs.get_or_create_xp_user(usuario_1.id, ctx.guild.id)
    saldo = await funcs.get_user_balance(usuario_1.id)

    level = userdbxp.xp / 1000
    xp_arredondado = math.floor(level)

    avatar_url = usuario_1.avatar.url if usuario_1.avatar else usuario_1.default_avatar.url
    data_formatada = discord.utils.format_dt(usuario_1.created_at, 'f')
    data_formatada2 = discord.utils.format_dt(usuario_1.joined_at, 'f') if usuario_1.joined_at else "Não disponível"

    embedinfo = discord.Embed(title=f"Informações de: {usuario_1.display_name}", color=discord.Color.dark_blue())
    embedinfo.add_field(name="🆔 ID", value=f"`{usuario_1.id}`", inline=True)
    embedinfo.add_field(name="👤 Username", value=f"`{usuario_1.name}`", inline=True)
    embedinfo.add_field(name="📅 Criação", value=f"{data_formatada}", inline=True)
    embedinfo.set_thumbnail(url=avatar_url)
    embedinfo.set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    embedinfo.timestamp = discord.utils.utcnow()

    embedinfo2 = discord.Embed(title=f"Informações no Keith", color=discord.Color.dark_blue())
    embedinfo2.add_field(name="💰 MDBs", value=f"Saldo: `{saldo:,}`", inline=True)
    embedinfo2.add_field(name="🔮 XP no servidor", value=f"Level: `{xp_arredondado}`\nXP: `{userdbxp.xp}`", inline=True)
    embedinfo2.set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    embedinfo2.timestamp = discord.utils.utcnow()

    embedinfo3 = discord.Embed(title=f"Informações no servidor", color=discord.Color.dark_blue())
    embedinfo3.add_field(name="📆 Entrada", value=f"{data_formatada2}", inline=True)
    embedinfo3.add_field(name="👑 Maior Cargo", value=f"`{usuario_1.top_role.name}`", inline=True)
    embedinfo3.set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url if ctx.author.avatar else ctx.author.default_avatar.url)
    embedinfo3.timestamp = discord.utils.utcnow()

    await ctx.reply(embeds=[embedinfo, embedinfo2, embedinfo3])

# =========================
# WARN SYSTEM
# =========================

@bot.command(name="warn", aliases=['aplicarwarn'])
@commands.has_permissions(ban_members=True)
async def warns_users(ctx: commands.Context, member: discord.Member, motivo: str = None):
    motivo = motivo or "Motivo não especificado."
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(DataForWarns).filter_by(user_id=member.id, guild_id=ctx.guild.id))
        userdb = result.scalars().first()
        
        result2 = await session.execute(select(DataForGuildWarns).filter_by(guild_id=ctx.guild.id))
        guild_db = result2.scalars().first()

        if not guild_db:
            guild_db = DataForGuildWarns(guild_id=ctx.guild.id)
            session.add(guild_db)
        if not userdb:
            userdb = DataForWarns(user_id=member.id, guild_id=ctx.guild.id, warns=0)
            session.add(userdb)
        if userdb.warns is None:
            userdb.warns = 0
        if userdb.warns >= 10:
            return await ctx.reply("Este usuário já bateu o limite de 10 warns.")

        userdb.warns += 1
        quantity = userdb.warns
        await session.commit()

        cor_ = guild_db.cor_embed or '#000000'
        recado_ = guild_db.recado or 'Um animal foi punido!'
        title_ = guild_db.title or f'{member.display_name} levou um warn.'

    rgb = ImageColor.getrgb(cor_)
    r, g, b = [x / 255 for x in rgb]

    m = discord.Embed(title=f"{member.display_name} foi punido!", 
                      color=discord.Color.from_rgb(r=int(r), g=int(g), b=int(b)), timestamp=discord.utils.utcnow())
    m.add_field(name=title_, value=recado_, inline=False)
    m.add_field(name="Motivo:", value=motivo, inline=False)
    m.add_field(name="Warns", value=f"{member.display_name} tem {quantity} warns!", inline=False)
    m.set_thumbnail(url=ctx.author.avatar.url)
    m.set_footer(text=ctx.author.name, icon_url=ctx.author.avatar.url)
    await ctx.reply(embed=m)

@bot.command(name="unwarn", aliases=['retirarwarn', 'uw', 'rw', 'removewarn'])
@commands.has_permissions(ban_members=True)
async def unwarns_ser(ctx: commands.Context, member: discord.Member, motivo: str = None):
    motivo = motivo or "Motivo não especificado."

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(DataForWarns).filter_by(user_id=member.id, guild_id=ctx.guild.id))
        userdb = result.scalars().first()

        if not userdb:
            userdb = DataForWarns(user_id=member.id, guild_id=ctx.guild.id, warns=0)
            session.add(userdb)

        if userdb.warns <= 0:
            return await ctx.reply("❌ Este usuário não tem nenhum warn para ser retirado.")

        userdb.warns -= 1
        await session.commit()
        quantity = userdb.warns

    m = discord.Embed(title="✅ Warn removido com sucesso!", color=discord.Color.green(), timestamp=discord.utils.utcnow())
    m.add_field(name="⚠️ Total de Warns", value=f"{quantity}", inline=True)
    m.add_field(name="📝 Motivo", value=motivo, inline=True)
    m.set_thumbnail(url=member.avatar.url)
    m.set_footer(text=f"Retirado por {ctx.author}", icon_url=ctx.author.avatar.url)
    await ctx.reply(embed=m)

# =========================
# PREMIUM
# =========================

from dbdata import PremiumDataSuper, PremiumDataBase
from datetime import timezone

async def add_premium(user_id: int):
    async with AsyncSessionLocal() as session:
        user = await session.get(PremiumDataSuper, user_id)
        if user:
            user.data_premium_init = datetime.now(timezone.utc)
        else:
            new_user = PremiumDataSuper(user_id=user_id, data_premium_init=datetime.now(timezone.utc))
            session.add(new_user)
        await session.commit()

@bot.command(name="addp")
@commands.is_owner()
async def adicionar_vip(ctx, member: discord.User):
    await add_premium(member.id)
    await ctx.send(f"✅ {member.mention} agora é VIP!")
    try:
        await member.send("🎉 Parabéns! Seu VIP foi ativado manualmente pelo administrador.")
    except:
        pass

class RequestVIPView(View):
    def __init__(self, user_id: int):
        super().__init__(timeout=300)
        self.user_id = user_id

    @discord.ui.button(label="Solicitar VIP", style=discord.ButtonStyle.green)
    async def request_vip(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("Este botão não é para você.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        admin_user = await bot.fetch_user(1319876406355955753)
        embed = discord.Embed(title="🛎️ Novo pedido de VIP", 
                            description=f"O usuário {interaction.user.mention} ({interaction.user.id}) deseja comprar VIP.",
                            color=discord.Color.gold(), timestamp=datetime.utcnow())
        embed.add_field(name="Servidor", value=interaction.guild.name if interaction.guild else "Privado", inline=False)
        embed.set_footer(text="Confirme manualmente após o pagamento.")

        try:
            await admin_user.send(embed=embed)
            await interaction.followup.send("✅ Sua solicitação foi enviada! O administrador entrará em contato.", ephemeral=True)
        except:
            await interaction.followup.send("⚠️ Não consegui enviar a solicitação ao administrador. Tente novamente mais tarde.", ephemeral=True)

@bot.command(name="premium")
async def premium_info(ctx: commands.Context):
    premium_embed = discord.Embed(
        title="💎 Premium Do Keith!",
        description=(
            "🌌 Benefícios do Premium:\n\n"
            "- 📡 Prioridade no suporte.\n"
            "- 🧿 Opções de customização exclusivas para premium:\n"
            "- 🔮 **Perfil GIF**\n- 🔮 **Nome Gradiente no perfil**\n"
            "- 💰 Dobro de Daily\n- 💰 Prêmios de até 2.5M na roleta diária.\n\n"
            "- 💷 Custa: 10R$."
        ),
        timestamp=discord.utils.utcnow(),
        color=discord.Color.purple()
    )
    premium_embed.set_footer(text=ctx.author.name, icon_url=ctx.author.avatar.url)
    premium_embed.set_thumbnail(url='https://media.discordapp.net/attachments/1415295712207572992/1430442924281434222/d4b304ece37ade6b05fceb50f42e855f.png')
    await ctx.reply(embed=premium_embed, view=RequestVIPView(ctx.author.id))

# =========================
# RANKING
# =========================

class RankDesign:
    WIDTH, HEIGHT = 920, 680
    COLORS = {
        'background': '#2a2e35', 'card': '#000000', 'text': '#ffffff',
        'xp_bar': '#7289da', 'xp_background': '#1e2124',
        'top1': (0, 0, 0), 'top2': (0, 0, 0), 'top3': (0, 0, 0), 'highlight': '#43b581'
    }
    AVATAR_SIZE = (100, 100)
    USERS_PER_PAGE = 4

async def fetch_avatar(user: discord.User) -> BytesIO:
    async with aiohttp.ClientSession() as session:
        async with session.get(str(user.display_avatar.url)) as resp:
            return BytesIO(await resp.read())

async def generate_rank_image(guild: discord.Guild, users: List[UserXP], page: int) -> discord.File:
    img = Image.new('RGB', (RankDesign.WIDTH, RankDesign.HEIGHT), RankDesign.COLORS['background'])
    draw = ImageDraw.Draw(img)
    
    try:
        title_font = ImageFont.truetype('fonts/BebasNeue.ttf', 48)
        name_font = ImageFont.truetype('fonts/Roboto-Medium.ttf', 28)
        info_font = ImageFont.truetype('fonts/Roboto-Regular.ttf', 22)
    except:
        title_font = ImageFont.load_default()
        name_font = ImageFont.load_default()
        info_font = ImageFont.load_default()

    draw.text((40, 30), f"🏆 RANKING - {limpar_unicode(guild.name)}", font=title_font, fill=RankDesign.COLORS['text'])
    draw.line((40, 90, RankDesign.WIDTH - 40, 90), fill=RankDesign.COLORS['xp_bar'], width=3)

    y_offset = 120
    for idx, user_data in enumerate(users, start=1):
        rank = idx + (page-1) * RankDesign.USERS_PER_PAGE
        user = await bot.fetch_user(user_data.user_id)
        
        if rank == 1:
            card_color = (*RankDesign.COLORS['top1'], 150)
            border_color = RankDesign.COLORS['top1']
        elif rank == 2:
            card_color = (*RankDesign.COLORS['top2'], 150)
            border_color = RankDesign.COLORS['top2']
        elif rank == 3:
            card_color = (*RankDesign.COLORS['top3'], 150)
            border_color = RankDesign.COLORS['top3']
        else:
            card_color = (*[int(c*0.7) for c in ImageColor.getcolor(RankDesign.COLORS['card'], "RGB")], 200)
            border_color = RankDesign.COLORS['xp_bar']

        draw.rounded_rectangle((40, y_offset, RankDesign.WIDTH-40, y_offset+110), radius=20, fill=card_color, outline=border_color, width=3)
        draw.text((60, y_offset+40), f"#{rank}", font=name_font, fill=border_color if rank <= 3 else RankDesign.COLORS['text'])

        try:
            avatar_data = await fetch_avatar(user)
            avatar = Image.open(avatar_data).resize(RankDesign.AVATAR_SIZE)
            mask = Image.new('L', RankDesign.AVATAR_SIZE, 0)
            ImageDraw.Draw(mask).ellipse((0, 0, *RankDesign.AVATAR_SIZE), fill=255)
            border = Image.new('RGBA', (RankDesign.AVATAR_SIZE[0]+8, RankDesign.AVATAR_SIZE[1]+8))
            ImageDraw.Draw(border).ellipse((0, 0, RankDesign.AVATAR_SIZE[0]+8, RankDesign.AVATAR_SIZE[1]+8), fill=border_color)
            avatar.putalpha(mask)
            border.paste(avatar, (4, 4), avatar)
            img.paste(border, (120, y_offset+5), border)
        except:
            draw.ellipse((120, y_offset+5, 120+RankDesign.AVATAR_SIZE[0], y_offset+5+RankDesign.AVATAR_SIZE[1]), fill=border_color)
            draw.text((150, y_offset+40), "?", font=name_font, fill=RankDesign.COLORS['background'])

        draw.text((240, y_offset+20), limpar_unicode(user.display_name), font=name_font, fill=RankDesign.COLORS['text'])
        level_ = math.floor(user_data.xp / 1000 + 1)
        level_info = f"Level: {level_} • XP: {user_data.xp}"
        draw.text((240, y_offset+55), level_info, font=info_font, fill=RankDesign.COLORS['text'])

        xp = user_data.xp
        progresso = (xp % 1000) / 1000
        bar_width = int(500 * progresso)
        
        draw.rounded_rectangle((240, y_offset+85, 740, y_offset+95), radius=5, fill=RankDesign.COLORS['xp_background'])
        draw.rounded_rectangle((240, y_offset+85, 240+bar_width, y_offset+95), radius=5, fill='#811dbb')
        draw.text((750, y_offset+80), f"{progresso*100:.1f}%", font=info_font, fill=RankDesign.COLORS['text'])
        
        y_offset += 130

    total_pages = math.ceil(len(users) / RankDesign.USERS_PER_PAGE)
    draw.text((RankDesign.WIDTH-180, RankDesign.HEIGHT-40), f"Pagina {page}/{total_pages}", font=info_font, fill=RankDesign.COLORS['text'])

    buffer = BytesIO()
    img.save(buffer, 'PNG', quality=100, optimize=True)
    buffer.seek(0)
    return discord.File(buffer, filename=f"rank_page_{page}.png")

@bot.command(name="rank", aliases=["top", "ranking"])
async def rank_command(ctx, page: int = 1):
    loading_msg = await ctx.send("🔄 Gerando ranking...")
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserXP).filter_by(guild_id=ctx.guild.id).order_by(UserXP.xp.desc())
        )
        users = result.scalars().all()
        
        if not users:
            await loading_msg.delete()
            return await ctx.send("📊 Nenhum dado de XP encontrado neste servidor!")
        
        total_pages = math.ceil(len(users) / RankDesign.USERS_PER_PAGE)
        page = max(1, min(page, total_pages))
        
        start_index = (page - 1) * RankDesign.USERS_PER_PAGE
        end_index = start_index + RankDesign.USERS_PER_PAGE
        rank_image = await generate_rank_image(ctx.guild, users[start_index:end_index], page)
        
        embed = discord.Embed(
            title=f"Ranking de XP • {limpar_unicode(ctx.guild.name)}",
            description=f"Página {page}/{total_pages}",
            color=discord.Color.blurple()
        )
        embed.set_image(url=f"attachment://rank_page_{page}.png")
        embed.set_footer(text=f"Total de usuários: {len(users)} | Comando solicitado por {ctx.author.display_name}")
        
        await loading_msg.delete()
        await ctx.send(embed=embed, file=rank_image)

# =========================
# PEgar fundo
# =========================

@bot.command(name="pegarfundo", aliases=["pf", "pegarbackground", "pb"])
async def pegarfundo(ctx: commands.Context, user_: discord.User = None, tipo: str = None):
    user = user_ or ctx.author
    
    if tipo is None or tipo == "png":
        caminho = f'fundos/{user.id}.png'
        file = discord.File(caminho, filename=f"{user.id}.png")
        link = f"attachment://{user.id}.png"
    elif tipo == "gif":
        caminho = f'fundos/{user.id}.gif'
        file = discord.File(caminho, filename=f'{user.id}.gif')
        link = f"attachment://{user.id}.gif"

    m = discord.Embed(title=f"Aqui está o fundo de {user.display_name}", color=discord.Color.dark_purple(), timestamp=discord.utils.utcnow())
    m.set_thumbnail(url=user.avatar.url)
    m.set_image(url=link)
    m.set_footer(text=user.name, icon_url=user.avatar.url)
    await ctx.reply(embed=m, file=file)

# =========================
# ANIVERSÁRIO
# =========================

from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import Integer, String, Date, extract

Base = declarative_base()

class Birthday(Base):
    __tablename__ = "birthdays"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String)
    guild_id: Mapped[str] = mapped_column(String)
    date: Mapped[Date] = mapped_column(Date)

class GuildConfig(Base):
    __tablename__ = "guild_config"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    guild_id: Mapped[str] = mapped_column(String, unique=True)
    channel_id: Mapped[str] = mapped_column(String, nullable=True)

engine_birthday = create_engine("sqlite:///birthdays.db", echo=False)
SessionLocalBirthday = sessionmaker(bind=engine_birthday)

def init_db_birthday():
    Base.metadata.create_all(engine_birthday)

class BirthdayModal(discord.ui.Modal, title="Defina seu aniversário"):
    day = discord.ui.TextInput(label="Dia", placeholder="Ex: 15", min_length=1, max_length=2)
    month = discord.ui.TextInput(label="Mês", placeholder="Ex: 08", min_length=1, max_length=2)
    year = discord.ui.TextInput(label="Ano (opcional)", required=False, placeholder="Ex: 2000")

    async def on_submit(self, interaction: discord.Interaction):
        try:
            day = int(self.day.value)
            month = int(self.month.value)
            year = int(self.year.value) if self.year.value else 2000
            bday = date(year, month, day)

            with SessionLocalBirthday() as session:
                existing = session.query(Birthday).filter_by(
                    user_id=str(interaction.user.id), guild_id=str(interaction.guild.id)
                ).first()
                if existing:
                    existing.date = bday
                else:
                    new_bday = Birthday(user_id=str(interaction.user.id), guild_id=str(interaction.guild.id), date=bday)
                    session.add(new_bday)
                session.commit()

            await interaction.response.send_message(f"🎉 Seu aniversário foi definido para **{bday.strftime('%d/%m')}**!", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Data inválida. Tente novamente.", ephemeral=True)

@bot.command(name="niver")
async def aniversario(ctx):
    m = discord.Embed(title="Adicione seu aniversário no Keith!", 
                      description="Adicione a data de seu aniversário no Keith, e ele irá mandar um parabéns para você.",
                      color=discord.Color.purple(), timestamp=discord.utils.utcnow())
    m.set_footer(text=ctx.author.name, icon_url=ctx.author.avatar.url)

    button_view = discord.ui.View()
    button = discord.ui.Button(label="Adicionar Niver", style=discord.ButtonStyle.green)
    
    async def niver_configuration(interaction: discord.Interaction):
        if interaction.user.id != ctx.author.id:
            return await interaction.response.send_message("Somente o autor do comando pode usar esse botão.", ephemeral=True)
        await interaction.response.send_modal(BirthdayModal())
    
    button.callback = niver_configuration
    button_view.add_item(button)
    await ctx.reply(embed=m, view=button_view)

@bot.command(name="niverlist")
async def listar_aniversarios(ctx):
    with SessionLocalBirthday() as session:
        aniversarios = session.query(Birthday).filter_by(guild_id=str(ctx.guild.id)).all()

    if not aniversarios:
        await ctx.send("Nenhum aniversário cadastrado neste servidor 🎂")
        return

    msg = "🎉 **Aniversários registrados:**\n"
    for b in aniversarios:
        user = ctx.guild.get_member(int(b.user_id))
        nome = user.display_name if user else f"ID {b.user_id}"
        msg += f"- {nome}: {b.date.strftime('%d/%m')}\n"
    await ctx.send(msg)

@tasks.loop(hours=24)
async def check_birthdays():
    today = datetime.now().date()
    with SessionLocalBirthday() as session:
        aniversariantes = session.query(Birthday).filter(
            extract("month", Birthday.date) == today.month,
            extract("day", Birthday.date) == today.day
        ).all()

        guild_map = {}
        for b in aniversariantes:
            guild_map.setdefault(b.guild_id, []).append(b)

        for guild_id, lista in guild_map.items():
            guild = bot.get_guild(int(guild_id))
            if not guild:
                continue
            config = session.query(GuildConfig).filter_by(guild_id=guild_id).first()
            if not config or not config.channel_id:
                continue
            canal = guild.get_channel(int(config.channel_id))
            if not canal:
                continue
            for b in lista:
                user = guild.get_member(int(b.user_id))
                if user:
                    await canal.send(f"🎂 Feliz aniversário, {user.mention}! 🎉🥳")

# =========================
# EVENTOS PRINCIPAIS
# =========================

@bot.event
async def on_ready():
    await init_db()
    init_db_birthday()
    await bot.tree.sync()
    check_birthdays.start()
    print(f'Bot online como {bot.user} (ID: {bot.user.id})')
    await bot.change_presence(
        status=discord.Status.do_not_disturb,
        activity=discord.Activity(type=discord.ActivityType.watching, name="B - The Beginning.")
    )

# =========================
# ON_MESSAGE PARA XP
# =========================

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    
    xp_ganho = len(message.content)
    
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserXP).filter_by(user_id=message.author.id, guild_id=message.guild.id)
        )
        userdb = result.scalars().first()
        
        if not userdb:
            userdb = UserXP(user_id=message.author.id, guild_id=message.guild.id, xp=1)
            session.add(userdb)
        else:
            userdb.xp += xp_ganho if message.guild.id != 1400704538696089620 else 1005
        
        result2 = await session.execute(select(XpGlobal).filter_by(user_id=message.author.id))
        userdb2 = result2.scalars().first()
        
        if not userdb2:
            userdb2 = XpGlobal(user_id=message.author.id, xp=1)
            session.add(userdb2)
        else:
            userdb2.xp += xp_ganho if message.guild.id != 1400704538696089620 else 1005
        
        await session.commit()
    
    await bot.process_commands(message)

# =========================
# LOAD COGS
# =========================

async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            try:
                await bot.load_extension(f"cogs.{filename[:-3]}")
                print(f"[OK] Cog carregado: {filename}")
            except Exception as e:
                print(f"[ERRO] Falha ao carregar {filename}: {e}")

# =========================
# MAIN
# =========================

async def main():
    await init_db()
    await init_db_server()
    await init_db_editor()
    async with bot:
        await load_cogs()
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())