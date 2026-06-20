import discord
from discord.ext import commands
import asyncio
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from dbdata import AsyncSessionLocal, UserMDBs  # ajuste conforme seu DB
from sqlalchemy.future import select
from sqlalchemy import desc
import random
import aiohttp
import unicodedata

def limpar_unicode(texto):
    texto = unicodedata.normalize("NFKC", texto)
    texto = texto.replace("□", "") 
    return ''.join(
        c for c in texto
        if c.isprintable() and (ord(c) < 128 or c in "çãáéíóúàêôÇÃÁÉÍÓÚÀÊÔ -_")
    )

class RankCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def obter_usuario_avatar(self, user_id):
        try:
            user = await self.bot.fetch_user(user_id)
            avatar_bytes = await user.display_avatar.read()
            return user.display_name, avatar_bytes
        except:
            return f"Usuário {user_id}", None

    @commands.command(name="globo")
    async def globo(self, ctx: commands.Context, palavra1: str, pagina: int = 1):
        if palavra1.lower() != "rank":
            return

        ITEMS_POR_PAGINA = 5
        pagina = max(1, pagina)

        # --------------------
        # Banco async
        # --------------------
        async with AsyncSessionLocal() as session:
            result_total = await session.execute(select(UserMDBs))
            todos_membros = result_total.scalars().all()
            total_usuarios = len(todos_membros)
            total_paginas = max(1, (total_usuarios + ITEMS_POR_PAGINA - 1) // ITEMS_POR_PAGINA)

            if pagina > total_paginas:
                return await ctx.send(f"❌ Página {pagina} não existe. Existem apenas {total_paginas} páginas.")

            result = await session.execute(
                select(UserMDBs)
                .order_by(desc(UserMDBs.MDBs))
                .offset((pagina - 1) * ITEMS_POR_PAGINA)
                .limit(ITEMS_POR_PAGINA)
            )
            top_membros = result.scalars().all()

        if not top_membros:
            return await ctx.send("Ranking vazio.")

        # --------------------
        # Preparar imagem
        # --------------------
        largura, altura = 1000, 700
        background = Image.new("RGBA", (largura, altura), (245, 245, 250, 255))
        draw = ImageDraw.Draw(background)

        try:
            fonte_titulo = ImageFont.truetype("fonts/arial.ttf", 52)
            fonte_subtitulo = ImageFont.truetype("fonts/arial.ttf", 32)
            fonte_itens = ImageFont.truetype("fonts/arial.ttf", 28)
            fonte_saldo = ImageFont.truetype("fonts/arial.ttf", 30)
        except:
            fonte_titulo = ImageFont.load_default()
            fonte_subtitulo = ImageFont.load_default()
            fonte_itens = ImageFont.load_default()
            fonte_saldo = ImageFont.load_default()

        draw.text((largura//2, 40), "🏆 RANKING MDBs", font=fonte_titulo, fill=(40, 40, 40), anchor="mm")
        draw.text((largura//2, 95), f"Página {pagina}/{total_paginas}", font=fonte_subtitulo, fill=(100, 100, 100), anchor="mm")

        start_y = 160
        card_height = 90
        spacing = 20
        card_width = largura - 160
        avatar_size = 70
        cores_posicao = {1: (255, 215, 0), 2: (192, 192, 192), 3: (205, 127, 50), "default": (80, 150, 220)}
        max_mdbs = max([m.MDBs for m in todos_membros]) if todos_membros else 1

        resultados = await asyncio.gather(*(self.obter_usuario_avatar(m.membro_id) for m in top_membros))

        for i, (usuario_db, resultado) in enumerate(zip(top_membros, resultados)):
            nome_real, avatar_bytes = resultado
            posicao_global = (pagina - 1) * ITEMS_POR_PAGINA + i + 1  # CORREÇÃO POSIÇÃO
            y_pos = start_y + i * (card_height + spacing)
            cor = cores_posicao.get(posicao_global, cores_posicao["default"])
            card_bg = Image.new("RGBA", (card_width, card_height), (255, 255, 255, 255))
            shadow = Image.new("RGBA", (card_width+6, card_height+6), (0, 0, 0, 60)).filter(ImageFilter.GaussianBlur(4))
            background.alpha_composite(shadow, (80-3, y_pos-3))
            background.alpha_composite(card_bg, (80, y_pos))

            draw.text((110, y_pos + card_height//2), f"{posicao_global}º", font=fonte_itens, fill=cor, anchor="lm")

            avatar_x = 190
            if avatar_bytes:
                try:
                    avatar = Image.open(BytesIO(avatar_bytes)).resize((avatar_size, avatar_size))
                    mask = Image.new("L", (avatar_size, avatar_size), 0)
                    mask_draw = ImageDraw.Draw(mask)
                    mask_draw.ellipse((0, 0, avatar_size, avatar_size), fill=255)
                    background.paste(avatar, (avatar_x, y_pos + (card_height - avatar_size)//2), mask)
                except:
                    draw.ellipse([avatar_x, y_pos + (card_height - avatar_size)//2,
                                  avatar_x + avatar_size, y_pos + (card_height - avatar_size)//2 + avatar_size], fill=(200,200,200))
            else:
                draw.ellipse([avatar_x, y_pos + (card_height - avatar_size)//2,
                              avatar_x + avatar_size, y_pos + (card_height - avatar_size)//2 + avatar_size], fill=(200,200,200))

            draw.text((avatar_x + avatar_size + 20, y_pos + 20), limpar_unicode(nome_real), font=fonte_itens, fill=(30,30,30))

            saldo_formatado = usuario_db.MDBs
            if saldo_formatado >= 1_000_000:
                saldo_text = f"{saldo_formatado/1_000_000:.1f}M MDBs"
            elif saldo_formatado >= 1_000:
                saldo_text = f"{saldo_formatado/1_000:.1f}K MDBs"
            else:
                saldo_text = f"{saldo_formatado} MDBs"

            draw.text((avatar_x + avatar_size + 20, y_pos + 50), saldo_text, font=fonte_saldo, fill=cor)

            progresso = usuario_db.MDBs / max_mdbs
            bar_width = 200
            bar_height = 10
            bar_x = largura - 110 - bar_width
            bar_y = y_pos + card_height//2 - bar_height//2
            draw.rectangle([bar_x, bar_y, bar_x + bar_width, bar_y + bar_height], fill=(220, 220, 220))
            draw.rectangle([bar_x, bar_y, bar_x + int(bar_width * progresso), bar_y + bar_height], fill=cor)

            brilho = Image.new("RGBA", (card_width, card_height), (255, 255, 255, 30))
            background.alpha_composite(brilho, (80, y_pos))

        draw.line((80, start_y + len(top_membros)*(card_height+spacing),
                   largura-80, start_y + len(top_membros)*(card_height+spacing)), fill=(200,200,200), width=2)
        draw.text((largura//2, start_y + len(top_membros)*(card_height+spacing)+10),
                  "💎 Sistema MDB - Ranking Atualizado", font=fonte_subtitulo, fill=(100,100,100), anchor="mm")

        buffer = BytesIO()
        background.save(buffer, format="PNG")
        buffer.seek(0)

        embed = discord.Embed(title=f"🏆 Ranking MDBs - Página {pagina}", color=0x1ABC9C)
        embed.set_image(url="attachment://rank.png")
        await ctx.send(file=discord.File(buffer, filename="rank.png"), embed=embed)

    async def obter_avatar_usuario(self, user_id):
        try:
            user = await self.bot.fetch_user(user_id)
            avatar_bytes = await user.display_avatar.read()
            return limpar_unicode(user.display_name), avatar_bytes
        except:
            return f"Usuário {user_id}", None

    @commands.command(name="rankmdbs")
    async def rankmdbs(self, ctx: commands.Context, pagina: int = 1):
        ITEMS_POR_PAGINA = 3
        pagina = max(1, pagina)

        largura, altura = 900, 450
        background = Image.new("RGBA", (largura, altura), (0, 0, 0))
        draw = ImageDraw.Draw(background)

        for y in range(altura):
            r = int(10 + 20 * (y/altura))
            g = int(10 + 30 * (y/altura))
            b = int(50 + 100 * (y/altura))
            draw.line([(0, y), (largura, y)], fill=(r, g, b, 255))

        async with AsyncSessionLocal() as session:
            membros_ids = [m.id for m in ctx.guild.members]

            result_total = await session.execute(
                select(UserMDBs).where(UserMDBs.membro_id.in_(membros_ids))
            )
            todos_usuarios = result_total.scalars().all()

            total_usuarios = len(todos_usuarios)
            total_paginas = max(1, (total_usuarios + ITEMS_POR_PAGINA - 1) // ITEMS_POR_PAGINA)

            if (pagina - 1) * ITEMS_POR_PAGINA >= total_usuarios:
                return await ctx.send(f"❌ Página {pagina} não existe. Existem apenas {total_paginas} páginas.")

            result = await session.execute(
                select(UserMDBs)
                .where(UserMDBs.membro_id.in_(membros_ids))  # 🔥 filtro só do servidor
                .order_by(UserMDBs.MDBs.desc())
                .offset((pagina - 1) * ITEMS_POR_PAGINA)
                .limit(ITEMS_POR_PAGINA)
            )
            top_membros = result.scalars().all()

        if not top_membros:
            return await ctx.send("❌ Nenhum membro com MDBs encontrado.")

        ranking = []
        avatar_urls = []
        inicio_rank = (pagina - 1) * ITEMS_POR_PAGINA + 1

        BADGE_USER_ID = 1319876406355955753
        BADGE_SIZE = 40
        BADGE_MARGIN = 5
        try:
            badge_img = Image.open('badges/marcosbadge.png').convert("RGBA").resize((BADGE_SIZE, BADGE_SIZE))
        except:
            badge_img = None

        for i, usuario in enumerate(top_membros, start=inicio_rank):
            membro = ctx.guild.get_member(usuario.membro_id)
            nome_uni = limpar_unicode(membro.display_name) if membro else f"ID: {usuario.membro_id}"
            saldo = usuario.MDBs
            if saldo > 1_000_000_000:
                valor_formatado = f"{saldo/1_000_000_000:.2f}B"
            elif saldo >= 1_000_000:
                valor_formatado = f"{saldo/1_000_000:.2f}M"
            elif saldo >= 1000:
                valor_formatado = f"{saldo/1000:.1f}K"
            else:
                valor_formatado = f"{saldo}"

            ranking.append((i, nome_uni, valor_formatado))
            avatar_urls.append(membro.display_avatar.url if membro else None)

        try:
            fonte_titulo = ImageFont.truetype("fonts/Aquire-BW0ox.otf", 36)
            fonte_ranking = ImageFont.truetype("fonts/Aquire-BW0ox.otf", 24)
            fonte_mdbs = ImageFont.truetype("fonts/ARIAL.TTF", 28)
        except:
            fonte_titulo = ImageFont.load_default(36)
            fonte_ranking = ImageFont.load_default(24)
            fonte_mdbs = ImageFont.load_default(28)

        draw.text((largura//2, 30), "RANK DE MDBs", font=fonte_titulo, fill=(0, 255, 255), anchor="mm")
        draw.text((largura//2, 70), f"Página {pagina}/{total_paginas}", font=fonte_mdbs, fill=(200, 200, 255), anchor="mm")

        y_pos = 120
        avatar_size = 60

        async with aiohttp.ClientSession() as session:
            for idx, ((posicao, nome, mdbs), avatar_url) in enumerate(zip(ranking, avatar_urls)):
                membro_atual = ctx.guild.get_member(top_membros[idx].membro_id)
                color = (100, int(200 + 55*(1 - idx/len(ranking))), 255)
                x1, y1 = 60, int(y_pos-10)
                x2, y2 = largura-60, int(y_pos+avatar_size+10)
                draw.rounded_rectangle([(x1, y1), (x2, y2)], radius=25, fill=(20,30,70,150), outline='#000000')
                draw.text((80, y_pos + avatar_size//2), f"{posicao}º", font=fonte_mdbs, fill='#ffffff', anchor="lm")

                if avatar_url:
                    try:
                        async with session.get(avatar_url) as resp:
                            if resp.status == 200:
                                avatar_data = await resp.read()
                                avatar = Image.open(BytesIO(avatar_data)).resize((avatar_size, avatar_size)).convert("RGBA")
                                mask = Image.new("L", (avatar_size, avatar_size), 0)
                                draw_mask = ImageDraw.Draw(mask)
                                draw_mask.ellipse((0,0,avatar_size,avatar_size), fill=255)
                                background.paste(avatar, (120, y_pos), mask)
                                draw.ellipse([(120, y_pos), (120+avatar_size, y_pos+avatar_size)], outline='#000000', width=3)
                                if membro_atual and membro_atual.id == BADGE_USER_ID and badge_img:
                                    badge_mask = badge_img.split()[3]
                                    background.paste(badge_img, (625+avatar_size-BADGE_SIZE+BADGE_MARGIN,105+avatar_size-BADGE_SIZE+BADGE_MARGIN), badge_mask)
                    except Exception as e:
                        print(f"Erro avatar: {e}")

                nome_truncado = nome[:20]+"..." if len(nome)>20 else nome
                draw.text((190 + avatar_size, y_pos + avatar_size//2), nome_truncado, font=fonte_ranking, fill=(255,255,255), anchor="lm")
                mdbs_width = int(draw.textlength(mdbs, font=fonte_mdbs))
                draw.text((largura-80-mdbs_width, y_pos + avatar_size//2), mdbs, font=fonte_mdbs, fill=(0,255,255), anchor="lm")

                icon_x = largura - 120 - mdbs_width
                icon_y = y_pos + 15
                icon_size = 25
                draw.ellipse([(icon_x, icon_y),(icon_x+icon_size, icon_y+icon_size)], fill=(0,100,255), outline=(0,255,255))
                draw.text((icon_x+icon_size//2, icon_y+icon_size//2), "M", font=fonte_ranking, fill=(255,255,255), anchor="mm")

                y_pos += avatar_size + 30

        for _ in range(3):
            x, y = random.randint(0, largura), random.randint(0, altura)
            radius = random.randint(2,5)
            draw.ellipse([(x-radius, y-radius),(x+radius, y+radius)], fill=(0,255,255))

        buffer = BytesIO()
        background.save(buffer, format="PNG")
        buffer.seek(0)
        await ctx.send(file=discord.File(buffer, filename=f"rank_mdbs_futurista_{pagina}.png"), content=f"Página {pagina}/{total_paginas}")

async def setup(bot):
    await bot.add_cog(RankCog(bot))
