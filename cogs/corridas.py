import discord
from discord.ext import commands
from discord import ui
import random
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from dbdata import AsyncSessionLocal, UserMDBs, VipsUserMdbs, CorridaUsersRandons
from functions import obter_membro

# -------------------------------
# UTILITÁRIOS ASYNC
# -------------------------------

async def get_user(session: AsyncSession, user_id: int) -> UserMDBs | None:
    result = await session.execute(select(UserMDBs).where(UserMDBs.membro_id == user_id))
    return result.scalars().first()

async def is_vip(session: AsyncSession, user_id: int) -> bool:
    result = await session.execute(select(VipsUserMdbs).where(VipsUserMdbs.user_id == user_id))
    return result.scalars().first() is not None

async def get_corrida_stats(session: AsyncSession, user_id: int) -> CorridaUsersRandons:
    result = await session.execute(select(CorridaUsersRandons).where(CorridaUsersRandons.user_id == user_id))
    stats = result.scalars().first()
    if not stats:
        stats = CorridaUsersRandons(user_id=user_id)
        session.add(stats)
        await session.commit()
        await session.refresh(stats)
    return stats

# -------------------------------
# COG DE CORRIDA
# -------------------------------

class CorridaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -------------------------------------
    # COMANDO SOLO
    # -------------------------------------
    @commands.command(name="corridasolo")
    async def corridasoloaposta(self, ctx: commands.Context, quantidade: int):
        try:
            author_id = ctx.author.id
            async with AsyncSessionLocal() as session:
                user = await get_user(session, author_id)
                if not user:
                    return await ctx.send("Você não tem conta na economia!")

                if quantidade <= 0:
                    return await ctx.send("Aposta deve ser maior que zero!")
                if quantidade > user.MDBs:
                    return await ctx.send(f"Saldo insuficiente! Você tem {user.MDBs} MDBs.")
                if quantidade > 50_000_000:
                    return await ctx.send("Não é permitido apostar mais que 50 milhões.")

                vip = await is_vip(session, author_id)
                pesos = [60, 40] if vip else [50, 50]
                multiplicador = 1.25 if vip else 1.10

                resultado = random.choices(["Fugiu", "Pego"], weights=pesos, k=1)[0]
                lucro = int(quantidade * multiplicador)

                imagens_policia = [
                    "https://media.discordapp.net/attachments/1400704538696089623/1403583198558158898/R.png",
                    "https://media.discordapp.net/attachments/1400704538696089623/1403416596847788162/rivals_05.png",
                    "https://media.discordapp.net/attachments/1400704538696089623/1403583455526387712/1241661-need-for-speed-rivals.png",
                    "https://media.discordapp.net/attachments/1400704538696089623/1403583526271582259/OIP.png",
                    "https://media.discordapp.net/attachments/1400704538696089623/1403583703778594899/nfsrveyronssrear.png",
                    "https://media.discordapp.net/attachments/1400704538696089623/1403584473081053184/need-for-speed-rivals-police-car-g4qd0hy1rkj56f9b.png"
                ]

                imagens_corredor = [
                    "https://media.discordapp.net/attachments/1400704538696089623/1403585917372858449/R.png",
                    "https://media.discordapp.net/attachments/1400704538696089623/1403586217215262751/4866597.png",
                    "https://media.discordapp.net/attachments/1400704538696089623/1403422298702217336/image.png",
                    "https://media.discordapp.net/attachments/1400704538696089623/1403586382991065208/my-futuristic-countach-v0-js7tk3722kka1.png",
                    "https://media.discordapp.net/attachments/1400704538696089623/1403586557528768596/5begrnctbx861.png",
                    "https://media.discordapp.net/attachments/1400704538696089623/1403587058345443328/wp1971689.png"
                ]

                if resultado == "Pego":
                    user.MDBs -= quantidade
                    embed = discord.Embed(
                        title="🚨 Você foi pego!",
                        description=f"Perdeu **{quantidade:,} MDBs** | Saldo atual: **{user.MDBs:,} MDBs**",
                        color=discord.Color.red()
                    )
                    embed.set_image(url=random.choice(imagens_policia))
                else:
                    user.MDBs += lucro
                    embed = discord.Embed(
                        title="🏎️💨 Você escapou!",
                        description=f"Ganhou **{lucro:,} MDBs**! | Saldo atual: **{user.MDBs:,} MDBs**",
                        color=discord.Color.green()
                    )
                    embed.set_image(url=random.choice(imagens_corredor))

                embed.set_thumbnail(url=ctx.author.display_avatar.url)
                embed.set_footer(text=f"Requisitado por {ctx.author.display_name}")
                await session.commit()

            await ctx.send(embed=embed)

        except Exception as e:
            print(f"[ERROR] CorridaSolo: {e}")
            await ctx.send("Ocorreu um erro ao processar a corrida solo.")

    # -------------------------------------
    # COMANDO MULTIPLAYER
    # -------------------------------------
    @commands.command(name="corrida")
    async def corrida_gambling(self, ctx: commands.Context, quantidade: int):
        if quantidade <= 0:
            return await ctx.send("Aposta deve ser maior que zero!")

        author = ctx.author
        async with AsyncSessionLocal() as session:
            user = await get_user(session, author.id)
            if not user or user.MDBs < quantidade:
                return await ctx.send(f"Saldo insuficiente para apostar {quantidade:,} MDBs!")

        if quantidade <= 0:
            return await ctx.reply("A aposta deve ser maior que zero!", ephemeral=True)

        corrida_embed = discord.Embed(
            title="🚗 Corrida Ilegal 🚓",
            description="Vença seu inimigo, e não deixe a polícia te pegar!",
            color=discord.Color.dark_blue(),
            timestamp=discord.utils.utcnow()
        )

        imagens_sorteadas_random = [
            "https://media.discordapp.net/attachments/1400704538696089623/1403406630925631639/R.png",
            "https://media.discordapp.net/attachments/1400704538696089623/1403587493944623288/R.png?ex=68981837&is=6896c6b7&hm=b398870bc54d8ee87de7acbe3b5968f4646da735d007f84a5d0e8d596befd4f4&=&format=webp&quality=lossless&width=792&height=445",
            "https://media.discordapp.net/attachments/1400704538696089623/1403587798795026472/OIP.png?ex=68981880&is=6896c700&hm=3f8f38805905f53886a3ce0ffdf7f0633a42f28c263f0b610e8c3738e45d90b7&=&format=webp&quality=lossless&width=1318&height=742",
            "https://media.discordapp.net/attachments/1400704538696089623/1403587806844162158/R.png?ex=68981882&is=6896c702&hm=de1aab552646e1ccaba3603d6210551d5fff2fa9827c60a38031374eeb9b561f&=&format=webp&quality=lossless&width=1318&height=742",
            "https://media.discordapp.net/attachments/1400704538696089623/1403588162927984660/R.png?ex=689818d7&is=6896c757&hm=a46bf3c4260aea198ca63ea7da8126dd1a506bf8aa855f7116b67a12d97e5452&=&format=webp&quality=lossless&width=1212&height=742"
        ]

        imagem_final_sssssssssss = random.choice(imagens_sorteadas_random)

        corrida_embed.set_image(url=imagem_final_sssssssssss)
        corrida_embed.set_thumbnail(url=author.display_avatar.url)
        corrida_embed.set_footer(text=f"Corrida iniciada por {author.name}", icon_url=author.display_avatar.url)

        view = CorridaView(author, quantidade)
        message = await ctx.send(embed=corrida_embed, view=view)
        view.message = message

# -------------------------------
# VIEW DA CORRIDA MULTIPLAYER
# -------------------------------
class CorridaView(ui.View):
    def __init__(self, author: discord.Member, quantidade: int):
        super().__init__(timeout=120)
        self.author = author
        self.quantidade = quantidade
        self.adversario: discord.Member | None = None
        self.message: discord.Message | None = None

    async def on_timeout(self):
        if self.message:
            await self.message.edit(view=None, content="⏰ Tempo esgotado! Ninguém entrou na corrida.")

    @ui.button(label="Entrar na corrida", style=discord.ButtonStyle.grey)
    async def entrar_na_corrida(self, interaction: discord.Interaction, button: ui.Button):
        if interaction.user.id == self.author.id:
            return await interaction.response.send_message("Você não pode correr contra si mesmo!", ephemeral=True)

        async with AsyncSessionLocal() as session:
            adversario_db = await get_user(session, interaction.user.id)
            if not adversario_db or adversario_db.MDBs < self.quantidade:
                return await interaction.response.send_message(
                    f"Saldo insuficiente para apostar {self.quantidade:,} MDBs!",
                    ephemeral=True
                )

        self.adversario = interaction.user
        self.clear_items()

        iniciar_button = ui.Button(label="Iniciar corrida", style=discord.ButtonStyle.blurple)
        iniciar_button.callback = self.iniciar_corrida_callback
        self.add_item(iniciar_button)

        embed = self.message.embeds[0]
        embed.description = (
            f"{self.author.mention} 🏎 | Aposta: {self.quantidade:,} MDBs\n"
            f"{interaction.user.mention} 🚗 | Aposta: {self.quantidade:,} MDBs"
        )
        await interaction.response.edit_message(embed=embed, view=self)

    async def iniciar_corrida_callback(self, interaction: discord.Interaction):
        if not self.adversario:
            return await interaction.response.send_message("Nenhum adversário entrou na corrida!", ephemeral=True)
        if interaction.user.id not in [self.author.id, self.adversario.id]:
            return await interaction.response.send_message("Apenas os participantes podem iniciar a corrida!", ephemeral=True)

        ganhador, pegou_policia = (None, False)
        if random.random() < 0.6:
            ganhador = random.choice([self.author, self.adversario])
        else:
            pegou_policia = True

        async with AsyncSessionLocal() as session:
            autor_db = await get_user(session, self.author.id)
            adversario_db = await get_user(session, self.adversario.id)

            if pegou_policia:
                perda = int(self.quantidade * 0.5)
                autor_db.MDBs = max(0, autor_db.MDBs - perda)
                adversario_db.MDBs = max(0, adversario_db.MDBs - perda)
                desc = f"🚓 {self.author.mention} e {self.adversario.mention} foram pegos! Perderam **{perda:,} MDBs** cada."
                cor = discord.Color.red()
            else:
                perdedor = self.adversario if ganhador == self.author else self.author
                ganhador_db = autor_db if ganhador == self.author else adversario_db
                perdedor_db = adversario_db if ganhador == self.author else autor_db

                premio = int(self.quantidade * 2)
                ganhador_db.MDBs += premio
                perdedor_db.MDBs = max(0, perdedor_db.MDBs - self.quantidade)

                stats = await get_corrida_stats(session, ganhador.id)
                stats.corridas_ganhas1 += 1

                desc = f"🏆 {ganhador.mention} venceu! Ganhou **{premio:,} MDBs**. {perdedor.mention} perdeu **{self.quantidade:,} MDBs**."
                cor = discord.Color.green()

            await session.commit()

        embed = discord.Embed(title="Resultado da Corrida", description=desc, color=cor)
        embed.set_footer(text=f"Corrida iniciada por {self.author.display_name}")
        self.clear_items()
        await interaction.response.edit_message(embed=embed, view=self)

# -------------------------------
# SETUP DO COG
# -------------------------------
async def setup(bot):
    await bot.add_cog(CorridaCog(bot))
