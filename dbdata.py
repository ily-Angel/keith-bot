from __future__ import annotations
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import BigInteger, String, Integer, DateTime, ForeignKey, JSON, Boolean, UniqueConstraint
from datetime import datetime


# =========================
# BASE PRINCIPAL
# =========================
class Base(DeclarativeBase):
    pass


# =========================
# MODELOS
# =========================

class UserMDBs(Base):
    __tablename__ = "membros"

    membro_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, primary_key=True)
    MDBs: Mapped[int] = mapped_column(Integer, default=0)


class CorridaUsersRandons(Base):
    __tablename__ = "corridas_category_true"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    corridas_nsfg: Mapped[int] = mapped_column(Integer, default=0)
    corridas_ganhas1: Mapped[int] = mapped_column(Integer, default=0)
    corridas_ganhas2: Mapped[int] = mapped_column(Integer, default=0)
    corridas_ganhas3: Mapped[int] = mapped_column(Integer, default=0)
    corridas_ganhas4: Mapped[int] = mapped_column(Integer, default=0)


class VipsUserMdbs(Base):
    __tablename__ = "vips"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    date_vip: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class DailyCooldown(Base):
    __tablename__ = "daily_cooldown"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    last_claimed: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class RoletaDiariaCooldown(Base):
    __tablename__ = "roleta_cooldown"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    last_claimed: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Poupanca(Base):
    __tablename__ = "poupancas"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    nickname: Mapped[str] = mapped_column(String(64), nullable=True)
    mdbs_poupanca: Mapped[int] = mapped_column(Integer, default=0)


class BolsaPeixes(Base):
    __tablename__ = "bolsa_peixes"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)

    robalo: Mapped[int] = mapped_column(Integer, default=0)
    garoupa: Mapped[int] = mapped_column(Integer, default=0)
    cherne: Mapped[int] = mapped_column(Integer, default=0)
    dourado: Mapped[int] = mapped_column(Integer, default=0)
    pescada: Mapped[int] = mapped_column(Integer, default=0)
    tainha: Mapped[int] = mapped_column(Integer, default=0)
    sardinha: Mapped[int] = mapped_column(Integer, default=0)
    atum: Mapped[int] = mapped_column(Integer, default=0)
    cloba: Mapped[int] = mapped_column(Integer, default=0)
    badejo: Mapped[int] = mapped_column(Integer, default=0)

    pintado: Mapped[int] = mapped_column(Integer, default=0)
    pacu: Mapped[int] = mapped_column(Integer, default=0)
    tambaqui: Mapped[int] = mapped_column(Integer, default=0)
    pirarucu: Mapped[int] = mapped_column(Integer, default=0)
    tilapia: Mapped[int] = mapped_column(Integer, default=0)
    matrinxa: Mapped[int] = mapped_column(Integer, default=0)
    jau: Mapped[int] = mapped_column(Integer, default=0)
    cascudo: Mapped[int] = mapped_column(Integer, default=0)
    corvina: Mapped[int] = mapped_column(Integer, default=0)


class StatsUserData(Base):
    __tablename__ = "stats_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    membro_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    ganho_total: Mapped[int] = mapped_column(Integer, default=0)
    perda_total: Mapped[int] = mapped_column(Integer, default=0)


class ReactionRoleMessage(Base):
    __tablename__ = "reaction_role_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    guild_id: Mapped[str] = mapped_column(String(20), nullable=False)
    message_id: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    channel_id: Mapped[str] = mapped_column(String(20), nullable=False)
    role_data: Mapped[dict] = mapped_column(JSON, nullable=False)  # {emoji: role_id}

class UserXP(Base):
    __tablename__ = "xp_guild"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    guild_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    xp: Mapped[int] = mapped_column(Integer, default=0)

class XpGlobal(Base):
    __tablename__ = 'global_xp'

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    xp: Mapped[int] = mapped_column(Integer, default=0)
    
class ChannelLogsConfiguration(Base):
    __tablename__ = 'logs_configuration'

    guild_id: Mapped[int] = mapped_column(BigInteger, default=0, primary_key=True)
    channel_id: Mapped[int] = mapped_column(BigInteger, default=0)

class DataForWarns(Base):
    __tablename__ = 'warns_users'
    
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, primary_key=True)
    warns: Mapped[int] = mapped_column(Integer, default=0)
    
class DataForGuildWarns(Base):
    __tablename__ = 'data_guild_warns'
    
    guild_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, primary_key=True)
    recado: Mapped[str] = mapped_column(String, default='')
    title: Mapped[str] = mapped_column(String, default='')
    cor_embed: Mapped[str] = mapped_column(String, default='')

class PremiumDataSuper(Base):
    __tablename__ = 'premium_users_super'
    
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, primary_key=True)
    data_premium_init = mapped_column(DateTime, default=datetime.utcnow)
    
class PremiumDataBase(Base):
    __tablename__ = 'premium_users_Base'
    
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, primary_key=True)
    data_premium_init = mapped_column(DateTime, default=datetime.utcnow)
    
class OptionsCommandsStyle(Base):
    __tablename__ = 'options_commands_styles'
    
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, primary_key=True)
    command_option_1: Mapped[str] = mapped_column(String, default='')
    command_option_2: Mapped[str] = mapped_column(String, default='')
    command_option_3: Mapped[str] = mapped_column(String, default='')
    command_option_4: Mapped[str] = mapped_column(String, default='')
    command_option_5: Mapped[str] = mapped_column(String, default='')
    command_option_6: Mapped[str] = mapped_column(String, default='')

class NotificationUser(Base):
    __tablename__ = "notification_users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    last_sent: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
  
class TomatoData(Base):
    __tablename__ = 'tomato_data'
    
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, primary_key=True)
    tomatos_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class PerfilUserData(Base):
    """Configurações visuais e gerais do <perfil (antiga tabela 'perfil')."""
    __tablename__ = "perfil_data"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, primary_key=True)
    background: Mapped[str] = mapped_column(String, default="")
    color: Mapped[str] = mapped_column(String, default="#2F3136")
    bio: Mapped[str] = mapped_column(String, default="Sem bio.")
    extra_emoji: Mapped[str] = mapped_column(String, default="")
    perfil_faixa_color: Mapped[str] = mapped_column(String, default="#1E1E1E")
    faixa_color: Mapped[str] = mapped_column(String, default="#1E1E1E")
    mostrar_badges: Mapped[bool] = mapped_column(Boolean, default=True)
    mostrar_xp_bar: Mapped[bool] = mapped_column(Boolean, default=False)
    xp_bar_color: Mapped[str] = mapped_column(String, default="#64B4FF")
    xp_background: Mapped[str] = mapped_column(String, default="")
    layout_faixa: Mapped[str] = mapped_column(String, default="perfil")
    layout_avatar: Mapped[str] = mapped_column(String, default="perfil")
    plataforma: Mapped[str] = mapped_column(String, nullable=True)
    mostrar_casamento: Mapped[bool] = mapped_column(Boolean, default=False)
    xp_text_color: Mapped[str] = mapped_column(String, default="#FFFFFF")


class SobreMimData(Base):
    """Seção '+Sobre Mim' do perfil (antiga tabela 'sobre_mim')."""
    __tablename__ = "sobre_mim_data"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, primary_key=True)
    genero: Mapped[str] = mapped_column(String, nullable=True)
    sexualidade: Mapped[str] = mapped_column(String, nullable=True)
    idade_18: Mapped[bool] = mapped_column(Boolean, default=False)
    pronomes: Mapped[str] = mapped_column(String, nullable=True)
    texto_extra: Mapped[str] = mapped_column(String, nullable=True)
    botao_style: Mapped[str] = mapped_column(String, default="azul")


class PerfilLike(Base):
    """Likes recebidos no perfil (antiga tabela 'likes'). Chave composta (user_id, liker_id)."""
    __tablename__ = "perfil_likes"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, primary_key=True)
    liker_id: Mapped[int] = mapped_column(BigInteger, nullable=False, primary_key=True)
    ultimo_like: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Casamento(Base):
    """Casamentos entre usuários (antiga tabela 'casamentos'). IDs sempre ordenados (user_id_1 < user_id_2)."""
    __tablename__ = "casamentos"

    user_id_1: Mapped[int] = mapped_column(BigInteger, nullable=False, primary_key=True)
    user_id_2: Mapped[int] = mapped_column(BigInteger, nullable=False, primary_key=True)
    data: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class FonteUserData(Base):
    """Fonte escolhida pelo usuário para os comandos de perfil/xp (antiga classe FontC)."""
    __tablename__ = "perfil_fontes"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, primary_key=True)
    font: Mapped[str] = mapped_column(String, default="arial")


class FontSizeData(Base):
    """Tamanhos (PX) de fonte do nome/bio/xp no <perfil (antiga classe FontPX)."""
    __tablename__ = "perfil_fonte_px"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, primary_key=True)
    font_nome_px: Mapped[int] = mapped_column(Integer, default=36)
    font_bio_px: Mapped[int] = mapped_column(Integer, default=24)
    font_xp_px: Mapped[int] = mapped_column(Integer, default=18)


class PerfilSizeData(Base):
    """Tamanho da imagem do perfil e curvatura/translucidez da faixa (antiga TamanhoDaImagemDoPerfilEExtras)."""
    __tablename__ = "perfil_tamanho_extras"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, primary_key=True)
    altura_p: Mapped[int] = mapped_column(Integer, default=300)
    largura: Mapped[int] = mapped_column(Integer, default=600)
    altura_da_faixa: Mapped[int] = mapped_column(Integer, default=1)
    translucides_da_faixa: Mapped[int] = mapped_column(Integer, default=150)


class PerfilBorderData(Base):
    """Cor e espessura da borda da faixa do perfil (antiga ExtrasAlterations)."""
    __tablename__ = "perfil_borda_extras"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, primary_key=True)
    borda: Mapped[str] = mapped_column(String, default="#000000")
    tamanho_borda: Mapped[int] = mapped_column(Integer, default=4)


class GradientNameData(Base):
    """Cores do gradiente do nome no perfil (antiga GradientForName, feature premium)."""
    __tablename__ = "perfil_gradient_nome"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, primary_key=True)
    colors: Mapped[list] = mapped_column(JSON, default=list)


class PerfilModelData(Base):
    """Modo do perfil: GIF ou estático (antiga GifProfileAndStatic, feature premium)."""
    __tablename__ = "perfil_model_data"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, primary_key=True)
    model: Mapped[str] = mapped_column(String, default="estatico")


class PerfilTextColorsData(Base):
    """Cores extras de texto do perfil (antiga ColorsTextOptions)."""
    __tablename__ = "perfil_text_colors"

    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True, primary_key=True)
    color_text1: Mapped[str] = mapped_column(String, default="#FFFFFF")
    color_text2: Mapped[str] = mapped_column(String, default="#FFFFFF")
    color_text3: Mapped[str] = mapped_column(String, default="#FFFFFF")
    color_text4: Mapped[str] = mapped_column(String, default="#FFFFFF")


# =========================
# ENGINE & SESSION
# =========================

DATABASE_URL = "sqlite+aiosqlite:///./bancodb.db"  # pode trocar por postgresql+asyncpg

engine = create_async_engine(DATABASE_URL, echo=False, future=True)

AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

AsyncSessionTwoLocal = AsyncSessionLocal

# =========================
# INIT DB
# =========================
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
