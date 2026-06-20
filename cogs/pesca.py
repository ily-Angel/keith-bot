import discord
from discord.ext import commands
import random
import asyncio
from datetime import datetime
from sqlalchemy.future import select
from dbdata import AsyncSessionLocal, BolsaPeixes, UserMDBs  # ajuste conforme seu DB

class PescaCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # -----------------------
    # COMANDO DE PESCA
    # -----------------------
    @commands.command(name="pescar")
    async def pescar(self, ctx: commands.Context):
        author = ctx.author

        embed_inicio = discord.Embed(
            title="🎣 Preparado para pescar?",
            description="Clique no botão abaixo para começar a pescaria!",
            color=discord.Color.blue(),
            timestamp=datetime.utcnow()
        )
        embed_inicio.add_field(name="⏰ Tempo de Espera", value="Cada pescaria leva 10 segundos", inline=False)
        embed_inicio.set_footer(text=f"Requisitado por {author.name}", icon_url=author.avatar.url)
        embed_inicio.set_thumbnail(url="https://media.discordapp.net/attachments/1400704538696089623/1407406558005952665/pesca-embarcacion.png")

        class PescaView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=180)
                self.pescando = False

            @discord.ui.button(label="🎣 Pescar", style=discord.ButtonStyle.primary, emoji="🎣")
            async def pescar_button(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user.id != ctx.author.id:
                    return await interaction.response.send_message("❌ Apenas quem iniciou a pesca pode clicar!", ephemeral=True)
                if self.pescando:
                    return await interaction.response.send_message("⏳ Você já está pescando!", ephemeral=True)

                self.pescando = True
                button.disabled = True
                button.label = "⏳ Pescando..."
                button.style = discord.ButtonStyle.secondary
                await interaction.response.edit_message(view=self)

                # -----------------------
                # Escolha do peixe
                # -----------------------
                peixes = [
                    "Robalo", "Garoupa", "Cherne", "Dourado", "Pescada",
                    "Tainha", "Sardinha", "Atum", "Cloba", "Badejo",
                    "Pintado", "Pacu", "Tambaqui", "Pirarucu", "Tilapia",
                    "Matrinxa", "Jau", "Cascudo", "Corvina"
                ]
                pesos = [2.5,2,6.5,7.5,9.5,12,10,2,7,8,9,3,14,2.5,1,12,8,1,12]
                peixe = random.choices(peixes, weights=pesos, k=1)[0]

                quantidades = {
                    "Robalo": random.randint(1,3), "Garoupa": random.randint(1,3),
                    "Cherne": random.randint(2,6), "Dourado": random.randint(4,18),
                    "Pescada": random.randint(4,18), "Tainha": random.randint(4,25),
                    "Sardinha": random.randint(4,25), "Atum": random.randint(1,3),
                    "Cloba": random.randint(2,6), "Badejo": random.randint(4,8),
                    "Pintado": random.randint(4,8), "Pacu": random.randint(6,18),
                    "Tambaqui": random.randint(6,18), "Pirarucu": random.randint(1,3),
                    "Tilapia": random.randint(12,24), "Matrinxa": random.randint(4,8),
                    "Jau": random.randint(1,3), "Cascudo": random.randint(12,24),
                    "Corvina": random.randint(12,24)
                }
                qtd = quantidades[peixe]
                coluna = peixe.lower()

                # -----------------------
                # Simula espera de pesca
                # -----------------------
                loading = await interaction.followup.send("🎣 **Iniciando pescaria...**", wait=True)
                for i in range(10, 0, -1):
                    await asyncio.sleep(1)
                    await loading.edit(content=f"🎣 **Pescando...** `{i}s restantes`")

                # -----------------------
                # Banco async
                # -----------------------
                async with AsyncSessionLocal() as session:
                    result = await session.execute(select(BolsaPeixes).filter_by(user_id=interaction.user.id))
                    userdb = result.scalars().first()
                    if not userdb:
                        userdb = BolsaPeixes(user_id=interaction.user.id)
                        session.add(userdb)
                        await session.flush()
                    atual = getattr(userdb, coluna, 0)
                    setattr(userdb, coluna, atual + qtd)
                    await session.commit()

                # -----------------------
                # Embed final
                # -----------------------
                embed = discord.Embed(
                    title=f"✅ Pesca concluída! 🐟",
                    description=f"{interaction.user.mention} pescou {qtd} {peixe}(s).",
                    color=discord.Color.green(),
                    timestamp=datetime.utcnow()
                )
                embed.add_field(name="📦 Peixe", value=peixe, inline=True)
                embed.add_field(name="🔢 Quantidade", value=str(qtd), inline=True)
                embed.add_field(name="💼 Total em estoque", value=str(atual + qtd), inline=True)
                embed.set_footer(text=f"Pesca realizada por {interaction.user.name}", icon_url=interaction.user.avatar.url)

                await loading.delete()
                await interaction.followup.send(embed=embed)

                self.pescando = False
                button.disabled = False
                button.label = "🎣 Pescar Novamente"
                button.style = discord.ButtonStyle.primary
                try:
                    await interaction.edit_original_response(view=self)
                except:
                    pass

        await ctx.send(embed=embed_inicio, view=PescaView())

    # -----------------------
    # COMANDO INVENTÁRIO E VENDA
    # -----------------------
    @commands.command(name="bolsadepeixes")
    async def bolsadepeixes(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🧺 Sua bolsa de peixes",
            description="Escolha um inventário ou venda seus peixes:",
            color=discord.Color.teal(),
            timestamp=datetime.utcnow()
        )
        embed.set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url)

        class InventoryView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=180)

            # -----------------------
            # ÁGUA DOCE
            # -----------------------
            @discord.ui.button(label="💧 Água Doce", style=discord.ButtonStyle.primary)
            async def agua_doce(self, interaction: discord.Interaction, button: discord.ui.Button):
                async with AsyncSessionLocal() as session:
                    result = await session.execute(select(BolsaPeixes).filter_by(user_id=interaction.user.id))
                    userdb = result.scalars().first()
                if not userdb:
                    return await interaction.response.send_message("❌ Você não possui peixes.", ephemeral=True)
                embed_bolsa = discord.Embed(
                    title="🛶 Água Doce",
                    description=(
                        f"Pintado 🐠: {userdb.pintado}\n"
                        f"Pacu 🐟: {userdb.pacu}\n"
                        f"Tambaqui 🐋: {userdb.tambaqui}\n"
                        f"Pirarucu 🐙: {userdb.pirarucu}\n"
                        f"Tilapia 🦈: {userdb.tilapia}\n"
                        f"Matrinxa 🐟: {userdb.matrinxa}\n"
                        f"Jau 🐡: {userdb.jau}\n"
                        f"Cascudo 🐬: {userdb.cascudo}\n"
                        f"Corvina 🦐: {userdb.corvina}"
                    ),
                    color=discord.Color.blue(),
                    timestamp=datetime.utcnow()
                )
                embed_bolsa.set_footer(text=f"Solicitado por {interaction.user.name}", icon_url=interaction.user.avatar.url)
                await interaction.response.send_message(embed=embed_bolsa, ephemeral=True)

            # -----------------------
            # ÁGUA SALGADA
            # -----------------------
            @discord.ui.button(label="🌊 Água Salgada", style=discord.ButtonStyle.secondary)
            async def agua_salgada(self, interaction: discord.Interaction, button: discord.ui.Button):
                async with AsyncSessionLocal() as session:
                    result = await session.execute(select(BolsaPeixes).filter_by(user_id=interaction.user.id))
                    userdb = result.scalars().first()
                if not userdb:
                    return await interaction.response.send_message("❌ Você não possui peixes.", ephemeral=True)
                embed_bolsa = discord.Embed(
                    title="⛵ Água Salgada",
                    description=(
                        f"Robalo 🐠: {userdb.robalo}\n"
                        f"Garoupa 🐟: {userdb.garoupa}\n"
                        f"Cherne 🐬: {userdb.cherne}\n"
                        f"Dourado 🐤: {userdb.dourado}\n"
                        f"Pescada 🐳: {userdb.pescada}\n"
                        f"Tainha 🐋: {userdb.tainha}\n"
                        f"Sardinha 🦈: {userdb.sardinha}\n"
                        f"Atum 🐊: {userdb.atum}\n"
                        f"Cloba 🦐: {userdb.cloba}\n"
                        f"Badejo 🦑: {userdb.badejo}"
                    ),
                    color=discord.Color.dark_blue(),
                    timestamp=datetime.utcnow()
                )
                embed_bolsa.set_footer(text=f"Solicitado por {interaction.user.name}", icon_url=interaction.user.avatar.url)
                await interaction.response.send_message(embed=embed_bolsa, ephemeral=True)

            # -----------------------
            # VENDER PEIXES
            # -----------------------
            @discord.ui.button(label="💰 Vender Peixes", style=discord.ButtonStyle.success)
            async def vender_peixes(self, interaction: discord.Interaction, button: discord.ui.Button):
                class VendaModal(discord.ui.Modal):
                    def __init__(self):
                        super().__init__(title="💰 Vender Peixes")
                        self.peixe_input = discord.ui.TextInput(label="Nome do peixe", placeholder="Ex: Robalo", max_length=20)
                        self.quant_input = discord.ui.TextInput(label="Quantidade", placeholder="Ex: 10", max_length=5)
                        self.add_item(self.peixe_input)
                        self.add_item(self.quant_input)

                    async def on_submit(self, interaction_modal: discord.Interaction):
                        peixe_nome = self.peixe_input.value.lower()
                        try:
                            quantidade = int(self.quant_input.value)
                        except ValueError:
                            return await interaction_modal.response.send_message("❌ Quantidade inválida.", ephemeral=True)

                        async with AsyncSessionLocal() as session:
                            result = await session.execute(select(BolsaPeixes).filter_by(user_id=interaction_modal.user.id))
                            userdb = result.scalars().first()
                            if not userdb or getattr(userdb, peixe_nome, 0) < quantidade:
                                return await interaction_modal.response.send_message("❌ Você não possui peixes suficientes.", ephemeral=True)
                            atual = getattr(userdb, peixe_nome)
                            setattr(userdb, peixe_nome, atual - quantidade)
                            await session.commit()

                            # Adiciona MDBs
                            preco = quantidade * 10
                            result2 = await session.execute(select(UserMDBs).filter_by(membro_id=interaction_modal.user.id))
                            user_mdbs = result2.scalars().first()
                            if not user_mdbs:
                                user_mdbs = UserMDBs(membro_id=interaction_modal.user.id, MDBs=0)
                                session.add(user_mdbs)
                                await session.flush()
                            user_mdbs.MDBs += preco
                            await session.commit()

                        await interaction_modal.response.send_message(f"✅ Vendido {quantidade} {peixe_nome}(s) por {preco} MDBs!", ephemeral=True)

                await interaction.response.send_modal(VendaModal())

        await ctx.send(embed=embed, view=InventoryView())


# ------------------------
# SETUP
# ------------------------
async def setup(bot):
    await bot.add_cog(PescaCog(bot))
