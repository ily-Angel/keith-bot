from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import select, delete, func

from dbdata import (
    Base, TomatoData, UserMDBs, CorridaUsersRandons, VipsUserMdbs,
    DailyCooldown, RoletaDiariaCooldown, AsyncSessionLocal,
    UserXP, XpGlobal,
    PerfilUserData, SobreMimData, PerfilLike, Casamento,
    FonteUserData, FontSizeData, PerfilSizeData, PerfilBorderData,
    GradientNameData, PerfilModelData, PerfilTextColorsData,
    PremiumDataSuper, PremiumDataBase
)

async def get_user(user_id: int) -> UserMDBs:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(UserMDBs).filter_by(membro_id=user_id))
        userdb = result.scalars().first()
        if not userdb:
            userdb = UserMDBs(membro_id=user_id)
            session.add(userdb)
            await session.commit()
        return userdb


async def obter_membro(user_id: int) -> UserMDBs:
    return await get_user(user_id)


async def get_quantity_tomatos(user_id: int) -> int:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(TomatoData).filter_by(user_id=user_id))
        userdb = result.scalars().first()
        if not userdb:
            userdb = TomatoData(user_id=user_id)
            session.add(userdb)
            await session.commit()
        return userdb.tomatos_quantity


async def get_or_create_perfil(user_id: int) -> PerfilUserData:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PerfilUserData).filter_by(user_id=user_id))
        userdb = result.scalars().first()
        if not userdb:
            userdb = PerfilUserData(user_id=user_id)
            session.add(userdb)
            await session.commit()
        return userdb


async def load_config(user_id: int) -> dict:
    userdb = await get_or_create_perfil(user_id)
    return {
        "user_id": userdb.user_id,
        "background": userdb.background,
        "color": userdb.color,
        "bio": userdb.bio,
        "extra_emoji": userdb.extra_emoji,
        "perfil_faixa_color": userdb.perfil_faixa_color,
        "faixa_color": userdb.faixa_color,
        "mostrar_badges": userdb.mostrar_badges,
        "mostrar_xp_bar": userdb.mostrar_xp_bar,
        "xp_bar_color": userdb.xp_bar_color,
        "xp_background": userdb.xp_background,
        "layout_faixa": userdb.layout_faixa,
        "layout_avatar": userdb.layout_avatar,
        "plataforma": userdb.plataforma,
        "mostrar_casamento": userdb.mostrar_casamento,
        "xp_text_color": userdb.xp_text_color,
    }


async def save_config(user_id: int, **kwargs) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PerfilUserData).filter_by(user_id=user_id))
        userdb = result.scalars().first()
        if not userdb:
            userdb = PerfilUserData(user_id=user_id)
            session.add(userdb)

        for key, value in kwargs.items():
            if hasattr(userdb, key):
                setattr(userdb, key, value)

        await session.commit()


async def get_plataforma(user_id: int) -> Optional[str]:
    cfg = await load_config(user_id)
    valor = cfg.get("plataforma")
    return valor if valor not in (None, "") else None


async def set_plataforma(user_id: int, tipo: str) -> None:
    if tipo not in ("mobile", "desktop"):
        raise ValueError("Tipo inválido de plataforma.")
    await save_config(user_id, plataforma=tipo)

async def get_likes(user_id: int) -> int:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(func.count()).select_from(PerfilLike).filter_by(user_id=user_id)
        )
        return result.scalar() or 0


async def pode_dar_like(user_id: int, liker_id: int) -> bool:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(PerfilLike).filter_by(user_id=user_id, liker_id=liker_id)
        )
        like = result.scalars().first()
        if not like:
            return True
        return datetime.utcnow() - like.ultimo_like >= timedelta(hours=1)


async def registrar_like(user_id: int, liker_id: int) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(PerfilLike).filter_by(user_id=user_id, liker_id=liker_id)
        )
        like = result.scalars().first()
        if not like:
            like = PerfilLike(user_id=user_id, liker_id=liker_id)
            session.add(like)
        like.ultimo_like = datetime.utcnow()
        await session.commit()


async def remover_like(user_id: int) -> None:
    """Remove o like mais antigo recebido pelo usuário."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(PerfilLike)
            .filter_by(user_id=user_id)
            .order_by(PerfilLike.ultimo_like.asc())
            .limit(1)
        )
        like = result.scalars().first()
        if like:
            await session.delete(like)
            await session.commit()

async def load_sobre_mim(user_id: int) -> Optional[dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(SobreMimData).filter_by(user_id=user_id))
        userdb = result.scalars().first()
        if not userdb:
            return None
        return {
            "genero": userdb.genero,
            "sexualidade": userdb.sexualidade,
            "idade_18": bool(userdb.idade_18),
            "pronomes": userdb.pronomes,
            "texto_extra": userdb.texto_extra,
            "botao_style": userdb.botao_style or "azul",
        }


async def save_sobre_mim(user_id: int, **kwargs) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(SobreMimData).filter_by(user_id=user_id))
        userdb = result.scalars().first()
        if not userdb:
            userdb = SobreMimData(user_id=user_id)
            session.add(userdb)

        for key, value in kwargs.items():
            if hasattr(userdb, key):
                setattr(userdb, key, value)

        await session.commit()

def _ids_ordenados(id_a: int, id_b: int) -> tuple[int, int]:
    return tuple(sorted((id_a, id_b)))


async def buscar_id_de_casamento(user_id: int) -> Optional[int]:
    """Retorna o ID do parceiro de casamento do usuário, ou None se não estiver casado."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Casamento).filter_by(user_id_1=user_id)
        )
        casamento = result.scalars().first()
        if casamento:
            return casamento.user_id_2

        result = await session.execute(
            select(Casamento).filter_by(user_id_2=user_id)
        )
        casamento = result.scalars().first()
        if casamento:
            return casamento.user_id_1

        return None


async def esta_casado(user_id: int) -> bool:
    return await buscar_id_de_casamento(user_id) is not None


async def criar_casamento(user_id_1: int, user_id_2: int) -> None:
    id1, id2 = _ids_ordenados(user_id_1, user_id_2)
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Casamento).filter_by(user_id_1=id1, user_id_2=id2)
        )
        casamento = result.scalars().first()
        if not casamento:
            casamento = Casamento(user_id_1=id1, user_id_2=id2, data=datetime.utcnow())
            session.add(casamento)
        else:
            casamento.data = datetime.utcnow()
        await session.commit()


async def desfazer_casamento(user_id_1: int, user_id_2: int) -> None:
    id1, id2 = _ids_ordenados(user_id_1, user_id_2)
    async with AsyncSessionLocal() as session:
        await session.execute(
            delete(Casamento).where(Casamento.user_id_1 == id1, Casamento.user_id_2 == id2)
        )
        await session.commit()


async def listar_casamentos_ordenados_por_data() -> list[Casamento]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Casamento).order_by(Casamento.data.asc()))
        return list(result.scalars().all())

async def adicionar_xp(user_id: int, quantidade: int, guild_id: Optional[int] = None) -> None:
    async with AsyncSessionLocal() as session:
        if guild_id:
            result = await session.execute(
                select(UserXP).filter_by(user_id=user_id, guild_id=guild_id)
            )
            userdb = result.scalars().first()
            if not userdb:
                userdb = UserXP(user_id=user_id, guild_id=guild_id, xp=quantidade)
                session.add(userdb)
            else:
                userdb.xp += quantidade
        else:
            result = await session.execute(select(XpGlobal).filter_by(user_id=user_id))
            userdb = result.scalars().first()
            if not userdb:
                userdb = XpGlobal(user_id=user_id, xp=quantidade)
                session.add(userdb)
            else:
                userdb.xp += quantidade
        await session.commit()


async def get_xp(user_id: int) -> int:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(XpGlobal).filter_by(user_id=user_id))
        userdb = result.scalars().first()
        return userdb.xp if userdb else 0


async def get_xp_guild(user_id: int, guild_id: int) -> int:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserXP).filter_by(user_id=user_id, guild_id=guild_id)
        )
        userdb = result.scalars().first()
        return userdb.xp if userdb else 0


async def get_xp_universal(user_id: int) -> int:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(func.sum(UserXP.xp)).filter_by(user_id=user_id)
        )
        total = result.scalar()
        return total or 0


async def calcular_nivel_e_xp(user_id: int, guild_id: int) -> tuple[int, int, int]:
    total_xp = await get_xp_guild(user_id, guild_id)
    nivel = total_xp // 1000
    restante = total_xp % 1000
    return nivel, restante, total_xp

async def get_fonte(user_id: int) -> str:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(FonteUserData).filter_by(user_id=user_id))
        userdb = result.scalars().first()
        return userdb.font if userdb else "arial"


async def set_fonte(user_id: int, fonte: str) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(FonteUserData).filter_by(user_id=user_id))
        userdb = result.scalars().first()
        if not userdb:
            userdb = FonteUserData(user_id=user_id, font=fonte)
            session.add(userdb)
        else:
            userdb.font = fonte
        await session.commit()


async def get_font_sizes(user_id: int) -> FontSizeData:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(FontSizeData).filter_by(user_id=user_id))
        userdb = result.scalars().first()
        if not userdb:
            userdb = FontSizeData(user_id=user_id)
            session.add(userdb)
            await session.commit()
        return userdb


async def set_font_sizes(user_id: int, nome_px: int, bio_px: int, xp_px: int) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(FontSizeData).filter_by(user_id=user_id))
        userdb = result.scalars().first()
        if not userdb:
            userdb = FontSizeData(user_id=user_id)
            session.add(userdb)
        userdb.font_nome_px = nome_px
        userdb.font_bio_px = bio_px
        userdb.font_xp_px = xp_px
        await session.commit()


async def get_perfil_size(user_id: int) -> PerfilSizeData:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PerfilSizeData).filter_by(user_id=user_id))
        userdb = result.scalars().first()
        if not userdb:
            userdb = PerfilSizeData(user_id=user_id)
            session.add(userdb)
            await session.commit()
        return userdb


async def set_perfil_size(user_id: int, tamanho: int, curvatura_faixa: int) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PerfilSizeData).filter_by(user_id=user_id))
        userdb = result.scalars().first()
        if not userdb:
            userdb = PerfilSizeData(user_id=user_id)
            session.add(userdb)
        userdb.altura_p = tamanho
        userdb.altura_da_faixa = curvatura_faixa
        await session.commit()


async def set_translucidez_faixa(user_id: int, translucidez: int) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PerfilSizeData).filter_by(user_id=user_id))
        userdb = result.scalars().first()
        if not userdb:
            userdb = PerfilSizeData(user_id=user_id, translucides_da_faixa=translucidez)
            session.add(userdb)
        else:
            userdb.translucides_da_faixa = translucidez
        await session.commit()


async def get_perfil_border(user_id: int) -> PerfilBorderData:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PerfilBorderData).filter_by(user_id=user_id))
        userdb = result.scalars().first()
        if not userdb:
            userdb = PerfilBorderData(user_id=user_id)
            session.add(userdb)
            await session.commit()
        return userdb


async def set_perfil_border(user_id: int, cor: str, tamanho: int) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PerfilBorderData).filter_by(user_id=user_id))
        userdb = result.scalars().first()
        if not userdb:
            userdb = PerfilBorderData(user_id=user_id, borda=cor, tamanho_borda=tamanho)
            session.add(userdb)
        else:
            userdb.borda = cor
            userdb.tamanho_borda = tamanho
        await session.commit()


async def get_gradient_colors(user_id: int) -> list:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(GradientNameData).filter_by(user_id=user_id))
        userdb = result.scalars().first()
        return userdb.colors if userdb else []


async def set_gradient_colors(user_id: int, colors: list) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(GradientNameData).filter_by(user_id=user_id))
        userdb = result.scalars().first()
        if not userdb:
            userdb = GradientNameData(user_id=user_id, colors=colors)
            session.add(userdb)
        else:
            userdb.colors = colors
        await session.commit()


async def get_perfil_model(user_id: int) -> str:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PerfilModelData).filter_by(user_id=user_id))
        userdb = result.scalars().first()
        return userdb.model if userdb else "estatico"


async def set_perfil_model(user_id: int, model: str) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PerfilModelData).filter_by(user_id=user_id))
        userdb = result.scalars().first()
        if not userdb:
            userdb = PerfilModelData(user_id=user_id, model=model)
            session.add(userdb)
        else:
            userdb.model = model
        await session.commit()


async def get_perfil_text_colors(user_id: int) -> PerfilTextColorsData:
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PerfilTextColorsData).filter_by(user_id=user_id))
        userdb = result.scalars().first()
        if not userdb:
            userdb = PerfilTextColorsData(user_id=user_id)
            session.add(userdb)
            await session.commit()
        return userdb


# =========================
# PREMIUM
# =========================

async def verificar_premium(user_id: int) -> bool:
    """Verifica se o usuário é premium super."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PremiumDataSuper).filter_by(user_id=user_id))
        return result.scalars().first() is not None

async def verificar_premium_base(user_id: int) -> bool:
    """Verifica se o usuário é premium base."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(PremiumDataBase).filter_by(user_id=user_id))
        return result.scalars().first() is not None

async def get_or_create_xp_user(user_id: int, guild_id: int):
    """Obtém ou cria um registro de XP para o usuário no servidor."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserXP).filter_by(user_id=user_id, guild_id=guild_id)
        )
        userdb = result.scalars().first()
        if not userdb:
            userdb = UserXP(user_id=user_id, guild_id=guild_id, xp=0)
            session.add(userdb)
            await session.commit()
        return userdb

async def get_user_balance(user_id: int) -> int:
    """Obtém o saldo de MDBs do usuário."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(UserMDBs).filter_by(membro_id=user_id))
        userdb = result.scalars().first()
        return userdb.MDBs if userdb else 0