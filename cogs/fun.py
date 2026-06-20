import discord
from discord.ext import commands
from discord import app_commands
from dbdata import AsyncSessionLocal, TomatoData
from sqlalchemy.future import select
import random
import time
from functions import get_quantity_tomatos
import requests
import random
from PIL import Image, ImageColor, ImageFont, ImageDraw, ImageFilter
import io
import math
import aiohttp
import locale
import asyncio
import locale
from functionspillow import breakingnews
from dotenv import load_dotenv
import os

locale.setlocale(locale.LC_TIME, 'C')
load_dotenv(dotenv_path="C:\Users\thelo\Downloads\KeithFix\.env")

def avatar_com_borda_gradiente(avatar_img, size=(250, 250), border_size=8):
    avatar_img = avatar_img.resize(size).convert("RGBA")

    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, size[0], size[1]), fill=255)

    rounded_avatar = Image.new("RGBA", size, (0, 0, 0, 0))
    rounded_avatar.paste(avatar_img, (0, 0), mask=mask)

    border_size_total = (size[0] + border_size * 2, size[1] + border_size * 2)

    border_mask = Image.new("L", border_size_total, 0)
    border_draw = ImageDraw.Draw(border_mask)
    border_draw.ellipse((0, 0, border_size_total[0], border_size_total[1]), fill=255)
    border_draw.ellipse((border_size, border_size,
                         border_size_total[0]-border_size,
                         border_size_total[1]-border_size), fill=0)

    gradient = Image.new("RGBA", border_size_total, (0, 0, 0, 0))
    grad_draw = ImageDraw.Draw(gradient)

    for angle in range(360):
        r = int((math.sin(math.radians(angle)) * 127 + 128))
        g = int((math.sin(math.radians(angle + 120)) * 127 + 128))
        b = int((math.sin(math.radians(angle + 240)) * 127 + 128))

        grad_draw.pieslice([0, 0, border_size_total[0], border_size_total[1]],
                           start=angle, end=angle+2,
                           fill=(r, g, b, 255))

    border = Image.new("RGBA", border_size_total, (0, 0, 0, 0))
    border.paste(gradient, (0, 0), border_mask)

    border.paste(rounded_avatar, (border_size, border_size), rounded_avatar)

    return border

cor_fundo_1 = ImageColor.getrgb('#b907ff')
cor_fundo2 = ImageColor.getrgb('#ff0795')

def fazer_fundo_gradiente(size=(800, 400), colors=[cor_fundo_1, cor_fundo2], vertical=False):

    width, height = size
    background = Image.new("RGBA", size, (0, 0, 0, 255))
    draw = ImageDraw.Draw(background)

    n_colors = len(colors)
    step = (height if vertical else width) / (n_colors - 1)

    for i in range(n_colors - 1):
        c1, c2 = colors[i], colors[i + 1]

        for j in range(int(step)):
            t = j / step
            r = int(c1[0] + (c2[0] - c1[0]) * t)
            g = int(c1[1] + (c2[1] - c1[1]) * t)
            b = int(c1[2] + (c2[2] - c1[2]) * t)

            if vertical:
                y = int(i * step + j)
                draw.line([(0, y), (width, y)], fill=(r, g, b, 255))
            else:
                x = int(i * step + j)
                draw.line([(x, 0), (x, height)], fill=(r, g, b, 255))

    return background

def barra_progresso_ship(progress, width=400, height=50, particle_count=10):

    progress = max(0, min(progress, 100))
    bar_length = width 
    filled_length = int(width * (progress / 100))

    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    bg_color = (230, 230, 230, 255)
    border_color = (255, 182, 193, 255) 
    gradient_colors = [(255, 105, 180), (255, 0, 80), (148, 0, 211)]

    radius = height // 2

    shadow = Image.new("RGBA", (width+8, height+8), (0,0,0,0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.rounded_rectangle([4,4,width+4,height+4], radius=radius, fill=(0,0,0,120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(4))
    img.alpha_composite(shadow.crop((4,4,width+4,height+4)))

    draw.rounded_rectangle([0,0,width,height], radius=radius, fill=bg_color)

    draw.rounded_rectangle([0,0,width,height], radius=radius, outline=border_color, width=4)

    filled = Image.new("RGBA", (width, height), (0,0,0,0))
    fill_draw = ImageDraw.Draw(filled)

    for x in range(width):
        ratio = x / width
        if ratio < 0.5:
            r = int(gradient_colors[0][0] + (gradient_colors[1][0]-gradient_colors[0][0])*(ratio*2))
            g = int(gradient_colors[0][1] + (gradient_colors[1][1]-gradient_colors[0][1])*(ratio*2))
            b = int(gradient_colors[0][2] + (gradient_colors[1][2]-gradient_colors[0][2])*(ratio*2))
        else:
            r = int(gradient_colors[1][0] + (gradient_colors[2][0]-gradient_colors[1][0])*((ratio-0.5)*2))
            g = int(gradient_colors[1][1] + (gradient_colors[2][1]-gradient_colors[1][1])*((ratio-0.5)*2))
            b = int(gradient_colors[1][2] + (gradient_colors[2][2]-gradient_colors[1][2])*((ratio-0.5)*2))
        fill_draw.line([(x,0),(x,height)], fill=(r,g,b,255))

    mask = Image.new("L", (width, height), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0,0,filled_length,height], radius=radius, fill=255)

    img.paste(filled, (0,0), mask)

    shine = Image.new("RGBA", (width, height//3), (255,255,255,80))
    shine_draw = ImageDraw.Draw(shine)
    shine_draw.rounded_rectangle([0,0,width,height//3], radius=radius//2, fill=(255,255,255,80))
    img.paste(shine, (0,0), shine)

    try:
        font = ImageFont.truetype("fonts/NotoEmoji-VariableFont_wght.ttf", height//2)
    except:
        font = ImageFont.load_default()

    for _ in range(particle_count):
        if filled_length > 20:
            x = random.randint(5, filled_length-5)
            y = random.randint(0, height//2)
            draw.text((x,y), "💖", font=font, fill=(255,0,100,200))

    if filled_length > 20:
        draw.text((filled_length - height//2, 0), "💕", font=font, fill=(255,0,100,255))

    return img

from PIL import Image, ImageColor

def add_border_to_final_image(final_image, border_size=10, border_color="#ffffff"):
    if isinstance(border_color, str):
        border_color = ImageColor.getrgb(border_color) + (255,)

    width, height = final_image.size
    new_width = width + border_size * 2
    new_height = height + border_size * 2

    bordered_image = Image.new("RGBA", (new_width, new_height), border_color)

    bordered_image.paste(final_image, (border_size, border_size))

    return bordered_image

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

        self.futuros_individuais = [
            "Você terá uma vida de mais puro sofrimento, você mesmo percebe isso atualmente...",
            "Seu futuro vai ser complicado, mas no fim vai valer a pena...",
            "Aguarde, uma coisa bem ruim está preste a acontecer.",
            "Seu dia hoje será ótimo!",
            "Você ainda vai ter uma vida cheia de coisas boas, então não se preocupe.",
            "No futuro, você será o(a) primeiro(a) humano(a) a se casar com um robô emocionalmente inteligente.",
            "Seu futuro reserva uma invenção revolucionária: a primeira máquina de café que também faz massagens!",
            "Seu futuro envolve uma viagem no tempo, mas você acidentalmente ficará preso na década de 1920."
        ]
        
        self.futuros_duo = [
            "Vocês irão se casar no futuro.",
            "Vocês irão lutar até a morte.",
            "No fundo, vocês se odeiam.",
            "Sempre serão melhores amigos.",
            "Enfrentarão diversos desafios, mas sempre manterão a parceria.",
            "Juntos, vocês descobrirão uma espécie rara de panda que canta ópera!",
            "Inventarão uma linguagem secreta baseada em memes.",
            "Serão os primeiros humanos a colonizar Marte, mas vão passar o tempo todo discutindo."
        ]

    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog Geral carregado!")

    @commands.command()
    async def ola(self, ctx):
        await ctx.send(f"Olá, {ctx.author.mention}! 👋")

    @commands.command(name="8ball", aliases=["bola8"])
    async def bola8(self, ctx: commands.Context):
        respostas = [
            "Sim.",
            "Com certeza!",
            "Talvez.",
            "Definitivamente.",
            "Não.",
            "Talvez não.",
            "Definitivamente não.",
            "Acredito que não."
        ]
        
        resposta = random.choice(respostas)
        await ctx.reply(resposta)


    @commands.command(name="ship", aliases=["shipar", "amorchance"])
    async def shiptesteimage(self, ctx: commands.Context, member1: discord.User = None, member2: discord.User = None):
        if member1 is None:
            member1 = ctx.author
        if member2 is None:
            member2 = ctx.author

        chance = random.randint(0, 100)

        metade1 = member1.name[:len(member1.name)//2]
        metade2 = member2.name[len(member2.name)//2:]
        nome_ship = metade1 + metade2
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(str(member1.display_avatar.url)) as response1:
                    imagem1 = await response1.read()  
                async with session.get(str(member2.display_avatar.url)) as response2:
                    imagem2 = await response2.read() 
        except Exception as e:
            await ctx.send(f"❌ Erro ao baixar avatares: {e}")
            return

        barra = barra_progresso_ship(progress=chance)

        try:
            fundo_ship = fazer_fundo_gradiente()
            avatar1 = Image.open(io.BytesIO(imagem1))
            avatar2 = Image.open(io.BytesIO(imagem2))
            
            avatar_resized1 = avatar_com_borda_gradiente(avatar_img=avatar1)
            avatar_resized2 = avatar_com_borda_gradiente(avatar_img=avatar2)
            
            try:
                decoracao1 = Image.open('assets/amor.png').resize((130, 130)).convert('RGBA')
                fundo_ship.alpha_composite(decoracao1, (320, 115))
            except FileNotFoundError:
                print("Arquivo assets/amor.png não encontrado")
            
            fundo_ship.alpha_composite(avatar_resized1, (420, 50))
            fundo_ship.alpha_composite(avatar_resized2, (80, 50))
            fundo_ship.alpha_composite(barra, (200, 330))
            
            fundo_final_com_borda = add_border_to_final_image(fundo_ship, border_size=10, border_color="#ffffff")

            buffer = io.BytesIO()
            fundo_final_com_borda.save(buffer, format="PNG")
            buffer.seek(0)

        except Exception as e:
            await ctx.send(f"❌ Erro ao processar imagens: {e}")
            return

        amor = discord.Embed(
            title="_💍Chance de amor💜_", 
            description=f"**Chance de amor💜:** {chance}%. **Nome ship:** {nome_ship}."
        )
        
        amor.set_thumbnail(url=member1.display_avatar.url)  # ✅ Correto
        amor.set_footer(text=f'{ctx.guild.name}', icon_url=ctx.author.display_avatar.url)
        amor.set_image(url="attachment://ship.png")
        
        await ctx.send(
            embed=amor,
            file=discord.File(fp=buffer, filename="ship.png")
        )
        
    @app_commands.command(name="ship")
    async def shiptesteimage_slash(self, interaction:discord.Interaction, member1: discord.User = None, member2: discord.User = None):
        if member1 is None:
            member1 = interaction.user
        if member2 is None:
            member2 = interaction.user

        chance = random.randint(0, 100)

        metade1 = member1.name[:len(member1.name)//2]
        metade2 = member2.name[len(member2.name)//2:]
        nome_ship = metade1 + metade2
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(str(member1.display_avatar.url)) as response1:
                    imagem1 = await response1.read()  
                async with session.get(str(member2.display_avatar.url)) as response2:
                    imagem2 = await response2.read() 
        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao baixar avatares: {e}")
            return

        barra = barra_progresso_ship(progress=chance)

        try:
            fundo_ship = fazer_fundo_gradiente()
            avatar1 = Image.open(io.BytesIO(imagem1))
            avatar2 = Image.open(io.BytesIO(imagem2))
            
            avatar_resized1 = avatar_com_borda_gradiente(avatar_img=avatar1)
            avatar_resized2 = avatar_com_borda_gradiente(avatar_img=avatar2)
            
            try:
                decoracao1 = Image.open('assets/amor.png').resize((130, 130)).convert('RGBA')
                fundo_ship.alpha_composite(decoracao1, (320, 115))
            except FileNotFoundError:
                print("Arquivo assets/amor.png não encontrado")
            
            fundo_ship.alpha_composite(avatar_resized1, (420, 50))
            fundo_ship.alpha_composite(avatar_resized2, (80, 50))
            fundo_ship.alpha_composite(barra, (200, 330))
            
            fundo_final_com_borda = add_border_to_final_image(fundo_ship, border_size=10, border_color="#ffffff")

            buffer = io.BytesIO()
            fundo_final_com_borda.save(buffer, format="PNG")
            buffer.seek(0)

        except Exception as e:
            await interaction.response.send_message(f"❌ Erro ao processar imagens: {e}")
            return

        # ✅ Criar embed
        amor = discord.Embed(
            title="_💍Chance de amor💜_", 
            description=f"**Chance de amor💜:** {chance}%. **Nome ship:** {nome_ship}."
        )
        
        amor.set_thumbnail(url=member1.display_avatar.url)  # ✅ Correto
        amor.set_footer(text=f'{interaction.guild.name}', icon_url=interaction.user.display_avatar.url)
        amor.set_image(url="attachment://ship.png")
        
        await interaction.response.send_message(
            embed=amor,
            file=discord.File(fp=buffer, filename="ship.png")
        )

    async def giphyfunc(self, query: str, limite: int = 10) -> str | None:
        TENOR_API_KEY= os.getenv("TENOR_API_KEY")
        url = f"https://tenor.googleapis.com/v2/search?q={query}&key={TENOR_API_KEY}&limit={limite}"
        resposta = requests.get(url)

        if resposta.status_code == 200:
            dados = resposta.json()
            if "results" in dados and len(dados["results"]) > 0:
                gif = random.choice(dados["results"])
                return gif["media_formats"]["gif"]["url"]
        return None


    # =========================
    # COMANDOS DE TEXTO
    # =========================
    @commands.command(name="beijo", aliases=["kiss", "beijar"])
    async def beijar(self, ctx: commands.Context, member: discord.Member = None):
        await self._interacao_base(ctx, member, "anime kiss", "beijou", "Dois pombinhos se beijando.", "Não tente fazer isso novamente.", "Jamais beijaria uma pessoa aleátoria que mal conheço.")

    @commands.command(name="abraço", aliases=["abraco", "hug", "abracar", "abraçar"])
    async def abraco(self, ctx: commands.Context, member: discord.Member = None):
        await self._interacao_base(ctx, member, "anime hug or patpat", "abraço anime", "Grandes amigos, isso me lembra eu e minha irmã.", "Obrigado?", "Nunca fui muito fã de abraços.")

    @commands.command(name="cafuné", aliases=["carinho", "patpat", "cute", "pat"])
    async def cafune(self, ctx: commands.Context, member: discord.Member = None):
        await self._interacao_base(ctx, member, "anime pat", "fez cafuné em", "Grandes amigos, isso me lembra eu e minha irmã.", "Obrigado?", "Nunca fui muito fã de carinho.")

    @commands.command(name="tapa", aliases=["slap"])
    async def slap_inte(self, ctx:commands.Context, member:discord.Member = None):
        await self._interacao_base(ctx, member, "anime luta", "Deu um tapão em", "Que violência...", "Não me Dê um tapa, baitola.", "_____")

    @commands.command(name="bombardeio")
    async def bombardeio(self, ctx: commands.Context, member: discord.Member = None):
        if not member:
            return await ctx.reply("Você precisa marcar um usuário para o comando funcionar corretamente.")

        embed = discord.Embed(
            title=f"Bombardeio no {member.display_name}",
            description=f"{ctx.author.mention}, está bombardeando a casa do {member.mention}."
        )
        embed.set_image(url="https://media1.giphy.com/media/v1.Y2lkPTc5MGI3NjExYnRhcnh4eHh3N3A1MWxpeWRiaWhtN2p3dDBwdGtiMzl2czZldmd0ciZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/oe33xf3B50fsc/giphy.gif")
        embed.set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    # =========================
    # COMANDOS SLASH
    # =========================
    @app_commands.command(name="beijo")
    async def beijar_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        await self._interacao_base(interaction, member, "anime kiss", "beijou", "Dois pombinhos se beijando.", "Não tente fazer isso novamente.", "Jamais beijaria uma pessoa aleátoria que mal conheço.", slash=True)

    @app_commands.command(name="abraço")
    async def abraco_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        await self._interacao_base(interaction, member, "anime hug", "abraçou", "Grandes amigos, isso me lembra eu e minha irmã.", "Obrigado?", "Nunca fui muito fã de abraços.", slash=True)

    @app_commands.command(name="cafuné")
    async def cafune_slash(self, interaction: discord.Interaction, member: discord.Member = None):
        await self._interacao_base(interaction, member, "anime pat", "fez cafuné em", "Grandes amigos, isso me lembra eu e minha irmã.", "Obrigado?", "Nunca fui muito fã de carinho.", slash=True)

    @app_commands.command(name="tapa")
    async def slap_inte_slash(self, interaction:discord.Interaction, member:discord.Member = None):
        await self._interacao_base(interaction, member, "anime punch", "Deu um tapão em", "Que violência...", "Não me Dê um tapa, baitola.", "_____", slash=True)


    # =========================
    # FUNÇÃO BASE DE INTERAÇÕES
    # =========================
    async def _interacao_base(
        self,
        ctx_or_interact,
        member: discord.Member,
        termo_gif: str,
        acao: str,
        descricao_normal: str,
        titulo_bot: str,
        descricao_bot: str,
        slash: bool = False
    ):
        pegar_gif = await self.giphyfunc(termo_gif)
        author = ctx_or_interact.user if slash else ctx_or_interact.author

        if member == author.bot:
            embedbot = discord.Embed(title=titulo_bot, description=descricao_bot, color=discord.Color.dark_blue())
            embedbot.set_image(url="https://media.discordapp.net/attachments/1400704538696089623/1405708238539984999/0bf42f74a88967fdd21f37a25bf851ea.png")
            embedbot.set_footer(text="Keith Kazama Flick", icon_url="https://media.discordapp.net/attachments/1400704538696089623/1405341056899481681/image.png")
            embedbot.timestamp = discord.utils.utcnow()
            if slash:
                await ctx_or_interact.response.send_message(embed=embedbot)
            else:
                await ctx_or_interact.reply(embed=embedbot)
            return

        if member is None:
            member = author
            embedsolo = discord.Embed(title=f"{author.display_name} {acao} a si mesmo?", description="Você definitivamente tá carente, e também é estranho.", color=discord.Color.red())
            embedsolo.set_image(url=pegar_gif)
            embedsolo.set_footer(text=f"{acao.capitalize()} por {author.name}")
            embedsolo.timestamp = discord.utils.utcnow()
            if slash:
                await ctx_or_interact.response.send_message(embed=embedsolo)
            else:
                await ctx_or_interact.reply(embed=embedsolo)
            return

        embed = discord.Embed(title=f"{author.display_name} {acao} {member.display_name}", description=descricao_normal, color=discord.Color.dark_blue())
        embed.set_image(url=pegar_gif)
        embed.set_footer(text=f"{acao.capitalize()} por {author.name}", icon_url=author.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        if slash:
            await ctx_or_interact.response.send_message(embed=embed)
        else:
            await ctx_or_interact.reply(embed=embed)

    @commands.command(name="ping")
    async def ping_nm(self, ctx):
        """Mostra a latência do bot"""
        ws_latency = round(self.bot.latency * 1000)
        
        rest_start = time.perf_counter()
        message = await ctx.reply("Calculando latência...")
        rest_end = time.perf_counter()
        rest_latency = round((rest_end - rest_start) * 1000)
        
        uptime_seconds = round(time.time() - self.start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"
        
        verde_url = "https://cdn.discordapp.com/attachments/1320526861322944602/1393256930100903977/884924726814867457.png"
        amarelo_url = "https://cdn.discordapp.com/attachments/1320526861322944602/1393256929769558107/884924627799916605.png"
        vermelho_url = "https://cdn.discordapp.com/attachments/1320526861322944602/1393256929517768734/884924036558250044.png"
        
        if ws_latency < 150:
            thumbnail_url = verde_url
            embed_color = discord.Color.green()
        elif ws_latency < 300:
            thumbnail_url = amarelo_url
            embed_color = discord.Color.orange()
        else:
            thumbnail_url = vermelho_url
            embed_color = discord.Color.red()
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"🔗 **WebSocket:** `{ws_latency} ms`\n🔗 **REST:** `{rest_latency} ms`\n⏱️ **Uptime:** `{uptime_str}`",
            color=embed_color
        )
        embed.set_thumbnail(url=thumbnail_url)
        
        await message.edit(content=None, embed=embed)

    @app_commands.command(name="ping")
    async def ping(self, interaction:discord.Interaction):
        ws_latency = round(self.bot.latency * 1000)
        
        rest_start = time.perf_counter()
        rest_end = time.perf_counter()
        rest_latency = round((rest_end - rest_start) * 1000)
        
        uptime_seconds = round(time.time() - self.start_time)
        hours, remainder = divmod(uptime_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"
        
        verde_url = "https://cdn.discordapp.com/attachments/1320526861322944602/1393256930100903977/884924726814867457.png"
        amarelo_url = "https://cdn.discordapp.com/attachments/1320526861322944602/1393256929769558107/884924627799916605.png"
        vermelho_url = "https://cdn.discordapp.com/attachments/1320526861322944602/1393256929517768734/884924036558250044.png"
        
        if ws_latency < 150:
            thumbnail_url = verde_url
            embed_color = discord.Color.green()
        elif ws_latency < 300:
            thumbnail_url = amarelo_url
            embed_color = discord.Color.orange()
        else:
            thumbnail_url = vermelho_url
            embed_color = discord.Color.red()
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"🔗 **WebSocket:** `{ws_latency} ms`\n🔗 **REST:** `{rest_latency} ms`\n⏱️ **Uptime:** `{uptime_str}`",
            color=embed_color
        )
        embed.set_thumbnail(url=thumbnail_url)
        
        await interaction.response.send_message(embed=embed)

    @commands.command(name="pfp", aliases=["avatar"])
    async def avatar(self, ctx, usuario: discord.User = None):
        """Mostra o avatar de um usuário"""
        usuario = usuario or ctx.author
        
        embed = discord.Embed(
            title=f'{usuario.display_name}',
            description=f"Avatar de {usuario.mention}",
            color=discord.Color.dark_red()
        )
        
        embed.set_image(url=usuario.display_avatar.url)
        
        if ctx.guild and ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)
            
        embed.set_footer(text=f"Solicitado por {ctx.author.display_name}", 
                        icon_url=ctx.author.display_avatar.url)
        
        await ctx.reply(embed=embed)

    @commands.command(name="serverinfo", aliases=["si", "infoservidor"])
    async def serverinfo(self, ctx, server_id: int = None):
        """Mostra informações do servidor (atual ou pelo ID)"""

        guild = None
        if server_id:
            guild = self.bot.get_guild(server_id)
            if guild is None:
                return await ctx.reply("❌ Não encontrei nenhum servidor com esse ID.")
        else:
            guild = ctx.guild

        nome_server = guild.name
        id_sv = guild.id
        data_criacao = guild.created_at.strftime("%d/%m/%Y %H:%M:%S")
        membros = guild.member_count

        humanos = sum(1 for m in guild.members if not m.bot)
        bots = membros - humanos

        canais_texto = len(guild.text_channels)
        canais_voz = len(guild.voice_channels)
        categorias = len(guild.categories)
        total_canais = canais_texto + canais_voz + categorias

        cargos = len(guild.roles)
        boosts = guild.premium_subscription_count
        nivel_boost = guild.premium_tier
        emojis = len(guild.emojis)

        embed = discord.Embed(
            title="📊 Informações do Servidor",
            description=f"**{nome_server}**",
            color=discord.Color.dark_blue(),
            timestamp=ctx.message.created_at
        )

        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        if guild.banner:
            embed.set_image(url=guild.banner.url)

        if guild.owner:
            embed.add_field(name="👑 Dono", value=f"{guild.owner.mention} (`{guild.owner.id}`)", inline=False)
        else:
            embed.add_field(name="👑 Dono", value="Indefinido", inline=False)

        embed.add_field(name="🆔 ID do Servidor", value=f"`{id_sv}`", inline=False)
        embed.add_field(name="📅 Criado em", value=f"`{data_criacao}`", inline=False)

        embed.add_field(
            name="👥 Membros",
            value=f"Total: **{membros}**\n👤 Humanos: **{humanos}**\n🤖 Bots: **{bots}**",
            inline=True
        )

        embed.add_field(
            name="📂 Canais",
            value=(
                f"Categorias: **{categorias}**\n"
                f"Texto: **{canais_texto}**\n"
                f"Voz: **{canais_voz}**\n"
                f"Total: **{total_canais}**"
            ),
            inline=True
        )

        embed.add_field(
            name="✨ Extras",
            value=(
                f"Cargos: **{cargos}**\n"
                f"Boosts: **{boosts}** (Nível {nivel_boost})\n"
                f"Emojis: **{emojis}**"
            ),
            inline=False
        )

        embed.set_footer(
            text=f"Requisitado por {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )

        await ctx.reply(embed=embed)

    @app_commands.command(name="serverinfo", description="Verifique as informações de um servidor.")
    async def serverinfo_slash(self, interaction:discord.Interaction):
        guild = interaction.guild
        
        nome_server = guild.name
        id_sv = guild.id
        data_criacao = guild.created_at.strftime("%d/%m/%Y %H:%M:%S")
        membros = guild.member_count
        
        humanos = sum(1 for m in guild.members if not m.bot)
        bots = membros - humanos
        
        canais_texto = len(guild.text_channels)
        canais_voz = len(guild.voice_channels)
        categorias = len(guild.categories)
        total_canais = canais_texto + canais_voz + categorias
        
        cargos = len(guild.roles)
        boosts = guild.premium_subscription_count
        nivel_boost = guild.premium_tier
        emojis = len(guild.emojis)
        
        embed = discord.Embed(
            title=f"📊 Informações do Servidor",
            description=f"**{nome_server}**",
            color=discord.Color.dark_blue(),
            timestamp=discord.utils.utcnow()
        )
        
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        if guild.banner:
            embed.set_image(url=guild.banner.url)
        
        embed.add_field(name="👑 Dono", value=f"{guild.owner.mention} (`{guild.owner.id}`)", inline=False)
        embed.add_field(name="🆔 ID do Servidor", value=f"`{id_sv}`", inline=False)
        embed.add_field(name="📅 Criado em", value=f"`{data_criacao}`", inline=False)
        
        embed.add_field(
            name="👥 Membros",
            value=f"Total: **{membros}**\n👤 Humanos: **{humanos}**\n🤖 Bots: **{bots}**",
            inline=True
        )
        
        embed.add_field(
            name="📂 Canais",
            value=(
                f"Categorias: **{categorias}**\n"
                f"Texto: **{canais_texto}**\n"
                f"Voz: **{canais_voz}**\n"
                f"Total: **{total_canais}**"
            ),
            inline=True
        )
        
        embed.add_field(
            name="✨ Extras",
            value=(
                f"Cargos: **{cargos}**\n"
                f"Boosts: **{boosts}** (Nível {nivel_boost})\n"
                f"Emojis: **{emojis}**"
            ),
            inline=False
        )
        
        author = interaction.user
        embed.set_footer(text=f"{author.display_name}", 
                        icon_url=author.display_avatar.url)
        
        await interaction.response.send_message(embed=embed)

    @commands.command(name="perdeutudo")
    async def meme_perdeu_tudo(self, ctx, member: discord.Member = None):
        """Gera um meme 'perdeu tudo'"""
        member = member or ctx.author
        
        try:
            fundo_meme = Image.open('assets/MEME2.jpg').convert('RGBA')
            
            async with aiohttp.ClientSession() as session:
                async with session.get(str(member.display_avatar.url)) as resp:
                    if resp.status != 200:
                        return await ctx.reply("Não foi possível baixar o avatar.")
                    avatar_bytes = await resp.read()

            avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert('RGBA')
            avatar_img = avatar_img.resize((180, 180))
            
            draw = ImageDraw.Draw(fundo_meme)
            try:
                font = ImageFont.truetype('fonts/OpenSans_Condensed-Regular.ttf', 40)
            except:
                font = ImageFont.load_default()
                
            draw.text((60, 280), f"{member.name}", font=font, fill=(0, 0, 0))
            
            fundo_meme.paste(avatar_img, (65, 100), avatar_img)
            
            with io.BytesIO() as image_binary:
                fundo_meme.save(image_binary, "PNG")
                image_binary.seek(0)
                await ctx.send(file=discord.File(fp=image_binary, filename="meme_luxo_ao_lixo.png"))
        except Exception as e:
            await ctx.send(f"Ocorreu um erro ao processar a imagem: {str(e)}")
                
    @app_commands.command(name="perdeutudo", description="Faça um meme com um amigo seu.")
    async def meme_perdeu_tudo_slash(self, interaction:discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        
        try:
            fundo_meme = Image.open('assets/MEME2.jpg').convert('RGBA')
            
            async with aiohttp.ClientSession() as session:
                async with session.get(str(member.display_avatar.url)) as resp:
                    if resp.status != 200:
                        return await interaction.response.send_message("Não foi possível baixar o avatar.")
                    avatar_bytes = await resp.read()

            avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert('RGBA')
            avatar_img = avatar_img.resize((180, 180))
            
            draw = ImageDraw.Draw(fundo_meme)
            try:
                font = ImageFont.truetype('fonts/OpenSans_Condensed-Regular.ttf', 40)
            except:
                font = ImageFont.load_default()
                
            draw.text((60, 280), f"{member.name}", font=font, fill=(0, 0, 0))
            
            fundo_meme.paste(avatar_img, (65, 100), avatar_img)
            
            with io.BytesIO() as image_binary:
                fundo_meme.save(image_binary, "PNG")
                image_binary.seek(0)
                await interaction.response.send_message(file=discord.File(fp=image_binary, filename="meme_luxo_ao_lixo.png"))
                
        except Exception as e:
            await interaction.response.send_message(f"Ocorreu um erro ao processar a imagem: {str(e)}")

    @commands.command(name="fate")
    async def fate(self, ctx):
        """Revela seu futuro"""
        resposta = random.choice(self.futuros_individuais)
        embed = discord.Embed(
            title="🔮 Sua Previsão",
            description=resposta,
            color=discord.Color.purple()
        )
        embed.set_footer(text=f"Para {ctx.author.display_name}")
        await ctx.reply(embed=embed)

    @commands.command(name="vidente")
    async def vidente(self, ctx, usuario: discord.User = None):
        """Revela o futuro de um duo - Use: <vidente @usuário"""
        if usuario is None:
            embed = discord.Embed(
                title="Como usar o comando vidente",
                description="Marque um amigo para ver qual é o futuro de vocês dois!\nExemplo: `<vidente @amigo`",
                color=discord.Color.blue()
            )
            await ctx.reply(embed=embed)
            return
            
        if usuario == ctx.author:
            return await ctx.reply("Você não pode ver seu futuro com você mesmo!")
            
        resposta = random.choice(self.futuros_duo)
        embed = discord.Embed(
            title="🔮 Previsão em Duo",
            description=resposta,
            color=discord.Color.purple()
        )
        embed.set_footer(text=f"Previsão para {ctx.author.display_name} e {usuario.display_name}")
        await ctx.reply(embed=embed)

    @commands.command(name="serverbanner")
    async def serverbanner(self, ctx):
        guild = ctx.guild
        if guild.banner:
            embed = discord.Embed(
                title=f"Banner do servidor: {guild.name}",
                color=discord.Color.blue()
            )
            embed.set_image(url=guild.banner.url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Este servidor não tem um banner.")
            
    @app_commands.command(name="serverbanner")
    async def serverbanner_slash(self, interaction:discord.Interaction):
        guild = interaction.guild
        if guild.banner:
            embed = discord.Embed(
                title=f"Banner do servidor: {guild.name}",
                color=discord.Color.blue()
            )
            embed.set_image(url=guild.banner.url)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Este servidor não tem um banner.")

    @commands.command(name="banner")
    async def banner(self, ctx: commands.Context, usuario: discord.User = None):
        usuario = usuario or ctx.author

        try:
            banner_url = usuario.banner.url if usuario.banner else None
        except Exception as e:
            banner_url = None

        if not banner_url:
            return await ctx.send(f" **{usuario.display_name}** não possui um banner.", ephemeral=True)

        embed = discord.Embed(
            title=f"🖼️ Banner de {usuario.display_name}",
            description="Aqui está o banner!",
            color=discord.Color.dark_blue()
        )
        embed.set_image(url=banner_url)
        embed.set_footer(
            text=f"Requisitado por {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )

        await ctx.send(embed=embed)
        
    @app_commands.command(name="banner")
    async def banner_slash(self, interaction:discord.Interaction, usuario: discord.User = None):
        usuario = usuario or interaction.user
        author = interaction.user

        try:
            banner_url = usuario.banner.url if usuario.banner else None
        except Exception as e:
            banner_url = None

        if not banner_url:
            return await interaction.response.send_message(f" **{usuario.display_name}** não possui um banner.", ephemeral=True)

        embed = discord.Embed(
            title=f"🖼️ Banner de {usuario.display_name}",
            description="Aqui está o banner!",
            color=discord.Color.dark_blue()
        )
        embed.set_image(url=banner_url)
        embed.set_footer(
            text=f"{author.display_name}",
            icon_url=author.display_avatar.url
        )

        await interaction.response.send_message(embed=embed)

    @commands.command(name="avatarservidor", aliases=["iconsv", "iconserver", "avatarserver", "avatarsv"])
    async def avatarservidor(self, ctx):
        if ctx.guild.icon:
            embed = discord.Embed(
                title=f"Avatar do servidor: {ctx.guild.name}",
                color=discord.Color.dark_blue()
            )
            embed.set_image(url=ctx.guild.icon.url)
            embed.set_footer(text=f"Solicitado por {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
            await ctx.send(embed=embed)
        else:
            await ctx.send("Este servidor não possui avatar.")
            
    @app_commands.command(name="avatarservidor", description="Consiga o avatar do servidor.")
    async def avatarservidor_slash(self, interaction:discord.Interaction):
        author = interaction.user
        if interaction.guild.icon:
            embed = discord.Embed(
                title=f"Avatar do servidor: {interaction.guild.name}",
                color=discord.Color.dark_blue()
            )
            embed.set_image(url=interaction.guild.icon.url)
            embed.set_footer(text=f"Solicitado por {interaction.user.name}", icon_url=author.avatar.url if author.avatar else None)
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message("Este servidor não possui avatar.")

    @commands.command(name="suporte", aliases=["support", "servidorsuporte", "svsuporte"])
    async def support(self, ctx:commands.Context):
        author = ctx.author
        
        support_embed = discord.Embed(
            title="Servidor suporte do Keith.",
            description="Aqui está o meu servidor onde você pode buscar ajuda sobre o bot, tirar dúvidas e sugerir melhorias.\n\n* LINK: [Servidor](https://discord.gg/t63Xf2PSFh)",
            color=discord.Color.dark_blue()
        )
        support_embed.set_thumbnail(url='https://media.discordapp.net/attachments/1410462821396774924/1411808908976066590/f9d0184cb5a304c6dc76faf534b5e2ef.png?ex=68b60102&is=68b4af82&hm=a5e539f8a650ce8dfdace4fc0ec1b066272fb831349fed466f79f8c3ec1ce417&=&format=webp&quality=lossless&width=350&height=350')
        support_embed.set_footer(text=f'Requisitado por {author.name}', icon_url=author.avatar.url)
        support_embed.timestamp = discord.utils.utcnow()

        await ctx.reply(embed=support_embed)
        
    @app_commands.command(name="suporte", description="Consiga o link do servidor de suporte do bot.")
    async def support_slash(self, interaction:discord.Interaction):
        author = interaction.user
        
        support_embed = discord.Embed(
            title="Servidor suporte do Keith.",
            description="Aqui está o meu servidor onde você pode buscar ajuda sobre o bot, tirar dúvidas e sugerir melhorias.\n\n* LINK: [Servidor](https://discord.gg/t63Xf2PSFh)",
            color=discord.Color.dark_blue()
        )
        support_embed.set_thumbnail(url='https://media.discordapp.net/attachments/1410462821396774924/1411808908976066590/f9d0184cb5a304c6dc76faf534b5e2ef.png?ex=68b60102&is=68b4af82&hm=a5e539f8a650ce8dfdace4fc0ec1b066272fb831349fed466f79f8c3ec1ce417&=&format=webp&quality=lossless&width=350&height=350')
        support_embed.set_footer(text=f'Requisitado por {author.name}', icon_url=author.avatar.url)
        support_embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=support_embed)

    @commands.command(name="invite", aliases=["convitebot", "linkinvite", "convitelink"])
    async def invitebot(self, ctx:commands.Context):
        author = ctx.author

        invite_embed = discord.Embed(
            title="Meu link de convite!",
            description="Aqui está meu link para me colocar em outros servidores.\n\n* LINK: [Convite](https://discord.com/oauth2/authorize?client_id=1367932530938089472&permissions=8&integration_type=0&scope=bot)",
            color=discord.Color.dark_blue()
        )
        invite_embed.set_thumbnail(url=author.avatar.url)
        invite_embed.set_footer(text=f'Requisitado por {author.name}', icon_url=author.avatar.url)
        invite_embed.timestamp = discord.utils.utcnow()

        await ctx.reply(embed=invite_embed)
        
    @app_commands.command(name="invite", description="Pegue o convite do bot.")
    async def invitebot_slash(self, interaction:discord.Interaction):
        author = interaction.user

        invite_embed = discord.Embed(
            title="Meu link de convite!",
            description="Aqui está meu link para me colocar em outros servidores.\n\n* LINK: [Convite](https://discord.com/oauth2/authorize?client_id=1367932530938089472&permissions=8&integration_type=0&scope=bot)",
            color=discord.Color.dark_blue()
        )
        invite_embed.set_thumbnail(url=author.avatar.url)
        invite_embed.set_footer(text=f'Requisitado por {author.name}', icon_url=author.avatar.url)
        invite_embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=invite_embed)        
        
    @commands.command(name="tomatar")
    async def tomatar_user(self, ctx:commands.Context, user:discord.User = None):
        
        if user is None:
            return await ctx.reply("Marque um usuário, para usar o comando de forma correta.")
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(TomatoData).filter_by(user_id=ctx.author.id))
            userdb = result.scalars().first()
            if not userdb:
                userdb = TomatoData(user_id=ctx.author.id, tomatos_quantity=1)
                session.add(userdb)
            userdb.tomatos_quantity += 1
            await session.commit()
        
        quantity = await get_quantity_tomatos(ctx.author.id)
        
        gif = random.choice(
            [
                "https://cdn.discordapp.com/attachments/1410462821396774924/1457758485033783379/memes.png?ex=695d2ae2&is=695bd962&hm=fe588163265e712b9191903a3d6bd29324fe5e19795deb0b14cde68ae7d87cb8&",
                "https://cdn.discordapp.com/attachments/1410462821396774924/1457759163152207926/nelson-deossa-pachuca.gif?ex=695d2b84&is=695bda04&hm=49fb010d421606760b97aa27073d2dddf030296480edcb7702c827f7c893e468&",
                "https://cdn.discordapp.com/attachments/1410462821396774924/1457769475368812751/tomatoes-tomato.gif?ex=695d351e&is=695be39e&hm=d56898b7b65a25098b9b924404db5924a6f790cea732a7d8194115e7423a4c3a&",
                "https://cdn.discordapp.com/attachments/1410462821396774924/1457769509501800711/little-witch-academia-akko.gif?ex=695d3527&is=695be3a7&hm=4a996f782344d7d1644ba1a4aee5d57b388d7aa378906676428f5072ef8cd47e&",
                "https://cdn.discordapp.com/attachments/1410462821396774924/1457769531232485407/ic0niclisa-throwing.gif?ex=695d352c&is=695be3ac&hm=9132c02e8150dcfcecbdc620c1c65d000a7186004ece38ea20f5c95b29fd802e&",
                "https://cdn.discordapp.com/attachments/1410462821396774924/1457769563356922019/ramy-bensebaini-ramy-bensebaini-throwing-a-tomato.gif?ex=695d3533&is=695be3b3&hm=fab9fc69421d5ce4a39cd6f478daae0b5d3c042d902a8155c189b3482d8db005&"
            ]
        )
        
        embed = discord.Embed(
            title=f"🍅 Tomatada!",
            description=f"🍅 {user.mention} foi tomatado! 🍅\n- {ctx.author.mention} já tomatou {quantity} pessoas 🍅",
            timestamp=discord.utils.utcnow(),
            color=discord.Color.red()
        )
        
        embed.set_image(url=gif)
        embed.set_thumbnail(url=user.avatar.url)
        embed.set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url)
        
        await ctx.reply(embed=embed)

async def setup(bot):
    await bot.add_cog(Fun(bot))