import discord
from discord.ext import commands, tasks
from dbdata import AsyncSessionLocal, UserMDBs, VipsUserMdbs, DailyCooldown, Poupanca, RoletaDiariaCooldown, StatsUserData, BolsaPeixes, OptionsCommandsStyle, PremiumDataSuper
from sqlalchemy.future import select
from datetime import datetime
import random
from sqlalchemy import update
from datetime import datetime
import asyncio
from discord import app_commands
from functions import get_user, get_plataforma
import math

async def pegar_usuario(user_id:int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(UserMDBs).filter_by(membro_id=user_id))
        membro_db = result.scalars().first()
        if not membro_db:
            membro_db = UserMDBs(membro_id=user_id, MDBs=0)
            session.add(membro_db)
            await session.commit()
        return membro_db
    
async def add_saldo(user_id:int, ganho:int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(UserMDBs).filter_by(membro_id=user_id))
        userdb = result.scalars().first()
        if not userdb:
            userdb = UserMDBs(user_id=user_id, MDBs=ganho)
            session.add(userdb)
        userdb.MDBs += ganho
        await session.commit()
        
async def retirar_saldo(user_id:int, perca:int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(UserMDBs).filter_by(membro_id=user_id))
        userdb = result.scalars().first()
        if not userdb:
            userdb = UserMDBs(user_id=user_id)
            session.add(userdb)
        userdb.MDBs -= perca
        await session.commit()
    
def interpretar_valor(valor_str: str) -> int:
    valor_str = valor_str.lower().replace(",", ".").strip()
    multiplicadores = {
        "k": 1_000,
        "m": 1_000_000,
        "b": 1_000_000_000
    }

    if valor_str[-1] in multiplicadores:
        try:
            numero = float(valor_str[:-1])
            return int(numero * multiplicadores[valor_str[-1]])
        except ValueError:
            raise ValueError("Valor de aposta inválido.")
    else:
        try:
            return int(float(valor_str))
        except ValueError:
            raise ValueError("Valor de aposta inválido.")
        
ROLL_IMAGE_CDN = "https://cdn.discordapp.com/attachments/1383937512933822586/1391543791219118260/images_4.jpg?"

def format_large_number_for_display(number: int) -> str:
    abs_number = abs(number)
    sign = '-' if number < 0 else ''
    suffixes = [
        (1_000_000_000_000_000_000, "QT"),
        (1_000_000_000_000_000, "Q"),
        (1_000_000_000_000, "T"),
        (1_000_000_000, "B"),
        (1_000_000, "M"),
        (1_000, "K"),
    ]
    for divisor, suffix in suffixes:
        if abs_number >= divisor:
            value = abs_number / divisor
            return f"{sign}{value:.1f}{suffix}"
    return f"{sign}{abs_number}"
        
def gerar_nova_bolinha():
    cores = ["vermelho", "preto", "verde"]
    pesos = [0.475, 0.475, 0.05]
    return random.choices(cores, weights=pesos, k=1)[0]

def gerar_linha_emojis(linha):
    emojis = {"vermelho": "🔴", "preto": "⚫", "verde": "🟢"}
    meio = len(linha) // 2
    display = ""
    for i, cor in enumerate(linha):
        if i == meio:
            display += f"│{emojis[cor]}│"
        else:
            display += emojis[cor]
        if i < len(linha) - 1:
            display += " "
    return display

async def get_saldo(user_id: int) -> int:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserMDBs).filter_by(membro_id=user_id)
        )
        membro = result.scalars().first()
        if not membro:
            membro = UserMDBs(membro_id=user_id, MDBs=0)
            session.add(membro)
            await session.commit()
        return membro.MDBs

async def set_saldo(user_id: int, novo_saldo: int):
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserMDBs).filter_by(membro_id=user_id)
        )
        membro = result.scalars().first()
        if not membro:
            membro = UserMDBs(membro_id=user_id, MDBs=novo_saldo)
            session.add(membro)
        else:
            membro.MDBs = novo_saldo
        await session.commit()

EMOJIS_NIQUEL = ["💵", "💎", "🪙", "💳", "💶", "💸"]

def random_emojis():
    return [random.choice(EMOJIS_NIQUEL) for _ in range(3)]

def draw_card() -> int:
    deck = [2,3,4,5,6,7,8,9,10,10,10,10,1]
    return random.choice(deck)

from sqlalchemy import update, literal
import discord
from discord.ext import commands
import math

class BlackjackView(discord.ui.View):
    def __init__(self, ctx: commands.Context, player_hand: list, marcos_hand: list, aposta: int):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.player_hand = player_hand
        self.marcos_hand = marcos_hand
        self.aposta = aposta
        self.game_over = False
        self.message: discord.Message | None = None
        self.dealer_finalized = False

    @staticmethod
    def calculate_total(hand: list) -> int:
        total = sum(hand)
        aces = hand.count(1)
        while aces > 0 and total + 10 <= 21:
            total += 10
            aces -= 1
        return total

    def create_embed(self, title: str, description: str, color: discord.Color) -> discord.Embed:
        embed = discord.Embed(title=title, description=description, color=color)
        embed.add_field(
            name="🎯 Sua Mão",
            value=f"{' + '.join(map(str, self.player_hand))} = **{self.calculate_total(self.player_hand)}**",
            inline=True
        )

        if self.game_over:
            embed.add_field(
                name="🤖 Mão do Marcos",
                value=f"{' + '.join(map(str, self.marcos_hand))} = **{self.calculate_total(self.marcos_hand)}**",
                inline=True
            )
        else:
            embed.add_field(
                name="🤖 Mão do Marcos",
                value=f"{self.marcos_hand[0]} + ?",
                inline=True
            )

        embed.add_field(name="💰 Aposta", value=f"{self.aposta} MDBs", inline=True)
        embed.set_footer(text=f"Jogador: {self.ctx.author.display_name}")
        embed.set_thumbnail(
            url="https://media.discordapp.net/attachments/1410462821396774924/1411434356123238481/Conheca-a-historia-do-blackjack-online.png"
        )
        return embed

    async def finalize_dealer(self):
        """Dealer compra até 17 ou mais (soft 17 incluso)."""
        if self.dealer_finalized:
            return
        self.dealer_finalized = True
        while self.calculate_total(self.marcos_hand) < 17:
            self.marcos_hand.append(draw_card())

    async def conclude(self, interaction: discord.Interaction, result: str, multiplier: float = 0):
        self.game_over = True
        self.clear_items()
        await self.finalize_dealer()

        player_total = self.calculate_total(self.player_hand)
        marcos_total = self.calculate_total(self.marcos_hand)

        # ------------- ATUALIZAÇÕES SQL CORRIGIDAS (literal()) -------------
        if result == "win":
            winnings = int(math.floor(self.aposta * multiplier))

            async with AsyncSessionLocal() as session:
                # devolve aposta + lucro
                await session.execute(
                    update(UserMDBs)
                    .where(UserMDBs.membro_id == self.ctx.author.id)
                    .values(MDBs=UserMDBs.MDBs + literal(self.aposta + winnings))
                )

                await session.execute(
                    update(StatsUserData)
                    .where(StatsUserData.membro_id == self.ctx.author.id)
                    .values(ganho_total=StatsUserData.ganho_total + literal(winnings))
                )

                await session.commit()

            color = discord.Color.green()
            title = "🎉 Você Ganhou!"
            description = f"Você ganhou **{winnings} MDBs**. Total: {player_total} vs {marcos_total}."

        elif result == "tie":
            async with AsyncSessionLocal() as session:
                await session.execute(
                    update(UserMDBs)
                    .where(UserMDBs.membro_id == self.ctx.author.id)
                    .values(MDBs=UserMDBs.MDBs + literal(self.aposta))
                )
                await session.commit()

            color = discord.Color.blue()
            title = "🤝 Empate!"
            description = f"Empate. Sua aposta de {self.aposta} MDBs foi devolvida."

        else:  # lose
            async with AsyncSessionLocal() as session:
                await session.execute(
                    update(StatsUserData)
                    .where(StatsUserData.membro_id == self.ctx.author.id)
                    .values(perda_total=StatsUserData.perda_total + literal(self.aposta))
                )
                await session.commit()

            color = discord.Color.red()
            title = "💥 Você Perdeu!"
            description = f"Você perdeu {self.aposta} MDBs. Total: {player_total} vs {marcos_total}."

        embed = self.create_embed(title, description, color)

        if interaction.response.is_done():
            await interaction.message.edit(embed=embed, view=self)
        else:
            await interaction.response.edit_message(embed=embed, view=self)

    async def check_and_end(self, interaction: discord.Interaction):
        await self.finalize_dealer()

        player_total = self.calculate_total(self.player_hand)
        marcos_total = self.calculate_total(self.marcos_hand)

        if player_total > 21:
            await self.conclude(interaction, "lose")
        elif marcos_total > 21:
            await self.conclude(interaction, "win", multiplier=1.0)
        elif player_total > marcos_total:
            await self.conclude(interaction, "win", multiplier=1.0)
        elif player_total < marcos_total:
            await self.conclude(interaction, "lose")
        else:
            await self.conclude(interaction, "tie")

    # ---------------- BOTÕES ----------------

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Apenas o jogador que iniciou pode usar estes botões.", ephemeral=True)
            return

        self.player_hand.append(draw_card())
        player_total = self.calculate_total(self.player_hand)

        if player_total > 21:
            self.game_over = True
            self.clear_items()

            embed = self.create_embed("💥 Estourou!", f"Sua mão: {player_total}. Você perdeu.", discord.Color.red())

            await interaction.response.edit_message(embed=embed, view=self)

            # registra perda
            async with AsyncSessionLocal() as session:
                await session.execute(
                    update(StatsUserData)
                    .where(StatsUserData.membro_id == self.ctx.author.id)
                    .values(perda_total=StatsUserData.perda_total + literal(self.aposta))
                )
                await session.commit()
            return

        embed = self.create_embed("🃏 Carta puxada", "Você puxou uma carta.", discord.Color.dark_gold())
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.secondary)
    async def stand(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.ctx.author.id:
            await interaction.response.send_message("Apenas o jogador que iniciou pode usar estes botões.", ephemeral=True)
            return

        await self.check_and_end(interaction)

    async def on_timeout(self):
        if self.game_over:
            return

        self.game_over = True
        self.clear_items()

        async with AsyncSessionLocal() as session:
            await session.execute(
                update(UserMDBs)
                .where(UserMDBs.membro_id == self.ctx.author.id)
                .values(MDBs=UserMDBs.MDBs + literal(self.aposta))
            )
            await session.commit()

        if self.message:
            embed = self.create_embed("⌛ Jogo Expirado", f"Tempo esgotado. Sua aposta ({self.aposta} MDBs) foi devolvida.", discord.Color.dark_gray())
            try:
                await self.message.edit(embed=embed, view=self)
            except Exception:
                pass

class ButtonsForRandomCards(discord.ui.View):
    def __init__(self, ctx_author_id, card1, card2, card3, card4, quantidade):
        super().__init__(timeout=120)
        self.ctx_author_id = ctx_author_id
        self.card1 = card1
        self.card2 = card2
        self.card3 = card3
        self.card4 = card4
        self.quantidade = quantidade
        self.button1 = discord.ui.Button(label=f"{self.card1}", style=discord.ButtonStyle.blurple, custom_id="card1_btn")
        self.button2 = discord.ui.Button(label=f"{self.card2}", style=discord.ButtonStyle.blurple, custom_id="card2_btn")
        self.button3 = discord.ui.Button(label=f"{self.card3}", style=discord.ButtonStyle.blurple, custom_id="card3_btn")
        self.button4 = discord.ui.Button(label=f"{self.card4}", style=discord.ButtonStyle.blurple, custom_id="card4_btn")
        
        self.button1.callback = self.callback_button1
        self.button2.callback = self.callback_button2
        self.button3.callback = self.callback_button3
        self.button4.callback = self.callback_button4
        
        self.add_item(self.button1)
        self.add_item(self.button2)
        self.add_item(self.button3)
        self.add_item(self.button4)
        
        self.correct_card = random.choice([self.card1, self.card2, self.card3, self.card4])
        
    async def construct_embed(self, card_true, balance, user, quantity):
        
        embed = discord.Embed(
            title="✅ Você acertou a carta!",
            color=discord.Color.dark_blue(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.set_footer(text=f"{user.name}", icon_url=user.avatar.url)
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1410462821396774924/1444002800731291791/b400b6a94a1b451e831a8cd693ba0ef0.png?ex=692b1fe7&is=6929ce67&hm=03d2860904b559e5ceb4d44d7b4473f7b6a1331f7f070082a3e51eed4a62925a&=&format=webp&quality=lossless&width=760&height=760")
        embed.add_field(name="🃏 Carta certa:", value=f"{card_true}", inline=True)
        embed.add_field(name="💎 Ganho:", value=f"{quantity}", inline=True)
        embed.add_field(name="💰 Novo Saldo:", value=f"{balance:,}", inline=True)
        
        return embed
    
    async def construct_embed_false(self, card_true, balance, user, quantity):
        
        embed = discord.Embed(
            title="❌ Você errou a carta!",
            color=discord.Color.dark_blue(),
            timestamp=discord.utils.utcnow()
        )
        
        embed.set_footer(text=f"{user.name}", icon_url=user.avatar.url)
        embed.set_thumbnail(url="https://media.discordapp.net/attachments/1410462821396774924/1444005886245998784/dc11f0727e2a9a0ffd590c9f4f73326d.png?ex=692b22c7&is=6929d147&hm=f32f1ac3671971c7ae31a26e605415e5be8ad5408e207b6dfbdab08a3cfa704b&=&format=webp&quality=lossless&width=760&height=760")
        embed.add_field(name="🎴 Carta certa:", value=f"{card_true}", inline=True)
        embed.add_field(name="📉 Perda:", value=f"{quantity}", inline=True)
        embed.add_field(name="💸 Novo Saldo:", value=f"{balance:,}", inline=True)
        
        return embed
        
    async def callback_button1(self, interaction:discord.Interaction):
        
        if self.ctx_author_id != interaction.user.id:
            return await interaction.response.send_message("🚫 Somente o autor do comando pode clicar nesses botões!", ephemeral=True)
        
        if self.card1 == self.correct_card:
            
            await add_saldo(user_id=interaction.user.id, ganho=self.quantidade)
            user_ = await get_user(interaction.user.id)
            embed = await self.construct_embed(self.correct_card, user_.MDBs, interaction.user, self.quantidade)
            
            await interaction.response.send_message(embed=embed)
            
        else:
            
            await retirar_saldo(interaction.user.id, self.quantidade)
            user_ = await get_user(interaction.user.id)
            embed = await self.construct_embed_false(self.correct_card, user_.MDBs, interaction.user, self.quantidade)
            
            await interaction.response.send_message(embed=embed)
            
    async def callback_button2(self, interaction:discord.Interaction):
        
        if self.ctx_author_id != interaction.user.id:
            return await interaction.response.send_message("🚫 Somente o autor do comando pode clicar nesses botões!", ephemeral=True)
        
        if self.card2 == self.correct_card:
            
            await add_saldo(user_id=interaction.user.id, ganho=self.quantidade)
            user_ = await get_user(interaction.user.id)
            embed = await self.construct_embed(self.correct_card, user_.MDBs, interaction.user, self.quantidade)
            
            await interaction.response.send_message(embed=embed)
            
        else:
            
            await retirar_saldo(interaction.user.id, self.quantidade)
            user_ = await get_user(interaction.user.id)
            embed = await self.construct_embed_false(self.correct_card, user_.MDBs, interaction.user, self.quantidade)
            
            await interaction.response.send_message(embed=embed)

    async def callback_button3(self, interaction:discord.Interaction):
        
        if self.ctx_author_id != interaction.user.id:
            return await interaction.response.send_message("🚫 Somente o autor do comando pode clicar nesses botões!", ephemeral=True)
        
        if self.card3 == self.correct_card:
            
            await add_saldo(user_id=interaction.user.id, ganho=self.quantidade)
            user_ = await get_user(interaction.user.id)
            embed = await self.construct_embed(self.correct_card, user_.MDBs, interaction.user, self.quantidade)
            
            await interaction.response.send_message(embed=embed)
            
        else:
            
            await retirar_saldo(interaction.user.id, self.quantidade)
            user_ = await get_user(interaction.user.id)
            embed = await self.construct_embed_false(self.correct_card, user_.MDBs, interaction.user, self.quantidade)
            
            await interaction.response.send_message(embed=embed)
            
    async def callback_button4(self, interaction:discord.Interaction):
        
        if self.ctx_author_id != interaction.user.id:
            return await interaction.response.send_message("🚫 Somente o autor do comando pode clicar nesses botões!", ephemeral=True)
        
        if self.card4 == self.correct_card:
            
            await add_saldo(user_id=interaction.user.id, ganho=self.quantidade)
            user_ = await get_user(interaction.user.id)
            embed = await self.construct_embed(self.correct_card, user_.MDBs, interaction.user, self.quantidade)
            
            await interaction.response.send_message(embed=embed)
            
        else:
            
            await retirar_saldo(interaction.user.id, self.quantidade)
            user_ = await get_user(interaction.user.id)
            embed = await self.construct_embed_false(self.correct_card, user_.MDBs, interaction.user, self.quantidade)
            
            await interaction.response.send_message(embed=embed)

class ButtonForCacaNiquel(discord.ui.View):
    def __init__(self, ctx_author_id, quantidade: int, mensagem: discord.Message):
        super().__init__(timeout=120)
        self.ctx_author_id = ctx_author_id
        self.quantidade = quantidade
        self.message = mensagem

    @discord.ui.button(label="🎰 Girar Caça-Níquel", style=discord.ButtonStyle.green)
    async def button_niquel(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != self.ctx_author_id:
            return await interaction.response.send_message("🚫 Essa aposta não é sua!", ephemeral=True)

        # Animação da roleta
        embed = discord.Embed(
            title="🎰 Caça-Níquel",
            description=f"{interaction.user.mention} puxou a alavanca...",
            color=discord.Color.blurple()
        )
        embed.set_footer(text=f'{interaction.user.name}', icon_url=interaction.user.avatar.url)
        await interaction.response.edit_message(embed=embed, view=None)

        for _ in range(6):  # faz a roleta girar algumas vezes
            slots = random_emojis()
            embed.description = f"{interaction.user.mention} girando a roleta...\n\n**{' '.join(slots)}**\n\nDica: Já experimentou o <perfil?"
            await self.message.edit(embed=embed)
            await asyncio.sleep(0.5)

        # Resultado final
        final_slots = random_emojis()
        resultado = f"{final_slots[0]} {final_slots[1]} {final_slots[2]}"

        if len(set(final_slots)) == 1:  # jackpot (3 iguais)
            
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(UserMDBs).filter_by(membro_id=interaction.user.id))
                userdb = result.scalars().first()
                if not userdb:
                    userdb = UserMDBs(membro_id=interaction.user.id)
                    session.add(userdb)
                userdb.MDBs += self.quantidade*2
                await session.commit()
            
            ganho = self.quantidade * 2
            embed = discord.Embed(
                title="🎉 JACKPOT!",
                description=f"Você conseguiu **3 emojis iguais**!\n💰 Ganhou **{ganho} MDBs**!",
                color=discord.Color.green(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_thumbnail(url='https://media.discordapp.net/attachments/1415295712207572992/1419570438186467368/OIP.png?ex=68d23d7e&is=68d0ebfe&hm=b2181e10ea002da5c11ee5e1fbd71ed4300313f1b8bfff3ff4fa96c12a0b0c29&=&format=webp&quality=lossless')
            embed.set_footer(text=f'{interaction.user.name}', icon_url=interaction.user.avatar.url)
        elif len(set(final_slots)) == 2:  # dois iguais
            
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(UserMDBs).filter_by(membro_id=interaction.user.id))
                userdb = result.scalars().first()
                if not userdb:
                    userdb = UserMDBs(membro_id=interaction.user.id)
                    session.add(userdb)
                userdb.MDBs += self.quantidade
                await session.commit()
            
            ganho = self.quantidade
            embed = discord.Embed(
                title="✨ Quase lá!",
                description=f"Você conseguiu **2 emojis iguais**.\n💵 Ganhou **{ganho} MDBs**.",
                color=discord.Color.gold(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_thumbnail(url='https://media.discordapp.net/attachments/1415295712207572992/1419570438186467368/OIP.png?ex=68d23d7e&is=68d0ebfe&hm=b2181e10ea002da5c11ee5e1fbd71ed4300313f1b8bfff3ff4fa96c12a0b0c29&=&format=webp&quality=lossless')
            embed.set_footer(text=f'{interaction.user.name}', icon_url=interaction.user.avatar.url)
        else:  # nenhum igual
            
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(UserMDBs).filter_by(membro_id=interaction.user.id))
                userdb = result.scalars().first()
                if not userdb:
                    userdb = UserMDBs(membro_id=interaction.user.id)
                    session.add(userdb)
                userdb.MDBs -= self.quantidade
                await session.commit()
            ganho = -self.quantidade
            embed = discord.Embed(
                title="❌ Azar!",
                description=f"Não veio nada...\n💸 Você perdeu **{self.quantidade} MDBs**.",
                color=discord.Color.red(),
                timestamp=discord.utils.utcnow()
            )
            embed.set_footer(text=f'{interaction.user.name}', icon_url=interaction.user.avatar.url)
            embed.set_thumbnail(url='https://media.discordapp.net/attachments/1415295712207572992/1419570438186467368/OIP.png?ex=68d23d7e&is=68d0ebfe&hm=b2181e10ea002da5c11ee5e1fbd71ed4300313f1b8bfff3ff4fa96c12a0b0c29&=&format=webp&quality=lossless')

        embed.add_field(name="🎲 Resultado", value=f"**{resultado}**", inline=False)
        embed.set_footer(text=f"{interaction.user.name}", icon_url=interaction.user.avatar.url)

        await self.message.edit(embed=embed, view=None)

THUMBNAIL_URL = "https://cdn.discordapp.com/attachments/1415295712207572992/1419553892760293376/OIG2.png"

def random_color():
    return random.choice(["azul", "vermelho", "verde", "cinza"])

AsyncSessionTwoLocal = AsyncSessionLocal

class ButtonsForRandomColorCommands(discord.ui.View):
    def __init__(self, ctx_author_id, color: str, quantidade: int):
        super().__init__(timeout=120)
        self.color_ = color
        self.ctx_author_id = ctx_author_id
        self.quantidade = quantidade

    async def process_result(self, interaction: discord.Interaction, chosen_color: str, color_display: discord.Color):
        """Centraliza a lógica de ganho/perda para todas as cores"""
        if self.ctx_author_id != interaction.user.id:
            return await interaction.response.send_message("🚫 Essa aposta não é sua!", ephemeral=True)

        acerto = self.color_ == chosen_color
        async with AsyncSessionTwoLocal() as session:
            result = await session.execute(select(UserMDBs).filter_by(membro_id=interaction.user.id))
            userdb = result.scalars().first()
            if not userdb:
                userdb = UserMDBs(membro_id=interaction.user.id, MDBs=0)
                session.add(userdb)

            if acerto:
                userdb.MDBs += self.quantidade
            else:
                userdb.MDBs -= self.quantidade
            await session.commit()
            saldo = userdb.MDBs

        # Embed de resultado
        m = discord.Embed(
            title=("🎉 Você acertou a cor!" if acerto else "❌ Você errou a cor!"),
            description=("✨ Você já pode ser vidente!" if acerto else "🔮 Parece que você não tem dons de adivinhação..."),
            color=(color_display if acerto else discord.Color.red()),
            timestamp=discord.utils.utcnow()
        )

        m.add_field(
            name="📌 Informações",
            value=f"🎨 Cor escolhida: **{chosen_color.capitalize()}**\n🎲 Cor sorteada: **{self.color_.capitalize()}**\n{'💰 Ganhou' if acerto else '💸 Perdeu'}: **{self.quantidade} MDBs**",
            inline=False
        )
        m.add_field(name="💳 Seu Saldo", value=f"**{saldo} MDBs**", inline=False)
        m.set_thumbnail(url=THUMBNAIL_URL)
        m.set_footer(text=f"{interaction.user.name}", icon_url=interaction.user.avatar.url)

        await interaction.response.send_message(embed=m)

    # Botões das cores
    @discord.ui.button(label="Azul", style=discord.ButtonStyle.blurple)
    async def azul(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_result(interaction, "azul", discord.Color.blue())

    @discord.ui.button(label="Verde", style=discord.ButtonStyle.green)
    async def verde(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_result(interaction, "verde", discord.Color.green())

    @discord.ui.button(label="Vermelho", style=discord.ButtonStyle.red)
    async def vermelho(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_result(interaction, "vermelho", discord.Color.red())

    @discord.ui.button(label="Preto", style=discord.ButtonStyle.grey)
    async def preto(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_result(interaction, "cinza", discord.Color.dark_gray())

class ButtonForRoletaRussa(discord.ui.View):
    def __init__(self, ctx_author_id, msg, quantidade: int):
        super().__init__(timeout=120)
        self.ctx_author_id = ctx_author_id
        self.muni = 6
        self.msg = msg
        self.quantidade = quantidade

        self.botao_muni = discord.ui.Button(
            label=f"Munições: {self.muni} / 6",
            style=discord.ButtonStyle.secondary,
            disabled=True
        )
        botao_tiro = discord.ui.Button(label="🔫 Atirar", style=discord.ButtonStyle.danger)
        botao_desistir = discord.ui.Button(label="🛑 Desistir", style=discord.ButtonStyle.success)

        botao_tiro.callback = self.tiro_button_callback
        botao_desistir.callback = self.desistir_button_callback

        self.add_item(botao_tiro)
        self.add_item(self.botao_muni)
        self.add_item(botao_desistir)

    async def tiro_button_callback(self, interaction: discord.Interaction):
        if self.ctx_author_id != interaction.user.id:
            return await interaction.response.send_message("❌ Esse jogo não é seu, não clique!", ephemeral=True)

        municao = random.randint(1, 6)
        self.muni -= 1

        if self.muni == municao:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(UserMDBs).filter_by(membro_id=interaction.user.id))
                userdb = result.scalars().first()
                if not userdb:
                    userdb = UserMDBs(membro_id=interaction.user.id)
                    session.add(userdb)
                userdb.MDBs -= self.quantidade
                await session.commit()

            embed = discord.Embed(
                title="💀 GAME OVER!",
                description=f"Você puxou o gatilho e...\n\n**💥 BANG!**\n\nPerdeu **{self.quantidade:,} MDBs**.",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/1415295712207572992/1419830608418312314/ilustracao-em-vetor-de-caixao-de-desenho-animado-em-fundo-branco_122784-8355.png?ex=68d32fcc&is=68d1de4c&hm=315aafb12df5bd15b95a48140ef13d4a5395509b9f1ed9d2217950ec5a328ee2&')
            
            return await interaction.response.edit_message(embed=embed, view=None)

        if self.muni == 0:
            async with AsyncSessionLocal() as session:
                result = await session.execute(select(UserMDBs).filter_by(membro_id=interaction.user.id))
                userdb = result.scalars().first()
                if not userdb:
                    userdb = UserMDBs(membro_id=interaction.user.id)
                    session.add(userdb)
                userdb.MDBs += self.quantidade
                await session.commit()

            embed = discord.Embed(
                title="🎉 VITÓRIA!",
                description=f"Você sobreviveu a **6 tiros** e ganhou **{self.quantidade:,} MDBs**!",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/1415295712207572992/1419830368588267580/R.png?ex=68d32f93&is=68d1de13&hm=37d1e150d0790b4020165b45da9283b480d49e664cb60458e273a748115c2d87&')
            
            return await interaction.response.edit_message(embed=embed, view=None)

        self.botao_muni.label = f"Munições: {self.muni} / 6"

        embed = discord.Embed(
            title="🔫 Roleta Russa",
            description=f"Você puxou o gatilho... **CLIC!**\n\nMunições restantes: **{self.muni}**",
            color=discord.Color.orange()
        )
        embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/1415295712207572992/1419830368588267580/R.png?ex=68d32f93&is=68d1de13&hm=37d1e150d0790b4020165b45da9283b480d49e664cb60458e273a748115c2d87&')
        
        await interaction.response.edit_message(embed=embed, view=self)

    async def desistir_button_callback(self, interaction: discord.Interaction):
        if self.ctx_author_id != interaction.user.id:
            return await interaction.response.send_message("❌ Esse jogo não é seu, não clique!", ephemeral=True)

        if self.muni == 6:
            embed = discord.Embed(
                title="😅 Covarde!",
                description=f"Você desistiu **sem dar um tiro**.\n\nPerdeu toda a aposta de **{self.quantidade:,} MDBs**.",
                color=discord.Color.dark_red()
            )
            embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/1415295712207572992/1419830368588267580/R.png?ex=68d32f93&is=68d1de13&hm=37d1e150d0790b4020165b45da9283b480d49e664cb60458e273a748115c2d87&')
            return await interaction.response.edit_message(embed=embed, view=None)

        ganhos = {5: 0.15, 4: 0.20, 3: 0.25, 2: 0.30, 1: 0.50}
        ganho = int(self.quantidade * ganhos.get(self.muni, 0))

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(UserMDBs).filter_by(membro_id=interaction.user.id))
            userdb = result.scalars().first()
            if not userdb:
                userdb = UserMDBs(membro_id=interaction.user.id)
                session.add(userdb)
            userdb.MDBs += ganho
            await session.commit()

        embed = discord.Embed(
            title="🛑 Você desistiu!",
            description=f"Sobreviveu a **{6 - self.muni} tiros**.\n\nRecebeu **{ganho:,} MDBs** como prêmio de consolação.",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/1415295712207572992/1419830368588267580/R.png?ex=68d32f93&is=68d1de13&hm=37d1e150d0790b4020165b45da9283b480d49e664cb60458e273a748115c2d87&')
        await interaction.response.edit_message(embed=embed, view=None)

class ButtonCoinFlip(discord.ui.View):
    def __init__(self, ctx, author, quantidade: int):
        super().__init__(timeout=120)
        self.ctx = ctx
        self.author = author
        self.quantidade = quantidade
        self.accepted = False
        self.desafiado = None

    async def on_timeout(self):
        if not self.accepted:
            embed_timeout = discord.Embed(
                title="💰 Coinflip Expirado",
                description="⏳ Ninguém aceitou o desafio a tempo.",
                color=discord.Color.red()
            )
            await self.ctx.send(embed=embed_timeout)

    @discord.ui.button(label="Aceitar", style=discord.ButtonStyle.green)
    async def aceitardesafio(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Prevenir auto-aceite
        if interaction.user.id == self.author.id:
            return await interaction.response.send_message(
                "❌ Você não pode aceitar seu próprio desafio!",
                ephemeral=True
            )

        # Prevenir múltiplos aceites
        if self.accepted:
            return await interaction.response.send_message(
                "❌ Este desafio já foi aceito por alguém!",
                ephemeral=True
            )

        self.desafiado = interaction.user

        # Verificar saldo do desafiado
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(UserMDBs).filter_by(membro_id=self.desafiado.id))
            desafiado_db = result.scalars().first()

            if not desafiado_db or desafiado_db.MDBs < self.quantidade:
                return await interaction.response.send_message(
                    "❌ Você não tem saldo suficiente para aceitar!",
                    ephemeral=True
                )

        # Marca que o desafio foi aceito
        self.accepted = True
        for child in self.children:
            if isinstance(child, discord.ui.Button):
                child.disabled = True
        await interaction.response.edit_message(view=self)

        # Animação
        embed_anim = discord.Embed(
            title="🪙 Coinflip",
            description="Girando a moeda...",
            color=discord.Color.light_grey()
        )
        msg_anim = await self.ctx.send(embed=embed_anim)

        await asyncio.sleep(2)

        # Processar aposta
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(UserMDBs).filter_by(membro_id=self.author.id))
            author_db = result.scalars().first()

            result = await session.execute(select(UserMDBs).filter_by(membro_id=self.desafiado.id))
            desafiado_db = result.scalars().first()

            if not author_db or author_db.MDBs < self.quantidade or not desafiado_db or desafiado_db.MDBs < self.quantidade:
                embed_fail = discord.Embed(
                    title="❌ Coinflip cancelado",
                    description="Um dos jogadores não tinha saldo suficiente no momento da aposta.",
                    color=discord.Color.red()
                )
                return await msg_anim.edit(embed=embed_fail)

            # Debitar valores
            author_db.MDBs -= self.quantidade
            desafiado_db.MDBs -= self.quantidade

            # Sortear vencedor
            ganhador_db = random.choice([author_db, desafiado_db])
            ganhador_db.MDBs += self.quantidade * 2

            await session.commit()

        try:
            usuario_ganhador = await self.ctx.bot.fetch_user(ganhador_db.membro_id)
        except:
            usuario_ganhador = self.ctx.guild.get_member(ganhador_db.membro_id) or f"<@{ganhador_db.membro_id}>"

        embed_ganhador = discord.Embed(
            title="💰 Coinflip - Resultado",
            description=(
                f"**Vencedor:** {usuario_ganhador.mention}\n"
                f"**Prêmio:** {self.quantidade * 2:,} MDBs\n"
                f"**Saldo atual:** {ganhador_db.MDBs:,} MDBs\n\n"
                f"💸 **Participantes:**\n"
                f"• {self.author.mention} (Desafiante)\n"
                f"• {self.desafiado.mention} (Desafiado)"
            ),
            color=discord.Color.green()
        )
        embed_ganhador.set_footer(text="Boa sorte na próxima!")
        await msg_anim.edit(embed=embed_ganhador)

class RoletaView(discord.ui.View):
    def __init__(self, user_id: int, valor: int, aposta_numero: int = None):
        super().__init__(timeout=30)
        self.user_id = user_id
        self.valor = valor
        self.aposta_numero = aposta_numero
        self.message = None
        self.bet_made = False

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        if self.message:
            embed = discord.Embed(
                title="⌛ Tempo Esgotado",
                description="⏱️ O tempo de 30 segundos acabou e a aposta foi cancelada.",
                color=discord.Color.light_gray()
            )
            embed.set_footer(text="Tente novamente quando estiver pronto!")
            await self.message.edit(embed=embed, view=self)

    @discord.ui.button(label="🔴 Vermelho", style=discord.ButtonStyle.red)
    async def vermelho(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_choice(interaction, "vermelho", 0.475, 2)

    @discord.ui.button(label="⚫ Preto", style=discord.ButtonStyle.gray)
    async def preto(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_choice(interaction, "preto", 0.475, 2)

    @discord.ui.button(label="🟢 Verde", style=discord.ButtonStyle.green)
    async def verde(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.process_choice(interaction, "verde", 0.05, 15)

    async def process_choice(self, interaction: discord.Interaction, escolha: str, chance: float, multiplicador: float):
        if self.bet_made:
            return await interaction.response.send_message("❌ Você já apostou nesta rodada.", ephemeral=True)

        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ Apenas quem iniciou a roleta pode jogar.", ephemeral=True)

        saldo = await get_saldo(self.user_id)
        if saldo < self.valor:
            await interaction.response.send_message("❌ Saldo insuficiente para completar a aposta.", ephemeral=True)
            self.stop()
            return

        self.bet_made = True

        cor_sorteada = random.choices(["vermelho", "preto", "verde"], weights=[47.5, 47.5, 5], k=1)[0]
        numero_sorteado = random.randint(1, 36)

        linha = [gerar_nova_bolinha() for _ in range(7)]
        embed = discord.Embed(
            title="🎰 Roleta de MDBs",
            description="Girando...",
            color=discord.Color.light_gray()
        )
        embed.add_field(name="🧑‍💻 Jogador:", value=interaction.user.mention, inline=True)
        embed.add_field(name="💰 Aposta:", value=f"{self.valor:,} MDBs", inline=True)
        embed.add_field(name="⏳ Girando:", value=gerar_linha_emojis(linha), inline=False)
        embed.set_footer(text="🎯 Girando a roleta...")

        await interaction.response.edit_message(embed=embed, view=self)
        self.message = await interaction.original_response()

        for i in range(15):
            linha.pop()
            linha.insert(0, gerar_nova_bolinha())
            if i == 14:
                linha[len(linha)//2] = cor_sorteada
            embed.set_field_at(2, name="⏳ Girando:", value=gerar_linha_emojis(linha), inline=False)
            await self.message.edit(embed=embed, view=self)
            await asyncio.sleep(1 / 3)

        acertou_cor = (escolha == cor_sorteada)
        acertou_numero = (self.aposta_numero == numero_sorteado) if self.aposta_numero is not None else False

        if self.aposta_numero is not None:
            if acertou_numero:
                ganho = self.valor * 36
            elif acertou_cor:
                ganho = int((self.valor * multiplicador) * 0.5)
            else:
                ganho = -self.valor
        else:
            if acertou_cor:
                ganho = int(self.valor * multiplicador)
            else:
                ganho = -self.valor

        novo_saldo = saldo + ganho
        await set_saldo(self.user_id, novo_saldo)

        cores_emojis = {"vermelho": "🔴", "preto": "⚫", "verde": "🟢"}
        cores_embed = {
            "vermelho": discord.Color.red(),
            "preto": discord.Color.from_rgb(100, 100, 100),
            "verde": discord.Color.green()
        }

        descricao = f"{cores_emojis[cor_sorteada]} **Cor sorteada:** `{cor_sorteada.upper()}`\n🎲 **Número sorteado:** `{numero_sorteado}`\n\n"

        if self.aposta_numero is not None and acertou_numero:
            descricao += "🏆 Você acertou o número e ganhou **36x** sua aposta!"
        elif acertou_cor:
            if self.aposta_numero is not None:
                descricao += "✅ Você acertou a cor, mas errou o número! Ganhou **50% do prêmio da cor.**"
            else:
                descricao += "✅ Você acertou a cor e ganhou **100% do prêmio da cor!**"
        else:
            descricao += "❌ Você perdeu!"

        embed.title = "🎯 Resultado da Roleta de MDBs"
        embed.color = cores_embed[cor_sorteada]
        embed.set_field_at(2, name="📊 Resultado:", value=descricao, inline=False)
        embed.add_field(name="🏆 Ganho / Perda:", value=f"{'+ ' if ganho > 0 else '- '}{abs(ganho):,} MDBs", inline=True)
        embed.add_field(name="💸 Saldo Atual:", value=f"{novo_saldo:,} MDBs", inline=True)
        embed.set_footer(text="🏁 Fim da rodada!")
        embed.set_image(url=ROLL_IMAGE_CDN)

        await self.message.edit(embed=embed, view=None)
        self.stop()

def gerar_nova_bolinha():
    cores = ["vermelho", "preto", "verde"]
    pesos = [0.475, 0.475, 0.05]
    return random.choices(cores, weights=pesos, k=1)[0]

def gerar_linha_emojis(linha):
    emojis = {"vermelho": "🔴", "preto": "⚫", "verde": "🟢"}
    meio = len(linha) // 2
    display = ""
    for i, cor in enumerate(linha):
        if i == meio:
            display += f"│{emojis[cor]}│"
        else:
            display += emojis[cor]
        if i < len(linha) - 1:
            display += " "
    return display

ROLL_IMAGE_CDN = "https://cdn.discordapp.com/attachments/1383937512933822586/1391543791219118260/images_4.jpg?"

class RoletaButton(discord.ui.View):
    def __init__(self, user_id: int):
        super().__init__(timeout=30)
        self.user_id = user_id

    @discord.ui.button(label="🎰 Girar a Roleta", style=discord.ButtonStyle.green)
    async def girar(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message(
                "❌ Apenas quem iniciou pode girar a roleta.", ephemeral=True
            )

        button.disabled = True
        self.stop()

        embed = discord.Embed(
            title="🎰 Roleta Diária",
            description=f"{interaction.user.mention} girando a roleta...",
            color=discord.Color.blue()
        )

        await interaction.response.defer()

        mensagem = await interaction.followup.send(embed=embed)
        
        async with AsyncSessionLocal() as session:
            result_vip = await session.execute(select(PremiumDataSuper).filter_by(user_id=self.user_id))
            user_vip = result_vip.scalars().first()
        
        if not user_vip:
            animacoes = ["💎 1000000", "💎 500000", "💎 250000", "💎 125000", "💎 60000", "💎 30000", "💎 10000", "💎 5000", "💎 0"]
        else:
            animacoes = ["💎 2500000", "💎 1500000", "💎 1250000", "💎 1000000", "💎 500000", "💎 250000", "💎 100000", "💎 50000", "💎 35000"]

        for _ in range(10):
            escolha_aleatoria = random.choice(animacoes)
            embed.description = f"{interaction.user.mention} girando a roleta...\n\n🎰 **{escolha_aleatoria}**"
            await mensagem.edit(embed=embed)
            await asyncio.sleep(0.4)

        ganho = 0
        hoje = datetime.utcnow().date()

        result = await session.execute(select(RoletaDiariaCooldown).filter_by(user_id=self.user_id))
        cooldown = result.scalars().first()

        if cooldown and cooldown.last_claimed.date() == hoje:
            embed = discord.Embed(
                title="⏳ Roleta Diária",
                description="❌ Você já girou a roleta hoje!\nVolte amanhã para tentar novamente.",
                color=discord.Color.red()
            )
            return await mensagem.edit(embed=embed)

        if cooldown:
            cooldown.last_claimed = datetime.utcnow()
        else:
            cooldown = RoletaDiariaCooldown(user_id=self.user_id, last_claimed=datetime.utcnow())
            session.add(cooldown)

        if not user_vip:
            opcoes = [1_000_000, 500_000, 250_000, 125_000, 60_000, 30_000, 10_000, 5_000, 0]
            pesos = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        else:
            opcoes = [2_500_000, 1_500_000, 1_250_000, 1_000_000, 500_000, 250_000, 100_000, 50_000, 35_000]
            pesos = [1, 2, 3, 4, 5, 6, 7, 8, 9]

        ganho = random.choices(opcoes, weights=pesos, k=1)[0]

        result_user = await session.execute(select(UserMDBs).filter_by(membro_id=self.user_id))
        membro_db = result_user.scalars().first()
        if not membro_db:
            membro_db = UserMDBs(membro_id=self.user_id, MDBs=ganho)
            session.add(membro_db)
        else:
            membro_db.MDBs += ganho

        await session.commit()

        cor_embed = discord.Color.gold() if ganho > 0 else discord.Color.dark_gray()
        embed.description = f"Parabéns {interaction.user.mention}!\nVocê girou a roleta e ganhou:\n\n💎 **{ganho:,} MDBs**"
        embed.color = cor_embed
        embed.set_thumbnail(url='https://media.discordapp.net/attachments/1410462821396774924/1410479150275231767/cartaz-da-roda-da-fortuna-girando-a-roleta-da-sorte-com-ganhar-dinheiro-em-dinheiro-premios-presentes-e-confetes-em-fundo-escuro-banner-do-jogo-de-azar-simbolo-de-boa-sorte-e-sucesso-de-vida-conceito-de-chance-do-vencedor-eps_502272-1188.png?ex=68b12a92&is=68afd912&hm=d6263772364199f353ee00974de8f0210c190431a0e7722ab7afe15d7cf356a3&=&format=webp&quality=lossless&width=823&height=548')
        embed.set_footer(text="Volte amanhã para girar novamente! ⏳")
        embed.timestamp = datetime.utcnow()

        await mensagem.edit(embed=embed)
        
class EconomiaMDBs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Evento
    @commands.Cog.listener()
    async def on_ready(self):
        print("Cog Economia carregado!")

    async def get_membro(self, membro_id: int) -> UserMDBs:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(UserMDBs).filter_by(membro_id=membro_id))
            membro = result.scalar_one_or_none()
            if not membro:
                membro = UserMDBs(membro_id=membro_id)
                session.add(membro)
                await session.commit()
                await session.refresh(membro)
            return membro

    async def get_poupanca(self, user_id: int) -> Poupanca:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Poupanca).filter_by(user_id=user_id))
            poupanca = result.scalar_one_or_none()
            if not poupanca:
                poupanca = Poupanca(user_id=user_id, mdbs_poupanca=0)
                session.add(poupanca)
                await session.commit()
                await session.refresh(poupanca)
            return poupanca

    async def add_ganho(self, user_id: int, quantia: int):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(StatsUserData).filter_by(membro_id=user_id))
            stats = result.scalar_one_or_none()
            if not stats:
                stats = StatsUserData(membro_id=user_id)
                session.add(stats)
                await session.commit()
            stats.ganho_total += quantia
            await session.commit()

    async def add_perda(self, user_id: int, quantia: int):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(StatsUserData).filter_by(membro_id=user_id))
            stats = result.scalar_one_or_none()
            if not stats:
                stats = StatsUserData(membro_id=user_id)
                session.add(stats)
                await session.commit()
            stats.perda_total += quantia
            await session.commit()

    @commands.command(name="diariaroleta", aliases=["roletadiaria", "roletadiária", "roletadiária"])
    async def diaria(self, ctx: commands.Context):

        view = RoletaButton(user_id=ctx.author.id)
        embed = discord.Embed(
            title="🎰 Roleta Diária",
            description=f"{ctx.author.mention}, clique no botão abaixo para girar a roleta!",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed, view=view)

    @commands.command(name="diario", aliases=["daily", "diária", "diaria"])
    async def diario(self, ctx:commands.Context):
        agora = datetime.utcnow()
        user_id = ctx.author.id
        plataforma = get_plataforma(user_id) 
        usar_espacos = (plataforma == "desktop")

        async with AsyncSessionLocal() as session:
            # Cooldown
            result = await session.execute(
                select(DailyCooldown).filter_by(user_id=user_id)
            )
            cooldown = result.scalars().first()

            if cooldown and cooldown.last_claimed and (agora.date() == cooldown.last_claimed.date()):
                embed_ja_pego = discord.Embed(
                    title="❌ Diária já coletada!",
                    description="Você já pegou sua diária hoje.\nVolte amanhã para mais recompensas!",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed_ja_pego)
                return
            
            if cooldown:
                cooldown.last_claimed = agora
            else:
                cooldown = DailyCooldown(user_id=user_id, last_claimed=agora)
                session.add(cooldown)

            # Verifica VIP (ajustado)
            result = await session.execute(
                select(PremiumDataSuper).filter_by(user_id=user_id)
            )
            VipUser = result.scalars().first()
            if VipUser:
                recompensa = random.randint(30000, 80000)
            else:
                recompensa = random.randint(10000, 40000)

            # Busca ou cria membro NA MESMA SESSÃO
            result = await session.execute(select(UserMDBs).filter_by(membro_id=user_id))
            membro_db = result.scalars().first()
            if not membro_db:
                membro_db = UserMDBs(membro_id=user_id, MDBs=0)
                session.add(membro_db)

            membro_db.MDBs += recompensa
            novo_saldo = membro_db.MDBs
            
            await session.commit()

        # Embed de resposta
        titulo = "🎁 Aqui Está Sua Recompensa Diária! ㅤ" if usar_espacos else "🎁 Aqui Está Sua Recompensa Diária!"

        embed = discord.Embed(title=titulo, color=discord.Color(0xFFEA00))
        embed.add_field(name="💎 Recompensa", value=f"**{recompensa}** mdbs", inline=True)
        embed.add_field(name="💼 Novo Saldo", value=f"**{novo_saldo}** mdbs", inline=True)

        if usar_espacos:
            embed.add_field(name="ㅤ", value="ㅤ", inline=True) 

        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1320526861322944602/1406795867444346930/money-bag_1f4b0_1.webp")
        embed.set_footer(text="Volte em 24 horas para coletar novamente! ⏳")

        await ctx.send(embed=embed)

    @commands.command(name="saldo", aliases=["bal", "balance", "mdbs", "saldos"])
    async def saldo_mdbs(self, ctx:commands.Context, membro:discord.User = None):
        
        if membro is None:
            membro = ctx.author
        
        user_id = membro.id
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(OptionsCommandsStyle).filter_by(user_id=membro.id))
            userdb_style = result.scalars().first()
            if not userdb_style:
                userdb_style = OptionsCommandsStyle(user_id=ctx.author.id)
                session.add(userdb_style)
            style_command = userdb_style.command_option_1 or "SALDO_EMBED"
            await session.commit()

            result = await session.execute(select(UserMDBs).filter_by(membro_id=user_id))
            membro_db = result.scalars().first()
            if not membro_db:
                membro_db = UserMDBs(membro_id=user_id, MDBs=0)
                session.add(membro_db)
                
            saldo = membro_db.MDBs
            
            resultpoupanca = await session.execute(select(Poupanca).filter_by(user_id=user_id))
            user_poupanca = resultpoupanca.scalars().first()
            if not user_poupanca:
                user_poupanca = Poupanca(user_id=user_id, mdbs_poupanca=0)
                session.add(user_poupanca)
                
            saldo_poupanca = user_poupanca.mdbs_poupanca
            
            await session.commit()
            
            saldo_poupanca_formatado = f"{saldo_poupanca/1_000_000:.1f}m" if saldo_poupanca >= 1_000_000 else f"{saldo_poupanca/1000:.1f}k" if saldo_poupanca >= 1000 else str(saldo_poupanca)
        
        embed_mdbs = discord.Embed(
            title="Saldo MDBs",
            description=f"Seu saldo é: {saldo:,} MDBs",
            color=discord.Color.yellow()
        )
        embed_mdbs.set_thumbnail(url="https://cdn.discordapp.com/attachments/1332184576625213451/1405359306903130112/money-bag_1f4b0.webp?ex=689e8a59&is=689d38d9&hm=90be9541f2af7b2b1e7a748477f094317cbd082b50dfc190ca7f161c79b2ca90&")

        embeds = [embed_mdbs]

        if saldo_poupanca > 0:
            embed_poupanca = discord.Embed(
                title="Saldo Poupança",
                description=f"Seu saldo é: {saldo_poupanca_formatado} MDBs",
                color=discord.Color.dark_grey()
            )
            embed_poupanca.set_thumbnail(url="https://cdn.discordapp.com/attachments/1332184576625213451/1405360018509008906/bank_1f3e6.png?ex=689e8b02&is=689d3982&hm=9b72a2870eb55e75fd79b5001c6d52a85e6d9146a7124b880098d026be0cf793&")
            embeds.append(embed_poupanca)

        for embed in embeds:
            await ctx.send(embed=embed)

    @commands.command(name="poupanca", aliases=["poupança", "poupar", "pouparmdbs"])
    async def addpoupanca(self, ctx:commands.Context, quantidade:interpretar_valor):
        userdb = await pegar_usuario(ctx.author.id)
        saldo = userdb.MDBs

        if quantidade <= 0:
            await ctx.reply("❌ A quantidade deve ser maior que zero.", ephemeral=True)
            return
        if quantidade > saldo:
            await ctx.reply("❌ Você não tem saldo suficiente para poupar essa quantia.", ephemeral=True)
            return

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Poupanca).filter_by(user_id=ctx.author.id))
            userdb_poupanca = result.scalars().first()
            if not userdb_poupanca:
                userdb_poupanca = Poupanca(user_id=ctx.author.id, mdbs_poupanca=0)
                session.add(userdb_poupanca)
            result2 = await session.execute(select(UserMDBs).filter_by(membro_id=ctx.author.id))
            userdb2 = result2.scalars().first()
            if not userdb2:
                userdb2 = UserMDBs(membro_id=ctx.author.id)
                session.add(userdb2)
            userdb2.MDBs -= quantidade
            userdb_poupanca.mdbs_poupanca += quantidade
            await session.commit()

        embed_sucesso = discord.Embed(
            title="Dinheiro adicionado na poupança!✅",
            description=f"Você adicionou **{quantidade:,}** MDBs na sua poupança.\nSeu novo saldo na poupança agora é: **{userdb_poupanca.mdbs_poupanca}**.\nDica: Use <saldo para checar seu saldo.",
            color=discord.Color.green()
            )
        
        embed_sucesso.set_thumbnail(url='https://media.discordapp.net/attachments/1400704538696089623/1410443729034285118/O-que-e-capacidade-de-poupanca.png?ex=68b10995&is=68afb815&hm=390109dc9dc0e655b5fb5aca0f0368225e7e4afa6d1bde998ebcd31c1d97f709&=&format=webp&quality=lossless&width=1144&height=764')
        embed_sucesso.set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url)
        embed_sucesso.timestamp = datetime.utcnow()

        await ctx.reply(embed=embed_sucesso)

    @commands.command(name="sacar", aliases=["resgatarpoupanca", "resgatarpoupança", "resgatar"])
    async def retirarpoupancauser(self, ctx:commands.Context, quantidade:interpretar_valor):

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Poupanca).filter_by(user_id=ctx.author.id))
            userdb_poupanca = result.scalars().first()
            result2 = await session.execute(select(UserMDBs).filter_by(membro_id=ctx.author.id))
            userdb = result2.scalars().first()
            if not userdb_poupanca or userdb_poupanca.mdbs_poupanca <= 0:
                await ctx.reply("❌ Você não tem saldo na poupança para sacar.", ephemeral=True)
                return
            if quantidade <= 0:
                await ctx.reply("❌ A quantidade deve ser maior que zero.", ephemeral=True)
                return
            if quantidade > userdb_poupanca.mdbs_poupanca:
                await ctx.reply("❌ Você não tem saldo suficiente na poupança para sacar essa quantia.", ephemeral=True)
                return

            userdb.MDBs += quantidade
            userdb_poupanca.mdbs_poupanca -= quantidade
            await session.commit()
        
        embed_sucesso = discord.Embed(
            title="Dinheiro sacado da poupança!✅",
            description=f"Você sacou **{quantidade:,}** MDBs da sua poupança.\nSeu novo saldo na poupança agora é: **{userdb_poupanca.mdbs_poupanca} MDBs💰**.\nDica: Use <saldo para checar seu saldo.",
            color=discord.Color.green()
            )
        embed_sucesso.set_thumbnail(url='https://media.discordapp.net/attachments/1400704538696089623/1410457738189996113/design-de-poupanca-fundo_1270-10.png?ex=68b116a1&is=68afc521&hm=3c8d9e0aa001fac7ee60ad14fbc4291e7f56f98c8a5424f20b6e7f0bf49f302e&=&format=webp&quality=lossless&width=823&height=823')
        embed_sucesso.set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url)
        embed_sucesso.timestamp = datetime.utcnow()

        await ctx.reply(embed=embed_sucesso)

    @commands.command(name="transferir", aliases=["transf", "pay", "pagar", "enviar"])
    async def transferir_mdbs(self, ctx:commands.Context, membro:discord.Member, quantidade:interpretar_valor):

        if membro is None:
            await ctx.reply("❌ Você precisa mencionar um membro para transferir MDBs.\nAssim: <pay [usuario] quantidade", ephemeral=True)
            return

        if membro.id == 1367932530938089472:
            await ctx.reply("Não tenho interesse nos seus MDBs.")
            return

        userdb_author = await pegar_usuario(ctx.author.id)
        userdb_membro = await pegar_usuario(membro.id)
        saldo_author = userdb_author.MDBs

        if membro.id == ctx.author.id:
            await ctx.reply("❌ Você não pode transferir MDBs para si mesmo.", ephemeral=True)
            return
        if quantidade <= 0:
            await ctx.reply("❌ A quantidade deve ser maior que zero.", ephemeral=True)
            return
        if quantidade > saldo_author:
            await ctx.reply("❌ Você não tem saldo suficiente para transferir essa quantia.", ephemeral=True)
            return
        
        async with AsyncSessionLocal() as session:
            result_author = await session.execute(select(UserMDBs).filter_by(membro_id=ctx.author.id))
            userdb_author = result_author.scalars().first()
            result_membro = await session.execute(select(UserMDBs).filter_by(membro_id=membro.id))
            userdb_membro = result_membro.scalars().first()
            if not userdb_author or not userdb_membro:
                await ctx.reply("❌ Ocorreu um erro ao processar a transferência. Tente novamente mais tarde.", ephemeral=True)
                return
            userdb_author.MDBs -= quantidade
            userdb_membro.MDBs += quantidade
            await session.commit()

        embed_sucesso = discord.Embed(
            title="Transferência bem-sucedida!💵",
            description=f"Você transferiu **{quantidade:,}** MDBs para {membro.mention}.\nSeu novo saldo agora é: **{userdb_author.MDBs} MDBs💰**.",
            color=discord.Color.green()
            )
        embed_sucesso.set_thumbnail(url='https://media.discordapp.net/attachments/1410462821396774924/1410462837813542932/pagamentos-online-696x392.png?ex=68b11b61&is=68afc9e1&hm=666c24162ff33d6767d399fd01fb5b54a35f982fad8d3bdf4863fe8e06710e5e&=&format=webp&quality=lossless&width=915&height=515')
        embed_sucesso.set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url)
        embed_sucesso.timestamp = datetime.utcnow()

        await ctx.reply(embed=embed_sucesso)

    @commands.command(name="acoes", aliases=["ação", "ações"])
    async def acoes(self, ctx:commands.Context, quantidade:interpretar_valor = None):
        userdb = await pegar_usuario(ctx.author.id)
        saldo = userdb.MDBs

        if quantidade is None:
            await ctx.reply("Você tem duas opções no mercado de ações, apostar em alta ou baixa, clique em um dos botões para escolher sua aposta.")
            return
        if quantidade <= 0:
            await ctx.reply("❌ A quantidade deve ser maior que zero.", ephemeral=True)
            return
        if quantidade > saldo:
            await ctx.reply("❌ Você não tem saldo suficiente para apostar essa quantia.", ephemeral=True)
            return
        
        embed_incial = discord.Embed(
            title="Mercado de Ações 📈📉",
            description=f"Você está prestes a apostar **{quantidade:,}** MDBs no mercado de ações.\nEscolha entre apostar em **Alta 📈** ou **Baixa 📉** clicando em um dos botões abaixo.\n\n**Regras:**\n- Se você apostar em Alta e o mercado subir, você ganha a quantia apostada.\n- Se você apostar em Alta e o mercado cair, você perde a quantia apostada.\n- Se você apostar em Baixa e o mercado cair, você ganha a quantia apostada.\n- Se você apostar em Baixa e o mercado subir, você perde a quantia apostada.",
            color=discord.Color.blue()
            )
        embed_incial.set_thumbnail(url='https://media.discordapp.net/attachments/1410462821396774924/1410472347466600542/Colunas_bolsa-de-valores-acoes_3set21_Manusapon-Kasosod_GettyImages-1536x1024-1-e1654788080105.png?ex=68b1243c&is=68afd2bc&hm=92c2b639c740110849c5ecce100cc8ae59102d3c3ae3cdef9482c9567e900a45&=&format=webp&quality=lossless&width=1204&height=803')
        embed_incial.set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url)
        embed_incial.timestamp = datetime.utcnow()
        
        class AcoesView(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=120)

            @discord.ui.button(label="Alta 📈", style=discord.ButtonStyle.green)
            async def alta(self, interaction:discord.Interaction, button:discord.ui.Button):

                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("❌ Apenas quem iniciou o comando pode usar esses botões.", ephemeral=True)
                    return

                resultado = random.choices([True, False], weights=[0.5, 0.5], k=1)[0]
                if resultado == True:
                    async with AsyncSessionLocal() as session:
                        result = await session.execute(select(UserMDBs).filter_by(membro_id=ctx.author.id))
                        userdb = result.scalars().first()
                        if not userdb:
                            await interaction.response.send_message("❌ Ocorreu um erro ao processar sua aposta. Tente novamente mais tarde.", ephemeral=True)
                            return
                        userdb.MDBs += quantidade
                        await session.commit()

                    embed_ganho = discord.Embed(
                        title="📈 Ações em Alta! Você Ganhou! 📈",
                        description=f"Parabéns! As ações subiram e você ganhou **{quantidade:,}** MDBs💰.\nDica: Use <saldo para verificar seu saldo.",
                        color=discord.Color.green()
                    )
                    embed_ganho.set_thumbnail(url='https://media.discordapp.net/attachments/1410462821396774924/1410469312619348098/R.png?ex=68b12169&is=68afcfe9&hm=8af53dbdf1d4aa12105109d727f6331c7ab7fd1a4ea91fd852527389a1da4874&=&format=webp&quality=lossless&width=1204&height=803')
                    embed_ganho.set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url)
                    embed_ganho.timestamp = datetime.utcnow()

                    await interaction.response.send_message(embed=embed_ganho)
                else:
                    async with AsyncSessionLocal() as session:
                        result = await session.execute(select(UserMDBs).filter_by(membro_id=ctx.author.id))
                        userdb = result.scalars().first()
                        if not userdb:
                            await interaction.response.send_message("❌ Ocorreu um erro ao processar sua aposta. Tente novamente mais tarde.", ephemeral=True)
                            return
                        userdb.MDBs -= quantidade
                        await session.commit()

                    embed_perda = discord.Embed(
                        title="📉 Ações em Baixa! Você Perdeu! 📉",
                        description=f"Infelizmente, as ações caíram e você perdeu **{quantidade:,}** MDBs💰.\nDica: Use <saldo para verificar seu saldo.",
                        color=discord.Color.red()
                    )
                    embed_perda.set_thumbnail(url='https://media.discordapp.net/attachments/1410462821396774924/1410469644313165824/acao-na-Bolsa-de-Valores.png?ex=68b121b8&is=68afd038&hm=53a6d4388b31ccc8c8a5e935d12567e3511e767608a969d9b497caed1d4fa5a6&=&format=webp&quality=lossless&width=1358&height=764')
                    embed_perda.set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url)
                    embed_perda.timestamp = datetime.utcnow()

                    await interaction.response.send_message(embed=embed_perda)
                self.stop()

            @discord.ui.button(label="Baixa 📉", style=discord.ButtonStyle.red)
            async def baixaacoes(self, interaction:discord.Interaction, button:discord.ui.Button):

                if interaction.user.id != ctx.author.id:
                    await interaction.response.send_message("Apenas quem iniciou o comando, pode continuar interagindo.", ephemeral=True)
                    return
                
                resultado = random.choices([True, False], weights=[0.5, 0.5], k=1)[0]
                if resultado == False:
                    async with AsyncSessionLocal() as session:
                        result = await session.execute(select(UserMDBs).filter_by(membro_id=ctx.author.id))
                        userdb = result.scalars().first()
                        if not userdb:
                            await interaction.response.send_message("❌ Ocorreu um erro ao processar sua aposta. Tente novamente mais tarde.", ephemeral=True)
                            return
                        userdb.MDBs += quantidade
                        await session.commit()

                    embed_ganho = discord.Embed(
                        title="📉 Ações em Baixa! Você Ganhou! 📉",
                        description=f"Parabéns! As ações caíram e você ganhou **{quantidade:,}** MDBs💰.\nDica: Use <saldo para verificar seu saldo.",
                        color=discord.Color.green()
                    )
                    embed_ganho.set_thumbnail(url='https://media.discordapp.net/attachments/1410462821396774924/1410470978001043486/OIP.png?ex=68b122f6&is=68afd176&hm=61006e6b9ebd2bd51f8d8cb405c5e2360bd2e77823cae047ac8533b562fd2ee3&=&format=webp&quality=lossless&width=1464&height=764')
                    embed_ganho.set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url)
                    embed_ganho.timestamp = datetime.utcnow()

                    await interaction.response.send_message(embed=embed_ganho)
                else:
                    async with AsyncSessionLocal() as session:
                        result = await session.execute(select(UserMDBs).filter_by(membro_id=ctx.author.id))
                        userdb = result.scalars().first()
                        if not userdb:
                            await interaction.response.send_message("❌ Ocorreu um erro ao processar sua aposta. Tente novamente mais tarde.", ephemeral=True)
                            return
                        userdb.MDBs -= quantidade
                        await session.commit()

                    embed_perda = discord.Embed(
                        title="📈 Ações em Alta! Você Perdeu! 📈",
                        description=f"Infelizmente, as ações subiram e você perdeu **{quantidade:,}** MDBs💰.\nDica: Use <saldo para verificar seu saldo.",
                        color=discord.Color.red()
                    )
                    embed_perda.set_thumbnail(url='https://media.discordapp.net/attachments/1410462821396774924/1410470639386755165/bolsa-de-valores-o-que-e-como-funciona-mitos-e-custos-para-investir-2.png?ex=68b122a5&is=68afd125&hm=2a2274b2664957e1bdc51e9538fc5fadabfc7d4829d86a6396fe4543514a5c87&=&format=webp&quality=lossless&width=986&height=644')
                    embed_perda.set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.avatar.url)
                    embed_perda.timestamp = datetime.utcnow()

                    await interaction.response.send_message(embed=embed_perda)
                self.stop()

        await ctx.send(embed=embed_incial, view=AcoesView())

    @commands.command(name="roleta", aliases=["rlt"])
    async def roleta(self, ctx:commands.Context, valor_aposta: str = None, numero: str = None):
        if valor_aposta is None:
            embed_help = discord.Embed(
                title="🎰 Como Jogar a Roleta de MDBs",
                description=(
                    "**Exemplos de uso:**\n"
                    "`-roleta 5k`\n"
                    "`-roleta 10000 23`\n\n"
                    "✅ Após rodar o comando, escolha a **cor** clicando nos botões.\n\n"
                    "🔢 Se quiser, você pode **apostar também em um número** (1-36) para tentar ganhar **36x** sua aposta.\n"
                    "🔴 Vermelho — 47.5% · 2x\n"
                    "⚫ Preto — 47.5% · 2x\n"
                    "🟢 Verde — 5% · 15x"
                ),
                color=discord.Color.blurple()
            )
            await ctx.send(embed=embed_help)
            return

        try:
            user_db = await pegar_usuario(ctx.author.id)
            saldo_disponivel = user_db.MDBs
            valor_aposta_int = interpretar_valor(valor_aposta)

            if valor_aposta_int <= 0:
                await ctx.send("❌ O valor da aposta deve ser positivo.")
                return
            if valor_aposta_int > saldo_disponivel:
                await ctx.send(f"❌ Você não tem saldo suficiente. Saldo: {format_large_number_for_display(saldo_disponivel)} MDBs")
                return

            numero_int = None
            if numero is not None:
                try:
                    numero_int = int(numero)
                    if numero_int < 1 or numero_int > 36:
                        await ctx.send("❌ O número deve ser entre 1 e 36.")
                        return
                except ValueError:
                    await ctx.send("❌ Número inválido. Use um valor entre 1 e 36 ou deixe em branco.")
                    return

            embed = discord.Embed(
                title="🎰 Roleta de MDBs",
                description=(
                    f"👤 **Jogador:** {ctx.author.mention}\n"
                    f"💰 **Aposta:** {format_large_number_for_display(valor_aposta_int)} MDBs\n\n"
                    "🔴 Vermelho — 47.5% · 2x\n"
                    "⚫ Preto — 47.5% · 2x\n"
                    "🟢 Verde — 5% · 15x\n\n"
                    "⤵️ Clique abaixo para escolher sua cor!"
                ),
                color=discord.Color.dark_red()
            )
            embed.set_footer(text="⏳ Você tem 30 segundos para apostar!")

            view = RoletaView(ctx.author.id, valor_aposta_int, numero_int)
            original_message = await ctx.send(embed=embed, view=view)
            view.original_message = original_message

        except ValueError as e:
            await ctx.send(f"❌ {e}")
        except Exception as e:
            await ctx.send(f"Ocorreu um erro: {e}")


    @commands.command(name="flipcoin", aliases=["coinflip", "girarmoeda"])
    async def flipcoin(self, ctx: commands.Context, quantidade: int):
        if quantidade <= 0:
            return await ctx.reply("❌ A quantidade deve ser maior que zero!")

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(UserMDBs).filter_by(membro_id=ctx.author.id))
            author_db = result.scalars().first()
            if not author_db:
                author_db = UserMDBs(membro_id=ctx.author.id)
                session.add(author_db)
                await session.commit

            if not author_db or author_db.MDBs < quantidade:
                return await ctx.reply("❌ Saldo insuficiente para realizar esta aposta!")

        embed_flip = discord.Embed(
            title="💰 Coinflip",
            description=f"{ctx.author.mention} lançou um desafio valendo **{quantidade:,} MDBs**\nPrimeiro a aceitar entra na aposta.",
            color=discord.Color.gold()
        )
        embed_flip.set_footer(text=f"Requisitado por {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        embed_flip.set_thumbnail(url='https://media.discordapp.net/attachments/1319887904700366869/1406332163451781263/dab550f2df174ef482c86523866f0135.gif?ex=68b13da4&is=68afec24&hm=cbde4fac2a790b368523372c3336a8a62a2a5a6e8d1904fa988d13cc0d6816b4&=&width=526&height=394')

        view = ButtonCoinFlip(ctx, ctx.author, quantidade)
        await ctx.send(embed=embed_flip, view=view)

    @commands.command(name="tiroaoalvo", aliases=["talv"])
    async def tiroaoalvo(self, ctx: commands.Context, quantidade: int):
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(UserMDBs).filter_by(membro_id=ctx.author.id))
            user = result.scalar_one_or_none()
            if not user:
                user = UserMDBs(membro_id=ctx.author.id, MDBs=0)
                session.add(user)
                await session.commit()
                await session.refresh(user)

        saldo = user.MDBs
        if quantidade <= 0:
            return await ctx.reply("Aposte um valor maior que zero!")
        if quantidade > saldo:
            return await ctx.reply("Você não tem saldo suficiente!")

        class ButtonTiro(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)

            @discord.ui.button(label="Atirar 🎯", style=discord.ButtonStyle.grey)
            async def atirar(self, interaction: discord.Interaction, button: discord.ui.Button):
                if interaction.user != ctx.author:
                    return await interaction.response.send_message("Somente quem usou o comando pode jogar!", ephemeral=True)

                resultado = random.choices(["ganhar", "perder"], weights=[35, 65])[0]
                await interaction.response.defer()
                button.disabled = True
                await msg.edit(view=self)
                await asyncio.sleep(2)

                async with AsyncSessionLocal() as session:
                    result = await session.execute(select(UserMDBs).filter_by(membro_id=interaction.user.id))
                    user = result.scalar_one()
                    if resultado == "ganhar":
                        user.MDBs += quantidade
                        await msg.edit(embed=discord.Embed(
                            title="Você acertou ✅!",
                            description=f"Ganhou **{quantidade} MDBs💰**!",
                            color=discord.Color.green()
                        ))
                    else:
                        user.MDBs -= quantidade
                        await msg.edit(embed=discord.Embed(
                            title="Você errou ❌!",
                            description=f"Perdeu **{quantidade} MDBs💰**!",
                            color=discord.Color.red()
                        ).set_thumbnail(url='https://media.discordapp.net/attachments/1410462821396774924/1410771004283949068/ai-generated-8416172_1280.png?ex=68b23a62&is=68b0e8e2&hm=82410cce5a3ec623056e29fd9f9e84207ece0fb0e0c623680973916831305842&=&format=webp&quality=lossless&width=900&height=900')
                        )
                    await session.commit()
                self.stop()

        embed = discord.Embed(
            title="Tiro ao alvo 🎯",
            description=f"Aposte **{quantidade} MDBs** e tente acertar o cervo!",
            color=discord.Color.dark_blue()
        )
        embed.set_thumbnail(url='https://media.discordapp.net/attachments/1410462821396774924/1410771004283949068/ai-generated-8416172_1280.png?ex=68b23a62&is=68b0e8e2&hm=82410cce5a3ec623056e29fd9f9e84207ece0fb0e0c623680973916831305842&=&format=webp&quality=lossless&width=900&height=900')
        msg = await ctx.reply(embed=embed, view=ButtonTiro())

    def cog_unload(self):
        self.aplicar_rendimento_poupanca.cancel() 

    @tasks.loop(hours=24)
    async def aplicar_rendimento_poupanca(self):
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(select(Poupanca))
                contas = result.scalars().all()
                total_contas = len(contas)
                contas_atualizadas = 0

                for conta in contas:
                    if conta.MDBs_poupanca > 0:
                        rendimento = conta.MDBs_poupanca * 0.005 
                        conta.MDBs_poupanca += int(rendimento)
                        contas_atualizadas += 1

                await session.commit()
                print(f"✅ Rendimento aplicado em {contas_atualizadas}/{total_contas} contas")

                canal_notificacao = self.bot.get_channel(1377430138513264782)
                if canal_notificacao:
                    await canal_notificacao.send(
                        f"🏦 Rendimento de 0.5% aplicado! {contas_atualizadas} contas atualizadas."
                    )

            except Exception as e:
                await session.rollback()
                print(f"❌ Erro ao aplicar rendimento: {e}")
                canal_notificacao = self.bot.get_channel(1377430138513264782)
                if canal_notificacao:
                    await canal_notificacao.send("⚠️ Falha ao aplicar rendimento nas poupanças!")

    @commands.command(name="blackjack", aliases=["bj"])
    async def blackjackaposta(self, ctx: commands.Context, aposta: interpretar_valor = None):
        if aposta is None:
            embed = discord.Embed(
                title="🎰 BlackJack - Aposta Necessária",
                description="Você precisa especificar o valor da aposta!\n\n**Exemplo:** `<blackjack 100`",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)
            return

        if aposta <= 0:
            embed = discord.Embed(
                title="❌ Aposta Inválida",
                description="A aposta deve ser maior que zero!",
                color=discord.Color.red()
            )
            await ctx.reply(embed=embed)
            return

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(UserMDBs).where(UserMDBs.membro_id == ctx.author.id)
            )
            user_data = result.scalar_one_or_none()

            if not user_data or user_data.MDBs < aposta:
                embed = discord.Embed(
                    title="💸 Saldo Insuficiente",
                    description=f"Você não tem MDBs suficientes para apostar {aposta}!\nSeu saldo: {user_data.MDBs if user_data else 0} MDBs",
                    color=discord.Color.red()
                )
                await ctx.reply(embed=embed)
                return

            await session.execute(
                update(UserMDBs)
                .where(UserMDBs.membro_id == ctx.author.id)
                .values(MDBs=UserMDBs.MDBs - aposta)
            )
            await session.commit()

        player_hand = [draw_card(), draw_card()]
        marcos_hand = [draw_card(), draw_card()]

        view = BlackjackView(ctx, player_hand, marcos_hand, aposta)

        player_total = view.calculate_total(player_hand)
        marcos_total = view.calculate_total([marcos_hand[0]]) 

        dealer_has_blackjack = view.calculate_total(marcos_hand) == 21
        player_has_blackjack = player_total == 21

        if player_has_blackjack:
            if dealer_has_blackjack:
                async with AsyncSessionLocal() as session:
                    await session.execute(
                        update(UserMDBs)
                        .where(UserMDBs.membro_id == ctx.author.id)
                        .values(MDBs=UserMDBs.MDBs + aposta)
                    )
                    await session.commit()
                embed = view.create_embed("🤝 Ambos têm Blackjack!", f"Empate. Sua aposta de {aposta} MDBs foi devolvida.", discord.Color.blue())
                msg = await ctx.reply(embed=embed)
                view.message = msg
                return
            else:
                blackjack_payout = 1.5
                winnings = int(math.floor(aposta * blackjack_payout))
                async with AsyncSessionLocal() as session:
                    await session.execute(
                        update(UserMDBs)
                        .where(UserMDBs.membro_id == ctx.author.id)
                        .values(MDBs=UserMDBs.MDBs + aposta + winnings)
                    )
                    await session.execute(
                        update(StatsUserData)
                        .where(StatsUserData.membro_id == ctx.author.id)
                        .values(ganho_total=StatsUserData.ganho_total + winnings)
                    )
                    await session.commit()
                embed = view.create_embed("🃏 Blackjack!", f"Blackjack! Você ganhou **{winnings} MDBs** (pagamento 3:2).", discord.Color.green())
                msg = await ctx.reply(embed=embed)
                view.message = msg
                return

        # se não terminou por blackjack, mostrar mensagem inicial com botões
        embed = view.create_embed("🂠 Blackjack", "Use os botões para Hit (comprar) ou Stand (parar).", discord.Color.dark_gold())
        msg = await ctx.reply(embed=embed, view=view)
        view.message = msg

    @commands.command(name="roletarussa")
    async def roletarussa(self, ctx: commands.Context, quantidade: interpretar_valor):
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(UserMDBs).filter_by(membro_id=ctx.author.id))
            userdb = result.scalars().first()
            if quantidade <= 0:
                return ctx.reply("Não aposte uma quantidade menor ou iqual a zero.")
            if quantidade > userdb.MDBs:
                return ctx.reply("Não aposte uma quantidade maior que seu saldo.")
        
        embed = discord.Embed(
            title="🔫 Roleta Russa",
            description=(
                f"Você apostou **{quantidade:,} MDBs**.\n\n"
                "Clique em **Atirar** para puxar o gatilho...\n"
                "Ou **Desistir** para sair com parte da aposta."
            ),
            color=discord.Color.orange()
        )
        embed.set_footer(text="Boa sorte, você vai precisar... 💀")
        embed.set_thumbnail(url='https://media.discordapp.net/attachments/1415295712207572992/1419830368588267580/R.png?ex=68d32f93&is=68d1de13&hm=37d1e150d0790b4020165b45da9283b480d49e664cb60458e273a748115c2d87&=&format=webp&quality=lossless&width=1453&height=819')

        msg = await ctx.reply(embed=embed)
        
        await msg.edit(view=ButtonForRoletaRussa(ctx.author.id, msg, quantidade))
    
    @app_commands.command(name="roleta-russa")
    async def roletarussa_slash(self, interaction:discord.Interaction, quantidade:int):

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(UserMDBs).filter_by(membro_id=interaction.user.id))
            userdb = result.scalars().first()
            if quantidade <= 0:
                return interaction.response.send_message("Não aposte uma quantidade menor ou iqual a zero.")
            if quantidade > userdb.MDBs:
                return interaction.response.send_message("Não aposte uma quantidade maior que seu saldo.")

        embed = discord.Embed(
            title="🔫 Roleta Russa",
            description=(
                f"Você apostou **{quantidade:,} MDBs**.\n\n"
                "Clique em **Atirar** para puxar o gatilho...\n"
                "Ou **Desistir** para sair com parte da aposta."
            ),
            color=discord.Color.orange()
        )
        embed.set_footer(text="Boa sorte, você vai precisar... 💀")
        embed.set_thumbnail(url='https://media.discordapp.net/attachments/1415295712207572992/1419830368588267580/R.png?ex=68d32f93&is=68d1de13&hm=37d1e150d0790b4020165b45da9283b480d49e664cb60458e273a748115c2d87&=&format=webp&quality=lossless&width=1453&height=819')

        msg = await interaction.response.send_message(embed=embed)
        await msg.edit(view=ButtonForRoletaRussa(interaction.user.id, msg, quantidade))

    @commands.command(name="adc", aliases=["adivinharcor", "sorteiocor", "stc"])
    async def adivinhar_cor_reformulad(self, ctx: commands.Context, quantidade: interpretar_valor):
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(UserMDBs).filter_by(membro_id=ctx.author.id))
            userdb = result.scalars().first()
            if quantidade <= 0:
                return ctx.reply("Não aposte uma quantidade menor ou iqual a zero.")
            if quantidade > userdb.MDBs:
                return ctx.reply("Não aposte uma quantidade maior que seu saldo.")

        m = discord.Embed(
            title="🎨 Adivinhe a Cor!",
            description="Quatro cores estão disponíveis, mas apenas **uma** é a correta.\n\n👉 Será que você tem sorte?",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow()
        )
        m.set_thumbnail(url=THUMBNAIL_URL)
        m.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar.url)

        await ctx.reply(embed=m, view=ButtonsForRandomColorCommands(ctx.author.id, color=random_color(), quantidade=quantidade))

    @app_commands.command(name="adc")
    async def adivinhar_cor_reformulad_slash(self, interaction:discord.Interaction, quantidade:int):

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(UserMDBs).filter_by(membro_id=interaction.user.id))
            userdb = result.scalars().first()
            if quantidade <= 0:
                return interaction.response.send_message("Não aposte uma quantidade menor ou iqual a zero.")
            if quantidade > userdb.MDBs:
                return interaction.response.send_message("Não aposte uma quantidade maior que seu saldo.")

        m = discord.Embed(
            title="🎨 Adivinhe a Cor!",
            description="Quatro cores estão disponíveis, mas apenas **uma** é a correta.\n\n👉 Será que você tem sorte?",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow()
        )
        m.set_thumbnail(url=THUMBNAIL_URL)
        m.set_footer(text=f"{interaction.user.name}", icon_url=interaction.user.avatar.url)

        await interaction.response.send_message(embed=m, view=ButtonsForRandomColorCommands(interaction.user.id, color=random_color(), quantidade=quantidade))

    # Comando do bot
    @commands.command(name="niquel", aliases=["slot", "cassino"])
    async def caca_niquel(self, ctx: commands.Context, quantidade: interpretar_valor):
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(UserMDBs).filter_by(membro_id=ctx.author.id))
            userdb = result.scalars().first()
            if quantidade <= 0:
                return ctx.reply("Não aposte uma quantidade menor ou iqual a zero.")
            if quantidade > userdb.MDBs:
                return ctx.reply("Não aposte uma quantidade maior que seu saldo.")

        
        embed = discord.Embed(
            title="🎰 Caça-Níquel",
            description=f"{ctx.author.mention}, clique no botão para girar a roleta apostando **{quantidade} MDBs**!",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url='https://media.discordapp.net/attachments/1415295712207572992/1419570438186467368/OIP.png?ex=68d23d7e&is=68d0ebfe&hm=b2181e10ea002da5c11ee5e1fbd71ed4300313f1b8bfff3ff4fa96c12a0b0c29&=&format=webp&quality=lossless')
        embed.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar.url)

        msg = await ctx.send(embed=embed, view=ButtonForCacaNiquel(ctx.author.id, quantidade, mensagem=None))
        view = ButtonForCacaNiquel(ctx.author.id, quantidade, mensagem=msg)
        await msg.edit(view=view)
        
    @app_commands.command(name="caça-niquel")
    async def caca_niquel_slash(self, interaction:discord.Interaction, quantidade:int):
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(UserMDBs).filter_by(membro_id=interaction.user.id))
            userdb = result.scalars().first()
            if quantidade <= 0:
                return interaction.response.send_message("Não aposte uma quantidade menor ou iqual a zero.")
            if quantidade > userdb.MDBs:
                return interaction.response.send_message("Não aposte uma quantidade maior que seu saldo.")

        embed = discord.Embed(
            title="🎰 Caça-Níquel",
            description=f"{interaction.user.mention}, clique no botão para girar a roleta apostando **{quantidade} MDBs**!",
            color=discord.Color.blurple()
        )
        embed.set_thumbnail(url='https://media.discordapp.net/attachments/1415295712207572992/1419570438186467368/OIP.png?ex=68d23d7e&is=68d0ebfe&hm=b2181e10ea002da5c11ee5e1fbd71ed4300313f1b8bfff3ff4fa96c12a0b0c29&=&format=webp&quality=lossless')
        embed.set_footer(text=f"{interaction.user.name}", icon_url=interaction.user.avatar.url)

        msg = await interaction.response.send_message(embed=embed, view=ButtonForCacaNiquel(interaction.user.id, quantidade, mensagem=None))
        view = ButtonForCacaNiquel(interaction.user.id, quantidade, mensagem=msg)
        await interaction.response.edit_message(view=view)
    
    @commands.command(name="adivinharcarta", aliases=["adct", "acertarcarta", "actc"])
    async def adivinhar_carta(self, ctx:commands.Context, quantidade:interpretar_valor):
        userdb = await get_user(ctx.author.id)
        
        if quantidade <= 0:
            return await ctx.reply("Não aposte uma quantidade igual ou menor que zero!", ephemeral=True)
        
        if userdb.MDBs < quantidade:
            return await ctx.reply("Não aposte uma quantidade maior que seu saldo!", ephemeral=True)
        
        cards = ["🂡", "🂢", "🂣", "🂤", "🂥", "🂦", "🂧", "🂨", "🂩", "🂪", "🂫", "🂬", "🂭", "🂮"]
        card1 = random.choice(cards)
        card2 = random.choice(cards)
        card3 = random.choice(cards)
        card4 = random.choice(cards)
        
        m = discord.Embed(
            title="🃏 Tente acertar a carta!",
            description="Aqui você tem 4 opções de cartas 🂠, uma delas é a correta, enquanto as outras três, são erradas.\nTente acertar para conseguir MDBs!",
            color=discord.Color.dark_blue(),
            timestamp=discord.utils.utcnow()
        )
        
        m.set_footer(text=f"{ctx.author.name}", icon_url=ctx.author.avatar.url)
        m.set_thumbnail(url="https://media.discordapp.net/attachments/1410462821396774924/1443999354477084682/116222f55368e978aeb756d9e80aec04.png?ex=692b1cb2&is=6929cb32&hm=017684578cd7e5f6c392bf7f8862154c598d164a4ed2c0b863d71cb2ba8dfa42&=&format=webp&quality=lossless&width=311&height=438")
        
        view = ButtonsForRandomCards(
            ctx.author.id, card1, card2, card3, card4, quantidade
        )
        
        await ctx.reply(embed=m, view=view)

    @aplicar_rendimento_poupanca.before_loop
    async def before_aplicar_rendimento_poupanca(self):
        await self.bot.wait_until_ready()
        print("⏳ Loop de rendimento da poupança iniciado...")

async def setup(bot):
    await bot.add_cog(EconomiaMDBs(bot))